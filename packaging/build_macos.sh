#!/usr/bin/env bash
# Run on macOS from the folder that CONTAINS worktracker/.
set -euo pipefail
python3 -m pip install pyinstaller PyQt5 openpyxl reportlab cryptography tzdata
python3 -m PyInstaller --noconfirm --clean --windowed --name WorkTracker --paths . worktracker/main.py
hdiutil create -volname WorkTracker -srcfolder dist/WorkTracker.app -ov -format UDZO dist/WorkTracker.dmg
