from __future__ import annotations

from collections import OrderedDict
from enum import IntEnum
from pathlib import Path

import pygame
from pygame.surface import Surface

TEXT_SHEET_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "new_assets"
    / "Arcade - Pac-Man - Miscellaneous - Text.png"
)

CELL_SIZE = 8
ROWS_PER_COLOR = 4
_RENDER_CACHE_MAX = 128
_SCALED_GLYPH_CACHE_MAX = 256

SCREEN_BACKDROP = (0, 0, 0)
MENU_ROW_HIGHLIGHT_COLOR = (40, 40, 80, 120)


class ArcadeTextColor(IntEnum):
    """Vertical color bands on the arcade text sprite sheet."""

    WHITE = 0
    RED = 1
    PINK = 2
    BLUE = 3
    GOLD = 4
    ROSE = 5
    YELLOW = 6


_GLYPH_SHEET_CELLS: dict[str, tuple[int, int]] = {
    **{chr(ord("A") + index): (index, 0) for index in range(15)},  # A-O
    **{chr(ord("P") + index): (index, 1) for index in range(11)},  # P-Z
    "!": (11, 1),
    "©": (12, 1),
    "/": (10, 2),
    "-": (11, 2),
    '"': (12, 2),
    **{str(digit): (digit, 2) for digit in range(10)},
}


