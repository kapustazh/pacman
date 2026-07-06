from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor, draw_menu_row_highlight

_KEY_COMMANDS: dict[int, str] = {
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
    pygame.K_RETURN: "activate",
    pygame.K_SPACE: "activate",
    pygame.K_ESCAPE: "escape",
}


class MenuState(GameState):
    """Main menu scene with keyboard navigation."""

    TITLE_Y: ClassVar[int] = 280
    MENU_START_Y: ClassVar[int] = 520
    TITLE_SCALE: ClassVar[int] = 5
    MENU_LINE_HEIGHT: ClassVar[int] = 56
    MENU_SCALE: ClassVar[int] = 3
    OPTIONS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("START GAME", "start"),
        ("HIGH SCORES", "highscores"),
        ("INSTRUCTIONS", "instructions"),
        ("EXIT", "exit"),
    )

    def __init__(self) -> None:
        self._selected_index = 0

    def select(self, index: int) -> None:
        """Highlight menu row at index."""
        self._selected_index = index

    def move(self, delta: int) -> None:
        """Move selection up or down, wrapping at list ends."""
        self._selected_index = (self._selected_index + delta) % len(
            self.OPTIONS
        )

    def activate_selected(self, context: GameContext) -> None:
        """Activate currently highlighted row."""
        self.activate_index(self._selected_index, context)

    def activate_index(self, index: int, context: GameContext) -> None:
        """Activate row at index when in range."""
        if 0 <= index < len(self.OPTIONS):
            self._activate_action(self.OPTIONS[index][1], context)

    def _activate_action(self, action: str, context: GameContext) -> None:
        """Run handler for named menu action."""
        handlers = {
            "start": self._start_game,
            "highscores": self._open_highscores,
            "instructions": self._open_instructions,
            "exit": self._exit_game,
        }
        handler = handlers.get(action)
        if handler is not None:
            handler(context)

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
                self._handle_menu_key(event, context)

    def _handle_menu_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        """Dispatch one KEYDOWN event through shared menu key bindings."""
        match _KEY_COMMANDS.get(event.key):
            case "up":
                self.move(-1)
            case "down":
                self.move(1)
            case "activate":
                self.activate_selected(context)
            case "escape":
                self._activate_action("exit", context)
            case None:
                max_key = pygame.K_0 + len(self.OPTIONS)
                if pygame.K_1 <= event.key <= max_key:
                    index = event.key - pygame.K_1
                    self.select(index)
                    self.activate_index(index, context)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Menu has no simulation."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw title and menu options."""
        context.text.draw_centered_arcade_text(
            surface,
            "PAC-MAN",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            self.TITLE_SCALE,
        )
        text = context.text
        for index, (label, _action) in enumerate(self.OPTIONS):
            y = self.MENU_START_Y + index * self.MENU_LINE_HEIGHT
            if index == self._selected_index:
                draw_menu_row_highlight(
                    surface,
                    index,
                    self.MENU_START_Y,
                    self.MENU_LINE_HEIGHT,
                )
            text.draw_centered_arcade_text(
                surface,
                label,
                y,
                ArcadeTextColor.WHITE,
                self.MENU_SCALE,
            )

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
