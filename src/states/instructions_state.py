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
    """Static screen listing game controls."""

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
        """No-op; scene has no setup work.

        Args:
            context: Shared game context (unused).
            enter_data: Optional payload from the previous scene (unused).
        """

    def leave(self, context: GameContext) -> None:
        """No-op; scene has no teardown work.

        Args:
            context: Shared game context (unused).
        """

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Pop back to the previous scene on back keys.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for scene transitions.
        """
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in BACK_KEYS:
                context.scene_manager.pop()
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No-op; screen has no simulation.

        Args:
            dt: Elapsed seconds since the last frame (unused).
            now_ms: Monotonic clock in milliseconds (unused).
            context: Shared game context (unused).
        """

    def covers_previous_layers(self) -> bool:
        """Hide the menu while this screen is active.

        Returns:
            Always True so the menu is not drawn underneath.
        """
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw the title, control rows, and return prompt.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "INSTRUCTIONS",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=self.TITLE_SCALE,
        )

        row_step = text.advance(self.ROW_SCALE) + self.ROW_GAP
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
