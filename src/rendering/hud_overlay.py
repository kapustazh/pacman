from __future__ import annotations

from typing import ClassVar

from pygame.surface import Surface

from game.game_session import GameSession, GameplayPhase
from game.game_world import ScorePopup
from game.render_config import MazeBounds
from states.text import ArcadeTextColor, ArcadeTextFont, ArcadeTextRenderer


class HudOverlay:
    """Classic Pac-Man-style persistent in-game HUD."""

    TOP_LABEL_Y: ClassVar[int] = 8
    TOP_VALUE_Y: ClassVar[int] = 28
    BOTTOM_EDGE: ClassVar[int] = 16
    HUD_SCALE: ClassVar[int] = 2
    SIDE_MARGIN: ClassVar[int] = 48
    LIFE_ICON_GAP: ClassVar[int] = 4
    MESSAGE_SCALE: ClassVar[int] = 3
    SCORE_POPUP_SCALE: ClassVar[int] = 1
    STATIC_LABELS: ClassVar[tuple[str, ...]] = ("1UP", "HIGH SCORE", "TIME")
    PHASE_TEXT_COLOR: ClassVar[dict[GameplayPhase, ArcadeTextColor]] = {
        GameplayPhase.GAME_OVER: ArcadeTextColor.RED,
        GameplayPhase.READY: ArcadeTextColor.YELLOW,
        GameplayPhase.LEVEL_COMPLETE: ArcadeTextColor.YELLOW,
    }

    __slots__ = (
        "_font",
        "_fruit_icon",
        "_label_surfaces",
        "_level_surface_cache",
        "_life_icon",
        "_phase_message_surfaces",
        "_text",
        "_value_surface_cache",
    )

    def __init__(
        self,
        text: ArcadeTextRenderer,
        life_icon: Surface | None = None,
        fruit_icon: Surface | None = None,
    ) -> None:
        self._text = text
        self._fruit_icon = fruit_icon
        self._font: ArcadeTextFont = text.font(
            ArcadeTextColor.WHITE, self.HUD_SCALE
        )
        self._label_surfaces = {
            label: self._font.render(label) for label in self.STATIC_LABELS
        }
        self._phase_message_surfaces: dict[GameplayPhase, Surface] = {}
        for phase, message in GameSession.PHASE_MESSAGE.items():
            if message is None:
                continue
            color = self.PHASE_TEXT_COLOR.get(phase, ArcadeTextColor.WHITE)
            self._phase_message_surfaces[phase] = text.font(
                color, self.MESSAGE_SCALE
            ).render(message)
        self._level_surface_cache: dict[int, Surface] = {}
        self._value_surface_cache: dict[str, Surface] = {}
        self._life_icon = life_icon

    def set_fruit_icon(self, fruit_icon: Surface | None) -> None:
        """Update HUD fruit preview for the active level."""
        self._fruit_icon = fruit_icon

    def draw_score_popups(
        self,
        surface: Surface,
        popups: tuple[ScorePopup, ...],
    ) -> None:
        """Draw floating point values where fruits were eaten."""
        if not popups:
            return
        font = self._text.font(
            ArcadeTextColor.WHITE, self.SCORE_POPUP_SCALE
        )
        for popup in popups:
            rendered = font.render(str(popup.points))
            rect = rendered.get_rect(midtop=popup.center)
            surface.blit(rendered, rect)

    def draw(
        self,
        surface: Surface,
        session: GameSession,
        maze_bounds: MazeBounds,
    ) -> None:
        """Draw top score band, bottom status band, and phase message."""
        self._draw_top_band(surface, session)
        self._draw_bottom_band(surface, session, maze_bounds)
        message = GameSession.PHASE_MESSAGE.get(session.phase)
        if message is not None:
            self._draw_phase_message(surface, session, maze_bounds, message)

    def _draw_top_band(self, surface: Surface, session: GameSession) -> None:
        """Draw 1UP, HIGH SCORE, and TIME across the top."""
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
        """Draw spare life icons and current level below the maze."""
        bottom_y = maze_bounds.bottom + self.BOTTOM_EDGE
        self._draw_life_icons(
            surface, session.spare_lives(), maze_bounds.x, bottom_y
        )
        if self._fruit_icon is not None:
            fruit_rect = self._fruit_icon.get_rect(
                midleft=(
                    maze_bounds.x + maze_bounds.width // 2 + 24,
                    bottom_y,
                ),
            )
            surface.blit(self._fruit_icon, fruit_rect)
        level_surface = self._cached_level_surface(session.level_number)
        level_rect = level_surface.get_rect(
            midright=(maze_bounds.x + maze_bounds.width, bottom_y),
        )
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
        """Draw one label/value HUD column."""
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
        spare_lives: int,
        x: int,
        y: int,
    ) -> None:
        """Draw one Pac-Man icon per spare life."""
        if self._life_icon is None or spare_lives <= 0:
            return

        icon_height = self._life_icon.get_height()
        icon_y = y - icon_height // 2
        for _ in range(spare_lives):
            surface.blit(self._life_icon, (x, icon_y))
            x += self._life_icon.get_width() + self.LIFE_ICON_GAP

    def _draw_phase_message(
        self,
        surface: Surface,
        session: GameSession,
        maze_bounds: MazeBounds,
        message: str,
    ) -> None:
        """Draw centered phase overlay over the maze."""
        rendered = self._phase_message_surfaces.get(session.phase)
        if rendered is None:
            return
        rect = rendered.get_rect(center=maze_bounds.center)
        surface.blit(rendered, rect)

    def _cached_level_surface(self, level_number: int) -> Surface:
        """Return cached level label surface."""
        cached = self._level_surface_cache.get(level_number)
        if cached is not None:
            return cached
        rendered = self._font.render(f"LEVEL {level_number}")
        self._level_surface_cache[level_number] = rendered
        return rendered

    def _cached_value_surface(self, value: str) -> Surface:
        """Return cached HUD value surface keyed by formatted string."""
        cached = self._value_surface_cache.get(value)
        if cached is not None:
            return cached
        rendered = self._font.render(value)
        self._value_surface_cache[value] = rendered
        return rendered


def _format_score(score: int) -> str:
    """Format score as six-digit zero-padded string."""
    return f"{max(0, score):06d}"


def _format_time(remaining_s: int) -> str:
    """Format remaining seconds as three-digit zero-padded string."""
    return f"{max(0, remaining_s):03d}"
