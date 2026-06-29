from pygame.sprite import Sprite
from pygame.surface import Surface

from entities.sprite_layer import SpriteLayer
from game.level import CellPos


class WallTileEntity(Sprite):
    """Static wall tile sprite."""

    __slots__ = (
        "_blue_surface",
        "_flash_white",
        "_white_surface",
        "cell",
        "center",
    )

    def __init__(
        self,
        blue_surface: Surface,
        white_surface: Surface,
        cell: CellPos,
        center: tuple[int, int],
    ) -> None:
        super().__init__()
        self.cell = cell
        self.center = center
        self._blue_surface = blue_surface
        self._white_surface = white_surface
        self._flash_white = False
        self.layer = int(SpriteLayer.BACKGROUND)
        self.image = blue_surface
        self.rect = blue_surface.get_rect(center=center)

    def set_flash_white(self, white: bool) -> None:
        """Swap drawable surface between blue and white maze tile variants."""
        if self._flash_white == white:
            return
        self._flash_white = white
        self.image = self._white_surface if white else self._blue_surface
