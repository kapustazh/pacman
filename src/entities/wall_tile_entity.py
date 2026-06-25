from pygame.surface import Surface

from entities.game_entity import GameEntity
from entities.sprite_layer import SpriteLayer
from game.level import CellPos
from sprites.sprite_types import TileKind


class WallTileEntity(GameEntity):
    """Static wall tile entity."""

    __slots__ = (
        "_blue_surface",
        "_flash_white",
        "_image",
        "_white_surface",
        "tile_kind",
    )

    def __init__(
        self,
        blue_surface: Surface,
        white_surface: Surface,
        tile_kind: TileKind,
        cell: CellPos,
        center: tuple[int, int],
    ) -> None:
        super().__init__(cell, center, SpriteLayer.BACKGROUND)
        self.tile_kind = tile_kind
        self._blue_surface = blue_surface
        self._white_surface = white_surface
        self._flash_white = False
        self._image = blue_surface

    @property
    def image(self) -> Surface:
        """Return wall tile surface."""
        return self._image

    def set_flash_white(self, white: bool) -> None:
        """Swap drawable surface between blue and white maze tile variants."""
        if self._flash_white == white:
            return
        self._flash_white = white
        self._image = self._white_surface if white else self._blue_surface
