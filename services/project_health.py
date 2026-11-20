"""Project progress and health for client reporting: weighted progress, RAG status *with reasons*, blockers, stale tasks, scope-creep tracking, budget / retainer alerts,
effective hourly rate, velocity-based forecast and US-holiday deadline warnings. Everything is computed from your entries / milestones; nothing is typed in twice."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from ..core.crm import Store
from ..core.database import Database
from ..core.models import Client, Invoice, InvoiceStatus, Project, Status, TimeEntry
from ..core.persian import UTC, now_utc
from ..reports import locale_us as us

DONE_MS = ("done", "accepted", "completed")


# ------------------------------------------------------------------ helpers
def project_tasks(db: Database, pid: str) -> List[TimeEntry]:
    return [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE project_id=? AND column != 'cancelled'", (pid,))]


def is_done(e: TimeEntry) -> bool:
    return e.column == "done" or e.status == Status.DONE


def size_min(e: TimeEntry) -> int:
    """A task's weight: its estimate, else the time already logged, else 30 minutes (so unestimated work still counts)."""
    return e.estimated_min or e.duration_sec // 60 or 30


def leaves(tasks: List[TimeEntry]) -> List[TimeEntry]:
    """Work that can actually be finished: sub-tasks when a task has them, the task itself otherwise."""
    kids: Dict[str, List[TimeEntry]] = {}
    for t in tasks:
        if t.parent_id:
            kids.setdefault(t.parent_id, []).append(t)
    out: List[TimeEntry] = []
    for t in tasks:
        if t.parent_id:
            continue
        out += kids.get(t.id) or [t]
    return out


def _day(t: Optional[dt.datetime]) -> Optional[dt.date]:
    return t.astimezone(UTC).date() if t else None


def _frac(ts: List[TimeEntry]) -> float:
    total = sum(size_min(t) for t in ts)
    return sum(size_min(t) for t in ts if is_done(t)) / total if total else 0.0


# ------------------------------------------------------------------ progress
def weighted_progress(db: Database, pid: str) -> Dict[str, Any]:
    """Milestone-weighted progress (0-100). Without milestones: estimate-weighted share of finished work. Tasks outside every milestone form one extra bucket."""
    st = Store(db)
    tasks = project_tasks(db, pid)
    lv = leaves(tasks)
    ms_rows = st.rows("milestones", "project_id=?", (pid,), "ord, due")
    buckets, used = [], set()
    for m in ms_rows:
        own = [t for t in tasks if t.extra.get("phase") == m["id"]]
        own_leaves = leaves(own)
        used.update(t.id for t in own)
        finished = bool(m.get("completed")) or m.get("status") in DONE_MS
        pct = 100.0 if finished else (100 * _frac(own_leaves) if own_leaves else 0.0)
        buckets.append({"id": m["id"], "name": m["name"], "weight": float(m.get("weight") or 1.0), "pct": round(pct, 1), "due": m.get("due"), "status": "done" if finished else (m.get("status") or "pending"),
                        "tasks": len(own_leaves), "done": sum(1 for t in own_leaves if is_done(t))})
    rest = [t for t in lv if t.id not in used and not (t.parent_id and any(t.parent_id == u for u in used))]
    if buckets:
        total_w = sum(b["weight"] for b in buckets) + (1.0 if rest else 0.0)
        pct = (sum(b["weight"] * b["pct"] for b in buckets) + (100 * _frac(rest) if rest else 0.0)) / total_w if total_w else 0.0
    else:
        pct = 100 * _frac(lv)
    return {"pct": round(pct, 1), "milestones": buckets, "tasks_total": len(lv), "tasks_done": sum(1 for t in lv if is_done(t)),
            "hours_total": round(sum(size_min(t) for t in lv) / 60, 1), "hours_done": round(sum(size_min(t) for t in lv if is_done(t)) / 60, 1)}


# ------------------------------------------------------------------ blockers / stale / scope
def set_blocked(db: Database, entry_id: str, reason: str = "", by: str = "client", now: Optional[dt.datetime] = None) -> TimeEntry:
    """Mark a task blocked (column 'delayed'); ``by`` is 'client' (waiting on the client) or 'internal'."""
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.column = "delayed"
    e.extra = {**e.extra, "blocked_since": (now or now_utc()).isoformat(), "blocked_reason": reason, "blocked_by": by}
    db.save(e)
    return e


