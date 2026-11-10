"""Sprint lifecycle: planning -> active -> completed, with commitment, carry-over, burndown and velocity.

A sprint holds tasks through ``TimeEntry.sprint_id``. The "size" of a task is its estimate (``estimated_min``), falling back to the time already logged.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List, Optional

from ..core.database import Database
from ..core.models import Sprint, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran


class SprintError(ValueError):
    """An illegal sprint operation (message is user-facing)."""


def _size_h(e: TimeEntry) -> float:
    return (e.estimated_min or e.duration_sec // 60) / 60.0


def tasks(db: Database, sprint_id: str) -> List[TimeEntry]:
    return [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE sprint_id=? AND parent_id IS NULL ORDER BY rank, created_at", (sprint_id,))]


def _get(db: Database, sprint_id: str) -> Sprint:
    sp = db.get(Sprint, sprint_id)
    if sp is None:
        raise KeyError(sprint_id)
    return sp


def create(db: Database, project_id: str, name: str, start: dt.date, days: int = 14, goal: str = "", capacity_hours: float = 0.0) -> Sprint:
    if not name.strip():
        raise SprintError("نام اسپرینت را وارد کنید")
    if not 1 <= days <= 60:
        raise SprintError("طول اسپرینت باید بین ۱ تا ۶۰ روز باشد")
    if capacity_hours < 0:
        raise SprintError("ظرفیت نمی‌تواند منفی باشد")
    s = dt.datetime.combine(start, dt.time(), tzinfo=TEHRAN).astimezone(UTC)
    sp = Sprint(project_id=project_id, name=name.strip(), start=s, end=s + dt.timedelta(days=days), goal=goal.strip(), status="planning", capacity_hours=capacity_hours)
    db.save(sp)
    return sp


def assign(db: Database, sprint_id: str, entry_ids: Iterable[str]) -> int:
    sp = _get(db, sprint_id)
    if sp.status == "completed":
        raise SprintError("به اسپرینت تمام‌شده نمی‌شود کار افزود")
    n = 0
    with db.transaction():
        for i in entry_ids:
            e = db.get(TimeEntry, i)
            if e is not None and not e.parent_id and e.column not in ("done", "cancelled"):
                e.sprint_id = sprint_id
                db.save(e); n += 1
    return n


def unassign(db: Database, entry_ids: Iterable[str]) -> int:
    n = 0
    with db.transaction():
        for i in entry_ids:
            e = db.get(TimeEntry, i)
            if e is not None and e.sprint_id:
                e.sprint_id = None
                db.save(e); n += 1
    return n


def start(db: Database, sprint_id: str) -> Sprint:
    sp = _get(db, sprint_id)
    if sp.status != "planning":
        raise SprintError("فقط اسپرینت در حالت برنامه‌ریزی را می‌شود شروع کرد")
    other = db.conn.execute("SELECT name FROM sprints WHERE project_id=? AND status='active' AND id!=?", (sp.project_id, sprint_id)).fetchone()
    if other:
        raise SprintError(f"اسپرینت «{other[0]}» هنوز فعال است؛ اول آن را تمام کنید")
    if not tasks(db, sprint_id):
        raise SprintError("اسپرینت خالی را نمی‌شود شروع کرد؛ اول کار اضافه کنید")
    sp.status = "active"
    db.save(sp)
    return sp


def _snapshot(db: Database, sprint_id: str) -> Optional[Dict[str, Any]]:
    return db.get_setting("sprint_results", {}).get(sprint_id)


def stats(db: Database, sprint_id: str) -> Dict[str, Any]:
    sp = _get(db, sprint_id)
    if sp.status == "completed":                       # a finished sprint keeps the numbers it ended with, even after tasks were carried elsewhere
        snap = _snapshot(db, sprint_id)
        if snap:
            return dict(snap)
    ts = tasks(db, sprint_id)
    committed = sum(_size_h(e) for e in ts)
    done = [e for e in ts if e.column == "done" or e.status == Status.DONE]
    completed = sum(_size_h(e) for e in done)
    return {"tasks": len(ts), "done_tasks": len(done), "committed_hours": round(committed, 2), "completed_hours": round(completed, 2),
            "remaining_hours": round(committed - completed, 2), "capacity_hours": sp.capacity_hours,
            "capacity_pct": round(100 * committed / sp.capacity_hours, 1) if sp.capacity_hours else None,
            "over_capacity": bool(sp.capacity_hours and committed > sp.capacity_hours), "progress_pct": round(100 * completed / committed, 1) if committed else 0.0,
            "status": sp.status}


def complete(db: Database, sprint_id: str, carry_over: str = "backlog", next_sprint_id: Optional[str] = None) -> Dict[str, Any]:
    """Close an active sprint. Unfinished tasks go to the backlog (``backlog``), into another sprint (``next``) or stay on it (``keep``)."""
    sp = _get(db, sprint_id)
    if sp.status != "active":
        raise SprintError("فقط اسپرینت فعال را می‌شود تمام کرد")
    if carry_over not in ("backlog", "next", "keep"):
        raise ValueError("bad carry_over")
    if carry_over == "next":
        nxt = _get(db, next_sprint_id) if next_sprint_id else None
        if nxt is None or nxt.project_id != sp.project_id or nxt.status == "completed" or nxt.id == sp.id:
            raise SprintError("اسپرینت مقصد معتبر نیست")
    result = stats(db, sprint_id)
    carried = 0
    with db.transaction():
        for e in tasks(db, sprint_id):
            if e.column in ("done", "cancelled") or e.status == Status.DONE:
                continue
            if carry_over == "backlog":
                e.sprint_id = None; e.column = "backlog"
            elif carry_over == "next":
                e.sprint_id = next_sprint_id
            else:
                continue
            db.save(e); carried += 1
        sp.status = "completed"
        db.save(sp)
        result.update({"carried": carried, "velocity_hours": result["completed_hours"], "status": "completed"})
        results = db.get_setting("sprint_results", {}); results[sprint_id] = result; db.set_setting("sprint_results", results)
    return result


def burndown(db: Database, sprint_id: str, today: Optional[dt.date] = None) -> Dict[str, Any]:
    """Remaining work (hours) at the end of each sprint day versus the ideal straight line. Days after ``today`` have no ``actual`` (None)."""
    sp = _get(db, sprint_id)
    ts = tasks(db, sprint_id)
    first = to_tehran(sp.start).date()
    n = max(1, (to_tehran(sp.end).date() - first).days)
    total = sum(_size_h(e) for e in ts)
    today = today or to_tehran(now_utc()).date()
    days = [first + dt.timedelta(days=i) for i in range(n + 1)]
    ideal = [round(total * (1 - i / n), 2) for i in range(n + 1)]
    actual: List[Optional[float]] = []
    for d in days:
        if d > today:
            actual.append(None); continue
        rem = 0.0
        for e in ts:
            finished = e.completed_at is not None and to_tehran(e.completed_at).date() <= d
            if not finished and not (e.column == "done" and e.completed_at is None and d >= today):
                rem += _size_h(e)
        actual.append(round(rem, 2))
    return {"days": days, "ideal": ideal, "actual": actual, "total_hours": round(total, 2)}


def velocity_history(db: Database, project_id: str) -> List[Dict[str, Any]]:
    rows = db.conn.execute("SELECT id, name FROM sprints WHERE project_id=? AND status='completed' ORDER BY \"end\"", (project_id,)).fetchall()
    return [{"sprint": r[1], "completed_hours": stats(db, r[0])["completed_hours"], "committed_hours": stats(db, r[0])["committed_hours"]} for r in rows]


def average_velocity(db: Database, project_id: str, last: int = 3) -> float:
    h = velocity_history(db, project_id)[-last:]
    return round(sum(x["completed_hours"] for x in h) / len(h), 2) if h else 0.0


def sprints_needed(db: Database, project_id: str) -> Optional[float]:
    """Forecast: remaining un-sprinted backlog hours / average velocity (None while there is no velocity yet)."""
    v = average_velocity(db, project_id)
    if v <= 0:
        return None
    backlog = sum(_size_h(TimeEntry.from_row(r)) for r in db.conn.execute(
        "SELECT * FROM entries WHERE project_id=? AND parent_id IS NULL AND sprint_id IS NULL AND column NOT IN ('done','cancelled')", (project_id,)))
    return round(backlog / v, 1)


def for_project(db: Database, project_id: str) -> List[Sprint]:
    return [Sprint.from_row(r) for r in db.conn.execute('SELECT * FROM sprints WHERE project_id=? ORDER BY "start" DESC', (project_id,))]
