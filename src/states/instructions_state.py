from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import BACK_KEYS, GameState, StateEnterData
from states.text import ArcadeTextColor

INSTRUCTION_ROWS: tuple[tuple[str, str], ...] = (
    ("MOVE", "WASD / ARROWS"),
    ("PAUSE", "ESC"),
    ("START", "ENTER"),
    ("BACK", "ESC"),
)


class InstructionsState(GameState):
    """Static instructions screen."""

    TITLE_Y = 300
    ROW_START_Y = 420
    ROW_SCALE = 3
    TITLE_SCALE = 4
    FOOTER_SCALE = 2
    ROW_GAP = 12
    FOOTER_GAP = 48

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Enter instructions view."""

    def leave(self, context: GameContext) -> None:
        """Leave instructions view."""

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
        """Hide menu while instructions screen is active."""
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw aligned control legend."""
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "INSTRUCTIONS",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=self.TITLE_SCALE,
        )

        font = text.font(ArcadeTextColor.WHITE, scale=self.ROW_SCALE)
        row_step = font.advance() + self.ROW_GAP
        for index, (label, value) in enumerate(INSTRUCTION_ROWS):
            y = self.ROW_START_Y + index * row_step
            text.draw_arcade_two_column_row(
                surface,
                label,
                value,
                y,
                color=ArcadeTextColor.WHITE,
                scale=self.ROW_SCALE,
                label_chars=6,
                gap_chars=2,
            )

        footer_y = (
            self.ROW_START_Y
            + len(INSTRUCTION_ROWS) * row_step
            + self.FOOTER_GAP
        )
        text.draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            footer_y,
            ArcadeTextColor.ROSE,
            scale=self.FOOTER_SCALE,
        )
