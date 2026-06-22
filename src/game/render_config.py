from __future__ import annotations

from dataclasses import dataclass

from game.level import LevelLayout


@dataclass(frozen=True, slots=True)
class MazeViewport:
    """Screen-space bounds for the centered maze playfield."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return pixel center of the maze viewport."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bottom(self) -> int:
        """Return bottom edge of the maze viewport."""
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class WorldRenderConfig:
    """Pixel scale and screen offset for grid-to-surface conversion."""

    tile_px: int = 16
    origin_x: int = 0
    origin_y: int = 0

    @classmethod
    def centered(
        cls,
        layout: LevelLayout,
        screen_size: tuple[int, int],
        tile_px: int = 16,
    ) -> WorldRenderConfig:
        """Build config that centers the level grid on screen."""
        width_px = layout.width * tile_px
        height_px = layout.height * tile_px
        screen_w, screen_h = screen_size
        return cls(
            tile_px=tile_px,
            origin_x=(screen_w - width_px) // 2,
            origin_y=(screen_h - height_px) // 2,
        )

    def viewport_for(self, layout: LevelLayout) -> MazeViewport:
        """Return screen-space bounds for the configured layout."""
        return MazeViewport(
            x=self.origin_x,
            y=self.origin_y,
            width=layout.width * self.tile_px,
            height=layout.height * self.tile_px,
        )


DEFAULT_RENDER_CONFIG = WorldRenderConfig()
