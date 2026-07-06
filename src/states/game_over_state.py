from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor

from managers.highscore_manager import HighscoreManager


class GameOverState(GameState):
    """End screen: score, initials entry, then main menu."""

    TITLE_Y: ClassVar[int] = 280
    SCORE_Y: ClassVar[int] = 370
    PROMPT_Y: ClassVar[int] = 470
    NAME_Y: ClassVar[int] = 540
    TITLE_SCALE: ClassVar[int] = 5
    SCORE_SCALE: ClassVar[int] = 4
    PROMPT_SCALE: ClassVar[int] = 2
    NAME_SCALE: ClassVar[int] = 3

    def __init__(self) -> None:
        self._name = ""
        self._score = 0
        self._won = False

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Apply enter_data and reset initials entry."""
        self._name = ""
        self._won = False
        self._score = 0
        if enter_data is not None:
            score = enter_data.get("score", 0)
            self._score = score if isinstance(score, int) else 0
            self._won = bool(enter_data.get("won", False))

    def leave(self, context: GameContext) -> None:
        """Leave end screen."""

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Capture initials; save and return to main menu on Enter."""
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
        """No simulation."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw title, score, and initials prompt."""
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
