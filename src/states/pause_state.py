from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from states.text import ArcadeTextColor


class PauseState(GameState):
    """Modal pause overlay over gameplay."""

    OVERLAY_COLOR = (0, 0, 0, 180)
    LINE_HEIGHT = 64
    LINES: tuple[tuple[str, ArcadeTextColor, int], ...] = (
        ("PAUSED", ArcadeTextColor.YELLOW, 5),
        ("ESC RESUME", ArcadeTextColor.WHITE, 3),
        ("M MAIN MENU", ArcadeTextColor.ROSE, 2),
    )

    __slots__ = ("_line_surfaces", "_overlay")

    def __init__(self) -> None:
        self._overlay: Surface | None = None
        self._line_surfaces: list[tuple[Surface, int]] = []

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Create pause overlay and cache text once."""
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
            rendered = text.font(color, scale).render(line)
            self._line_surfaces.append((rendered, y))

    def leave(self, context: GameContext) -> None:
        """Release cached pause resources."""
        self._overlay = None
        self._line_surfaces.clear()

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Resume or return to main menu."""
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
        """Pause freezes underlying play state."""

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw cached pause overlay."""
        if self._overlay is not None:
            surface.blit(self._overlay, (0, 0))

        center_x = surface.get_width() // 2
        for rendered, y in self._line_surfaces:
            rect = rendered.get_rect(center=(center_x, y))
            surface.blit(rendered, rect)
