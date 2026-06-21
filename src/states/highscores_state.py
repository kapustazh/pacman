from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StatePayload
from states.text import (
    ArcadeTextColor,
    draw_centered_arcade_text,
    draw_screen_backdrop,
)

TITLE_Y = 300
BODY_Y = 480
FOOTER_Y = 620


class HighscoresState(GameState):
    """Placeholder high scores screen."""

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
    ) -> None:
        """Enter high scores view."""

    def leave(self, context: GameContext) -> None:
        """Leave high scores view."""

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Return to menu on back input."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_BACKSPACE,
            ):
                context.scene_manager.pop()
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No simulation."""

    def covers_previous_layers(self) -> bool:
        """Hide menu while high scores screen is active."""
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw placeholder high scores."""
        draw_screen_backdrop(surface)

        draw_centered_arcade_text(
            surface,
            "HIGH SCORES",
            TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=4,
        )
        draw_centered_arcade_text(
            surface,
            "NO SCORES YET",
            BODY_Y,
            ArcadeTextColor.WHITE,
            scale=3,
        )
        draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            FOOTER_Y,
            ArcadeTextColor.ROSE,
            scale=2,
        )
