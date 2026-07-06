from __future__ import annotations

from collections.abc import Callable
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


class SelectableMenuState(GameState):
    """Reusable keyboard-navigated menu with configurable rows."""

    MENU_LINE_HEIGHT: ClassVar[int] = 56
    MENU_SCALE: ClassVar[int] = 3

    def __init__(
        self,
        entries: tuple[tuple[str, str], ...],
        menu_start_y: int,
        action_handlers: dict[str, Callable[[GameContext], None]],
        shortcuts: dict[int, tuple[int, str]] | None = None,
    ) -> None:
        """Configure menu rows, layout, and action handlers.

        Args:
            entries: Label and action-key pairs for each row.
            menu_start_y: Vertical center of the first row.
            action_handlers: Map from action keys to callbacks.
            shortcuts: Optional direct key-to-(index, action) bindings.
        """
        self._entries = entries
        self._menu_start_y = menu_start_y
        self._action_handlers = action_handlers
        self._shortcuts = shortcuts or {}
        self._selected_index = 0

    def option_count(self) -> int:
        """Return the number of selectable rows.

        Returns:
            Count of configured menu entries.
        """
        return len(self._entries)

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
        count = self.option_count()
        self._selected_index = (self._selected_index + delta) % count

    def activate_selected(self, context: GameContext) -> None:
        """Run the action for the highlighted row.

        Args:
            context: Shared game context passed to the action handler.
        """
        self.activate_index(self._selected_index, context)

    def activate_index(self, index: int, context: GameContext) -> None:
        """Run the action for one row when the index is valid.

        Args:
            index: Zero-based row index to activate.
            context: Shared game context passed to the action handler.
        """
        if 0 <= index < len(self._entries):
            self.activate_action(self._entries[index][1], context)

    def activate_action(self, action: str, context: GameContext) -> None:
        """Dispatch a named menu action to its handler.

        Args:
            action: Internal action key from the entries table.
            context: Shared game context passed to the action handler.
        """
        handler = self._action_handlers.get(action)
        if handler is not None:
            handler(context)

    def draw_header(self, surface: Surface, context: GameContext) -> None:
        """No-op; subclasses draw content above the option list.

        Args:
            surface: Destination draw target (unused).
            context: Shared game context (unused).
        """

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
        *,
        escape_action: str = "exit",
    ) -> None:
        """Handle one key press for menu navigation or activation.

        Args:
            event: Keydown event to interpret.
            context: Shared game context for scene transitions.
            escape_action: Action key to run when Escape is pressed.
        """
        shortcut = self._shortcuts.get(event.key)
        if shortcut is not None:
            index, action = shortcut
            self.select(index)
            self.activate_action(action, context)
            return

        match _KEY_COMMANDS.get(event.key):
            case "up":
                self.move(-1)
            case "down":
                self.move(1)
            case "activate":
                self.activate_selected(context)
            case "escape":
                self.activate_action(escape_action, context)
            case None:
                max_key = pygame.K_0 + self.option_count()
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
        """Draw the header and selectable menu rows.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        self.draw_header(surface, context)
        self.draw_options(surface, context)

    def draw_options(self, surface: Surface, context: GameContext) -> None:
        """Draw selectable rows with highlight for the current selection.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        text = context.text
        options = self._entries

        for index, (label, _action) in enumerate(options):
            y = self._menu_start_y + index * self.MENU_LINE_HEIGHT
            if index == self._selected_index:
                draw_menu_row_highlight(
                    surface,
                    index,
                    self._menu_start_y,
                    self.MENU_LINE_HEIGHT,
                )
            text.draw_centered_arcade_text(
                surface,
                label,
                y,
                ArcadeTextColor.WHITE,
                self.MENU_SCALE,
            )
