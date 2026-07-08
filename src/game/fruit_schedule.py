# [transition] SCRUM-35 — bonus fruit schedule tables.

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
LEVEL_SPAWN_SECONDS: tuple[tuple[int, ...], ...] = (
    (9, 41),
    (15, 41),
    (15, 41),
    (15, 41),
    (9, 41),
    (9, 41),
    (9, 41),
)  # TODO: add spawn times for fruits
# can conflict with game session timer, need to be adjusted
FRUIT_VISIBLE_DURATION_S: int = 10  # TODO: review fruit visible duration


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


def spawn_seconds_for_level(level_number: int) -> tuple[int, ...]:
    """Return fruit spawn times measured from level start.

    Args:
        level_number: One-based level index.

    Returns:
        Spawn offsets in seconds for that level's fruit schedule.
    """
    if level_number <= len(LEVEL_SPAWN_SECONDS):
        return LEVEL_SPAWN_SECONDS[level_number - 1]
    return LEVEL_SPAWN_SECONDS[-1]
