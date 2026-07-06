# [transition] SCRUM-35 — rewritten from wehan GameState.

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pygame
from pygame.sprite import LayeredUpdates
from pygame.surface import Surface

from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.fruit_schedule import (
    FRUIT_VISIBLE_DURATION_S,
    fruit_for_level,
    spawn_seconds_for_level,
)
from game.level import CellPos, LevelLayout
from game.render_config import DIRECTION_DELTA, WorldRenderConfig, cell_center
from game.wall_tile_picker import pick
from game.ghost_logic import (
    activate_frightened_mode,
    move_ghosts,
    resolve_actor_collisions,
    update_frightened_state,
)
from maze.map_data import TileType
from sprites.assets import Assets
from pygame.sprite import Sprite
from sprites.sprite_types import Direction, FRUIT_POINTS, GhostKind


@dataclass(slots=True, frozen=True)
class ScorePopup:
    """Floating score label shown briefly after collecting points."""

    center: tuple[int, int]
    points: int
    expires_at_ms: int


class GameWorld:
    """Runtime gameplay state: entities, movement, collisions, and score."""

    PLAYER_STEP_MS: ClassVar[int] = 180
    PLAYER_STEP_MS_MIN: ClassVar[int] = 60
    PLAYER_STEP_MS_MAX: ClassVar[int] = 360
    PLAYER_SPEED_STEP_MS: ClassVar[int] = 20
    DEFAULT_TRAVEL_DIRECTION: ClassVar[Direction] = Direction.RIGHT
    PELLET_POINTS: ClassVar[int] = 10
    POWER_PELLET_POINTS: ClassVar[int] = 50
    GHOST_POINTS: ClassVar[int] = 200
    FRIGHTENED_DURATION_MS: ClassVar[int] = 6000
    FRIGHTENED_FLASH_MS: ClassVar[int] = 2000
    FRIGHTENED_GHOST_SPEED_DIVISOR: ClassVar[int] = 2
    SCORE_POPUP_DURATION_MS: ClassVar[int] = 1000
    # wehan's terminal game alternated 20 chase turns / 20 scatter turns;
    # one turn = one player grid step (PLAYER_STEP_MS), so 20 x 180ms.
    CHASE_DURATION_MS: ClassVar[int] = 20 * PLAYER_STEP_MS
    SCATTER_DURATION_MS: ClassVar[int] = 20 * PLAYER_STEP_MS
    GHOST_EATEN_PAUSE_MS: ClassVar[int] = 1000

    def __init__(
        self,
        layout: LevelLayout,
        catalog: Assets,
        render_config: WorldRenderConfig,
        initial_score: int = 0,
        level_number: int = 1,
        pellet_points: int = PELLET_POINTS,
        power_pellet_points: int = POWER_PELLET_POINTS,
        ghost_points: int = GHOST_POINTS,
    ) -> None:
        """Create a world and spawn all entities from a level layout.

        Args:
            layout: Immutable maze layout with spawns and collectibles.
            catalog: Loaded sprite assets for actors and tiles.
            render_config: Grid-to-pixel mapping for entity placement.
            initial_score: Starting score carried into this level.
            level_number: One-based level index for fruit scheduling.
            pellet_points: Points awarded for normal pellets.
            power_pellet_points: Points awarded for power pellets.
            ghost_points: Points awarded for eating a frightened ghost.
        """
        self._layout: LevelLayout = layout
        self._catalog: Assets = catalog
        self._render_config: WorldRenderConfig = render_config
        self._level_number: int = level_number
        self.pellet_points = pellet_points
        self.power_pellet_points = power_pellet_points
        self.ghost_points = ghost_points
        self.all_sprites: LayeredUpdates[Sprite] = LayeredUpdates()
        self._pellets: dict[CellPos, PelletEntity] = {}
        self._player: PlayerEntity | None = None
        self._ghosts: dict[GhostKind, GhostEntity] = {}
        self._ghost_home: dict[GhostKind, CellPos] = {}
        self._frightened_until_ms: int = 0
        self.frightened: bool = False
        self._scatter_mode: bool = False
        self._mode_started_ms: int = pygame.time.get_ticks()
        self._pause_until_ms: int = 0
        self._ghost_step_count: int = 0
        self._invincible: bool = False
        self._ghosts_frozen: bool = False
        self._player_step_ms: int = self.PLAYER_STEP_MS
        self._fruit: PelletEntity | None = None
        self._fruit_spawn_index: int = 0
        self._fruit_kill_at_ms: int = 0
        self.score: int = initial_score
        self.score_popups: list[ScorePopup] = []
        self.frozen: bool = False
        self._step_now_ms: int = 0
        self._wall_flash_white: bool = False
        self._wall_sprites: list[WallTileEntity] = []
        self._step_accumulator_ms: float = 0.0
        self._ghost_step_accumulator_ms: float = 0.0
        self._travel_direction: Direction = self.DEFAULT_TRAVEL_DIRECTION
        self._requested_direction: Direction | None = None
        _spawn_from_layout(self)

    @property
    def all_consumables_cleared(self) -> bool:
        """Return whether all pellets and power pellets are gone.

        Returns:
            True when no collectibles remain on the maze.
        """
        return not self._pellets

    @property
    def player_is_dying(self) -> bool:
        """Return whether Pac-Man's death animation is playing.

        Returns:
            True while the death sequence is active.
        """
        return self._player is not None and self._player.dying

    @property
    def player_death_finished(self) -> bool:
        """Return whether Pac-Man's death animation has finished.

        Returns:
            True once the death sequence completes.
        """
        return self._player is not None and self._player.death_finished

    @property
    def level_fruit_surface(self) -> Surface | None:
        """Return the HUD fruit sprite for the current level.

        Returns:
            Fruit surface for the level, or None if unavailable.
        """
        kind = fruit_for_level(self._level_number)
        fruit = self._catalog.fruits.get(kind)
        return fruit

    @property
    def invincible(self) -> bool:
        """Return whether cheat invincibility is enabled.

        Returns:
            True when Pac-Man cannot be killed by ghosts.
        """
        return self._invincible

    @property
    def ghosts_frozen(self) -> bool:
        """Return whether cheat ghost-freeze is enabled.

        Returns:
            True when ghost movement is disabled.
        """
        return self._ghosts_frozen

    @property
    def player_step_ms(self) -> int:
        """Return Pac-Man's current grid step interval in milliseconds.

        Returns:
            Milliseconds between player grid steps.
        """
        return self._player_step_ms

    @property
    def speed_cheat_active(self) -> bool:
        """Return whether the player speed cheat differs from default.

        Returns:
            True when step interval has been adjusted away from default.
        """
        return self._player_step_ms != self.PLAYER_STEP_MS

    def set_wall_flash(self, white: bool) -> None:
        """Toggle wall tiles between blue and white maze sprites.

        Args:
            white: When True, use white flash sprites; otherwise blue.
        """
        if self._wall_flash_white == white:
            return
        self._wall_flash_white = white
        for wall in self._wall_sprites:
            wall.set_flash_white(white)

    def toggle_invincible(self) -> bool:
        """Flip cheat invincibility.

        Returns:
            New invincibility state after toggling.
        """
        self._invincible = not self._invincible
        return self._invincible

    def toggle_ghosts_frozen(self) -> bool:
        """Flip cheat ghost-freeze.

        Returns:
            New ghost-freeze state after toggling.
        """
        self._ghosts_frozen = not self._ghosts_frozen
        return self._ghosts_frozen

    def adjust_player_speed(self, delta_ms: int) -> None:
        """Adjust Pac-Man step interval for the speed cheat.

        Args:
            delta_ms: Change in milliseconds; lower values move faster.
        """
        self._player_step_ms = max(
            self.PLAYER_STEP_MS_MIN,
            min(
                self.PLAYER_STEP_MS_MAX,
                self._player_step_ms + delta_ms,
            ),
        )

    def freeze_gameplay(self) -> None:
        """Pause movement and clear pending input."""
        self.frozen = True
        self._requested_direction = None
        self._step_accumulator_ms = 0.0
        self._ghost_step_accumulator_ms = 0.0
        self._sync_visual_centers()

    def unfreeze_gameplay(self) -> None:
        """Resume movement after a pause."""
        self.frozen = False

    def pause_gameplay(self, duration_ms: int) -> None:
        """Freeze gameplay for a fixed duration.

        Args:
            duration_ms: Pause length in milliseconds; update() auto-resumes.
        """
        self.freeze_gameplay()
        self._pause_until_ms = pygame.time.get_ticks() + duration_ms

    def start_auto_movement(self) -> None:
        """Start default auto-walk after the READY phase ends."""
        self._travel_direction = self.DEFAULT_TRAVEL_DIRECTION
        self._step_accumulator_ms = 0.0
        self._ghost_step_accumulator_ms = 0.0
        self._mode_started_ms = pygame.time.get_ticks()
        if self._player is not None:
            self._player.face(self._travel_direction)

    def update(self, dt: float, now_ms: int) -> None:
        """Advance animations, ghost mode, and transient UI state.

        Args:
            dt: Frame delta time in seconds.
            now_ms: Current timestamp in milliseconds.
        """
        if self._pause_until_ms and now_ms >= self._pause_until_ms:
            self._pause_until_ms = 0
            self.unfreeze_gameplay()
        cycle = self.CHASE_DURATION_MS + self.SCATTER_DURATION_MS
        elapsed = now_ms - self._mode_started_ms
        self._scatter_mode = elapsed % cycle >= self.CHASE_DURATION_MS
        if self._player is not None:
            self._player.update(dt, now_ms)
        for ghost in self._ghosts.values():
            if not ghost.hidden:
                ghost.update(dt, now_ms)
        self._apply_step_visual()
        update_frightened_state(self, now_ms)
        _prune_score_popups(self, now_ms)

    def _apply_step_visual(self) -> None:
        """Interpolate actor sprites between discrete grid steps."""
        if self.frozen:
            return
        t = min(1.0, self._step_accumulator_ms / self.player_step_ms)
        if self._player is not None:
            self._player.apply_visual_lerp(t)
        ghost_t = min(
            1.0,
            self._ghost_step_accumulator_ms / self.PLAYER_STEP_MS,
        )
        for ghost in self._ghosts.values():
            if not ghost.hidden:
                ghost.apply_visual_lerp(ghost_t)

    def draw(self, surface: Surface) -> None:
        """Draw all sprites in layer order.

        Args:
            surface: Destination pygame surface.
        """
        self.all_sprites.draw(surface)

    def respawn_player(self) -> None:
        """Reset Pac-Man to the level spawn after losing a life."""
        if self._player is None:
            return
        spawn = self._layout.player_spawn
        center = cell_center(self._render_config, spawn)
        self._player.reset_after_death(spawn, center)

    def respawn_ghosts(self) -> None:
        """Return every ghost to its home cell and clear frightened mode."""
        self._frightened_until_ms = 0
        self.frightened = False
        for kind, ghost in self._ghosts.items():
            home = self._ghost_home[kind]
            center = cell_center(self._render_config, home)
            ghost.respawn_at(home, center)
            self.all_sprites.add(ghost, layer=ghost.layer)

    def reset_fruit_spawns(self) -> None:
        """Clear active fruit and reset fruit spawn progression."""
        _kill_fruit(self)
        self._fruit_spawn_index = 0

    def teardown(self) -> None:
        """Destroy all sprites and clear world state."""
        for sprite in list(self.all_sprites.sprites()):
            sprite.kill()
        self.all_sprites.empty()
        self._player = None
        self._ghosts.clear()
        self._ghost_home.clear()
        self._fruit = None
        self._pellets.clear()
        self.score_popups.clear()
        self.frozen = False
        self._wall_flash_white = False
        self._wall_sprites.clear()
        self._frightened_until_ms = 0
        self.frightened = False
        self._fruit_spawn_index = 0
        self._fruit_kill_at_ms = 0

    def _consume_current_cell(self) -> None:
        """Eat pellet or power pellet at Pac-Man's current cell."""
        if self._player is None:
            return
        pellet = self._pellets.pop(self._player.cell, None)
        if pellet is not None:
            self.score += pellet.points
            if pellet.cell in self._layout.power_pellet_cells:
                activate_frightened_mode(self)
            pellet.kill()
        _collect_fruit(self)

    def _sync_visual_centers(self) -> None:
        """Snap actor visuals to grid centers when movement pauses."""
        if self._player is not None:
            self._player.begin_step()
        for ghost in self._ghosts.values():
            if not ghost.hidden:
                ghost.begin_step()


