from __future__ import annotations

from typing import Protocol

from sprites.assets import Assets, ItemSprites, MazeSprites
from sprites.sprites import AnimatedSprite, AssetSprite
from sprites.types import Direction, FruitKind


class AssetCatalog(Protocol):
    """Read-only asset surface required by entity factories."""

    pacman: dict[Direction, AnimatedSprite]
    items: ItemSprites
    fruits: dict[FruitKind, AssetSprite]
    maze: MazeSprites


class ResourceManager(Protocol):
    """Global resource access interface."""

    def load_all(self) -> None:
        """Load all required resources once."""

    def get_asset_catalog(self) -> AssetCatalog:
        """Return loaded assets through a narrow catalog interface."""


class AssetsResourceManager:
    """Resource manager backed by the existing Assets loader."""

    __slots__ = ("_assets",)

    def __init__(self, assets: Assets) -> None:
        self._assets = assets

    def load_all(self) -> None:
        """Load all sprites once."""
        self._assets.load()

    def get_asset_catalog(self) -> AssetCatalog:
        """Return loaded sprite catalog."""
        return self._assets
