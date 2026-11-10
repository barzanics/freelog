"""Dataclass models with a single serialization point (``to_row``/``from_row``).

Rules: datetimes are stored as UTC ISO-8601 text, enums as plain strings,
lists/dicts as JSON text. Nothing else in the code base touches that format.
"""
from __future__ import annotations

import datetime as dt
import json
import uuid
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar

from .persian import UTC, now_utc

T = TypeVar("T")


class Status(str, Enum):
    """Lifecycle of a time entry."""
    RUNNING = "running"
    DONE = "done"
    PLANNED = "planned"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"


def new_id() -> str:
    """Short unique id."""
    return uuid.uuid4().hex[:16]


def _dump_dt(value: Optional[dt.datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("naive datetime rejected; use aware UTC datetimes")
    return value.astimezone(UTC).isoformat()


def _load_dt(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class _Row:
    """Mixin giving every model symmetric row (de)serialization."""

    JSON_FIELDS: tuple = ()
    DT_FIELDS: tuple = ()
    ENUM_FIELDS: Dict[str, Type[Enum]] = {}
    BOOL_FIELDS: tuple = ()

    def to_row(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in fields(self):  # type: ignore[arg-type]
            v = getattr(self, f.name)
            if f.name in self.JSON_FIELDS:
                v = json.dumps(v, ensure_ascii=False)
            elif f.name in self.DT_FIELDS:
                v = _dump_dt(v)
            elif f.name in self.ENUM_FIELDS:
                v = v.value if isinstance(v, Enum) else str(v)
            elif f.name in self.BOOL_FIELDS:
                v = int(bool(v))
            out[f.name] = v
        return out

    @classmethod
    def from_row(cls: Type[T], row: Mapping[str, Any]) -> T:
        kwargs: Dict[str, Any] = {}
        for f in fields(cls):  # type: ignore[arg-type]
            if f.name not in row.keys():
                continue
            v = row[f.name]
            if f.name in cls.JSON_FIELDS:  # type: ignore[attr-defined]
                v = json.loads(v) if v else ({} if f.name in ("extra", "recurrence", "apps") else [])
            elif f.name in cls.DT_FIELDS:  # type: ignore[attr-defined]
                v = _load_dt(v)
            elif f.name in cls.ENUM_FIELDS:  # type: ignore[attr-defined]
                v = cls.ENUM_FIELDS[f.name](v)  # type: ignore[attr-defined]
            elif f.name in cls.BOOL_FIELDS:  # type: ignore[attr-defined]
                v = bool(v)
            kwargs[f.name] = v
        return cls(**kwargs)  # type: ignore[call-arg]


@dataclass
class Project(_Row):
    name: str
    id: str = field(default_factory=new_id)
    code: str = ""
    description: str = ""
    client_id: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: str = "#6D5DFC"
    icon: str = "📁"
    estimated_hours: float = 0.0
    budget: float = 0.0
    rate_per_hour: float = 0.0
    currency: str = "IRR"
    deadline: Optional[dt.datetime] = None
    tags: List[str] = field(default_factory=list)
    created_at: dt.datetime = field(default_factory=now_utc)
    updated_at: dt.datetime = field(default_factory=now_utc)
    priority: int = 3
    start: Optional[dt.datetime] = None
    team_members: List[str] = field(default_factory=list)   # member ids
    dependencies: List[str] = field(default_factory=list)   # other project ids
    notes: str = ""

    JSON_FIELDS = ("tags", "team_members", "dependencies")
    DT_FIELDS = ("deadline", "created_at", "updated_at", "start")
    ENUM_FIELDS = {"status": ProjectStatus}

    def __post_init__(self) -> None:
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be 1..5")
        if self.start and self.deadline and self.deadline < self.start:
            raise ValueError("deadline before start")
        if self.id in self.dependencies:
            raise ValueError("project cannot depend on itself")


@dataclass
class Client(_Row):
    name: str
    id: str = field(default_factory=new_id)
    email: str = ""
    phone: str = ""
    default_rate: float = 0.0
    currency: str = "IRR"
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: dt.datetime = field(default_factory=now_utc)
    company: str = ""
    address: str = ""

    JSON_FIELDS = ("tags",)
    DT_FIELDS = ("created_at",)


@dataclass
class TimeEntry(_Row):
    """A tracked (or planned) block of work."""
    title: str
    start_utc: dt.datetime
    id: str = field(default_factory=new_id)
    end_utc: Optional[dt.datetime] = None
    duration_sec: int = 0
    project_id: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    priority: int = 3
    status: Status = Status.DONE
    billable: bool = False
    estimated_min: int = 0
    energy: int = 0  # 0 = unset, 1-5
    notes: str = ""
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)  # plugin-owned data (e.g. calendar link)
    created_at: dt.datetime = field(default_factory=now_utc)
    updated_at: dt.datetime = field(default_factory=now_utc)
    sprint_id: Optional[str] = None
    milestone_id: Optional[str] = None
    parent_id: Optional[str] = None
    column: str = "backlog"          # kanban: backlog / in_progress / review / done
    location: str = ""
    interruptions: int = 0
    mood: str = ""
    due_utc: Optional[dt.datetime] = None
    important: bool = False          # Eisenhower
    invoice_id: Optional[str] = None
    completed_at: Optional[dt.datetime] = None
    notes_private: str = ""          # ciphertext only (see services.security.encrypt_text); never plaintext
    subcategory: str = ""
    progress: int = 0                # 0..100
    color: str = ""
    icon: str = ""
    recurrence: Dict[str, Any] = field(default_factory=dict)   # {"type": "weekly", "interval": 1, "end": iso|None}
    reminders: List[int] = field(default_factory=list)         # minutes before start
    all_day: bool = False
    rank: float = 0.0                # manual order inside a list/column (drag & drop)
    source: str = "manual"           # manual / timer / auto / checkin / import
    assignee: str = ""               # member id
    description: str = ""            # long text (the v5 task form had a separate description from notes)
    attachments: List[str] = field(default_factory=list)       # file paths

    JSON_FIELDS = ("tags", "checklist", "extra", "recurrence", "reminders", "attachments")
    DT_FIELDS = ("start_utc", "end_utc", "created_at", "updated_at", "due_utc", "completed_at")
    ENUM_FIELDS = {"status": Status}
    BOOL_FIELDS = ("billable", "important", "all_day")

    def __post_init__(self) -> None:
        if self.end_utc is not None and self.end_utc < self.start_utc:
            raise ValueError("end before start")
        if self.end_utc is not None and not self.duration_sec and self.status == Status.DONE:       # planned blocks have a *length*, not worked time
            self.duration_sec = int((self.end_utc - self.start_utc).total_seconds())
        if not 0 <= self.energy <= 5:
            raise ValueError("energy must be 0..5")
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be 1..5")
        if not 0 <= self.progress <= 100:
            raise ValueError("progress must be 0..100")

    def is_overdue(self, now: Optional[dt.datetime] = None) -> bool:
        """Past its due date and not done."""
        return bool(self.due_utc and self.status != Status.DONE and (now or now_utc()) > self.due_utc)

    @property
    def variance_min(self) -> Optional[float]:
        """Actual minus estimated minutes (None when no estimate)."""
        return self.duration_sec / 60 - self.estimated_min if self.estimated_min else None


@dataclass
class Invoice(_Row):
    client_id: str
    id: str = field(default_factory=new_id)
    number: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)  # {desc, hours, rate}
    tax_percent: float = 0.0
    discount: float = 0.0
    paid: float = 0.0
    currency: str = "IRR"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issued_at: dt.datetime = field(default_factory=now_utc)

    JSON_FIELDS = ("items",)
    DT_FIELDS = ("issued_at",)
    ENUM_FIELDS = {"status": InvoiceStatus}

    @property
    def subtotal(self) -> float:
        return round(sum(float(i.get("hours", 0)) * float(i.get("rate", 0)) for i in self.items), 2)

    @property
    def total(self) -> float:
        """(subtotal - discount) + tax, never negative."""
        base = max(0.0, self.subtotal - self.discount)
        return round(base * (1 + self.tax_percent / 100), 2)

    @property
    def balance(self) -> float:
        return round(max(0.0, self.total - self.paid), 2)

    def apply_payment(self, amount: float) -> None:
        """Record a payment and update status."""
        if amount <= 0:
            raise ValueError("payment must be positive")
        self.paid = round(self.paid + amount, 2)
        self.status = InvoiceStatus.PAID if self.balance == 0 else InvoiceStatus.PARTIAL


KANBAN_COLUMNS = ("backlog", "in_progress", "review", "done")
ALL_COLUMNS = ("backlog", "in_progress", "review", "delayed", "done", "cancelled")   # v5 statuses: pending/in_progress/review/delayed/completed/cancelled


@dataclass
class Milestone(_Row):
    project_id: str
    name: str
    id: str = field(default_factory=new_id)
    due: Optional[dt.datetime] = None
    completed: bool = False
    completed_at: Optional[dt.datetime] = None
    deliverables: List[str] = field(default_factory=list)
    notes: str = ""

    JSON_FIELDS = ("deliverables",)
    DT_FIELDS = ("due", "completed_at")
    BOOL_FIELDS = ("completed",)


@dataclass
class Sprint(_Row):
    project_id: str
    name: str
    start: dt.datetime
    end: dt.datetime
    id: str = field(default_factory=new_id)
    goal: str = ""
    status: str = "planning"  # planning / active / completed
    capacity_hours: float = 0.0

    DT_FIELDS = ("start", "end")

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("sprint end must be after start")


@dataclass
class Dependency(_Row):
    task_id: str
    depends_on: str
    kind: str = "finish_to_start"  # finish_to_start / start_to_start / finish_to_finish / start_to_finish
    lag_days: int = 0
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        if self.task_id == self.depends_on:
            raise ValueError("a task cannot depend on itself")
        if self.kind not in ("finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"):
            raise ValueError("bad dependency kind")


@dataclass
class Habit(_Row):
    name: str
    id: str = field(default_factory=new_id)
    target_per_week: int = 7
    log: List[str] = field(default_factory=list)  # ISO dates (Tehran days)
    created_at: dt.datetime = field(default_factory=now_utc)
    icon: str = "💧"
    color: str = "#00E5FF"
    days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])   # weekdays (Mon=0) the habit applies to
    note: str = ""

    JSON_FIELDS = ("log", "days")
    DT_FIELDS = ("created_at",)


