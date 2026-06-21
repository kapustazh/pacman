from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorldRenderConfig:
    """Pixel scale for grid-to-surface conversion."""

    tile_px: int = 16


DEFAULT_RENDER_CONFIG = WorldRenderConfig()
