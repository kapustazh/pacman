from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor

_BACK_KEYS = (
    pygame.K_ESCAPE,
    pygame.K_RETURN,
    pygame.K_SPACE,
    pygame.K_BACKSPACE,
)


class HighscoresState(GameState):
    """Placeholder high scores screen."""

    TITLE_Y = 300
    BODY_Y = 480
    FOOTER_Y = 620
    TITLE_SCALE = 4
    BODY_SCALE = 3
    FOOTER_SCALE = 2

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
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
            if event.type == pygame.KEYDOWN and event.key in _BACK_KEYS:
                context.scene_manager.pop()
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No simulation."""

    def covers_previous_layers(self) -> bool:
        """Hide menu while high scores screen is active."""
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw placeholder high scores."""
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "HIGH SCORES",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=self.TITLE_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            "NO SCORES YET",
            self.BODY_Y,
            ArcadeTextColor.WHITE,
            scale=self.BODY_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            self.FOOTER_Y,
            ArcadeTextColor.ROSE,
            scale=self.FOOTER_SCALE,
        )
