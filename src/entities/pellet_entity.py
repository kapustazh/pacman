from pygame.sprite import Sprite
from pygame.surface import Surface

from game.level import CellPos


class PelletEntity(Sprite):
    """Static consumable sprite."""

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
        self.layer = 1  # z-order: consumables draw above background
        self.image = image
        self.rect = image.get_rect(center=center)
