from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor

from managers.highscore_manager import HighscoreManager


class GameOverState(GameState):
    """End screen for score display, initials entry, and save."""

    TITLE_Y: ClassVar[int] = 280
    SCORE_Y: ClassVar[int] = 370
    PROMPT_Y: ClassVar[int] = 470
    NAME_Y: ClassVar[int] = 540
    TITLE_SCALE: ClassVar[int] = 5
    SCORE_SCALE: ClassVar[int] = 4
    PROMPT_SCALE: ClassVar[int] = 2
    NAME_SCALE: ClassVar[int] = 3

    def __init__(self) -> None:
        """Initialize empty initials buffer and default outcome."""
        self._name = ""
        self._score = 0
        self._won = False

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Read enter payload and reset initials entry.

        Args:
            context: Shared game context (unused).
            enter_data: Optional dict with score and won flag.
        """
        self._name = ""
        self._won = False
        self._score = 0
        if enter_data is not None:
            score = enter_data.get("score", 0)
            self._score = score if isinstance(score, int) else 0
            self._won = bool(enter_data.get("won", False))

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
        """Capture initials and save the score on Enter.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for high scores and scene changes.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_RETURN:
                name = HighscoreManager.clean_name(self._name or "AAA")
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
                and len(self._name) < 10
            ):
                self._name += char

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No-op; screen has no simulation.

        Args:
            dt: Elapsed seconds since the last frame (unused).
            now_ms: Monotonic clock in milliseconds (unused).
            context: Shared game context (unused).
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
            "ENTER NAME - RETURN TO SAVE",
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
