# [transition] SCRUM-35 — pygame sprite rewrite of wehan Ghost.

from pygame.sprite import Sprite

from game.level import CellPos
from sprites.sprites import AnimatedSprite, lerp_center
from sprites.sprite_types import GhostKind, GhostMode, RenderLayer


class GhostEntity(Sprite):
    """Pygame sprite for a ghost with mode-specific animations."""

    FLASH_INTERVAL_MS = 200

    def __init__(
        self,
        kind: GhostKind,
        animation: AnimatedSprite,
        frightened_animation: AnimatedSprite,
        cell: CellPos,
        center: tuple[int, int],
        flash_animation: AnimatedSprite | None = None,
        eyes_animation: AnimatedSprite | None = None,
    ) -> None:
        """Create a ghost sprite at the given grid cell and pixel center.

        Args:
            kind: Ghost personality used by gameplay logic.
            animation: Normal chase animation.
            frightened_animation: Blue vulnerable animation.
            cell: Initial maze grid position.
            center: Initial pixel center on screen.
            flash_animation: Alternate frightened frame for end-of-power flash.
            eyes_animation: Eyes-only animation when returning home.
        """
        super().__init__()
        self.kind = kind
        self.cell = cell
        self.last_cell = cell
        self.center = center
        self._prev_center = center
        self._animation = animation
        self._frightened_animation = frightened_animation
        self._flash_animation = flash_animation or frightened_animation
        self._eyes_animation = eyes_animation or animation
        self.mode = GhostMode.NORMAL
        self.layer = RenderLayer.ACTOR
        self.image = animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)
        self._step_elapsed_ms: float = 0.0
        # Per-ghost frightened deadline: an energizer frightens each ghost
        # individually, and a respawn clears only that ghost's timer.
        self.frightened_until_ms: int = 0

    def set_frightened(self, frightened: bool, flashing: bool = False) -> None:
        """Switch between normal, frightened, and flashing appearance.

        No-op while the ghost is EYES or HIDDEN: eyes always outrank
        frightened/flashing in ``update()``.

        Args:
            frightened: Whether the ghost is vulnerable to being eaten.
            flashing: Whether to alternate frightened and flash frames.
        """
        if self.mode in (GhostMode.EYES, GhostMode.HIDDEN):
            return
        if not frightened:
            self.mode = GhostMode.NORMAL
        else:
            self.mode = (
                GhostMode.FLASHING if flashing else GhostMode.FRIGHTENED
            )

    def start_returning_home(self) -> None:
        """Show eyes-only and begin travel back to the ghost house."""
        self.mode = GhostMode.EYES

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Advance the ghost one grid step and update the sprite rect.

        Args:
            cell: Destination maze grid position.
            center: Destination pixel center on screen.
        """
        self.cell = cell
        self.center = center
        if self.image is not None:
            self.rect = self.image.get_rect(
                center=lerp_center(self._prev_center, self.center, 1.0)
            )

    def begin_step(self) -> None:
        """Record the current center as the interpolation start point."""
        self._prev_center = self.center

    def apply_visual_lerp(self, t: float) -> None:
        """Interpolate the sprite rect between step start and end.

        Args:
            t: Blend factor from 0.0 (previous center) to 1.0 (current).
        """
        rect = self.rect
        if rect is None:
            return
        center = lerp_center(self._prev_center, self.center, t)
        if rect.center != center:
            rect.center = center

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

    def respawn_at(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Return the ghost to its home corner after being eaten.

        Args:
            cell: Home maze grid position.
            center: Home pixel center on screen.
        """
        self.cell = cell
        self.last_cell = cell
        self.center = center
        self._prev_center = center
        self._step_elapsed_ms = 0.0
        self.mode = GhostMode.NORMAL
        self.frightened_until_ms = 0
        self.image = self._animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float, now_ms: int) -> None:
        """Advance the animation frame for the ghost's current mode.

        Args:
            dt: Elapsed time since the last update in seconds.
            now_ms: Game clock time in milliseconds.
        """
        if self.mode is GhostMode.HIDDEN:
            return
        if self.mode is GhostMode.EYES:
            animation = self._eyes_animation
        elif self.mode is GhostMode.FLASHING:
            toggle = (now_ms // self.FLASH_INTERVAL_MS) % 2
            animation = (
                self._flash_animation
                if toggle == 0
                else self._frightened_animation
            )
        elif self.mode is GhostMode.FRIGHTENED:
            animation = self._frightened_animation
        else:
            animation = self._animation
        frame = animation.frame_at(now_ms)
        if frame is not self.image:
            self.image = frame
            if self.rect is not None:
                self.rect.size = frame.get_size()
