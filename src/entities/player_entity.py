from typing import ClassVar

from pygame.sprite import Sprite
from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import Direction


class PlayerEntity(Sprite):
    """Animated Pac-Man sprite."""

    DEATH_FRAME_MS: ClassVar[int] = 200

    __slots__ = (
        "_animations_by_direction",
        "_death_animation",
        "_death_finished",
        "_death_started_ms",
        "_direction",
        "_dying",
        "_moved_this_step",
        "_prev_center",
        "cell",
        "center",
        "image",
        "layer",
        "rect",
    )

    def __init__(
        self,
        animations_by_direction: dict[Direction, AnimatedSprite],
        cell: CellPos,
        center: tuple[int, int],
        direction: Direction = Direction.RIGHT,
        death_animation: AnimatedSprite | None = None,
    ) -> None:
        super().__init__()
        self.cell = cell
        self.center = center
        self._prev_center = center
        self._animations_by_direction = animations_by_direction
        self._death_animation = death_animation
        self._direction = direction
        self._dying = False
        self._death_started_ms = 0
        self._death_finished = False
        self._moved_this_step = False
        self.layer = int(SpriteLayer.ACTORS)
        self.image = animations_by_direction[direction].frame_at(0)
        self.rect = self.image.get_rect(center=center)

    @property
    def is_dying(self) -> bool:
        """Return True while the death animation is playing."""
        return self._dying

    @property
    def death_finished(self) -> bool:
        """Return True once the death animation has completed."""
        return self._death_finished

    def face(self, direction: Direction) -> None:
        """Set current animation direction."""
        self._direction = direction

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Move player to grid cell and pixel center."""
        self.cell = cell
        self.center = center
        self._moved_this_step = True
        if self.image is not None:
            self.rect = self.image.get_rect(center=self._visual_center(1.0))

    def start_death(self, now_ms: int) -> None:
        """Begin Pac-Man death animation at current position."""
        self._dying = True
        self._death_finished = False
        self._death_started_ms = now_ms
        if self._death_animation is not None and self._death_animation.frames:
            frame = self._death_animation.frames[0]
            self.image = frame
            self.rect = frame.get_rect(center=self.center)

    def reset_after_death(
        self,
        cell: CellPos,
        center: tuple[int, int],
    ) -> None:
        """Respawn player at spawn cell after losing a life."""
        self.cell = cell
        self.center = center
        self._prev_center = center
        self._dying = False
        self._death_finished = False
        self._death_started_ms = 0
        self._moved_this_step = False
        self.image = self._animations_by_direction[self._direction].frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def begin_step(self) -> None:
        """Mark grid-step start for visual interpolation."""
        self._prev_center = self.center

    def apply_visual_lerp(self, t: float) -> None:
        """Slide sprite between prev and current cell centers."""
        if self._dying:
            return
        rect = self.rect
        if rect is None:
            return
        center = self._visual_center(t)
        if rect.center != center:
            rect.center = center

    def _visual_center(self, t: float) -> tuple[int, int]:
        px, py = self._prev_center
        cx, cy = self.center
        return (
            round(px + (cx - px) * t),
            round(py + (cy - py) * t),
        )

    def update(self, dt: float, now_ms: int) -> None:
        """Update player animation frame."""
        if self._dying:
            self._update_death(now_ms)
            return
        if not self._moved_this_step:
            return
        self._moved_this_step = False
        animation = self._animations_by_direction[self._direction]
        frame = animation.frame_at(now_ms)
        if frame is not self.image:
            self.image = frame
            if self.rect is not None:
                self.rect.size = frame.get_size()

    def _update_death(self, now_ms: int) -> None:
        if self._death_animation is None or not self._death_animation.frames:
            self._death_finished = True
            return
        elapsed_ms = max(0, now_ms - self._death_started_ms)
        frame_count = len(self._death_animation.frames)
        frame_index = min(elapsed_ms // self.DEATH_FRAME_MS, frame_count - 1)
        frame = self._death_animation.frames[frame_index]
        if frame is not self.image:
            self.image = frame
            self.rect = frame.get_rect(center=self.center)
        total_ms = self.DEATH_FRAME_MS * frame_count
        if elapsed_ms >= total_ms:
            self._death_finished = True
