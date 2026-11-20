"""Desktop / Start-menu shortcuts that carry the FreeLog icon (created once, on first run; switch off with the setting ``create_shortcuts``).

Windows: .lnk on the Desktop and in the Start menu, started with ``pythonw`` (no console window) and ``assets/freelog.ico``.
Linux: a ``.desktop`` launcher in the applications menu (and on the Desktop when that folder exists).  macOS: a double-clickable ``FreeLog.command`` on the Desktop.
The text of every launcher is built by a pure function so it is unit-tested; only the final write / PowerShell call touches the system.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional

log = logging.getLogger("worktracker.shortcuts")
NAME = "FreeLog"
COMMENT = "Track time, manage tasks and send professional client reports"


def _pythonw(python: str) -> str:
    p = Path(python)
    w = p.with_name("pythonw.exe")
    return str(w) if p.name.lower() == "python.exe" and w.exists() else python


def desktop_entry(root: Path, python: str = "python3") -> str:
    """Freedesktop launcher. ``Exec`` quotes the interpreter so a path with spaces works."""
    icon = root / "assets" / "icons" / "freelog_256.png"
    return ("[Desktop Entry]\nType=Application\nVersion=1.0\n" f"Name={NAME}\nComment={COMMENT}\nExec=\"{python}\" -m worktracker.main\nPath={root}\nIcon={icon}\n"
            "Terminal=false\nCategories=Office;ProjectManagement;Utility;\nStartupWMClass=freelog\nStartupNotify=true\n")


def _ps_quote(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def powershell_script(root: Path, python: str) -> str:
    """Creates the Desktop and Start-menu .lnk files (single-quoted PowerShell strings; embedded quotes are doubled)."""
    icon = root / "assets" / "freelog.ico"
    return "\n".join([
        "$ErrorActionPreference = 'Stop'", "$sh = New-Object -ComObject WScript.Shell",
        f"$targets = @([Environment]::GetFolderPath('Desktop'), (Join-Path ([Environment]::GetFolderPath('Programs')) ''))",
        "foreach ($dir in $targets) {", f"  $lnk = $sh.CreateShortcut((Join-Path $dir '{NAME}.lnk'))", f"  $lnk.TargetPath = {_ps_quote(_pythonw(python))}", "  $lnk.Arguments = '-m worktracker.main'",
        f"  $lnk.WorkingDirectory = {_ps_quote(root)}", f"  $lnk.IconLocation = {_ps_quote(str(icon) + ',0')}", f"  $lnk.Description = {_ps_quote(COMMENT)}", "  $lnk.Save()", "}"])


def create_shortcuts(root: Path, python: Optional[str] = None, platform: str = sys.platform, home: Optional[Path] = None,
                     runner: Callable[..., object] = subprocess.run) -> List[str]:
    """Create the launchers for this system. Returns what was written (empty when nothing could be)."""
    python = python or sys.executable
    home = home or Path.home()
    made: List[str] = []
    try:
        if platform == "win32":
            runner(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script(root, python)], check=True, timeout=30, capture_output=True)
            made += ["Desktop", "Start menu"]
        elif platform.startswith("linux"):
            apps = home / ".local" / "share" / "applications"
            apps.mkdir(parents=True, exist_ok=True)
            entry = desktop_entry(root, python)
            (apps / "freelog.desktop").write_text(entry, encoding="utf-8"); made.append(str(apps / "freelog.desktop"))
            desk = home / "Desktop"
            if desk.is_dir():
                f = desk / "FreeLog.desktop"
                f.write_text(entry, encoding="utf-8"); f.chmod(0o755); made.append(str(f))
        elif platform == "darwin":
            desk = home / "Desktop"
            if desk.is_dir():
                f = desk / "FreeLog.command"
                f.write_text(f"#!/bin/bash\ncd \"{root}\" && \"{python}\" -m worktracker.main\n", encoding="utf-8"); f.chmod(0o755); made.append(str(f))
    except Exception:  # noqa: BLE001 - shortcuts are a convenience, never a startup failure
        log.warning("could not create shortcuts", exc_info=True)
    return made


def ensure_shortcuts(db, root: Path, **kw) -> bool:
    """Once per installation: create the shortcuts unless the user turned it off. Returns True when it ran."""
    if not db.get_setting("create_shortcuts", True) or db.get_setting("shortcuts_created", False):
        return False
    made = create_shortcuts(root, **kw)
    if made:
        db.set_setting("shortcuts_created", True)
    return bool(made)
