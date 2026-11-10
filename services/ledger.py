"""The hourly ledger: how many minutes of every clock hour were *really* worked, in which apps, and how much of that is still unlogged.

Samples (every few seconds from the runtime) are attributed to the hour they fall in - an interval that straddles :00 is split exactly. Three states:
``active`` (input within the timeout), ``passive`` (no input but the screen is alive in a work app: a call, slides, a long read) and ``idle``. A gap longer than ``max_gap``
(sleep, lock, the app was suspended) counts as nothing at all, so a laptop lid never inflates the numbers.

``pending()`` then answers the question the prompt has to ask: *for each finished hour, how much engaged time is not covered by any logged entry?* Logged time is the UNION of
entries (overlaps are never double counted, running timers count until now). ``suggest()`` turns the answer into a pre-filled prompt placed in the real free slot.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import HourLog, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran, tr
from .activity import classify
from .autotrack import hour_summary

ACTIVE, PASSIVE, IDLE = "active", "passive", "idle"
Interval = Tuple[dt.datetime, dt.datetime]


def hour_floor(t: dt.datetime) -> dt.datetime:
    """Start of the Tehran clock hour containing ``t`` (as UTC)."""
    return to_tehran(t).replace(minute=0, second=0, microsecond=0).astimezone(UTC)


def merge(intervals: List[Interval]) -> List[Interval]:
    out: List[Interval] = []
    for a, b in sorted(i for i in intervals if i[1] > i[0]):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


class Ledger:
    def __init__(self, db: Database, clock: Callable[[], dt.datetime] = now_utc, max_gap: float = 90.0) -> None:
        self.db, self.clock, self.max_gap = db, clock, max_gap
        self._last: Optional[dt.datetime] = None
        self._buf: Dict[dt.datetime, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ measuring
    def _bucket(self, h: dt.datetime) -> Dict[str, Any]:
        b = self._buf.get(h)
        if b is None:                                            # first touch: continue from what the previous run of the app already stored
            row = self.db.conn.execute("SELECT * FROM hour_log WHERE hour_start=?", (h.isoformat(),)).fetchone()
            hl = HourLog.from_row(row) if row else None
            b = {"engaged": float(hl.engaged_sec) if hl else 0.0, "idle": float(hl.idle_sec) if hl else 0.0, "apps": {k: float(v) for k, v in (hl.apps.items() if hl else [])}, "dirty": False}
            self._buf[h] = b
        return b

    def sample(self, state: str, app: str = "", now: Optional[dt.datetime] = None) -> None:
        """Attribute the time since the previous sample to ``state``."""
        now = now or self.clock()
        last, self._last = self._last, now
        if last is None or now <= last or (now - last).total_seconds() > self.max_gap:
            return                                               # first sample, clock going backwards, or a sleep/lock gap: count nothing
        cur = last
        while cur < now:
            h = hour_floor(cur)
            end = min(now, h + dt.timedelta(hours=1))
            sec = (end - cur).total_seconds()
            b = self._bucket(h)
            if state == IDLE:
                b["idle"] += sec
            else:
                b["engaged"] += sec
                key = app or "?"
                b["apps"][key] = b["apps"].get(key, 0.0) + sec
            b["dirty"] = True
            cur = end

    def flush(self) -> int:
        """Write changed hours to ``hour_log`` (one row per hour; reuses the row so nothing is duplicated). Returns how many rows were written."""
        n = 0
        with self.db.transaction():
            for h, b in self._buf.items():
                if not b["dirty"]:
                    continue
                row = self.db.conn.execute("SELECT * FROM hour_log WHERE hour_start=?", (h.isoformat(),)).fetchone()
                hl = HourLog.from_row(row) if row else HourLog(hour_start=h)
                hl.engaged_sec, hl.idle_sec = int(round(b["engaged"])), int(round(b["idle"]))
                hl.apps = {k: int(round(v)) for k, v in b["apps"].items() if v >= 1}
                hl.summary = hour_summary(hl.apps)
                self.db.save(hl)
                b["dirty"] = False
                n += 1
        return n

    # ------------------------------------------------------------------ reading
    def logged_intervals(self, lo: dt.datetime, hi: dt.datetime, now: Optional[dt.datetime] = None) -> List[Interval]:
        now = now or self.clock()
        out: List[Interval] = []
        for r in self.db.conn.execute("SELECT * FROM entries WHERE status IN ('done','running') AND start_utc >= ? AND start_utc < ?",
                                        ((lo - dt.timedelta(days=1)).isoformat(), hi.isoformat())):
            e = TimeEntry.from_row(r)
            end = e.end_utc or now
            a, b = max(e.start_utc, lo), min(end, hi)
            if b > a:
                out.append((a, b))
        return merge(out)

    def free_slots(self, hour_start: dt.datetime, now: Optional[dt.datetime] = None, min_sec: int = 60) -> List[Interval]:
        """Parts of the hour not covered by any logged entry, longest first."""
        hi = hour_start + dt.timedelta(hours=1)
        slots, cur = [], hour_start
        for a, b in self.logged_intervals(hour_start, hi, now):
            if a > cur:
                slots.append((cur, a))
            cur = max(cur, b)
        if cur < hi:
            slots.append((cur, hi))
        return sorted((s for s in slots if (s[1] - s[0]).total_seconds() >= min_sec), key=lambda s: -(s[1] - s[0]).total_seconds())

    def hour(self, hour_start: dt.datetime, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
        b = self._bucket(hour_start)
        hi = hour_start + dt.timedelta(hours=1)
        logged = sum((e - s).total_seconds() for s, e in self.logged_intervals(hour_start, hi, now))
        engaged = min(3600.0, b["engaged"])
        apps = sorted(((k, int(v)) for k, v in b["apps"].items() if v >= 1), key=lambda kv: -kv[1])
        return {"hour_start": hour_start, "engaged_sec": int(engaged), "idle_sec": int(min(3600.0, b["idle"])), "apps": apps, "logged_sec": int(logged),
                "unlogged_sec": int(max(0.0, engaged - logged))}

    def answered(self) -> Dict[str, str]:
        return self.db.get_setting("ledger_answered", {})

    def mark_answered(self, hour_start: dt.datetime, action: str, now: Optional[dt.datetime] = None) -> None:
        d = self.answered()
        d[hour_start.isoformat()] = action
        cutoff = ((now or self.clock()) - dt.timedelta(days=4)).isoformat()
        self.db.set_setting("ledger_answered", {k: v for k, v in d.items() if k >= cutoff})

    def pending(self, now: Optional[dt.datetime] = None, lookback_hours: int = 12, min_unlogged_sec: int = 300, grace_sec: int = 120) -> List[Dict[str, Any]]:
        """Finished hours (oldest first) with at least ``min_unlogged_sec`` of engaged time that no entry covers and that were not answered/skipped yet.
        The hour that just ended is only asked about ``grace_sec`` after the boundary, so its last minutes are measured."""
        now = now or self.clock()
        done = self.answered()
        cur = hour_floor(now)
        out = []
        for k in range(lookback_hours, 0, -1):
            h = cur - dt.timedelta(hours=k)
            if h.isoformat() in done or now < h + dt.timedelta(hours=1, seconds=grace_sec):
                continue
            rep = self.hour(h, now)
            if rep["unlogged_sec"] >= min_unlogged_sec:
                out.append(rep)
        return out

    def suggest(self, rep: Dict[str, Any], now: Optional[dt.datetime] = None) -> Dict[str, Any]:
        """Pre-filled prompt for one hour: minutes = the unlogged part, placed inside the biggest free slot."""
        h = rep["hour_start"]
        minutes = max(1, min(60, math.ceil(rep["unlogged_sec"] / 60)))
        slots = self.free_slots(h, now)
        if slots:
            a, b = slots[0]
            to = min(b, a + dt.timedelta(minutes=minutes))
            frm = a
            minutes = max(1, min(minutes, int((b - a).total_seconds() // 60) or 1))
        else:
            frm, to = h, h + dt.timedelta(minutes=minutes)
        top = rep["apps"][0][0] if rep["apps"] else ""
        name = top.replace(".exe", "")
        cat = classify(top, "") if top else "general"
        return {"hour_start": h, "from": frm, "to": to, "minutes": minutes, "apps": rep["apps"][:4], "engaged_min": rep["engaged_sec"] // 60, "logged_min": rep["logged_sec"] // 60,
                "title_hint": tr(f"کار با {name}", f"Work in {name}") if name else "", "category": cat if cat not in ("other", "") else "general"}
