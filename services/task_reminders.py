"""Task reminders: which (task, offset) pairs should fire now. Fired pairs are remembered so nothing repeats after a restart."""
from __future__ import annotations

import datetime as dt
from typing import Callable, Dict, List, Tuple

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import now_utc


def due(db: Database, now: dt.datetime = None, window_min: int = 120) -> List[Tuple[TimeEntry, int]]:
    """Reminders whose moment has arrived (start - offset <= now < start+1min) and were not fired yet."""
    now = now or now_utc()
    fired: Dict[str, str] = db.get_setting("fired_reminders", {})
    out: List[Tuple[TimeEntry, int]] = []
    lo, hi = now - dt.timedelta(minutes=5), now + dt.timedelta(minutes=window_min + 1440)
    for r in db.conn.execute("SELECT * FROM entries WHERE status IN ('planned') AND reminders!='[]' AND start_utc>=? AND start_utc<=?", ((now - dt.timedelta(minutes=5)).isoformat(), hi.isoformat())):
        e = TimeEntry.from_row(r)
        if e.column in ("done", "cancelled"):
            continue
        for off in e.reminders:
            moment = e.start_utc - dt.timedelta(minutes=off)
            key = f"{e.id}:{off}:{e.start_utc.isoformat()}"
            if moment <= now < e.start_utc + dt.timedelta(minutes=1) and key not in fired:
                out.append((e, off))
    return out


def mark_fired(db: Database, items: List[Tuple[TimeEntry, int]], now: dt.datetime = None) -> None:
    now = now or now_utc()
    fired = db.get_setting("fired_reminders", {})
    for e, off in items:
        fired[f"{e.id}:{off}:{e.start_utc.isoformat()}"] = now.isoformat()
    cutoff = (now - dt.timedelta(days=3)).isoformat()
    db.set_setting("fired_reminders", {k: v for k, v in fired.items() if v >= cutoff})


def overdue(db: Database, now: dt.datetime = None) -> List[TimeEntry]:
    now = now or now_utc()
    return [e for e in db.all(TimeEntry) if e.is_overdue(now) and e.column not in ("cancelled",) and not e.parent_id]
