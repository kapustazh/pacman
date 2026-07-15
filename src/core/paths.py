"""
Resolve read-only resources and writable data paths.
"""

import sys
from pathlib import Path


def resource_root() -> Path:
    """Return the directory that contains bundled read-only assets.

    Returns:
        ``sys._MEIPASS`` when running as a PyInstaller executable;
        otherwise the project root (two levels above ``src/core/paths.py``).
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Return the directory for writable user files such as highscores.

    Returns:
        The directory containing the executable when frozen;
        otherwise the project root (two levels above ``src/core/paths.py``).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]
