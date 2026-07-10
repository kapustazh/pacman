from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from rendering.widgets import draw_menu_row_highlight
from states.text import ArcadeTextColor

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
    """Main menu with keyboard-navigated options."""

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
        """Initialize selection on the first menu row."""
        self._selected_index = 0

    def select(self, index: int) -> None:
        """Move the highlight to a menu row.

        Args:
            index: Zero-based row index to select.
        """
        self._selected_index = index

    def move(self, delta: int) -> None:
        """Move the highlight up or down with wraparound.

        Args:
            delta: Row offset; negative moves up, positive moves down.
        """
        self._selected_index = (self._selected_index + delta) % len(
            self.OPTIONS
        )

    def activate_selected(self, context: GameContext) -> None:
        """Run the action for the highlighted row.

        Args:
            context: Shared game context for scene transitions.
        """
        self.activate_index(self._selected_index, context)

    def activate_index(self, index: int, context: GameContext) -> None:
        """Run the action for one row when the index is valid.

        Args:
            index: Zero-based row index to activate.
            context: Shared game context for scene transitions.
        """
        if 0 <= index < len(self.OPTIONS):
            self._activate_action(self.OPTIONS[index][1], context)

    def _activate_action(self, action: str, context: GameContext) -> None:
        """Dispatch a named menu action to its handler.

        Args:
            action: Internal action key from the options table.
            context: Shared game context for scene transitions.
        """
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
        """Reset selection to the first row.

        Args:
            context: Shared game context (unused).
            enter_data: Optional payload from the previous scene (unused).
        """
        self._selected_index = 0

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
        """Route keyboard input to menu navigation.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for scene transitions.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_menu_key(event, context)

    def _handle_menu_key(
        self,
        event: pygame.event.Event,
        context: GameContext,
    ) -> None:
        """Handle one key press for menu navigation or activation.

        Args:
            event: Keydown event to interpret.
            context: Shared game context for scene transitions.
        """
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
        """No-op; menu has no simulation.

        Args:
            dt: Elapsed seconds since the last frame (unused).
            now_ms: Monotonic clock in milliseconds (unused).
            context: Shared game context (unused).
        """

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw the title and selectable menu rows.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
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
        """Switch to gameplay.

        Args:
            context: Shared game context for scene transitions.
        """
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _open_highscores(self, context: GameContext) -> None:
        """Push the high scores screen.

        Args:
            context: Shared game context for scene transitions.
        """
        from states.highscores_state import HighscoresState

        context.scene_manager.push(HighscoresState())

    def _open_instructions(self, context: GameContext) -> None:
        """Push the instructions screen.

        Args:
            context: Shared game context for scene transitions.
        """
        from states.instructions_state import InstructionsState

        context.scene_manager.push(InstructionsState())

    def _exit_game(self, context: GameContext) -> None:
        """Request application shutdown.

        Args:
            context: Shared game context for scene transitions.
        """
        context.scene_manager.request_shutdown()
