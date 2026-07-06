# [transition] SCRUM-35 — pygame sprite rewrite of wehan Ghost.

from pygame.sprite import Sprite

from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import GhostKind


class GhostEntity(Sprite):
    """Static ghost sprite; movement deferred."""

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
        """Switch between normal, frightened and flashing appearance."""
        self._frightened = frightened
        self._flashing = flashing

    def start_returning_home(self) -> None:
        """Switch to eyes-only and travel back to home instead of hiding."""
        self.returning = True
        self._frightened = False
        self._flashing = False

    def arrive_home(self) -> None:
        """End the eyes-only trip; resume normal appearance at home."""
        self.returning = False

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Move ghost one grid step."""
        self.cell = cell
        self.center = center
        if self.image is not None:
            self.rect = self.image.get_rect(center=self._visual_center(1.0))

    def begin_step(self) -> None:
        """Mark grid-step start for visual interpolation."""
        self._prev_center = self.center

    def apply_visual_lerp(self, t: float) -> None:
        """Slide sprite between prev and current cell centers."""
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

    def respawn_at(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Return ghost to home corner after being eaten."""
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
        """Update ghost animation frame."""
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
