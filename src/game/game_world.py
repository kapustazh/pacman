from __future__ import annotations

import pygame
from pygame.sprite import Group, LayeredUpdates, spritecollide
from pygame.surface import Surface

from entities.entity_sprite import EntitySprite
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.entity_factory import EntityFactory
from game.level import CellPos, CellType, LevelLayout
from sprites.sprite_types import Direction

PLAYER_STEP_MS = 120
DEFAULT_TRAVEL_DIRECTION = Direction.RIGHT


class GameWorld:
    """Owns runtime gameplay entities, groups, and collision state."""

    __slots__ = (
        "_factory",
        "_layout",
        "_player",
        "_player_sprite",
        "_travel_direction",
        "_requested_direction",
        "_step_accumulator_ms",
        "_remaining_consumables",
        "_score",
        "_frozen",
        "all_sprites",
        "consumables",
    )

    def __init__(
        self,
        layout: LevelLayout,
        factory: EntityFactory,
        initial_score: int = 0,
    ) -> None:
        self._layout: LevelLayout = layout
        self._factory: EntityFactory = factory
        self.all_sprites: LayeredUpdates = LayeredUpdates()
        self.consumables: Group[EntitySprite] = Group()
        self._remaining_consumables: set[CellPos] = set(layout.pellet_cells)
        self._remaining_consumables.update(layout.power_pellet_cells)
        self._player: PlayerEntity | None = None
        self._player_sprite: EntitySprite | None = None
        self._score: int = initial_score
        self._frozen: bool = False
        self._step_accumulator_ms: float = 0.0
        self._travel_direction: Direction = DEFAULT_TRAVEL_DIRECTION
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

        self._player.move_to(target, self._factory.cell_center(target))
        if self._player_sprite is not None:
            self._player_sprite.sync_from_entity()
        self._consume_current_cell()
        return True

    def start_auto_movement(self) -> None:
        """Begin classic auto-walk after READY clears."""
        self._travel_direction = DEFAULT_TRAVEL_DIRECTION
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
        while self._step_accumulator_ms >= PLAYER_STEP_MS:
            self._step_accumulator_ms -= PLAYER_STEP_MS
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
        self._player_sprite = None
        self._remaining_consumables.clear()
        self._frozen = False

    def _spawn_from_layout(self) -> None:
        for row_index, row in enumerate(self._layout.cells):
            for col_index, cell_type in enumerate(row):
                pos = CellPos(row_index, col_index)
                if cell_type == CellType.WALL:
                    self._register_wall(self._factory.create_wall(pos))

        for pos in self._layout.pellet_cells:
            self._register_consumable(self._factory.create_pellet(pos))

        for pos in self._layout.power_pellet_cells:
            self._register_consumable(self._factory.create_power_pellet(pos))

        self._player = self._factory.create_player(self._layout.player_spawn)
        self._player_sprite = EntitySprite(self._player)
        self.all_sprites.add(self._player_sprite, layer=self._player.layer)

    def _register_wall(self, wall: WallTileEntity) -> None:
        sprite = EntitySprite(wall)
        self.all_sprites.add(sprite, layer=wall.layer)

    def _register_consumable(self, pellet: PelletEntity) -> None:
        sprite = EntitySprite(pellet)
        self.all_sprites.add(sprite, layer=pellet.layer)
        self.consumables.add(sprite)

    def _consume_current_cell(self) -> None:
        if self._player_sprite is None:
            return

        hits = spritecollide(
            self._player_sprite,
            self.consumables,
            dokill=False,
            collided=pygame.sprite.collide_rect,
        )
        for hit in hits:
            entity = hit.entity
            if not isinstance(entity, PelletEntity):
                continue
            if entity.cell not in self._remaining_consumables:
                continue
            self._remaining_consumables.remove(entity.cell)
            self._score += entity.points
            hit.kill()

    def _direction_delta(self, direction: Direction) -> tuple[int, int]:
        if direction == Direction.UP:
            return (-1, 0)
        if direction == Direction.DOWN:
            return (1, 0)
        if direction == Direction.LEFT:
            return (0, -1)
        return (0, 1)
