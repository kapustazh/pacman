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
    GOLD = 4
    ROSE = 5
    YELLOW = 6


class ArcadeTextFont:
    """Color/scale-bound view of a renderer for one draw style."""

    __slots__ = ("_color", "_renderer", "_scale")

    def __init__(
        self,
        renderer: ArcadeTextRenderer,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> None:
        self._renderer: ArcadeTextRenderer = renderer
        self._color: ArcadeTextColor = color
        self._scale: int = scale

    def advance(self) -> int:
        """Return fixed monospace advance for one glyph cell."""
        return ArcadeTextRenderer.CELL_SIZE * self._scale

    def render(self, text: str) -> Surface:
        """Render text to a surface at the configured scale."""
        self._renderer._ensure_atlas()

        upper = text.upper()
        cache_key = (upper, self._color, self._scale)
        cached = self._renderer._render_cache.get(cache_key)
        if cached is not None:
            self._renderer._render_cache.move_to_end(cache_key)
            return cached

        surface = self._build_surface(upper)
        self._renderer._cache_render(cache_key, surface)
        return surface

    def _build_surface(self, upper: str) -> Surface:
        advance = self.advance()
        width = 0
        for char in upper:
            if char == " ":
                width += self._space_advance()
                continue
            if self._renderer._glyph(char, self._color) is not None:
                width += advance
        width = max(width, 0)
        height = advance
        surface = Surface((width, height), pygame.SRCALPHA)

        x = 0
        for char in upper:
            if char == " ":
                x += self._space_advance()
                continue
            scaled = self._renderer._scaled_glyph(
                char, self._color, self._scale
            )
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

    def _space_advance(self) -> int:
        """Spaces use half cell width so inline gaps stay tight."""
        return max(1, self.advance() // 2)


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
    SCALED_GLYPH_CACHE_MAX: ClassVar[int] = 256
    SCREEN_BACKDROP: ClassVar[tuple[int, int, int]] = (0, 0, 0)
    MENU_ROW_HIGHLIGHT_COLOR: ClassVar[tuple[int, int, int, int]] = (
        40,
        40,
        80,
        120,
    )

    __slots__ = (
        "_atlas_loaded",
        "_glyphs_by_color",
        "_render_cache",
        "_scaled_glyph_cache",
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

    def font(
        self,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> ArcadeTextFont:
        """Return a font bound to this renderer instance."""
        return ArcadeTextFont(self, color, scale)

    def draw_screen_backdrop(self, surface: Surface) -> None:
        """Fill screen to hide states beneath on the scene stack."""
        surface.fill(self.SCREEN_BACKDROP)

    def draw_centered_arcade_text(
        self,
        surface: Surface,
        text: str,
        y: int,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> pygame.rect.Rect:
        """Draw horizontally centered arcade text and return its rect."""
        rendered = self.font(color, scale).render(text)
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
        font = self.font(color, scale)
        advance = font.advance()
        label_width = label_chars * advance
        gap_width = gap_chars * advance
        value_surface = font.render(value)
        block_width = label_width + gap_width + value_surface.get_width()
        left = (surface.get_width() - block_width) // 2

        label_surface = font.render(label)
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
        self._scaled_glyph_cache[key] = scaled
        while len(self._scaled_glyph_cache) > self.SCALED_GLYPH_CACHE_MAX:
            self._scaled_glyph_cache.pop(next(iter(self._scaled_glyph_cache)))
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
