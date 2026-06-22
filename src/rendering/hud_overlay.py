from __future__ import annotations

from pygame.surface import Surface

from game.game_session import GameplayPhase, HudSnapshot
from game.render_config import MazeViewport
from states.text import ArcadeFont, ArcadeTextColor


TOP_LABEL_Y = 8
TOP_VALUE_Y = 28
BOTTOM_MARGIN = 16
HUD_SCALE = 2
SIDE_MARGIN = 48
LIFE_ICON_GAP = 4
MESSAGE_SCALE = 3


class HudOverlay:
    """Classic Pac-Man-style persistent in-game HUD."""

    __slots__ = ("_font", "_label_cache", "_life_icon")

    def __init__(self, life_icon: Surface | None = None) -> None:
        self._font = ArcadeFont(ArcadeTextColor.WHITE, HUD_SCALE)
        self._label_cache: dict[str, Surface] = {}
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
            x=SIDE_MARGIN,
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
            x=surface.get_width() - SIDE_MARGIN,
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
        bottom_y = viewport.bottom + BOTTOM_MARGIN
        self._draw_life_icons(surface, snapshot.spare_lives, viewport.x, bottom_y)
        level_text = f"LEVEL {snapshot.level_number}"
        level_surface = self._font.render(level_text)
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
            label_rect = label_surface.get_rect(midtop=(x, TOP_LABEL_Y))
            value_rect = value_surface.get_rect(midtop=(x, TOP_VALUE_Y))
        elif right_aligned:
            label_rect = label_surface.get_rect(topright=(x, TOP_LABEL_Y))
            value_rect = value_surface.get_rect(topright=(x, TOP_VALUE_Y))
        else:
            label_rect = label_surface.get_rect(topleft=(x, TOP_LABEL_Y))
            value_rect = value_surface.get_rect(topleft=(x, TOP_VALUE_Y))

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
            x += self._life_icon.get_width() + LIFE_ICON_GAP

    def _draw_phase_message(
        self,
        surface: Surface,
        snapshot: HudSnapshot,
        viewport: MazeViewport,
    ) -> None:
        """Draw centered phase overlay over the maze."""
        if snapshot.message is None:
            return
        color = _message_color(snapshot.phase)
        rendered = ArcadeFont(color, MESSAGE_SCALE).render(snapshot.message)
        rect = rendered.get_rect(center=viewport.center)
        surface.blit(rendered, rect)

    def _cached_label(self, label: str) -> Surface:
        """Return cached static label surface."""
        cached = self._label_cache.get(label)
        if cached is not None:
            return cached
        rendered = self._font.render(label)
        self._label_cache[label] = rendered
        return rendered


def _format_score(score: int) -> str:
    """Format score as six-digit zero-padded string."""
    return f"{max(0, score):06d}"


def _format_time(remaining_s: int) -> str:
    """Format remaining seconds as three-digit zero-padded string."""
    return f"{max(0, remaining_s):03d}"


def _message_color(phase: GameplayPhase) -> ArcadeTextColor:
    """Return arcade color for a phase overlay message."""
    if phase == GameplayPhase.GAME_OVER:
        return ArcadeTextColor.RED
    if phase in (GameplayPhase.READY, GameplayPhase.LEVEL_COMPLETE):
        return ArcadeTextColor.YELLOW
    if phase == GameplayPhase.VICTORY:
        return ArcadeTextColor.GOLD
    return ArcadeTextColor.WHITE