@dataclass
class Goal(_Row):
    """Objective with key results: [{name, target, current, unit}]."""
    name: str
    id: str = field(default_factory=new_id)
    key_results: List[Dict[str, Any]] = field(default_factory=list)
    deadline: Optional[dt.datetime] = None
    notes: str = ""

    JSON_FIELDS = ("key_results",)
    DT_FIELDS = ("deadline",)

    @property
    def progress(self) -> float:
        """Mean completion of key results, clamped to 0..1."""
        if not self.key_results:
            return 0.0
        parts = [min(1.0, max(0.0, float(k.get("current", 0)) / float(k["target"]))) if float(k.get("target", 0)) else 0.0
                 for k in self.key_results]
        return sum(parts) / len(parts)


@dataclass
class Template(_Row):
    """Reusable task template (e.g. daily standup)."""
    name: str
    id: str = field(default_factory=new_id)
    title: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    estimated_min: int = 30
    billable: bool = False

    JSON_FIELDS = ("tags",)
    BOOL_FIELDS = ("billable",)


@dataclass
class Rule(_Row):
    """Automation: if <attr> <op> <value> then <action>(<arg>)."""
    name: str
    attr: str = "duration_sec"
    op: str = ">"
    value: Any = 0
    action: str = "add_tag"          # add_tag / set_category / set_billable / webhook
    arg: str = ""
    id: str = field(default_factory=new_id)
    enabled: bool = True

    JSON_FIELDS = ("value",)
    BOOL_FIELDS = ("enabled",)


