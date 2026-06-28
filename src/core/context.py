from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pygame.surface import Surface

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
