# [transition UI] sprite sheet loader for pygame assets.

from pathlib import Path
from typing import ClassVar

import pygame
from pygame.surface import Surface

from sprites.sprites import AnimatedSprite
from sprites.sprite_types import (
    Direction,
    FruitKind,
    GhostKind,
    TileKind,
)


class AssetError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Asset loading error: {detail}")


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
    FRIGHTENED_FLASH_COORDS: ClassVar[list[tuple[int, int]]] = [
        (77, 8),
        (79, 8),
    ]
    EYES_COORDS: ClassVar[list[tuple[int, int]]] = [(75, 10)]

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

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or self.ASSETS
        self.pacman: dict[Direction, AnimatedSprite] = {}
        self.pacman_death = AnimatedSprite(frames=[])
        self.ghosts_by_kind: dict[GhostKind, AnimatedSprite] = {}
        self.ghost_frightened = AnimatedSprite(frames=[])
        self.ghost_frightened_flash = AnimatedSprite(frames=[])
        self.ghost_eyes = AnimatedSprite(frames=[])
        self.dot_surface: Surface = Surface((1, 1))
        self.power_pellet_surface: Surface = Surface((1, 1))
        self.maze_tiles: dict[TileKind, Surface] = {}
        self.maze_white_tiles: dict[TileKind, Surface] = {}
        self.wall_fill: Surface = Surface((1, 1))
        self.wall_fill_white: Surface = Surface((1, 1))
        self.fruits: dict[FruitKind, Surface] = {}
        self._general_sheet: Surface | None = None
        self._maze_sheet: Surface | None = None
        self._loaded = False

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

    def _load_fruits(self) -> None:
        for kind, coord in self.FRUIT_COORDS.items():
            col, row = coord
            self.fruits[kind] = self._slice_cells(col, row)

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
            self.ghosts_by_kind[kind] = self._load_frames(coords)
        self.ghost_frightened = self._load_frames(self.FRIGHTENED_COORDS)
        self.ghost_frightened_flash = self._load_frames(
            self.FRIGHTENED_FLASH_COORDS
        )
        self.ghost_eyes = self._load_frames(self.EYES_COORDS)

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
        for tile_kind, coords in self.TILE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                # No line-art shape exists for a fully-enclosed wall cell in
                # the original sheet (source mazes are always 1 cell thick);
                # fill it light blue — the text sheet's 4th color band
                # (ArcadeTextColor.CYAN), so wall mass reads as solid but
                # distinct from the line walls.
                self.maze_tiles[tile_kind] = self._solid_tile(
                    self.WALL_FILL_COLOR
                )
                continue
            col, row = coords
            blue_surface = self._slice_cells(
                col, row, width_cells=1, height_cells=1
            )
            # black background transparent, so line art layered over the
            # interior fill doesn't punch black squares into it
            # (convert() drops per-pixel alpha, otherwise the colorkey
            # would be ignored)
            blue_surface = blue_surface.convert()
            blue_surface.set_colorkey((0, 0, 0))
            self.maze_tiles[tile_kind] = blue_surface
        for tile_kind, coords in self.MAZE_PARTS_WHITE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                self.maze_white_tiles[tile_kind] = self._solid_tile(
                    (255, 255, 255)
                )
                continue
            col, row = coords
            sheet_surface = self._slice_maze_cells(col, row)
            white_surface = self._make_white_tile(sheet_surface).convert()
            white_surface.set_colorkey((0, 0, 0))
            self.maze_white_tiles[tile_kind] = white_surface
        self.maze_tiles[TileKind.PILLAR] = self._dot_tile(self.WALL_LINE_COLOR)
        self.maze_white_tiles[TileKind.PILLAR] = self._dot_tile((255, 255, 255))
        # T-junctions and the 4-way cross have no matching cell in the
        # sheet's double-line maze, so build them from the same row-4/col-4
        # line pixels the HORIZONTAL and VERTICAL slices use — one arm per
        # wall neighbour. This tiles seamlessly with the sliced straights
        # and corners and removes the old solid-block fallback.
        for tile_kind, mask in self.JUNCTION_MASKS.items():
            self.maze_tiles[tile_kind] = self._junction_tile(
                mask, self.WALL_LINE_COLOR
            )
            self.maze_white_tiles[tile_kind] = self._junction_tile(
                mask, (255, 255, 255)
            )
        # Interior-hole fill spans 2x2 tiles: it reaches the centre lines
        # of the surrounding wall tiles, merging adjacent holes into one
        # solid mass bounded exactly by the blue wall lines.
        fill_px = self.DISPLAY_TILE_SIZE * 2
        self.wall_fill = pygame.Surface((fill_px, fill_px))
        self.wall_fill.fill(self.WALL_FILL_COLOR)
        self.wall_fill_white = pygame.Surface((fill_px, fill_px))
        self.wall_fill_white.fill((255, 255, 255))

    # Light blue sampled from the text sheet's 4th color band (CYAN).
    WALL_FILL_COLOR: ClassVar[tuple[int, int, int]] = (0, 255, 255)
    # Dark blue from general_sprites wall line art (VERTICAL/HORIZONTAL cells).
    WALL_LINE_COLOR: ClassVar[tuple[int, int, int]] = (33, 33, 255)

    # (up, down, left, right) arms present, matching wall_tile_picker.
    JUNCTION_MASKS: ClassVar[dict[TileKind, tuple[bool, bool, bool, bool]]] = {
        TileKind.T_UP: (True, False, True, True),
        TileKind.T_DOWN: (False, True, True, True),
        TileKind.T_LEFT: (True, True, True, False),
        TileKind.T_RIGHT: (True, True, False, True),
        TileKind.CROSS: (True, True, True, True),
    }

    @staticmethod
    def _junction_tile(
        mask: tuple[bool, bool, bool, bool],
        color: tuple[int, int, int],
    ) -> Surface:
        """Compose a junction tile from centered arms (row 4 / col 4)."""
        up, down, left, right = mask
        cell = 8  # native sheet cell size before display scaling
        mid = cell // 2
        native = pygame.Surface((cell, cell), pygame.SRCALPHA)
        for i in range(cell):  # column
            for j in range(cell):  # row
                on = (
                    (up and i == mid and j <= mid)
                    or (down and i == mid and j >= mid)
                    or (left and j == mid and i <= mid)
                    or (right and j == mid and i >= mid)
                )
                if on:
                    native.set_at((i, j), (*color, 255))
        return pygame.transform.scale(
            native, (Assets.DISPLAY_TILE_SIZE, Assets.DISPLAY_TILE_SIZE)
        )

    @staticmethod
    def _solid_tile(color: tuple[int, int, int]) -> Surface:
        """Flat-filled tile for wall cells with no matching line-art shape."""
        surface = pygame.Surface(
            (Assets.DISPLAY_TILE_SIZE, Assets.DISPLAY_TILE_SIZE)
        )
        surface.fill(color)
        return surface

    @staticmethod
    def _dot_tile(color: tuple[int, int, int], scale: float = 0.5) -> Surface:
        """Small centered circle for a lone wall post with no neighbours."""
        size = Assets.DISPLAY_TILE_SIZE
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = max(1, round(size * scale / 2))
        pygame.draw.circle(surface, color, (size // 2, size // 2), radius)
        return surface
