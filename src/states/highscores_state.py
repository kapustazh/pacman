from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import BACK_KEYS, GameState, StateEnterData
from states.text import ArcadeTextColor


class HighscoresState(GameState):
    """High scores screen reading from HighscoreManager."""

    TITLE_Y = 200
    LIST_Y = 340
    ROW_STEP = 48
    FOOTER_Y = 920
    TITLE_SCALE = 4
    ROW_SCALE = 2
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
            if event.type == pygame.KEYDOWN and event.key in BACK_KEYS:
                context.scene_manager.pop()
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No simulation."""

    def covers_previous_layers(self) -> bool:
        """Hide menu while high scores screen is active."""
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw title, top-10 rows, and back prompt."""
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "HIGH SCORES",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=self.TITLE_SCALE,
        )

        entries = context.highscores.highscores
        if not entries:
            text.draw_centered_arcade_text(
                surface,
                "NO SCORES YET",
                self.LIST_Y,
                ArcadeTextColor.WHITE,
                scale=self.ROW_SCALE,
            )
        else:
            for index, entry in enumerate(entries[:10]):
                label = f"{index + 1:>2} {entry['name']}"
                value = f"{int(entry['score']):06d}"
                text.draw_arcade_two_column_row(
                    surface,
                    label,
                    value,
                    self.LIST_Y + index * self.ROW_STEP,
                    color=ArcadeTextColor.WHITE,
                    scale=self.ROW_SCALE,
                    label_chars=14,
                    gap_chars=2,
                )

        text.draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            self.FOOTER_Y,
            ArcadeTextColor.ROSE,
            scale=self.FOOTER_SCALE,
        )
