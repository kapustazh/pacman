from pygame.sprite import Sprite
from pygame.surface import Surface

from game.level import CellPos


class PelletEntity(Sprite):
    """Pygame sprite for a pellet or power pellet on the maze."""

    def __init__(
        self,
        image: Surface,
        cell: CellPos,
        center: tuple[int, int],
        points: int,
    ) -> None:
        """Create a consumable pellet sprite at a maze cell.

        Args:
            image: Drawable surface for the pellet.
            cell: Maze grid position of the pellet.
            center: Pixel center on screen.
            points: Score value awarded when eaten.
        """
        super().__init__()
        self.cell = cell
        self.center = center
        self.points = points
        self.layer = 1  # z-order: consumables draw above background
        self.image = image
        self.rect = image.get_rect(center=center)
