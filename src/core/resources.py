from __future__ import annotations

from typing import Protocol, cast

from sprites.assets import Assets, ItemSprites, MazeSprites
from sprites.sprites import AnimatedSprite, AssetSprite
from sprites.sprite_types import Direction, FruitKind
from states.text import ArcadeTextRenderer


class AssetCatalog(Protocol):
    """Read-only asset surface required by entity factories."""

    pacman: dict[Direction, AnimatedSprite]
    items: ItemSprites
    # TODO: populated after Assets.load_fruits() when fruit entities land.
    fruits: dict[FruitKind, AssetSprite]
    maze: MazeSprites


class ResourceManager(Protocol):
    """Global resource access interface."""

    def load_all(self) -> None:
        """Load all required resources once."""

    def get_asset_catalog(self) -> AssetCatalog:
        """Return loaded assets through a narrow catalog interface."""

    def get_text_renderer(self) -> ArcadeTextRenderer:
        """Return arcade text renderer for UI drawing."""


class AssetsResourceManager:
    """Resource manager backed by the existing Assets loader."""

    __slots__ = ("_assets", "_text_renderer")

    def __init__(
        self,
        assets: Assets,
        text_renderer: ArcadeTextRenderer | None = None,
    ) -> None:
        self._assets = assets
        self._text_renderer = text_renderer or ArcadeTextRenderer()

    def load_all(self) -> None:
        """Load all sprites and text once."""
        self._assets.load()
        self._text_renderer.preload()

    def get_asset_catalog(self) -> AssetCatalog:
        """Return loaded sprite catalog."""
        return cast(AssetCatalog, self._assets)

    def get_text_renderer(self) -> ArcadeTextRenderer:
        """Return arcade text renderer."""
        return self._text_renderer
