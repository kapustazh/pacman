from __future__ import annotations

from sprites.sprite_types import FruitKind

LEVEL_FRUIT: tuple[FruitKind, ...] = (
    FruitKind.CHERRY,
    FruitKind.STRAWBERRY,
    FruitKind.ORANGE,
    FruitKind.APPLE,
    FruitKind.MELON,
    FruitKind.GALAXIAN,
    FruitKind.BELL,
)

FRUIT_VISIBLE_DURATION_S: int = 10


def fruit_spawn_seconds(level_max_time_s: int) -> tuple[int, ...]:
    """Return the seconds at which the fruits will spawn from the level start.
    The fruits will spawn at 1/4 and 1/2 of the level

    Args:
        level_max_time_s: The maximum time of the level.

    Returns:
        A tuple of the seconds at which the fruits will spawn.
    """
    slots = (level_max_time_s // 4, level_max_time_s // 2)
    return tuple(
        at
        for at in slots
        if at > 0 and at + FRUIT_VISIBLE_DURATION_S <= level_max_time_s
    )


def fruit_for_level(level_number: int) -> FruitKind:
    """Return the bonus fruit kind for a level.

    Args:
        level_number: One-based level index.

    Returns:
        Configured fruit for early levels, or a key for later ones.
    """
    if level_number <= len(LEVEL_FRUIT):
        return LEVEL_FRUIT[level_number - 1]
    return FruitKind.KEY
