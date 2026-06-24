from __future__ import annotations

from typing import ClassVar

import pygame
from pygame.surface import Surface

from game.render_config import MazeViewport


class LevelClearEffect:
    """Maze flash overlay during LEVEL_COMPLETE."""

    FLASH_PERIOD_MS: ClassVar[int] = 200
    FLASH_ALPHA: ClassVar[int] = 140
    FLASH_COLOR: ClassVar[tuple[int, int, int, int]] = (255, 255, 180, 140)

    __slots__ = ("_overlay_cache",)

    def __init__(self) -> None:
        self._overlay_cache: dict[tuple[int, int], Surface] = {}

    # TODO: change the flash to the maze color change
    def surface_for(
        self,
        viewport: MazeViewport,
        elapsed_ms: int,
    ) -> Surface | None:
        """Return a blink overlay for the maze viewport, or None when off."""
        cycle_ms = elapsed_ms % (self.FLASH_PERIOD_MS * 2)
        if cycle_ms >= self.FLASH_PERIOD_MS:
            return None
        return self._overlay_for_size(viewport.width, viewport.height)

    def _overlay_for_size(self, width: int, height: int) -> Surface:
        key = (width, height)
        cached = self._overlay_cache.get(key)
        if cached is not None:
            return cached
        overlay = pygame.Surface(key, pygame.SRCALPHA)
        overlay.fill(self.FLASH_COLOR)
        self._overlay_cache[key] = overlay
        return overlay
