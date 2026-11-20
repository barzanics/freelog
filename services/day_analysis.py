"""How was the day spent? From 00:00 to 24:00 of any day (Tehran local time): tracked segments per project, gaps nobody accounted for, focus blocks, hour-by-hour minutes,
plan versus reality - and the same aggregated over any range. This is the data behind the calendar's "actual" lane, the day summary and the statistics panel."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran
from . import calendar_events as ce

Interval = Tuple[dt.datetime, dt.datetime]
GAP_MIN = 15          # an untracked stretch inside the working day counts as "unaccounted" from this length
FOCUS_JOIN = 5        # tracked blocks separated by less than this many minutes form one focus block


def day_bounds(day: dt.date) -> Interval:
    lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN).astimezone(UTC)
    return lo, dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), tzinfo=TEHRAN).astimezone(UTC)


def _merge(iv: List[Interval]) -> List[Interval]:
    out: List[Interval] = []
    for a, b in sorted(i for i in iv if i[1] > i[0]):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _minutes(iv: Interval) -> float:
    return (iv[1] - iv[0]).total_seconds() / 60.0


def tracked_segments(db: Database, day: dt.date, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    """Finished and running time entries clipped to the day, oldest first (a running timer is counted until ``now``)."""
    now = now or now_utc()
    lo, hi = day_bounds(day)
    names = {p.id: p.name for p in db.all(Project)}
    out = []
    for r in db.conn.execute("SELECT * FROM entries WHERE status IN ('done','running') AND start_utc>=? AND start_utc<?", ((lo - dt.timedelta(days=1)).isoformat(), hi.isoformat())):
        e = TimeEntry.from_row(r)
        end = e.end_utc or now
        a, b = max(e.start_utc, lo), min(end, hi)
        if b > a:
            out.append({"start": a, "end": b, "minutes": _minutes((a, b)), "entry_id": e.id, "project_id": e.project_id, "project": names.get(e.project_id or "", ""), "title": e.title,
                        "source": e.source, "billable": e.billable, "running": e.status == Status.RUNNING})
    return sorted(out, key=lambda s: s["start"])


def _hour_minutes(merged: List[Interval], lo: dt.datetime) -> List[float]:
    hours = [0.0] * 24
    for a, b in merged:
        cur = a
        while cur < b:
            k = min(23, int((cur - lo).total_seconds() // 3600))
            nxt = min(b, lo + dt.timedelta(hours=k + 1))
            if nxt <= cur:                                              # defensive: always progress
                break
            hours[k] += _minutes((cur, nxt))
            cur = nxt
    return hours


def day_summary(db: Database, day: dt.date, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    now = now or now_utc()
    lo, hi = day_bounds(day)
    segs = tracked_segments(db, day, now)
    merged = _merge([(s["start"], s["end"]) for s in segs])
    total = sum(_minutes(i) for i in merged)
    by_project: Dict[str, Dict[str, Any]] = {}
    for s in segs:
        row = by_project.setdefault(s["project_id"] or "", {"project_id": s["project_id"], "project": s["project"] or "—", "minutes": 0.0})
        row["minutes"] += s["minutes"]
    projects = sorted(by_project.values(), key=lambda r: -r["minutes"])
    for r in projects:
        r["minutes"] = round(r["minutes"], 1); r["pct"] = round(100 * r["minutes"] / total, 1) if total else 0.0
    gaps = []
    for (a1, b1), (a2, b2) in zip(merged, merged[1:]):
        if _minutes((b1, a2)) >= GAP_MIN:
            gaps.append({"start": b1, "end": a2, "minutes": round(_minutes((b1, a2)), 1)})
    focus, cur = 0.0, None
    for a, b in merged:
        if cur and _minutes((cur[1], a)) < FOCUS_JOIN:
            cur = (cur[0], b)
        else:
            cur = (a, b)
        focus = max(focus, _minutes(cur))
    plans = [(max(e.start_utc, lo), min(e.end_utc, hi)) for e in (TimeEntry.from_row(r) for r in db.conn.execute(
        "SELECT * FROM entries WHERE status='planned' AND column NOT IN ('done','cancelled') AND end_utc IS NOT NULL AND start_utc>=? AND start_utc<?", (lo.isoformat(), hi.isoformat())))]
    events = ce.occurrences(db, lo, hi)
    plan_iv = _merge(plans + [(max(o["start"], lo), min(o["end"], hi)) for o in events if not o["all_day"]])
    planned = sum(_minutes(i) for i in plan_iv)
    on_plan = sum(max(0.0, _minutes((max(a, c), min(b, d)))) for a, b in plan_iv for c, d in merged if min(b, d) > max(a, c))
    return {"date": day, "total_min": round(total, 1), "by_project": projects, "segments": segs, "first": merged[0][0] if merged else None, "last": merged[-1][1] if merged else None,
            "longest_focus_min": round(focus, 1), "gaps": gaps, "unaccounted_min": round(sum(g["minutes"] for g in gaps), 1), "hour_minutes": [round(m, 1) for m in _hour_minutes(merged, lo)],
            "planned_min": round(planned, 1), "on_plan_min": round(on_plan, 1), "adherence_pct": round(100 * on_plan / planned) if planned else None, "events": events,
            "billable_min": round(sum(s["minutes"] for s in segs if s["billable"]), 1), "running": any(s["running"] for s in segs)}


def range_summary(db: Database, start: dt.date, end: dt.date, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """The same numbers over a range, plus the aggregates a statistics panel needs."""
    days: List[Dict[str, Any]] = []
    d = start
    while d <= end:
        days.append(day_summary(db, d, now))
        d += dt.timedelta(days=1)
    proj: Dict[str, Dict[str, Any]] = {}
    titles: Dict[str, float] = {}
    hours = [0.0] * 24
    weekday = [0.0] * 7
    for ds in days:
        weekday[ds["date"].weekday()] += ds["total_min"]
        for h in range(24):
            hours[h] += ds["hour_minutes"][h]
        for p in ds["by_project"]:
            r = proj.setdefault(p["project_id"] or "", {"project_id": p["project_id"], "project": p["project"], "minutes": 0.0})
            r["minutes"] += p["minutes"]
        for s in ds["segments"]:
            titles[s["title"]] = titles.get(s["title"], 0.0) + s["minutes"]
    total = sum(ds["total_min"] for ds in days)
    plist = sorted(proj.values(), key=lambda r: -r["minutes"])
    for r in plist:
        r["minutes"] = round(r["minutes"], 1); r["pct"] = round(100 * r["minutes"] / total, 1) if total else 0.0
    worked = [ds for ds in days if ds["total_min"] > 0]
    best = max(days, key=lambda ds: ds["total_min"]) if days else None
    return {"start": start, "end": end, "days": days, "total_min": round(total, 1), "by_project": plist, "hour_minutes": [round(h, 1) for h in hours], "weekday_minutes": [round(w, 1) for w in weekday],
            "worked_days": len(worked), "avg_per_worked_day_min": round(total / len(worked), 1) if worked else 0.0, "best_day": (best["date"], best["total_min"]) if best and best["total_min"] else None,
            "planned_min": round(sum(ds["planned_min"] for ds in days), 1), "unaccounted_min": round(sum(ds["unaccounted_min"] for ds in days), 1),
            "events_min": round(sum(_minutes((max(o["start"], day_bounds(ds["date"])[0]), min(o["end"], day_bounds(ds["date"])[1]))) for ds in days for o in ds["events"]), 1),
            "top_titles": [{"title": k, "minutes": round(v, 1)} for k, v in sorted(titles.items(), key=lambda kv: -kv[1])[:10]],
            "peak_hour": max(range(24), key=lambda h: hours[h]) if total else None, "longest_focus_min": max((ds["longest_focus_min"] for ds in days), default=0.0)}
