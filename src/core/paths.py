"""
Resolve read-only resources and writable data paths.
"""

import sys
from pathlib import Path


def is_frozen_build() -> bool:
    """Return whether the game runs from a PyInstaller package.

    Returns:
        True when ``sys.frozen`` is set by the PyInstaller bootloader.
    """
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Return the directory that contains bundled read-only assets.

    Returns:
        ``sys._MEIPASS`` when running as a PyInstaller executable;
        otherwise the project root (two levels above ``src/core/paths.py``).
    """
    if is_frozen_build():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Return the directory for writable user files such as highscores.

    Returns:
        The directory containing the executable when frozen;
        otherwise the project root (two levels above ``src/core/paths.py``).
    """
    if is_frozen_build():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]