def _spawn_from_layout(world: GameWorld) -> None:
    """Instantiate walls, pellets, ghosts, and the player from layout.

    Args:
        world: Target world whose sprite groups are populated.
    """
    cfg = world._render_config
    # Enclosed holes inside wall formations get a 2x2-tile solid fill
    # first, reaching the centre lines of the surrounding wall tiles so
    # the whole formation reads as one solid mass. Wall line art is added
    # afterwards and draws on top (same layer, insertion order).
    for pos in world._layout.unreachable_floor:
        fill = WallTileEntity(
            world._catalog.wall_fill,
            world._catalog.wall_fill_white,
            cell_center(cfg, pos),
        )
        world._wall_sprites.append(fill)
        world.all_sprites.add(fill, layer=fill.layer)
    for row_index, row in enumerate(world._layout.cells):
        for col_index, tile in enumerate(row):
            pos = CellPos(row_index, col_index)
            if tile != TileType.WALL:
                continue
            wall_kind = pick(world._layout, pos)
            blue_surface = world._catalog.maze_tiles[wall_kind]
            white_surface = world._catalog.maze_white_tiles[wall_kind]
            wall = WallTileEntity(
                blue_surface,
                white_surface,
                cell_center(cfg, pos),
            )
            world._wall_sprites.append(wall)
            world.all_sprites.add(wall, layer=wall.layer)

    for pos in world._layout.pellet_cells:
        pellet = PelletEntity(
            world._catalog.dot_surface,
            pos,
            cell_center(cfg, pos),
            world.pellet_points,
        )
        world.all_sprites.add(pellet, layer=pellet.layer)
        world._pellets[pos] = pellet

    for pos in world._layout.power_pellet_cells:
        pellet = PelletEntity(
            world._catalog.power_pellet_surface,
            pos,
            cell_center(cfg, pos),
            world.power_pellet_points,
        )
        world.all_sprites.add(pellet, layer=pellet.layer)
        world._pellets[pos] = pellet

    for kind, cell in world._layout.ghost_spawns:
        ghost = GhostEntity(
            kind,
            world._catalog.ghosts_by_kind[kind],
            world._catalog.ghost_frightened,
            cell,
            cell_center(cfg, cell),
            flash_animation=world._catalog.ghost_frightened_flash,
            eyes_animation=world._catalog.ghost_eyes,
        )
        world._ghosts[kind] = ghost
        world._ghost_home[kind] = cell
        world.all_sprites.add(ghost, layer=ghost.layer)

    spawn = world._layout.player_spawn
    pacman_by_dir = {
        direction: world._catalog.pacman[direction] for direction in Direction
    }
    world._player = PlayerEntity(
        pacman_by_dir,
        spawn,
        cell_center(cfg, spawn),
        death_animation=world._catalog.pacman_death,
    )
    world.all_sprites.add(world._player, layer=world._player.layer)


