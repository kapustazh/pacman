from pygame.surface import Surface

from entities.game_entity import GameEntity
from entities.sprite_layer import SpriteLayer
from game.level import CellPos


class PelletEntity(GameEntity):
    """Static consumable entity."""

    __slots__ = ("_image", "points")

    def __init__(
        self,
        image: Surface,
        cell: CellPos,
        center: tuple[int, int],
        points: int,
    ) -> None:
        super().__init__(cell, center, SpriteLayer.CONSUMABLES)
        self._image = image
        self.points = points

    @property
    def image(self) -> Surface:
        """Return pellet surface."""
        return self._image
