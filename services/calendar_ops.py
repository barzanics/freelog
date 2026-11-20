"""What the calendar UI does to your data, without any Qt: list what is shown in a range, create / move / resize / delete an item (an event or a planned task block), pick colours.
Drag-and-drop in the time grid ends in exactly one of these calls, so the behaviour is unit-tested."""
from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any, Dict, List, Optional

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import UTC, now_utc, tr
from . import calendar_events as ce, taskform as tf


class CalendarError(ValueError):
    """Illegal calendar operation (message is user-facing)."""


def project_colors(db: Database, palette: List[str]) -> Dict[str, str]:
    """Project -> colour: the project's own colour, else a stable pick from the palette (the same project is always the same colour)."""
    out = {}
    for p in db.all(Project):
        out[p.id] = p.color if p.color and p.color.startswith("#") else palette[int(hashlib.blake2b(p.id.encode(), digest_size=2).hexdigest(), 16) % len(palette)]
    return out


def items_for_range(db: Database, start: dt.datetime, end: dt.datetime) -> List[Dict[str, Any]]:
    """Events (recurrences expanded) and planned task blocks that overlap [start, end). Time logs are NOT here - they are the separate 'actual' lane."""
    items: List[Dict[str, Any]] = []
    for o in ce.occurrences(db, start, end):
        items.append({**o, "source": "event", "id": o["event_id"], "occ_start": o["start"], "done": False})
    for r in db.conn.execute("SELECT * FROM entries WHERE status='planned' AND column NOT IN ('cancelled') AND end_utc IS NOT NULL AND start_utc<? AND end_utc>? AND source NOT IN ('auto','prompt','quick')",
                             (end.astimezone(UTC).isoformat(), start.astimezone(UTC).isoformat())):
        e = TimeEntry.from_row(r)
        items.append({"source": "entry", "id": e.id, "occ_id": e.id, "event_id": None, "title": e.title, "kind": "task", "start": e.start_utc, "end": e.end_utc, "occ_start": e.start_utc, "all_day": False,
                      "link": "", "project_id": e.project_id, "color": e.color, "location": "", "recurring": False, "auto_open": False, "done": e.column == "done", "reminders": []})
    return sorted(items, key=lambda i: (i["start"], i["title"]))


def create_item(db: Database, kind: str, title: str, start: dt.datetime, end: dt.datetime, **kw: Any) -> Dict[str, Any]:
    """``kind`` 'task' makes a planned task block (it appears on the board and in reports); every other kind makes an event with reminders."""
    if end <= start:
        raise CalendarError(tr("پایان باید بعد از شروع باشد", "The end must be after the start"))
    if kind == "task":
        e = tf.apply(db, tf.TaskValues(title=title, start=start, end=end, estimated_min=int((end - start).total_seconds() // 60), project_id=kw.get("project_id"), column="backlog"))
        return {"source": "entry", "id": e.id}
    ev = ce.add_event(db, title, start, end, kind, **kw)
    return {"source": "event", "id": ev["id"]}


def move_item(db: Database, item: Dict[str, Any], new_start: dt.datetime, new_end: dt.datetime, scope: str = "this") -> None:
    """Drag (move) or resize. Events go through the recurrence-aware mover; a task block simply gets its new times. Finished time logs cannot be moved."""
    if new_end <= new_start:
        raise CalendarError(tr("پایان باید بعد از شروع باشد", "The end must be after the start"))
    if item["source"] == "event":
        ce.move_occurrence(db, item["id"], item["occ_start"], new_start, new_end, scope)
        return
    e = db.get(TimeEntry, item["id"])
    if e is None:
        raise KeyError(item["id"])
    if e.status == Status.DONE:
        raise CalendarError(tr("زمان ثبت‌شده را نمی‌شود جابه‌جا کرد", "Logged time cannot be moved"))
    e.start_utc, e.end_utc = new_start.astimezone(UTC), new_end.astimezone(UTC)
    e.estimated_min = max(e.estimated_min, 0) if e.estimated_min and e.estimated_min == int((item["end"] - item["start"]).total_seconds() // 60) and False else int((new_end - new_start).total_seconds() // 60)
    e.updated_at = now_utc()
    db.save(e, touch=False)


def delete_item(db: Database, item: Dict[str, Any], scope: str = "this") -> None:
    if item["source"] == "event":
        if scope == "all":
            ce.delete_event(db, item["id"])
        else:
            ce.skip_occurrence(db, item["id"], item["occ_start"])
        return
    db.delete(TimeEntry, item["id"])


def duplicate_item(db: Database, item: Dict[str, Any], days: int = 1) -> Dict[str, Any]:
    d = dt.timedelta(days=days)
    if item["source"] == "event":
        ev = ce.get_event(db, item["id"])
        n = ce.add_event(db, ev["title"], item["start"] + d, item["end"] + d, ev["kind"], project_id=ev["project_id"], client_id=ev["client_id"], location=ev["location"], link=ev["link"],
                         notes=ev["notes"], reminders=ev["reminders"], auto_open=bool(ev["auto_open"]), color=ev["color"])
        return {"source": "event", "id": n["id"]}
    return create_item(db, "task", item["title"], item["start"] + d, item["end"] + d, project_id=item.get("project_id"))
