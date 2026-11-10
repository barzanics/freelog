"""Global hotkey. ``parse_hotkey`` is portable and tested; ``WindowsHotkey`` uses RegisterHotKey (Windows only, needs on-device test)."""
from __future__ import annotations

import sys
import threading
from typing import Callable, Optional, Tuple

MODS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
_SPECIAL = {"space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B}


def parse_hotkey(text: str) -> Tuple[int, int]:
    """``"Ctrl+Shift+Space"`` -> (modifier_mask, virtual_key)."""
    parts = [p.strip().lower() for p in text.split("+") if p.strip()]
    if len(parts) < 2:
        raise ValueError("need at least one modifier and a key")
    mods = 0
    for m in parts[:-1]:
        if m not in MODS:
            raise ValueError(f"unknown modifier {m!r}")
        mods |= MODS[m]
    key = parts[-1]
    if key in _SPECIAL:
        vk = _SPECIAL[key]
    elif len(key) == 1 and key.isalnum():
        vk = ord(key.upper())
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x6F + int(key[1:])
    else:
        raise ValueError(f"unknown key {key!r}")
    return mods, vk


class WindowsHotkey:
    """Runs a message loop in a daemon thread; ``callback`` is invoked from that thread (marshal to Qt with a signal)."""

    def __init__(self, text: str, callback: Callable[[], None]) -> None:
        self.mods, self.vk = parse_hotkey(text)
        self.callback = callback
        self._thread: Optional[threading.Thread] = None
        self._tid = 0
        self.ok = threading.Event()
        self.registered = False

    def start(self) -> bool:
        if sys.platform != "win32":
            return False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.ok.wait(2)
        return self.registered

    def _loop(self) -> None:  # pragma: no cover - Windows only
        import ctypes
        from ctypes import wintypes
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        self._tid = k32.GetCurrentThreadId()
        self.registered = bool(u32.RegisterHotKey(None, 1, self.mods | 0x4000, self.vk))  # MOD_NOREPEAT
        self.ok.set()
        msg = wintypes.MSG()
        while self.registered and u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:       # WM_HOTKEY
                self.callback()
        if self.registered:
            u32.UnregisterHotKey(None, 1)

    def stop(self) -> None:  # pragma: no cover - Windows only
        if self.registered and sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)   # WM_QUIT
            self.registered = False
