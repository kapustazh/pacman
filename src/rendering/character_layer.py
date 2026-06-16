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
            frame_index = (now_ms // FRAME_DURATION_MS) % animation.num_frames
            x = col * SPRITE_STRIDE
            surface.blit(animation.frames[frame_index], (x, self.y))
            col += 1

        for kind in GhostKind:
            animation = self.assets.ghosts.by_kind[kind]
            frame_index = (now_ms // FRAME_DURATION_MS) % animation.num_frames
            x = col * SPRITE_STRIDE
            surface.blit(animation.frames[frame_index], (x, self.y))
            col += 1

        frightened = self.assets.ghosts.frightened
        frame_index = (now_ms // FRAME_DURATION_MS) % frightened.num_frames
        x = col * SPRITE_STRIDE
        surface.blit(frightened.frames[frame_index], (x, self.y))
