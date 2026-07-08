# [transition UI] in-game HUD overlay.

from __future__ import annotations

from typing import ClassVar

from pygame.surface import Surface

from game.game_session import GameSession, GameplayPhase
from game.game_world import ScorePopup
from game.render_config import MazeBounds
from states.text import (
    ArcadeTextColor,
    ArcadeTextRenderer,
    plus_glyph,
)


class HudOverlay:
    """Draws the classic Pac-Man score band, lives, and phase messages."""

    TOP_LABEL_Y: ClassVar[int] = 8
    TOP_VALUE_Y: ClassVar[int] = 28
    BOTTOM_EDGE: ClassVar[int] = 16
    HUD_SCALE: ClassVar[int] = 2
    SIDE_MARGIN: ClassVar[int] = 48
    LIFE_ICON_GAP: ClassVar[int] = 4
    FRUIT_ICON_GAP: ClassVar[int] = 12
    MAX_LIFE_ICONS: ClassVar[int] = 3
    MESSAGE_SCALE: ClassVar[int] = 3
    SCORE_POPUP_SCALE: ClassVar[int] = 1
    STATIC_LABELS: ClassVar[tuple[str, ...]] = ("1UP", "HIGH SCORE", "TIME")
    PHASE_TEXT_COLOR: ClassVar[dict[GameplayPhase, ArcadeTextColor]] = {
        GameplayPhase.GAME_OVER: ArcadeTextColor.RED,
        GameplayPhase.READY: ArcadeTextColor.YELLOW,
        GameplayPhase.LEVEL_COMPLETE: ArcadeTextColor.YELLOW,
    }
    YELLOW: ClassVar[tuple[int, int, int, int]] = (255, 255, 0, 255)

    def __init__(
        self,
        text: ArcadeTextRenderer,
        life_icon: Surface | None = None,
        fruit_icon: Surface | None = None,
    ) -> None:
        """Prepare cached HUD text and optional life and fruit icons.

        Args:
            text: Renderer used for all HUD labels and values.
            life_icon: Optional Pac-Man icon drawn for spare lives.
            fruit_icon: Optional fruit preview for the current level.
        """
        self._text = text
        self._fruit_icon = fruit_icon
        self._label_surfaces: dict[str, Surface] = {
            label: text.render(label, scale=self.HUD_SCALE)
            for label in self.STATIC_LABELS
        }
        self._phase_message_surfaces: dict[GameplayPhase, Surface] = {}
        for phase, message in GameSession.PHASE_MESSAGE.items():
            if message is None:
                continue
            color = self.PHASE_TEXT_COLOR.get(phase, ArcadeTextColor.WHITE)
            self._phase_message_surfaces[phase] = text.render(
                message, color, self.MESSAGE_SCALE
            )
        self._level_surface_cache: dict[int, Surface] = {}
        self._value_surface_cache: dict[str, Surface] = {}
        self._life_icon = life_icon

    def set_fruit_icon(self, fruit_icon: Surface | None) -> None:
        """Replace the fruit icon shown beside the level number.

        Args:
            fruit_icon: New fruit surface, or None to hide the icon.
        """
        self._fruit_icon = fruit_icon

    def draw_score_popups(
        self,
        surface: Surface,
        popups: list[ScorePopup],
    ) -> None:
        """Draw floating point values where pellets or ghosts were eaten.

        Args:
            surface: Destination screen surface.
            popups: Active score popups with points and screen positions.
        """
        if not popups:
            return
        for popup in popups:
            rendered = self._text.render(
                str(popup.points), scale=self.SCORE_POPUP_SCALE
            )
            rect = rendered.get_rect(midtop=popup.center)
            surface.blit(rendered, rect)

    def draw(
        self,
        surface: Surface,
        session: GameSession,
        maze_bounds: MazeBounds,
    ) -> None:
        """Draw the full HUD around the active maze.

        Args:
            surface: Destination screen surface.
            session: Current score, lives, level, and gameplay phase.
            maze_bounds: Screen rectangle occupied by the maze.
        """
        self._draw_top_band(surface, session)
        self._draw_bottom_band(surface, session, maze_bounds)
        message = GameSession.PHASE_MESSAGE.get(session.phase)
        if message is not None:
            self._draw_phase_message(surface, session, maze_bounds, message)

    def _draw_top_band(self, surface: Surface, session: GameSession) -> None:
        """Draw 1UP, high score, and time across the top edge.

        Args:
            surface: Destination screen surface.
            session: Current score and timer state.
        """
        self._draw_score_column(
            surface,
            x=self.SIDE_MARGIN,
            label="1UP",
            value=_format_score(session.score),
        )
        self._draw_score_column(
            surface,
            x=surface.get_width() // 2,
            label="HIGH SCORE",
            value=_format_score(session.high_score),
            centered=True,
        )
        self._draw_score_column(
            surface,
            x=surface.get_width() - self.SIDE_MARGIN,
            label="TIME",
            value=_format_time(session.remaining_time_s()),
            right_aligned=True,
        )

    def _draw_bottom_band(
        self,
        surface: Surface,
        session: GameSession,
        maze_bounds: MazeBounds,
    ) -> None:
        """Draw spare lives, fruit icon, and level below the maze.

        Args:
            surface: Destination screen surface.
            session: Current lives and level number.
            maze_bounds: Screen rectangle occupied by the maze.
        """
        bottom_y = maze_bounds.bottom + self.BOTTOM_EDGE
        self._draw_life_icons(surface, session.lives, maze_bounds.x, bottom_y)
        level_surface = self._cached_level_surface(session.level_number)
        level_rect = level_surface.get_rect(
            midright=(maze_bounds.x + maze_bounds.width, bottom_y),
        )
        if self._fruit_icon is not None:
            fruit_rect = self._fruit_icon.get_rect(
                midright=(level_rect.left - self.FRUIT_ICON_GAP, bottom_y),
            )
            surface.blit(self._fruit_icon, fruit_rect)
        surface.blit(level_surface, level_rect)

    def _draw_score_column(
        self,
        surface: Surface,
        x: int,
        label: str,
        value: str,
        *,
        centered: bool = False,
        right_aligned: bool = False,
    ) -> None:
        """Draw one label and value column in the top HUD band.

        Args:
            surface: Destination screen surface.
            x: Horizontal anchor for the column.
            label: Static label text key, such as ``1UP``.
            value: Preformatted value string to display.
            centered: Anchor the column at ``x`` center.
            right_aligned: Anchor the column at ``x`` right edge.
        """
        label_surface = self._label_surfaces[label]
        value_surface = self._cached_value_surface(value)

        if centered:
            label_rect = label_surface.get_rect(midtop=(x, self.TOP_LABEL_Y))
            value_rect = value_surface.get_rect(midtop=(x, self.TOP_VALUE_Y))
        elif right_aligned:
            label_rect = label_surface.get_rect(topright=(x, self.TOP_LABEL_Y))
            value_rect = value_surface.get_rect(topright=(x, self.TOP_VALUE_Y))
        else:
            label_rect = label_surface.get_rect(topleft=(x, self.TOP_LABEL_Y))
            value_rect = value_surface.get_rect(topleft=(x, self.TOP_VALUE_Y))

        surface.blit(label_surface, label_rect)
        surface.blit(value_surface, value_rect)

    def _draw_life_icons(
        self,
        surface: Surface,
        lives: int,
        x: int,
        y: int,
    ) -> None:
        """Draw spare life icons, collapsing overflow into a plus counter.

        Args:
            surface: Destination screen surface.
            lives: Total lives remaining, including the active life.
            x: Left edge for the first icon.
            y: Vertical center for icons and overflow text.
        """
        if lives <= 0 or self._life_icon is None:
            return

        spare = max(0, lives - 1)
        icon_count = min(spare, self.MAX_LIFE_ICONS)
        icon_height = self._life_icon.get_height()
        icon_y = y - icon_height // 2
        for _ in range(icon_count):
            surface.blit(self._life_icon, (x, icon_y))
            x += self._life_icon.get_width() + self.LIFE_ICON_GAP

        if spare <= self.MAX_LIFE_ICONS:
            return

        gap = self.LIFE_ICON_GAP
        x += gap
        plus = plus_glyph(self.YELLOW, self.HUD_SCALE)
        plus_rect = plus.get_rect(midleft=(x, y))
        surface.blit(plus, plus_rect)
        count_surface = self._text.render(
            str(spare - self.MAX_LIFE_ICONS),
            ArcadeTextColor.YELLOW,
            self.HUD_SCALE,
        )
        count_rect = count_surface.get_rect(midleft=(plus_rect.right + gap, y))
        surface.blit(count_surface, count_rect)

    def _draw_phase_message(
        self,
        surface: Surface,
        session: GameSession,
        maze_bounds: MazeBounds,
        message: str,
    ) -> None:
        """Draw a centered phase overlay such as READY or GAME OVER.

        Args:
            surface: Destination screen surface.
            session: Current gameplay phase used to pick cached text.
            maze_bounds: Screen rectangle used to center the message.
            message: Phase message string; must match a cached phase entry.
        """
        rendered = self._phase_message_surfaces.get(session.phase)
        if rendered is None:
            return
        rect = rendered.get_rect(center=maze_bounds.center)
        surface.blit(rendered, rect)

    def _cached_level_surface(self, level_number: int) -> Surface:
        """Return a cached ``LEVEL N`` label surface.

        Args:
            level_number: Level index shown in the bottom HUD.

        Returns:
            Rendered level label surface.
        """
        cached = self._level_surface_cache.get(level_number)
        if cached is not None:
            return cached
        surface = self._text.render(
            f"LEVEL {level_number}", scale=self.HUD_SCALE
        )
        self._level_surface_cache[level_number] = surface
        return self._level_surface_cache[level_number]

    def _cached_value_surface(self, value: str) -> Surface:
        """Return a cached HUD value surface for a formatted string.

        Args:
            value: Preformatted score or time text.

        Returns:
            Rendered value surface.
        """
        cached = self._value_surface_cache.get(value)
        if cached is not None:
            return cached
        surface = self._text.render(value, scale=self.HUD_SCALE)
        self._value_surface_cache[value] = surface
        return self._value_surface_cache[value]


def _format_score(score: int) -> str:
    """Format a score as a six-digit zero-padded string.

    Args:
        score: Raw score value.

    Returns:
        Score string clamped to non-negative values.
    """
    return f"{max(0, score):06d}"


def _format_time(remaining_s: int) -> str:
    """Format remaining seconds as a three-digit zero-padded string.

    Args:
        remaining_s: Seconds left on the level timer.

    Returns:
        Timer string clamped to non-negative values.
    """
    return f"{max(0, remaining_s):03d}"
