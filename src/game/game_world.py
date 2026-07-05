# [transition] SCRUM-35 — rewritten from wehan GameState.

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pygame
from pygame.sprite import Group, LayeredUpdates, spritecollide
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
from game.render_config import WorldRenderConfig, cell_center, direction_delta
from game.wall_tile_picker import pick
from game.ghost_logic import (
    activate_frightened_mode,
    move_ghosts,
    resolve_actor_collisions,
    update_frightened_state,
    update_ghost_respawns,
)
from maze.map_data import TileType
from sprites.assets import Assets
from pygame.sprite import Sprite
from sprites.sprite_types import Direction, FRUIT_POINTS, GhostKind


@dataclass(slots=True, frozen=True)
class ScorePopup:
    """Short-lived point label shown where a fruit was eaten."""

    center: tuple[int, int]
    points: int
    expires_at_ms: int


class GameWorld:
    """Owns runtime gameplay entities, groups, and collision state."""

    PLAYER_STEP_MS: ClassVar[int] = 180
    DEFAULT_TRAVEL_DIRECTION: ClassVar[Direction] = Direction.RIGHT
    PELLET_POINTS: ClassVar[int] = 10
    POWER_PELLET_POINTS: ClassVar[int] = 50
    GHOST_POINTS: ClassVar[int] = 200
    FRIGHTENED_DURATION_MS: ClassVar[int] = 6000
    GHOST_EATEN_RESPAWN_MS: ClassVar[int] = 5000
    SCORE_POPUP_DURATION_MS: ClassVar[int] = 1000

    __slots__ = (
        "_catalog",
        "_fruit",
        "_fruit_kill_at_ms",
        "_fruit_spawn_index",
        "_ghost_home",
        "_ghost_respawn_at_ms",
        "_ghosts",
        "_frightened_until_ms",
        "_layout",
        "_level_number",
        "_player",
        "_render_config",
        "pellet_points",
        "power_pellet_points",
        "ghost_points",
        "_travel_direction",
        "_requested_direction",
        "_step_accumulator_ms",
        "_remaining_consumables",
        "_score",
        "_score_popups",
        "_frozen",
        "_step_now_ms",
        "_wall_flash_white",
        "_wall_sprites",
        "all_sprites",
        "consumables",
    )

    def __init__(
        self,
        layout: LevelLayout,
        catalog: Assets,
        render_config: WorldRenderConfig,
        initial_score: int = 0,
        level_number: int = 1,
        pellet_points: int | None = None,
        power_pellet_points: int | None = None,
        ghost_points: int | None = None,
    ) -> None:
        self._layout: LevelLayout = layout
        self._catalog: Assets = catalog
        self._render_config: WorldRenderConfig = render_config
        self._level_number: int = level_number
        self.pellet_points = (
            self.PELLET_POINTS if pellet_points is None else pellet_points
        )
        self.power_pellet_points = (
            self.POWER_PELLET_POINTS
            if power_pellet_points is None
            else power_pellet_points
        )
        self.ghost_points = (
            self.GHOST_POINTS if ghost_points is None else ghost_points
        )
        self.all_sprites: LayeredUpdates[Sprite] = LayeredUpdates()
        self.consumables: Group[PelletEntity] = Group()
        self._remaining_consumables: set[CellPos] = set(layout.pellet_cells)
        self._remaining_consumables.update(layout.power_pellet_cells)
        self._player: PlayerEntity | None = None
        self._ghosts: dict[GhostKind, GhostEntity] = {}
        self._ghost_home: dict[GhostKind, CellPos] = {}
        self._ghost_respawn_at_ms: dict[GhostKind, int] = {}
        self._frightened_until_ms: int = 0
        self._fruit: PelletEntity | None = None
        self._fruit_spawn_index: int = 0
        self._fruit_kill_at_ms: int = 0
        self._score: int = initial_score
        self._score_popups: list[ScorePopup] = []
        self._frozen: bool = False
        self._step_now_ms: int = 0
        self._wall_flash_white: bool = False
        self._wall_sprites: list[WallTileEntity] = []
        self._step_accumulator_ms: float = 0.0
        self._travel_direction: Direction = self.DEFAULT_TRAVEL_DIRECTION
        self._requested_direction: Direction | None = None
        _spawn_from_layout(self)

    @property
    def score(self) -> int:
        """Return current score."""
        return self._score

    @property
    def all_consumables_cleared(self) -> bool:
        """Return True when no pellets or power pellets remain on the maze."""
        return not self._remaining_consumables

    @property
    def is_frozen(self) -> bool:
        """Return True when movement and input are paused."""
        return self._frozen

    @property
    def player_is_dying(self) -> bool:
        """Return True while Pac-Man death animation is active."""
        return self._player is not None and self._player.is_dying

    @property
    def player_death_finished(self) -> bool:
        """Return True once Pac-Man death animation has completed."""
        return self._player is not None and self._player.death_finished

    @property
    def level_fruit_surface(self) -> Surface | None:
        """Return HUD fruit sprite for the active level."""
        kind = fruit_for_level(self._level_number)
        fruit = self._catalog.fruits.get(kind)
        return None if fruit is None else fruit.surface

    @property
    def score_popups(self) -> tuple[ScorePopup, ...]:
        """Return active floating score labels."""
        return tuple(self._score_popups)

    def set_wall_flash(self, white: bool) -> None:
        """Toggle wall tiles between blue and white maze sprites."""
        if self._wall_flash_white == white:
            return
        self._wall_flash_white = white
        for wall in self._wall_sprites:
            wall.set_flash_white(white)

    def freeze_gameplay(self) -> None:
        """Pause gameplay."""
        self._frozen = True
        self._requested_direction = None
        self._step_accumulator_ms = 0.0
        self._sync_visual_centers()

    def unfreeze_gameplay(self) -> None:
        """Resume gameplay after a pause (death, level transition, etc.)."""
        self._frozen = False

    def start_auto_movement(self) -> None:
        """Begin classic auto-walk after READY clears."""
        self._travel_direction = self.DEFAULT_TRAVEL_DIRECTION
        self._step_accumulator_ms = 0.0
        if self._player is not None:
            self._player.face(self._travel_direction)

    def update(self, dt: float, now_ms: int) -> None:
        """Update animated sprites."""
        if self._player is not None:
            self._player.update(dt, now_ms)
        for ghost in self._ghosts.values():
            if not ghost.is_hidden:
                ghost.update(dt, now_ms)
        self._apply_step_visual()
        update_frightened_state(self, now_ms)
        update_ghost_respawns(self, now_ms)
        _prune_score_popups(self, now_ms)

    def _apply_step_visual(self) -> None:
        """Lerp actor sprites between grid steps; logic stays on cell."""
        if self._frozen:
            return
        t = min(1.0, self._step_accumulator_ms / self.PLAYER_STEP_MS)
        if self._player is not None:
            self._player.apply_visual_lerp(t)
        for ghost in self._ghosts.values():
            if not ghost.is_hidden:
                ghost.apply_visual_lerp(t)

    def draw(self, surface: Surface) -> None:
        """Draw all sprites once in z-layer order."""
        self.all_sprites.draw(surface)

    def respawn_player(self) -> None:
        """Move Pac-Man back to the level spawn after losing a life."""
        if self._player is None:
            return
        spawn = self._layout.player_spawn
        center = cell_center(self._render_config, spawn)
        self._player.reset_after_death(spawn, center)

    def respawn_ghosts(self) -> None:
        """Return every ghost to its home cell after losing a life."""
        self._ghost_respawn_at_ms.clear()
        self._frightened_until_ms = 0
        for kind, ghost in self._ghosts.items():
            home = self._ghost_home[kind]
            center = cell_center(self._render_config, home)
            ghost.respawn_at(home, center)
            self.all_sprites.add(ghost, layer=ghost.layer)

    def reset_fruit_spawns(self) -> None:
        """Clear bonus-fruit state so spawn times re-evaluate from level start."""
        _kill_fruit(self)
        self._fruit_spawn_index = 0

    def teardown(self) -> None:
        """Kill all sprites and empty all groups."""
        for sprite in list(self.all_sprites.sprites()):
            sprite.kill()
        self.all_sprites.empty()
        self.consumables.empty()
        self._player = None
        self._ghosts.clear()
        self._ghost_home.clear()
        self._ghost_respawn_at_ms.clear()
        self._fruit = None
        self._remaining_consumables.clear()
        self._score_popups.clear()
        self._frozen = False
        self._wall_flash_white = False
        self._wall_sprites.clear()
        self._frightened_until_ms = 0
        self._fruit_spawn_index = 0
        self._fruit_kill_at_ms = 0

    def _consume_current_cell(self) -> None:
        if self._player is None:
            return

        hits = spritecollide(
            self._player,
            self.consumables,
            dokill=False,
            collided=pygame.sprite.collide_rect,
        )
        for sprite in hits:
            if not isinstance(sprite, PelletEntity):
                continue
            pellet = sprite
            if pellet.cell not in self._remaining_consumables:
                continue
            self._remaining_consumables.remove(pellet.cell)
            self._score += pellet.points
            if pellet.cell in self._layout.power_pellet_cells:
                activate_frightened_mode(self)
            pellet.kill()

        _collect_fruit(self)

    def _sync_visual_centers(self) -> None:
        """Snap visual interpolation when movement pauses."""
        if self._player is not None:
            self._player.begin_step()
        for ghost in self._ghosts.values():
            if not ghost.is_hidden:
                ghost.begin_step()


