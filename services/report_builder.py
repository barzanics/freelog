"""Full report engine: build once, render anywhere (HTML with inline SVG charts, Markdown, CSV, XLSX, JSON).

Sections: summary + comparison with the previous period, by project / category / sub-category / tag / client, by day / weekday / hour /
month, top tasks, estimates vs actuals, billing, app usage, habits, goals, project health, prompt compliance, screenshots count and the
full entry list. Formats mirror the v5 app (daily / weekly / monthly / custom / summary / detailed / company) and add yearly.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..core import taxonomy
from ..core.database import Database
from ..core.models import Client, Goal, Habit, Project, TimeEntry
from ..core.persian import (MONTHS_FA, TEHRAN, UTC, date_to_jalali, format_duration, format_jalali, jalali_month_length, jalali_to_date,
                            to_fa_digits, to_tehran)
from .analytics import spread_hours, split_by_local_day, streaks
from .billing import Billing

KINDS = ("daily", "weekly", "monthly", "yearly", "custom", "summary", "detailed", "company")
ALL_SECTIONS = ("summary", "by_project", "by_category", "by_subcategory", "by_tag", "by_client", "by_day", "by_weekday", "by_hour", "by_month",
                "top_tasks", "estimates", "billing", "apps", "habits", "goals", "health", "compliance", "screenshots", "entries")
PRESET_SECTIONS: Dict[str, Tuple[str, ...]] = {
    "summary": ("summary", "by_project", "by_category"),
    "daily": ("summary", "by_hour", "by_project", "entries"),
    "weekly": ("summary", "by_day", "by_project", "by_category", "by_weekday", "top_tasks"),
    "monthly": ("summary", "by_day", "by_project", "by_category", "by_tag", "by_weekday", "by_hour", "top_tasks", "estimates", "billing", "compliance"),
    "yearly": ("summary", "by_month", "by_project", "by_category", "by_client", "by_weekday", "by_hour", "top_tasks", "billing", "habits", "goals", "health"),
    "detailed": ALL_SECTIONS, "custom": ("summary", "by_project", "by_category", "by_day", "entries"),
    "company": ("summary", "by_project", "entries"),
}
WEEKDAYS_SAT = ("شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه")
PALETTE = ("#6D5DFC", "#00E5FF", "#FF3D71", "#2ED573", "#FFB020", "#C56CF0", "#FF7A45", "#1E88E5", "#00BFA5", "#E91E63")


@dataclass
class ReportSpec:
    kind: str = "monthly"
    start: dt.date = field(default_factory=dt.date.today)
    end: dt.date = field(default_factory=dt.date.today)          # inclusive
    title: str = ""
    sections: Set[str] = field(default_factory=lambda: set(PRESET_SECTIONS["monthly"]))
    projects: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    billable: Optional[bool] = None
    min_minutes: int = 0
    include_notes: bool = True
    persian_digits: bool = True
    compare_previous: bool = True

    @classmethod
    def preset(cls, kind: str, ref: dt.date) -> "ReportSpec":
        """Period boundaries in the *Jalali* calendar (week = Saturday..Friday)."""
        if kind not in KINDS:
            raise ValueError(f"unknown report kind {kind!r}")
        jy, jm, _ = date_to_jalali(ref)
        if kind == "daily":
            s = e = ref
        elif kind == "weekly":
            s = ref - dt.timedelta(days=(ref.weekday() + 2) % 7); e = s + dt.timedelta(days=6)
        elif kind == "yearly":
            s, e = jalali_to_date(jy, 1, 1), jalali_to_date(jy + 1, 1, 1) - dt.timedelta(days=1)
        else:                                                    # monthly / summary / custom / detailed / company default to the month
            s, e = jalali_to_date(jy, jm, 1), jalali_to_date(jy, jm, jalali_month_length(jy, jm))
        titles = {"daily": "گزارش روزانه", "weekly": "گزارش هفتگی", "monthly": f"گزارش {MONTHS_FA[jm - 1]} {jy}", "yearly": f"گزارش سال {jy}",
                  "summary": "گزارش خلاصه", "detailed": "گزارش تفصیلی", "company": "برگه‌ی ساعت کاری", "custom": "گزارش دلخواه"}
        return cls(kind=kind, start=s, end=e, title=titles[kind], sections=set(PRESET_SECTIONS[kind]))

    def bounds(self) -> Tuple[dt.datetime, dt.datetime]:
        if self.end < self.start:
            raise ValueError("end before start")
        return (dt.datetime.combine(self.start, dt.time(), tzinfo=TEHRAN), dt.datetime.combine(self.end + dt.timedelta(days=1), dt.time(), tzinfo=TEHRAN))


def _matches(e: TimeEntry, spec: ReportSpec) -> bool:
    return ((not spec.projects or e.project_id in spec.projects) and (not spec.categories or e.category in spec.categories)
            and (not spec.tags or any(t in e.tags for t in spec.tags)) and (spec.billable is None or e.billable == spec.billable)
            and e.duration_sec >= spec.min_minutes * 60)


def _top(d: Dict[str, float], n: int = 12) -> List[Tuple[str, float]]:
    return sorted(d.items(), key=lambda kv: -kv[1])[:n]


def build(db: Database, spec: ReportSpec, _with_prev: bool = True) -> Dict[str, Any]:
    """Aggregate everything for ``spec``. Returns a JSON-serialisable dict."""
    lo, hi = spec.bounds()
    projects = {p.id: p for p in db.all(Project)}
    clients = {c.id: c for c in db.all(Client)}
    billing = Billing(db)
    cats = taxonomy.categories(db.get_setting("custom_categories", {}))
    entries = [e for e in db.entries_between(lo - dt.timedelta(days=1), hi) if _matches(e, spec)]
    agg: Dict[str, Dict[str, float]] = {k: {} for k in ("project", "category", "subcategory", "tag", "client", "day", "weekday", "hour", "month")}
    total = billable = 0
    per_task: Dict[str, Tuple[str, float]] = {}
    amounts: Dict[str, float] = {}
    rows: List[Dict[str, Any]] = []
    d0, d1 = spec.start, spec.end
    est_pairs: List[Tuple[int, int]] = []
    for e in entries:
        pieces = [(d, s, c) for d, s, c in split_by_local_day(e) if d0 <= d <= d1]
        if not pieces:
            continue
        p = projects.get(e.project_id or "")
        c = clients.get(p.client_id or "") if p else None
        secs = sum(s for _, s, _ in pieces)
        for day, sec, cs in pieces:
            total += sec
            billable += sec if e.billable else 0
            for key, val in (("project", p.name if p else "بدون پروژه"), ("category", cats.get(e.category, {}).get("name", e.category)),
                             ("client", c.name if c else "—"), ("day", day.isoformat()), ("weekday", str((day.weekday() + 2) % 7)),
                             ("month", str(date_to_jalali(day)[1]))):
                agg[key][val] = agg[key].get(val, 0) + sec
            if e.subcategory:
                agg["subcategory"][e.subcategory] = agg["subcategory"].get(e.subcategory, 0) + sec
            for t in e.tags:
                agg["tag"][t] = agg["tag"].get(t, 0) + sec
            hours = [0] * 24                                            # spread over the clock hours really covered (see analytics.spread_hours)
            spread_hours(hours, cs, sec)
            for h, v in enumerate(hours):
                if v:
                    agg["hour"][str(h)] = agg["hour"].get(str(h), 0) + v
        per_task[e.title] = (e.title, per_task.get(e.title, (e.title, 0))[1] + secs)
        if e.estimated_min and e.duration_sec:
            est_pairs.append((e.estimated_min, e.duration_sec // 60))
        if e.billable:
            cur_code = c.currency if c else (p.currency if p else "IRR")
            amounts[cur_code] = round(amounts.get(cur_code, 0) + secs / 3600 * billing.rate_for(e, p, c), 2)
        rows.append({"id": e.id, "title": e.title, "project": p.name if p else "", "category": cats.get(e.category, {}).get("name", e.category),
                     "subcategory": e.subcategory, "tags": e.tags, "start": to_tehran(e.start_utc).strftime("%Y-%m-%d %H:%M"),
                     "end": to_tehran(e.end_utc).strftime("%Y-%m-%d %H:%M") if e.end_utc else "", "minutes": round(secs / 60, 1),
                     "billable": e.billable, "notes": (e.notes or e.description) if spec.include_notes else ""})
    days = sorted(agg["day"])
    worked_days = [dt.date.fromisoformat(d) for d in days]
    longest, _ = streaks(worked_days) if worked_days else (0, 0)
    n_days = (spec.end - spec.start).days + 1
    data: Dict[str, Any] = {
        "title": spec.title, "kind": spec.kind, "start": spec.start.isoformat(), "end": spec.end.isoformat(), "days_in_period": n_days,
        "summary": {"total_sec": total, "billable_sec": billable, "entries": len(rows), "days_worked": len(days), "avg_per_worked_day_sec": total // len(days) if days else 0,
                    "avg_per_calendar_day_sec": total // n_days, "longest_streak": longest, "busiest_day": max(agg["day"].items(), key=lambda kv: kv[1]) if days else None,
                    "billable_pct": round(100 * billable / total, 1) if total else 0.0},
        "by_project": _top(agg["project"]), "by_category": _top(agg["category"]), "by_subcategory": _top(agg["subcategory"]), "by_tag": _top(agg["tag"]),
        "by_client": _top(agg["client"]), "by_day": [(d, agg["day"][d]) for d in days],
        "by_weekday": [(WEEKDAYS_SAT[i], agg["weekday"].get(str(i), 0)) for i in range(7)],
        "by_hour": [(h, agg["hour"].get(str(h), 0)) for h in range(24)],
        "by_month": [(MONTHS_FA[i], agg["month"].get(str(i + 1), 0)) for i in range(12)],
        "top_tasks": _top({t: s for t, (_, s) in per_task.items()}, 10),
        "estimates": {"pairs": len(est_pairs), "estimated_min": sum(a for a, _ in est_pairs), "actual_min": sum(b for _, b in est_pairs),
                      "accuracy_pct": round(100 * sum(b for _, b in est_pairs) / sum(a for a, _ in est_pairs), 1) if est_pairs else None},
        "billing": {"amounts": amounts, "billable_hours": round(billable / 3600, 2)},
        "entries": sorted(rows, key=lambda r: r["start"]), "sections": sorted(spec.sections),
    }
    # --- extras that need other tables
    data["apps"] = _apps(db, lo, hi)
    data["habits"] = _habits(db, spec)
    data["goals"] = [{"name": g.name, "progress": round(g.progress * 100)} for g in db.all(Goal)]
    from .projects import ProjectService
    ps = ProjectService(db)
    data["health"] = [{"project": p.name, "health": ps.health(p.id), "status": p.status.value} for p in projects.values() if p.status.value in ("active", "planning")]
    data["compliance"] = _compliance(db, lo, hi)
    data["screenshots"] = db.conn.execute("SELECT COUNT(*) FROM screenshots WHERE at>=? AND at<?", (lo.astimezone(UTC).isoformat(), hi.astimezone(UTC).isoformat())).fetchone()[0]
    from .analytics import Analytics
    data["productivity_score"] = Analytics.productivity_score(total, len(days), n_days)
    if spec.compare_previous and _with_prev:
        span = (spec.end - spec.start).days + 1
        prev = ReportSpec(**{**spec.__dict__, "start": spec.start - dt.timedelta(days=span), "end": spec.start - dt.timedelta(days=1), "sections": set(), "compare_previous": False})
        pt = build(db, prev, _with_prev=False)["summary"]["total_sec"]
        data["previous"] = {"total_sec": pt, "change_pct": round(100 * (total - pt) / pt, 1) if pt else None}
    return data


def _apps(db: Database, lo: dt.datetime, hi: dt.datetime) -> List[Tuple[str, int]]:
    from collections import Counter
    c: Counter = Counter()
    for r in db.conn.execute("SELECT app, start_utc, end_utc FROM activity_events WHERE start_utc>=? AND start_utc<?", (lo.astimezone(UTC).isoformat(), hi.astimezone(UTC).isoformat())):
        c[r[0]] += int((dt.datetime.fromisoformat(r[2]) - dt.datetime.fromisoformat(r[1])).total_seconds())
    return c.most_common(10)


def _habits(db: Database, spec: ReportSpec) -> List[Dict[str, Any]]:
    out = []
    for h in db.all(Habit):
        days = [d for d in h.log if spec.start.isoformat() <= d <= spec.end.isoformat()]
        want = sum(1 for i in range((spec.end - spec.start).days + 1) if (spec.start + dt.timedelta(days=i)).weekday() in h.days)
        out.append({"name": h.name, "done": len(days), "expected": want, "pct": round(100 * len(days) / want) if want else 0})
    return out


def _compliance(db: Database, lo: dt.datetime, hi: dt.datetime) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for r in db.conn.execute("SELECT action FROM prompt_log WHERE shown_at>=? AND shown_at<?", (lo.astimezone(UTC).isoformat(), hi.astimezone(UTC).isoformat())):
        counts[r[0] or "unanswered"] = counts.get(r[0] or "unanswered", 0) + 1
    tot = sum(counts.values())
    return {"counts": counts, "total": tot, "rate_pct": round(100 * (counts.get("logged", 0) + counts.get("away", 0)) / tot, 1) if tot else None}


# ====================================================================== SVG charts (no external libs)
def _e(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _fa(s: Any, on: bool = True) -> str:
    return to_fa_digits(s) if on else str(s)


def svg_bars(items: List[Tuple[str, float]], w: int = 720, h: int = 220, color: str = "#6D5DFC", unit: float = 3600.0, fa: bool = True) -> str:
    if not items:
        return ""
    mx = max(v for _, v in items) or 1
    n = len(items)
    bw = (w - 20) / n
    step = max(1, math.ceil(n / 16))
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">']
    for i, (lab, v) in enumerate(items):
        bh = (h - 50) * v / mx
        x, y = 10 + i * bw, h - 28 - bh
        out.append(f'<rect x="{x + bw * 0.12:.1f}" y="{y:.1f}" width="{bw * 0.76:.1f}" height="{max(bh, 0.5):.1f}" rx="4" fill="{color}" opacity="0.88"/>')
        if v and (n <= 16 or i % step == 0):
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y - 4:.1f}" font-size="9" text-anchor="middle" fill="#555">{_fa(round(v / unit, 1), fa)}</text>')
        if i % step == 0:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{h - 12}" font-size="9" text-anchor="middle" fill="#777">{_e(_fa(lab[-5:] if len(lab) > 8 and "-" in lab else lab, fa))}</text>')
    return "".join(out) + "</svg>"


def svg_hbars(items: List[Tuple[str, float]], w: int = 720, unit: float = 3600.0, fa: bool = True) -> str:
    if not items:
        return ""
    mx = max(v for _, v in items) or 1
    rowh = 26
    h = rowh * len(items) + 8
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">']
    for i, (lab, v) in enumerate(items):
        y = 4 + i * rowh
        bw = (w - 260) * v / mx
        col = PALETTE[i % len(PALETTE)]
        out.append(f'<rect x="{w - 250 - bw:.1f}" y="{y + 4}" width="{max(bw, 1):.1f}" height="{rowh - 10}" rx="5" fill="{col}" opacity="0.9"/>')
        out.append(f'<text x="{w - 6}" y="{y + 17}" font-size="11" text-anchor="end" fill="#333">{_e(_fa(lab[:28], fa))}</text>')
        out.append(f'<text x="{w - 256 - bw:.1f}" y="{y + 17}" font-size="10" text-anchor="end" fill="#666">{_fa(round(v / unit, 1), fa)}</text>')
    return "".join(out) + "</svg>"


def svg_donut(items: List[Tuple[str, float]], size: int = 190, fa: bool = True) -> str:
    total = sum(v for _, v in items)
    if total <= 0:
        return ""
    r, circ = 70.0, 2 * math.pi * 70.0
    out = [f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" xmlns="http://www.w3.org/2000/svg"><g transform="rotate(-90 {size / 2} {size / 2})">']
    off = 0.0
    for i, (_, v) in enumerate(items):
        ln = circ * v / total
        out.append(f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" fill="none" stroke="{PALETTE[i % len(PALETTE)]}" stroke-width="26" stroke-dasharray="{ln:.2f} {circ - ln:.2f}" stroke-dashoffset="{-off:.2f}"/>')
        off += ln
    out.append(f'</g><text x="{size / 2}" y="{size / 2 + 5}" text-anchor="middle" font-size="15" font-weight="700" fill="#333">{_fa(round(total / 3600, 1), fa)}h</text></svg>')
    return "".join(out)


def svg_heat(matrix: List[List[float]], fa: bool = True) -> str:
    """7 rows (Sat..Fri) x 24 columns."""
    mx = max((v for r in matrix for v in r), default=0) or 1
    cw, ch, left = 26, 22, 70
    out = [f'<svg viewBox="0 0 {left + 24 * cw} {7 * ch + 22}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">']
    for r in range(7):
        out.append(f'<text x="{left - 6}" y="{r * ch + 15}" font-size="10" text-anchor="end" fill="#555">{WEEKDAYS_SAT[r]}</text>')
        for c in range(24):
            a = matrix[r][c] / mx
            out.append(f'<rect x="{left + c * cw + 1}" y="{r * ch + 1}" width="{cw - 2}" height="{ch - 2}" rx="4" fill="#6D5DFC" opacity="{0.07 + 0.93 * a:.2f}"/>')
    for c in range(0, 24, 3):
        out.append(f'<text x="{left + c * cw + cw / 2}" y="{7 * ch + 14}" font-size="9" text-anchor="middle" fill="#777">{_fa(c, fa)}</text>')
    return "".join(out) + "</svg>"


def svg_line(points: List[float], w: int = 720, h: int = 160, color: str = "#00BFA5") -> str:
    if len(points) < 2:
        return ""
    mx = max(points) or 1
    xs = [10 + (w - 20) * i / (len(points) - 1) for i in range(len(points))]
    ys = [h - 12 - (h - 24) * p / mx for p in points]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"10,{h - 12} {pts} {w - 10},{h - 12}"
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg"><polygon points="{area}" fill="{color}" opacity="0.15"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/></svg>')


# ====================================================================== renderers
def _hm(sec: float, fa: bool) -> str:
    return _fa(format_duration(int(sec)), fa)


def _table(head: List[str], rows: List[List[Any]], fa: bool) -> str:
    th = "".join(f"<th>{_e(h)}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td>{_e(_fa(c, fa))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{body}</table>"


def _day_label(iso: str, fa: bool) -> str:
    return format_jalali(dt.date.fromisoformat(iso), "{m:02d}/{d:02d}", fa_digits=fa)


def to_html(data: Dict[str, Any], fa: bool = True) -> str:
    """One self-contained RTL page (print it to get a PDF with perfect Persian shaping)."""
    s, secs = data["summary"], set(data["sections"])
    parts: List[str] = []
    if "summary" in secs:
        prev = data.get("previous") or {}
        chg = "" if prev.get("change_pct") is None else f'<div class="sub">{"▲" if prev["change_pct"] >= 0 else "▼"} {_fa(abs(prev["change_pct"]), fa)}٪ نسبت به دوره‌ی قبل</div>'
        cards = [("جمع ساعت", _hm(s["total_sec"], fa), chg), ("روزهای کاری", _fa(s["days_worked"], fa), f'از {_fa(data["days_in_period"], fa)} روز'),
                 ("میانگین روز کاری", _hm(s["avg_per_worked_day_sec"], fa), ""), ("قابل صورتحساب", _fa(f'{s["billable_pct"]}٪', fa), _hm(s["billable_sec"], fa)),
                 ("بیشترین رشته", _fa(s["longest_streak"], fa), "روز پیاپی"), ("امتیاز بهره‌وری", _fa(data["productivity_score"], fa), "از ۱۰۰")]
        parts.append('<div class="cards">' + "".join(f'<div class="card"><div class="k">{_e(k)}</div><div class="v">{v}</div>{sub}</div>' for k, v, sub in cards) + "</div>")
        if s["busiest_day"]:
            parts.append(f'<p class="note">پرکارترین روز: {_e(_day_label(s["busiest_day"][0], fa))} با {_hm(s["busiest_day"][1], fa)} ساعت</p>')
    if "by_day" in secs and data["by_day"]:
        parts.append("<h2>ساعت کار هر روز</h2>" + svg_bars([(_day_label(d, fa), v) for d, v in data["by_day"]], fa=fa))
        cum, acc = [], 0
        for _, v in data["by_day"]:
            acc += v; cum.append(acc / 3600)
        parts.append("<h3>جمع تجمعی</h3>" + svg_line(cum))
    if "by_month" in secs and any(v for _, v in data["by_month"]):
        parts.append("<h2>ساعت هر ماه</h2>" + svg_bars(data["by_month"], fa=fa))
    for key, title, donut in (("by_project", "به تفکیک پروژه", True), ("by_category", "به تفکیک دسته", True), ("by_subcategory", "به تفکیک زیردسته", False),
                              ("by_tag", "به تفکیک برچسب", False), ("by_client", "به تفکیک مشتری", False)):
        if key in secs and data[key]:
            tot = sum(v for _, v in data[key]) or 1
            tbl = _table(["نام", "ساعت", "درصد"], [[n, format_duration(int(v)), f"{round(100 * v / tot)}٪"] for n, v in data[key]], fa)
            parts.append(f"<h2>{title}</h2><div class='row'>{svg_donut(data[key], fa=fa) if donut else ''}<div class='grow'>{svg_hbars(data[key][:10], fa=fa)}</div></div>{tbl}")
    if "by_weekday" in secs and any(v for _, v in data["by_weekday"]):
        parts.append("<h2>روزهای هفته</h2>" + svg_bars(data["by_weekday"], color="#00E5FF", fa=fa))
    if "by_hour" in secs and any(v for _, v in data["by_hour"]):
        parts.append("<h2>ساعت‌های روز</h2>" + svg_bars([(str(h), v) for h, v in data["by_hour"]], color="#FF3D71", fa=fa))
    if "top_tasks" in secs and data["top_tasks"]:
        parts.append("<h2>پرزمان‌ترین کارها</h2>" + _table(["کار", "ساعت"], [[n, format_duration(int(v))] for n, v in data["top_tasks"]], fa))
    if "estimates" in secs and data["estimates"]["pairs"]:
        e = data["estimates"]
        parts.append(f"<h2>تخمین در برابر واقعیت</h2><p>{_fa(e['pairs'], fa)} کار با تخمین: تخمین {_fa(e['estimated_min'], fa)} دقیقه، واقعی {_fa(e['actual_min'], fa)} دقیقه "
                     f"(<b>{_fa(e['accuracy_pct'], fa)}٪</b> از تخمین).</p>")
    if "billing" in secs and data["billing"]["amounts"]:
        parts.append("<h2>صورتحساب</h2>" + _table(["ارز", "مبلغ قابل دریافت"], [[k, f"{v:,.0f}"] for k, v in data["billing"]["amounts"].items()], fa)
                     + f"<p>ساعت قابل صورتحساب: {_fa(data['billing']['billable_hours'], fa)}</p>")
    if "apps" in secs and data["apps"]:
        parts.append("<h2>برنامه‌های پرکاربرد</h2>" + svg_hbars([(a, v) for a, v in data["apps"]], unit=3600, fa=fa))
    if "habits" in secs and data["habits"]:
        parts.append("<h2>عادت‌ها</h2>" + _table(["عادت", "انجام", "هدف", "درصد"], [[h["name"], h["done"], h["expected"], f'{h["pct"]}٪'] for h in data["habits"]], fa))
    if "goals" in secs and data["goals"]:
        parts.append("<h2>اهداف</h2>" + _table(["هدف", "پیشرفت"], [[g["name"], f'{g["progress"]}٪'] for g in data["goals"]], fa))
    if "health" in secs and data["health"]:
        names = {"on_track": "طبق برنامه", "at_risk": "در معرض خطر", "off_track": "عقب‌افتاده"}
        parts.append("<h2>سلامت پروژه‌ها</h2>" + _table(["پروژه", "وضعیت"], [[h["project"], names.get(h["health"], h["health"])] for h in data["health"]], fa))
    if "compliance" in secs and data["compliance"]["total"]:
        c = data["compliance"]
        parts.append(f"<h2>پایبندی به ثبت کار</h2><p>{_fa(c['total'], fa)} یادآور نمایش داده شد؛ نرخ پاسخ‌گویی <b>{_fa(c['rate_pct'], fa)}٪</b>.</p>")
    if "screenshots" in secs and data["screenshots"]:
        parts.append(f"<p class='note'>{_fa(data['screenshots'], fa)} اسکرین‌شات در این دوره ذخیره شده است.</p>")
    if "entries" in secs and data["entries"]:
        rows = [[r["start"], r["end"][-5:], r["title"], r["project"], r["category"], ("، ".join(r["tags"])), format_duration(int(r["minutes"] * 60)),
                 "✓" if r["billable"] else ""] + ([r["notes"]] if any(x["notes"] for x in data["entries"]) else []) for r in data["entries"]]
        head = ["شروع", "پایان", "عنوان", "پروژه", "دسته", "برچسب", "مدت", "قابل صورتحساب"] + (["یادداشت"] if any(x["notes"] for x in data["entries"]) else [])
        parts.append("<h2>فهرست کامل</h2>" + _table(head, rows, fa))
    if data["kind"] == "company":
        parts.append('<div class="sign"><div>نام و امضای کارمند</div><div>تأییدیه‌ی مدیر</div></div>')
    css = ("@font-face{font-family:'IRANSans';src:local('IRANSans'),local('IRANSansWeb'),local('IRANSansX')}"
           "body{font-family:'IRANSans','Vazirmatn',Tahoma,sans-serif;margin:32px auto;max-width:900px;color:#1d1d2b;line-height:1.8}"
           "h1{font-size:24px;border-bottom:3px solid #6D5DFC;padding-bottom:8px}h2{font-size:17px;margin-top:30px;color:#4b3fd1}h3{font-size:13px;color:#777}"
           ".cards{display:flex;flex-wrap:wrap;gap:12px}.card{flex:1 1 130px;border:1px solid #e3e3f0;border-radius:14px;padding:12px;background:#fafaff}"
           ".k{font-size:12px;color:#777}.v{font-size:22px;font-weight:700}.sub{font-size:11px;color:#2c8}.row{display:flex;gap:14px;align-items:center}.grow{flex:1}"
           "table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}td,th{border-bottom:1px solid #eee;padding:5px 6px;text-align:right}"
           "th{background:#f3f2ff}.note{color:#666;font-size:12px}.sign{display:flex;justify-content:space-around;margin-top:60px}.sign div{border-top:1px solid #333;padding-top:6px;width:30%;text-align:center}"
           "@media print{body{margin:10mm}}")
    period = f"{format_jalali(dt.date.fromisoformat(data['start']), fa_digits=fa)} تا {format_jalali(dt.date.fromisoformat(data['end']), fa_digits=fa)}"
    return (f"<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'><title>{_e(data['title'])}</title><style>{css}</style>"
            f"<h1>{_e(data['title'])}</h1><p class='note'>{period}</p>" + "\n".join(parts) + "</html>")


def to_markdown(data: Dict[str, Any], fa: bool = True) -> str:
    s = data["summary"]
    out = [f"# {data['title']}", f"{data['start']} → {data['end']}", "", f"- جمع ساعت: **{format_duration(s['total_sec'])}**", f"- روزهای کاری: **{s['days_worked']}** از {data['days_in_period']}",
           f"- میانگین روز کاری: **{format_duration(s['avg_per_worked_day_sec'])}**", f"- قابل صورتحساب: **{s['billable_pct']}٪**", f"- امتیاز بهره‌وری: **{data['productivity_score']}**"]
    prev = data.get("previous") or {}
    if prev.get("change_pct") is not None:
        out.append(f"- نسبت به دوره‌ی قبل: **{prev['change_pct']}٪**")
    for key, title in (("by_project", "پروژه‌ها"), ("by_category", "دسته‌ها"), ("by_tag", "برچسب‌ها"), ("by_client", "مشتریان"), ("top_tasks", "پرزمان‌ترین کارها")):
        if key in data["sections"] and data[key]:
            out += ["", f"## {title}", "| نام | ساعت |", "|---|---|"] + [f"| {n.replace('|', '/')} | {format_duration(int(v))} |" for n, v in data[key]]
    if "entries" in data["sections"] and data["entries"]:
        out += ["", "## فهرست", "| شروع | عنوان | پروژه | مدت |", "|---|---|---|---|"] + [f"| {r['start']} | {r['title'].replace('|', '/')} | {r['project'].replace('|', '/')} | {format_duration(int(r['minutes'] * 60))} |" for r in data["entries"]]
    text = "\n".join(out)
    return to_fa_digits(text) if fa else text


def _safe(c: Any) -> Any:
    return "'" + c if isinstance(c, str) and c[:1] in ("=", "+", "-", "@") else c


def to_csv(data: Dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["start", "end", "title", "project", "category", "subcategory", "tags", "minutes", "billable", "notes"])
    for r in data["entries"]:
        w.writerow([_safe(x) for x in (r["start"], r["end"], r["title"], r["project"], r["category"], r["subcategory"], ";".join(r["tags"]), r["minutes"], int(r["billable"]), r["notes"])])
    return buf.getvalue()


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=1, default=str)


def to_xlsx(data: Dict[str, Any], dest: Union[str, Path]) -> Path:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "خلاصه"
    ws.sheet_view.rightToLeft = True
    s = data["summary"]
    for row in (["عنوان", data["title"]], ["از", data["start"]], ["تا", data["end"]], ["جمع ساعت", round(s["total_sec"] / 3600, 2)], ["روزهای کاری", s["days_worked"]],
                ["قابل صورتحساب (ساعت)", round(s["billable_sec"] / 3600, 2)], ["امتیاز بهره‌وری", data["productivity_score"]]):
        ws.append([_safe(x) for x in row])
    for key, name in (("by_project", "پروژه"), ("by_category", "دسته"), ("by_tag", "برچسب"), ("by_client", "مشتری"), ("by_day", "روز"), ("by_hour", "ساعت"), ("by_weekday", "هفته")):
        sh = wb.create_sheet(name); sh.sheet_view.rightToLeft = True
        sh.append(["نام", "ساعت"])
        for n, v in data[key]:
            sh.append([_safe(str(n)), round(v / 3600, 2)])
    sh = wb.create_sheet("فهرست"); sh.sheet_view.rightToLeft = True
    sh.append(["شروع", "پایان", "عنوان", "پروژه", "دسته", "برچسب", "دقیقه", "قابل صورتحساب"])
    for r in data["entries"]:
        sh.append([_safe(x) for x in (r["start"], r["end"], r["title"], r["project"], r["category"], ";".join(r["tags"]), r["minutes"], int(r["billable"]))])
    wb.save(str(dest))
    return Path(dest)


def save(data: Dict[str, Any], dest: Union[str, Path], fmt: str, fa: bool = True) -> Path:
    """Write a report in ``fmt``: html / md / csv / json / xlsx."""
    dest = Path(dest)
    if fmt == "xlsx":
        return to_xlsx(data, dest)
    text = {"html": lambda: to_html(data, fa), "md": lambda: to_markdown(data, fa), "csv": lambda: to_csv(data), "json": lambda: to_json(data)}.get(fmt)
    if text is None:
        raise ValueError(f"unknown format {fmt!r}")
    dest.write_text(text(), encoding="utf-8-sig" if fmt == "csv" else "utf-8")
    return dest
