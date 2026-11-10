"""Self-check: ``python -m worktracker.tools.doctor`` tells you exactly what is missing before you start the app."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path


def _ok(flag: bool, text: str) -> bool:
    print(("  [OK]   " if flag else "  [FAIL] ") + text)
    return flag


def main() -> int:
    ok = True
    print("WorkTracker doctor\n")
    ok &= _ok(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]} (needs 3.10+)")
    qt = importlib.util.find_spec("PyQt5") is not None
    ok &= _ok(qt, "PyQt5 installed" + ("" if qt else "  ->  pip install PyQt5"))
    _ok(importlib.util.find_spec("PyQt5.QtMultimedia") is not None if qt else False, "QtMultimedia available (needed for sounds; the app still runs silently without it)")
    for mod, why in (("openpyxl", "Excel export"), ("reportlab", "PDF invoices"), ("cryptography", "encrypted backups")):
        _ok(importlib.util.find_spec(mod) is not None, f"{mod} (optional: {why})")
    here = Path(__file__).resolve().parents[1]
    from worktracker.ui import fonts
    dirs = fonts.candidate_dirs(here, extra=[Path(os.environ.get("WORKTRACKER_HOME", Path.home())) / "assets" / "fonts"])
    found = fonts.discover(dirs)
    names = [p.name for p in found]
    _ok(bool(found), f"font files found: {len(found)} {names[:6]}")
    _ok(any("iransans" in n.lower() for n in names), "IRANSans present" + ("" if any("iransans" in n.lower() for n in names) else f"  ->  copy your assets/fonts folder to: {dirs[0]}"))
    try:
        from worktracker.core.database import Database
        with tempfile.TemporaryDirectory() as d:
            db = Database(Path(d) / "t.db"); v = db.version; db.close()
        ok &= _ok(True, f"database engine works (schema v{v})")
    except Exception as exc:  # noqa: BLE001
        ok &= _ok(False, f"database failed: {exc}")
    free = shutil.disk_usage(Path.home()).free / 2 ** 30
    _ok(free > 1, f"free disk space: {free:.1f} GB")
    print("\n" + ("Everything needed is in place." if ok else "Fix the [FAIL] lines above, then run again."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