def unblock(db: Database, entry_id: str) -> TimeEntry:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.column = "in_progress" if e.status == Status.RUNNING else "backlog"
    e.extra = {k: v for k, v in e.extra.items() if not k.startswith("blocked_")}
    db.save(e)
    return e


def blockers(db: Database, pid: str, aging_days: int = 3, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    now = now or now_utc()
    out = []
    for t in project_tasks(db, pid):
        if t.column != "delayed" or is_done(t):
            continue
        since = dt.datetime.fromisoformat(t.extra["blocked_since"]) if t.extra.get("blocked_since") else t.updated_at
        days = (now - since).days
        out.append({"id": t.id, "title": t.title, "reason": t.extra.get("blocked_reason", ""), "by": t.extra.get("blocked_by", "internal"), "days": days, "aged": days >= aging_days})
    return sorted(out, key=lambda b: -b["days"])


def stale_tasks(db: Database, pid: str, days: int = 14, now: Optional[dt.datetime] = None) -> List[TimeEntry]:
    now = now or now_utc()
    return [t for t in project_tasks(db, pid) if not t.parent_id and not is_done(t) and t.column != "delayed" and (now - t.updated_at).days >= days]


def set_baseline(db: Database, pid: str, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Freeze the agreed scope: the current task ids and total hours. Later additions are measured against it."""
    tasks = [t for t in project_tasks(db, pid) if not t.parent_id]
    base = {"task_ids": [t.id for t in tasks], "hours": round(sum(size_min(t) for t in tasks) / 60, 2), "set_at": (now or now_utc()).isoformat()}
    Store(db).update("projects", pid, baseline=base)
    return base


def scope_creep(db: Database, pid: str) -> Dict[str, Any]:
    """Work added after the baseline - the evidence for "that was outside the original scope"."""
    base = (Store(db).get("projects", pid) or {}).get("baseline") or {}
    if not base.get("task_ids") and not base.get("set_at"):
        return {"has_baseline": False, "added": [], "added_hours": 0.0, "baseline_hours": 0.0, "pct": 0.0, "flag": False}
    known = set(base.get("task_ids", []))
    added = [t for t in project_tasks(db, pid) if not t.parent_id and t.id not in known]
    ah = round(sum(size_min(t) for t in added) / 60, 2)
    bh = float(base.get("hours") or 0)
    pct = round(100 * ah / bh, 1) if bh else (100.0 if ah else 0.0)
    return {"has_baseline": True, "added": [{"id": t.id, "title": t.title, "hours": round(size_min(t) / 60, 2)} for t in added], "added_hours": ah, "baseline_hours": bh, "pct": pct, "flag": pct > 10}


# ------------------------------------------------------------------ money & time budgets
def _rate(db: Database, p: Project) -> float:
    if p.rate_per_hour:
        return p.rate_per_hour
    c = db.get(Client, p.client_id) if p.client_id else None
    return c.default_rate if c else 0.0


def budget_status(db: Database, pid: str) -> Dict[str, Any]:
    p = db.get(Project, pid)
    if p is None:
        raise KeyError(pid)
    secs = db.conn.execute("SELECT COALESCE(SUM(duration_sec),0) FROM entries WHERE project_id=? AND billable=1 AND status='done'", (pid,)).fetchone()[0]
    hours, amount = secs / 3600, secs / 3600 * _rate(db, p)
    pct_h = round(100 * hours / p.estimated_hours, 1) if p.estimated_hours else None
    pct_a = round(100 * amount / p.budget, 1) if p.budget else None
    worst = max([x for x in (pct_h, pct_a) if x is not None], default=0.0)
    return {"hours_used": round(hours, 2), "hours_budget": p.estimated_hours, "hours_pct": pct_h, "amount_used": round(amount, 2), "amount_budget": p.budget, "amount_pct": pct_a,
            "currency": p.currency, "crossed": [t for t in (75, 90, 100) if worst >= t]}


def new_budget_alerts(db: Database, pid: str) -> List[int]:
    """Thresholds (75 / 90 / 100 %) crossed since the last call - so each notification fires exactly once."""
    seen = db.get_setting("budget_alerts", {})
    now_crossed = budget_status(db, pid)["crossed"]
    fresh = [t for t in now_crossed if t not in seen.get(pid, [])]
    if fresh:
        seen[pid] = sorted(set(seen.get(pid, [])) | set(now_crossed))
        db.set_setting("budget_alerts", seen)
    return fresh


def retainer_status(db: Database, client_id: str, month_start: dt.date) -> Dict[str, Any]:
    c = db.get(Client, client_id)
    if c is None:
        raise KeyError(client_id)
    end = dt.date(month_start.year + (month_start.month == 12), month_start.month % 12 + 1, 1)
    lo, hi = (dt.datetime.combine(d, dt.time(), tzinfo=UTC).isoformat() for d in (month_start, end))
    secs = db.conn.execute("SELECT COALESCE(SUM(e.duration_sec),0) FROM entries e JOIN projects p ON p.id=e.project_id WHERE p.client_id=? AND e.status='done' AND e.start_utc>=? AND e.start_utc<?",
                           (client_id, lo, hi)).fetchone()[0]
    ret = float((Store(db).get("clients", client_id) or {}).get("retainer_hours") or 0)
    used = secs / 3600
    return {"retainer_hours": ret, "used_hours": round(used, 2), "remaining_hours": round(max(0.0, ret - used), 2), "pct": round(100 * used / ret, 1) if ret else None, "over": bool(ret and used > ret)}


def effective_rate(db: Database, client_id: str, start: dt.date, end: dt.date) -> Optional[float]:
    """Revenue invoiced in the period divided by the hours really worked for the client in it (None without hours)."""
    lo, hi = (dt.datetime.combine(d, dt.time(), tzinfo=UTC) for d in (start, end + dt.timedelta(days=1)))
    revenue = sum(i.total for i in (Invoice.from_row(r) for r in db.conn.execute("SELECT * FROM invoices WHERE client_id=? AND issued_at>=? AND issued_at<?", (client_id, lo.isoformat(), hi.isoformat()))))
    secs = db.conn.execute("SELECT COALESCE(SUM(e.duration_sec),0) FROM entries e JOIN projects p ON p.id=e.project_id WHERE p.client_id=? AND e.status='done' AND e.start_utc>=? AND e.start_utc<?",
                           (client_id, lo.isoformat(), hi.isoformat())).fetchone()[0]
    return round(revenue / (secs / 3600), 2) if secs else None


# ------------------------------------------------------------------ forecast, holidays, health
def forecast(db: Database, pid: str, now: Optional[dt.datetime] = None, window_days: int = 28) -> Dict[str, Any]:
    """Projected finish from recent velocity (hours of work completed per week over the last ``window_days``), counted in US business days."""
    now = now or now_utc()
    lv = leaves(project_tasks(db, pid))
    remaining = sum(size_min(t) for t in lv if not is_done(t)) / 60
    cutoff = now - dt.timedelta(days=window_days)
    done_recent = sum(size_min(t) for t in lv if is_done(t) and t.completed_at and t.completed_at >= cutoff) / 60
    vel = done_recent / (window_days / 7)
    p = db.get(Project, pid)
    out: Dict[str, Any] = {"remaining_hours": round(remaining, 1), "velocity_hours_per_week": round(vel, 1), "projected_date": None, "late_days": None}
    if remaining <= 0:
        out["projected_date"] = _day(now)
        return out
    if vel > 0:
        weeks = remaining / vel
        proj = us.add_business_days(_day(now), max(1, int(round(weeks * 5))))
        out["projected_date"] = proj
        if p and p.deadline:
            out["late_days"] = (proj - _day(p.deadline)).days
    return out


def holiday_warnings(db: Database, pid: str, tz: str = "America/New_York") -> List[Dict[str, Any]]:
    """Open tasks / milestones whose due date lands on a US holiday or weekend in the client's time zone."""
    out = []
    for t in project_tasks(db, pid):
        if t.due_utc and not is_done(t):
            d = us.to_client_tz(t.due_utc, tz).date()
            name = us.holiday_name(d) or ("weekend" if d.weekday() >= 5 else None)
            if name:
                out.append({"kind": "task", "title": t.title, "date": d, "why": name})
    for m in Store(db).rows("milestones", "project_id=? AND completed=0", (pid,)):
        if m.get("due"):
            d = us.to_client_tz(dt.datetime.fromisoformat(m["due"]), tz).date()
            name = us.holiday_name(d) or ("weekend" if d.weekday() >= 5 else None)
            if name:
                out.append({"kind": "milestone", "title": m["name"], "date": d, "why": name})
    return out


def health(db: Database, pid: str, now: Optional[dt.datetime] = None, aging_days: int = 3) -> Dict[str, Any]:
    """RAG status with the reasons behind it. on_track: not more than 10 points behind the schedule; at_risk: 10-20 behind; off_track: more - then overdue milestones,
    budget overruns and aged blockers can only make it worse."""
    now = now or now_utc()
    p = db.get(Project, pid)
    if p is None:
        raise KeyError(pid)
    prog = weighted_progress(db, pid)
    actual = prog["pct"]
    reasons: List[Dict[str, str]] = []
    status = "on_track"
    planned: Optional[float] = None
    start = _day(p.start) or _day(p.created_at)
    if p.deadline and start and _day(p.deadline) > start:
        span = (_day(p.deadline) - start).days
        planned = round(100 * max(0.0, min(1.0, (_day(now) - start).days / span)), 1)
    gap = round(planned - actual, 1) if planned is not None else 0.0
    rank = {"on_track": 0, "at_risk": 1, "off_track": 2}

    def worsen(to: str, code: str, text: str) -> None:
        nonlocal status
        reasons.append({"code": code, "text": text})
        if rank[to] > rank[status]:
            status = to
    if actual >= 100:
        reasons.append({"code": "complete", "text": "All planned work is finished."})
    else:
        if planned is not None:
            if gap > 20:
                worsen("off_track", "schedule", f"{gap:.0f} points behind schedule ({actual:.0f}% done vs {planned:.0f}% of the time elapsed).")
            elif gap > 10:
                worsen("at_risk", "schedule", f"{gap:.0f} points behind schedule ({actual:.0f}% done vs {planned:.0f}% of the time elapsed).")
            else:
                reasons.append({"code": "schedule", "text": f"On schedule ({actual:.0f}% done vs {planned:.0f}% of the time elapsed)."})
        overdue = [m for m in prog["milestones"] if m["status"] != "done" and m["due"] and _day(dt.datetime.fromisoformat(m["due"])) < _day(now)]
        if overdue:
            worst = max((_day(now) - _day(dt.datetime.fromisoformat(m["due"]))).days for m in overdue)
            worsen("off_track" if (len(overdue) >= 2 or worst > 14) else "at_risk", "milestone", f"{len(overdue)} milestone(s) overdue (up to {worst} days).")
        b = budget_status(db, pid)
        worst_pct = max([x for x in (b["hours_pct"], b["amount_pct"]) if x is not None], default=0)
        if worst_pct > 100:
            worsen("off_track", "budget", f"Budget exceeded ({worst_pct:.0f}% used) with work still open.")
        elif worst_pct >= 90 and actual < 80:
            worsen("at_risk", "budget", f"{worst_pct:.0f}% of the budget is used but only {actual:.0f}% of the work is done.")
        aged = [x for x in blockers(db, pid, aging_days, now) if x["aged"]]
        if aged:
            worsen("at_risk", "blockers", f"{len(aged)} task(s) blocked for {aging_days}+ days (oldest {aged[0]['days']} days).")
    if status != "on_track":                                                   # "On schedule" must never be the headline of an at-risk project
        reasons.sort(key=lambda r: r["text"].startswith("On schedule"))
    if len(reasons) == 1 and reasons[0]["code"] == "schedule" and planned is None:
        reasons[0]["text"] = f"{actual:.0f}% complete."
    if not reasons:
        reasons.append({"code": "progress", "text": f"{actual:.0f}% complete; no deadline set."})
    return {"status": status, "reasons": reasons, "planned_pct": planned, "actual_pct": actual, "gap_pts": gap}


def refresh_health(db: Database, pid: str, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Compute and store the status on the project row (so lists and the portal can show it without recomputing)."""
    h = health(db, pid, now)
    Store(db).update("projects", pid, health=h["status"], health_reason=" ".join(r["text"] for r in h["reasons"])[:500])
    return h
