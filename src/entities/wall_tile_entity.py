from pygame.sprite import Sprite
from pygame.surface import Surface

from game.level import CellPos
from sprites.sprite_types import RenderLayer


class WallTileEntity(Sprite):
    """Pygame sprite for one maze wall tile with optional flash."""

    def __init__(
        self,
        blue_surface: Surface,
        white_surface: Surface,
        center: tuple[int, int],
        cell: CellPos,
    ) -> None:
        """Create a wall tile sprite at a pixel position.

        Args:
            blue_surface: Default blue maze tile image.
            white_surface: Alternate white tile used during flash effects.
            center: Pixel center on screen.
            cell: Maze grid position for this tile.
        """
        super().__init__()
        self.cell = cell
        self._blue_surface = blue_surface
        self._white_surface = white_surface
        self._flash_white = False
        self.layer = RenderLayer.BACKGROUND
        self.image = blue_surface
        self.rect = blue_surface.get_rect(center=center)

    def relocate(self, center: tuple[int, int]) -> None:
        """Move the tile to a new pixel center after a display resize.

        Args:
            center: Updated pixel center on screen.
        """
        rect = self.rect
        if rect is not None:
            rect.center = center

    def set_flash_white(self, white: bool) -> None:
        """Swap between blue and white tile surfaces.

        Args:
            white: Use the white surface when True, blue when False.
        """
        if self._flash_white == white:
            return
        self._flash_white = white
        self.image = self._white_surface if white else self._blue_surface
