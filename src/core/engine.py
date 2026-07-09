from __future__ import annotations

from dataclasses import replace

from core.context import GameContext
from core.scene_manager import SceneManager
from core.state import GameState

import pygame
from pygame.surface import Surface

from managers.highscore_manager import HighscoreManager
from sprites.assets import Assets
from states.text import ArcadeTextRenderer


BG_COLOR = (0, 0, 0)


class GameEngine:
    """Runs the pygame loop and delegates to the active scene stack."""

    def __init__(
        self,
        screen: Surface,
        assets: Assets,
        text: ArcadeTextRenderer,
        highscores: HighscoreManager,
        config: dict[str, object],
        initial_state: GameState,
        window_size: tuple[int, int] = (1920, 1080),
        target_fps: int = 120,
    ) -> None:
        """Wire shared context and push the first scene.

        Args:
            screen: Main display surface.
            assets: Loaded sprite catalog.
            text: Arcade font renderer.
            highscores: Persistent score table.
            config: Gameplay settings from config file.
            initial_state: Scene shown on startup.
            window_size: Windowed resolution restored when leaving fullscreen.
            target_fps: Frame rate cap for the main loop.
        """
        self._window_size = window_size
        self._fullscreen = False
        self._clock = pygame.time.Clock()
        self._scene_manager = SceneManager()
        self._context = GameContext(
            screen=screen,
            assets=assets,
            text=text,
            scene_manager=self._scene_manager,
            highscores=highscores,
            config=config,
        )
        self._target_fps = target_fps
        self._scene_manager.change(initial_state)
        self._scene_manager.flush(self._context)

    def run(self) -> None:
        """Poll events, update scenes, and flip the display until quit."""
        while not self._scene_manager.shutdown_requested:
            dt = self._clock.tick(self._target_fps) / 1000.0
            now_ms = pygame.time.get_ticks()
            events = self._handle_global_events(pygame.event.get())

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
        """Draw visible scenes from the first opaque layer downward."""
        stack = self._scene_manager.stack_bottom_up()
        if not stack:
            return

        draw_from = 0
        for index, state in enumerate(stack):
            if state.covers_previous_layers():
                draw_from = index

        for state in stack[draw_from:]:
            state.draw(self._context.screen, self._context)

    def _handle_global_events(
        self, events: list[pygame.event.Event]
    ) -> list[pygame.event.Event]:
        """Handle engine-level input and return events for scenes."""
        remaining: list[pygame.event.Event] = []
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self._toggle_fullscreen()
                continue
            remaining.append(event)
        return remaining

    def _toggle_fullscreen(self) -> None:
        """Switch between windowed and fullscreen display."""
        if self._fullscreen:
            screen = pygame.display.set_mode(self._window_size, vsync=1)
        else:
            screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN, vsync=1
            )
        self._fullscreen = not self._fullscreen
        self._context = replace(self._context, screen=screen)
