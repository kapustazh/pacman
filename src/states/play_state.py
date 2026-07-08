# [transition] SCRUM-35 — main loop from wehan start/handle_input.

from __future__ import annotations

import random
import threading

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import GameState, StateEnterData
from game.game_session import GameplayPhase, GameSession
from game.game_world import (
    GameWorld,
    request_turn,
    update_fruit_spawns,
    update_ghost_movement,
    update_player_movement,
)
from game.level import LevelLayout, load_level
from game.render_config import MazeBounds, WorldRenderConfig
from rendering.hud_overlay import HudOverlay
from sprites.sprite_types import Direction
from states.text import ArcadeTextColor

LOADING_TEXT_Y: int = 400
LOADING_PACMAN_Y: int = 440
LOADING_DOT_CYCLE_MS: int = 400
CHEAT_MESSAGE_MARGIN: int = 12
CHEAT_MESSAGE_SCALE: int = 2


def _cheat_labels(
    *, invincible: bool, frozen: bool, speed_active: bool
) -> list[str]:
    """Build HUD labels for active cheat toggles.

    Args:
        invincible: Whether invincibility cheat is on.
        frozen: Whether ghost-freeze cheat is on.
        speed_active: Whether speed cheat is on.

    Returns:
        Display labels for each active cheat.
    """
    labels: list[str] = []
    if invincible:
        labels.append("INVINCIBLE")
    if frozen:
        labels.append("FREEZE")
    if speed_active:
        labels.append("SPEED")
    return labels


