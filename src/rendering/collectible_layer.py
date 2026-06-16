from pygame.surface import Surface

from rendering.layers import RenderLayer
from sprites.assets import Assets
from sprites.types import FruitKind

SPRITE_GAP = 4
SPRITE_STRIDE = 16 + SPRITE_GAP


class CollectibleLayer(RenderLayer):
    def __init__(self, assets: Assets, y: int = 80) -> None:
        self.assets = assets
        self.y = y

    def render(self, surface: Surface, now_ms: int) -> None:
        col = 0
        for sprite in (self.assets.items.dot, self.assets.items.power_pellet):
            x = col * SPRITE_STRIDE
            surface.blit(sprite.surface, (x, self.y))
            col += 1

        for kind in FruitKind:
            sprite = self.assets.fruits[kind]
            x = col * SPRITE_STRIDE
            surface.blit(sprite.surface, (x, self.y))
            col += 1
