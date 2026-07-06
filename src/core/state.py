from __future__ import annotations

from abc import ABC, abstractmethod

import pygame
from pygame.surface import Surface

from core.context import GameContext

StateEnterData = dict[str, object]

BACK_KEYS = (
    pygame.K_ESCAPE,
    pygame.K_RETURN,
    pygame.K_SPACE,
    pygame.K_BACKSPACE,
)


class GameState(ABC):
    """
    Base interface for all scenes managed by SceneManager.
    """

    @abstractmethod
    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Enter state with optional initialization data."""

    @abstractmethod
    def leave(self, context: GameContext) -> None:
        """Leave state, releasing any allocated resources."""

    @abstractmethod
    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Handle pygame events for this state."""

    @abstractmethod
    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Advance state simulation."""

    @abstractmethod
    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw state to target surface."""

    def covers_previous_layers(self) -> bool:
        """When True, states below this one are skipped during draw."""
        return False
