from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StatePayload
from game.entity_factory import EntityFactory
from game.game_session import (
    GAME_OVER_DURATION_MS,
    LIFE_LOST_DURATION_MS,
    LEVEL_COMPLETE_DURATION_MS,
    READY_DURATION_MS,
    GameplayPhase,
    GameSession,
)
from game.game_world import GameWorld
from game.level import load_smoke_level
from game.render_config import MazeViewport, WorldRenderConfig
from rendering.hud_overlay import HudOverlay
from sprites.types import Direction


class PlayState(GameState):
    """Gameplay scene backed by GameWorld."""

    def __init__(self) -> None:
        self._world: GameWorld | None = None
        self._session: GameSession | None = None
        self._hud: HudOverlay | None = None
        self._maze_viewport: MazeViewport | None = None

    def enter(
        self,
        context: GameContext,
        payload: StatePayload | None = None,
    ) -> None:
        """Create a fresh world from smoke level boilerplate."""
        catalog = context.resources.get_asset_catalog()
        # DEMO: smoke level only; TODO: swap for real loader.
        layout = load_smoke_level()
        render_config = WorldRenderConfig.centered(
            layout,
            context.screen.get_size(),
        )
        factory = EntityFactory(catalog, render_config, layout)
        self._world = GameWorld(layout, factory)
        self._maze_viewport = render_config.viewport_for(layout)

        life_icon = catalog.pacman[Direction.RIGHT].frames[0]
        self._hud = HudOverlay(life_icon=life_icon)

        started_at = pygame.time.get_ticks()
        self._session = GameSession(phase_started_at_ms=started_at)
        self._session.enter_ready(started_at)

    def leave(self, context: GameContext) -> None:
        """Tear down world resources."""
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._session = None
        self._hud = None
        self._maze_viewport = None

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Route play input to world or scene transitions."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                from states.pause_state import PauseState

                context.scene_manager.push(PauseState())
                return
            direction = _direction_from_key(event.key)
            if (
                direction is not None
                and self._world is not None
                and self._session is not None
                and self._session.phase
                in (GameplayPhase.READY, GameplayPhase.PLAYING)
            ):
                self._world.request_turn(direction)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Advance gameplay phase, timer, and world animation."""
        if self._session is None or self._world is None:
            return

        phase = self._session.phase
        if phase == GameplayPhase.READY:
            if self._session.phase_elapsed_ms(now_ms) >= READY_DURATION_MS:
                self._session.begin_play(now_ms)
                self._world.start_auto_movement()
            self._world.update(dt, now_ms)
            return

        if phase == GameplayPhase.PLAYING:
            timer_expired = self._session.tick_timer(dt)
            self._world.update_player_movement(dt)
            self._world.update(dt, now_ms)
            if timer_expired:
                self._handle_life_lost(now_ms)
            return

        if phase == GameplayPhase.LIFE_LOST:
            if self._session.phase_elapsed_ms(now_ms) >= LIFE_LOST_DURATION_MS:
                self._finish_life_lost(now_ms)
            return

        if phase == GameplayPhase.LEVEL_COMPLETE:
            if (
                self._session.phase_elapsed_ms(now_ms)
                >= LEVEL_COMPLETE_DURATION_MS
            ):
                self._session.advance_level()
                self._session.enter_ready(now_ms)
            return

        if phase == GameplayPhase.GAME_OVER:
            if self._session.phase_elapsed_ms(now_ms) >= GAME_OVER_DURATION_MS:
                self._open_game_over(context)
            return

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw world, classic HUD bands, and phase message."""
        if (
            self._world is None
            or self._session is None
            or self._hud is None
            or self._maze_viewport is None
        ):
            return
        self._world.draw(surface)
        snapshot = self._session.snapshot(score=self._world.score)
        self._hud.draw(surface, snapshot, self._maze_viewport)

    def _handle_life_lost(self, now_ms: int) -> None:
        """Lose one life when timer expires or collision lands later."""
        if self._session is None:
            return
        self._session.lose_life(now_ms)
        if self._session.lives == 0:
            self._session.enter_game_over(now_ms)

    def _finish_life_lost(self, now_ms: int) -> None:
        """Respawn after death or end the run."""
        if self._session is None:
            return
        if self._session.lives <= 0:
            self._session.enter_game_over(now_ms)
            return
        self._session.reset_level_timer()
        self._session.enter_ready(now_ms)

    def _open_game_over(self, context: GameContext) -> None:
        """Transition to game-over screen with final score."""
        from states.game_over_state import GameOverState

        score = self._world.score if self._world is not None else 0
        context.scene_manager.change(GameOverState(), {"score": score})


def _direction_from_key(key: int) -> Direction | None:
    if key in (pygame.K_UP, pygame.K_w):
        return Direction.UP
    if key in (pygame.K_DOWN, pygame.K_s):
        return Direction.DOWN
    if key in (pygame.K_LEFT, pygame.K_a):
        return Direction.LEFT
    if key in (pygame.K_RIGHT, pygame.K_d):
        return Direction.RIGHT
    return None
