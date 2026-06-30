from pygame.sprite import Sprite

from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import GhostKind


class GhostEntity(Sprite):
    """Static ghost sprite; movement deferred."""

    __slots__ = (
        "_animation",
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
    ) -> None:
        super().__init__()
        self.kind = kind
        self.cell = cell
        self.last_cell = cell
        self.center = center
        self._prev_center = center
        self._animation = animation
        self._frightened_animation = frightened_animation
        self._frightened = False
        self._hidden = False
        self.layer = int(SpriteLayer.ACTORS)
        self.image = animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    @property
    def is_hidden(self) -> bool:
        """Return True when ghost was eaten and not yet respawned."""
        return self._hidden

    def set_frightened(self, frightened: bool) -> None:
        """Switch between normal and frightened appearance."""
        self._frightened = frightened

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
        center = self._visual_center(t)
        if self.rect.center != center:
            self.rect.center = center

    def _visual_center(self, t: float) -> tuple[int, int]:
        return (
            round(self._prev_center[0] + (self.center[0] - self._prev_center[0]) * t),
            round(self._prev_center[1] + (self.center[1] - self._prev_center[1]) * t),
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
        self.image = self._animation.frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float, now_ms: int) -> None:
        """Update ghost animation frame."""
        if self._hidden:
            return
        animation = (
            self._frightened_animation
            if self._frightened
            else self._animation
        )
        frame = animation.frame_at(now_ms)
        if frame is not self.image:
            self.image = frame
            self.rect.size = frame.get_size()