class PlayState(GameState):
    """Active gameplay scene backed by GameWorld and GameSession."""

    def __init__(self) -> None:
        """Initialize empty world, session, and loading state."""
        self._world: GameWorld | None = None
        self._session: GameSession | None = None
        self._level_index: int = 0
        self._level_seed: int = 42
        self._hud: HudOverlay | None = None
        self._maze_bounds: MazeBounds | None = None
        self._loading_thread: threading.Thread | None = None
        self._pending_layout: LevelLayout | None = None
        self._loading_error: BaseException | None = None
        self._load_id: int = 0

    def enter(
        self,
        context: GameContext,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Create session state and start loading the first level.

        Args:
            context: Shared game context with config, assets, and scores.
            enter_data: Optional payload from the previous scene (unused).
        """
        catalog = context.assets
        life_icon = catalog.pacman[Direction.LEFT].frames[1]
        self._hud = HudOverlay(
            context.text,
            life_icon=life_icon,
            fruit_icon=None,
        )

        started_at = pygame.time.get_ticks()
        config = context.config
        level_max_time_s = int(config.get("level_max_time", 90))
        self._session = GameSession(
            phase_started_at_ms=started_at,
            high_score=context.highscores.top_score(),
            lives=int(config.get("lives", 3)),
            level_time_limit_s=level_max_time_s,
            remaining_time_ms=level_max_time_s * 1000,
        )
        self._level_index = 0
        self._level_seed = int(context.config.get("seed", 42))
        self._start_loading(context)

    def leave(self, context: GameContext) -> None:
        """Tear down world resources and reset play state.

        Args:
            context: Shared game context (unused).
        """
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._session = None
        self._level_index = 0
        self._level_seed = 42
        self._hud = None
        self._maze_bounds = None
        self._load_id += 1
        self._loading_thread = None
        self._pending_layout = None
        self._loading_error = None

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Route keyboard input to movement, cheats, pause, and phase skips.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for scene transitions.
        """
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
            if event.key == pygame.K_i and self._world is not None:
                self._world.toggle_invincible()
                continue
            if event.key == pygame.K_f and self._world is not None:
                self._world.toggle_ghosts_frozen()
                continue
            if (
                event.key in (pygame.K_PLUS, pygame.K_EQUALS)
                and self._world is not None
            ):
                self._world.adjust_player_speed(
                    -GameWorld.PLAYER_SPEED_STEP_MS
                )
                continue
            if event.key == pygame.K_MINUS and self._world is not None:
                self._world.adjust_player_speed(GameWorld.PLAYER_SPEED_STEP_MS)
                continue
            if event.key == pygame.K_l and self._session is not None:
                self._session.lives += 1
                continue
            if (
                event.key == pygame.K_n
                and self._session is not None
                and self._world is not None
            ):
                self._advance_level_or_win(context, pygame.time.get_ticks())
                continue
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
        """Advance loading, gameplay phase logic, and world animation.

        Args:
            dt: Elapsed seconds since the last frame.
            now_ms: Monotonic clock in milliseconds.
            context: Shared game context for scene transitions.
        """
        if self._loading_thread is not None:
            self._poll_loading(context, now_ms)
            return
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
        """Wait out the ready delay, then start movement.

        Args:
            dt: Elapsed seconds since the last frame.
            now_ms: Monotonic clock in milliseconds.
        """
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
        """Run movement, timer, fruit spawns, and win/lose checks.

        Args:
            dt: Elapsed seconds since the last frame.
            now_ms: Monotonic clock in milliseconds.
        """
        if self._session is None or self._world is None:
            return
        if self._world.player_is_dying:
            self._world.update(dt, now_ms)
            if self._world.player_death_finished:
                self._handle_life_lost(now_ms)
            return
        if not self._world.frozen:
            timer_expired = self._session.tick_timer(dt)
            update_player_movement(self._world, dt, now_ms)
            update_ghost_movement(self._world, dt, now_ms)
            update_fruit_spawns(
                self._world,
                self._session.level_elapsed_s(),
                now_ms,
            )
            self._world.update(dt, now_ms)
            if self._world.player_is_dying:
                return
            if self._world.all_consumables_cleared:
                self._session.sync_score(self._world.score)
                self._world.freeze_gameplay()
                self._session.enter_level_complete(now_ms)
            elif timer_expired:
                self._handle_life_lost(now_ms)
        else:
            self._world.update(dt, now_ms)

    def _update_life_lost(self, now_ms: int) -> None:
        """Finish the life-lost delay and respawn or end the run.

        Args:
            now_ms: Monotonic clock in milliseconds.
        """
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
        """Animate level-complete effects and advance when the timer ends.

        Args:
            dt: Elapsed seconds since the last frame.
            now_ms: Monotonic clock in milliseconds.
            context: Shared game context for scene transitions.
        """
        if self._session is None or self._world is None:
            return
        self._world.update(dt, now_ms)
        elapsed_ms = self._session.phase_elapsed_ms(now_ms)
        # [transition SCRUM-34] level-complete wall flash
        cycle_ms = elapsed_ms % 400
        self._world.set_wall_flash(cycle_ms < 200)
        if elapsed_ms >= GameSession.LEVEL_COMPLETE_DURATION_MS:
            self._advance_level_or_win(context, now_ms)

    def _advance_level_or_win(self, context: GameContext, now_ms: int) -> None:
        """Load the next level or open the win screen.

        Args:
            context: Shared game context for scene transitions.
            now_ms: Monotonic clock in milliseconds (unused).
        """
        if self._session is None:
            return
        levels = context.config.get("levels", [])
        if self._level_index + 1 >= len(levels):
            self._open_end_screen(context, won=True)
            return
        self._level_index += 1
        self._level_seed = random.randint(0, 100000)
        self._session.advance_level()
        self._reload_world(context)

    def _update_game_over(self, now_ms: int, context: GameContext) -> None:
        """Wait out the game-over delay, then open the end screen.

        Args:
            now_ms: Monotonic clock in milliseconds.
            context: Shared game context for scene transitions.
        """
        if self._session is None:
            return
        if (
            self._session.phase_elapsed_ms(now_ms)
            >= GameSession.GAME_OVER_DURATION_MS
        ):
            self._open_end_screen(context, won=False)

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw loading UI or the maze, HUD, and cheat overlay.

        Args:
            surface: Destination draw target.
            context: Shared game context with assets and text renderer.
        """
        if self._loading_thread is not None:
            self._draw_loading(surface, context)
            self._draw_cheat_message(surface, context)
            return
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
        self._draw_cheat_message(surface, context)

    def _draw_cheat_message(
        self, surface: Surface, context: GameContext
    ) -> None:
        """Draw active cheat labels in the bottom-right corner.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        if self._world is None:
            return
        labels = _cheat_labels(
            invincible=self._world.invincible,
            frozen=self._world.ghosts_frozen,
            speed_active=self._world.speed_cheat_active,
        )
        if not labels:
            return
        rendered = context.text.render(
            "CHEATS - " + " ".join(labels),
            ArcadeTextColor.RED,
            CHEAT_MESSAGE_SCALE,
        )
        rect = rendered.get_rect(
            bottomright=(
                surface.get_width() - CHEAT_MESSAGE_MARGIN,
                surface.get_height() - CHEAT_MESSAGE_MARGIN,
            )
        )
        surface.blit(rendered, rect)

    def _draw_loading(self, surface: Surface, context: GameContext) -> None:
        """Show animated loading text while the maze generates.

        Args:
            surface: Destination draw target.
            context: Shared game context with assets and text renderer.
        """
        now_ms = pygame.time.get_ticks()
        dots = "." * (1 + (now_ms // LOADING_DOT_CYCLE_MS) % 3)
        context.text.draw_centered_arcade_text(
            surface,
            f"GENERATING MAZE{dots}",
            LOADING_TEXT_Y,
            ArcadeTextColor.YELLOW,
        )
        frame = context.assets.pacman[Direction.RIGHT].frame_at(now_ms)
        rect = frame.get_rect(
            center=(surface.get_width() // 2, LOADING_PACMAN_Y)
        )
        surface.blit(frame, rect)

    def _sync_session_score(self) -> None:
        """Mirror world score and high score into the session."""
        if self._session is None or self._world is None:
            return
        self._session.sync_score(self._world.score)
        self._session.update_high_score(self._session.score)

    def _build_world(self, context: GameContext, layout: LevelLayout) -> None:
        """Construct GameWorld and HUD fruit icon from a loaded layout.

        Args:
            context: Shared game context with config and assets.
            layout: Generated level layout to instantiate.
        """
        if self._session is None:
            return
        catalog = context.assets
        render_config = WorldRenderConfig.centered(
            layout,
            context.screen.get_size(),
        )
        self._maze_bounds = render_config.maze_bounds(layout)
        initial_score = self._session.score
        level_number = self._session.level_number
        config = context.config
        self._world = GameWorld(
            layout,
            catalog,
            render_config,
            initial_score=initial_score,
            level_number=level_number,
            level_max_time_s=int(config.get("level_max_time", 90)),
            pellet_points=int(config.get("points_per_pacgum", 10)),
            power_pellet_points=int(config.get("points_per_super_pacgum", 50)),
            ghost_points=int(config.get("points_per_ghost", 200)),
        )
        if self._hud is not None:
            self._hud.set_fruit_icon(self._world.level_fruit_surface)

    def _reload_world(self, context: GameContext) -> None:
        """Tear down the current world and start loading the next level.

        Args:
            context: Shared game context for level loading.
        """
        if self._world is not None:
            self._world.teardown()
            self._world = None
        self._start_loading(context)

    def _start_loading(self, context: GameContext) -> None:
        """Generate the maze on a background thread.

        Args:
            context: Shared game context with level config.
        """
        self._load_id += 1
        load_id = self._load_id
        self._pending_layout = None
        self._loading_error = None
        config = context.config
        level_index = self._level_index
        seed = self._level_seed

        def generate() -> None:
            """Load level layout on the worker thread."""
            try:
                layout = load_level(config, level_index, seed)
            except BaseException as exc:  # noqa: BLE001 - surfaced below
                if load_id != self._load_id:
                    return
                self._loading_error = exc
                return
            if load_id != self._load_id:
                return
            self._pending_layout = layout

        self._loading_thread = threading.Thread(target=generate, daemon=True)
        self._loading_thread.start()

    def _poll_loading(self, context: GameContext, now_ms: int) -> None:
        """Finish world setup after background level generation completes.

        Args:
            context: Shared game context for world construction.
            now_ms: Monotonic clock used to enter the ready phase.

        Raises:
            BaseException: Re-raises any error captured during generation.
        """
        if self._loading_thread is None or self._loading_thread.is_alive():
            return
        self._loading_thread = None
        if self._loading_error is not None:
            raise self._loading_error
        if self._pending_layout is None or self._session is None:
            return
        self._build_world(context, self._pending_layout)
        self._pending_layout = None
        self._session.reset_level_timer()
        self._session.enter_ready(now_ms)

    def _handle_life_lost(self, now_ms: int) -> None:
        """Freeze play and enter life-lost or game-over phase.

        Args:
            now_ms: Monotonic clock in milliseconds.
        """
        if self._session is None:
            return
        if self._world is not None:
            self._world.freeze_gameplay()
        self._session.lose_life(now_ms)
        if self._session.lives == 0:
            self._session.enter_game_over(now_ms)

    def _finish_life_lost(self, now_ms: int) -> None:
        """Respawn actors after a death or end the run when out of lives.

        Args:
            now_ms: Monotonic clock used to enter the next phase.
        """
        if self._session is None:
            return
        if self._session.lives <= 0:
            self._session.enter_game_over(now_ms)
            return
        if self._world is not None:
            self._world.respawn_player()
            self._world.respawn_ghosts()
            self._world.reset_fruit_spawns()
            self._world.unfreeze_gameplay()
        self._session.reset_level_timer()
        self._session.enter_ready(now_ms)

    def _open_end_screen(self, context: GameContext, *, won: bool) -> None:
        """Switch to the end screen with the final score.

        Args:
            context: Shared game context for scene transitions.
            won: Whether the player cleared all levels.
        """
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
    """Map a pygame key code to a movement direction.

    Args:
        key: Pygame key constant from a keydown event.

    Returns:
        Matching direction, or None if the key is not a movement binding.
    """
    return _KEY_TO_DIRECTION.get(key)
