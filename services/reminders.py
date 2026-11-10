"""Health reminders (20-20-20 eye rule, posture, hydration). Pure scheduler; the UI shows the notification."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Callable, Dict, List

from ..core.database import Database
from ..core.persian import now_utc

DEFAULTS = {"eyes": 20, "posture": 45, "water": 60}   # minutes
MESSAGES = {"eyes": "۲۰ ثانیه به نقطه‌ای دور نگاه کنید", "posture": "وضعیت نشستن را اصلاح کنید و کمی بایستید", "water": "کمی آب بنوشید"}


@dataclass
class Reminders:
    db: Database
    clock: Callable[[], dt.datetime] = now_utc

    def intervals(self) -> Dict[str, int]:
        return {**DEFAULTS, **self.db.get_setting("reminder_intervals", {})}

    def set_interval(self, kind: str, minutes: int) -> None:
        if kind not in DEFAULTS or minutes < 1:
            raise ValueError("bad reminder")
        self.db.set_setting("reminder_intervals", {**self.db.get_setting("reminder_intervals", {}), kind: minutes})

    def due(self, working: bool, focus_mode: bool = False) -> List[str]:
        """Kinds that should fire now. Only while ``working``; silenced in focus mode. Marks them fired."""
        if not working or focus_mode:
            return []
        now = self.clock()
        last = self.db.get_setting("reminder_last", {})
        out = []
        for kind, mins in self.intervals().items():
            if kind not in last:
                last[kind] = now.isoformat()          # first time: start counting from now
            elif now - dt.datetime.fromisoformat(last[kind]) >= dt.timedelta(minutes=mins):
                out.append(kind)
                last[kind] = now.isoformat()
        self.db.set_setting("reminder_last", last)
        return out
