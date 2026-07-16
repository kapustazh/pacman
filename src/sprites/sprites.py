from dataclasses import dataclass, field

from pygame.surface import Surface


class SpriteError(Exception):
    """Raised when sprite data is invalid."""


def lerp_center(
    prev_center: tuple[int, int],
    center: tuple[int, int],
    t: float,
) -> tuple[int, int]:
    """Blend two pixel centers for smooth grid-step motion.

    Args:
        prev_center: Pixel center at the start of the step.
        center: Pixel center at the end of the step.
        t: Blend factor from 0.0 (prev_center) to 1.0 (center).

    Returns:
        Interpolated (x, y) pixel center.
    """
    px, py = prev_center
    cx, cy = center
    return (round(px + (cx - px) * t), round(py + (cy - py) * t))


@dataclass(slots=True)
class AnimatedSprite:
    """Cycles through frame surfaces on a fixed timer."""

    frames: list[Surface] = field(default_factory=list)
    frame_duration_ms: int = 150

    def frame_at(self, now_ms: int) -> Surface:
        """Pick the frame for the current animation time.

        Args:
            now_ms: Monotonic pygame clock in milliseconds.

        Returns:
            Surface for the active frame.

        Raises:
            SpriteError: When no frames were loaded.
        """
        if not self.frames:
            raise SpriteError("Animated sprite has no frames")
        frame_index = (now_ms // self.frame_duration_ms) % len(self.frames)
        return self.frames[frame_index]
