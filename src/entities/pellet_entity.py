from pygame.sprite import Sprite
from pygame.surface import Surface

from game.level import CellPos
from sprites.sprite_types import RenderLayer


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
        self.layer = RenderLayer.CONSUMABLE
        self.image = image
        self.rect = image.get_rect(center=center)

    def relocate(self, center: tuple[int, int]) -> None:
        """Move the pellet to a new pixel center after a display resize.

        Args:
            center: Updated pixel center on screen.
        """
        self.center = center
        rect = self.rect
        if rect is not None:
            rect.center = center
