from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.menu_input import MenuKeyBindings, handle_menu_key
from states.text import ArcadeTextColor, draw_menu_row_highlight


@dataclass(frozen=True, slots=True)
class GameOverOption:
    """Single game-over menu entry."""

    label: str
    action: str


class GameOverState(GameState):
    """Game-over scene with arcade score display and menu."""

    TITLE_Y = 340
    SCORE_Y = 430
    MENU_START_Y = 560
    MENU_LINE_HEIGHT = 56
    MENU_SCALE = 3
    TITLE_SCALE = 5
    SCORE_SCALE = 4
    OPTIONS: tuple[GameOverOption, ...] = (
        GameOverOption("REPLAY", "replay"),
        GameOverOption("MAIN MENU", "menu"),
        GameOverOption("EXIT", "exit"),
    )

    __slots__ = ("_action_handlers", "_score", "_selected_index")

    def __init__(self) -> None:
        self._score = 0
        self._selected_index = 0
        self._action_handlers: dict[str, Callable[[GameContext], None]] = {
            "replay": self._replay,
            "menu": self._main_menu,
            "exit": self._exit_game,
        }

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Apply enter_data and reset menu selection."""
        self._selected_index = 0
        if enter_data is not None:
            score = enter_data.get("score", 0)
            self._score = score if isinstance(score, int) else 0

    def leave(self, context: GameContext) -> None:
        """Leave game-over state."""

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Navigate game-over menu with keyboard."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_key(event, context)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Game-over has no simulation."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw game-over title, score, and menu."""
        text = context.resources.get_text_renderer()
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

        for index, option in enumerate(self.OPTIONS):
            y = self.MENU_START_Y + index * self.MENU_LINE_HEIGHT
            if index == self._selected_index:
                draw_menu_row_highlight(
                    surface,
                    index,
                    self.MENU_START_Y,
                    self.MENU_LINE_HEIGHT,
                )
            text.draw_centered_menu_line(
                surface,
                option.label,
                y,
                color=ArcadeTextColor.WHITE,
                scale=self.MENU_SCALE,
            )

    def _handle_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        handle_menu_key(
            event,
            MenuKeyBindings(
                option_count=len(self.OPTIONS),
                on_move_up=lambda: self._move_selection(-1),
                on_move_down=lambda: self._move_selection(1),
                on_activate_selected=lambda: self._activate(
                    self._selected_index,
                    context,
                ),
                on_select_index=lambda index: setattr(
                    self, "_selected_index", index
                ),
                on_activate_index=lambda index: self._activate(index, context),
                on_activate_action=lambda action: self._activate_by_name(
                    action,
                    context,
                ),
                shortcuts={
                    pygame.K_r: (0, "replay"),
                    pygame.K_m: (1, "menu"),
                },
            ),
        )

    def _move_selection(self, delta: int) -> None:
        self._selected_index = (self._selected_index + delta) % len(
            self.OPTIONS
        )

    def _activate(self, index: int, context: GameContext) -> None:
        if 0 <= index < len(self.OPTIONS):
            self._activate_by_name(self.OPTIONS[index].action, context)

    def _activate_by_name(self, action: str, context: GameContext) -> None:
        handler = self._action_handlers.get(action)
        if handler is not None:
            handler(context)

    def _replay(self, context: GameContext) -> None:
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _main_menu(self, context: GameContext) -> None:
        from states.menu_state import MenuState

        context.scene_manager.change(MenuState())

    def _exit_game(self, context: GameContext) -> None:
        context.scene_manager.request_shutdown()
