from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pygame
from pygame.surface import Surface

from sprites.sprites import AnimatedSprite, AssetSprite
from sprites.types import (
    Direction,
    FruitKind,
    GhostKind,
    TileKind,
)

ASSETS_ROOT = Path(__file__).resolve().parents[2] / "assets"

CELL_SIZE = 8
SPRITE_CELLS = 2
DISPLAY_TILE_SIZE = 16

# 8x8 cell coordinates on general_sprites.png (top-left of each 16x16 sprite)
PACMAN_COORDS: dict[Direction, list[tuple[int, int]]] = {
    Direction.RIGHT: [(57, 0), (59, 0), (61, 0)],
    Direction.LEFT: [(57, 2), (59, 2), (61, 2)],
    Direction.UP: [(57, 4), (59, 4), (61, 4)],
    Direction.DOWN: [(57, 6), (59, 6), (61, 6)],
}

GHOST_COORDS: dict[GhostKind, list[tuple[int, int]]] = {
    GhostKind.BLINKY: [(57, 8), (59, 8)],
    GhostKind.PINKY: [(57, 10), (59, 10)],
    GhostKind.INKY: [(57, 12), (59, 12)],
    GhostKind.CLYDE: [(57, 14), (59, 14)],
}

FRIGHTENED_COORDS: list[tuple[int, int]] = [(73, 8), (75, 8)]

FRUIT_COORDS: dict[FruitKind, tuple[int, int]] = {
    FruitKind.CHERRY: (63, 6),
    FruitKind.STRAWBERRY: (65, 6),
    FruitKind.ORANGE: (67, 6),
    FruitKind.APPLE: (69, 6),
    FruitKind.MELON: (71, 6),
    FruitKind.GALAXIAN: (73, 6),
    FruitKind.BELL: (75, 6),
    FruitKind.KEY: (77, 6),
}

DOT_COORD: tuple[int, int] = (13, 12)
POWER_PELLET_COORD: tuple[int, int] = (11, 10)

TILE_KIND_COORDS: dict[TileKind, tuple[int, int]] = {
    TileKind.WALL: (26, 0),
    TileKind.HORIZONTAL: (24, 0),
    TileKind.VERTICAL: (27, 1),
    TileKind.CORNER_TL: (22, 0),
    TileKind.CORNER_TR: (24, 0),
    TileKind.CORNER_BL: (22, 2),
    TileKind.CORNER_BR: (24, 2),
}


class AssetError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Asset loading error: {detail}")


@dataclass(slots=True)
class ItemSprites:
    dot: AssetSprite = field(
        default_factory=lambda: AssetSprite(pygame.Surface((1, 1))),
    )
    power_pellet: AssetSprite = field(
        default_factory=lambda: AssetSprite(pygame.Surface((1, 1))),
    )


@dataclass(slots=True)
class MazeSprites:
    tiles: dict[TileKind, AssetSprite] = field(default_factory=dict)


@dataclass(slots=True)
class GhostSprites:
    by_kind: dict[GhostKind, AnimatedSprite] = field(default_factory=dict)
    frightened: AnimatedSprite = field(
        default_factory=lambda: AnimatedSprite(frames=[]),
    )


class Assets:
    __slots__ = (
        "_fruits_loaded",
        "_general_sheet",
        "_ghosts_loaded",
        "_loaded",
        "fruits",
        "ghosts",
        "items",
        "maze",
        "pacman",
        "root",
    )

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ASSETS_ROOT
        self.pacman: dict[Direction, AnimatedSprite] = {}
        self.ghosts = GhostSprites()
        self.items = ItemSprites()
        self.fruits: dict[FruitKind, AssetSprite] = {}
        self.maze = MazeSprites()
        self._general_sheet: Surface | None = None
        self._loaded = False
        self._ghosts_loaded = False
        self._fruits_loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        sprites_root = self.root / "sprites"

        def load_image(*parts: str) -> Surface:
            path = sprites_root.joinpath(*parts)
            if not path.exists():
                raise AssetError(f"File not found: {path}")
            return pygame.image.load(path).convert_alpha()

        try:
            self._general_sheet = load_image("sheets", "general_sprites.png")
            self._load_gameplay_assets()
            self._load_maze_tiles(load_image)
            self._loaded = True
        except FileNotFoundError as exc:
            raise AssetError(f"File not found: {exc}") from exc

    def load_ghosts(self) -> None:
        """Load ghost animations when ghost entities are implemented."""
        if self._ghosts_loaded:
            return
        if self._general_sheet is None:
            raise AssetError("General sprites sheet not loaded")
        self._load_ghosts()
        self._ghosts_loaded = True

    def load_fruits(self) -> None:
        """Load fruit sprites when bonus fruit entities are implemented."""
        if self._fruits_loaded:
            return
        if self._general_sheet is None:
            raise AssetError("General sprites sheet not loaded")
        self._load_fruits()
        self._fruits_loaded = True

    def _slice_cells(
        self,
        col: int,
        row: int,
        width_cells: int = SPRITE_CELLS,
        height_cells: int = SPRITE_CELLS,
    ) -> Surface:
        if self._general_sheet is None:
            raise AssetError("General sprites sheet not loaded")
        rect = pygame.Rect(
            col * CELL_SIZE,
            row * CELL_SIZE,
            width_cells * CELL_SIZE,
            height_cells * CELL_SIZE,
        )
        surface = self._general_sheet.subsurface(rect).copy()
        if (
            surface.get_width() != DISPLAY_TILE_SIZE
            or surface.get_height() != DISPLAY_TILE_SIZE
        ):
            surface = pygame.transform.scale(
                surface, (DISPLAY_TILE_SIZE, DISPLAY_TILE_SIZE)
            )
        return surface

    def _load_frames(self, coords: list[tuple[int, int]]) -> AnimatedSprite:
        frames = [self._slice_cells(col, row) for col, row in coords]
        return AnimatedSprite(frames=frames)

    def _load_sprite(self, coord: tuple[int, int]) -> AssetSprite:
        col, row = coord
        return AssetSprite(self._slice_cells(col, row))

    def _load_gameplay_assets(self) -> None:
        for direction, coords in PACMAN_COORDS.items():
            self.pacman[direction] = self._load_frames(coords)

        dot_surface = self._slice_cells(
            DOT_COORD[0], DOT_COORD[1], width_cells=1, height_cells=1
        )
        self.items.dot = AssetSprite(dot_surface)
        self.items.power_pellet = AssetSprite(
            self._slice_cells(POWER_PELLET_COORD[0], POWER_PELLET_COORD[1])
        )

    def _load_ghosts(self) -> None:
        for kind, coords in GHOST_COORDS.items():
            self.ghosts.by_kind[kind] = self._load_frames(coords)
        self.ghosts.frightened = self._load_frames(FRIGHTENED_COORDS)

    def _load_fruits(self) -> None:
        for kind, coord in FRUIT_COORDS.items():
            self.fruits[kind] = self._load_sprite(coord)

    def _load_maze_tiles(self, load_image: Callable[..., Surface]) -> None:
        sheet = load_image("maze", "maze_parts.png")
        for tile_kind, coords in TILE_KIND_COORDS.items():
            col, row = coords
            rect = pygame.Rect(
                col * CELL_SIZE,
                row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            tile_surface = sheet.subsurface(rect)
            scaled = pygame.transform.scale(
                tile_surface, (DISPLAY_TILE_SIZE, DISPLAY_TILE_SIZE)
            )
            self.maze.tiles[tile_kind] = AssetSprite(scaled)
