from core.resources import AssetCatalog
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.level import CellPos
from game.render_config import WorldRenderConfig
from sprites.types import Direction, TileKind

PELLET_POINTS = 10
POWER_PELLET_POINTS = 50


class EntityFactory:
    """Create pygame entities from immutable level data and loaded assets."""

    __slots__ = ("_catalog", "_render_config")

    def __init__(
        self,
        catalog: AssetCatalog,
        render_config: WorldRenderConfig,
    ) -> None:
        self._catalog = catalog
        self._render_config = render_config

    def cell_center(self, cell: CellPos) -> tuple[int, int]:
        """Convert grid cell to pixel center."""
        tile_px = self._render_config.tile_px
        return (
            cell.col * tile_px + tile_px // 2,
            cell.row * tile_px + tile_px // 2,
        )

    def create_wall(self, cell: CellPos) -> WallTileEntity:
        """Create wall tile entity."""
        surface = self._catalog.maze.tiles[TileKind.WALL].surface
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
            direction: self._catalog.pacman[direction] for direction in Direction
        }
        return PlayerEntity(
            animations_by_direction,
            cell,
            self.cell_center(cell),
        )
