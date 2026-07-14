from __future__ import annotations
from typing import ClassVar

import pygame
from pygame.surface import Surface

from core.context import GameContext
from core.state import BACK_KEYS, GameState
from rendering.widgets import plus_glyph
from states.text import ArcadeTextColor, ArcadeTextRenderer


class InstructionsState(GameState):
    """Static screen listing game controls."""

    INSTRUCTION_ROWS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("MOVE", "WASD / ARROWS"),
        ("PAUSE", "ESC"),
        ("START", "ENTER"),
        ("BACK", "ESC"),
    )

    CHEAT_ROWS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("INVINCIBLE", "I"),
        ("SKIP LEVEL", "N"),
        ("FREEZE", "F"),
        ("SPEED", " / -"),
        ("LIFE", "L"),
    )

    TITLE_Y: ClassVar[int] = 300
    ROW_START_Y: ClassVar[int] = 420
    ROW_SCALE: ClassVar[int] = 3
    TITLE_SCALE: ClassVar[int] = 4
    FOOTER_SCALE: ClassVar[int] = 2
    ROW_GAP: ClassVar[int] = 12
    SECTION_GAP: ClassVar[int] = 24
    SECTION_SCALE: ClassVar[int] = 2
    FOOTER_GAP: ClassVar[int] = 48
    LABEL_CHARS: ClassVar[int] = 6
    GAP_CHARS: ClassVar[int] = 2
    CHEAT_SHIFT_CHARS: ClassVar[int] = 4

    def enter(self, context: GameContext) -> None:
        """No-op; scene has no setup work.

        Args:
            context: Shared game context.
        """

    def leave(self, context: GameContext) -> None:
        """No-op; scene has no teardown work.

        Args:
            context: Shared game context (unused).
        """

    def handle_events(
        self,
        events: list[pygame.event.Event],
        context: GameContext,
    ) -> None:
        """Pop back to the previous scene on back keys.

        Args:
            events: Pygame events for this frame.
            context: Shared game context for scene transitions.
        """
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in BACK_KEYS:
                context.scene_manager.pop()
                return

    def update(self, dt: float, now_ms: int, context: GameContext) -> None:
        """No-op; screen has no simulation.

        Args:
            dt: Elapsed seconds since the last frame (unused).
            now_ms: Monotonic clock in milliseconds (unused).
            context: Shared game context (unused).
        """

    def covers_previous_layers(self) -> bool:
        """Hide the menu while this screen is active.

        Returns:
            Always True so the menu is not drawn underneath.
        """
        return True

    def draw(self, surface: Surface, context: GameContext) -> None:
        """Draw the title, control rows, and return prompt.

        Args:
            surface: Destination draw target.
            context: Shared game context with text renderer.
        """
        text = context.text
        text.draw_centered_arcade_text(
            surface,
            "INSTRUCTIONS",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            scale=self.TITLE_SCALE,
        )

        row_step = text.advance(self.ROW_SCALE) + self.ROW_GAP
        layout = self._table_layout(
            surface,
            text,
            self.INSTRUCTION_ROWS + self.CHEAT_ROWS,
        )
        y = self._draw_rows(
            surface,
            text,
            self.INSTRUCTION_ROWS,
            self.ROW_START_Y,
            row_step,
            layout,
        )

        y += self.SECTION_GAP
        cheat_shift = text.advance(self.ROW_SCALE) * self.CHEAT_SHIFT_CHARS
        cheat_layout = self._shifted_layout(layout, cheat_shift)
        cheat_label_right, cheat_value_left, _ = cheat_layout
        cheats = text.render(
            "CHEATS", ArcadeTextColor.YELLOW, self.SECTION_SCALE
        )
        table_left = cheat_label_right - self.LABEL_CHARS * text.advance(
            self.ROW_SCALE
        )
        max_cheat_value = max(
            self._value_width(text, label, value)
            for label, value in self.CHEAT_ROWS
        )
        table_center_x = (table_left + cheat_value_left + max_cheat_value) // 2
        cheats_rect = cheats.get_rect(center=(table_center_x, y))
        surface.blit(cheats, cheats_rect)
        y += row_step
        y = self._draw_rows(
            surface,
            text,
            self.CHEAT_ROWS,
            y,
            row_step,
            cheat_layout,
        )

        footer_y = y + self.FOOTER_GAP
        text.draw_centered_arcade_text(
            surface,
            "PRESS ESC TO RETURN",
            footer_y,
            ArcadeTextColor.ROSE,
            scale=self.FOOTER_SCALE,
        )

    def _value_width(
        self,
        text: ArcadeTextRenderer,
        label: str,
        value: str,
    ) -> int:
        """Return pixel width of a row's value column content."""
        scale = self.ROW_SCALE
        if label == "SPEED":
            plus = plus_glyph(ArcadeTextRenderer.WHITE_RGBA, scale)
            suffix = text.render(value, ArcadeTextColor.WHITE, scale)
            return plus.get_width() + suffix.get_width()
        return text.render(value, ArcadeTextColor.WHITE, scale).get_width()

    def _table_layout(
        self,
        surface: Surface,
        text: ArcadeTextRenderer,
        rows: tuple[tuple[str, str], ...],
    ) -> tuple[int, int, int]:
        """Compute shared label edge and value start for aligned columns."""
        scale = self.ROW_SCALE
        advance = text.advance(scale)
        label_width = self.LABEL_CHARS * advance
        gap_width = self.GAP_CHARS * advance
        max_value_width = max(
            self._value_width(text, label, value) for label, value in rows
        )
        block_width = label_width + gap_width + max_value_width
        left = (surface.get_width() - block_width) // 2
        label_right = left + label_width
        value_left = label_right + gap_width
        return label_right, value_left, scale

    def _shifted_layout(
        self,
        layout: tuple[int, int, int],
        shift_x: int,
    ) -> tuple[int, int, int]:
        """Return table layout shifted horizontally."""
        label_right, value_left, scale = layout
        return label_right + shift_x, value_left + shift_x, scale

    def _draw_rows(
        self,
        surface: Surface,
        text: ArcadeTextRenderer,
        rows: tuple[tuple[str, str], ...],
        start_y: int,
        row_step: int,
        layout: tuple[int, int, int],
    ) -> int:
        """Draw label/value rows and return y below the last row."""
        label_right, value_left, scale = layout
        y = start_y
        for label, value in rows:
            if label == "SPEED":
                self._draw_speed_row(
                    surface, text, label, value, y, label_right, value_left
                )
            else:
                self._draw_row(
                    surface,
                    text,
                    label,
                    value,
                    y,
                    label_right,
                    value_left,
                    scale,
                )
            y += row_step
        return y

    def _draw_row(
        self,
        surface: Surface,
        text: ArcadeTextRenderer,
        label: str,
        value: str,
        y: int,
        label_right: int,
        value_left: int,
        scale: int,
    ) -> None:
        """Draw one aligned label/value row."""
        label_surface = text.render(label, ArcadeTextColor.WHITE, scale)
        value_surface = text.render(value, ArcadeTextColor.WHITE, scale)
        label_rect = label_surface.get_rect(midright=(label_right, y))
        value_rect = value_surface.get_rect(midleft=(value_left, y))
        surface.blit(label_surface, label_rect)
        surface.blit(value_surface, value_rect)

    def _draw_speed_row(
        self,
        surface: Surface,
        text: ArcadeTextRenderer,
        label: str,
        suffix_text: str,
        y: int,
        label_right: int,
        value_left: int,
    ) -> None:
        """Draw SPEED row with a drawn plus glyph instead of '+' text."""
        scale = self.ROW_SCALE
        plus = plus_glyph(ArcadeTextRenderer.WHITE_RGBA, scale)
        suffix = text.render(suffix_text, ArcadeTextColor.WHITE, scale)
        label_surface = text.render(label, ArcadeTextColor.WHITE, scale)
        label_rect = label_surface.get_rect(midright=(label_right, y))
        plus_rect = plus.get_rect(midleft=(value_left, y))
        suffix_rect = suffix.get_rect(midleft=(plus_rect.right, y))
        surface.blit(label_surface, label_rect)
        surface.blit(plus, plus_rect)
        surface.blit(suffix, suffix_rect)
