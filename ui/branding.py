"""Product identity: name, author, company, the logo, the application icon and the Windows taskbar identity.

Windows groups taskbar buttons and picks their icon by the *AppUserModelID*; without one it shows the icon of ``python.exe``. ``set_windows_app_id`` must run before the first
window exists. ``app_icon`` loads every size from ``assets`` (the .ico / .png files made from the FreeLog logo) so the taskbar, title bar, Alt-Tab, tray and shortcuts all show it.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

APP_NAME = "FreeLog"
ORGANIZATION = "barzanics"
AUTHOR = "Amirhossein Barzegar"
AUTHOR_FA = "امیرحسین برزگر"
APP_ID = "barzanics.FreeLog"
TAGLINE = "Track time. Own your work. Impress your clients."
TAGLINE_FA = "زمانت را ثبت کن، کارت را در اختیار بگیر، کلاینتت را شگفت‌زده کن."
LOGO_NAMES = ("freelog.png", "icons/freelog_512.png", "icons/freelog_256.png")
log = logging.getLogger("worktracker.branding")


def asset_dirs(extra: Optional[List[Path]] = None) -> List[Path]:
    here = Path(__file__).resolve().parents[1]
    return [*(extra or []), here / "assets", here.parent / "assets", Path.cwd() / "assets"]


def find_asset(name: str, extra: Optional[List[Path]] = None) -> Optional[Path]:
    for d in asset_dirs(extra):
        p = d / name
        if p.exists():
            return p
    return None


def logo_path(extra: Optional[List[Path]] = None) -> Optional[Path]:
    for n in LOGO_NAMES:
        p = find_asset(n, extra)
        if p:
            return p
    return None


def ico_path(extra: Optional[List[Path]] = None) -> Optional[Path]:
    return find_asset("freelog.ico", extra)


def set_windows_app_id() -> bool:
    """Give the process its own identity so the taskbar shows FreeLog's icon and groups its windows. No-op on other systems. Call BEFORE creating QApplication."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        return True
    except Exception:  # noqa: BLE001 - cosmetic
        log.info("could not set the AppUserModelID", exc_info=True)
        return False


def app_icon(extra: Optional[List[Path]] = None):
    """QIcon with all sizes (16..512). Falls back to the single logo file, then to an empty icon (never raises)."""
    from PyQt5.QtGui import QIcon
    icon = QIcon()
    for d in asset_dirs(extra):
        found = False
        for n in (16, 24, 32, 48, 64, 128, 256, 512):
            p = d / "icons" / f"freelog_{n}.png"
            if p.exists():
                icon.addFile(str(p)); found = True
        if found:
            return icon
    p = logo_path(extra)
    if p:
        icon.addFile(str(p))
    return icon


def apply(app, extra: Optional[List[Path]] = None):
    """Name the application, set its organisation and icon. Returns the icon."""
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    app.setOrganizationDomain("barzanics.com")
    if hasattr(app, "setDesktopFileName"):
        app.setDesktopFileName("freelog")
    icon = app_icon(extra)
    app.setWindowIcon(icon)
    return icon
