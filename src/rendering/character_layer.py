from pygame.surface import Surface

from rendering.layers import RenderLayer
from sprites.assets import Assets
from sprites.types import Direction, GhostKind


SPRITE_GAP = 4
SPRITE_STRIDE = 16 + SPRITE_GAP
FRAME_DURATION_MS = 150


class CharacterLayer(RenderLayer):
    def __init__(self, assets: Assets, y: int = 48) -> None:
        self.assets = assets
        self.y = y

    def render(self, surface: Surface, now_ms: int) -> None:
        col = 0
        for direction in Direction:
            animation = self.assets.pacman[direction]
            x = col * SPRITE_STRIDE
            surface.blit(
                self.get_current_sprite(now_ms, animation, FRAME_DURATION_MS),
                (x, self.y),
            )
            col += 1

        for kind in GhostKind:
            animation = self.assets.ghosts.by_kind[kind]
            x = col * SPRITE_STRIDE
            surface.blit(
                self.get_current_sprite(now_ms, animation, FRAME_DURATION_MS),
                (x, self.y),
            )
            col += 1

        frightened = self.assets.ghosts.frightened
        x = col * SPRITE_STRIDE
        surface.blit(
            self.get_current_sprite(now_ms, frightened, FRAME_DURATION_MS),
            (x, self.y),
        )
