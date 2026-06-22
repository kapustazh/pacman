from __future__ import annotations

from abc import ABC, abstractmethod

from pygame.surface import Surface

from entities.sprite_layer import SpriteLayer
from game.level import CellPos


class GameEntity(ABC):
    """BOILERPLATE: game logic/draw state without pygame Sprite inheritance."""

    __slots__ = ("cell", "center", "_layer")

    def __init__(
        self,
        cell: CellPos,
        center: tuple[int, int],
        layer: SpriteLayer,
    ) -> None:
        self.cell = cell
        self.center = center
        self._layer = int(layer)

    @property
    def layer(self) -> int:
        """Return pygame layer index for LayeredUpdates."""
        return self._layer

    @property
    @abstractmethod
    def image(self) -> Surface:
        """Return current drawable surface."""

    def update(self, dt: float, now_ms: int) -> None:
        """Default no-op for static entities."""
