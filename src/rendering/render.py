from pygame.surface import Surface

from rendering.character_layer import CharacterLayer
from rendering.collectible_layer import CollectibleLayer
from rendering.layers import RenderLayer
from rendering.wall_tile_layer import WallTileLayer
from sprites.assets import Assets


class DemoRenderer:
    def __init__(self, assets: Assets) -> None:
        self.assets = assets
        self.layers: list[RenderLayer] = [
            WallTileLayer(assets, y=16),
            CharacterLayer(assets, y=48),
            CollectibleLayer(assets, y=80),
        ]

    def render(self, surface: Surface, now_ms: int) -> None:
        for layer in self.layers:
            layer.render(surface, now_ms)
