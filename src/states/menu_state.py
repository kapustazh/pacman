from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StatePayload
from states.text import (
    ArcadeTextColor,
    draw_centered_arcade_text,
    draw_centered_menu_line,
    draw_menu_row_highlight,
)


@dataclass(frozen=True, slots=True)
class MenuOption:
    """Single main-menu entry."""

    label: str
    action: str


MENU_OPTIONS: tuple[MenuOption, ...] = (
    MenuOption("START GAME", "start"),
    MenuOption("HIGH SCORES", "highscores"),
    MenuOption("INSTRUCTIONS", "instructions"),
    MenuOption("EXIT", "exit"),
)

TITLE_Y = 280
MENU_START_Y = 520
MENU_LINE_HEIGHT = 56
MENU_SCALE = 3
TITLE_SCALE = 5


class MenuState(GameState):
    """Main menu scene with keyboard navigation."""

    __slots__ = ("_selected_index",)

    def __init__(self) -> None:
        self._selected_index = 0

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
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
        draw_centered_arcade_text(
            surface,
            "PAC-MAN",
            TITLE_Y,
            ArcadeTextColor.YELLOW,
            TITLE_SCALE,
        )

        for index, option in enumerate(MENU_OPTIONS):
            y = MENU_START_Y + index * MENU_LINE_HEIGHT
            if index == self._selected_index:
                draw_menu_row_highlight(
                    surface,
                    index,
                    MENU_START_Y,
                    MENU_LINE_HEIGHT,
                )
            draw_centered_menu_line(
                surface,
                option.label,
                y,
                color=ArcadeTextColor.WHITE,
                scale=MENU_SCALE,
            )

    def _handle_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        if event.key in (pygame.K_UP, pygame.K_w):
            self._selected_index = (self._selected_index - 1) % len(
                MENU_OPTIONS
            )
            return
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self._selected_index = (self._selected_index + 1) % len(
                MENU_OPTIONS
            )
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate(self._selected_index, context)
            return
        if event.key == pygame.K_ESCAPE:
            self._activate_by_name("exit", context)
            return
        if pygame.K_1 <= event.key <= pygame.K_4:
            index = event.key - pygame.K_1
            self._selected_index = index
            self._activate(index, context)

    def _activate(self, index: int, context: GameContext) -> None:
        if 0 <= index < len(MENU_OPTIONS):
            self._activate_by_name(MENU_OPTIONS[index].action, context)

    def _activate_by_name(self, action: str, context: GameContext) -> None:
        handlers: dict[str, Callable[[GameContext], None]] = {
            "start": self._start_game,
            "highscores": self._open_highscores,
            "instructions": self._open_instructions,
            "exit": self._exit_game,
        }
        handler = handlers.get(action)
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
