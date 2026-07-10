from __future__ import annotations

from game.game_world import GameWorld
from game.render_config import WorldRenderConfig
from states.play_state import _cheat_labels


def test_apply_render_config_recenters_world(game_world: GameWorld) -> None:
    world = game_world
    player = world._player
    assert player is not None
    original_center = player.center

    render_config = WorldRenderConfig.centered(world.layout, (1280, 720))
    world.apply_render_config(render_config)

    assert player.center != original_center
    assert player.center == render_config.cell_center(player.cell)
    assert world._render_config == render_config


def test_cheat_labels_empty_when_inactive() -> None:
    assert (
        _cheat_labels(invincible=False, frozen=False, speed_active=False) == []
    )


def test_cheat_labels_single_flags() -> None:
    assert _cheat_labels(invincible=True, frozen=False, speed_active=False) == [
        "INVINCIBLE"
    ]
    assert _cheat_labels(invincible=False, frozen=True, speed_active=False) == [
        "FREEZE"
    ]
    assert _cheat_labels(invincible=False, frozen=False, speed_active=True) == [
        "SPEED"
    ]


def test_cheat_labels_all_active() -> None:
    assert _cheat_labels(invincible=True, frozen=True, speed_active=True) == [
        "INVINCIBLE",
        "FREEZE",
        "SPEED",
    ]


def test_adjust_player_speed_clamps_and_speed_cheat_flag(
    game_world: GameWorld,
) -> None:
    world = game_world
    assert not world.speed_cheat_active

    world.adjust_player_speed(-20)
    assert world.player_step_ms == 160
    assert world.speed_cheat_active

    world.adjust_player_speed(20)
    assert world.player_step_ms == GameWorld.PLAYER_STEP_MS
    assert not world.speed_cheat_active

    world.adjust_player_speed(-1000)
    assert world.player_step_ms == GameWorld.PLAYER_STEP_MS_MIN
    world.adjust_player_speed(1000)
    assert world.player_step_ms == GameWorld.PLAYER_STEP_MS_MAX


def test_speed_cheat_does_not_accelerate_ghosts(game_world: GameWorld) -> None:
    from game.ghost_logic import update_ghost_movement
    from game.world_player import update_player_movement

    world = game_world
    world.unfreeze_gameplay()
    world.adjust_player_speed(-120)
    assert world.player_step_ms == 60

    steps_before = world._ghost_step_count
    update_player_movement(world, 0.180, 1_000)
    update_ghost_movement(world, 0.180, 1_000)
    assert world._ghost_step_count == steps_before + 1
