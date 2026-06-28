from pygame.sprite import Sprite
from pygame.surface import Surface

from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import Direction


class PlayerEntity(Sprite):
    """Animated Pac-Man sprite."""

    __slots__ = (
        "_animations_by_direction",
        "_direction",
        "cell",
        "center",
    )

    def __init__(
        self,
        animations_by_direction: dict[Direction, AnimatedSprite],
        cell: CellPos,
        center: tuple[int, int],
        direction: Direction = Direction.RIGHT,
    ) -> None:
        super().__init__()
        self.cell = cell
        self.center = center
        self._animations_by_direction = animations_by_direction
        self._direction = direction
        self.image = animations_by_direction[direction].frame_at(0)
        self.rect = self.image.get_rect(center=center)

    def face(self, direction: Direction) -> None:
        """Set current animation direction."""
        self._direction = direction

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Move player to grid cell and pixel center."""
        self.cell = cell
        self.center = center
        self.rect.center = center

    def update(self, dt: float, now_ms: int) -> None:
        """Update player animation frame."""
        animation = self._animations_by_direction[self._direction]
        self.image = animation.frame_at(now_ms)
        self.rect = self.image.get_rect(center=self.center)

    @property
    def layer(self) -> int:
        return int(SpriteLayer.ACTORS)