def request_turn(world: GameWorld, direction: Direction) -> None:
    """Buffer a direction change from player input.

    Args:
        world: Active game world receiving the input.
        direction: Requested travel direction.
    """
    if world.frozen or world.player_is_dying:
        return
    world._requested_direction = direction


def _move_player(world: GameWorld, direction: Direction) -> bool:
    """Move Pac-Man one grid step if the target cell is walkable.

    Args:
        world: Active game world.
        direction: Direction to attempt.

    Returns:
        True when the move succeeded.
    """
    if world._player is None or world._player.dying:
        return False

    row_delta, col_delta = DIRECTION_DELTA[direction]
    target = CellPos(
        world._player.cell.row + row_delta,
        world._player.cell.col + col_delta,
    )
    world._player.face(direction)
    if world._layout.is_wall(target):
        return False

    world._player.move_to(
        target,
        cell_center(world._render_config, target),
    )
    world._consume_current_cell()
    return True


def _auto_step(world: GameWorld) -> None:
    """Try a buffered turn, otherwise continue in the travel direction.

    Args:
        world: Active game world.
    """
    if world._requested_direction is not None:
        if _move_player(world, world._requested_direction):
            world._travel_direction = world._requested_direction
            return
    _move_player(world, world._travel_direction)


def _begin_player_visual_step(world: GameWorld) -> None:
    """Start visual interpolation for Pac-Man's next grid step.

    Args:
        world: Active game world.
    """
    if world._player is not None:
        world._player.begin_step()


