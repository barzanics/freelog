"""Advanced analytics: trends, comparisons, flow, context switches, correlations, Sankey, year in review, weekly review."""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Project, TimeEntry
from ..core.persian import MONTHS_FA, TEHRAN, date_to_jalali, jalali_year_bounds, to_tehran, to_fa_digits
from .analytics import Analytics, YearSummary, split_by_local_day


def daily_seconds(db: Database, start: dt.date, end: dt.date) -> Dict[dt.date, int]:
    """Tehran-local seconds per day for [start, end)."""
    lo = dt.datetime.combine(start - dt.timedelta(days=1), dt.time(), tzinfo=TEHRAN)
    hi = dt.datetime.combine(end, dt.time(), tzinfo=TEHRAN)
    out: Dict[dt.date, int] = defaultdict(int)
    for e in db.entries_between(lo, hi):
        for day, sec, _ in split_by_local_day(e):
            if start <= day < end:
                out[day] += sec
    return dict(out)


def moving_average(values: List[float], window: int = 7) -> List[float]:
    """Trailing moving average (shorter window at the start)."""
    if window < 1:
        raise ValueError("window must be >= 1")
    out, acc = [], 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= window:
            acc -= values[i - window]
        out.append(round(acc / min(i + 1, window), 4))
    return out


def compare_periods(db: Database, a: Tuple[dt.date, dt.date], b: Tuple[dt.date, dt.date]) -> Dict[str, float]:
    """Hours of period a vs b (end exclusive) and the % change (None-safe: 0 if b is empty)."""
    ha = sum(daily_seconds(db, *a).values()) / 3600
    hb = sum(daily_seconds(db, *b).values()) / 3600
    return {"a_hours": round(ha, 2), "b_hours": round(hb, 2), "change_pct": round(100 * (ha - hb) / hb, 1) if hb else 0.0}


def week_over_week(db: Database, today: dt.date) -> Dict[str, float]:
    """This Saturday-based week up to today vs the same span last week."""
    start = today - dt.timedelta(days=(today.weekday() + 2) % 7)
    n = (today - start).days + 1
    prev = start - dt.timedelta(days=7)
    return compare_periods(db, (start, start + dt.timedelta(days=n)), (prev, prev + dt.timedelta(days=n)))


def year_over_year(db: Database, jalali_year: int) -> Dict[str, float]:
    def span(y: int) -> Tuple[dt.date, dt.date]:
        s, e = jalali_year_bounds(y)
        return to_tehran(s).date(), to_tehran(e).date()
    return compare_periods(db, span(jalali_year), span(jalali_year - 1))


def flow_sessions(entries: List[TimeEntry], max_gap_min: int = 5, min_minutes: int = 45) -> List[Tuple[dt.datetime, dt.datetime]]:
    """Uninterrupted work stretches (entries separated by <= gap) lasting at least ``min_minutes``; longest first."""
    spans = sorted((e.start_utc, e.end_utc) for e in entries if e.end_utc)
    merged: List[List[dt.datetime]] = []
    for s, e in spans:
        if merged and s - merged[-1][1] <= dt.timedelta(minutes=max_gap_min):
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    res = [(s, e) for s, e in merged if e - s >= dt.timedelta(minutes=min_minutes)]
    return sorted(res, key=lambda x: x[0] - x[1])


def context_switches(entries: List[TimeEntry], max_gap_min: int = 10) -> int:
    """Number of back-to-back entries that changed project/category (a proxy for distraction cost)."""
    es = sorted((e for e in entries if e.end_utc), key=lambda e: e.start_utc)
    n = 0
    for a, b in zip(es, es[1:]):
        if b.start_utc - a.end_utc <= dt.timedelta(minutes=max_gap_min) and (a.project_id, a.category) != (b.project_id, b.category):
            n += 1
    return n


def switch_cost_minutes(switches: int, minutes_per_switch: float = 15 * 0.5) -> float:
    """Rough cost: ~7.5 min of refocus per switch (configurable estimate, not a measurement)."""
    return switches * minutes_per_switch


