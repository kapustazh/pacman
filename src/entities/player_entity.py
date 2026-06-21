from pygame.surface import Surface

from entities.game_entity import GameEntity
from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprites import AnimatedSprite
from sprites.types import Direction


class PlayerEntity(GameEntity):
    """Animated Pac-Man entity."""

    __slots__ = ("_animations_by_direction", "_direction", "_image")

    def __init__(
        self,
        animations_by_direction: dict[Direction, AnimatedSprite],
        cell: CellPos,
        center: tuple[int, int],
        direction: Direction = Direction.RIGHT,
    ) -> None:
        super().__init__(cell, center, SpriteLayer.ACTORS)
        self._animations_by_direction = animations_by_direction
        self._direction = direction
        self._image = animations_by_direction[direction].frame_at(0)

    @property
    def direction(self) -> Direction:
        """Return current movement direction."""
        return self._direction

    @property
    def image(self) -> Surface:
        """Return current animation frame."""
        return self._image

    def face(self, direction: Direction) -> None:
        """Set current animation direction."""
        self._direction = direction

    def move_to(self, cell: CellPos, center: tuple[int, int]) -> None:
        """Move player to grid cell and pixel center."""
        self.cell = cell
        self.center = center

    def update(self, dt: float, now_ms: int) -> None:
        """Update player animation frame."""
        animation = self._animations_by_direction[self._direction]
        self._image = animation.frame_at(now_ms)
