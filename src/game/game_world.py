from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pygame
from pygame.sprite import Group, LayeredUpdates, spritecollide
from pygame.surface import Surface

from entities.fruit_entity import FruitEntity
from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.fruit_schedule import (
    FRUIT_VISIBLE_DURATION_S,
    fruit_for_level,
    spawn_seconds_for_level,
)
from game.level import CellPos, CellType, LevelLayout
from game.render_config import WorldRenderConfig
from game.wall_tile_picker import pick
from sprites.assets import Assets
from sprites.sprite_types import Direction, FRUIT_POINTS, GhostKind


@dataclass(slots=True, frozen=True)
class ScorePopup:
    """Short-lived point label shown where a fruit was eaten."""

    center: tuple[int, int]
    points: int
    expires_at_ms: int


class GameWorld:
    """Owns runtime gameplay entities, groups, and collision state."""

    PLAYER_STEP_MS: ClassVar[int] = 120
    DEFAULT_TRAVEL_DIRECTION: ClassVar[Direction] = Direction.RIGHT
    PELLET_POINTS: ClassVar[int] = 10
    POWER_PELLET_POINTS: ClassVar[int] = 50
    GHOST_POINTS: ClassVar[int] = 200
    # TODO: review frightened duration
    FRIGHTENED_DURATION_MS: ClassVar[int] = 6000
    # TODO: review ghost eaten respawn time
    GHOST_EATEN_RESPAWN_MS: ClassVar[int] = 5000
    SCORE_POPUP_DURATION_MS: ClassVar[int] = 1000
    _DIRECTION_DELTA: ClassVar[dict[Direction, tuple[int, int]]] = {
        Direction.UP: (-1, 0),
        Direction.DOWN: (1, 0),
        Direction.LEFT: (0, -1),
        Direction.RIGHT: (0, 1),
    }

    __slots__ = (
        "_catalog",
        "_fruit",
        "_fruit_despawn_at_ms",
        "_fruit_spawn_index",
        "_ghost_home",
        "_ghost_respawn_at_ms",
        "_ghosts",
        "_frightened_until_ms",
        "_layout",
        "_level_number",
        "_player",
        "_render_config",
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
    ) -> None:
        self._layout: LevelLayout = layout
        self._catalog: Assets = catalog
        self._render_config: WorldRenderConfig = render_config
        self._level_number: int = level_number
        self.all_sprites: LayeredUpdates = LayeredUpdates()
        self.consumables: Group[PelletEntity] = Group()
        self._remaining_consumables: set[CellPos] = set(layout.pellet_cells)
        self._remaining_consumables.update(layout.power_pellet_cells)
        self._player: PlayerEntity | None = None
        self._ghosts: list[GhostEntity] = []
        self._ghost_home: dict[GhostKind, CellPos] = {}
        self._ghost_respawn_at_ms: dict[GhostKind, int] = {}
        self._frightened_until_ms: int = 0
        self._fruit: FruitEntity | None = None
        self._fruit_spawn_index: int = 0
        self._fruit_despawn_at_ms: int = 0
        self._score: int = initial_score
        self._score_popups: list[ScorePopup] = []
        self._frozen: bool = False
        self._step_now_ms: int = 0
        self._wall_flash_white: bool = False
        self._wall_sprites: list[WallTileEntity] = []
        self._step_accumulator_ms: float = 0.0
        self._travel_direction: Direction = self.DEFAULT_TRAVEL_DIRECTION
        self._requested_direction: Direction | None = None
        self._spawn_from_layout()

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

    def unfreeze_gameplay(self) -> None:
        """Resume gameplay after a pause (death, level transition, etc.)."""
        self._frozen = False

    def move_player(self, direction: Direction) -> bool:
        """Move player one grid step if target cell is walkable."""
        if self._player is None or self._player.is_dying:
            return False

        row_delta, col_delta = self._direction_delta(direction)
        target = CellPos(
            self._player.cell.row + row_delta,
            self._player.cell.col + col_delta,
        )
        self._player.face(direction)
        if self._layout.is_wall(target):
            return False

        self._player.move_to(target, self._cell_center(target))
        self._consume_current_cell()
        self._resolve_actor_collisions()
        return True

    def start_auto_movement(self) -> None:
        """Begin classic auto-walk after READY clears."""
        self._travel_direction = self.DEFAULT_TRAVEL_DIRECTION
        self._step_accumulator_ms = 0.0
        if self._player is not None:
            self._player.face(self._travel_direction)

    def request_turn(self, direction: Direction) -> None:
        """Buffer a direction change from player input."""
        if self._frozen or self.player_is_dying:
            return
        self._requested_direction = direction

    def update_player_movement(self, dt_s: float, now_ms: int) -> None:
        """Advance player on grid at fixed speed while PLAYING."""
        if self._frozen or self._player is None or self._player.is_dying:
            return
        self._step_now_ms = now_ms
        self._step_accumulator_ms += dt_s * 1000.0
        while self._step_accumulator_ms >= self.PLAYER_STEP_MS:
            self._step_accumulator_ms -= self.PLAYER_STEP_MS
            self._auto_step()

    def update_fruit_spawns(self, level_elapsed_s: int, now_ms: int) -> None:
        """Spawn bonus fruit at configured level-play seconds."""
        spawn_times = spawn_seconds_for_level(self._level_number)
        while (
            self._fruit_spawn_index < len(spawn_times)
            and level_elapsed_s >= spawn_times[self._fruit_spawn_index]
        ):
            self._spawn_fruit(now_ms)
            self._fruit_spawn_index += 1
        if self._fruit is not None and now_ms >= self._fruit_despawn_at_ms:
            self._despawn_fruit()

    @property
    def score_popups(self) -> tuple[ScorePopup, ...]:
        """Return active floating score labels."""
        return tuple(self._score_popups)

    def update(self, dt: float, now_ms: int) -> None:
        """Update animated sprites."""
        if self._player is not None:
            self._player.update(dt, now_ms)
        for ghost in self._ghosts:
            if not ghost.is_hidden:
                ghost.update(dt, now_ms)
        self._update_frightened_state(now_ms)
        self._update_ghost_respawns(now_ms)
        self._prune_score_popups(now_ms)

    def draw(self, surface: Surface) -> None:
        """Draw all sprites once in z-layer order."""
        self.all_sprites.draw(surface)

    def respawn_player(self) -> None:
        """Move Pac-Man back to the level spawn after losing a life."""
        if self._player is None:
            return
        spawn = self._layout.player_spawn
        self._player.reset_after_death(spawn, self._cell_center(spawn))

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
        self._fruit_despawn_at_ms = 0

    def _cell_center(self, cell: CellPos) -> tuple[int, int]:
        """Convert grid cell to pixel center."""
        tile_px = self._render_config.tile_px
        return (
            self._render_config.origin_x + cell.col * tile_px + tile_px // 2,
            self._render_config.origin_y + cell.row * tile_px + tile_px // 2,
        )

    def _spawn_wall(self, cell: CellPos) -> WallTileEntity:
        tile_kind = pick(self._layout, cell)
        blue_surface = self._catalog.maze_tiles[tile_kind]
        white_surface = self._catalog.maze_white_tiles[tile_kind]
        return WallTileEntity(
            blue_surface,
            white_surface,
            cell,
            self._cell_center(cell),
        )

    def _spawn_pellet(self, cell: CellPos) -> PelletEntity:
        return PelletEntity(
            self._catalog.dot_surface,
            cell,
            self._cell_center(cell),
            self.PELLET_POINTS,
        )

    def _spawn_power_pellet(self, cell: CellPos) -> PelletEntity:
        return PelletEntity(
            self._catalog.power_pellet_surface,
            cell,
            self._cell_center(cell),
            self.POWER_PELLET_POINTS,
        )

    def _spawn_player(self, cell: CellPos) -> PlayerEntity:
        animations_by_direction = {
            direction: self._catalog.pacman[direction]
            for direction in Direction
        }
        return PlayerEntity(
            animations_by_direction,
            cell,
            self._cell_center(cell),
            death_animation=self._catalog.pacman_death,
        )

    def _spawn_ghost(self, kind: GhostKind, cell: CellPos) -> GhostEntity:
        return GhostEntity(
            kind,
            self._catalog.ghosts.by_kind[kind],
            self._catalog.ghosts.frightened,
            cell,
            self._cell_center(cell),
        )

    def _spawn_fruit(self, now_ms: int) -> None:
        self._despawn_fruit()
        kind = fruit_for_level(self._level_number)
        fruit_sprite = self._catalog.fruits.get(kind)
        if fruit_sprite is None:
            return
        cell = self._layout.fruit_spawn
        self._fruit = FruitEntity(
            fruit_sprite.surface,
            cell,
            self._cell_center(cell),
            FRUIT_POINTS[kind],
        )
        self.all_sprites.add(self._fruit, layer=self._fruit.layer)
        self._fruit_despawn_at_ms = now_ms + FRUIT_VISIBLE_DURATION_S * 1000

    def _despawn_fruit(self) -> None:
        if self._fruit is None:
            return
        self._fruit.kill()
        self._fruit = None
        self._fruit_despawn_at_ms = 0

    def _spawn_from_layout(self) -> None:
        self._catalog.load_ghosts()
        self._catalog.load_fruits()

        for row_index, row in enumerate(self._layout.cells):
            for col_index, cell_type in enumerate(row):
                pos = CellPos(row_index, col_index)
                if cell_type == CellType.WALL:
                    self._register_wall(self._spawn_wall(pos))

        for pos in self._layout.pellet_cells:
            self._register_consumable(self._spawn_pellet(pos))

        for pos in self._layout.power_pellet_cells:
            self._register_consumable(self._spawn_power_pellet(pos))

        for kind, cell in self._layout.ghost_spawns:
            ghost = self._spawn_ghost(kind, cell)
            self._ghosts.append(ghost)
            self._ghost_home[kind] = cell
            self.all_sprites.add(ghost, layer=ghost.layer)

        self._player = self._spawn_player(self._layout.player_spawn)
        self.all_sprites.add(self._player, layer=self._player.layer)

    def _register_wall(self, wall: WallTileEntity) -> None:
        self._wall_sprites.append(wall)
        self.all_sprites.add(wall, layer=wall.layer)

    def _register_consumable(self, pellet: PelletEntity) -> None:
        self.all_sprites.add(pellet, layer=pellet.layer)
        self.consumables.add(pellet)

    def _consume_current_cell(self) -> None:
        if self._player is None:
            return

        hits = spritecollide(
            self._player,
            self.consumables,
            dokill=False,
            collided=pygame.sprite.collide_rect,
        )
        for pellet in hits:
            if pellet.cell not in self._remaining_consumables:
                continue
            self._remaining_consumables.remove(pellet.cell)
            self._score += pellet.points
            if pellet.cell in self._layout.power_pellet_cells:
                self._activate_frightened_mode()
            pellet.kill()

        if self._fruit is not None and self._player.cell == self._fruit.cell:
            points = self._fruit.points
            center = self._fruit.center
            self._score += points
            self._spawn_score_popup(center, points)
            self._despawn_fruit()

    def _resolve_actor_collisions(self) -> None:
        if self._player is None or self._player.is_dying:
            return
        for ghost in self._ghosts:
            if ghost.is_hidden or ghost.cell != self._player.cell:
                continue
            if self._is_frightened():
                self._eat_ghost(ghost)
            else:
                self._start_player_death(self._step_now_ms)
                return

    def _start_player_death(self, now_ms: int) -> None:
        if self._player is None:
            return
        self.freeze_gameplay()
        self._player.start_death(now_ms)

    def _activate_frightened_mode(self) -> None:
        now_ms = pygame.time.get_ticks()
        self._frightened_until_ms = now_ms + self.FRIGHTENED_DURATION_MS
        for ghost in self._ghosts:
            if not ghost.is_hidden:
                ghost.set_frightened(True)

    def _is_frightened(self) -> bool:
        return pygame.time.get_ticks() < self._frightened_until_ms

    def _update_frightened_state(self, now_ms: int) -> None:
        frightened = now_ms < self._frightened_until_ms
        for ghost in self._ghosts:
            if not ghost.is_hidden:
                ghost.set_frightened(frightened)

    def _eat_ghost(self, ghost: GhostEntity) -> None:
        self._score += self.GHOST_POINTS
        ghost.hide_eaten()
        self._ghost_respawn_at_ms[ghost.kind] = (
            pygame.time.get_ticks() + self.GHOST_EATEN_RESPAWN_MS
        )

    def _update_ghost_respawns(self, now_ms: int) -> None:
        for kind, respawn_at_ms in list(self._ghost_respawn_at_ms.items()):
            if now_ms < respawn_at_ms:
                continue
            del self._ghost_respawn_at_ms[kind]
            home = self._ghost_home[kind]
            ghost = self._find_ghost(kind)
            if ghost is None:
                continue
            ghost.respawn_at(home, self._cell_center(home))
            self.all_sprites.add(ghost, layer=ghost.layer)
            if self._is_frightened():
                ghost.set_frightened(True)

    def _find_ghost(self, kind: GhostKind) -> GhostEntity | None:
        for ghost in self._ghosts:
            if ghost.kind == kind:
                return ghost
        return None

    def _spawn_score_popup(
        self,
        fruit_center: tuple[int, int],
        points: int,
    ) -> None:
        """Show classic point value beneath a collected fruit."""
        tile_px = self._render_config.tile_px
        center = (fruit_center[0], fruit_center[1] + tile_px // 2 + 2)
        expires_at_ms = pygame.time.get_ticks() + self.SCORE_POPUP_DURATION_MS
        self._score_popups.append(
            ScorePopup(
                center=center, points=points, expires_at_ms=expires_at_ms
            )
        )

    def _prune_score_popups(self, now_ms: int) -> None:
        if not self._score_popups:
            return
        self._score_popups = [
            popup
            for popup in self._score_popups
            if now_ms < popup.expires_at_ms
        ]

    def _auto_step(self) -> None:
        """Try buffered turn first, else keep walking current direction."""
        if self._requested_direction is not None:
            if self.move_player(self._requested_direction):
                self._travel_direction = self._requested_direction
                return
        self.move_player(self._travel_direction)

    def _direction_delta(self, direction: Direction) -> tuple[int, int]:
        return self._DIRECTION_DELTA[direction]
