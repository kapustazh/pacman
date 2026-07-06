# [transition] SCRUM-35 — pygame sprite rewrite of wehan Ghost.

from pygame.sprite import Sprite

from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import GhostKind


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
        self._frightened = False
        self._flashing = False
        self.returning = False
        self.hidden = False
        self.layer = 2  # z-order: actors draw above background/consumables
        self.image = animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def set_frightened(self, frightened: bool, flashing: bool = False) -> None:
        """Switch between normal, frightened, and flashing appearance.

        Args:
            frightened: Whether the ghost is vulnerable to being eaten.
            flashing: Whether to alternate frightened and flash frames.
        """
        self._frightened = frightened
        self._flashing = flashing

    def start_returning_home(self) -> None:
        """Show eyes-only and begin travel back to the ghost house."""
        self.returning = True
        self._frightened = False
        self._flashing = False

    def arrive_home(self) -> None:
        """End the eyes-only trip and resume normal appearance."""
        self.returning = False

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Advance the ghost one grid step and update the sprite rect.

        Args:
            cell: Destination maze grid position.
            center: Destination pixel center on screen.
        """
        self.cell = cell
        self.center = center
        if self.image is not None:
            self.rect = self.image.get_rect(center=self._visual_center(1.0))

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
        center = self._visual_center(t)
        if rect.center != center:
            rect.center = center

    def _visual_center(self, t: float) -> tuple[int, int]:
        """Blend previous and current pixel centers for smooth motion.

        Args:
            t: Blend factor from 0.0 to 1.0.

        Returns:
            Interpolated (x, y) pixel center.
        """
        px, py = self._prev_center
        cx, cy = self.center
        return (
            round(px + (cx - px) * t),
            round(py + (cy - py) * t),
        )

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
        self.hidden = False
        self._frightened = False
        self._flashing = False
        self.returning = False
        self.image = self._animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float, now_ms: int) -> None:
        """Advance the animation frame for the ghost's current mode.

        Args:
            dt: Elapsed time since the last update in seconds.
            now_ms: Game clock time in milliseconds.
        """
        if self.hidden:
            return
        if self.returning:
            animation = self._eyes_animation
        elif self._frightened and self._flashing:
            toggle = (now_ms // self.FLASH_INTERVAL_MS) % 2
            animation = (
                self._flash_animation
                if toggle == 0
                else self._frightened_animation
            )
        elif self._frightened:
            animation = self._frightened_animation
        else:
            animation = self._animation
        frame = animation.frame_at(now_ms)
        if frame is not self.image:
            self.image = frame
            if self.rect is not None:
                self.rect.size = frame.get_size()
