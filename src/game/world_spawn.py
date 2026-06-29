from __future__ import annotations

from typing import TYPE_CHECKING

from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.level import CellPos, CellType
from game.wall_tile_picker import pick
from sprites.sprite_types import Direction, GhostKind

if TYPE_CHECKING:
    from game.game_world import GameWorld

DIRECTION_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}


def cell_center(world: GameWorld, cell: CellPos) -> tuple[int, int]:
    """Convert grid cell to pixel center."""
    tile_px = world._render_config.tile_px
    return (
        world._render_config.origin_x + cell.col * tile_px + tile_px // 2,
        world._render_config.origin_y + cell.row * tile_px + tile_px // 2,
    )


def direction_delta(direction: Direction) -> tuple[int, int]:
    return DIRECTION_DELTA[direction]


def spawn_wall(world: GameWorld, cell: CellPos) -> WallTileEntity:
    tile_kind = pick(world._layout, cell)
    blue_surface = world._catalog.maze_tiles[tile_kind]
    white_surface = world._catalog.maze_white_tiles[tile_kind]
    return WallTileEntity(
        blue_surface,
        white_surface,
        cell,
        cell_center(world, cell),
    )


def spawn_pellet(world: GameWorld, cell: CellPos) -> PelletEntity:
    return PelletEntity(
        world._catalog.dot_surface,
        cell,
        cell_center(world, cell),
        world.PELLET_POINTS,
    )


def spawn_power_pellet(world: GameWorld, cell: CellPos) -> PelletEntity:
    return PelletEntity(
        world._catalog.power_pellet_surface,
        cell,
        cell_center(world, cell),
        world.POWER_PELLET_POINTS,
    )


def spawn_player(world: GameWorld, cell: CellPos) -> PlayerEntity:
    animations_by_direction = {
        direction: world._catalog.pacman[direction] for direction in Direction
    }
    return PlayerEntity(
        animations_by_direction,
        cell,
        cell_center(world, cell),
        death_animation=world._catalog.pacman_death,
    )


def spawn_ghost(
    world: GameWorld,
    kind: GhostKind,
    cell: CellPos,
) -> GhostEntity:
    return GhostEntity(
        kind,
        world._catalog.ghosts.by_kind[kind],
        world._catalog.ghosts.frightened,
        cell,
        cell_center(world, cell),
    )


def spawn_from_layout(world: GameWorld) -> None:
    for row_index, row in enumerate(world._layout.cells):
        for col_index, cell_type in enumerate(row):
            pos = CellPos(row_index, col_index)
            if cell_type == CellType.WALL:
                wall = spawn_wall(world, pos)
                world._wall_sprites.append(wall)
                world.all_sprites.add(wall, layer=wall.layer)

    for pos in world._layout.pellet_cells:
        pellet = spawn_pellet(world, pos)
        world.all_sprites.add(pellet, layer=pellet.layer)
        world.consumables.add(pellet)

    for pos in world._layout.power_pellet_cells:
        pellet = spawn_power_pellet(world, pos)
        world.all_sprites.add(pellet, layer=pellet.layer)
        world.consumables.add(pellet)

    for kind, cell in world._layout.ghost_spawns:
        ghost = spawn_ghost(world, kind, cell)
        world._ghosts[kind] = ghost
        world._ghost_home[kind] = cell
        world.all_sprites.add(ghost, layer=ghost.layer)

    world._player = spawn_player(world, world._layout.player_spawn)
    world.all_sprites.add(world._player, layer=world._player.layer)
