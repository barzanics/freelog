"""Active-window capture -> activity events, app-usage analytics, task suggestions.

The foreground-window provider is injectable (tests) and OS-specific (Windows ctypes / macOS osascript / Linux xdotool).
Capture only runs when the user enables it and never leaves the machine.
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from collections import Counter
from typing import Callable, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import ActivityEvent
from ..core.persian import now_utc

CATEGORY_PATTERNS: List[Tuple[str, str]] = [
    (r"code|pycharm|idea|vim|studio|terminal|powershell|cmd|git", "development"),
    (r"figma|photoshop|illustrator|sketch|canva|blender", "design"),
    (r"zoom|teams|meet|skype|slack|telegram|discord", "communication"),
    (r"word|docs|notion|obsidian|excel|sheets|powerpoint|pdf", "documents"),
    (r"chrome|firefox|edge|safari|brave", "browsing"),
    (r"outlook|mail|thunderbird|gmail", "email"),
    (r"youtube|netflix|spotify|steam|game", "entertainment"),
]


def classify(app: str, title: str = "") -> str:
    for text in (app.lower(), title.lower()):       # the application wins; the title is only a fallback
        for pat, cat in CATEGORY_PATTERNS:
            if re.search(pat, text):
                return cat
    return "other"


def foreground_window() -> Optional[Tuple[str, str]]:
    """(app, title) of the focused window, or None when unavailable."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
            hwnd = u32.GetForegroundWindow()
            if not hwnd:
                return None
            buf = ctypes.create_unicode_buffer(512)
            u32.GetWindowTextW(hwnd, buf, 512)
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h = k32.OpenProcess(0x1000, False, pid.value)
            name = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)
            ok = k32.QueryFullProcessImageNameW(h, 0, name, ctypes.byref(size))
            k32.CloseHandle(h)
            return (name.value.rsplit("\\", 1)[-1] if ok else "unknown", buf.value)
        if sys.platform == "darwin":
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=2).stdout.strip()
            return (out, "") if out else None
        title = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=2).stdout.strip()
        pid = subprocess.run(["xdotool", "getactivewindow", "getwindowpid"], capture_output=True, text=True, timeout=2).stdout.strip()
        app = subprocess.run(["ps", "-p", pid, "-o", "comm="], capture_output=True, text=True, timeout=2).stdout.strip() if pid else ""
        return (app or "unknown", title) if title else None
    except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
        return None


class ActivityRecorder:
    """Call ``sample()`` every few seconds; consecutive samples of the same app are merged into one event."""

    def __init__(self, db: Database, provider: Callable[[], Optional[Tuple[str, str]]] = foreground_window,
                 clock: Callable[[], dt.datetime] = now_utc, idle: Callable[[], int] = lambda: 0, idle_limit: int = 120) -> None:
        self.db, self.provider, self.clock, self.idle, self.idle_limit = db, provider, clock, idle, idle_limit
        self._cur: Optional[ActivityEvent] = None

    def sample(self) -> Optional[ActivityEvent]:
        now = self.clock()
        if self.idle() >= self.idle_limit:
            self.flush()
            return None
        win = self.provider()
        if win is None:
            self.flush()
            return None
        app, title = win
        if self._cur and self._cur.app == app and (now - self._cur.end_utc) < dt.timedelta(minutes=2):
            self._cur.end_utc, self._cur.title = now, title
        else:
            self.flush()
            self._cur = ActivityEvent(app=app, title=title[:200], start_utc=now, end_utc=now, category=classify(app, title))
        return self._cur

    def flush(self) -> None:
        if self._cur and self._cur.seconds >= 5:
            self.db.save(self._cur)
        self._cur = None


def app_usage(db: Database, start: dt.datetime, end: dt.datetime) -> List[Tuple[str, int]]:
    """Seconds per app in [start, end), most used first."""
    c: Counter = Counter()
    for r in db.conn.execute("SELECT app, start_utc, end_utc FROM activity_events WHERE start_utc>=? AND start_utc<?",
                             (start.isoformat(), end.isoformat())):
        c[r[0]] += int((dt.datetime.fromisoformat(r[2]) - dt.datetime.fromisoformat(r[1])).total_seconds())
    return c.most_common()


def category_usage(db: Database, start: dt.datetime, end: dt.datetime) -> Dict[str, int]:
    c: Counter = Counter()
    for r in db.conn.execute("SELECT category, start_utc, end_utc FROM activity_events WHERE start_utc>=? AND start_utc<?",
                             (start.isoformat(), end.isoformat())):
        c[r[0]] += int((dt.datetime.fromisoformat(r[2]) - dt.datetime.fromisoformat(r[1])).total_seconds())
    return dict(c)


def suggest_task(db: Database, since: dt.datetime) -> Optional[Dict[str, str]]:
    """Guess the current task from the longest-used app/title since ``since``."""
    best: Counter = Counter()
    meta: Dict[Tuple[str, str], str] = {}
    for r in db.conn.execute("SELECT app, title, category, start_utc, end_utc FROM activity_events WHERE start_utc>=?", (since.isoformat(),)):
        best[(r[0], r[1])] += int((dt.datetime.fromisoformat(r[4]) - dt.datetime.fromisoformat(r[3])).total_seconds())
        meta[(r[0], r[1])] = r[2]
    if not best:
        return None
    (app, title), _ = best.most_common(1)[0]
    return {"title": title or app, "category": meta[(app, title)], "app": app}
