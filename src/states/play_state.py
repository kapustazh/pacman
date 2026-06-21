from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StatePayload
from game.entity_factory import EntityFactory
from game.game_world import GameWorld
from game.level import load_smoke_level
from game.render_config import DEFAULT_RENDER_CONFIG
from sprites.types import Direction


class PlayState(GameState):
    """Gameplay scene backed by GameWorld."""

    def __init__(self) -> None:
        self._world: GameWorld | None = None

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
    ) -> None:
        """Create a fresh world from smoke level boilerplate."""
        catalog = context.resources.get_asset_catalog()
        # DEMO: smoke level only; TODO: swap for real loader.
        layout = load_smoke_level()
        factory = EntityFactory(catalog, DEFAULT_RENDER_CONFIG)
        self._world = GameWorld(layout, factory)

    def leave(self, context: GameContext) -> None:
        """Tear down world resources."""
        if self._world is not None:
            self._world.teardown()
            self._world = None

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Route play input to world or scene transitions."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                from states.pause_state import PauseState

                context.scene_manager.push(PauseState())
                return
            direction = self._event_direction(event)
            if direction is not None and self._world is not None:
                self._world.move_player(direction)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Update world animation."""
        if self._world is not None:
            self._world.update(dt, now_ms)

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw world."""
        if self._world is not None:
            self._world.draw(surface)

    def _event_direction(
        self,
        event: pygame.event.Event,
    ) -> Direction | None:
        if event.key in (pygame.K_UP, pygame.K_w):
            return Direction.UP
        if event.key in (pygame.K_DOWN, pygame.K_s):
            return Direction.DOWN
        if event.key in (pygame.K_LEFT, pygame.K_a):
            return Direction.LEFT
        if event.key in (pygame.K_RIGHT, pygame.K_d):
            return Direction.RIGHT
        return None