class ArcadeFontAtlas:
    """Lazy-loaded glyph atlas sliced from the Pac-Man text sheet."""

    __slots__ = ("_glyphs_by_color", "_loaded")

    def __init__(self) -> None:
        self._glyphs_by_color: dict[ArcadeTextColor, dict[str, Surface]] = {}
        self._loaded = False

    def is_loaded(self) -> bool:
        """Return True when the atlas has been sliced."""
        return self._loaded

    def ensure_loaded(self) -> None:
        """Load the atlas if it is not already available."""
        self.load()

    def load(self) -> None:
        """Load and slice the text sheet once."""
        if self._loaded:
            return

        if not TEXT_SHEET_PATH.exists():
            raise FileNotFoundError(f"Text sheet not found: {TEXT_SHEET_PATH}")

        sheet = pygame.image.load(TEXT_SHEET_PATH).convert_alpha()
        for color in ArcadeTextColor:
            block_row = int(color) * ROWS_PER_COLOR
            glyphs: dict[str, Surface] = {}
            for char, (col, row) in _GLYPH_SHEET_CELLS.items():
                rect = pygame.Rect(
                    col * CELL_SIZE,
                    (block_row + row) * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                glyphs[char] = sheet.subsurface(rect).copy()
            self._glyphs_by_color[color] = glyphs

        self._loaded = True

    def glyph(self, char: str, color: ArcadeTextColor) -> Surface | None:
        """Return a single glyph surface for char and color."""
        if not self._loaded:
            self.load()
        return self._glyphs_by_color[color].get(char.upper())


class ArcadeTextRenderer:
    """Arcade text rendering with injected atlas and bounded caches."""

    __slots__ = ("_atlas", "_render_cache", "_scaled_glyph_cache")

    def __init__(self) -> None:
        self._atlas = ArcadeFontAtlas()
        self._scaled_glyph_cache: dict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = {}
        self._render_cache: OrderedDict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = OrderedDict()

    def preload(self) -> None:
        """Load text atlas up front so first menu frame does not hitch."""
        self._atlas.load()

    def font(
        self,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> ArcadeFont:
        """Return a font bound to this renderer instance."""
        return ArcadeFont(self, color, scale)

    def draw_screen_backdrop(self, surface: Surface) -> None:
        """Fill screen to hide states beneath on the scene stack."""
        surface.fill(SCREEN_BACKDROP)

    def draw_centered_arcade_text(
        self,
        surface: Surface,
        text: str,
        y: int,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> pygame.Rect:
        """Draw horizontally centered arcade text and return its rect."""
        rendered = self.font(color, scale).render(text)
        rect = rendered.get_rect(center=(surface.get_width() // 2, y))
        surface.blit(rendered, rect)
        return rect

    def draw_centered_menu_line(
        self,
        surface: Surface,
        label: str,
        y: int,
        *,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> None:
        """Draw centered menu label."""
        rendered = self.font(color, scale).render(label)
        rect = rendered.get_rect(center=(surface.get_width() // 2, y))
        surface.blit(rendered, rect)

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

    def _cache_render(
        self,
        cache_key: tuple[str, ArcadeTextColor, int],
        surface: Surface,
    ) -> None:
        """Store rendered text with bounded LRU eviction."""
        self._render_cache[cache_key] = surface
        self._render_cache.move_to_end(cache_key)
        while len(self._render_cache) > _RENDER_CACHE_MAX:
            self._render_cache.popitem(last=False)

    def _scaled_glyph(
        self,
        char: str,
        color: ArcadeTextColor,
        scale: int,
    ) -> Surface | None:
        """Return cached scaled glyph surface."""
        glyph = self._atlas.glyph(char, color)
        if glyph is None:
            return None
        if scale == 1:
            return glyph
        key = (char.upper(), color, scale)
        cached = self._scaled_glyph_cache.get(key)
        if cached is not None:
            return cached
        size = (CELL_SIZE * scale, CELL_SIZE * scale)
        scaled = pygame.transform.scale(glyph, size)
        self._scaled_glyph_cache[key] = scaled
        while len(self._scaled_glyph_cache) > _SCALED_GLYPH_CACHE_MAX:
            self._scaled_glyph_cache.pop(next(iter(self._scaled_glyph_cache)))
        return scaled


class ArcadeFont:
    """Render strings using arcade sheet glyphs."""

    __slots__ = ("_color", "_renderer", "_scale")

    def __init__(
        self,
        renderer: ArcadeTextRenderer,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> None:
        self._renderer = renderer
        self._color = color
        self._scale = scale

    def advance(self) -> int:
        """Return fixed monospace advance for one glyph cell."""
        return CELL_SIZE * self._scale

    def line_height(self) -> int:
        """Return rendered line height."""
        return self.advance()

    def render(self, text: str) -> Surface:
        """Render text to a surface at the configured scale."""
        self._renderer._atlas.ensure_loaded()

        upper = text.upper()
        cache_key = (upper, self._color, self._scale)
        cached = self._renderer._render_cache.get(cache_key)
        if cached is not None:
            self._renderer._render_cache.move_to_end(cache_key)
            return cached

        surface = self._build_surface(upper)
        self._renderer._cache_render(cache_key, surface)
        return surface

    def render_uncached(self, text: str) -> Surface:
        """Render dynamic text without storing it in the render cache."""
        self._renderer._atlas.ensure_loaded()
        return self._build_surface(text.upper())

    def _build_surface(self, upper: str) -> Surface:
        advance = self.advance()
        width = 0
        for char in upper:
            if char == " ":
                width += self._space_advance()
                continue
            if self._renderer._atlas.glyph(char, self._color) is not None:
                width += advance
        width = max(width, 0)
        height = advance
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        x = 0
        for char in upper:
            if char == " ":
                x += self._space_advance()
                continue
            scaled = self._renderer._scaled_glyph(
                char, self._color, self._scale
            )
            if scaled is None:
                x += advance
                continue
            blit_x = x + (advance - scaled.get_width()) // 2
            blit_y = (advance - scaled.get_height()) // 2
            surface.blit(scaled, (blit_x, blit_y))
            x += advance

        return surface

    def _space_advance(self) -> int:
        """Spaces use half cell width so inline gaps stay tight."""
        return max(1, self.advance() // 2)


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


def draw_menu_row_highlight(
    surface: Surface,
    index: int,
    start_y: int,
    line_height: int,
    *,
    color: tuple[int, int, int, int] = MENU_ROW_HIGHLIGHT_COLOR,
) -> None:
    """Draw semi-transparent highlight band behind a menu row."""
    row = menu_row_rect(surface, index, start_y, line_height)
    highlight = pygame.Surface(row.size, pygame.SRCALPHA)
    highlight.fill(color)
    surface.blit(highlight, row.topleft)
