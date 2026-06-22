from __future__ import annotations

import pygame
from pygame.sprite import Sprite

from entities.game_entity import GameEntity


class EntitySprite(Sprite):
    """Thin pygame sprite shell that mirrors a slotted GameEntity."""

    __slots__ = ("entity",)

    def __init__(self, entity: GameEntity) -> None:
        super().__init__()
        self.entity = entity
        self._sync_from_entity()

    def update(self, dt: float, now_ms: int) -> None:
        """Advance entity state and refresh drawable rect."""
        self.entity.update(dt, now_ms)
        self.sync_from_entity()

    def sync_from_entity(self) -> None:
        """Mirror entity image and center into pygame rect."""
        self._sync_from_entity()

    def _sync_from_entity(self) -> None:
        image = self.entity.image
        self.image = image
        self.rect = image.get_rect(center=self.entity.center)