def _begin_ghost_visual_step(world: GameWorld) -> None:
    """Start visual interpolation for every visible ghost.

    Args:
        world: Active game world.
    """
    for ghost in world._ghosts.values():
        if not ghost.hidden:
            ghost.begin_step()


def update_player_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance Pac-Man on the grid while gameplay is active.

    Args:
        world: Active game world.
        dt_s: Elapsed time in seconds since the last update.
        now_ms: Current timestamp in milliseconds.
    """
    if world.frozen or world._player is None or world._player.dying:
        return
    world._step_now_ms = now_ms
    world._step_accumulator_ms += dt_s * 1000.0
    while world._step_accumulator_ms >= world.player_step_ms:
        world._step_accumulator_ms -= world.player_step_ms
        _begin_player_visual_step(world)
        _auto_step(world)
        resolve_actor_collisions(world)


def update_ghost_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance ghosts on their fixed grid step while gameplay is active.

    Args:
        world: Active game world.
        dt_s: Elapsed time in seconds since the last update.
        now_ms: Current timestamp in milliseconds.
    """
    if world.frozen or world._player is None or world._player.dying:
        return
    world._step_now_ms = now_ms
    world._ghost_step_accumulator_ms += dt_s * 1000.0
    while world._ghost_step_accumulator_ms >= world.PLAYER_STEP_MS:
        world._ghost_step_accumulator_ms -= world.PLAYER_STEP_MS
        _begin_ghost_visual_step(world)
        move_ghosts(world)
        resolve_actor_collisions(world)


