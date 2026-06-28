from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class MenuEntry:
    """Single keyboard-navigated menu row."""

    label: str
    action: str


class SelectableMenuState(GameState):
    """Shared keyboard-navigated option list."""

    MENU_LINE_HEIGHT: ClassVar[int] = 56
    MENU_SCALE: ClassVar[int] = 3

    __slots__ = (
        "_action_handlers",
        "_entries",
        "_menu_start_y",
        "_selected_index",
        "_shortcuts",
    )

    def __init__(
        self,
        entries: tuple[MenuEntry, ...],
        menu_start_y: int,
        action_handlers: dict[str, Callable[[GameContext], None]],
        shortcuts: dict[int, tuple[int, str]] | None = None,
    ) -> None:
        self._entries = entries
        self._menu_start_y = menu_start_y
        self._action_handlers = action_handlers
        self._shortcuts = shortcuts or {}
        self._selected_index = 0

    def option_count(self) -> int:
        """Return number of selectable menu rows."""
        return len(self._entries)

    def select(self, index: int) -> None:
        """Highlight menu row at index."""
        self._selected_index = index

    def move(self, delta: int) -> None:
        """Move selection up or down, wrapping at list ends."""
        count = self.option_count()
        self._selected_index = (self._selected_index + delta) % count

    def activate_selected(self, context: GameContext) -> None:
        """Activate currently highlighted row."""
        self.activate_index(self._selected_index, context)

    def activate_index(self, index: int, context: GameContext) -> None:
        """Activate row at index when in range."""
        if 0 <= index < len(self._entries):
            self.activate_action(self._entries[index].action, context)

    def activate_action(self, action: str, context: GameContext) -> None:
        """Run handler for named menu action."""
        handler = self._action_handlers.get(action)
        if handler is not None:
            handler(context)

    def draw_header(self, surface: Surface, context: GameContext) -> None:
        """Draw screen content above the option list."""

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
        *,
        escape_action: str = "exit",
    ) -> None:
        """Dispatch one KEYDOWN event through shared menu key bindings."""
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
        """Menu has no simulation."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw header and menu options."""
        self.draw_header(surface, context)
        text = context.text
        options = self._entries

        for index, option in enumerate(options):
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
                option.label,
                y,
                ArcadeTextColor.WHITE,
                self.MENU_SCALE,
            )
