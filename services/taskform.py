"""All the *logic* behind the Add/Edit Task dialog (no Qt): values, validation, quick presets, saving.

The dialog only collects widget values into :class:`TaskValues`; everything else - rules, time sync, subtasks, dependencies, recurrence,
starting a timer - lives here so it can be unit-tested. It covers everything the v5 task form had (category + sub-category, priority,
project, tags, start/end, duration, recurrence, reminder, checklist, description, subtasks, dependencies, attachments) and adds
due date, estimate, energy, location, billing rate, colour/icon, assignee, progress and a "start the timer now" switch.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core import taxonomy
from ..core.database import Database
from ..core.models import ALL_COLUMNS, Project, Status, TimeEntry, new_id
from ..core.persian import now_utc, to_tehran

LOCATIONS = ("", "office", "home", "client", "cafe", "travel")
REMINDER_CHOICES = (0, 5, 10, 15, 30, 60, 120, 1440)            # minutes before start (0 = at the start)
DURATION_CHIPS = (15, 30, 45, 60, 90, 120, 180, 240)
RECURRENCE_TYPES = ("", "daily", "weekly", "monthly", "custom")
COLUMN_LABELS = {"backlog": "بک‌لاگ", "in_progress": "در حال انجام", "review": "بازبینی", "delayed": "تعویق‌شده", "done": "انجام‌شده", "cancelled": "لغو شده"}
MAX_TITLE = 200
ALL_COLUMNS_ORDER = ("backlog", "in_progress", "review", "delayed", "done", "cancelled")


@dataclass
class TaskValues:
    title: str = ""
    description: str = ""
    project_id: Optional[str] = None
    category: str = "general"
    subcategory: str = ""
    priority: int = 3
    column: str = "backlog"
    tags: List[str] = field(default_factory=list)
    assignee: str = ""
    color: str = ""
    icon: str = ""
    all_day: bool = False
    start: Optional[dt.datetime] = None
    end: Optional[dt.datetime] = None
    due: Optional[dt.datetime] = None
    estimated_min: int = 0
    energy: int = 0
    location: str = ""
    billable: bool = False
    rate: Optional[float] = None
    start_timer_now: bool = False
    checklist: List[Dict[str, Any]] = field(default_factory=list)       # [{"text":..., "done":bool}]
    subtasks: List[str] = field(default_factory=list)                    # titles of *new* subtasks to create
    depends_on: List[str] = field(default_factory=list)                  # entry ids
    progress: int = 0
    notes: str = ""
    attachments: List[str] = field(default_factory=list)
    recurrence: Dict[str, Any] = field(default_factory=dict)             # {"type","interval","until"(iso)}
    reminders: List[int] = field(default_factory=list)
    important: bool = False


# ---------------------------------------------------------------- time helpers
def end_from_minutes(start: dt.datetime, minutes: int) -> dt.datetime:
    return start + dt.timedelta(minutes=max(0, minutes))


def minutes_between(start: Optional[dt.datetime], end: Optional[dt.datetime]) -> int:
    return max(0, int((end - start).total_seconds() // 60)) if start and end else 0


def quick_time(kind: str, now: Optional[dt.datetime] = None) -> dt.datetime:
    """Presets for the quick-time chips (all in Tehran time, rounded to 5 minutes): now / +30m / +1h / tonight / tomorrow morning."""
    now = to_tehran(now or now_utc())
    base = now.replace(second=0, microsecond=0)
    base -= dt.timedelta(minutes=base.minute % 5)
    if kind == "now": return base
    if kind == "in30": return base + dt.timedelta(minutes=30)
    if kind == "in60": return base + dt.timedelta(hours=1)
    if kind == "tonight": return base.replace(hour=20, minute=0) if base.hour < 20 else base + dt.timedelta(hours=1)
    if kind == "tomorrow": return (base + dt.timedelta(days=1)).replace(hour=9, minute=0)
    raise ValueError(f"unknown preset {kind!r}")


# ---------------------------------------------------------------- validation
def validate(v: TaskValues) -> Dict[str, str]:
    """Field -> Persian message. Empty dict means the form can be saved."""
    err: Dict[str, str] = {}
    t = v.title.strip()
    if not t:
        err["title"] = "عنوان را وارد کنید"
    elif len(t) > MAX_TITLE:
        err["title"] = f"عنوان نباید بیش از {MAX_TITLE} نویسه باشد"
    if v.priority not in taxonomy.PRIORITIES:
        err["priority"] = "اولویت نامعتبر است"
    if v.column not in ALL_COLUMNS:
        err["column"] = "وضعیت نامعتبر است"
    if v.start and v.end and v.end < v.start:
        err["end"] = "زمان پایان قبل از شروع است"
    if v.end and not v.start:
        err["start"] = "برای زمان پایان، زمان شروع هم لازم است"
    if v.due and v.start and v.due < v.start and v.column not in ("done", "cancelled"):
        err["due"] = "موعد قبل از شروع است"
    if v.estimated_min < 0 or v.estimated_min > 60 * 24 * 30:
        err["estimated_min"] = "تخمین زمان نامعتبر است"
    if not 0 <= v.energy <= 5:
        err["energy"] = "انرژی باید بین ۱ تا ۵ باشد"
    if not 0 <= v.progress <= 100:
        err["progress"] = "پیشرفت باید بین ۰ تا ۱۰۰ باشد"
    if v.rate is not None and v.rate < 0:
        err["rate"] = "نرخ نمی‌تواند منفی باشد"
    if v.start_timer_now and v.column in ("done", "cancelled"):
        err["start_timer_now"] = "برای کار تمام‌شده نمی‌توان تایمر زد"
    r = v.recurrence
    if r.get("type"):
        if r["type"] not in RECURRENCE_TYPES:
            err["recurrence"] = "نوع تکرار نامعتبر است"
        elif int(r.get("interval", 1)) < 1:
            err["recurrence"] = "فاصله‌ی تکرار باید حداقل ۱ باشد"
        elif not v.start:
            err["recurrence"] = "برای تکرار، زمان شروع لازم است"
    if any(m < 0 for m in v.reminders):
        err["reminders"] = "یادآور نامعتبر است"
    if any(not c.get("text", "").strip() for c in v.checklist):
        err["checklist"] = "آیتم خالی در چک‌لیست هست"
    return err


# ---------------------------------------------------------------- conversion
def from_entry(db: Database, e: TimeEntry) -> TaskValues:
    deps = [r[0] for r in db.conn.execute("SELECT depends_on FROM dependencies WHERE task_id=?", (e.id,))]
    rec = dict(e.recurrence or {})
    scheduled = e.end_utc is not None
    return TaskValues(title=e.title, description=e.description, project_id=e.project_id, category=e.category, subcategory=e.subcategory, priority=e.priority,
                      column=e.column, tags=list(e.tags), assignee=e.assignee, color=e.color, icon=e.icon, all_day=e.all_day,
                      start=e.start_utc if scheduled or e.status != Status.PLANNED else None, end=e.end_utc, due=e.due_utc,
                      estimated_min=e.estimated_min, energy=e.energy, location=e.location, billable=e.billable, rate=e.extra.get("rate"),
                      checklist=[dict(c) for c in e.checklist], depends_on=deps, progress=e.progress, notes=e.notes, attachments=list(e.attachments),
                      recurrence=rec, reminders=list(e.reminders), important=e.important)


def _rule(rec: Dict[str, Any]) -> str:
    t, n = rec.get("type"), int(rec.get("interval", 1) or 1)
    if t == "custom" or (t in ("daily", "weekly", "monthly") and n > 1):
        mult = {"daily": 1, "weekly": 7, "monthly": 30, "custom": 1}[t]
        return f"every:{n * mult}"
    return t or ""


def apply(db: Database, v: TaskValues, entry: Optional[TimeEntry] = None, now: Optional[dt.datetime] = None) -> TimeEntry:
    """Validate and persist atomically: the entry, new subtasks, dependencies, recurrence copies and (optionally) a running timer."""
    errors = validate(v)
    if errors:
        raise ValueError("; ".join(errors.values()))
    now = now or now_utc()
    new = entry is None
    with db.transaction():
        e = entry or TimeEntry(title=v.title.strip(), start_utc=v.start or now)
        e.title, e.description, e.project_id = v.title.strip(), v.description.strip(), v.project_id
        e.category, e.subcategory, e.priority, e.column = v.category, v.subcategory, v.priority, v.column
        e.tags, e.assignee, e.color, e.icon, e.all_day = sorted(set(t.strip() for t in v.tags if t.strip())), v.assignee, v.color, v.icon, v.all_day
        e.due_utc, e.estimated_min, e.energy, e.location, e.billable = v.due, v.estimated_min, v.energy, v.location, v.billable
        e.important, e.notes, e.attachments = v.important, v.notes, list(v.attachments)
        e.checklist = [{"text": c["text"].strip(), "done": bool(c.get("done"))} for c in v.checklist]
        e.recurrence, e.reminders = dict(v.recurrence) if v.recurrence.get("type") else {}, sorted(set(v.reminders))
        extra = dict(e.extra)
        if v.rate is not None: extra["rate"] = v.rate
        else: extra.pop("rate", None)
        e.extra = extra
        e.progress = 100 if v.column == "done" else v.progress
        if v.start:
            e.start_utc, e.end_utc = v.start, v.end
        else:
            e.start_utc = e.start_utc if not new else now
            e.end_utc = None if not v.end else v.end
        if v.column == "done":
            e.status, e.completed_at = Status.DONE, e.completed_at or now
            if e.end_utc and e.start_utc: e.duration_sec = int((e.end_utc - e.start_utc).total_seconds())
        else:
            e.status = Status.RUNNING if (not new and e.status == Status.RUNNING and v.column == "in_progress") else Status.PLANNED
            e.completed_at = None
            if e.end_utc and e.start_utc: e.duration_sec = 0
        e.updated_at = now
        db.save(e)
        # --- subtasks (new ones only; existing ones are managed on the board)
        for title in (s.strip() for s in v.subtasks):
            if title and not e.parent_id:
                db.save(TimeEntry(title=title, start_utc=now, status=Status.PLANNED, project_id=e.project_id, parent_id=e.id, category=e.category, priority=e.priority))
        # --- dependencies: replace the set, keep graph acyclic
        if v.depends_on is not None:
            from .projects import ProjectService
            svc = ProjectService(db)
            current = {r[0] for r in db.conn.execute("SELECT depends_on FROM dependencies WHERE task_id=?", (e.id,))}
            for dep in current - set(v.depends_on):
                db.conn.execute("DELETE FROM dependencies WHERE task_id=? AND depends_on=?", (e.id, dep))
            for dep in set(v.depends_on) - current:
                if dep != e.id:
                    svc.add_dependency(e.id, dep)
        # --- recurrence copies (first save only, 60 max)
        if new and e.recurrence.get("type") and e.end_utc:
            from . import recurrence
            until = dt.datetime.fromisoformat(e.recurrence["until"]) if e.recurrence.get("until") else e.start_utc + dt.timedelta(days=90)
            recurrence.expand(db, e.id, _rule(e.recurrence), until)
        # --- timer
        if v.start_timer_now:
            for r in db.running_entries():
                if r.id != e.id:
                    from .tracker import Tracker
                    Tracker(db).stop(entry_id=r.id)
            e.status, e.start_utc, e.end_utc, e.column = Status.RUNNING, now, None, "in_progress"
            db.save(e)
    return e
