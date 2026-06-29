from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from sprites.sprite_types import GhostKind


# BOILERPLATE: logic grid cell types; final maze generator may expand this.
class CellType(Enum):
    """BOILERPLATE: logic grid cell types, not render sprite kinds."""

    WALL = auto()
    EMPTY = auto()


# BOILERPLATE: immutable cell address used by layout and runtime pickup sets.
@dataclass(frozen=True, slots=True)
class CellPos:
    """Immutable row/column position in level coordinates."""

    row: int
    col: int


# BOILERPLATE: frozen map snapshot; replace loader source, not this.
@dataclass(frozen=True, slots=True)
class LevelLayout:
    """BOILERPLATE: immutable snapshot used to spawn GameWorld."""

    cells: tuple[tuple[CellType, ...], ...]
    pellet_cells: frozenset[CellPos]
    power_pellet_cells: frozenset[CellPos]
    player_spawn: CellPos
    ghost_spawns: tuple[
        tuple[GhostKind, CellPos], ...
    ]  # TODO: add corner spawn points for ghosts
    fruit_spawn: CellPos  # TODO: add random spawn points for fruits

    @property
    def height(self) -> int:
        """Return number of rows."""
        return len(self.cells)

    @property
    def width(self) -> int:
        """Return number of columns."""
        return len(self.cells[0]) if self.cells else 0

    def is_wall(self, pos: CellPos) -> bool:
        """Return True when position is outside grid or blocked by wall."""
        if pos.row < 0 or pos.col < 0:
            return True
        if pos.row >= self.height or pos.col >= self.width:
            return True
        return self.cells[pos.row][pos.col] == CellType.WALL


def load_smoke_level() -> LevelLayout:
    """DEMO: tiny static grid for FSM and sprite-pipeline smoke tests."""
    # DEMO: hand-authored grid only proves FSM/entity pipeline.
    # TODO: replace with load_level_from_config() when maze generation lands.
    grid = (
        "###################",
        "#                 #",
        "# ### ### #####   #",
        "# #   #     #   # #",
        "# # # # ### # # # #",
        "# #   #     #   # #",
        "# ##### ### ##### #",
        "#            .    #",
        "# ### ### ### ### #",
        "# #             # #",
        "#                 #",
        "###################",
    )
    cells: list[tuple[CellType, ...]] = []
    pellets: set[CellPos] = set()
    power_pellets: set[CellPos] = set()
    player_spawn = CellPos(7, 10)
    ghost_spawns = (
        (GhostKind.BLINKY, CellPos(1, 1)),
        (GhostKind.PINKY, CellPos(1, 17)),
        (GhostKind.INKY, CellPos(10, 1)),
        (GhostKind.CLYDE, CellPos(10, 17)),
    )  # TODO: add corner spawn points for ghosts
    fruit_spawn = CellPos(7, 9)

    for row_index, row in enumerate(grid):
        current_row: list[CellType] = []
        for col_index, marker in enumerate(row):
            pos = CellPos(row_index, col_index)
            if marker == "#":
                current_row.append(CellType.WALL)
                continue
            current_row.append(CellType.EMPTY)
            if marker == ".":
                pellets.add(pos)
            elif marker == "o":
                power_pellets.add(pos)

        cells.append(tuple(current_row))

    return LevelLayout(
        cells=tuple[tuple[CellType, ...], ...](cells),
        pellet_cells=frozenset(pellets),
        power_pellet_cells=frozenset(power_pellets),
        player_spawn=player_spawn,
        ghost_spawns=ghost_spawns,
        fruit_spawn=fruit_spawn,
    )
