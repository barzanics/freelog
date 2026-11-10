"""Entry point. Fully offline: no network call is made at startup.

Fonts: put IRANSans (any ``*.ttf`` / ``*.otf``) in ``assets/fonts`` next to this folder, next to the app or in the data folder;
icons can be overridden the same way with ``assets/icons/<name>.svg|png``.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # allow `python worktracker/main.py`


def data_dir() -> Path:
    base = os.environ.get("WORKTRACKER_HOME")
    if base:
        return Path(base)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "WorkTracker"
    return Path.home() / ".local" / "share" / "worktracker"


def main() -> int:
    home = data_dir()
    (home / "logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(home / "logs" / "app.log", maxBytes=500_000, backupCount=2, encoding="utf-8")],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("worktracker.main")

    def _excepthook(etype, value, tb) -> None:
        """PyQt5 aborts the whole process on an unhandled exception inside a slot; log it instead and keep the app alive."""
        log.error("unhandled exception", exc_info=(etype, value, tb))
    sys.excepthook = _excepthook
    try:
        from worktracker.core import recovery
        used = recovery.recover(home / "worktracker.db", home / "backups")      # corrupt database -> newest healthy backup
        if used:
            log.warning("database restored from %s", used)
    except Exception:  # noqa: BLE001 - never block startup on the safety net
        log.exception("recovery check failed")

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from worktracker.core.database import Database
    from worktracker.ui import fonts, icons
    from worktracker.ui.app import App

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    db = Database(home / "worktracker.db")
    app.setLayoutDirection(Qt.RightToLeft if db.get_setting("lang", "fa") == "fa" else Qt.LeftToRight)

    here = Path(__file__).resolve().parent
    info = fonts.load(here, extra=[home / "assets" / "fonts"])
    fonts.apply_app_font(app, info, 10)
    if info.missing_message():
        log.warning(info.missing_message())
    icons.set_override_dirs([here / "assets" / "icons", here.parent / "assets" / "icons", home / "assets" / "icons"])

    win = App(db, home, info)
    win.show()
    code = app.exec_()
    db.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
