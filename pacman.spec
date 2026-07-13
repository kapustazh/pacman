# Pac-Man release build for itch.io.
#
#   make build-itch    → dist/pac-man/
#   make package-itch  → dist/pac-man-linux.zip
#
# PyInstaller runs in 4 steps:
#   1. Analysis  — scan pac-man.py and collect code + dependencies
#   2. PYZ         — pack Python modules into an archive
#   3. EXE         — create the launcher binary (pac-man)
#   4. COLLECT     — put exe, libraries, and assets into one folder

from pathlib import Path

# --- things you might change ---
ROOT = Path(SPECPATH)
APP_NAME = "pac-man"
ENTRY_POINT = "pac-man.py"
ICON = ROOT / "assets" / "icon" / "image.png"

# --- 1. Analysis ---
a = Analysis(
    [ENTRY_POINT],
    pathex=[str(ROOT), str(ROOT / "src")],
    datas=[(str(ROOT / "assets"), "assets")],
    hiddenimports=["pygame", "mazegenerator"],
)

# --- 2. PYZ ---
pyz = PYZ(a.pure, a.zipped_data)

# --- 3. EXE ---
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
    icon=str(ICON),
)

# --- 4. COLLECT ---
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=APP_NAME,
)
