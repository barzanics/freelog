#!/usr/bin/env bash
# Run from the folder that CONTAINS worktracker/.  Builds a one-folder app; AppImage/.deb steps are documented below (not run in CI here).
set -euo pipefail
python3 -m pip install pyinstaller PyQt5 openpyxl reportlab cryptography tzdata
python3 -m PyInstaller --noconfirm --clean --windowed --name WorkTracker --paths . worktracker/main.py
echo "Built dist/WorkTracker. For an AppImage: use appimagetool on an AppDir containing dist/WorkTracker + a .desktop file."
echo "For a .deb: use fpm -s dir -t deb -n worktracker -v 6.0.1 dist/WorkTracker=/opt/worktracker"
