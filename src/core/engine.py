from __future__ import annotations

from core.context import GameContext
from core.scene_manager import SceneManager
from core.state import GameState

import pygame
from pygame.surface import Surface

from sprites.assets import Assets
from states.text import ArcadeTextRenderer


BG_COLOR = (0, 0, 0)


class GameEngine:
    """Main pygame loop delegating behavior to SceneManager."""

    __slots__ = ("_clock", "_context", "_scene_manager", "_target_fps")

    def __init__(
        self,
        screen: Surface,
        assets: Assets,
        text: ArcadeTextRenderer,
        initial_state: GameState,
        target_fps: int = 60,
    ) -> None:
        self._clock = pygame.time.Clock()
        self._scene_manager = SceneManager()
        self._context = GameContext(
            screen=screen,
            assets=assets,
            text=text,
            scene_manager=self._scene_manager,
        )
        self._target_fps = target_fps
        self._scene_manager.change(initial_state)
        self._scene_manager.flush(self._context)

    def run(self) -> None:
        """Run main game loop until a state or QUIT event requests shutdown."""
        while not self._scene_manager.shutdown_requested:
            dt = self._clock.tick(self._target_fps) / 1000.0
            now_ms = pygame.time.get_ticks()
            events = pygame.event.get()

            if any(event.type == pygame.QUIT for event in events):
                self._scene_manager.request_shutdown()
            else:
                top = self._scene_manager.top()
                if top is not None:
                    top.handle_events(events, self._context)

            self._scene_manager.flush(self._context)
            if self._scene_manager.shutdown_requested:
                break

            top = self._scene_manager.top()
            if top is not None:
                top.update(dt, now_ms, self._context)

            self._scene_manager.flush(self._context)
            if self._scene_manager.shutdown_requested:
                break

            self._context.screen.fill(BG_COLOR)
            self._draw_stack()
            pygame.display.flip()

    def _draw_stack(self) -> None:
        """Draw scene stack, skipping layers covered by opaque states."""
        stack = self._scene_manager.stack_bottom_up()
        if not stack:
            return

        draw_from = 0
        for index, state in enumerate(stack):
            if state.covers_previous_layers():
                draw_from = index

        for state in stack[draw_from:]:
            state.draw(self._context.screen, self._context)
