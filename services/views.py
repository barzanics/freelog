"""Planner views (week grid, Jalali month calendar) and time-boxing adherence."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Status, TimeEntry
import calendar as _cal
from ..core import persian as _p
from ..core.persian import TEHRAN, date_to_jalali, jalali_month_length, jalali_to_date, to_tehran
from .analytics import split_by_local_day


def week_start(day: dt.date) -> dt.date:
    """Saturday on/before ``day`` (Persian week)."""
    return day - dt.timedelta(days=(day.weekday() + 2) % 7)


def week_grid(db: Database, day: dt.date) -> List[Dict[str, object]]:
    """7 columns Sat..Fri; each has date and blocks (title, start_hh_mm, end_hh_mm, status) in Tehran time."""
    start = week_start(day)
    lo = dt.datetime.combine(start, dt.time(), tzinfo=TEHRAN)
    entries = db.entries_between(lo - dt.timedelta(hours=12), lo + dt.timedelta(days=7), only_done=False)
    cols: List[Dict[str, object]] = [{"date": start + dt.timedelta(days=i), "blocks": []} for i in range(7)]
    for e in entries:
        if e.end_utc is None:
            continue
        s, en = to_tehran(e.start_utc), to_tehran(e.end_utc)
        for i, c in enumerate(cols):
            d: dt.date = c["date"]  # type: ignore[assignment]
            day_lo = dt.datetime.combine(d, dt.time(), tzinfo=TEHRAN)
            day_hi = day_lo + dt.timedelta(days=1)
            a, b = max(s, day_lo), min(en, day_hi)
            if a < b:
                c["blocks"].append({"id": e.id, "title": e.title, "start": a.strftime("%H:%M"), "end": b.strftime("%H:%M"), "status": e.status.value})  # type: ignore[union-attr]
    for c in cols:
        c["blocks"].sort(key=lambda b: b["start"])  # type: ignore[union-attr]
    return cols


def month_calendar(db: Database, jy: int, jm: int) -> Dict[str, object]:
    """Jalali month grid: rows of 7 (Sat..Fri) with None padding; per-day seconds and month total."""
    first = jalali_to_date(jy, jm, 1)
    n = jalali_month_length(jy, jm)
    lo = dt.datetime.combine(first, dt.time(), tzinfo=TEHRAN)
    totals: Dict[dt.date, int] = {}
    for e in db.entries_between(lo - dt.timedelta(days=1), lo + dt.timedelta(days=n + 1)):
        for d, sec, _ in split_by_local_day(e):
            if first <= d < first + dt.timedelta(days=n):
                totals[d] = totals.get(d, 0) + sec
    cells: List[Optional[Tuple[int, int]]] = [None] * ((first.weekday() + 2) % 7)
    cells += [(i + 1, totals.get(first + dt.timedelta(days=i), 0)) for i in range(n)]
    cells += [None] * (-len(cells) % 7)
    return {"year": jy, "month": jm, "weeks": [cells[i:i + 7] for i in range(0, len(cells), 7)], "total_sec": sum(totals.values())}


def timebox_adherence(db: Database, day: dt.date) -> Dict[str, float]:
    """How much of the planned blocks of ``day`` was actually worked (overlap with done entries)."""
    lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN)
    hi = lo + dt.timedelta(days=1)
    rows = db.entries_between(lo, hi, only_done=False)
    planned = [e for e in rows if e.status == Status.PLANNED and e.end_utc]
    done = [e for e in rows if e.status == Status.DONE and e.end_utc]
    planned_sec = sum((e.end_utc - e.start_utc).total_seconds() for e in planned)  # type: ignore[operator]
    covered = 0.0
    for p in planned:
        for d in done:
            a, b = max(p.start_utc, d.start_utc), min(p.end_utc, d.end_utc)  # type: ignore[type-var]
            if a < b:
                covered += (b - a).total_seconds()
    return {"planned_min": round(planned_sec / 60, 1), "worked_in_plan_min": round(covered / 60, 1),
            "adherence_pct": round(100 * min(covered, planned_sec) / planned_sec, 1) if planned_sec else 0.0}


def breakdown_by_category(entries: List[TimeEntry]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for e in entries:
        out[e.category] = out.get(e.category, 0) + e.duration_sec
    return out


def jalali_grid(jy: int, jm: int) -> List[List[Optional[int]]]:
    """Rows of 7 (Saturday-first) with the Jalali day numbers of one month; None pads the ends. Used by the date-picker popup."""
    first = jalali_to_date(jy, jm, 1)
    cells: List[Optional[int]] = [None] * ((first.weekday() + 2) % 7) + list(range(1, jalali_month_length(jy, jm) + 1))
    cells += [None] * (-len(cells) % 7)
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def shift_month(jy: int, jm: int, delta: int) -> Tuple[int, int]:
    n = jy * 12 + (jm - 1) + delta
    return n // 12, n % 12 + 1


def today_ym(d: dt.date) -> Tuple[int, int]:
    """(year, month) of ``d`` in the active calendar."""
    return (d.year, d.month) if _p.is_gregorian() else date_to_jalali(d)[:2]


def month_layout(y: int, m: int) -> Dict[str, object]:
    """Everything a month grid needs, for the active calendar: Jalali (Saturday-first) or Gregorian (Monday-first).

    Returns {title, first, days, weeks: [[date|None]*7...], labels: [7 weekday names]}.
    """
    if _p.is_gregorian():
        first, n = dt.date(y, m, 1), _cal.monthrange(y, m)[1]
        offset = first.weekday()
        title = f"{_p.MONTHS_EN[m - 1]} {y}"
    else:
        first, n = jalali_to_date(y, m, 1), jalali_month_length(y, m)
        offset = (first.weekday() + 2) % 7
        title = f"{_p.MONTHS_FA[m - 1]} {y}"
    cells: List[Optional[dt.date]] = [None] * offset + [first + dt.timedelta(days=i) for i in range(n)]
    cells += [None] * (-len(cells) % 7)
    return {"title": title, "first": first, "days": n, "weeks": [cells[i:i + 7] for i in range(0, len(cells), 7)], "labels": _p.weekday_names(short=False)}
