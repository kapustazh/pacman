from pathlib import Path
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from pygame.surface import Surface  # noqa: E402
import pygame  # noqa: E402


class AssetError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Asset loading error: {detail}")


class Assets:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> None:
        assets_root = self.root

        def load_image(*parts: str) -> Surface:
            return pygame.image.load(
                assets_root.joinpath(*parts)
            ).convert_alpha()

        try:
            print("Loading assets...")
        except FileNotFoundError as e:
            raise AssetError(f"File not found: {e}")

        self._prepare_sprites()

    def _prepare_sprites(self) -> None:
        """Scale, slice, and post-process sprites"""
        pass
