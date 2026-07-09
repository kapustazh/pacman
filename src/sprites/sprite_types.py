from enum import Enum, IntEnum, auto


class RenderLayer(IntEnum):
    """Sprite draw order in ``LayeredUpdates``; higher draws on top."""

    BACKGROUND = 0
    CONSUMABLE = 1
    ACTOR = 2


class Direction(Enum):
    """Cardinal movement directions."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class GhostKind(Enum):
    """The four classic ghost characters."""

    BLINKY = "blinky"
    PINKY = "pinky"
    INKY = "inky"
    CLYDE = "clyde"


class GhostMode(Enum):
    """A ghost's current vulnerability/movement/animation state."""

    NORMAL = auto()
    FRIGHTENED = auto()
    FLASHING = auto()
    EYES = auto()
    HIDDEN = auto()


class FruitKind(Enum):
    """Bonus fruit types and their display order by level."""

    CHERRY = "cherry"
    STRAWBERRY = "strawberry"
    ORANGE = "orange"
    APPLE = "apple"
    MELON = "melon"
    GALAXIAN = "galaxian"
    BELL = "bell"
    KEY = "key"


class TileKind(Enum):
    """Wall tile shapes used for maze autotiling."""

    WALL = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()
    CORNER_TL = auto()
    CORNER_TR = auto()
    CORNER_BL = auto()
    CORNER_BR = auto()
    PILLAR = auto()
    T_UP = auto()
    T_DOWN = auto()
    T_LEFT = auto()
    T_RIGHT = auto()
    CROSS = auto()


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
