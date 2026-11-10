"""Break big work down: a whole project from one outline (phases -> tasks -> sub-tasks), one big task into sub-tasks, or one project into two.

Outline example (indentation or ``#`` headings, check boxes, ``45m``, ``#tag``, ``d:2026-06-01``)::

    # Research
    - [x] Interview 5 readers 3h
    - [ ] Outline the chapters
        - [ ] Chapter 1 draft 2h
    # Writing
    - [ ] First draft 20h
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from ..core.database import Database
from ..core.models import Milestone, Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran, tr
from . import outline, quick
from .quickadd import resolve_project

TEMPLATES: Dict[str, Dict[str, str]] = {
    "book": {"fa": "# پژوهش و طرح\n- [ ] تعیین مخاطب و وعده‌ی کتاب 2h\n- [ ] مصاحبه یا مرور منابع 6h\n- [ ] طرح کلی فصل‌ها 3h\n# نگارش\n- [ ] پیش‌نویس فصل ۱ 8h\n    - [ ] مقدمه\n    - [ ] بدنه\n- [ ] پیش‌نویس فصل ۲ 8h\n- [ ] پیش‌نویس فصل ۳ 8h\n# ویرایش\n- [ ] ویرایش ساختاری 10h\n- [ ] ویرایش زبانی 6h\n# انتشار\n- [ ] طراحی جلد 4h\n- [ ] صفحه‌ی فروش 3h\n- [ ] برنامه‌ی عرضه 2h",
             "en": "# Research & plan\n- [ ] Define the reader and the promise 2h\n- [ ] Interviews or source review 6h\n- [ ] Chapter outline 3h\n# Writing\n- [ ] Chapter 1 draft 8h\n    - [ ] Introduction\n    - [ ] Body\n- [ ] Chapter 2 draft 8h\n- [ ] Chapter 3 draft 8h\n# Editing\n- [ ] Structural edit 10h\n- [ ] Line edit 6h\n# Publishing\n- [ ] Cover design 4h\n- [ ] Sales page 3h\n- [ ] Launch plan 2h"},
    "product": {"fa": "# تعریف\n- [ ] مشکل و مشتری هدف 2h\n- [ ] ۵ گفتگوی کشف نیاز 5h\n# ساخت\n- [ ] نسخه‌ی حداقلی (MVP) 20h\n    - [ ] طراحی\n    - [ ] پیاده‌سازی\n    - [ ] تست\n# راه‌اندازی\n- [ ] صفحه‌ی فرود 4h\n- [ ] اولین ۱۰ مشتری 8h\n# رشد\n- [ ] بازخوردگیری هفتگی 1h",
                "en": "# Define\n- [ ] Problem and target customer 2h\n- [ ] 5 discovery conversations 5h\n# Build\n- [ ] Minimum viable product 20h\n    - [ ] Design\n    - [ ] Implementation\n    - [ ] Testing\n# Launch\n- [ ] Landing page 4h\n- [ ] First 10 customers 8h\n# Grow\n- [ ] Weekly feedback loop 1h"},
    "course": {"fa": "# طراحی\n- [ ] نتیجه‌ی یادگیری 2h\n- [ ] سرفصل‌ها 3h\n# تولید\n- [ ] درس ۱ 6h\n- [ ] درس ۲ 6h\n- [ ] تمرین‌ها 4h\n# عرضه\n- [ ] صفحه‌ی فروش 4h\n- [ ] پشتیبانی دانشجویان 2h",
               "en": "# Design\n- [ ] Learning outcome 2h\n- [ ] Syllabus 3h\n# Production\n- [ ] Lesson 1 6h\n- [ ] Lesson 2 6h\n- [ ] Exercises 4h\n# Launch\n- [ ] Sales page 4h\n- [ ] Student support 2h"},
}


class SplitError(ValueError):
    """Invalid split request (message is user-facing)."""


def template(name: str) -> str:
    t = TEMPLATES[name]
    return t[tr("fa", "en")]


def _levels(roots: List[outline.Node]) -> str:
    """'phases' when the outline is phases -> tasks (headings or 3 levels), else 'tasks'."""
    if any(r.heading for r in roots) or any(c.children for r in roots for c in r.children):
        return "phases"
    return "tasks"


def preview(text: str) -> Dict[str, Any]:
    roots = outline.parse(text, max_depth=3)
    mode = _levels(roots)
    phases = len(roots) if mode == "phases" else 0
    tasks = sum(len(r.children) for r in roots) if mode == "phases" else len(roots)
    subs = (sum(len(c.children) for r in roots for c in r.children) if mode == "phases" else sum(len(r.children) for r in roots))
    mins = sum(n.minutes for r in roots for n in r.walk())
    return {"mode": mode, "phases": phases, "tasks": tasks, "subtasks": subs, "estimate_hours": round(mins / 60, 1)}


def apply_outline(db: Database, project_id: str, text: str, start: Optional[dt.date] = None, phase_days: int = 14, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Create milestones (phases), tasks and sub-tasks for a project in one transaction. Phase due dates follow each other every ``phase_days`` days from ``start``."""
    if db.get(Project, project_id) is None:
        raise SplitError(tr("پروژه پیدا نشد", "Project not found"))
    if not 1 <= phase_days <= 365:
        raise SplitError(tr("طول فاز باید بین ۱ تا ۳۶۵ روز باشد", "Phase length must be 1-365 days"))
    roots = outline.parse(text, max_depth=3)
    if not roots:
        raise SplitError(tr("طرحی پیدا نشد؛ هر خط یک مورد", "No outline found; one item per line"))
    now = now or now_utc()
    mode = _levels(roots)
    start = start or to_tehran(now).date()
    res: Dict[str, Any] = {"mode": mode, "phases": 0, "tasks": 0, "subtasks": 0, "estimate_hours": 0.0, "milestone_ids": [], "entry_ids": []}
    rank = 0.0

    def make(node: outline.Node, parent: Optional[str], phase: Optional[str]) -> TimeEntry:
        nonlocal rank
        rank += 10.0
        e = TimeEntry(title=node.title, start_utc=now, status=Status.PLANNED, column="backlog", project_id=project_id, parent_id=parent, tags=list(node.tags), important=node.starred,
                      estimated_min=node.minutes, rank=rank, extra={"phase": phase} if phase else {}, source="split",
                      due_utc=dt.datetime.combine(node.due, dt.time(), tzinfo=TEHRAN).astimezone(UTC) if node.due else None)
        if node.done:
            e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, now, 100
        e.updated_at = now
        db.save(e)
        res["entry_ids"].append(e.id)
        res["estimate_hours"] += node.minutes / 60
        return e

    with db.transaction():
        groups = []
        if mode == "phases":
            for i, ph in enumerate(roots):
                due = dt.datetime.combine(start + dt.timedelta(days=phase_days * (i + 1)), dt.time(), tzinfo=TEHRAN).astimezone(UTC)
                ms = Milestone(project_id=project_id, name=ph.title, due=due, deliverables=[c.title for c in ph.children][:20])
                db.save(ms)
                res["phases"] += 1; res["milestone_ids"].append(ms.id)
                groups.append((ph.children, ms.id))
        else:
            groups.append((roots, None))
        for tasks_, phase_id in groups:
            for t in tasks_:
                parent = make(t, None, phase_id); res["tasks"] += 1
                for sub in (c for c in t.walk() if c is not t):
                    make(sub, parent.id, phase_id); res["subtasks"] += 1
    res["estimate_hours"] = round(res["estimate_hours"], 1)
    return res