@dataclass
class Member(_Row):
    """Local team profile (no accounts, no cloud)."""
    name: str
    id: str = field(default_factory=new_id)
    role: str = ""
    email: str = ""
    color: str = "#00E5FF"
    hourly_cost: float = 0.0
    active: bool = True

    BOOL_FIELDS = ("active",)


@dataclass
class Comment(_Row):
    """Threaded comment on a task (parent_id = another comment id)."""
    entry_id: str
    author_id: str
    text: str
    id: str = field(default_factory=new_id)
    parent_id: Optional[str] = None
    mentions: List[str] = field(default_factory=list)  # member ids
    created_at: dt.datetime = field(default_factory=now_utc)

    JSON_FIELDS = ("mentions",)
    DT_FIELDS = ("created_at",)


@dataclass
class SavedFilter(_Row):
    name: str
    query: str
    id: str = field(default_factory=new_id)


@dataclass
class ActivityEvent(_Row):
    """A span in which one application/window was in the foreground."""
    app: str
    start_utc: dt.datetime
    end_utc: dt.datetime
    title: str = ""
    category: str = "other"
    id: str = field(default_factory=new_id)

    DT_FIELDS = ("start_utc", "end_utc")

    @property
    def seconds(self) -> int:
        return int((self.end_utc - self.start_utc).total_seconds())


@dataclass
class Screenshot(_Row):
    """Index row of one stored screenshot; the JPEG lives as ``member`` inside the daily zip ``path``."""
    at: dt.datetime
    path: str
    member: str = ""
    id: str = field(default_factory=new_id)
    app: str = ""
    title: str = ""
    bytes: int = 0
    width: int = 0
    height: int = 0
    sig: str = ""            # tiny content signature (used to skip identical consecutive screens)

    DT_FIELDS = ("at",)


@dataclass
class HourLog(_Row):
    """What happened in one clock hour (auto summary of apps + engagement), shown next to that hour's screenshot."""
    hour_start: dt.datetime
    id: str = field(default_factory=new_id)
    summary: str = ""
    apps: Dict[str, int] = field(default_factory=dict)     # app -> seconds
    engaged_sec: int = 0
    idle_sec: int = 0
    entry_ids: List[str] = field(default_factory=list)

    JSON_FIELDS = ("apps", "entry_ids")
    DT_FIELDS = ("hour_start",)


@dataclass
class PromptLog(_Row):
    """One "what did you do?" prompt and how the user answered it (for compliance reporting)."""
    shown_at: dt.datetime
    id: str = field(default_factory=new_id)
    answered_at: Optional[dt.datetime] = None
    action: str = ""            # logged / snoozed / away / skipped
    entry_id: Optional[str] = None
    covers_from: Optional[dt.datetime] = None
    covers_to: Optional[dt.datetime] = None

    DT_FIELDS = ("shown_at", "answered_at", "covers_from", "covers_to")
