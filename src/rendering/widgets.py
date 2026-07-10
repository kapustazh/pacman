# [transition UI] generic drawing helpers shared by HUD and menu screens.

from __future__ import annotations

import pygame
from pygame.surface import Surface

from states.text import ArcadeTextRenderer

_plus_glyph_cache: dict[tuple[tuple[int, int, int, int], int], Surface] = {}


def plus_glyph(color: tuple[int, int, int, int], scale: int) -> Surface:
    """Return a cached plus sign for HUD life overflow.

    Args:
        color: RGBA color for the drawn lines.
        scale: Integer scale factor for the glyph cell.

    Returns:
        Alpha surface containing the plus sign.
    """
    key = (color, scale)
    cached = _plus_glyph_cache.get(key)
    if cached is not None:
        return cached

    cell = ArcadeTextRenderer.CELL_SIZE * scale
    surface = pygame.Surface((cell, cell), pygame.SRCALPHA)
    cx = cy = cell // 2
    thickness = max(1, scale)
    arm = cx - scale
    pygame.draw.line(surface, color, (cx - arm, cy), (cx + arm, cy), thickness)
    pygame.draw.line(surface, color, (cx, cy - arm), (cx, cy + arm), thickness)
    _plus_glyph_cache[key] = surface
    return surface


def menu_row_rect(
    surface: Surface,
    index: int,
    start_y: int,
    line_height: int,
) -> pygame.Rect:
    """Return the highlight band rect for one menu row.

    Args:
        surface: Screen used to compute horizontal centering.
        index: Zero-based row index.
        start_y: Vertical center of the first row.
        line_height: Pixel height of each row.

    Returns:
        Rect covering the row highlight area.
    """
    width = int(surface.get_width() * 0.9)
    left = (surface.get_width() - width) // 2
    y_center = start_y + index * line_height
    return pygame.Rect(left, y_center - line_height // 2, width, line_height)


_menu_row_highlight_cache: dict[tuple[int, int], Surface] = {}


def menu_row_highlight_surface(
    screen_width: int,
    line_height: int,
    *,
    color: tuple[int, int, int, int] | None = None,
) -> Surface:
    """Return a cached semi-transparent menu row highlight band.

    Args:
        screen_width: Width used to size the highlight strip.
        line_height: Pixel height of the band.
        color: Optional RGBA fill; defaults to the menu highlight color.

    Returns:
        Reusable highlight surface.
    """
    if color is None:
        color = ArcadeTextRenderer.MENU_ROW_HIGHLIGHT_COLOR
    cache_key = (screen_width, line_height)
    cached = _menu_row_highlight_cache.get(cache_key)
    if cached is not None:
        return cached
    width = int(screen_width * 0.9)
    highlight = pygame.Surface((width, line_height), pygame.SRCALPHA)
    highlight.fill(color)
    _menu_row_highlight_cache[cache_key] = highlight
    return highlight


def draw_menu_row_highlight(
    surface: Surface,
    index: int,
    start_y: int,
    line_height: int,
    *,
    color: tuple[int, int, int, int] | None = None,
) -> None:
    """Draw a semi-transparent highlight behind one menu row.

    Args:
        surface: Destination draw target.
        index: Zero-based row index.
        start_y: Vertical center of the first row.
        line_height: Pixel height of each row.
        color: Optional RGBA fill; defaults to the menu highlight color.
    """
    row = menu_row_rect(surface, index, start_y, line_height)
    highlight = menu_row_highlight_surface(
        surface.get_width(), line_height, color=color
    )
    surface.blit(highlight, row.topleft)
