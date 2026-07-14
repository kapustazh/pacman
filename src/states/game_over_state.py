from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState
from states.text import ArcadeTextColor


class GameOverState(GameState):
    """End screen for score display, initials entry, and save."""

    TITLE_Y: ClassVar[int] = 280
    SCORE_Y: ClassVar[int] = 370
    PROMPT_Y: ClassVar[int] = 470
    NAME_Y: ClassVar[int] = 540
    HINT_Y: ClassVar[int] = 580
    TITLE_SCALE: ClassVar[int] = 5
    SCORE_SCALE: ClassVar[int] = 4
    PROMPT_SCALE: ClassVar[int] = 2
    HINT_SCALE: ClassVar[int] = 2
    NAME_SCALE: ClassVar[int] = 3
    MAX_NAME_LENGTH: ClassVar[int] = 10
    DEFAULT_NAME: ClassVar[str] = "GUEST"
    MAX_NAME_Y: ClassVar[int] = 620

    def __init__(self, score: int = 0, won: bool = False) -> None:
        """Initialize the end screen with the final outcome.

        Args:
            score: Final score to display and save.
            won: True when the player cleared all levels.
        """
        self._name = ""
        self._score = score
        self._won = won

    def enter(self, context: GameContext) -> None:
        """Clear the initials buffer when the scene becomes active.

        Args:
            context: Shared game context.
        """
        self._name = ""

    def leave(self, context: GameContext) -> None:
        """No-op; scene has no teardown work.

        Args:
            context: Shared game context.
        """

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Capture initials and save the score on Enter.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for high scores and scene changes.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_RETURN:
                name = context.highscores._clean_name(
                    self._name or self.DEFAULT_NAME
                )
                context.highscores.add_score(name, self._score)
                from states.menu_state import MenuState

                context.scene_manager.change(MenuState())
                return
            if event.key == pygame.K_BACKSPACE:
                self._name = self._name[:-1]
                return
            char = event.unicode
            if (
                char
                and (char.isalnum() or char == " ")
                and len(self._name) < self.MAX_NAME_LENGTH
            ):
                self._name += char

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No-op; screen has no simulation.

        Args:
            dt: Elapsed seconds since the last frame.
            now_ms: Monotonic clock in milliseconds.
            context: Shared game context.
        """

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw outcome title, score, and initials prompt.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        text = context.text
        title = "YOU WIN!" if self._won else "GAME OVER"
        title_color = (
            ArcadeTextColor.YELLOW if self._won else ArcadeTextColor.RED
        )
        text.draw_centered_arcade_text(
            surface,
            title,
            self.TITLE_Y,
            title_color,
            self.TITLE_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            f"SCORE {self._score:06d}",
            self.SCORE_Y,
            ArcadeTextColor.GOLD,
            self.SCORE_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            "ENTER YOUR NAME",
            self.PROMPT_Y,
            ArcadeTextColor.WHITE,
            self.PROMPT_SCALE,
        )
        display = self._name if self._name else "-"
        text.draw_centered_arcade_text(
            surface,
            display,
            self.NAME_Y,
            ArcadeTextColor.YELLOW,
            self.NAME_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            "A-Z 0-9 SPACE",
            self.HINT_Y,
            ArcadeTextColor.WHITE,
            self.HINT_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            "MAX 10 CHARACTERS",
            self.MAX_NAME_Y,
            ArcadeTextColor.WHITE,
            self.HINT_SCALE,
        )
