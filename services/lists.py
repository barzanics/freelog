"""Task lists in the style of Google Tasks: several named lists, tick to complete, drag between lists, reorder inside a list, star, indent into sub-tasks.

A task is an ordinary entry (``TimeEntry``) whose ``extra["list"]`` names its list, so it also shows up on the board, in reports and in search.
Lists themselves live in the settings table (``task_lists``), so backups and configuration export carry them.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Status, TimeEntry, new_id
from ..core.persian import TEHRAN, UTC, now_utc, tr
from . import outline


class ListError(ValueError):
    """Invalid list operation (message is user-facing)."""


# ------------------------------------------------------------------ lists
def lists(db: Database) -> List[Dict[str, Any]]:
    return list(db.get_setting("task_lists", []))


def ensure_default(db: Database) -> Dict[str, Any]:
    items = lists(db)
    if not items:
        items = [{"id": "default", "name": tr("کارهای من", "My tasks"), "color": "", "gid": None}]
        db.set_setting("task_lists", items)
    return items[0]


def get_list(db: Database, list_id: str) -> Optional[Dict[str, Any]]:
    return next((l for l in lists(db) if l["id"] == list_id), None)


def add_list(db: Database, name: str, color: str = "") -> Dict[str, Any]:
    name = name.strip()
    if not name or len(name) > 60:
        raise ListError(tr("نام لیست باید بین ۱ تا ۶۰ نویسه باشد", "A list name must be 1-60 characters"))
    ensure_default(db)
    items = lists(db)
    if any(l["name"].lower() == name.lower() for l in items):
        raise ListError(tr("لیستی با این نام هست", "A list with this name already exists"))
    it = {"id": new_id(), "name": name, "color": color, "gid": None}
    db.set_setting("task_lists", items + [it])
    return it


def rename_list(db: Database, list_id: str, name: str) -> None:
    name = name.strip()
    items = lists(db)
    if not name:
        raise ListError(tr("نام لیست را وارد کنید", "Enter a list name"))
    if any(l["name"].lower() == name.lower() and l["id"] != list_id for l in items):
        raise ListError(tr("لیستی با این نام هست", "A list with this name already exists"))
    for l in items:
        if l["id"] == list_id:
            l["name"] = name
            db.set_setting("task_lists", items)
            return
    raise KeyError(list_id)


def set_remote_id(db: Database, list_id: str, gid: Optional[str]) -> None:
    items = lists(db)
    for l in items:
        if l["id"] == list_id:
            l["gid"] = gid
    db.set_setting("task_lists", items)


def reorder_lists(db: Database, ids: List[str]) -> None:
    items = {l["id"]: l for l in lists(db)}
    ordered = [items[i] for i in ids if i in items] + [l for i, l in items.items() if i not in ids]
    db.set_setting("task_lists", ordered)


def delete_list(db: Database, list_id: str, move_to: Optional[str] = None) -> int:
    """Remove a list. Its tasks move to ``move_to`` or, without it, are deleted. The last list cannot be removed. Returns how many tasks were affected."""
    items = lists(db)
    if len(items) <= 1:
        raise ListError(tr("آخرین لیست را نمی‌شود حذف کرد", "The last list cannot be deleted"))
    if move_to is not None and (move_to == list_id or get_list(db, move_to) is None):
        raise ListError(tr("لیست مقصد معتبر نیست", "Invalid target list"))
    affected = 0
    with db.transaction():
        for e in _all_in(db, list_id, with_children=True):
            if move_to:
                e.extra = {**e.extra, "list": move_to}; db.save(e)
            else:
                _tombstone(db, e); db.delete(TimeEntry, e.id)
            affected += 1
        db.set_setting("task_lists", [l for l in items if l["id"] != list_id])
    return affected


# ------------------------------------------------------------------ tasks
def _all_in(db: Database, list_id: str, with_children: bool = False) -> List[TimeEntry]:
    out = [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE extra LIKE '%\"list\"%'")]
    out = [e for e in out if e.extra.get("list") == list_id]
    return out if with_children else [e for e in out if not e.parent_id]


def is_done(e: TimeEntry) -> bool:
    return e.column == "done" or e.status == Status.DONE


def tasks(db: Database, list_id: str, include_done: bool = True) -> List[TimeEntry]:
    """Open tasks in manual order first, then completed ones (newest first). Cancelled/remotely-deleted tasks are hidden."""
    ts = [e for e in _all_in(db, list_id) if e.column != "cancelled"]
    open_ = sorted((e for e in ts if not is_done(e)), key=lambda e: (e.rank, e.created_at))
    done = sorted((e for e in ts if is_done(e)), key=lambda e: e.completed_at or e.created_at, reverse=True)
    return open_ + (done if include_done else [])


def children(db: Database, parent_id: str) -> List[TimeEntry]:
    return [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE parent_id=? ORDER BY rank, created_at", (parent_id,))]


def counts(db: Database, list_id: str) -> Tuple[int, int]:
    ts = tasks(db, list_id)
    d = sum(1 for e in ts if is_done(e))
    return len(ts) - d, d


def _touch(e: TimeEntry, now: Optional[dt.datetime] = None) -> None:
    e.updated_at = now or now_utc()


def add_task(db: Database, list_id: str, title: str, due: Optional[dt.date] = None, notes: str = "", starred: bool = False, parent_id: Optional[str] = None,
             now: Optional[dt.datetime] = None) -> TimeEntry:
    title = title.strip()
    if not title:
        raise ListError(tr("عنوان را وارد کنید", "Enter a title"))
    if get_list(db, list_id) is None:
        raise ListError(tr("لیست پیدا نشد", "List not found"))
    now = now or now_utc()
    open_ranks = [e.rank for e in tasks(db, list_id, include_done=False)]
    e = TimeEntry(title=title, start_utc=now, status=Status.PLANNED, column="backlog", description=notes.strip(), important=starred, parent_id=parent_id,
                  due_utc=dt.datetime.combine(due, dt.time(), tzinfo=TEHRAN).astimezone(UTC) if due else None, extra={"list": list_id},
                  rank=(min(open_ranks) - 10.0) if open_ranks else 0.0, source="list")             # new tasks go to the top, like Google Tasks
    _touch(e, now)
    db.save(e)
    return e


def update_task(db: Database, entry_id: str, title: Optional[str] = None, notes: Optional[str] = None, due: Optional[dt.date] = ..., now: Optional[dt.datetime] = None) -> TimeEntry:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    if title is not None:
        if not title.strip():
            raise ListError(tr("عنوان را وارد کنید", "Enter a title"))
        e.title = title.strip()
    if notes is not None:
        e.description = notes.strip()
    if due is not ...:
        e.due_utc = dt.datetime.combine(due, dt.time(), tzinfo=TEHRAN).astimezone(UTC) if due else None
    _touch(e, now)
    db.save(e)
    return e


def toggle(db: Database, entry_id: str, now: Optional[dt.datetime] = None) -> bool:
    """Tick / untick. Returns True when the task is now done."""
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    now = now or now_utc()
    if is_done(e):
        e.column, e.status, e.completed_at, e.progress = "backlog", Status.PLANNED, None, 0
    else:
        e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, now, 100
    _touch(e, now)
    db.save(e)
    return is_done(e)


def star(db: Database, entry_id: str) -> bool:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.important = not e.important
    _touch(e)
    db.save(e)
    return e.important


def _renumber(db: Database, ordered: List[TimeEntry]) -> None:
    for i, e in enumerate(ordered):
        if e.rank != i * 10.0:
            e.rank = i * 10.0
            _touch(e); db.save(e)


def reorder(db: Database, list_id: str, ordered_ids: List[str]) -> None:
    """Make the open tasks follow ``ordered_ids`` (unknown ids are ignored; omitted tasks keep their relative order after the listed ones)."""
    open_ = tasks(db, list_id, include_done=False)
    by_id = {e.id: e for e in open_}
    first = [by_id[i] for i in ordered_ids if i in by_id]
    rest = [e for e in open_ if e.id not in set(ordered_ids)]
    with db.transaction():
        _renumber(db, first + rest)


def move(db: Database, entry_id: str, to_list: str, index: int = 0) -> None:
    """Drag a task into another list (or another position) - its sub-tasks go with it."""
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    if get_list(db, to_list) is None:
        raise ListError(tr("لیست مقصد پیدا نشد", "Target list not found"))
    if e.parent_id:
        e.parent_id = None                                                              # dragging a sub-task out promotes it
    with db.transaction():
        old = e.extra.get("list")
        e.extra = {**e.extra, "list": to_list}
        _touch(e); db.save(e)
        for c in children(db, e.id):
            c.extra = {**c.extra, "list": to_list}; _touch(c); db.save(c)
        dest = [t for t in tasks(db, to_list, include_done=False) if t.id != e.id]
        index = max(0, min(index, len(dest)))
        dest.insert(index, db.get(TimeEntry, e.id))
        _renumber(db, dest)
        if old and old != to_list:
            _renumber(db, tasks(db, old, include_done=False))


def indent(db: Database, entry_id: str) -> bool:
    """Make a task a sub-task of the open task just above it (one level deep). Returns False when that is impossible."""
    e = db.get(TimeEntry, entry_id)
    if e is None or e.parent_id:
        return False
    open_ = tasks(db, e.extra.get("list", ""), include_done=False)
    i = next((k for k, t in enumerate(open_) if t.id == entry_id), -1)
    if i <= 0 or children(db, entry_id):
        return False
    e.parent_id = open_[i - 1].id
    _touch(e); db.save(e)
    return True


def outdent(db: Database, entry_id: str) -> bool:
    e = db.get(TimeEntry, entry_id)
    if e is None or not e.parent_id:
        return False
    e.parent_id = None
    _touch(e); db.save(e)
    return True


def _tombstone(db: Database, e: TimeEntry) -> None:
    """Remember a deleted task that exists in Google Tasks so the next sync can delete it there too."""
    gid = e.extra.get("gid")
    if gid:
        lst = get_list(db, e.extra.get("list", "")) or {}
        t = db.get_setting("gtasks_deleted", [])
        t.append({"gid": gid, "list_gid": lst.get("gid")})
        db.set_setting("gtasks_deleted", t)


def delete_task(db: Database, entry_id: str) -> bool:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        return False
    with db.transaction():
        for c in children(db, entry_id):
            _tombstone(db, c); db.delete(TimeEntry, c.id)
        _tombstone(db, e)
        db.delete(TimeEntry, entry_id)
    return True


def clear_completed(db: Database, list_id: str) -> int:
    done = [e for e in tasks(db, list_id) if is_done(e)]
    for e in done:
        delete_task(db, e.id)
    return len(done)


def sort_by_due(db: Database, list_id: str) -> None:
    far = dt.datetime.max.replace(tzinfo=UTC)
    open_ = sorted(tasks(db, list_id, include_done=False), key=lambda e: (e.due_utc or far, e.rank))
    with db.transaction():
        _renumber(db, open_)


def bulk_add(db: Database, list_id: str, text: str, now: Optional[dt.datetime] = None, max_items: int = 500) -> List[TimeEntry]:
    """Paste a whole check list at once. ``- [ ] a`` / ``- [x] b`` / indented lines become tasks / done tasks / sub-tasks; ``#tag @project 45m d:2026-05-03 !star`` are understood.
    The pasted order is kept at the top of the list. Returns every created entry (parents first)."""
    if get_list(db, list_id) is None:
        raise ListError(tr("لیست پیدا نشد", "List not found"))
    roots = outline.parse(text, max_depth=2, max_lines=max_items)
    if not roots:
        raise ListError(tr("چیزی برای افزودن پیدا نشد", "Nothing to add"))
    from .quickadd import resolve_project
    now = now or now_utc()
    open_ranks = [e.rank for e in tasks(db, list_id, include_done=False)]
    base = (min(open_ranks) if open_ranks else 0.0) - 10.0 * len(roots)
    out: List[TimeEntry] = []

    def make(node, parent_id: Optional[str], rank: float) -> TimeEntry:
        e = TimeEntry(title=node.title, start_utc=now, status=Status.PLANNED, column="backlog", important=node.starred, parent_id=parent_id, tags=list(node.tags),
                      project_id=resolve_project(db, node.project), estimated_min=node.minutes, extra={"list": list_id}, rank=rank, source="list",
                      due_utc=dt.datetime.combine(node.due, dt.time(), tzinfo=TEHRAN).astimezone(UTC) if node.due else None)
        if node.done:
            e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, now, 100
        _touch(e, now)
        db.save(e)
        out.append(e)
        return e

    with db.transaction():
        for i, root in enumerate(roots):
            parent = make(root, None, base + 10.0 * i)
            for j, child in enumerate(c for c in root.walk() if c is not root):
                make(child, parent.id, 10.0 * j)
    return out
