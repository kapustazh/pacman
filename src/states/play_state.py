from __future__ import annotations

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
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
from rendering.level_clear_effect import LevelClearEffect
from sprites.sprite_types import Direction


class PlayState(GameState):
    """Gameplay scene backed by GameWorld."""

    def __init__(self) -> None:
        self._world: GameWorld | None = None
        self._session: GameSession | None = None
        self._hud: HudOverlay | None = None
        self._maze_viewport: MazeViewport | None = None
        self._level_clear_effect = LevelClearEffect()

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Create a fresh world from smoke level boilerplate."""
        catalog = context.resources.get_asset_catalog()
        life_icon = catalog.pacman[Direction.RIGHT].frames[0]
        self._hud = HudOverlay(
            context.resources.get_text_renderer(),
            life_icon=life_icon,
        )

        started_at = pygame.time.get_ticks()
        self._session = GameSession(phase_started_at_ms=started_at)
        self._build_world(context)
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
                if (
                    self._session is not None
                    and self._session.phase == GameplayPhase.LEVEL_COMPLETE
                ):
                    continue
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
            if not self._world.is_frozen:
                timer_expired = self._session.tick_timer(dt)
                self._world.update_player_movement(dt)
                self._world.update(dt, now_ms)
                if timer_expired:
                    self._handle_life_lost(now_ms)
                elif self._world.all_consumables_cleared:
                    self._session.sync_score(self._world.score)
                    self._world.freeze_gameplay()
                    self._session.enter_level_complete(now_ms)
            else:
                self._world.update(dt, now_ms)
            return

        if phase == GameplayPhase.LIFE_LOST:
            if self._session.phase_elapsed_ms(now_ms) >= LIFE_LOST_DURATION_MS:
                self._finish_life_lost(now_ms)
            return

        if phase == GameplayPhase.LEVEL_COMPLETE:
            self._world.update(dt, now_ms)
            if (
                self._session.phase_elapsed_ms(now_ms)
                >= LEVEL_COMPLETE_DURATION_MS
            ):
                self._session.advance_level()
                self._reload_world(context)
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
        if self._session.phase == GameplayPhase.LEVEL_COMPLETE:
            elapsed_ms = self._session.phase_elapsed_ms(pygame.time.get_ticks())
            overlay = self._level_clear_effect.surface_for(
                self._maze_viewport,
                elapsed_ms,
            )
            if overlay is not None:
                surface.blit(overlay, (self._maze_viewport.x, self._maze_viewport.y))
        world_score = self._world.score
        snapshot = self._session.snapshot(score=world_score)
        self._hud.draw(surface, snapshot, self._maze_viewport)

    def _build_world(self, context: GameContext) -> None:
        """Load smoke level and spawn a fresh GameWorld."""
        catalog = context.resources.get_asset_catalog()
        layout = load_smoke_level()
        render_config = WorldRenderConfig.centered(
            layout,
            context.screen.get_size(),
        )
        factory = EntityFactory(catalog, render_config, layout)
        initial_score = self._session.score if self._session is not None else 0
        self._world = GameWorld(layout, factory, initial_score=initial_score)
        self._maze_viewport = render_config.viewport_for(layout)

    def _reload_world(self, context: GameContext) -> None:
        """Tear down the active world and build a new one for the next level."""
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._build_world(context)

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

        score = self._session.score if self._session is not None else 0
        if self._world is not None:
            score = max(score, self._world.score)
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
