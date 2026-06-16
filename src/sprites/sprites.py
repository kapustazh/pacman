import os
from dataclasses import dataclass, field

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from pygame.surface import Surface  # noqa: E402
import pygame  # noqa: E402


class Sprite:
    """Single image with width and height."""

    def __init__(self, surface: Surface) -> None:
        self.surface: Surface = surface
        self.width: int = surface.get_width()
        self.height: int = surface.get_height()

    def get_upscaled(self, factor: float) -> None:
        self.surface = pygame.transform.scale(
            self.surface, (int(self.width * factor), int(self.height * factor))
        )
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()

    def get_upscaled_from_mask(
        self, x: int, y: int, w: int, h: int, factor: float
    ) -> None:
        tile = self.surface.subsurface(pygame.Rect(x, y, w, h))
        new_size = (int(w * factor), int(h * factor))
        self.surface = pygame.transform.scale(tile, new_size)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()


@dataclass
class AnimatedSprite:
    """Animation built from a list of frame surfaces."""

    frames: list[Surface] = field(default_factory=list)
    frame_duration_ms: int = 150

    @property
    def num_frames(self) -> int:
        return len(self.frames)
