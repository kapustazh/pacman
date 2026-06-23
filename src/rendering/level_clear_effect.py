from __future__ import annotations

import pygame
from pygame.surface import Surface

from game.render_config import MazeViewport

FLASH_PERIOD_MS = 200
FLASH_ALPHA = 140
FLASH_COLOR = (255, 255, 180, FLASH_ALPHA)


class LevelClearEffect:
    """Maze flash overlay during LEVEL_COMPLETE."""

    # TODO: change the flash to the maze color change
    def surface_for(
        self,
        viewport: MazeViewport,
        elapsed_ms: int,
    ) -> Surface | None:
        """Return a blink overlay for the maze viewport, or None when off."""
        cycle_ms = elapsed_ms % (FLASH_PERIOD_MS * 2)
        if cycle_ms >= FLASH_PERIOD_MS:
            return None
        overlay = pygame.Surface(
            (viewport.width, viewport.height),
            pygame.SRCALPHA,
        )
        overlay.fill(FLASH_COLOR)
        return overlay
