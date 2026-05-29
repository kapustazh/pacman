from abc import ABC, abstractmethod
from pygame.surface import Surface  # noqa E402
from sprites import AnimatedSprite


class LayerRenderError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Layer render error: {detail}")


class RenderLayer(ABC):

    @abstractmethod
    def render(self, surface: Surface) -> None:
        pass

    def get_current_sprite(
        self,
        current_time: int,
        sprite: AnimatedSprite,
        animation: int = 150,
    ) -> Surface:
        frame_index = (current_time // animation) % sprite.num_frames
        return sprite.frames[frame_index]
