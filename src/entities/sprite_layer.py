from enum import IntEnum, auto


# BOILERPLATE: central layer names for pygame.sprite.LayeredUpdates.
class SpriteLayer(IntEnum):
    """BOILERPLATE: z-order buckets for pygame LayeredUpdates."""

    BACKGROUND = auto()
    CONSUMABLES = auto()
    ACTORS = auto()
