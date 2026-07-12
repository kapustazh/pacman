from __future__ import annotations
from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import BACK_KEYS, GameState, StateEnterData
from states.text import ArcadeTextColor


class HighscoresState(GameState):
    """Screen showing the top saved scores."""

    TITLE_Y: ClassVar[int] = 200
    LIST_Y: ClassVar[int] = 340
    ROW_STEP: ClassVar[int] = 48
    FOOTER_Y: ClassVar[int] = 920
    TITLE_SCALE: ClassVar[int] = 4
    ROW_SCALE: ClassVar[int] = 2
    FOOTER_SCALE: ClassVar[int] = 2

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
        """Draw the title, score list, and return prompt.

        Args:
            surface: Destination draw target.
            context: Shared game context with high scores and text renderer.
        """
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
