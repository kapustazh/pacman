from typing import ClassVar
from pygame.sprite import Sprite
from game.level import CellPos
from sprites.sprites import AnimatedSprite, lerp_center
from sprites.sprite_types import Direction, RenderLayer


class PlayerEntity(Sprite):
    """Pygame sprite for Pac-Man movement, animation, and death."""

    DEATH_FRAME_MS: ClassVar[int] = 200

    def __init__(
        self,
        animations_by_direction: dict[Direction, AnimatedSprite],
        cell: CellPos,
        center: tuple[int, int],
        direction: Direction = Direction.RIGHT,
        death_animation: AnimatedSprite | None = None,
    ) -> None:
        """Create a player sprite at the given grid cell and pixel center.

        Args:
            animations_by_direction: Walk-cycle animations keyed by facing.
            cell: Initial maze grid position.
            center: Initial pixel center on screen.
            direction: Starting facing direction.
            death_animation: Optional frames played when Pac-Man dies.
        """
        super().__init__()
        self.cell = cell
        self.center = center
        self._prev_center = center
        self._animations_by_direction = animations_by_direction
        self._death_animation = death_animation
        self._direction = direction
        self.dying = False
        self._death_started_ms = 0
        self.death_finished = False
        self._moved_this_step = False
        self.layer = RenderLayer.ACTOR
        self.image = animations_by_direction[direction].frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def face(self, direction: Direction) -> None:
        """Update the facing direction used for walk animation.

        Args:
            direction: New facing direction.
        """
        self._direction = direction

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Advance the player one grid step and snap the sprite rect.

        Args:
            cell: Destination maze grid position.
            center: Destination pixel center on screen.
        """
        self.cell = cell
        self.center = center
        self._moved_this_step = True
        if self.image is not None:
            self.rect = self.image.get_rect(
                center=lerp_center(self._prev_center, self.center, 1.0)
            )

    def start_death(self, now_ms: int) -> None:
        """Start the death animation from the current position.

        Args:
            now_ms: Game clock time in milliseconds.
        """
        self.dying = True
        self.death_finished = False
        self._death_started_ms = now_ms
        if self._death_animation is not None and self._death_animation.frames:
            frame = self._death_animation.frames[0]
            self.image = frame
            self.rect = frame.get_rect(center=self.center)

    def relocate(self, center: tuple[int, int]) -> None:
        """Snap the sprite to a new pixel center after a display resize.

        Args:
            center: Updated pixel center on screen.
        """
        self.center = center
        self._prev_center = center
        rect = self.rect
        if rect is not None:
            rect.center = center

    def reset_after_death(
        self,
        cell: CellPos,
        center: tuple[int, int],
    ) -> None:
        """Respawn Pac-Man after a life is lost.

        Args:
            cell: Spawn maze grid position.
            center: Spawn pixel center on screen.
        """
        self.cell = cell
        self.center = center
        self._prev_center = center
        self.dying = False
        self.death_finished = False
        self._death_started_ms = 0
        self._moved_this_step = False
        self.image = self._animations_by_direction[self._direction].frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def begin_step(self) -> None:
        """Record the current center as the interpolation start point."""
        self._prev_center = self.center

    def apply_visual_lerp(self, t: float) -> None:
        """Interpolate the sprite rect between step start and end.

        Args:
            t: Blend factor from 0.0 (previous center) to 1.0 (current).
        """
        if self.dying:
            return
        rect = self.rect
        if rect is None:
            return
        center = lerp_center(self._prev_center, self.center, t)
        if rect.center != center:
            rect.center = center

    def update(self, dt: float, now_ms: int) -> None:
        """Advance walk or death animation for the current frame.

        Args:
            dt: Elapsed time since the last update in seconds.
            now_ms: Game clock time in milliseconds.
        """
        if self.dying:
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
        """Advance the death animation and mark completion when done.

        Args:
            now_ms: Game clock time in milliseconds.
        """
        if self._death_animation is None or not self._death_animation.frames:
            self.death_finished = True
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
            self.death_finished = True
