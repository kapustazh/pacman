# [transition] SCRUM-35 — grid-to-pixel layout (new for pygame UI).

from __future__ import annotations

from dataclasses import dataclass

from game.level import CellPos, LevelLayout
from sprites.sprite_types import Direction


@dataclass(frozen=True, slots=True)
class MazeBounds:
    """Screen-space rectangle for the centered maze playfield."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return the pixel center of the maze playfield.

        Returns:
            (x, y) center point in screen coordinates.
        """
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bottom(self) -> int:
        """Return the bottom edge of the maze playfield.

        Returns:
            Y coordinate of the lower boundary.
        """
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class WorldRenderConfig:
    """Pixel scale and screen offset for converting grid cells to pixels."""

    tile_px: int = 16
    origin_x: int = 0
    origin_y: int = 0

    def maze_bounds(self, layout: LevelLayout) -> MazeBounds:
        """Compute screen bounds for a layout at this render config.

        Args:
            layout: Level grid whose width and height define the maze size.

        Returns:
            Pixel rectangle covering the full maze playfield.
        """
        return MazeBounds(
            x=self.origin_x,
            y=self.origin_y,
            width=layout.width * self.tile_px,
            height=layout.height * self.tile_px,
        )

    @classmethod
    def centered(
        cls,
        layout: LevelLayout,
        screen_size: tuple[int, int],
        tile_px: int = 16,
    ) -> WorldRenderConfig:
        """Build a render config that centers the maze on screen.

        Args:
            layout: Level grid whose size determines maze dimensions.
            screen_size: Screen width and height in pixels.
            tile_px: Pixel size of one grid cell.

        Returns:
            Config with origin offsets that center the maze.
        """
        width_px = layout.width * tile_px
        height_px = layout.height * tile_px
        screen_w, screen_h = screen_size
        return cls(
            tile_px=tile_px,
            origin_x=(screen_w - width_px) // 2,
            origin_y=(screen_h - height_px) // 2,
        )

    def cell_center(self, cell: CellPos) -> tuple[int, int]:
        """Convert a grid cell to its pixel center on screen.

        Args:
            cell: Grid position to convert.

        Returns:
            (x, y) pixel center of the cell.
        """
        return (
            self.origin_x + cell.col * self.tile_px + self.tile_px // 2,
            self.origin_y + cell.row * self.tile_px + self.tile_px // 2,
        )


DIRECTION_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}
