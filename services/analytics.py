"""Analytics: the "how many hours did I work this year, on what?" engine.

All aggregation happens in Tehran local days (the Jalali day boundary), with
SQL fetching only the rows in range.
"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Project, TimeEntry
from ..core.persian import TEHRAN, date_to_jalali, jalali_year_bounds, to_tehran


@dataclass
class YearSummary:
    """Everything the dashboard needs for one Jalali year."""
    jalali_year: int
    total_sec: int = 0
    billable_sec: int = 0
    days_worked: int = 0
    longest_streak: int = 0
    current_streak: int = 0
    by_project: Dict[str, int] = field(default_factory=dict)   # project name -> sec
    by_category: Dict[str, int] = field(default_factory=dict)
    by_tag: Dict[str, int] = field(default_factory=dict)
    by_month: List[int] = field(default_factory=lambda: [0] * 12)
    by_weekday: List[int] = field(default_factory=lambda: [0] * 7)  # Mon..Sun
    by_hour: List[int] = field(default_factory=lambda: [0] * 24)
    daily: Dict[dt.date, int] = field(default_factory=dict)         # Gregorian date -> sec

    @property
    def total_hours(self) -> float:
        return round(self.total_sec / 3600, 2)

    @property
    def avg_hours_per_worked_day(self) -> float:
        return round(self.total_sec / 3600 / self.days_worked, 2) if self.days_worked else 0.0


def split_by_local_day_raw(start: dt.datetime, duration_sec: int) -> List[Tuple[dt.date, int, dt.datetime]]:
    """Split [start, start+duration) (Tehran-aware) at local midnights into (day, seconds, chunk_start)."""
    end = start + dt.timedelta(seconds=duration_sec)
    out: List[Tuple[dt.date, int, dt.datetime]] = []
    cur = start
    while cur < end:
        nxt_midnight = dt.datetime.combine(cur.date() + dt.timedelta(days=1), dt.time(), tzinfo=TEHRAN)
        piece_end = min(end, nxt_midnight)
        out.append((cur.date(), int((piece_end - cur).total_seconds()), cur))
        cur = piece_end
    return out


def split_by_local_day(entry: TimeEntry) -> List[Tuple[dt.date, int, dt.datetime]]:
    """Split an entry crossing Tehran midnight into (day, seconds, chunk_start) pieces."""
    if entry.end_utc is None or entry.duration_sec <= 0:
        return []
    return split_by_local_day_raw(to_tehran(entry.start_utc), entry.duration_sec)


def spread_hours(buckets: List[int], start: dt.datetime, sec: int) -> None:
    """Distribute ``sec`` seconds from ``start`` over the clock hours actually covered.

    ``start`` is first truncated to whole seconds: with fractional seconds the distance to the next hour boundary can round down to 0 and the loop would
    never advance (a freeze that any real timer entry, which carries microseconds, could trigger).
    """
    cur = start.replace(microsecond=0)
    left = int(sec)
    while left > 0:
        nxt = cur.replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
        part = max(1, min(left, int((nxt - cur).total_seconds())))          # always make progress
        buckets[cur.hour] += part
        cur, left = cur + dt.timedelta(seconds=part), left - part


_spread_hours = spread_hours                                                   # old name kept for callers/tests


def streaks(days: List[dt.date], today: Optional[dt.date] = None) -> Tuple[int, int]:
    """Return (longest, current) streak over a sorted list of unique dates."""
    if not days:
        return 0, 0
    longest = run = 1
    for a, b in zip(days, days[1:]):
        run = run + 1 if (b - a).days == 1 else 1
        longest = max(longest, run)
    # current streak counts back from today (or yesterday - today may not be worked yet)
    ref = today or days[-1]
    s = set(days)
    cur_day = ref if ref in s else ref - dt.timedelta(days=1)
    current = 0
    while cur_day in s:
        current += 1
        cur_day -= dt.timedelta(days=1)
    return longest, current


class Analytics:
    """Read-only reporting over the database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def year_summary(self, jalali_year: int, today: Optional[dt.date] = None) -> YearSummary:
        """Aggregate a Jalali year. Reads only the needed columns (no model objects) for speed."""
        start, end = jalali_year_bounds(jalali_year)
        lo, hi = (start - dt.timedelta(days=1)).isoformat(), end.isoformat()
        names = {p.id: p.name for p in self.db.all(Project)}
        s = YearSummary(jalali_year)
        y_start, y_end = to_tehran(start).date(), to_tehran(end).date()
        rows = self.db.conn.execute(
            "SELECT start_utc, duration_sec, project_id, category, tags, billable FROM entries "
            "WHERE status='done' AND end_utc IS NOT NULL AND duration_sec>0 AND start_utc>=? AND start_utc<?", (lo, hi))
        month_of: Dict[dt.date, int] = {}
        tag_cache: Dict[str, List[str]] = {}
        for start_iso, dur, pid, cat, tags_json, billable in rows:
            local = to_tehran(dt.datetime.fromisoformat(start_iso))
            end_local = local + dt.timedelta(seconds=dur)
            if tags_json == "[]":
                tags: List[str] = []
            else:
                tags = tag_cache.get(tags_json) or tag_cache.setdefault(tags_json, json.loads(tags_json))
            pname = names.get(pid or "", "—")
            last = end_local - dt.timedelta(microseconds=1)
            pieces = [(local.date(), dur, local)] if local.date() == last.date() else split_by_local_day_raw(local, dur)
            for day, sec, chunk_start in pieces:
                if not (y_start <= day < y_end):
                    continue
                s.total_sec += sec
                if billable:
                    s.billable_sec += sec
                s.daily[day] = s.daily.get(day, 0) + sec
                s.by_project[pname] = s.by_project.get(pname, 0) + sec
                s.by_category[cat] = s.by_category.get(cat, 0) + sec
                for t in tags:
                    s.by_tag[t] = s.by_tag.get(t, 0) + sec
                m = month_of.get(day)
                if m is None:
                    m = month_of[day] = date_to_jalali(day)[1] - 1
                s.by_month[m] += sec
                s.by_weekday[day.weekday()] += sec
                _spread_hours(s.by_hour, chunk_start, sec)
        worked = sorted(s.daily)
        s.days_worked = len(worked)
        s.longest_streak, s.current_streak = streaks(worked, today)
        return s

    @staticmethod
    def heatmap_levels(daily: Dict[dt.date, int], levels: int = 4) -> Dict[dt.date, int]:
        """Map seconds-per-day to 0..levels using quantiles of non-zero days."""
        vals = sorted(v for v in daily.values() if v > 0)
        if not vals:
            return {}
        cuts = [vals[min(len(vals) - 1, int(len(vals) * q / levels))] for q in range(1, levels)]
        out: Dict[dt.date, int] = {}
        for d, v in daily.items():
            if v <= 0:
                continue
            out[d] = 1 + sum(v > c for c in cuts)
        return out

    @staticmethod
    def productivity_score(total_sec: int, days_worked: int, days_in_period: int,
                           interruptions_per_day: float = 0.0, target_daily_hours: float = 6.0) -> int:
        """0-100: output (45%), consistency (35%), focus (20%). Bounded and monotonic."""
        if days_in_period <= 0:
            return 0
        daily_avg_h = total_sec / 3600 / days_in_period
        output = min(1.0, daily_avg_h / target_daily_hours)
        consistency = min(1.0, days_worked / days_in_period)
        focus = max(0.0, 1.0 - min(1.0, interruptions_per_day / 10))
        return round(100 * (0.45 * output + 0.35 * consistency + 0.20 * focus))

    def forecast_year_total_hours(self, jalali_year: int, today: dt.date) -> float:
        """Linear projection of the year total from progress so far."""
        start, end = jalali_year_bounds(jalali_year)
        y0, y1 = to_tehran(start).date(), to_tehran(end).date()
        total_days = (y1 - y0).days
        elapsed = min(total_days, max(1, (today - y0).days + 1))
        so_far = self.year_summary(jalali_year, today).total_sec / 3600
        return round(so_far / elapsed * total_days, 1)

    def month_totals_hours(self, jalali_year: int) -> List[float]:
        return [round(x / 3600, 2) for x in self.year_summary(jalali_year).by_month]

    def project_budget_status(self, project_id: str) -> Dict[str, float]:
        """Hours/cost used versus estimate and budget."""
        p = self.db.get(Project, project_id)
        if p is None:
            raise KeyError(project_id)
        sec = self.db.conn.execute("SELECT COALESCE(SUM(duration_sec),0) FROM entries WHERE project_id=? AND status='done'",
                                   (project_id,)).fetchone()[0]
        hours = sec / 3600
        cost = hours * p.rate_per_hour
        return {"hours": round(hours, 2), "estimated_hours": p.estimated_hours,
                "hours_pct": round(100 * hours / p.estimated_hours, 1) if p.estimated_hours else 0.0,
                "cost": round(cost, 2), "budget": p.budget,
                "budget_pct": round(100 * cost / p.budget, 1) if p.budget else 0.0}
