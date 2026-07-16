"""Instantiate entities on a GameWorld from its level layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame.surface import Surface

from entities.ghost_entity import GhostEntity
from entities.pellet_entity import PelletEntity
from entities.player_entity import PlayerEntity
from game.level import CellPos
from game.render_config import WorldRenderConfig
from game.wall_tile_picker import pick
from maze.map_data import TileType
from sprites.sprite_types import Direction

if TYPE_CHECKING:
    from game.game_world import GameWorld
    from sprites.sprite_types import TileKind


def draw_maze_background(
    world: GameWorld,
    fill: Surface,
    tiles: dict[TileKind, Surface],
) -> Surface:
    """Draw wall fills and autotile art into one maze-local surface.
    Args:
        world: World whose layout supplies wall and fill positions.
        fill: Wall fill surface.
        tiles: Wall tile art keyed by autotile kind.

    Returns:
        Maze-local surface with fills and wall line art in.
    """
    layout = world._layout
    local = WorldRenderConfig(tile_px=world._render_config.tile_px)
    bounds = local.maze_bounds(layout)
    background = pygame.Surface((bounds.width, bounds.height))
    for pos in layout.unreachable_floor:   # empty cells inside walls
        background.blit(fill, fill.get_rect(center=local.cell_center(pos)))
    for row_index, row in enumerate(layout.cells):
        for col_index, tile in enumerate(row):
            if tile != TileType.WALL:
                continue
            pos = CellPos(row_index, col_index)
            art = tiles[pick(layout, pos)]
            background.blit(art, art.get_rect(center=local.cell_center(pos)))
    return background.convert()


def spawn_from_layout(world: GameWorld) -> None:
    """Draw maze backgrounds and spawn pellets, ghosts, and the player.

    Args:
        world: Target world whose sprite groups are populated.
    """
    cfg = world._render_config
    catalog = world._catalog
    world._maze_background = draw_maze_background(
        world, catalog.wall_fill, catalog.maze_tiles
    )
    world._maze_background_white = draw_maze_background(
        world, catalog.wall_fill_white, catalog.maze_white_tiles
    )

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
