from dataclasses import dataclass, field

from pygame.surface import Surface


class SpriteError(Exception):
    """Raised when sprite data is invalid."""


class AssetSprite:
    """Single image with width and height."""

    __slots__ = ("height", "surface", "width")

    def __init__(self, surface: Surface) -> None:
        self.surface: Surface = surface
        self.width: int = surface.get_width()
        self.height: int = surface.get_height()


@dataclass(slots=True)
class AnimatedSprite:
    """Animation built from a list of frame surfaces."""

    frames: list[Surface] = field(default_factory=list)
    frame_duration_ms: int = 150

    @property
    def num_frames(self) -> int:
        return len(self.frames)

    def frame_at(self, now_ms: int) -> Surface:
        """Return animation frame for current monotonic pygame time."""
        if self.num_frames == 0:
            raise SpriteError("Animated sprite has no frames")
        frame_index = (now_ms // self.frame_duration_ms) % self.num_frames
        return self.frames[frame_index]