# [transition] module helpers extracted from wehan GameState
# (request_turn, update_player_movement, _spawn_from_layout)


def _spawn_from_layout(world: GameWorld) -> None:
    cfg = world._render_config
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
                pos,
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
        world.consumables.add(pellet)

    for pos in world._layout.power_pellet_cells:
        pellet = PelletEntity(
            world._catalog.power_pellet_surface,
            pos,
            cell_center(cfg, pos),
            world.power_pellet_points,
        )
        world.all_sprites.add(pellet, layer=pellet.layer)
        world.consumables.add(pellet)

    for kind, cell in world._layout.ghost_spawns:
        ghost = GhostEntity(
            kind,
            world._catalog.ghosts.by_kind[kind],
            world._catalog.ghosts.frightened,
            cell,
            cell_center(cfg, cell),
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
    """Buffer a direction change from player input."""
    if world._frozen or world.player_is_dying:
        return
    world._requested_direction = direction


def _move_player(world: GameWorld, direction: Direction) -> bool:
    if world._player is None or world._player.is_dying:
        return False

    row_delta, col_delta = direction_delta(direction)
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
    if world._requested_direction is not None:
        if _move_player(world, world._requested_direction):
            world._travel_direction = world._requested_direction
            return
    _move_player(world, world._travel_direction)


def _begin_visual_step(world: GameWorld) -> None:
    if world._player is not None:
        world._player.begin_step()
    for ghost in world._ghosts.values():
        if not ghost.is_hidden:
            ghost.begin_step()


def update_player_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance player on grid at fixed speed while PLAYING."""
    if world._frozen or world._player is None or world._player.is_dying:
        return
    world._step_now_ms = now_ms
    world._step_accumulator_ms += dt_s * 1000.0
    while world._step_accumulator_ms >= world.PLAYER_STEP_MS:
        world._step_accumulator_ms -= world.PLAYER_STEP_MS
        _begin_visual_step(world)
        _auto_step(world)
        move_ghosts(world)
        resolve_actor_collisions(world)


def spawn_fruit(world: GameWorld, now_ms: int) -> None:
    _kill_fruit(world)
    kind = fruit_for_level(world._level_number)
    fruit_sprite = world._catalog.fruits.get(kind)
    if fruit_sprite is None:
        return
    cell = world._layout.fruit_spawn
    world._fruit = PelletEntity(
        fruit_sprite.surface,
        cell,
        cell_center(world._render_config, cell),
        FRUIT_POINTS[kind],
    )
    world.all_sprites.add(world._fruit, layer=world._fruit.layer)
    world._fruit_kill_at_ms = now_ms + FRUIT_VISIBLE_DURATION_S * 1000


def _kill_fruit(world: GameWorld) -> None:
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
    """Spawn bonus fruit at configured level-play seconds."""
    spawn_times = spawn_seconds_for_level(world._level_number)
    while (
        world._fruit_spawn_index < len(spawn_times)
        and level_elapsed_s >= spawn_times[world._fruit_spawn_index]
    ):
        spawn_fruit(world, now_ms)
        world._fruit_spawn_index += 1
    if world._fruit is not None and now_ms >= world._fruit_kill_at_ms:
        _kill_fruit(world)


def _collect_fruit(world: GameWorld) -> None:
    if world._player is None or world._fruit is None:
        return
    if world._player.cell != world._fruit.cell:
        return
    points = world._fruit.points
    fruit_center_px = world._fruit.center
    world._score += points
    tile_px = world._render_config.tile_px
    popup_center = (
        fruit_center_px[0],
        fruit_center_px[1] + tile_px // 2 + 2,
    )
    expires_at_ms = pygame.time.get_ticks() + world.SCORE_POPUP_DURATION_MS
    world._score_popups.append(
        ScorePopup(
            center=popup_center,
            points=points,
            expires_at_ms=expires_at_ms,
        )
    )
    _kill_fruit(world)


def _prune_score_popups(world: GameWorld, now_ms: int) -> None:
    if not world._score_popups:
        return
    world._score_popups = [
        popup for popup in world._score_popups if now_ms < popup.expires_at_ms
    ]
