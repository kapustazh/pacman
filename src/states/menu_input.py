from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pygame


@dataclass(frozen=True, slots=True)
class MenuKeyBindings:
    """Callbacks for shared keyboard menu navigation."""

    option_count: int
    on_move_up: Callable[[], None]
    on_move_down: Callable[[], None]
    on_activate_selected: Callable[[], None]
    on_select_index: Callable[[int], None]
    on_activate_index: Callable[[int], None]
    on_activate_action: Callable[[str], None]
    shortcuts: dict[int, tuple[int, str]] = field(default_factory=dict)
    escape_action: str = "exit"


_KEY_COMMANDS: dict[int, str] = {
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
    pygame.K_RETURN: "activate",
    pygame.K_SPACE: "activate",
    pygame.K_ESCAPE: "escape",
}


def handle_menu_key(
    event: pygame.event.Event,
    bindings: MenuKeyBindings,
) -> None:
    """Dispatch one KEYDOWN event through shared menu key bindings."""
    shortcut = bindings.shortcuts.get(event.key)
    if shortcut is not None:
        index, action = shortcut
        bindings.on_select_index(index)
        bindings.on_activate_action(action)
        return

    match _KEY_COMMANDS.get(event.key):
        case "up":
            bindings.on_move_up()
        case "down":
            bindings.on_move_down()
        case "activate":
            bindings.on_activate_selected()
        case "escape":
            bindings.on_activate_action(bindings.escape_action)
        case None:
            max_key = pygame.K_0 + bindings.option_count
            if pygame.K_1 <= event.key <= max_key:
                index = event.key - pygame.K_1
                bindings.on_select_index(index)
                bindings.on_activate_index(index)
