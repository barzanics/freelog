"""One entry point for "put this on my list / in my log right now": task, finished time block, or a running timer, from a single line of text."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran
from . import quick, taskform as tf
from .tracker import Tracker

MODES = ("task", "log", "timer")


@dataclass
class QuickResult:
    kind: str
    entry: TimeEntry
    minutes: int = 0


def resolve_project(db: Database, name: Optional[str]) -> Optional[str]:
    """``@web`` finds "WebApp": exact (case-insensitive) first, then unique prefix, then unique substring."""
    if not name:
        return None
    n = name.lower()
    ps = db.all(Project)
    for test in (lambda p: p.name.lower() == n, lambda p: p.name.lower().startswith(n), lambda p: n in p.name.lower()):
        hits = [p for p in ps if test(p)]
        if len(hits) == 1:
            return hits[0].id
        if hits:
            return hits[0].id
    return None


def _today_at(t: dt.time, base: dt.datetime) -> dt.datetime:
    return dt.datetime.combine(to_tehran(base).date(), t, tzinfo=TEHRAN).astimezone(UTC)


def create(db: Database, text: str, mode: str = "task", project_id: Optional[str] = None, minutes: int = 0, now: Optional[dt.datetime] = None) -> QuickResult:
    """Parse ``text`` and create what ``mode`` asks for. Explicit ``project_id``/``minutes`` (from chips) override what the text says."""
    if mode not in MODES:
        raise ValueError("unknown mode")
    now = now or now_utc()
    cap = quick.parse(text)
    pid = project_id or resolve_project(db, cap.project)
    mins = minutes or cap.minutes
    if mode == "timer":
        e = Tracker(db, clock=lambda: now).start(cap.title, project_id=pid, tags=cap.tags)
        return QuickResult("timer", e)
    if mode == "log":
        if cap.has_range:
            start, end = _today_at(cap.start_time, now), _today_at(cap.end_time, now)        # type: ignore[arg-type]
            if end <= start:
                end += dt.timedelta(days=1)
            if end > now + dt.timedelta(minutes=1):                                         # "21:00-23:00" typed at 22:00 means yesterday evening
                start, end = start - dt.timedelta(days=1), end - dt.timedelta(days=1)
        else:
            if mins <= 0:
                raise ValueError("برای ثبت زمان، مدت (مثل 45m) یا بازه‌ی ساعت (مثل 09:30-11:00) بنویس")
            end = now
            start = end - dt.timedelta(minutes=mins)
        if (end - start) > dt.timedelta(hours=16):
            raise ValueError("بازه‌ی زمانی بیش از ۱۶ ساعت است")
        e = tf.apply(db, tf.TaskValues(title=cap.title, tags=cap.tags, project_id=pid, start=start, end=end, column="done"), now=now)
        e.source = "quick"
        db.save(e)
        return QuickResult("log", e, int((end - start).total_seconds() // 60))
    start = now if not cap.has_range else _today_at(cap.start_time, now)                     # type: ignore[arg-type]
    mins = cap.range_minutes() if cap.has_range else mins
    v = tf.TaskValues(title=cap.title, tags=cap.tags, project_id=pid, estimated_min=mins, start=start, end=start + dt.timedelta(minutes=mins) if mins else None)
    e = tf.apply(db, v, now=now)
    return QuickResult("task", e, mins)
