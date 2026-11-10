"""Project management: health, milestones, sprints, dependencies/Gantt, kanban, subtasks."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from ..core.database import Database
from ..core.models import (KANBAN_COLUMNS, Dependency, Milestone, Project, ProjectStatus, Sprint, Status, TimeEntry)
from ..core.persian import now_utc


class ProjectService:
    def __init__(self, db: Database) -> None:
        self.db = db

    # ---- kanban -----------------------------------------------------
    def board(self, project_id: Optional[str] = None) -> Dict[str, List[TimeEntry]]:
        sql, args = "SELECT * FROM entries WHERE status IN ('planned','running')", []
        if project_id:
            sql += " AND project_id=?"; args.append(project_id)
        out: Dict[str, List[TimeEntry]] = {c: [] for c in KANBAN_COLUMNS}
        for r in self.db.conn.execute(sql + " ORDER BY priority, created_at", args):
            e = TimeEntry.from_row(r)
            out.setdefault(e.column, []).append(e)
        return out

    def move(self, entry_id: str, column: str) -> TimeEntry:
        """Move a card. Blocked cards cannot enter in_progress/review/done."""
        if column not in KANBAN_COLUMNS:
            raise ValueError("unknown column")
        e = self.db.get(TimeEntry, entry_id)
        if e is None:
            raise KeyError(entry_id)
        if column != "backlog" and self.blockers(entry_id):
            raise ValueError("task is blocked by unfinished dependencies")
        e.column = column
        if column == "done":
            e.status = Status.DONE
            e.end_utc = e.end_utc or now_utc()
            e.completed_at = e.completed_at or now_utc()
        elif e.status == Status.DONE:
            e.status, e.completed_at = Status.PLANNED, None
        self.db.save(e)
        return e

    # ---- subtasks -----------------------------------------------------
    def add_subtask(self, parent_id: str, title: str) -> TimeEntry:
        parent = self.db.get(TimeEntry, parent_id)
        if parent is None:
            raise KeyError(parent_id)
        if parent.parent_id:
            raise ValueError("only one level of nesting is supported")
        sub = TimeEntry(title=title, start_utc=now_utc(), status=Status.PLANNED, project_id=parent.project_id,
                        parent_id=parent_id, category=parent.category)
        self.db.save(sub)
        return sub

    def progress(self, task_id: str) -> float:
        """Share of done subtasks (0..1); a task with no subtasks is 1.0 if done else 0.0."""
        subs = [TimeEntry.from_row(r) for r in self.db.conn.execute("SELECT * FROM entries WHERE parent_id=?", (task_id,))]
        if not subs:
            t = self.db.get(TimeEntry, task_id)
            return 1.0 if t and t.status == Status.DONE else 0.0
        return sum(s.status == Status.DONE for s in subs) / len(subs)

    # ---- dependencies ---------------------------------------------------
    def add_dependency(self, task_id: str, depends_on: str, kind: str = "finish_to_start", lag_days: int = 0) -> Dependency:
        """Add an edge; rejects cycles."""
        if self._reaches(depends_on, task_id):
            raise ValueError("dependency would create a cycle")
        d = Dependency(task_id=task_id, depends_on=depends_on, kind=kind, lag_days=lag_days)
        self.db.save(d)
        return d

    def _edges(self) -> Dict[str, Set[str]]:
        g: Dict[str, Set[str]] = defaultdict(set)
        for r in self.db.conn.execute("SELECT task_id, depends_on FROM dependencies"):
            g[r[0]].add(r[1])
        return g

    def _reaches(self, start: str, target: str) -> bool:
        """True if following 'depends_on' from start reaches target."""
        g, seen, dq = self._edges(), set(), deque([start])
        while dq:
            n = dq.popleft()
            if n == target:
                return True
            if n in seen:
                continue
            seen.add(n)
            dq.extend(g.get(n, ()))
        return False

    def blockers(self, task_id: str) -> List[str]:
        """Ids of unfinished tasks this task waits on."""
        rows = self.db.conn.execute(
            "SELECT e.id FROM dependencies d JOIN entries e ON e.id=d.depends_on WHERE d.task_id=? AND e.status!='done'", (task_id,))
        return [r[0] for r in rows]

    def gantt(self, project_id: str, project_start: Optional[dt.date] = None) -> Dict[str, Tuple[dt.date, dt.date]]:
        """Earliest (start, end) per task using estimates (min 1 day) and finish-to-start style dependencies."""
        tasks = {t.id: t for t in (TimeEntry.from_row(r) for r in self.db.conn.execute(
            "SELECT * FROM entries WHERE project_id=? AND parent_id IS NULL", (project_id,)))}
        g = self._edges()
        base = project_start or now_utc().date()
        kinds = {(r[0], r[1]): (r[2], r[3]) for r in self.db.conn.execute("SELECT task_id, depends_on, kind, lag_days FROM dependencies")}
        memo: Dict[str, Tuple[dt.date, dt.date]] = {}

        def days(t: TimeEntry) -> int:
            return max(1, -(-(t.estimated_min or t.duration_sec // 60 or 480) // 480))

        def calc(tid: str) -> Tuple[dt.date, dt.date]:
            if tid in memo:
                return memo[tid]
            t, start = tasks[tid], base
            for dep in g.get(tid, ()):
                if dep not in tasks:
                    continue
                ds, de = calc(dep)
                kind, lag = kinds[(tid, dep)]
                anchor = {"finish_to_start": de, "start_to_start": ds, "finish_to_finish": de - dt.timedelta(days=days(t) - 1),
                          "start_to_finish": ds - dt.timedelta(days=days(t) - 1)}[kind]
                cand = anchor + dt.timedelta(days=lag + (1 if kind == "finish_to_start" else 0))
                start = max(start, cand)
            memo[tid] = (start, start + dt.timedelta(days=days(t) - 1))
            return memo[tid]

        for tid in tasks:
            calc(tid)
        return memo

    # ---- milestones ---------------------------------------------------
    def milestone_progress(self, project_id: str) -> Tuple[int, int]:
        ms = [Milestone.from_row(r) for r in self.db.conn.execute("SELECT * FROM milestones WHERE project_id=?", (project_id,))]
        return sum(m.completed for m in ms), len(ms)

    def complete_milestone(self, milestone_id: str) -> Milestone:
        m = self.db.get(Milestone, milestone_id)
        if m is None:
            raise KeyError(milestone_id)
        m.completed, m.completed_at = True, now_utc()
        self.db.save(m)
        return m

    # ---- sprints ------------------------------------------------------
    def sprint_stats(self, sprint_id: str) -> Dict[str, float]:
        sp = self.db.get(Sprint, sprint_id)
        if sp is None:
            raise KeyError(sprint_id)
        rows = [TimeEntry.from_row(r) for r in self.db.conn.execute("SELECT * FROM entries WHERE sprint_id=?", (sprint_id,))]
        committed = sum(max(r.estimated_min, r.duration_sec // 60) for r in rows) / 60
        done = sum(max(r.estimated_min, r.duration_sec // 60) for r in rows if r.status == Status.DONE) / 60
        logged = sum(r.duration_sec for r in rows) / 3600
        return {"committed_hours": round(committed, 2), "completed_hours": round(done, 2), "logged_hours": round(logged, 2),
                "capacity_hours": sp.capacity_hours, "over_capacity": float(sp.capacity_hours > 0 and committed > sp.capacity_hours),
                "burn_pct": round(100 * done / committed, 1) if committed else 0.0}

    def velocity(self, project_id: str, last: int = 3) -> float:
        """Average completed hours of the last ``last`` completed sprints."""
        rows = self.db.conn.execute("SELECT id FROM sprints WHERE project_id=? AND status='completed' ORDER BY \"end\" DESC LIMIT ?",
                                    (project_id, last)).fetchall()
        vals = [self.sprint_stats(r[0])["completed_hours"] for r in rows]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    # ---- health ---------------------------------------------------------
    def health(self, project_id: str, today: Optional[dt.datetime] = None) -> str:
        """on_track / at_risk / off_track from budget burn, hours burn vs. time elapsed, and deadline."""
        p = self.db.get(Project, project_id)
        if p is None:
            raise KeyError(project_id)
        if p.status in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
            return "on_track"
        today = today or now_utc()
        sec = self.db.conn.execute("SELECT COALESCE(SUM(duration_sec),0) FROM entries WHERE project_id=? AND status='done'", (project_id,)).fetchone()[0]
        hours = sec / 3600
        score = 0
        if p.estimated_hours:
            r = hours / p.estimated_hours
            score += 2 if r > 1.0 else 1 if r > 0.85 else 0
        if p.budget and p.rate_per_hour:
            r = hours * p.rate_per_hour / p.budget
            score += 2 if r > 1.0 else 1 if r > 0.85 else 0
        if p.deadline:
            if today > p.deadline:
                done, total = self.milestone_progress(project_id)
                score += 3 if not (total and done == total) else 0
            else:
                span = (p.deadline - p.created_at).total_seconds()
                if span > 0 and p.estimated_hours:
                    time_used = (today - p.created_at).total_seconds() / span
                    if hours / p.estimated_hours < time_used - 0.3:   # far behind schedule
                        score += 1
        return "off_track" if score >= 3 else "at_risk" if score >= 1 else "on_track"
