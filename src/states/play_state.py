from __future__ import annotations

import random

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from game.game_session import GameplayPhase, GameSession
from game.game_world import (
    GameWorld,
    request_turn,
    update_fruit_spawns,
    update_player_movement,
)
from game.level import load_level
from game.render_config import MazeBounds, WorldRenderConfig
from rendering.hud_overlay import HudOverlay
from sprites.sprite_types import Direction


class PlayState(GameState):
    """Gameplay scene backed by GameWorld."""

    def __init__(self) -> None:
        self._world: GameWorld | None = None
        self._session: GameSession | None = None
        self._level_index: int = 0
        self._level_seed: int = 42
        self._hud: HudOverlay | None = None
        self._maze_bounds: MazeBounds | None = None

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Create a fresh world from smoke level boilerplate."""
        catalog = context.assets
        life_icon = catalog.pacman[Direction.LEFT].frames[1]
        self._hud = HudOverlay(
            context.text,
            life_icon=life_icon,
            fruit_icon=None,
        )

        started_at = pygame.time.get_ticks()
        self._session = GameSession(
            phase_started_at_ms=started_at,
            high_score=context.highscores.top_score(),
        )
        self._level_index = 0
        self._level_seed = int(context.config.get("seed", 42))
        self._build_world(context)
        self._session.enter_ready(started_at)

    def leave(self, context: GameContext) -> None:
        """Tear down world resources."""
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._session = None
        self._level_index = 0
        self._level_seed = 42
        self._hud = None
        self._maze_bounds = None

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
                request_turn(self._world, direction)

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """Advance gameplay phase, timer, and world animation."""
        if self._session is None or self._world is None:
            return

        match self._session.phase:
            case GameplayPhase.READY:
                self._update_ready(dt, now_ms)
            case GameplayPhase.PLAYING:
                self._update_playing(dt, now_ms)
            case GameplayPhase.LIFE_LOST:
                self._update_life_lost(now_ms)
            case GameplayPhase.LEVEL_COMPLETE:
                self._update_level_complete(dt, now_ms, context)
            case GameplayPhase.GAME_OVER:
                self._update_game_over(now_ms, context)

        self._sync_session_score()

    def _update_ready(self, dt: float, now_ms: int) -> None:
        if self._session is None or self._world is None:
            return
        if (
            self._session.phase_elapsed_ms(now_ms)
            >= GameSession.READY_DURATION_MS
        ):
            self._session.begin_play(now_ms)
            self._world.start_auto_movement()
        self._world.update(dt, now_ms)

    def _update_playing(self, dt: float, now_ms: int) -> None:
        if self._session is None or self._world is None:
            return
        if self._world.player_is_dying:
            self._world.update(dt, now_ms)
            if self._world.player_death_finished:
                self._handle_life_lost(now_ms)
            return
        if not self._world.is_frozen:
            timer_expired = self._session.tick_timer(dt)
            update_player_movement(self._world, dt, now_ms)
            update_fruit_spawns(
                self._world,
                self._session.level_elapsed_s(),
                now_ms,
            )
            self._world.update(dt, now_ms)
            if timer_expired:
                self._handle_life_lost(now_ms)
            elif self._world.all_consumables_cleared:
                self._session.sync_score(self._world.score)
                self._world.freeze_gameplay()
                self._session.enter_level_complete(now_ms)
        else:
            self._world.update(dt, now_ms)

    def _update_life_lost(self, now_ms: int) -> None:
        if self._session is None:
            return
        if (
            self._session.phase_elapsed_ms(now_ms)
            >= GameSession.LIFE_LOST_DURATION_MS
        ):
            self._finish_life_lost(now_ms)

    def _update_level_complete(
        self,
        dt: float,
        now_ms: int,
        context: GameContext,
    ) -> None:
        if self._session is None or self._world is None:
            return
        self._world.update(dt, now_ms)
        elapsed_ms = self._session.phase_elapsed_ms(now_ms)
        cycle_ms = elapsed_ms % 400
        self._world.set_wall_flash(cycle_ms < 200)
        if elapsed_ms >= GameSession.LEVEL_COMPLETE_DURATION_MS:
            levels = context.config.get("levels", [])
            if self._level_index + 1 >= len(levels):
                self._open_end_screen(context, won=True)
                return
            self._level_index += 1
            self._level_seed = random.randint(0, 100000)
            self._session.advance_level()
            self._reload_world(context)
            self._session.reset_level_timer()
            self._session.enter_ready(now_ms)

    def _update_game_over(self, now_ms: int, context: GameContext) -> None:
        if self._session is None:
            return
        if (
            self._session.phase_elapsed_ms(now_ms)
            >= GameSession.GAME_OVER_DURATION_MS
        ):
            self._open_end_screen(context, won=False)

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw world, classic HUD bands, and phase message."""
        if (
            self._world is None
            or self._session is None
            or self._hud is None
            or self._maze_bounds is None
        ):
            return
        self._world.draw(surface)
        self._hud.draw_score_popups(surface, self._world.score_popups)
        self._hud.draw(surface, self._session, self._maze_bounds)

    def _sync_session_score(self) -> None:
        """Keep session score/high-score in sync with world during update."""
        if self._session is None or self._world is None:
            return
        self._session.sync_score(self._world.score)
        self._session.update_high_score(self._session.score)

    def _build_world(self, context: GameContext) -> None:
        """Load procedural level and spawn a fresh GameWorld."""
        assert self._session is not None
        catalog = context.assets
        layout = load_level(
            context.config,
            self._level_index,
            self._level_seed,
        )
        render_config = WorldRenderConfig.centered(
            layout,
            context.screen.get_size(),
        )
        self._maze_bounds = render_config.maze_bounds(layout)
        initial_score = self._session.score if self._session is not None else 0
        level_number = (
            self._session.level_number if self._session is not None else 1
        )
        self._world = GameWorld(
            layout,
            catalog,
            render_config,
            initial_score=initial_score,
            level_number=level_number,
        )
        if self._hud is not None:
            self._hud.set_fruit_icon(self._world.level_fruit_surface)

    def _reload_world(self, context: GameContext) -> None:
        """Tear down world and build a new one for the next level."""
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._build_world(context)

    def _handle_life_lost(self, now_ms: int) -> None:
        """Lose one life when timer expires or ghost collision."""
        if self._session is None:
            return
        if self._world is not None:
            self._world.freeze_gameplay()
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
        if self._world is not None:
            self._world.respawn_player()
            self._world.unfreeze_gameplay()
        self._session.reset_level_timer()
        self._session.enter_ready(now_ms)

    def _open_end_screen(self, context: GameContext, *, won: bool) -> None:
        """Transition to end screen with final score."""
        from states.game_over_state import GameOverState

        score = self._session.score if self._session is not None else 0
        if self._world is not None:
            score = max(score, self._world.score)
        context.scene_manager.change(
            GameOverState(),
            {"score": score, "won": won},
        )


_KEY_TO_DIRECTION: dict[int, Direction] = {
    pygame.K_UP: Direction.UP,
    pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_d: Direction.RIGHT,
}


def _direction_from_key(key: int) -> Direction | None:
    return _KEY_TO_DIRECTION.get(key)
