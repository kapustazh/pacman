from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pygame.surface import Surface

from core.resources import ResourceManager

if TYPE_CHECKING:
    from core.scene_manager import SceneManager


@dataclass(frozen=True, slots=True)
class GameContext:
    """Shared runtime services passed into states."""

    screen: Surface
    resources: ResourceManager
    scene_manager: SceneManager
