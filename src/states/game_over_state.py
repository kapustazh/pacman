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
class GameOverOption:
    """Single game-over menu entry."""

    label: str
    action: str


GAME_OVER_OPTIONS: tuple[GameOverOption, ...] = (
    GameOverOption("REPLAY", "replay"),
    GameOverOption("MAIN MENU", "menu"),
    GameOverOption("EXIT", "exit"),
)

TITLE_Y = 340
SCORE_Y = 430
MENU_START_Y = 560
MENU_LINE_HEIGHT = 56
MENU_SCALE = 3
TITLE_SCALE = 5
SCORE_SCALE = 4


class GameOverState(GameState):
    """Game-over scene with arcade score display and menu."""

    __slots__ = ("_score", "_selected_index")

    def __init__(self) -> None:
        self._score = 0
        self._selected_index = 0

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
    ) -> None:
        """Read score payload and reset menu selection."""
        self._selected_index = 0
        if payload is not None:
            score = payload.get("score", 0)
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
        draw_centered_arcade_text(
            surface,
            "GAME OVER",
            TITLE_Y,
            ArcadeTextColor.RED,
            TITLE_SCALE,
        )
        draw_centered_arcade_text(
            surface,
            f"SCORE {self._score:06d}",
            SCORE_Y,
            ArcadeTextColor.GOLD,
            SCORE_SCALE,
        )

        for index, option in enumerate(GAME_OVER_OPTIONS):
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
                GAME_OVER_OPTIONS
            )
            return
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self._selected_index = (self._selected_index + 1) % len(
                GAME_OVER_OPTIONS
            )
            return
        if event.key == pygame.K_r:
            self._selected_index = 0
            self._activate_by_name("replay", context)
            return
        if event.key == pygame.K_m:
            self._selected_index = 1
            self._activate_by_name("menu", context)
            return
        if event.key == pygame.K_ESCAPE:
            self._activate_by_name("exit", context)
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate(self._selected_index, context)
            return
        if pygame.K_1 <= event.key <= pygame.K_3:
            index = event.key - pygame.K_1
            self._selected_index = index
            self._activate(index, context)

    def _activate(self, index: int, context: GameContext) -> None:
        if 0 <= index < len(GAME_OVER_OPTIONS):
            self._activate_by_name(GAME_OVER_OPTIONS[index].action, context)

    def _activate_by_name(self, action: str, context: GameContext) -> None:
        handlers: dict[str, Callable[[GameContext], None]] = {
            "replay": self._replay,
            "menu": self._main_menu,
            "exit": self._exit_game,
        }
        handler = handlers.get(action)
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
