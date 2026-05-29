import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from pygame.surface import Surface  # noqa E402
import pygame  # noqa E402


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
        new_size = (w * factor, h * factor)
        self.surface = pygame.transform.scale(tile, new_size)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()


class AnimatedSprite:

    def __init__(self, frames: list[Sprite], fps: int) -> None:
        self.num_frames: int = fps
        self.frames: list[Surface] = []

    def prepare_frames(self, scale: float = 1.0) -> None:
        width = self.width // self.num_frames
        for i in range(self.num_frames):
            rect = pygame.Rect(i * width, 0, width, self.height)
            frame = self.surface.subsurface(rect)
            new_size = (
                frame.get_width() * scale,
                frame.get_height() * scale,
            )
            frame = pygame.transform.scale(frame, new_size)
            self.frames.append(frame)
