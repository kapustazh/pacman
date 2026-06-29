from __future__ import annotations

from sprites.sprite_types import FruitKind

# TODO: add fruit schedule for each level
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
FRUIT_VISIBLE_DURATION_S: int = 10  # TODO: review fruit visible duration


def fruit_for_level(level_number: int) -> FruitKind:
    """Return bonus fruit kind for a 1-based level index."""
    if level_number <= len(LEVEL_FRUIT):
        return LEVEL_FRUIT[level_number - 1]
    return FruitKind.KEY


def spawn_seconds_for_level(level_number: int) -> tuple[int, ...]:
    """Return spawn times in level-play seconds for a 1-based level index."""
    if level_number <= len(LEVEL_SPAWN_SECONDS):
        return LEVEL_SPAWN_SECONDS[level_number - 1]
    return LEVEL_SPAWN_SECONDS[-1]
