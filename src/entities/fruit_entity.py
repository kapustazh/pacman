from pygame.sprite import Sprite
from pygame.surface import Surface

from entities.sprite_layer import SpriteLayer
from game.level import CellPos


class FruitEntity(Sprite):
    """Bonus fruit that appears briefly during a level."""

    __slots__ = ("cell", "center", "points")

    def __init__(
        self,
        image: Surface,
        cell: CellPos,
        center: tuple[int, int],
        points: int,
    ) -> None:
        super().__init__()
        self.cell = cell
        self.center = center
        self.points = points
        self.layer = int(SpriteLayer.CONSUMABLES)
        self.image = image
        self.rect = image.get_rect(center=center)
