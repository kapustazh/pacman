# [transition UI] arcade text renderer for menus/HUD.

from __future__ import annotations

from collections import OrderedDict
from enum import IntEnum
from pathlib import Path
from typing import ClassVar

import pygame
from pygame.surface import Surface


class ArcadeTextColor(IntEnum):
    """Vertical color bands on the arcade text sprite sheet."""

    WHITE = 0
    RED = 1
    CYAN = 3
    GOLD = 4
    ROSE = 5
    YELLOW = 6


class ArcadeTextRenderer:
    """Arcade text rendering with lazy glyph atlas and bounded caches."""

    TEXT_SHEET_PATH: ClassVar[Path] = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "new_assets"
        / "Arcade - Pac-Man - Miscellaneous - Text.png"
    )
    CELL_SIZE: ClassVar[int] = 8
    ROWS_PER_COLOR: ClassVar[int] = 4
    GLYPH_SHEET_CELLS: ClassVar[dict[str, tuple[int, int]]] = {
        **{chr(ord("A") + index): (index, 0) for index in range(15)},  # A-O
        **{chr(ord("P") + index): (index, 1) for index in range(11)},  # P-Z
        "!": (11, 1),
        "©": (12, 1),
        "/": (10, 2),
        "-": (11, 2),
        '"': (12, 2),
        **{str(digit): (digit, 2) for digit in range(10)},
    }
    RENDER_CACHE_MAX: ClassVar[int] = 128
    MENU_ROW_HIGHLIGHT_COLOR: ClassVar[tuple[int, int, int, int]] = (
        40,
        40,
        80,
        120,
    )

    def __init__(self) -> None:
        self._glyphs_by_color: dict[ArcadeTextColor, dict[str, Surface]] = {}
        self._atlas_loaded = False
        self._scaled_glyph_cache: dict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = {}
        self._render_cache: OrderedDict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = OrderedDict()

    def preload(self) -> None:
        """Load text atlas up front so first menu frame does not hitch."""
        self._ensure_atlas()

    def advance(self, scale: int = 3) -> int:
        """Return fixed monospace advance for one glyph cell."""
        return self.CELL_SIZE * scale

    def render(
        self,
        text: str,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> Surface:
        """Render text to a cached surface at the given color and scale."""
        self._ensure_atlas()
        upper = text.upper()
        cache_key = (upper, color, scale)
        cached = self._render_cache.get(cache_key)
        if cached is not None:
            self._render_cache.move_to_end(cache_key)
            return cached
        surface = self._build_surface(upper, color, scale)
        self._cache_render(cache_key, surface)
        return surface

    def _build_surface(
        self, upper: str, color: ArcadeTextColor, scale: int
    ) -> Surface:
        advance = self.advance(scale)
        # spaces use half cell width so inline gaps stay tight
        space = max(1, advance // 2)
        width = 0
        for char in upper:
            if char == " ":
                width += space
            elif self._glyph(char, color) is not None:
                width += advance
        surface = Surface((width, advance), pygame.SRCALPHA)

        x = 0
        for char in upper:
            if char == " ":
                x += space
                continue
            scaled = self._scaled_glyph(char, color, scale)
            if scaled is None:
                # No glyph for this char (e.g. unsupported punctuation):
                # reserve no space, matching the width pass above — do not
                # advance, or later characters get pushed past the
                # surface's width and are silently clipped.
                continue
            blit_x = x + (advance - scaled.get_width()) // 2
            blit_y = (advance - scaled.get_height()) // 2
            surface.blit(scaled, (blit_x, blit_y))
            x += advance

        return surface

    def draw_centered_arcade_text(
        self,
        surface: Surface,
        text: str,
        y: int,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> pygame.rect.Rect:
        """Draw horizontally centered arcade text and return its rect."""
        rendered = self.render(text, color, scale)
        rect = rendered.get_rect(center=(surface.get_width() // 2, y))
        surface.blit(rendered, rect)
        return rect

    def draw_arcade_two_column_row(
        self,
        surface: Surface,
        label: str,
        value: str,
        y: int,
        *,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
        label_chars: int = 6,
        gap_chars: int = 2,
    ) -> None:
        """Draw one aligned label/value row centered on screen."""
        advance = self.advance(scale)
        label_width = label_chars * advance
        gap_width = gap_chars * advance
        value_surface = self.render(value, color, scale)
        block_width = label_width + gap_width + value_surface.get_width()
        left = (surface.get_width() - block_width) // 2

        label_surface = self.render(label, color, scale)
        label_rect = label_surface.get_rect(midright=(left + label_width, y))
        value_rect = value_surface.get_rect(
            midleft=(left + label_width + gap_width, y)
        )
        surface.blit(label_surface, label_rect)
        surface.blit(value_surface, value_rect)

    def _ensure_atlas(self) -> None:
        """Load and slice the text sheet once."""
        if self._atlas_loaded:
            return

        if not self.TEXT_SHEET_PATH.exists():
            raise FileNotFoundError(
                f"Text sheet not found: {self.TEXT_SHEET_PATH}"
            )

        sheet = pygame.image.load(self.TEXT_SHEET_PATH).convert_alpha()
        for color in ArcadeTextColor:
            block_row = int(color) * self.ROWS_PER_COLOR
            glyphs: dict[str, Surface] = {}
            for char, (col, row) in self.GLYPH_SHEET_CELLS.items():
                rect = pygame.Rect(
                    col * self.CELL_SIZE,
                    (block_row + row) * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                glyphs[char] = sheet.subsurface(rect).copy()
            self._glyphs_by_color[color] = glyphs

        self._atlas_loaded = True

    def _glyph(self, char: str, color: ArcadeTextColor) -> Surface | None:
        """Return a single glyph surface for char and color."""
        self._ensure_atlas()
        return self._glyphs_by_color[color].get(char.upper())

    def _cache_render(
        self,
        cache_key: tuple[str, ArcadeTextColor, int],
        surface: Surface,
    ) -> None:
        """Store rendered text with bounded LRU eviction."""
        self._render_cache[cache_key] = surface
        self._render_cache.move_to_end(cache_key)
        while len(self._render_cache) > self.RENDER_CACHE_MAX:
            self._render_cache.popitem(last=False)

    def _scaled_glyph(
        self,
        char: str,
        color: ArcadeTextColor,
        scale: int,
    ) -> Surface | None:
        """Return cached scaled glyph surface."""
        glyph = self._glyph(char, color)
        if glyph is None:
            return None
        if scale == 1:
            return glyph
        key = (char.upper(), color, scale)
        cached = self._scaled_glyph_cache.get(key)
        if cached is not None:
            return cached
        size = (self.CELL_SIZE * scale, self.CELL_SIZE * scale)
        scaled = pygame.transform.scale(glyph, size)
        # bounded naturally: ~40 glyphs x 6 colors x a few scales
        self._scaled_glyph_cache[key] = scaled
        return scaled


_plus_glyph_cache: dict[tuple[tuple[int, int, int, int], int], Surface] = {}


def plus_glyph(color: tuple[int, int, int, int], scale: int) -> Surface:
    """Return a cached plus sign surface for HUD life overflow."""
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
    """Return centered row band for menu selection highlight."""
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
    """Return cached semi-transparent menu row highlight band."""
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
    """Draw semi-transparent highlight band behind a menu row."""
    row = menu_row_rect(surface, index, start_y, line_height)
    highlight = menu_row_highlight_surface(
        surface.get_width(), line_height, color=color
    )
    surface.blit(highlight, row.topleft)