def split_task(db: Database, task_id: str, parts: List[str], divide_estimate: bool = True, now: Optional[dt.datetime] = None) -> List[TimeEntry]:
    """Turn one big task into sub-tasks. Without an explicit duration per part, the task's estimate is shared equally (the remainder goes to the first)."""
    parent = db.get(TimeEntry, task_id)
    if parent is None:
        raise KeyError(task_id)
    if parent.parent_id:
        raise SplitError(tr("یک زیرتسک را نمی‌شود دوباره شکست", "A sub-task cannot be split again"))
    parsed = []
    for p in parts:
        if p.strip():
            try:
                parsed.append(quick.parse(p))
            except ValueError:
                continue
    if not parsed:
        raise SplitError(tr("حداقل یک بخش بنویس", "Write at least one part"))
    if len(parsed) > 50:
        raise SplitError(tr("حداکثر ۵۰ بخش", "At most 50 parts"))
    free = [c for c in parsed if not c.minutes]
    share, rest = (divmod(parent.estimated_min, len(free)) if (divide_estimate and parent.estimated_min and free) else (0, 0))
    now = now or now_utc()
    out: List[TimeEntry] = []
    with db.transaction():
        for i, c in enumerate(parsed):
            mins = c.minutes or (share + (rest if c is free[0] else 0) if free and divide_estimate else 0)
            e = TimeEntry(title=c.title, start_utc=now, status=Status.PLANNED, column="backlog", project_id=parent.project_id, parent_id=parent.id, category=parent.category, priority=parent.priority,
                          tags=list(dict.fromkeys(parent.tags + c.tags)), estimated_min=mins, rank=10.0 * (i + 1), extra={k: v for k, v in parent.extra.items() if k in ("list", "phase")}, source="split")
            e.updated_at = now
            db.save(e); out.append(e)
    return out


