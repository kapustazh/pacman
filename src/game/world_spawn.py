"""Instantiate entities on a GameWorld from its level layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from entities.wall_tile_entity import WallTileEntity
from game.level import CellPos
from game.wall_tile_picker import pick
from maze.map_data import TileType
from sprites.sprite_types import Direction

if TYPE_CHECKING:
    from game.game_world import GameWorld


def spawn_from_layout(world: GameWorld) -> None:
    """Instantiate walls, pellets, ghosts, and the player from layout.

    Args:
        world: Target world whose sprite groups are populated.
    """
    cfg = world._render_config
    # Enclosed holes inside wall formations get a 2x2-tile solid fill
    # first, reaching the centre lines of the surrounding wall tiles so
    # the whole formation reads as one solid mass. Wall line art is added
    # afterwards and draws on top (same layer, insertion order).
    for pos in world._layout.unreachable_floor:
        fill = WallTileEntity(
            world._catalog.wall_fill,
            world._catalog.wall_fill_white,
            cfg.cell_center(pos),
        )
        world._wall_sprites.append(fill)
        world.all_sprites.add(fill, layer=fill.layer)
    for row_index, row in enumerate(world._layout.cells):
        for col_index, tile in enumerate(row):
            pos = CellPos(row_index, col_index)
            if tile != TileType.WALL:
                continue
            wall_kind = pick(world._layout, pos)
            blue_surface = world._catalog.maze_tiles[wall_kind]
            white_surface = world._catalog.maze_white_tiles[wall_kind]
            wall = WallTileEntity(
                blue_surface,
                white_surface,
                cfg.cell_center(pos),
            )
            world._wall_sprites.append(wall)
            world.all_sprites.add(wall, layer=wall.layer)

    for pos in world._layout.pellet_cells:
        pellet = PelletEntity(
            world._catalog.dot_surface,
            pos,
            cfg.cell_center(pos),
            world.pellet_points,
        )
        world.all_sprites.add(pellet, layer=pellet.layer)
        world._pellets[pos] = pellet

    for pos in world._layout.power_pellet_cells:
        pellet = PelletEntity(
            world._catalog.power_pellet_surface,
            pos,
            cfg.cell_center(pos),
            world.power_pellet_points,
        )
        world.all_sprites.add(pellet, layer=pellet.layer)
        world._pellets[pos] = pellet

    for kind, cell in world._layout.ghost_spawns:
        ghost = GhostEntity(
            kind,
            world._catalog.ghosts_by_kind[kind],
            world._catalog.ghost_frightened,
            cell,
            cfg.cell_center(cell),
            flash_animation=world._catalog.ghost_frightened_flash,
            eyes_animation=world._catalog.ghost_eyes,
        )
        world._ghosts[kind] = ghost
        world._ghost_home[kind] = cell
        world.all_sprites.add(ghost, layer=ghost.layer)

    spawn = world._layout.player_spawn
    pacman_by_dir = {
        direction: world._catalog.pacman[direction] for direction in Direction
    }
    world._player = PlayerEntity(
        pacman_by_dir,
        spawn,
        cfg.cell_center(spawn),
        death_animation=world._catalog.pacman_death,
    )
    world.all_sprites.add(world._player, layer=world._player.layer)
