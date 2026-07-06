from dataclasses import dataclass, field

from pygame.surface import Surface


class SpriteError(Exception):
    """Raised when sprite data is invalid."""


@dataclass(slots=True)
class AnimatedSprite:
    """Animation built from a list of frame surfaces."""

    frames: list[Surface] = field(default_factory=list)
    frame_duration_ms: int = 150

    def frame_at(self, now_ms: int) -> Surface:
        """Return animation frame for current monotonic pygame time."""
        if not self.frames:
            raise SpriteError("Animated sprite has no frames")
        frame_index = (now_ms // self.frame_duration_ms) % len(self.frames)
        return self.frames[frame_index]
