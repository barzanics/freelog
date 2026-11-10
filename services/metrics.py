"""Funnels, client cohorts, custom KPIs and saved dashboards."""
from __future__ import annotations

from typing import Dict, List

from ..core.database import Database
from ..core.models import Client, Invoice, Project, TimeEntry
from .analytics import Analytics
from .extras import evaluate_formula

WIDGETS = ("hero", "timer", "tip", "heatmap", "donut", "bars", "pomodoro", "analytics_text")


def funnel(db: Database) -> Dict[str, int]:
    """Task lifecycle counts: planned -> started (in progress/review/running or has time) -> completed."""
    planned = started = done = 0
    for e in db.all(TimeEntry):
        if e.parent_id:
            continue
        planned += 1
        if e.column in ("in_progress", "review", "done") or e.duration_sec > 0 or e.status.value in ("running", "done"):
            started += 1
        if e.status.value == "done":
            done += 1
    return {"planned": planned, "started": started, "completed": done}


def client_cohorts(db: Database) -> Dict[str, Dict[str, float]]:
    """First-time clients (<=1 invoice) vs repeat clients (>=2): count, hours and billed total."""
    inv_count: Dict[str, int] = {}
    billed: Dict[str, float] = {}
    for i in db.all(Invoice):
        inv_count[i.client_id] = inv_count.get(i.client_id, 0) + 1
        billed[i.client_id] = billed.get(i.client_id, 0.0) + i.total
    hours: Dict[str, float] = {}
    pc = {p.id: p.client_id for p in db.all(Project)}
    for e in db.all(TimeEntry):
        cid = pc.get(e.project_id or "")
        if cid:
            hours[cid] = hours.get(cid, 0.0) + e.duration_sec / 3600
    out = {"first_time": {"clients": 0, "hours": 0.0, "billed": 0.0}, "repeat": {"clients": 0, "hours": 0.0, "billed": 0.0}}
    for c in db.all(Client):
        k = "repeat" if inv_count.get(c.id, 0) >= 2 else "first_time"
        out[k]["clients"] += 1
        out[k]["hours"] = round(out[k]["hours"] + hours.get(c.id, 0.0), 2)
        out[k]["billed"] = round(out[k]["billed"] + billed.get(c.id, 0.0), 2)
    return out


# ---- custom KPIs ----------------------------------------------------------
def define_kpi(db: Database, name: str, formula: str) -> None:
    """Formula over: total_hours, billable_hours, days_worked, avg_day, billable_pct. Validated on save."""
    evaluate_formula(formula, {"total_hours": 1, "billable_hours": 1, "days_worked": 1, "avg_day": 1, "billable_pct": 1})
    k = db.get_setting("kpis", {})
    k[name] = formula
    db.set_setting("kpis", k)


def evaluate_kpis(db: Database, jalali_year: int) -> Dict[str, float]:
    s = Analytics(db).year_summary(jalali_year)
    v = {"total_hours": s.total_hours, "billable_hours": round(s.billable_sec / 3600, 2), "days_worked": float(s.days_worked),
         "avg_day": s.avg_hours_per_worked_day, "billable_pct": round(100 * s.billable_sec / s.total_sec, 1) if s.total_sec else 0.0}
    out = {}
    for name, f in db.get_setting("kpis", {}).items():
        try:
            out[name] = round(evaluate_formula(f, v), 2)
        except ValueError:
            out[name] = float("nan")
    return out


# ---- saved dashboards -------------------------------------------------------
def save_dashboard(db: Database, name: str, widgets: List[str]) -> None:
    bad = [w for w in widgets if w not in WIDGETS]
    if bad or not name.strip():
        raise ValueError(f"invalid dashboard: {bad or 'name'}")
    d = db.get_setting("dashboards", {})
    d[name] = list(dict.fromkeys(widgets))      # order kept, duplicates removed
    db.set_setting("dashboards", d)


def get_dashboard(db: Database, name: str) -> List[str]:
    return db.get_setting("dashboards", {}).get(name, list(WIDGETS))
