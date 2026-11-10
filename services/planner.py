"""Planning: day blocks, free slots, auto-scheduling, buffers, Eisenhower, estimate learning."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import TEHRAN, UTC, to_tehran

Slot = Tuple[dt.datetime, dt.datetime]


@dataclass
class WorkingHours:
    start: dt.time = dt.time(9, 0)
    end: dt.time = dt.time(17, 0)
    off_weekdays: Tuple[int, ...] = (4,)  # Friday (Mon=0)


def merge(slots: List[Slot]) -> List[Slot]:
    """Merge overlapping/adjacent intervals."""
    out: List[Slot] = []
    for s, e in sorted(slots):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def free_slots(window: Slot, busy: List[Slot], min_minutes: int = 1) -> List[Slot]:
    """Gaps inside ``window`` not covered by ``busy``."""
    out: List[Slot] = []
    cur = window[0]
    for s, e in merge([(max(s, window[0]), min(e, window[1])) for s, e in busy if e > window[0] and s < window[1]]):
        if s - cur >= dt.timedelta(minutes=min_minutes):
            out.append((cur, s))
        cur = max(cur, e)
    if window[1] - cur >= dt.timedelta(minutes=min_minutes):
        out.append((cur, window[1]))
    return out


def eisenhower(e: TimeEntry, today: Optional[dt.datetime] = None) -> str:
    """Quadrant: do / schedule / delegate / eliminate."""
    today = today or dt.datetime.now(UTC)
    urgent = e.due_utc is not None and e.due_utc - today <= dt.timedelta(days=2)
    return {(True, True): "do", (False, True): "schedule", (True, False): "delegate", (False, False): "eliminate"}[(urgent, e.important)]


class Planner:
    def __init__(self, db: Database, hours: Optional[WorkingHours] = None) -> None:
        self.db, self.hours = db, hours or WorkingHours()

    def day_window(self, day: dt.date) -> Optional[Slot]:
        if day.weekday() in self.hours.off_weekdays:
            return None
        return (dt.datetime.combine(day, self.hours.start, tzinfo=TEHRAN), dt.datetime.combine(day, self.hours.end, tzinfo=TEHRAN))

    def busy(self, day: dt.date, exclude: Optional[str] = None) -> List[Slot]:
        lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN)
        rows = self.db.entries_between(lo - dt.timedelta(hours=12), lo + dt.timedelta(days=1), only_done=False)
        out = []
        for e in rows:
            if e.id == exclude or (e.status == Status.PLANNED and e.end_utc is None):
                continue
            end = e.end_utc or e.start_utc + dt.timedelta(seconds=e.duration_sec)
            out.append((to_tehran(e.start_utc), to_tehran(end)))
        return out

    def day_free(self, day: dt.date, buffer_min: int = 0) -> List[Slot]:
        win = self.day_window(day)
        if win is None:
            return []
        busy = [(s - dt.timedelta(minutes=buffer_min), e + dt.timedelta(minutes=buffer_min)) for s, e in self.busy(day)]
        return free_slots(win, busy)

    def time_block(self, entry_id: str, start: dt.datetime) -> TimeEntry:
        """Reserve a block for a planned task starting at ``start`` (uses its estimate)."""
        e = self.db.get(TimeEntry, entry_id)
        if e is None:
            raise KeyError(entry_id)
        mins = e.estimated_min or 30
        end = start + dt.timedelta(minutes=mins)
        for s, b_end in self.busy(to_tehran(start).date(), exclude=entry_id):
            if start < b_end and end > s:
                raise ValueError("overlaps an existing block")
        e.start_utc, e.end_utc, e.status = start.astimezone(UTC), end.astimezone(UTC), Status.PLANNED
        e.duration_sec = 0
        self.db.save(e)
        return e

    def auto_schedule(self, tasks: List[TimeEntry], from_day: dt.date, horizon_days: int = 14, buffer_min: int = 10,
                      now: Optional[dt.datetime] = None) -> Dict[str, Optional[dt.datetime]]:
        """Greedy: earliest deadline, then priority (1=highest), longest first; placed in free slots with buffers."""
        order = sorted(tasks, key=lambda t: (t.due_utc or dt.datetime.max.replace(tzinfo=UTC), t.priority, -(t.estimated_min or 30)))
        placed: Dict[str, Optional[dt.datetime]] = {}
        extra_busy: Dict[dt.date, List[Slot]] = {}
        for t in order:
            need = dt.timedelta(minutes=t.estimated_min or 30)
            placed[t.id] = None
            for off in range(horizon_days):
                day = from_day + dt.timedelta(days=off)
                win = self.day_window(day)
                if win is None:
                    continue
                busy = self.busy(day) + extra_busy.get(day, [])
                busy = [(s - dt.timedelta(minutes=buffer_min), e + dt.timedelta(minutes=buffer_min)) for s, e in busy]
                for s, e in free_slots(win, busy):
                    if now and e <= now:
                        continue
                    s = max(s, now) if now else s
                    if e - s >= need:
                        placed[t.id] = s
                        extra_busy.setdefault(day, []).append((s, s + need))
                        break
                if placed[t.id]:
                    break
        return placed

    def estimate_accuracy(self) -> Dict[str, float]:
        """Learn bias per category: ratio actual/estimate over finished entries with estimates."""
        ratios: Dict[str, List[float]] = {}
        for r in self.db.conn.execute("SELECT category, duration_sec, estimated_min FROM entries WHERE status='done' AND estimated_min>0 AND duration_sec>0"):
            ratios.setdefault(r[0], []).append(r[1] / 60 / r[2])
        return {k: round(mean(v), 2) for k, v in ratios.items()}

    def suggest_estimate(self, category: str, raw_estimate_min: int) -> int:
        """Adjust a raw estimate by the learned bias for the category."""
        return round(raw_estimate_min * self.estimate_accuracy().get(category, 1.0))


def set_quadrant(db: Database, entry_id: str, quadrant: str, now: Optional[dt.datetime] = None) -> TimeEntry:
    """Move a task to an Eisenhower quadrant by adjusting ``important`` and ``due_utc`` (drag-drop target)."""
    if quadrant not in ("do", "schedule", "delegate", "eliminate"):
        raise ValueError("unknown quadrant")
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    now = now or dt.datetime.now(UTC)
    urgent_wanted = quadrant in ("do", "delegate")
    e.important = quadrant in ("do", "schedule")
    soon = e.due_utc is not None and e.due_utc - now <= dt.timedelta(days=2)
    if urgent_wanted and not soon:
        e.due_utc = now + dt.timedelta(days=1)
    elif not urgent_wanted and soon:
        e.due_utc = now + dt.timedelta(days=14)           # keep a deadline, just not urgent
    db.save(e)
    return e


def quadrants(db: Database, now: Optional[dt.datetime] = None) -> Dict[str, List[TimeEntry]]:
    """Open (not done) top-level tasks grouped by quadrant."""
    now = now or dt.datetime.now(UTC)
    out: Dict[str, List[TimeEntry]] = {"do": [], "schedule": [], "delegate": [], "eliminate": []}
    for e in db.all(TimeEntry):
        if e.status != Status.DONE and not e.parent_id:
            out[eisenhower(e, now)].append(e)
    return out
