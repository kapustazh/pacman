# [transition] SCRUM-35 — pygame sprite rewrite of wehan Ghost.

from pygame.sprite import Sprite

from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import GhostKind


class GhostEntity(Sprite):
    """Static ghost sprite; movement deferred."""

    __slots__ = (
        "_animation",
        "_flashing",
        "_flash_animation",
        "_frightened_animation",
        "_frightened",
        "_hidden",
        "_prev_center",
        "cell",
        "center",
        "image",
        "kind",
        "last_cell",
        "layer",
        "rect",
    )

    def __init__(
        self,
        kind: GhostKind,
        animation: AnimatedSprite,
        frightened_animation: AnimatedSprite,
        cell: CellPos,
        center: tuple[int, int],
        flash_animation: AnimatedSprite | None = None,
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
        self._frightened = False
        self._flashing = False
        self._hidden = False
        self.layer = int(SpriteLayer.ACTORS)
        self.image = animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    @property
    def is_hidden(self) -> bool:
        """Return True when ghost was eaten and not yet respawned."""
        return self._hidden

    def set_frightened(self, frightened: bool, flashing: bool = False) -> None:
        """Switch between normal, frightened and flashing-warning appearance."""
        self._frightened = frightened
        self._flashing = flashing

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

    def hide_eaten(self) -> None:
        """Remove ghost from play until respawn."""
        self._hidden = True
        self.kill()

    def respawn_at(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Return ghost to home corner after being eaten."""
        self.cell = cell
        self.last_cell = cell
        self.center = center
        self._prev_center = center
        self._hidden = False
        self._frightened = False
        self._flashing = False
        self.image = self._animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float, now_ms: int) -> None:
        """Update ghost animation frame."""
        if self._hidden:
            return
        if self._frightened and self._flashing:
            animation = self._flash_animation
        elif self._frightened:
            animation = self._frightened_animation
        else:
            animation = self._animation
        frame = animation.frame_at(now_ms)
        if frame is not self.image:
            self.image = frame
            if self.rect is not None:
                self.rect.size = frame.get_size()
