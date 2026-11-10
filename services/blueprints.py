"""Project templates (blueprints) and the computed project summary (actual hours, spent, health)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import now_utc
from .projects import ProjectService


def save_blueprint(db: Database, name: str, tasks: List[Dict[str, Any]], defaults: Optional[Dict[str, Any]] = None) -> None:
    """tasks: [{title, estimated_min, column, depends_on: [index,...]}]. Validated: dependencies must point to earlier tasks."""
    if not name.strip() or not tasks:
        raise ValueError("name and at least one task required")
    for i, t in enumerate(tasks):
        if not str(t.get("title", "")).strip():
            raise ValueError(f"task {i} has no title")
        if any(not (isinstance(d, int) and 0 <= d < i) for d in t.get("depends_on", [])):
            raise ValueError(f"task {i}: dependencies must reference earlier tasks")
    b = db.get_setting("blueprints", {})
    b[name] = {"tasks": tasks, "defaults": defaults or {}}
    db.set_setting("blueprints", b)


def create_from_blueprint(db: Database, blueprint: str, project_name: str, client_id: Optional[str] = None) -> Project:
    bp = db.get_setting("blueprints", {}).get(blueprint)
    if bp is None:
        raise KeyError(blueprint)
    svc = ProjectService(db)
    with db.transaction():
        p = Project(name=project_name, client_id=client_id, **bp["defaults"])
        db.save(p)
        made: List[TimeEntry] = []
        for t in bp["tasks"]:
            e = TimeEntry(title=t["title"], start_utc=now_utc(), status=Status.PLANNED, project_id=p.id,
                          estimated_min=int(t.get("estimated_min", 0)), column=t.get("column", "backlog"))
            db.save(e)
            made.append(e)
        for i, t in enumerate(bp["tasks"]):
            for d in t.get("depends_on", []):
                svc.add_dependency(made[i].id, made[d].id)
    return p


def project_summary(db: Database, project_id: str) -> Dict[str, Any]:
    """Computed fields from the spec: actual_hours, spent, health, progress."""
    p = db.get(Project, project_id)
    if p is None:
        raise KeyError(project_id)
    sec = db.conn.execute("SELECT COALESCE(SUM(duration_sec),0) FROM entries WHERE project_id=? AND status='done'", (project_id,)).fetchone()[0]
    total, done = db.conn.execute("SELECT COUNT(*), COALESCE(SUM(status='done'),0) FROM entries WHERE project_id=? AND parent_id IS NULL", (project_id,)).fetchone()
    hours = sec / 3600
    return {"actual_hours": round(hours, 2), "spent": round(hours * p.rate_per_hour, 2),
            "health": ProjectService(db).health(project_id), "progress": round(done / total, 3) if total else 0.0, "tasks": total}
