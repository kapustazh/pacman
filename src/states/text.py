# [transition UI] arcade text renderer for menus/HUD.

from __future__ import annotations

from collections import OrderedDict
from enum import IntEnum
from pathlib import Path
from typing import ClassVar

import pygame
from pygame.surface import Surface


class ArcadeTextColor(IntEnum):
    """Palette rows on the arcade text sprite sheet."""

    WHITE = 0
    RED = 1
    CYAN = 3
    GOLD = 4
    ROSE = 5
    YELLOW = 6


class ArcadeTextRenderer:
    """Renders arcade-style text from a shared glyph atlas."""

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
        """Initialize empty glyph and render caches."""
        self._glyphs_by_color: dict[ArcadeTextColor, dict[str, Surface]] = {}
        self._scaled_glyph_cache: dict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = {}
        self._render_cache: OrderedDict[
            tuple[str, ArcadeTextColor, int], Surface
        ] = OrderedDict()

    def preload(self) -> None:
        """Warm the atlas so the first frame does not hitch."""
        self._ensure_atlas()

    def advance(self, scale: int = 3) -> int:
        """Return pixel width of one monospace glyph cell.

        Args:
            scale: Integer scale factor applied to the base cell size.

        Returns:
            Advance width in pixels.
        """
        return self.CELL_SIZE * scale

    def render(
        self,
        text: str,
        color: ArcadeTextColor = ArcadeTextColor.WHITE,
        scale: int = 3,
    ) -> Surface:
        """Build or return cached arcade text at the given color and scale.

        Args:
            text: Source string; uppercased before lookup.
            color: Palette row to draw from.
            scale: Integer scale factor for glyphs.

        Returns:
            Alpha surface containing the rendered line.
        """
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
        """Lay out and blit glyphs into a single-line surface.

        Args:
            upper: Uppercased text to render.
            color: Palette row to draw from.
            scale: Integer scale factor for glyphs.

        Returns:
            Alpha surface with the composed line.
        """
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
        """Draw horizontally centered arcade text.

        Args:
            surface: Destination draw target.
            text: String to render.
            y: Vertical center of the text line.
            color: Palette row to draw from.
            scale: Integer scale factor for glyphs.

        Returns:
            Bounding rect of the blitted text.
        """
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
        """Draw a centered label/value row with fixed column widths.

        Args:
            surface: Destination draw target.
            label: Left-column text.
            value: Right-column text.
            y: Vertical center of the row.
            color: Palette row to draw from.
            scale: Integer scale factor for glyphs.
            label_chars: Fixed label width in glyph cells.
            gap_chars: Gap between columns in glyph cells.
        """
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
        """Load and slice the text sheet on first use.

        Raises:
            FileNotFoundError: If the sprite sheet path is missing.
        """
        if self._glyphs_by_color:
            return

        if not self.TEXT_SHEET_PATH.exists():
            raise FileNotFoundError(
                f"Text sheet not found: {self.TEXT_SHEET_PATH}"
            )

        sheet = pygame.image.load(self.TEXT_SHEET_PATH).convert()
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
                glyph = sheet.subsurface(rect).copy()
                glyph.set_colorkey((0, 0, 0))
                glyphs[char] = glyph
            self._glyphs_by_color[color] = glyphs

    def _glyph(self, char: str, color: ArcadeTextColor) -> Surface | None:
        """Look up one glyph surface for a character and color.

        Args:
            char: Single character to resolve.
            color: Palette row to draw from.

        Returns:
            Glyph surface, or None if the character is unsupported.
        """
        self._ensure_atlas()
        return self._glyphs_by_color[color].get(char.upper())

    def _cache_render(
        self,
        cache_key: tuple[str, ArcadeTextColor, int],
        surface: Surface,
    ) -> None:
        """Store a rendered line and evict the oldest entry when full.

        Args:
            cache_key: Tuple of uppercased text, color, and scale.
            surface: Rendered line to cache.
        """
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
        """Return a cached scaled glyph, building it on first use.

        Args:
            char: Single character to scale.
            color: Palette row to draw from.
            scale: Integer scale factor for the glyph cell.

        Returns:
            Scaled glyph surface, or None if the character is unsupported.
        """
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
        scaled.set_colorkey((0, 0, 0))
        self._scaled_glyph_cache[key] = scaled
        return scaled