def phase_progress(db: Database, project_id: str) -> List[Dict[str, Any]]:
    """Per phase (milestone): tasks, done, percent and hours; tasks without a phase are reported last under ``None``."""
    now = now_utc()
    tasks = [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE project_id=? AND parent_id IS NULL AND column != 'cancelled'", (project_id,))]
    out = []
    ms_list = sorted((Milestone.from_row(r) for r in db.conn.execute("SELECT * FROM milestones WHERE project_id=?", (project_id,))), key=lambda m: (m.due or now, m.name))
    def line(mid, name, due, ts):
        done = sum(1 for t in ts if t.column == "done" or t.status == Status.DONE)
        return {"milestone": mid, "name": name, "tasks": len(ts), "done": done, "pct": round(100 * done / len(ts), 1) if ts else 0.0,
                "hours": round(sum(t.estimated_min for t in ts) / 60, 1), "due": due, "overdue": bool(due and due < now and done < len(ts))}
    used = set()
    for m in ms_list:
        ts = [t for t in tasks if t.extra.get("phase") == m.id]
        used.update(t.id for t in ts)
        out.append(line(m.id, m.name, m.due, ts))
    rest = [t for t in tasks if t.id not in used]
    if rest:
        out.append(line(None, tr("بدون فاز", "No phase"), None, rest))
    return out


def split_project(db: Database, project_id: str, task_ids: List[str], new_name: str) -> Project:
    """Move the chosen tasks (with their sub-tasks) into a brand-new project that inherits client, rate, currency, colour and icon."""
    src = db.get(Project, project_id)
    if src is None:
        raise KeyError(project_id)
    if not new_name.strip():
        raise SplitError(tr("نام پروژه‌ی تازه را وارد کنید", "Enter the new project's name"))
    ids = [i for i in dict.fromkeys(task_ids)]
    ents = [db.get(TimeEntry, i) for i in ids]
    ents = [e for e in ents if e is not None and e.project_id == project_id and not e.parent_id]
    if not ents:
        raise SplitError(tr("هیچ تسکی انتخاب نشده", "No task selected"))
    new = Project(name=new_name.strip(), client_id=src.client_id, rate_per_hour=src.rate_per_hour, currency=src.currency, color=src.color, icon=src.icon, tags=list(src.tags),
                  description=tr(f"جداشده از «{src.name}»", f"Split from \"{src.name}\""))
    with db.transaction():
        db.save(new)
        for e in ents:
            for t in [e] + [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE parent_id=?", (e.id,))]:
                t.project_id = new.id
                t.extra = {k: v for k, v in t.extra.items() if k != "phase"}              # phases belong to the old project
                db.save(t)
    return new
