from __future__ import annotations

from typing import ClassVar

from pygame.surface import Surface

from game.game_session import GameplayPhase, HudSnapshot
from game.render_config import MazeViewport
from states.text import ArcadeTextColor, ArcadeTextRenderer


class HudOverlay:
    """Classic Pac-Man-style persistent in-game HUD."""

    TOP_LABEL_Y: ClassVar[int] = 8
    TOP_VALUE_Y: ClassVar[int] = 28
    BOTTOM_MARGIN: ClassVar[int] = 16
    HUD_SCALE: ClassVar[int] = 2
    SIDE_MARGIN: ClassVar[int] = 48
    LIFE_ICON_GAP: ClassVar[int] = 4
    MESSAGE_SCALE: ClassVar[int] = 3
    PHASE_TEXT_COLOR: ClassVar[dict[GameplayPhase, ArcadeTextColor]] = {
        GameplayPhase.GAME_OVER: ArcadeTextColor.RED,
        GameplayPhase.READY: ArcadeTextColor.YELLOW,
        GameplayPhase.LEVEL_COMPLETE: ArcadeTextColor.YELLOW,
        GameplayPhase.VICTORY: ArcadeTextColor.GOLD,
    }

    __slots__ = (
        "_font",
        "_label_cache",
        "_level_surface_cache",
        "_life_icon",
        "_phase_message_cache",
        "_text",
    )

    def __init__(
        self,
        text: ArcadeTextRenderer,
        life_icon: Surface | None = None,
    ) -> None:
        self._text = text
        self._font = text.font(ArcadeTextColor.WHITE, self.HUD_SCALE)
        self._label_cache: dict[str, Surface] = {}
        self._phase_message_cache: dict[GameplayPhase, Surface] = {}
        self._level_surface_cache: dict[int, Surface] = {}
        self._life_icon = life_icon

    def draw(
        self,
        surface: Surface,
        snapshot: HudSnapshot,
        viewport: MazeViewport,
    ) -> None:
        """Draw top score band, bottom status band, and phase message."""
        self._draw_top_band(surface, snapshot)
        self._draw_bottom_band(surface, snapshot, viewport)
        if snapshot.message is not None:
            self._draw_phase_message(surface, snapshot, viewport)

    def _draw_top_band(self, surface: Surface, snapshot: HudSnapshot) -> None:
        """Draw 1UP, HIGH SCORE, and TIME across the top."""
        self._draw_score_column(
            surface,
            x=self.SIDE_MARGIN,
            label="1UP",
            value=_format_score(snapshot.score),
        )
        self._draw_score_column(
            surface,
            x=surface.get_width() // 2,
            label="HIGH SCORE",
            value=_format_score(snapshot.high_score),
            centered=True,
        )
        self._draw_score_column(
            surface,
            x=surface.get_width() - self.SIDE_MARGIN,
            label="TIME",
            value=_format_time(snapshot.remaining_time_s),
            right_aligned=True,
        )

    def _draw_bottom_band(
        self,
        surface: Surface,
        snapshot: HudSnapshot,
        viewport: MazeViewport,
    ) -> None:
        """Draw spare life icons and current level below the maze."""
        bottom_y = viewport.bottom + self.BOTTOM_MARGIN
        self._draw_life_icons(
            surface, snapshot.spare_lives, viewport.x, bottom_y
        )
        level_surface = self._cached_level_surface(snapshot.level_number)
        level_rect = level_surface.get_rect(
            midright=(viewport.x + viewport.width, bottom_y),
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
        label_surface = self._cached_label(label)
        value_surface = self._font.render_uncached(value)

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
        snapshot: HudSnapshot,
        viewport: MazeViewport,
    ) -> None:
        """Draw centered phase overlay over the maze."""
        if snapshot.message is None:
            return
        rendered = self._cached_phase_message(snapshot.phase, snapshot.message)
        rect = rendered.get_rect(center=viewport.center)
        surface.blit(rendered, rect)

    def _cached_label(self, label: str) -> Surface:
        """Return cached static label surface."""
        cached = self._label_cache.get(label)
        if cached is not None:
            return cached
        rendered: Surface = self._font.render(label)
        self._label_cache[label] = rendered
        return rendered

    def _cached_phase_message(
        self,
        phase: GameplayPhase,
        message: str,
    ) -> Surface:
        """Return cached phase overlay text surface."""
        cached = self._phase_message_cache.get(phase)
        if cached is not None:
            return cached
        color = self.PHASE_TEXT_COLOR.get(phase, ArcadeTextColor.WHITE)
        rendered = self._text.font(color, self.MESSAGE_SCALE).render(message)
        self._phase_message_cache[phase] = rendered
        return rendered

    def _cached_level_surface(self, level_number: int) -> Surface:
        """Return cached level label surface."""
        cached = self._level_surface_cache.get(level_number)
        if cached is not None:
            return cached
        rendered = self._font.render(f"LEVEL {level_number}")
        self._level_surface_cache[level_number] = rendered
        return rendered


def _format_score(score: int) -> str:
    """Format score as six-digit zero-padded string."""
    return f"{max(0, score):06d}"


def _format_time(remaining_s: int) -> str:
    """Format remaining seconds as three-digit zero-padded string."""
    return f"{max(0, remaining_s):03d}"
