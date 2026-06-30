from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pygame.surface import Surface

from managers.highscore_manager import HighscoreManager
from sprites.assets import Assets
from states.text import ArcadeTextRenderer

if TYPE_CHECKING:
    from core.scene_manager import SceneManager


@dataclass(frozen=True, slots=True)
class GameContext:
    """Shared runtime services passed into states."""

    screen: Surface
    assets: Assets
    text: ArcadeTextRenderer
    scene_manager: SceneManager
    highscores: HighscoreManager
    config: dict[str, Any]
