# [transition UI] sprite sheet loader for pygame assets.

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import pygame
from pygame.surface import Surface

from sprites.sprites import AnimatedSprite, AssetSprite
from sprites.sprite_types import (
    Direction,
    FruitKind,
    GhostKind,
    TileKind,
)


class AssetError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Asset loading error: {detail}")


@dataclass(slots=True)
class GhostSprites:
    by_kind: dict[GhostKind, AnimatedSprite] = field(default_factory=dict)
    frightened: AnimatedSprite = field(
        default_factory=lambda: AnimatedSprite(frames=[]),
    )
    frightened_flash: AnimatedSprite = field(
        default_factory=lambda: AnimatedSprite(frames=[]),
    )


class Assets:
    """Sprite sheet loader and gameplay asset catalog."""

    ASSETS: ClassVar[Path] = Path(__file__).resolve().parents[2] / "assets"
    CELL_SIZE: ClassVar[int] = 8
    SPRITE_CELLS: ClassVar[int] = 2
    DISPLAY_TILE_SIZE: ClassVar[int] = 16

    # 8x8 cell coords on general_sprites.png (top-left of each 16x16 sprite)
    PACMAN_COORDS: ClassVar[dict[Direction, list[tuple[int, int]]]] = {
        Direction.RIGHT: [(57, 0), (59, 0), (61, 0)],
        Direction.LEFT: [(57, 2), (59, 2), (61, 2)],
        Direction.UP: [(57, 4), (59, 4), (61, 4)],
        Direction.DOWN: [(57, 6), (59, 6), (61, 6)],
    }
    DEATH_COORDS: ClassVar[list[tuple[int, int]]] = [
        (63, 0),
        (65, 0),
        (67, 0),
        (69, 0),
        (71, 0),
        (73, 0),
        (75, 0),
        (77, 0),
        (79, 0),
        (81, 0),
        (83, 0),
    ]

    GHOST_COORDS: ClassVar[dict[GhostKind, list[tuple[int, int]]]] = {
        GhostKind.BLINKY: [(57, 8), (59, 8)],
        GhostKind.PINKY: [(57, 10), (59, 10)],
        GhostKind.INKY: [(57, 12), (59, 12)],
        GhostKind.CLYDE: [(57, 14), (59, 14)],
    }

    FRIGHTENED_COORDS: ClassVar[list[tuple[int, int]]] = [(73, 8), (75, 8)]
    FRIGHTENED_FLASH_COORDS: ClassVar[list[tuple[int, int]]] = [(77, 8), (79, 8)]

    FRUIT_COORDS: ClassVar[dict[FruitKind, tuple[int, int]]] = {
        FruitKind.CHERRY: (63, 6),
        FruitKind.STRAWBERRY: (65, 6),
        FruitKind.ORANGE: (67, 6),
        FruitKind.APPLE: (69, 6),
        FruitKind.MELON: (71, 6),
        FruitKind.GALAXIAN: (73, 6),
        FruitKind.BELL: (75, 6),
        FruitKind.KEY: (77, 6),
    }

    DOT_COORD: ClassVar[tuple[int, int]] = (10, 1)
    POWER_PELLET_COORD: ClassVar[tuple[int, int]] = (26, 3)

    # Blue walls from general_sprites isolated catalog (rows 2-4).
    TILE_KIND_COORDS: ClassVar[dict[TileKind, tuple[int, int]]] = {
        TileKind.WALL: (23, 2),
        TileKind.HORIZONTAL: (23, 2),
        TileKind.VERTICAL: (22, 3),
        TileKind.CORNER_TL: (22, 2),
        TileKind.CORNER_TR: (25, 2),
        TileKind.CORNER_BL: (2, 4),
        TileKind.CORNER_BR: (5, 4),
    }

    # White flash: maze_parts.png uses its own cell grid (not general_sprites).
    # TL/BL corners need different cells than TILE_KIND_COORDS — do not reuse.
    MAZE_PARTS_WHITE_KIND_COORDS: ClassVar[dict[TileKind, tuple[int, int]]] = {
        TileKind.WALL: (23, 2),
        TileKind.HORIZONTAL: (23, 2),
        TileKind.VERTICAL: (22, 3),
        TileKind.CORNER_TL: (7, 2),
        TileKind.CORNER_TR: (25, 2),
        TileKind.CORNER_BL: (13, 4),
        TileKind.CORNER_BR: (5, 4),
    }

    __slots__ = (
        "_fruits_loaded",
        "_general_sheet",
        "_maze_sheet",
        "_ghosts_loaded",
        "_loaded",
        "dot_surface",
        "fruits",
        "ghosts",
        "maze_tiles",
        "maze_white_tiles",
        "pacman",
        "pacman_death",
        "power_pellet_surface",
        "root",
    )

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or self.ASSETS
        self.pacman: dict[Direction, AnimatedSprite] = {}
        self.pacman_death = AnimatedSprite(frames=[])
        self.ghosts = GhostSprites()
        self.dot_surface: Surface = Surface((1, 1))
        self.power_pellet_surface: Surface = Surface((1, 1))
        self.maze_tiles: dict[TileKind, Surface] = {}
        self.maze_white_tiles: dict[TileKind, Surface] = {}
        self.fruits: dict[FruitKind, AssetSprite] = {}
        self._general_sheet: Surface | None = None
        self._maze_sheet: Surface | None = None
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
            self._load_ghosts()
            self._load_fruits()
            self._load_maze_tiles()
            self._ghosts_loaded = True
            self._fruits_loaded = True
            self._loaded = True
        except pygame.error as exc:
            raise AssetError(str(exc)) from exc

    def _slice_cells(
        self,
        col: int,
        row: int,
        width_cells: int | None = None,
        height_cells: int | None = None,
    ) -> Surface:
        if width_cells is None:
            width_cells = self.SPRITE_CELLS
        if height_cells is None:
            height_cells = self.SPRITE_CELLS
        if self._general_sheet is None:
            raise AssetError("General sprites sheet not loaded")
        rect = pygame.Rect(
            col * self.CELL_SIZE,
            row * self.CELL_SIZE,
            width_cells * self.CELL_SIZE,
            height_cells * self.CELL_SIZE,
        )
        surface = self._general_sheet.subsurface(rect).copy()
        if (
            surface.get_width() != self.DISPLAY_TILE_SIZE
            or surface.get_height() != self.DISPLAY_TILE_SIZE
        ):
            surface = pygame.transform.scale(
                surface, (self.DISPLAY_TILE_SIZE, self.DISPLAY_TILE_SIZE)
            )
        return surface

    def _load_frames(self, coords: list[tuple[int, int]]) -> AnimatedSprite:
        frames = [self._slice_cells(col, row) for col, row in coords]
        return AnimatedSprite(frames=frames)

    def _load_sprite(self, coord: tuple[int, int]) -> AssetSprite:
        col, row = coord
        return AssetSprite(self._slice_cells(col, row))

    def _load_gameplay_assets(self) -> None:
        for direction, coords in self.PACMAN_COORDS.items():
            self.pacman[direction] = self._load_frames(coords)
        self.pacman_death = self._load_frames(self.DEATH_COORDS)
        empty_death = pygame.Surface(
            (self.DISPLAY_TILE_SIZE, self.DISPLAY_TILE_SIZE),
            pygame.SRCALPHA,
        )
        self.pacman_death.frames.append(empty_death)

        dot_surface = self._slice_cells(
            self.DOT_COORD[0],
            self.DOT_COORD[1],
            width_cells=1,
            height_cells=1,
        )
        self.dot_surface = dot_surface
        self.power_pellet_surface = self._slice_cells(
            self.POWER_PELLET_COORD[0],
            self.POWER_PELLET_COORD[1],
            width_cells=1,
            height_cells=1,
        )

    def _load_ghosts(self) -> None:
        for kind, coords in self.GHOST_COORDS.items():
            self.ghosts.by_kind[kind] = self._load_frames(coords)
        self.ghosts.frightened = self._load_frames(self.FRIGHTENED_COORDS)
        self.ghosts.frightened_flash = self._load_frames(
            self.FRIGHTENED_FLASH_COORDS
        )

    def _load_fruits(self) -> None:
        for kind, coord in self.FRUIT_COORDS.items():
            self.fruits[kind] = self._load_sprite(coord)

    def _slice_maze_cells(
        self,
        col: int,
        row: int,
        width_cells: int = 1,
        height_cells: int = 1,
    ) -> Surface:
        if self._maze_sheet is None:
            raise AssetError("Maze parts sheet not loaded")
        rect = pygame.Rect(
            col * self.CELL_SIZE,
            row * self.CELL_SIZE,
            width_cells * self.CELL_SIZE,
            height_cells * self.CELL_SIZE,
        )
        surface = self._maze_sheet.subsurface(rect).copy()
        if (
            surface.get_width() != self.DISPLAY_TILE_SIZE
            or surface.get_height() != self.DISPLAY_TILE_SIZE
        ):
            surface = pygame.transform.scale(
                surface, (self.DISPLAY_TILE_SIZE, self.DISPLAY_TILE_SIZE)
            )
        return surface

    @staticmethod
    def _make_white_tile(surface: Surface) -> Surface:
        """Tint every non-black pixel to pure white for level-clear flash."""
        result = surface.copy()
        for x in range(result.get_width()):
            for y in range(result.get_height()):
                r, g, b, a = result.get_at((x, y))
                if r + g + b > 20:
                    result.set_at((x, y), (255, 255, 255, a))
        return result

    def _load_maze_tiles(self) -> None:
        if self._general_sheet is None:
            raise AssetError("General sprites sheet not loaded")
        maze_path = self.root / "sprites" / "maze" / "maze_parts.png"
        if not maze_path.exists():
            raise AssetError(f"File not found: {maze_path}")
        self._maze_sheet = pygame.image.load(maze_path).convert_alpha()
        vertical_col, vertical_row = self.TILE_KIND_COORDS[TileKind.VERTICAL]
        wall_color = self._dominant_color(
            self._slice_cells(
                vertical_col, vertical_row, width_cells=1, height_cells=1
            )
        )
        for tile_kind, coords in self.TILE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                # No line-art shape exists for a fully-enclosed wall cell in
                # the original sheet (source mazes are always 1 cell thick);
                # synthesize a flat fill instead of reusing HORIZONTAL's
                # hollow outline.
                self.maze_tiles[tile_kind] = self._solid_tile(wall_color)
                continue
            col, row = coords
            blue_surface = self._slice_cells(
                col, row, width_cells=1, height_cells=1
            )
            self.maze_tiles[tile_kind] = blue_surface
        for tile_kind, coords in self.MAZE_PARTS_WHITE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                self.maze_white_tiles[tile_kind] = self._solid_tile(
                    (255, 255, 255)
                )
                continue
            col, row = coords
            sheet_surface = self._slice_maze_cells(col, row)
            self.maze_white_tiles[tile_kind] = self._make_white_tile(
                sheet_surface
            )
        self.maze_tiles[TileKind.PILLAR] = self._solid_tile(
            wall_color, scale=0.5
        )
        self.maze_white_tiles[TileKind.PILLAR] = self._solid_tile(
            (255, 255, 255), scale=0.5
        )

    @staticmethod
    def _solid_tile(color: tuple[int, int, int], scale: float = 1.0) -> Surface:
        """Flat-filled tile for wall cells with no matching line-art shape.

        scale < 1 draws a centered, smaller square (e.g. a lone junction
        post) on a transparent tile instead of a full-tile block.
        """
        size = Assets.DISPLAY_TILE_SIZE
        if scale >= 1.0:
            surface = pygame.Surface((size, size))
            surface.fill(color)
            return surface
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        square_size = max(1, round(size * scale))
        offset = (size - square_size) // 2
        pygame.draw.rect(
            surface, color, (offset, offset, square_size, square_size)
        )
        return surface

    @staticmethod
    def _dominant_color(surface: Surface) -> tuple[int, int, int]:
        """Most common non-black opaque pixel color, to match the wall hue."""
        counts: dict[tuple[int, int, int], int] = {}
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                if a == 0 or r + g + b < 20:
                    continue
                counts[(r, g, b)] = counts.get((r, g, b), 0) + 1
        return max(counts, key=counts.get) if counts else (0, 0, 0)
