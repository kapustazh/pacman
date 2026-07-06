from pygame.sprite import Sprite
from pygame.surface import Surface


class WallTileEntity(Sprite):
    """Static wall tile sprite."""

    def __init__(
        self,
        blue_surface: Surface,
        white_surface: Surface,
        center: tuple[int, int],
    ) -> None:
        super().__init__()
        self._blue_surface = blue_surface
        self._white_surface = white_surface
        self._flash_white = False
        self.layer = 0  # z-order: background draws below consumables/actors
        self.image = blue_surface
        self.rect = blue_surface.get_rect(center=center)

    def set_flash_white(self, white: bool) -> None:
        """Swap drawable surface between blue and white maze tile variants."""
        if self._flash_white == white:
            return
        self._flash_white = white
        self.image = self._white_surface if white else self._blue_surface
