from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor


class PauseState(GameState):
    """Modal pause overlay shown above active gameplay."""

    OVERLAY_COLOR = (0, 0, 0, 180)
    LINE_HEIGHT = 64
    LINES: tuple[tuple[str, ArcadeTextColor, int], ...] = (
        ("PAUSED", ArcadeTextColor.YELLOW, 5),
        ("ESC RESUME", ArcadeTextColor.WHITE, 3),
        ("M MAIN MENU", ArcadeTextColor.ROSE, 2),
    )

    def __init__(self) -> None:
        """Initialize empty overlay and text caches."""
        self._overlay: Surface | None = None
        self._line_surfaces: list[tuple[Surface, int]] = []

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Build the dim overlay and cache pause text once.

        Args:
            context: Shared game context with screen size and text renderer.
            enter_data: Optional payload from the previous scene (unused).
        """
        self._overlay = Surface(context.screen.get_size(), pygame.SRCALPHA)
        self._overlay.fill(self.OVERLAY_COLOR)

        total_height = self.LINE_HEIGHT * len(self.LINES)
        start_y = (
            context.screen.get_height() - total_height
        ) // 2 + self.LINE_HEIGHT // 2

        self._line_surfaces = []
        text = context.text
        for index, (line, color, scale) in enumerate(self.LINES):
            y = start_y + index * self.LINE_HEIGHT
            rendered = text.render(line, color, scale)
            self._line_surfaces.append((rendered, y))

    def on_screen_resize(self, context: GameContext) -> None:
        """Rebuild the overlay for the new display size.

        Args:
            context: Shared game context with the updated screen surface.
        """
        self.leave(context)
        self.enter(context)

    def leave(self, context: GameContext) -> None:
        """Release cached overlay and text surfaces.

        Args:
            context: Shared game context (unused).
        """
        self._overlay = None
        self._line_surfaces.clear()

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Resume play or return to the main menu.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for scene transitions.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                context.scene_manager.pop()
                return
            if event.key == pygame.K_m:
                from states.menu_state import MenuState

                context.scene_manager.change(MenuState())
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No-op; underlying play state stays frozen.

        Args:
            dt: Elapsed seconds since the last frame (unused).
            now_ms: Monotonic clock in milliseconds (unused).
            context: Shared game context (unused).
        """

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw the dim overlay and cached pause lines.

        Args:
            surface: Destination draw target.
            context: Shared game context (unused).
        """
        if self._overlay is not None:
            surface.blit(self._overlay, (0, 0))

        center_x = surface.get_width() // 2
        for rendered, y in self._line_surfaces:
            rect = rendered.get_rect(center=(center_x, y))
            surface.blit(rendered, rect)
