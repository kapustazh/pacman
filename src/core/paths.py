"""
Resolve read-only resources and writable data paths.
"""

import sys
from pathlib import Path


def resource_root() -> Path:
    """Project root in dev; PyInstaller extract dir when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Writable directory next to the executable, or project root in dev."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]
