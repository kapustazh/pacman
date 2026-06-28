from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.sprite import Group, LayeredUpdates, spritecollide
from pygame.surface import Surface

from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.level import CellPos, CellType, LevelLayout
from game.render_config import WorldRenderConfig
from game.wall_tile_picker import pick
from sprites.assets import Assets
from sprites.sprite_types import Direction


class GameWorld:
    """Owns runtime gameplay entities, groups, and collision state."""

    PLAYER_STEP_MS: ClassVar[int] = 120
    DEFAULT_TRAVEL_DIRECTION: ClassVar[Direction] = Direction.RIGHT
    PELLET_POINTS: ClassVar[int] = 10
    POWER_PELLET_POINTS: ClassVar[int] = 50
    _DIRECTION_DELTA: ClassVar[dict[Direction, tuple[int, int]]] = {
        Direction.UP: (-1, 0),
        Direction.DOWN: (1, 0),
        Direction.LEFT: (0, -1),
        Direction.RIGHT: (0, 1),
    }

    __slots__ = (
        "_catalog",
        "_layout",
        "_player",
        "_render_config",
        "_travel_direction",
        "_requested_direction",
        "_step_accumulator_ms",
        "_remaining_consumables",
        "_score",
        "_frozen",
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
    ) -> None:
        self._layout: LevelLayout = layout
        self._catalog: Assets = catalog
        self._render_config: WorldRenderConfig = render_config
        self.all_sprites: LayeredUpdates = LayeredUpdates()
        self.consumables: Group[PelletEntity] = Group()
        self._remaining_consumables: set[CellPos] = set(layout.pellet_cells)
        self._remaining_consumables.update(layout.power_pellet_cells)
        self._player: PlayerEntity | None = None
        self._score: int = initial_score
        self._frozen: bool = False
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

    def set_wall_flash(self, white: bool) -> None:
        """Toggle wall tiles between blue and white maze sprites."""
        if self._wall_flash_white == white:
            return
        self._wall_flash_white = white
        for wall in self._wall_sprites:
            wall.set_flash_white(white)

    def freeze_gameplay(self) -> None:
        """Stop movement and buffered turns while sprite animation continues."""
        self._frozen = True
        self._requested_direction = None
        self._step_accumulator_ms = 0.0

    def move_player(self, direction: Direction) -> bool:
        """Move player one grid step if target cell is walkable."""
        if self._player is None:
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
        return True

    def start_auto_movement(self) -> None:
        """Begin classic auto-walk after READY clears."""
        self._travel_direction = self.DEFAULT_TRAVEL_DIRECTION
        self._step_accumulator_ms = 0.0
        if self._player is not None:
            self._player.face(self._travel_direction)

    def request_turn(self, direction: Direction) -> None:
        """Buffer a direction change from player input."""
        if self._frozen:
            return
        self._requested_direction = direction

    def update_player_movement(self, dt_s: float) -> None:
        """Advance player on grid at fixed speed while PLAYING."""
        if self._frozen or self._player is None:
            return
        self._step_accumulator_ms += dt_s * 1000.0
        while self._step_accumulator_ms >= self.PLAYER_STEP_MS:
            self._step_accumulator_ms -= self.PLAYER_STEP_MS
            self._auto_step()

    def _auto_step(self) -> None:
        """Try buffered turn first, else keep walking current direction."""
        if self._requested_direction is not None:
            if self.move_player(self._requested_direction):
                self._travel_direction = self._requested_direction
                return
        self.move_player(self._travel_direction)

    def update(self, dt: float, now_ms: int) -> None:
        """Update all sprites."""
        self.all_sprites.update(dt, now_ms)

    def draw(self, surface: Surface) -> None:
        """Draw all sprites once in z-layer order."""
        self.all_sprites.draw(surface)

    def teardown(self) -> None:
        """Kill all sprites and empty all groups."""
        for sprite in list(self.all_sprites.sprites()):
            sprite.kill()
        self.all_sprites.empty()
        self.consumables.empty()
        self._player = None
        self._remaining_consumables.clear()
        self._frozen = False
        self._wall_flash_white = False
        self._wall_sprites.clear()

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
        )

    def _spawn_from_layout(self) -> None:
        for row_index, row in enumerate(self._layout.cells):
            for col_index, cell_type in enumerate(row):
                pos = CellPos(row_index, col_index)
                if cell_type == CellType.WALL:
                    self._register_wall(self._spawn_wall(pos))

        for pos in self._layout.pellet_cells:
            self._register_consumable(self._spawn_pellet(pos))

        for pos in self._layout.power_pellet_cells:
            self._register_consumable(self._spawn_power_pellet(pos))

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
            pellet.kill()

    def _direction_delta(self, direction: Direction) -> tuple[int, int]:
        return self._DIRECTION_DELTA[direction]
