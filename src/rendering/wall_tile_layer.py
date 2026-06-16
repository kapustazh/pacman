from pygame.surface import Surface

from rendering.layers import RenderLayer
from sprites.assets import Assets
from sprites.types import TileKind

TILE_GAP = 4
TILE_STRIDE = 16 + TILE_GAP


class WallTileLayer(RenderLayer):
    def __init__(self, assets: Assets, y: int = 16) -> None:
        self.assets = assets
        self.y = y

    def render(self, surface: Surface, now_ms: int) -> None:
        for col, tile_kind in enumerate(TileKind):
            tile = self.assets.maze.tiles[tile_kind]
            x = col * TILE_STRIDE
            surface.blit(tile.surface, (x, self.y))
