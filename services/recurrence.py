"""Recurring planned tasks: daily / weekly / monthly (Gregorian month-day, clamped) expansion."""
from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import replace
from typing import List

from ..core.database import Database
from ..core.models import Status, TimeEntry, new_id


def occurrences(start: dt.datetime, rule: str, until: dt.datetime, limit: int = 500) -> List[dt.datetime]:
    """Dates after ``start`` up to ``until``. Rules: ``daily``, ``weekly``, ``monthly`` or ``every:N`` (days)."""
    out: List[dt.datetime] = []
    if rule.startswith("every:"):
        step = int(rule.split(":")[1])
        if step < 1:
            raise ValueError("step must be >= 1")
    elif rule in ("daily", "weekly", "monthly"):
        step = 1 if rule == "daily" else 7
    else:
        raise ValueError(f"unknown rule {rule!r}")
    n = 1
    while len(out) < limit:
        if rule == "monthly":
            m0 = start.month - 1 + n
            y, m = start.year + m0 // 12, m0 % 12 + 1
            cur = start.replace(year=y, month=m, day=min(start.day, calendar.monthrange(y, m)[1]))
        else:
            cur = start + dt.timedelta(days=step * n)
        if cur > until:
            break
        out.append(cur)
        n += 1
    return out


def expand(db: Database, entry_id: str, rule: str, until: dt.datetime) -> List[TimeEntry]:
    """Create planned copies of an entry; idempotent per (source, start)."""
    src = db.get(TimeEntry, entry_id)
    if src is None:
        raise KeyError(entry_id)
    existing = {e.start_utc for e in db.all(TimeEntry) if e.extra.get("recurs_from") == src.id}
    made: List[TimeEntry] = []
    span = (src.end_utc - src.start_utc) if src.end_utc else None
    with db.transaction():
        for when in occurrences(src.start_utc, rule, until):
            if when in existing:
                continue
            e = replace(src, id=new_id(), start_utc=when, end_utc=when + span if span else None, duration_sec=0,
                        status=Status.PLANNED, extra={**src.extra, "recurs_from": src.id}, invoice_id=None, recurrence={})
            db.save(e)
            made.append(e)
    return made
