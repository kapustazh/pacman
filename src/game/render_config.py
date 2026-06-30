from __future__ import annotations

from dataclasses import dataclass

from game.level import CellPos, LevelLayout
from sprites.sprite_types import Direction


@dataclass(frozen=True, slots=True)
class MazeBounds:
    """Screen-space bounds for the centered maze playfield."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return pixel center of the maze playfield."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bottom(self) -> int:
        """Return bottom edge of the maze playfield."""
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class WorldRenderConfig:
    """Pixel scale and screen offset for grid-to-surface conversion."""

    tile_px: int = 16
    origin_x: int = 0
    origin_y: int = 0

    def maze_bounds(self, layout: LevelLayout) -> MazeBounds:
        """Return screen-space bounds for this config and layout."""
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
        """Build centered config for a layout on screen."""
        width_px = layout.width * tile_px
        height_px = layout.height * tile_px
        screen_w, screen_h = screen_size
        return cls(
            tile_px=tile_px,
            origin_x=(screen_w - width_px) // 2,
            origin_y=(screen_h - height_px) // 2,
        )


DIRECTION_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}


def direction_delta(direction: Direction) -> tuple[int, int]:
    return DIRECTION_DELTA[direction]


def cell_center(config: WorldRenderConfig, cell: CellPos) -> tuple[int, int]:
    """Convert grid cell to pixel center."""
    tile_px = config.tile_px
    return (
        config.origin_x + cell.col * tile_px + tile_px // 2,
        config.origin_y + cell.row * tile_px + tile_px // 2,
    )
