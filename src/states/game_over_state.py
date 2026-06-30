from __future__ import annotations

from enum import Enum, auto
from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import StateEnterData
from states.selectable_menu_state import MenuEntry, SelectableMenuState
from states.text import ArcadeTextColor

from managers.highscore_manager import HighscoreManager


class _GameOverPhase(Enum):
    ENTER_INITIALS = auto()
    SAVED = auto()
    MENU = auto()


class GameOverState(SelectableMenuState):
    """Game-over scene: initials entry, then replay/menu/exit."""

    TITLE_Y: ClassVar[int] = 280
    SCORE_Y: ClassVar[int] = 370
    PROMPT_Y: ClassVar[int] = 470
    NAME_Y: ClassVar[int] = 540
    MENU_START_Y: ClassVar[int] = 660
    TITLE_SCALE: ClassVar[int] = 5
    SCORE_SCALE: ClassVar[int] = 4
    PROMPT_SCALE: ClassVar[int] = 2
    NAME_SCALE: ClassVar[int] = 3
    OPTIONS: ClassVar[tuple[MenuEntry, ...]] = (
        MenuEntry("REPLAY", "replay"),
        MenuEntry("MAIN MENU", "menu"),
        MenuEntry("EXIT", "exit"),
    )

    __slots__ = ("_name", "_phase", "_score")

    def __init__(self) -> None:
        self._name = ""
        self._phase = _GameOverPhase.ENTER_INITIALS
        self._score = 0
        super().__init__(
            entries=self.OPTIONS,
            menu_start_y=self.MENU_START_Y,
            action_handlers={
                "replay": self._replay,
                "menu": self._main_menu,
                "exit": self._exit_game,
            },
            shortcuts={
                pygame.K_r: (0, "replay"),
                pygame.K_m: (1, "menu"),
            },
        )

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Apply enter_data and reset to initials phase."""
        super().enter(context, enter_data)
        self._name = ""
        self._phase = _GameOverPhase.ENTER_INITIALS
        if enter_data is not None:
            score = enter_data.get("score", 0)
            self._score = score if isinstance(score, int) else 0

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Route keys to initials entry or menu navigation."""
        if self._phase == _GameOverPhase.ENTER_INITIALS:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    self._handle_initials_key(event, context)
            return
        if self._phase == _GameOverPhase.SAVED:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    self._handle_saved_key(event, context)
            return
        super().handle_events(events, context)

    def _handle_initials_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        if event.key == pygame.K_RETURN:
            name = HighscoreManager.clean_name(self._name or "AAA")
            context.highscores.add_score(name, self._score)
            self._phase = _GameOverPhase.SAVED
            return
        if event.key == pygame.K_BACKSPACE:
            self._name = self._name[:-1]
            return
        char = event.unicode
        if char and (char.isalnum() or char == " ") and len(self._name) < 10:
            self._name += char

    def _handle_saved_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        if event.key == pygame.K_m:
            self._phase = _GameOverPhase.MENU
            return
        if event.key == pygame.K_r:
            self._replay(context)

    def draw_header(self, surface: Surface, context: GameContext) -> None:
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "GAME OVER",
            self.TITLE_Y,
            ArcadeTextColor.RED,
            self.TITLE_SCALE,
        )
        text.draw_centered_arcade_text(
            surface,
            f"SCORE {self._score:06d}",
            self.SCORE_Y,
            ArcadeTextColor.GOLD,
            self.SCORE_SCALE,
        )
        if self._phase == _GameOverPhase.ENTER_INITIALS:
            text.draw_centered_arcade_text(
                surface,
                "ENTER NAME - RETURN TO SAVE",
                self.PROMPT_Y,
                ArcadeTextColor.WHITE,
                self.PROMPT_SCALE,
            )
            display = self._name if self._name else "AAA"
            text.draw_centered_arcade_text(
                surface,
                display,
                self.NAME_Y,
                ArcadeTextColor.YELLOW,
                self.NAME_SCALE,
            )
        elif self._phase == _GameOverPhase.SAVED:
            text.draw_centered_arcade_text(
                surface,
                "SCORE SAVED",
                self.PROMPT_Y,
                ArcadeTextColor.WHITE,
                self.PROMPT_SCALE,
            )
            text.draw_centered_arcade_text(
                surface,
                "M FOR MENU  R TO REPLAY",
                self.NAME_Y,
                ArcadeTextColor.YELLOW,
                self.NAME_SCALE,
            )

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw header; menu rows only after explicit menu request."""
        self.draw_header(surface, context)
        if self._phase == _GameOverPhase.MENU:
            self.draw_options(surface, context)

    def _replay(self, context: GameContext) -> None:
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _main_menu(self, context: GameContext) -> None:
        from states.menu_state import MenuState

        context.scene_manager.change(MenuState())

    def _exit_game(self, context: GameContext) -> None:
        context.scene_manager.request_shutdown()
