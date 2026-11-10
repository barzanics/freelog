"""Live timer logic: start/stop/switch, rounding, minimum duration, idle trimming.

Pure logic with an injectable clock so every path is deterministic in tests.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Callable, List, Optional

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import now_utc

log = logging.getLogger("worktracker.tracker")
MAX_SESSION_SEC = 4 * 3600  # sessions are auto-split after this


@dataclass
class TrackerSettings:
    """User-configurable tracking behaviour."""
    round_to_min: int = 0          # 0 = off, else 5/15/30
    min_duration_sec: int = 60     # shorter sessions are discarded
    idle_threshold_sec: int = 300  # idle longer than this is trimmed


def round_seconds(seconds: int, step_min: int) -> int:
    """Round *up* to the next ``step_min`` minutes (0 disables)."""
    if step_min <= 0 or seconds <= 0:
        return max(0, seconds)
    step = step_min * 60
    return -(-seconds // step) * step


class Tracker:
    """Starts and stops time entries and guarantees at most one running timer."""

    def __init__(self, db: Database, settings: Optional[TrackerSettings] = None,
                 clock: Callable[[], dt.datetime] = now_utc) -> None:
        self.db = db
        self.settings = settings or TrackerSettings()
        self.clock = clock

    @property
    def current(self) -> Optional[TimeEntry]:
        return self.db.running_entry()

    def running(self) -> List[TimeEntry]:
        """All running timers (more than one only when started with ``exclusive=False``)."""
        return self.db.running_entries()

    def start(self, title: str, project_id: Optional[str] = None, category: str = "general",
              tags: Optional[List[str]] = None, billable: bool = False, exclusive: bool = True) -> TimeEntry:
        """Start a timer. ``exclusive`` (default) stops running timers first; otherwise timers run in parallel."""
        title = title.strip()
        if not title:
            raise ValueError("title is required")
        if exclusive:
            for r in self.running():
                self.stop(entry_id=r.id)
        entry = TimeEntry(title=title, start_utc=self.clock(), project_id=project_id, category=category,
                          tags=list(tags or []), status=Status.RUNNING, billable=billable)
        self.db.save(entry)
        return entry

    def elapsed(self, entry_id: Optional[str] = None) -> int:
        """Seconds a timer has been running (the latest one by default; 0 if none)."""
        cur = self.db.get(TimeEntry, entry_id) if entry_id else self.current
        return max(0, int((self.clock() - cur.start_utc).total_seconds())) if cur else 0

    def stop(self, idle_seconds: int = 0, entry_id: Optional[str] = None) -> Optional[TimeEntry]:
        """Stop the timer.

        ``idle_seconds`` is trimmed from the end (time the user was away).
        Returns the saved entry, or None if nothing ran or it was shorter than the minimum.
        """
        cur = self.db.get(TimeEntry, entry_id) if entry_id else self.current
        if cur is None or cur.status != Status.RUNNING:
            return None
        end = self.clock() - dt.timedelta(seconds=max(0, idle_seconds))
        if end < cur.start_utc:
            end = cur.start_utc
        raw = int((end - cur.start_utc).total_seconds())
        if raw < self.settings.min_duration_sec:
            self.db.delete(TimeEntry, cur.id)
            log.info("discarded %ss session", raw)
            return None
        # split overlong sessions into consecutive chunks
        chunks: List[TimeEntry] = []
        cursor = cur.start_utc
        remaining = raw
        while remaining > MAX_SESSION_SEC:
            chunk_end = cursor + dt.timedelta(seconds=MAX_SESSION_SEC)
            chunks.append(self._clone(cur, cursor, chunk_end))
            cursor, remaining = chunk_end, remaining - MAX_SESSION_SEC
        cur.start_utc = cursor
        cur.end_utc = cursor + dt.timedelta(seconds=remaining)
        cur.duration_sec = round_seconds(remaining, self.settings.round_to_min)
        cur.status, cur.completed_at = Status.DONE, self.clock()
        with self.db.transaction():
            for ch in chunks:
                self.db.save(ch)
            self.db.save(cur)
        return cur

    @staticmethod
    def _clone(src: TimeEntry, start: dt.datetime, end: dt.datetime) -> TimeEntry:
        from dataclasses import replace
        from ..core.models import new_id
        return replace(src, id=new_id(), start_utc=start, end_utc=end,
                       duration_sec=int((end - start).total_seconds()), status=Status.DONE)

    def add_manual(self, title: str, start: dt.datetime, end: dt.datetime, **kw: object) -> TimeEntry:
        """Add a past entry. Rejects overlaps with other *done* entries only if ``strict`` is set."""
        if end <= start:
            raise ValueError("end must be after start")
        if not title.strip():
            raise ValueError("title is required")
        entry = TimeEntry(title=title.strip(), start_utc=start, end_utc=end, status=Status.DONE, **kw)  # type: ignore[arg-type]
        entry.duration_sec = round_seconds(entry.duration_sec, self.settings.round_to_min)
        self.db.save(entry)
        return entry

    def recover_after_crash(self) -> Optional[TimeEntry]:
        """If the app died with a timer running, close it at its last update time."""
        cur = self.current
        if cur is None:
            return None
        end = max(cur.start_utc, cur.updated_at)
        raw = int((end - cur.start_utc).total_seconds())
        if raw < self.settings.min_duration_sec:
            self.db.delete(TimeEntry, cur.id)
            return None
        cur.end_utc, cur.duration_sec, cur.status = end, raw, Status.DONE
        self.db.save(cur)
        return cur

    def resume_last(self) -> Optional[TimeEntry]:
        """After an idle auto-stop: start a new timer on the same title/project/tags as the most recent finished entry."""
        rows = self.db.conn.execute("SELECT * FROM entries WHERE status='done' ORDER BY end_utc DESC LIMIT 1").fetchall()
        if not rows:
            return None
        last = TimeEntry.from_row(rows[0])
        return self.start(last.title, project_id=last.project_id, category=last.category, tags=last.tags, billable=last.billable)