def spawn_fruit(world: GameWorld, now_ms: int) -> None:
    """Place the level's bonus fruit at the fruit spawn cell.

    Args:
        world: Active game world.
        now_ms: Current timestamp in milliseconds.
    """
    _kill_fruit(world)
    kind = fruit_for_level(world._level_number)
    surface = world._catalog.fruits.get(kind)
    if surface is None:
        return
    cell = world._layout.fruit_spawn
    world._fruit = PelletEntity(
        surface,
        cell,
        cell_center(world._render_config, cell),
        FRUIT_POINTS[kind],
    )
    world.all_sprites.add(world._fruit, layer=world._fruit.layer)
    world._fruit_kill_at_ms = now_ms + FRUIT_VISIBLE_DURATION_S * 1000
    # Fruit spawns on the player's spawn cell; if Pac-Man is standing there
    # collection must happen now, not on his next move.
    _collect_fruit(world)


def _kill_fruit(world: GameWorld) -> None:
    """Remove the active bonus fruit sprite, if any.

    Args:
        world: Active game world.
    """
    if world._fruit is None:
        return
    world._fruit.kill()
    world._fruit = None
    world._fruit_kill_at_ms = 0


def update_fruit_spawns(
    world: GameWorld,
    level_elapsed_s: int,
    now_ms: int,
) -> None:
    """Spawn or expire bonus fruit based on the level schedule.

    Args:
        world: Active game world.
        level_elapsed_s: Seconds elapsed since level play began.
        now_ms: Current timestamp in milliseconds.
    """
    spawn_times = spawn_seconds_for_level(world._level_number)
    while (
        world._fruit_spawn_index < len(spawn_times)
        and level_elapsed_s >= spawn_times[world._fruit_spawn_index]
    ):
        spawn_fruit(world, now_ms)
        world._fruit_spawn_index += 1
    if world._fruit is not None and now_ms >= world._fruit_kill_at_ms:
        _kill_fruit(world)


def add_score_popup(
    world: GameWorld, center: tuple[int, int], points: int
) -> None:
    """Show a short-lived floating score label near a pixel position.

    Args:
        world: Active game world.
        center: Anchor pixel position for the popup.
        points: Score value to display.
    """
    tile_px = world._render_config.tile_px
    world.score_popups.append(
        ScorePopup(
            center=(center[0], center[1] + tile_px // 2 + 2),
            points=points,
            expires_at_ms=(
                pygame.time.get_ticks() + world.SCORE_POPUP_DURATION_MS
            ),
        )
    )


def _collect_fruit(world: GameWorld) -> None:
    """Award points when Pac-Man occupies the same cell as the fruit.

    Args:
        world: Active game world.
    """
    if world._player is None or world._fruit is None:
        return
    if world._player.cell != world._fruit.cell:
        return
    world.score += world._fruit.points
    add_score_popup(world, world._fruit.center, world._fruit.points)
    _kill_fruit(world)


def _prune_score_popups(world: GameWorld, now_ms: int) -> None:
    """Drop expired floating score labels.

    Args:
        world: Active game world.
        now_ms: Current timestamp in milliseconds.
    """
    if not world.score_popups:
        return
    world.score_popups = [
        popup for popup in world.score_popups if now_ms < popup.expires_at_ms
    ]
