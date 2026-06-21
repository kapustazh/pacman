from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StatePayload
from states.text import (
    ArcadeFont,
    ArcadeTextColor,
    draw_arcade_two_column_row,
    draw_centered_arcade_text,
    draw_screen_backdrop,
)

INSTRUCTION_ROWS: tuple[tuple[str, str], ...] = (
    ("MOVE", "WASD / ARROWS"),
    ("PAUSE", "ESC"),
    ("START", "ENTER"),
    ("BACK", "ESC"),
)

TITLE_Y = 300
ROW_START_Y = 420
ROW_SCALE = 3
TITLE_SCALE = 4
FOOTER_SCALE = 2
ROW_GAP = 12


class InstructionsState(GameState):
    """Static instructions screen."""

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
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
        """Hide menu while instructions screen is active."""
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw aligned control legend."""
        draw_screen_backdrop(surface)

        draw_centered_arcade_text(
            surface,
            "INSTRUCTIONS",
            TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=TITLE_SCALE,
        )

        font = ArcadeFont(ArcadeTextColor.WHITE, scale=ROW_SCALE)
        row_step = font.line_height() + ROW_GAP
        for index, (label, value) in enumerate(INSTRUCTION_ROWS):
            y = ROW_START_Y + index * row_step
            draw_arcade_two_column_row(
                surface,
                label,
                value,
                y,
                color=ArcadeTextColor.WHITE,
                scale=ROW_SCALE,
                label_chars=6,
                gap_chars=2,
            )

        footer_y = ROW_START_Y + len(INSTRUCTION_ROWS) * row_step + 48
        draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            footer_y,
            ArcadeTextColor.ROSE,
            scale=FOOTER_SCALE,
        )
