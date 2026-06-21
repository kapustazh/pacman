from pygame.surface import Surface

from entities.game_entity import GameEntity
from entities.sprite_layer import SpriteLayer
from game.level import CellPos


class WallTileEntity(GameEntity):
    """Static wall tile entity."""

    __slots__ = ("_image",)

    def __init__(
        self,
        image: Surface,
        cell: CellPos,
        center: tuple[int, int],
    ) -> None:
        super().__init__(cell, center, SpriteLayer.BACKGROUND)
        self._image = image

    @property
    def image(self) -> Surface:
        """Return wall tile surface."""
        return self._image
