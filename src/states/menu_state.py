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
class MenuOption:
    """Single main-menu entry."""

    label: str
    action: str


class MenuState(GameState):
    """Main menu scene with keyboard navigation."""

    TITLE_Y = 280
    MENU_START_Y = 520
    MENU_LINE_HEIGHT = 56
    MENU_SCALE = 3
    TITLE_SCALE = 5
    OPTIONS: tuple[MenuOption, ...] = (
        MenuOption("START GAME", "start"),
        MenuOption("HIGH SCORES", "highscores"),
        MenuOption("INSTRUCTIONS", "instructions"),
        MenuOption("EXIT", "exit"),
    )

    __slots__ = ("_action_handlers", "_selected_index")

    def __init__(self) -> None:
        self._selected_index = 0
        self._action_handlers: dict[str, Callable[[GameContext], None]] = {
            "start": self._start_game,
            "highscores": self._open_highscores,
            "instructions": self._open_instructions,
            "exit": self._exit_game,
        }

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Reset menu selection."""
        self._selected_index = 0

    def leave(self, context: GameContext) -> None:
        """Leave menu."""

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Handle keyboard menu navigation."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_key(event, context)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Menu has no simulation."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw title and menu options."""
        text = context.resources.get_text_renderer()
        text.draw_centered_arcade_text(
            surface,
            "PAC-MAN",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            self.TITLE_SCALE,
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

    def _start_game(self, context: GameContext) -> None:
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _open_highscores(self, context: GameContext) -> None:
        from states.highscores_state import HighscoresState

        context.scene_manager.push(HighscoresState())

    def _open_instructions(self, context: GameContext) -> None:
        from states.instructions_state import InstructionsState

        context.scene_manager.push(InstructionsState())

    def _exit_game(self, context: GameContext) -> None:
        context.scene_manager.request_shutdown()
