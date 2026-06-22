from core.resources import AssetCatalog
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.level import CellPos, LevelLayout
from game.render_config import WorldRenderConfig
from game.wall_tile_picker import pick_wall_tile
from sprites.sprite_types import Direction

PELLET_POINTS = 10
POWER_PELLET_POINTS = 50


class EntityFactory:
    """Create pygame entities from immutable level data and loaded assets."""

    __slots__ = ("_catalog", "_layout", "_render_config")

    def __init__(
        self,
        catalog: AssetCatalog,
        render_config: WorldRenderConfig,
        layout: LevelLayout,
    ) -> None:
        self._catalog = catalog
        self._render_config = render_config
        self._layout = layout

    def cell_center(self, cell: CellPos) -> tuple[int, int]:
        """Convert grid cell to pixel center."""
        tile_px = self._render_config.tile_px
        return (
            self._render_config.origin_x + cell.col * tile_px + tile_px // 2,
            self._render_config.origin_y + cell.row * tile_px + tile_px // 2,
        )

    def create_wall(self, cell: CellPos) -> WallTileEntity:
        """Create wall tile entity with neighbor-aware sprite selection."""
        tile_kind = pick_wall_tile(self._layout, cell)
        surface = self._catalog.maze.tiles[tile_kind].surface
        return WallTileEntity(surface, cell, self.cell_center(cell))

    def create_pellet(self, cell: CellPos) -> PelletEntity:
        """Create normal pellet entity."""
        surface = self._catalog.items.dot.surface
        return PelletEntity(
            surface,
            cell,
            self.cell_center(cell),
            PELLET_POINTS,
        )

    def create_power_pellet(self, cell: CellPos) -> PelletEntity:
        """Create power pellet entity."""
        surface = self._catalog.items.power_pellet.surface
        return PelletEntity(
            surface,
            cell,
            self.cell_center(cell),
            POWER_PELLET_POINTS,
        )

    def create_player(self, cell: CellPos) -> PlayerEntity:
        """Create player entity from loaded directional animations."""
        animations_by_direction = {
            direction: self._catalog.pacman[direction]
            for direction in Direction
        }
        return PlayerEntity(
            animations_by_direction,
            cell,
            self.cell_center(cell),
        )
