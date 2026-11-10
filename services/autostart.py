"""Start with the OS. Creates parent directories first (fixes the v5 bug). ``home`` is injectable for tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Union

NAME = "WorkTracker"


def command() -> str:
    return f'"{sys.executable}" -m worktracker.main'


def _linux(home: Path) -> Path:
    return home / ".config" / "autostart" / "worktracker.desktop"


def _mac(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / "com.worktracker.plist"


def enable(home: Optional[Union[str, Path]] = None, platform: Optional[str] = None, cmd: Optional[str] = None) -> Optional[Path]:
    """Enable autostart; returns the created file (None on Windows where the registry is used)."""
    plat, home, cmd = platform or sys.platform, Path(home or Path.home()), cmd or command()
    if plat == "win32":
        import winreg  # type: ignore[import-not-found]  # pragma: no cover
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:  # pragma: no cover
            winreg.SetValueEx(k, NAME, 0, winreg.REG_SZ, cmd)  # pragma: no cover
        return None  # pragma: no cover
    if plat == "darwin":
        f = _mac(home)
        body = (f'<?xml version="1.0" encoding="UTF-8"?>\n<plist version="1.0"><dict><key>Label</key><string>com.worktracker</string>'
                f'<key>ProgramArguments</key><array><string>/bin/sh</string><string>-c</string><string>{cmd.replace("&", "&amp;")}</string></array>'
                f'<key>RunAtLoad</key><true/></dict></plist>\n')
    else:
        f = _linux(home)
        body = f"[Desktop Entry]\nType=Application\nName={NAME}\nExec={cmd}\nX-GNOME-Autostart-enabled=true\n"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body, encoding="utf-8")
    return f


def disable(home: Optional[Union[str, Path]] = None, platform: Optional[str] = None) -> bool:
    plat, home = platform or sys.platform, Path(home or Path.home())
    if plat == "win32":
        import winreg  # type: ignore[import-not-found]  # pragma: no cover
        try:  # pragma: no cover
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, NAME)
            return True
        except OSError:  # pragma: no cover
            return False
    f = _mac(home) if plat == "darwin" else _linux(home)
    if f.exists():
        f.unlink()
        return True
    return False


def is_enabled(home: Optional[Union[str, Path]] = None, platform: Optional[str] = None) -> bool:
    plat, home = platform or sys.platform, Path(home or Path.home())
    if plat == "win32":
        return False  # pragma: no cover
    return (_mac(home) if plat == "darwin" else _linux(home)).exists()
