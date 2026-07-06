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
    """Base class for scenes managed by ``SceneManager``."""

    @abstractmethod
    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Prepare the scene when it becomes active.

        Args:
            context: Shared game context.
            enter_data: Optional startup data from the previous scene.
        """

    @abstractmethod
    def leave(self, context: GameContext) -> None:
        """Release resources when the scene is removed.

        Args:
            context: Shared game context.
        """

    @abstractmethod
    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Handle pygame input for this scene.

        Args:
            events: Events polled this frame.
            context: Shared game context.
        """

    @abstractmethod
    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Advance scene logic.

        Args:
            dt: Seconds since the last frame.
            now_ms: Monotonic pygame clock in milliseconds.
            context: Shared game context.
        """

    @abstractmethod
    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw this scene onto the target surface.

        Args:
            surface: Destination display surface.
            context: Shared game context.
        """

    def covers_previous_layers(self) -> bool:
        """Tell the engine to skip drawing scenes below this one.

        Returns:
            True when this scene fully covers earlier layers.
        """
        return False
