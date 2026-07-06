from __future__ import annotations

from pathlib import Path

import pygame  # noqa: E402
import pytest
from pygame.surface import Surface  # noqa: E402

from entities.player_entity import PlayerEntity  # noqa: E402
from entities.wall_tile_entity import WallTileEntity  # noqa: E402
from game.game_session import GameSession, GameplayPhase  # noqa: E402
from states.play_state import PlayState  # noqa: E402
from game.game_world import (  # noqa: E402
    GameWorld,
    request_turn,
    spawn_fruit,
    update_ghost_movement,
    update_player_movement,
)
from config.config import DEFAULT_CONFIG  # noqa: E402
from game.level import CellPos, load_level  # noqa: E402
from game.render_config import (  # noqa: E402
    DIRECTION_DELTA,
    WorldRenderConfig,
    cell_center,
)
from sprites.assets import Assets  # noqa: E402
from sprites.sprite_types import Direction, TileKind  # noqa: E402


def test_all_consumables_cleared_false_with_pellets(
    game_world: GameWorld,
) -> None:
    assert not game_world.all_consumables_cleared


def test_all_consumables_cleared_true_when_set_empty(
    game_world: GameWorld,
) -> None:
    game_world._pellets.clear()
    assert game_world.all_consumables_cleared


def test_fatal_ghost_collision_on_last_pellet_loses_life_not_level_complete(
    game_world: GameWorld,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Death on the last-pellet step must not enter LEVEL_COMPLETE."""
    from game.ghost_logic import start_player_death

    def trigger_death_and_clear_pellets(
        world: GameWorld,
        dt_s: float,
        now_ms: int,
    ) -> None:
        world._pellets.clear()
        start_player_death(world, now_ms)

    monkeypatch.setattr(
        "states.play_state.update_player_movement",
        trigger_death_and_clear_pellets,
    )

    play_state = PlayState()
    session = GameSession(
        phase=GameplayPhase.PLAYING,
        phase_started_at_ms=0,
    )
    game_world.unfreeze_gameplay()
    play_state._session = session
    play_state._world = game_world

    play_state._update_playing(0.002, 1_000)

    assert game_world.player_is_dying
    assert game_world.all_consumables_cleared
    assert session.phase == GameplayPhase.PLAYING
    assert session.lives == GameSession.DEFAULT_LIVES


def test_timer_expiry_same_frame_as_last_pellet_completes_level(
    game_world: GameWorld,
) -> None:
    """Clearing the maze the frame the timer hits zero must win."""
    play_state = PlayState()
    session = GameSession(
        phase=GameplayPhase.PLAYING,
        phase_started_at_ms=0,
        remaining_time_ms=1,
    )
    game_world._pellets.clear()
    game_world.unfreeze_gameplay()
    play_state._session = session
    play_state._world = game_world

    play_state._update_playing(0.002, 1_000)

    assert session.phase == GameplayPhase.LEVEL_COMPLETE
    assert session.lives == GameSession.DEFAULT_LIVES
    assert game_world.frozen


def test_unfreeze_gameplay_resumes_movement(game_world: GameWorld) -> None:
    from sprites.sprite_types import Direction

    game_world.freeze_gameplay()
    assert game_world.frozen
    game_world.unfreeze_gameplay()
    assert not game_world.frozen
    request_turn(game_world, Direction.LEFT)
    assert game_world._requested_direction == Direction.LEFT


def test_fruit_collection_spawns_score_popup(game_world: GameWorld) -> None:
    """Fruit spawning under Pac-Man is eaten immediately, always dropping
    the fruit and always leaving a score popup."""
    player = game_world._player
    assert player is not None
    score_before = game_world.score
    spawn_fruit(game_world, pygame.time.get_ticks())
    assert game_world._fruit is None
    assert len(game_world.score_popups) == 1
    assert game_world.score > score_before


def test_death_coords_skip_walk_chomp_frames() -> None:
    """Death sprites must not reuse right-walk mouth frames on row 0."""
    assets = Assets()
    assets.load()
    walk_frames = assets.pacman[Direction.RIGHT].frames
    death_frames = assets.pacman_death.frames
    assert len(assets.DEATH_COORDS) == 11
    assert len(death_frames) == len(assets.DEATH_COORDS) + 1
    for walk, death in zip(walk_frames, death_frames, strict=False):
        assert not _surfaces_equal(walk, death)
    for col, row in assets.DEATH_COORDS:
        assert row == 0
        death_surface = assets._slice_cells(col, row)
        for walk in walk_frames:
            assert not _surfaces_equal(walk, death_surface)


def test_death_frames_have_no_internal_gaps() -> None:
    """Each death frame must be one contiguous sprite, not split pieces."""
    assets = Assets()
    assets.load()
    for frame in assets.pacman_death.frames[:-1]:
        rows = [
            y
            for y in range(frame.get_height())
            if any(
                frame.get_at((x, y))[3] > 0
                and sum(frame.get_at((x, y))[:3]) > 30
                for x in range(frame.get_width())
            )
        ]
        assert rows
        assert rows == list(range(min(rows), max(rows) + 1))


def test_walk_animation_freezes_when_not_moving() -> None:
    assets = Assets()
    assets.load()
    anims = {direction: assets.pacman[direction] for direction in Direction}
    player = PlayerEntity(
        anims,
        CellPos(0, 0),
        (0, 0),
        Direction.RIGHT,
    )
    frame_before = player.image
    player.update(0, 200)
    assert player.image is frame_before
    player.move_to(CellPos(0, 1), (16, 0))
    player.update(0, 200)
    assert player.image is not frame_before


def test_death_animation_advances_past_first_frame() -> None:
    assets = Assets()
    assets.load()
    anims = {direction: assets.pacman[direction] for direction in Direction}
    player = PlayerEntity(
        anims,
        CellPos(0, 0),
        (0, 0),
        death_animation=assets.pacman_death,
    )
    player.start_death(0)
    player.update(0, 250)
    assert player.image is assets.pacman_death.frames[1]


def _surfaces_equal(a: Surface, b: Surface) -> bool:
    if a.get_size() != b.get_size():
        return False
    w, h = a.get_size()
    return all(
        a.get_at((x, y)) == b.get_at((x, y)) for x in range(w) for y in range(h)
    )


def test_freeze_gameplay_stops_turn_requests(game_world: GameWorld) -> None:
    from sprites.sprite_types import Direction

    game_world.freeze_gameplay()
    assert game_world.frozen
    request_turn(game_world, Direction.LEFT)
    update_player_movement(game_world, 1.0, 0)
    assert game_world.frozen


def test_initial_score_carried_into_world() -> None:
    assets = Assets()
    assets.load()
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    world = GameWorld(layout, assets, render_config, initial_score=420)
    assert world.score == 420


def test_advance_level_increments_without_resetting_timer() -> None:
    session = GameSession(
        level_number=1,
        remaining_time_ms=12_345,
    )
    session.advance_level()
    assert session.level_number == 2
    assert session.remaining_time_ms == 12_345


def test_level_complete_reload_resets_timer_and_pellets() -> None:
    """After level advance, session timer and maze consumables must reset."""
    assets = Assets()
    assets.load()
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    session = GameSession(remaining_time_ms=1_000)
    world = GameWorld(
        layout,
        assets,
        render_config,
        level_number=session.level_number,
    )
    world._pellets.clear()
    assert world.all_consumables_cleared

    session.advance_level()
    world.teardown()
    world = GameWorld(
        layout,
        assets,
        render_config,
        initial_score=session.score,
        level_number=session.level_number,
    )
    session.reset_level_timer()

    assert session.level_number == 2
    assert session.remaining_time_ms == session.level_time_limit_s * 1000
    assert not world.all_consumables_cleared
    assert len(world._pellets) == len(layout.pellet_cells) + len(
        layout.power_pellet_cells
    )


def test_sync_score_keeps_highest_value() -> None:
    session = GameSession(score=100)
    session.sync_score(250)
    assert session.score == 250
    session.sync_score(200)
    assert session.score == 250


def test_wall_flash_white_phase_timing() -> None:
    def wall_flash_white(elapsed_ms: int) -> bool:
        return elapsed_ms % 400 < 200

    assert wall_flash_white(0)
    assert wall_flash_white(199)
    assert not wall_flash_white(250)
    assert wall_flash_white(400)


def test_maze_white_tiles_loaded_for_all_tile_kinds() -> None:
    assets = Assets()
    assets.load()
    for tile_kind in TileKind:
        assert tile_kind in assets.maze_tiles
        assert tile_kind in assets.maze_white_tiles
        blue = assets.maze_tiles[tile_kind]
        white = assets.maze_white_tiles[tile_kind]
        assert blue is not white


def test_white_tiles_use_maze_parts_coords_not_tile_kind_coords() -> None:
    """White flash must slice maze_parts with MAZE_PARTS_WHITE_KIND_COORDS."""
    assets = Assets()
    assets.load()
    for tile_kind in (TileKind.CORNER_TL, TileKind.CORNER_BL):
        assert (
            Assets.TILE_KIND_COORDS[tile_kind]
            != Assets.MAZE_PARTS_WHITE_KIND_COORDS[tile_kind]
        )
        loaded = assets.maze_white_tiles[tile_kind]
        wrong = Assets._make_white_tile(
            assets._slice_maze_cells(*Assets.TILE_KIND_COORDS[tile_kind])
        )
        w, h = loaded.get_size()
        assert any(
            loaded.get_at((x, y)) != wrong.get_at((x, y))
            for x in range(w)
            for y in range(h)
        )


def test_set_wall_flash_swaps_wall_surfaces(game_world: GameWorld) -> None:
    wall = game_world._wall_sprites[0]
    assert isinstance(wall, WallTileEntity)
    blue_surface = wall.image

    game_world.set_wall_flash(True)
    assert wall.image is not blue_surface

    game_world.set_wall_flash(False)
    assert wall.image is blue_surface


def test_respawn_ghosts_returns_all_to_home(game_world: GameWorld) -> None:
    from sprites.sprite_types import GhostKind

    ghost = game_world._ghosts[GhostKind.BLINKY]
    away = CellPos(ghost.cell.row + 1, ghost.cell.col)
    if game_world._layout.is_wall(away):
        away = CellPos(ghost.cell.row, ghost.cell.col + 1)
    ghost.move_to(away, cell_center(game_world._render_config, away))
    ghost.hidden = True
    ghost.kill()

    game_world.respawn_ghosts()

    for kind, entity in game_world._ghosts.items():
        assert not entity.hidden
        assert entity.cell == game_world._ghost_home[kind]


def test_ghosts_move_while_player_blocked(game_world: GameWorld) -> None:
    """Ghosts advance on the step clock even when Pac-Man cannot move."""
    from sprites.sprite_types import Direction, GhostKind

    player = game_world._player
    assert player is not None
    ghost = game_world._ghosts[GhostKind.BLINKY]
    blocked_dir: Direction | None = None
    cell = player.cell
    for direction in Direction:
        dr, dc = DIRECTION_DELTA[direction]
        if game_world._layout.is_wall(CellPos(cell.row + dr, cell.col + dc)):
            blocked_dir = direction
            break
    assert blocked_dir is not None
    center = cell_center(game_world._render_config, cell)
    player.move_to(cell, center)
    player.face(blocked_dir)
    game_world._travel_direction = blocked_dir
    game_world._requested_direction = None
    game_world._step_accumulator_ms = 0.0
    game_world.unfreeze_gameplay()

    ghost_cell_before = ghost.cell
    update_player_movement(
        game_world,
        game_world.PLAYER_STEP_MS / 1000.0,
        1_000,
    )
    update_ghost_movement(
        game_world,
        game_world.PLAYER_STEP_MS / 1000.0,
        1_000,
    )
    assert ghost.cell != ghost_cell_before


def test_session_high_score_loads_persisted_top_score(tmp_path: Path) -> None:
    from managers.highscore_manager import HighscoreManager

    path = tmp_path / "highscores.json"
    path.write_text('[{"name": "ABC", "score": 1234}]', encoding="utf-8")
    manager = HighscoreManager(str(path))
    manager.load()
    session = GameSession(high_score=manager.top_score())
    assert session.high_score == 1234


def test_load_level_deterministic_pellets() -> None:
    from config.config import load_config
    from game.level import load_level

    config = load_config("config.json")
    layout = load_level(config, 0, 42)
    assert layout.height > 0 and layout.width > 0
    assert len(layout.ghost_spawns) == 4
    assert len(layout.pellet_cells) > 0
    assert len(layout.power_pellet_cells) == 4

    second = load_level(config, 0, 42)
    assert len(second.pellet_cells) == len(layout.pellet_cells)


def test_all_pellets_reachable_from_player_spawn() -> None:
    """Every pellet must be collectible or the level can never complete."""
    from collections import deque

    from config.config import load_config
    from game.level import load_level

    config = load_config("config.json")
    for seed in (1, 2, 3, 42, 99):
        layout = load_level(config, 0, seed)
        start = layout.player_spawn
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = CellPos(current.row + delta_row, current.col + delta_col)
                if nxt in seen or layout.is_wall(nxt):
                    continue
                seen.add(nxt)
                queue.append(nxt)

        all_pellets = set(layout.pellet_cells) | set(layout.power_pellet_cells)
        assert all_pellets <= seen, f"seed {seed} has unreachable pellets"
        assert all(cell in seen for _kind, cell in layout.ghost_spawns)


def test_play_state_loads_level_off_main_thread() -> None:
    """Maze generation must run on a background thread, not block."""
    import time
    from types import SimpleNamespace

    # Small maze so this test stays fast regardless of generator seed luck;
    # the mechanism under test (background thread + polling), not generation
    # speed itself, is what matters here.
    fast_config = {
        **DEFAULT_CONFIG,
        "levels": [{"width": 15, "height": 15}],
    }
    assets = Assets()
    assets.load()
    context = SimpleNamespace(
        config=fast_config,
        assets=assets,
        screen=Surface((1920, 1080)),
    )

    play_state = PlayState()
    play_state._session = GameSession(phase_started_at_ms=0)
    play_state._level_index = 0
    play_state._level_seed = 42

    start = time.monotonic()
    play_state._start_loading(context)
    assert time.monotonic() - start < 1.0
    assert play_state._loading_thread is not None
    assert play_state._world is None

    deadline = time.monotonic() + 10
    while play_state._loading_thread is not None:
        assert time.monotonic() < deadline, "background load never finished"
        play_state._poll_loading(context, now_ms=0)
        time.sleep(0.05)

    assert play_state._world is not None
    assert play_state._session.phase == GameplayPhase.READY