def peak_hours(summary: YearSummary, top: int = 3) -> List[int]:
    """Clock hours with the most worked time."""
    return [h for h, s in sorted(enumerate(summary.by_hour), key=lambda x: -x[1])[:top] if s > 0]


def early_start_effect(db: Database, start: dt.date, end: dt.date, before_hour: int = 9) -> Optional[Dict[str, float]]:
    """Compare average daily hours on days whose first entry started before ``before_hour`` vs later."""
    lo = dt.datetime.combine(start, dt.time(), tzinfo=TEHRAN)
    hi = dt.datetime.combine(end, dt.time(), tzinfo=TEHRAN)
    first: Dict[dt.date, int] = {}
    tot: Dict[dt.date, int] = defaultdict(int)
    for e in db.entries_between(lo, hi):
        t = to_tehran(e.start_utc)
        d = t.date()
        first[d] = min(first.get(d, 24 * 60), t.hour * 60 + t.minute)
        tot[d] += e.duration_sec
    early = [tot[d] / 3600 for d in tot if first[d] < before_hour * 60]
    late = [tot[d] / 3600 for d in tot if first[d] >= before_hour * 60]
    if not early or not late:
        return None
    ae, al = sum(early) / len(early), sum(late) / len(late)
    return {"early_avg": round(ae, 2), "late_avg": round(al, 2), "difference_pct": round(100 * (ae - al) / al, 1) if al else 0.0}


def sankey(db: Database, jalali_year: int) -> Dict[str, List]:
    """Nodes and links (project -> category, seconds) for a Sankey diagram."""
    s, e = jalali_year_bounds(jalali_year)
    names = {p.id: p.name for p in db.all(Project)}
    links: Counter = Counter()
    for en in db.entries_between(s, e):
        links[(names.get(en.project_id or "", "—"), en.category)] += en.duration_sec
    nodes = sorted({a for a, _ in links} | {b for _, b in links})
    return {"nodes": nodes, "links": [{"source": a, "target": b, "hours": round(v / 3600, 2)} for (a, b), v in links.most_common()]}


def year_in_review(db: Database, jalali_year: int) -> Dict[str, object]:
    """Spotify-Wrapped style facts for one Jalali year."""
    s = Analytics(db).year_summary(jalali_year)
    if not s.total_sec:
        return {"year": jalali_year, "empty": True}
    busiest = max(s.daily.items(), key=lambda kv: kv[1])
    top_p = max(s.by_project.items(), key=lambda kv: kv[1])
    top_c = max(s.by_category.items(), key=lambda kv: kv[1])
    wd = max(range(7), key=lambda i: s.by_weekday[i])
    month = max(range(12), key=lambda i: s.by_month[i])
    return {"year": jalali_year, "empty": False, "total_hours": s.total_hours, "days_worked": s.days_worked,
            "longest_streak": s.longest_streak, "busiest_day": busiest[0].isoformat(), "busiest_day_hours": round(busiest[1] / 3600, 2),
            "top_project": top_p[0], "top_project_hours": round(top_p[1] / 3600, 1), "top_category": top_c[0],
            "favorite_weekday": wd, "best_month": MONTHS_FA[month], "peak_hours": peak_hours(s),
            "avg_per_worked_day": s.avg_hours_per_worked_day}


def weekly_review(db: Database, today: dt.date) -> str:
    """Auto-generated Persian weekly summary with one insight."""
    wow = week_over_week(db, today)
    start = today - dt.timedelta(days=(today.weekday() + 2) % 7)
    days = daily_seconds(db, start, today + dt.timedelta(days=1))
    if not days:
        return "این هفته کاری ثبت نشده است."
    best = max(days.items(), key=lambda kv: kv[1])
    trend = "بیشتر" if wow["change_pct"] > 0 else "کمتر" if wow["change_pct"] < 0 else "برابر"
    return to_fa_digits(f"این هفته {wow['a_hours']} ساعت کار کردید ({abs(wow['change_pct'])}٪ {trend} از هفته قبل). "
                        f"پرکارترین روز: {best[0].isoformat()} با {round(best[1] / 3600, 1)} ساعت.")
