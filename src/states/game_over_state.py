from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import StateEnterData
from states.selectable_menu_state import MenuEntry, SelectableMenuState
from states.text import ArcadeTextColor


class GameOverState(SelectableMenuState):
    """Game-over scene with arcade score display and menu."""

    TITLE_Y: ClassVar[int] = 340
    SCORE_Y: ClassVar[int] = 430
    MENU_START_Y: ClassVar[int] = 560
    TITLE_SCALE: ClassVar[int] = 5
    SCORE_SCALE: ClassVar[int] = 4
    OPTIONS: ClassVar[tuple[MenuEntry, ...]] = (
        MenuEntry("REPLAY", "replay"),
        MenuEntry("MAIN MENU", "menu"),
        MenuEntry("EXIT", "exit"),
    )

    __slots__ = ("_score",)

    def __init__(self) -> None:
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
        """Apply enter_data and reset menu selection."""
        super().enter(context, enter_data)
        if enter_data is not None:
            score = enter_data.get("score", 0)
            self._score = score if isinstance(score, int) else 0

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

    def _replay(self, context: GameContext) -> None:
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _main_menu(self, context: GameContext) -> None:
        from states.menu_state import MenuState

        context.scene_manager.change(MenuState())

    def _exit_game(self, context: GameContext) -> None:
        context.scene_manager.request_shutdown()
