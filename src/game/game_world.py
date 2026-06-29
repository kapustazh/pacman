from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.sprite import Group, LayeredUpdates, spritecollide
from pygame.surface import Surface

from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.fruit_schedule import fruit_for_level
from game.level import CellPos, LevelLayout
from game.render_config import WorldRenderConfig
from game.world_fruit import ScorePopup, collect_fruit, prune_score_popups
from game.world_ghosts import (
    activate_frightened_mode,
    update_frightened_state,
    update_ghost_respawns,
)
from game.world_spawn import cell_center, spawn_from_layout
from sprites.assets import Assets
from sprites.sprite_types import Direction, GhostKind

__all__ = ("GameWorld", "ScorePopup")


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
        self.consumables: Group = Group()
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
        spawn_from_layout(self)

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
        update_frightened_state(self, now_ms)
        update_ghost_respawns(self, now_ms)
        prune_score_popups(self, now_ms)

    def draw(self, surface: Surface) -> None:
        """Draw all sprites once in z-layer order."""
        self.all_sprites.draw(surface)

    def respawn_player(self) -> None:
        """Move Pac-Man back to the level spawn after losing a life."""
        if self._player is None:
            return
        spawn = self._layout.player_spawn
        self._player.reset_after_death(spawn, cell_center(self, spawn))

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

        collect_fruit(self)
