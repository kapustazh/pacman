# [transition UI] generic drawing helpers shared by HUD and menu screens.

from __future__ import annotations

import pygame
from pygame.surface import Surface

from states.text import ArcadeTextRenderer


def plus_glyph(color: tuple[int, int, int, int], scale: int) -> Surface:
    """Return a plus sign for HUD life overflow.

    Args:
        color: RGBA color for the drawn lines.
        scale: Integer scale factor for the glyph cell.

    Returns:
        Alpha surface containing the plus sign.
    """
    cell = ArcadeTextRenderer.CELL_SIZE * scale
    surface = pygame.Surface((cell, cell), pygame.SRCALPHA)
    cx = cy = cell // 2
    thickness = max(1, scale)
    arm = cx - scale
    pygame.draw.line(surface, color, (cx - arm, cy), (cx + arm, cy), thickness)
    pygame.draw.line(surface, color, (cx, cy - arm), (cx, cy + arm), thickness)
    return surface


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
    if color is None:
        color = ArcadeTextRenderer.MENU_ROW_HIGHLIGHT_COLOR
    width = int(surface.get_width() * 0.9)
    left = (surface.get_width() - width) // 2
    y_center = start_y + index * line_height
    row = pygame.Rect(left, y_center - line_height // 2, width, line_height)
    highlight = pygame.Surface((width, line_height), pygame.SRCALPHA)
    highlight.fill(color)
    surface.blit(highlight, row.topleft)
