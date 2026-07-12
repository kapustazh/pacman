# [transition UI] sprite sheet loader for pygame assets.

from pathlib import Path
from typing import ClassVar

import pygame
from pygame.surface import Surface

from game.wall_tile_picker import BUILT_TILE_NEIGHBOR_MASKS
from sprites.sprites import AnimatedSprite
from sprites.sprite_types import (
    Direction,
    FruitKind,
    GhostKind,
    TileKind,
)


class AssetError(Exception):
    """Raised when a sprite sheet or slice cannot be loaded."""

    def __init__(self, detail: str) -> None:
        """Build an error message from a short detail string.

        Args:
            detail: What failed during asset loading.
        """
        super().__init__(f"Asset loading error: {detail}")


class Assets:
    """Loads sprite sheets and exposes gameplay surfaces."""

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
        """Create an unloaded asset catalog.

        Args:
            root: Asset directory; defaults to the project ``assets`` folder.
        """
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

    def load(self) -> None:
        """Load sprite sheets once; no-op when already loaded.

        Raises:
            AssetError: When a required image is missing or corrupt.
        """
        if self.wall_fill.get_width() > 1:
            return

        sprites_root = self.root / "sprites"

        def load_image(*parts: str) -> Surface:
            """Load one image under ``sprites/`` relative to the asset root.

            Args:
                *parts: Path segments after ``sprites/``.

            Returns:
                Loaded surface with per-pixel alpha.

            Raises:
                AssetError: When the file does not exist.
            """
            path = sprites_root.joinpath(*parts)
            if not path.exists():
                raise AssetError(f"File not found: {path}")
            return pygame.image.load(path).convert()  # transparent background

        try:
            self._general_sheet = load_image("sheets", "general_sprites.png")
            self._load_gameplay_assets()
            self._load_ghosts()
            self._load_fruits()
            self._load_maze_tiles()
        except pygame.error as exc:
            raise AssetError(str(exc)) from exc

    @staticmethod
    def _slice_sheet(
        sheet: Surface,
        col: int,
        row: int,
        width_cells: int,
        height_cells: int,
    ) -> Surface:
        """Cut one sprite from a sheet and scale it to tile size.

        Args:
            sheet: Loaded sprite sheet to slice from.
            col: Left cell column on the sheet.
            row: Top cell row on the sheet.
            width_cells: Slice width in cells.
            height_cells: Slice height in cells.

        Returns:
            Copied surface scaled to ``DISPLAY_TILE_SIZE``.
        """
        rect = pygame.Rect(
            col * Assets.CELL_SIZE,
            row * Assets.CELL_SIZE,
            width_cells * Assets.CELL_SIZE,
            height_cells * Assets.CELL_SIZE,
        )
        surface = sheet.subsurface(rect).copy()
        if (
            surface.get_width() != Assets.DISPLAY_TILE_SIZE
            or surface.get_height() != Assets.DISPLAY_TILE_SIZE
        ):
            surface = pygame.transform.scale(
                surface, (Assets.DISPLAY_TILE_SIZE, Assets.DISPLAY_TILE_SIZE)
            )
        surface.set_colorkey((0, 0, 0))  # transparent background
        return surface

    def _slice_cells(
        self,
        col: int,
        row: int,
        width_cells: int | None = None,
        height_cells: int | None = None,
    ) -> Surface:
        """Cut one sprite from the general sheet and scale to tile size.

        Args:
            col: Left cell column on the sheet.
            row: Top cell row on the sheet.
            width_cells: Slice width in cells; defaults to ``SPRITE_CELLS``.
            height_cells: Slice height in cells; defaults to ``SPRITE_CELLS``.

        Returns:
            Copied surface scaled to ``DISPLAY_TILE_SIZE``.
        """
        return self._slice_sheet(
            self._general_sheet,
            col,
            row,
            self.SPRITE_CELLS if width_cells is None else width_cells,
            self.SPRITE_CELLS if height_cells is None else height_cells,
        )

    def _load_frames(self, coords: list[tuple[int, int]]) -> AnimatedSprite:
        """Build an animation from general-sheet cell coordinates.

        Args:
            coords: List of ``(col, row)`` frame positions.

        Returns:
            Animated sprite with one surface per coordinate.
        """
        frames = [self._slice_cells(col, row) for col, row in coords]
        return AnimatedSprite(frames=frames)

    def _load_fruits(self) -> None:
        """Slice bonus-fruit sprites from the general sheet."""
        for kind, coord in self.FRUIT_COORDS.items():
            col, row = coord
            self.fruits[kind] = self._slice_cells(col, row)

    def _load_gameplay_assets(self) -> None:
        """Load Pac-Man, death animation, dots, and power pellets."""
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
        """Load normal, frightened, flash, and eyes ghost animations."""
        for kind, coords in self.GHOST_COORDS.items():
            self.ghosts_by_kind[kind] = self._load_frames(coords)
        self.ghost_frightened = self._load_frames(self.FRIGHTENED_COORDS)
        self.ghost_frightened_flash = self._load_frames(
            self.FRIGHTENED_FLASH_COORDS
        )
        self.ghost_eyes = self._load_frames(self.EYES_COORDS)

    def _make_white_tile(self, surface: Surface) -> Surface:
        """Tint non-black pixels white for the level-clear flash.

        Args:
            surface: Source maze tile.

        Returns:
            Copy of the tile with line art recolored to white.
        """
        result = surface.copy()
        for x in range(result.get_width()):
            for y in range(result.get_height()):
                r, g, b, a = result.get_at((x, y))
                if r + g + b > 20:  # not black
                    result.set_at((x, y), (*self.WHITE_COLOR, a))
        return result

    def _load_maze_tiles(self) -> None:
        """Build blue and white maze tile sets, fills, and junctions."""
        maze_path = self.root / "sprites" / "maze" / "maze_parts.png"
        if not maze_path.exists():
            raise AssetError(f"File not found: {maze_path}")
        self._maze_sheet = pygame.image.load(maze_path).convert()
        for tile_kind, coords in self.TILE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                self.maze_tiles[tile_kind] = solid_tile(self.WALL_FILL_COLOR)
                continue
            col, row = coords
            self.maze_tiles[tile_kind] = self._slice_cells(
                col, row, width_cells=1, height_cells=1
            )
        for tile_kind, coords in self.MAZE_PARTS_WHITE_KIND_COORDS.items():
            if tile_kind == TileKind.WALL:
                self.maze_white_tiles[tile_kind] = solid_tile(self.WHITE_COLOR)
                continue
            col, row = coords
            sheet_surface = self._slice_sheet(self._maze_sheet, col, row, 1, 1)
            self.maze_white_tiles[tile_kind] = self._make_white_tile(
                sheet_surface
            )
        for kind, mask in BUILT_TILE_NEIGHBOR_MASKS.items():
            self.maze_tiles[kind] = built_tile(
                kind, mask, self.WALL_LINE_COLOR
            )
            self.maze_white_tiles[kind] = built_tile(
                kind, mask, self.WHITE_COLOR
            )
        fill_px = self.DISPLAY_TILE_SIZE * 2
        self.wall_fill = pygame.Surface((fill_px, fill_px))
        self.wall_fill.fill(self.WALL_FILL_COLOR)
        self.wall_fill_white = pygame.Surface((fill_px, fill_px))
        self.wall_fill_white.fill(self.WHITE_COLOR)

    # Blue/Purple
    WALL_FILL_COLOR: ClassVar[tuple[int, int, int]] = (66, 66, 255)
    # Dark blue
    WALL_LINE_COLOR: ClassVar[tuple[int, int, int]] = (33, 33, 255)

    WHITE_COLOR: ClassVar[tuple[int, int, int]] = (255, 255, 255)


