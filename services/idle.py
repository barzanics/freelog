"""Real OS idle detection (seconds since last input). Returns 0 when unsupported."""
from __future__ import annotations

import logging
import subprocess
import sys

log = logging.getLogger("worktracker.idle")


def system_idle_seconds() -> int:
    """Seconds since the last keyboard/mouse input, using native APIs."""
    try:
        if sys.platform == "win32":
            import ctypes

            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(info)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):  # type: ignore[attr-defined]
                return 0
            tick = ctypes.windll.kernel32.GetTickCount()  # type: ignore[attr-defined]
            return max(0, int((tick - info.dwTime) & 0xFFFFFFFF) // 1000)
        if sys.platform == "darwin":
            out = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=2).stdout
            for line in out.splitlines():
                if "HIDIdleTime" in line:
                    return int(int(line.split("=")[-1].strip()) / 1_000_000_000)
            return 0
        out = subprocess.run(["xprintidle"], capture_output=True, text=True, timeout=2)
        return int(out.stdout.strip()) // 1000 if out.returncode == 0 else 0
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        log.debug("idle detection unavailable", exc_info=True)
        return 0
