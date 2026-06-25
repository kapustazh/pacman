from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


# TODO: populate when ghost entities are implemented.
class GhostKind(Enum):
    BLINKY = "blinky"
    PINKY = "pinky"
    INKY = "inky"
    CLYDE = "clyde"


# TODO: populate when bonus fruit entities are implemented.
class FruitKind(Enum):
    CHERRY = "cherry"
    STRAWBERRY = "strawberry"
    ORANGE = "orange"
    APPLE = "apple"
    MELON = "melon"
    GALAXIAN = "galaxian"
    BELL = "bell"
    KEY = "key"


class TileKind(Enum):
    """Semantic maze wall tile mapped to spritesheet coordinates."""

    WALL = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()
    CORNER_TL = auto()
    CORNER_TR = auto()
    CORNER_BL = auto()
    CORNER_BR = auto()


# TODO: populated after Assets.load_fruits() when bonus fruit entities land.
FRUIT_POINTS: dict[FruitKind, int] = {
    FruitKind.CHERRY: 100,
    FruitKind.STRAWBERRY: 300,
    FruitKind.ORANGE: 500,
    FruitKind.APPLE: 700,
    FruitKind.MELON: 1000,
    FruitKind.GALAXIAN: 2000,
    FruitKind.BELL: 3000,
    FruitKind.KEY: 5000,
}