def built_tile(
    kind: TileKind,
    mask: tuple[bool, bool, bool, bool],
    color: tuple[int, int, int],
) -> Surface:
    """Draw pillar dots or T/cross arms not present on the maze sheets."""
    if kind is TileKind.PILLAR:
        return dot_tile(color)
    return junction_tile(mask, color)


def junction_tile(
    mask: tuple[bool, bool, bool, bool],
    color: tuple[int, int, int],
) -> Surface:
    """Compose a junction tile from centered line arms."""
    up, down, left, right = mask
    cell = Assets.CELL_SIZE
    mid = cell // 2
    native = pygame.Surface((cell, cell), pygame.SRCALPHA)
    if up:
        pygame.draw.line(native, color, (mid, 0), (mid, mid))
    if down:
        pygame.draw.line(native, color, (mid, mid), (mid, cell - 1))
    if left:
        pygame.draw.line(native, color, (0, mid), (mid, mid))
    if right:
        pygame.draw.line(native, color, (mid, mid), (cell - 1, mid))
    return pygame.transform.scale(
        native, (Assets.DISPLAY_TILE_SIZE, Assets.DISPLAY_TILE_SIZE)
    )


def solid_tile(color: tuple[int, int, int]) -> Surface:
    """Create a flat-filled wall tile."""
    surface = pygame.Surface(
        (Assets.DISPLAY_TILE_SIZE, Assets.DISPLAY_TILE_SIZE)
    )
    surface.fill(color)
    return surface


def dot_tile(color: tuple[int, int, int], scale: float = 0.5) -> Surface:
    """Create a small centered circle for a lone wall post."""
    size = Assets.DISPLAY_TILE_SIZE
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    radius = max(1, round(size * scale / 2))
    pygame.draw.circle(surface, color, (size // 2, size // 2), radius)
    return surface
