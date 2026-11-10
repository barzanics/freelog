"""Bulk entry from pasted text: ``2026-05-01 09:00-10:30 write docs #docs @Project``."""
from __future__ import annotations

import datetime as dt
import re
from typing import Dict, List, Tuple

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, parse_jalali, to_en_digits

_LINE = re.compile(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s+(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})\s+(.+)$")


def parse_line(line: str) -> Tuple[dt.datetime, dt.datetime, str, List[str], str]:
    m = _LINE.match(to_en_digits(line.strip()))
    if not m:
        raise ValueError("expected: YYYY-MM-DD HH:MM-HH:MM title #tag @project")
    ds = m.group(1).replace("/", "-")
    y, mo, d = (int(x) for x in ds.split("-"))
    day = parse_jalali(ds) if y < 1700 else dt.date(y, mo, d)
    sh, sm, eh, em = (int(m.group(i)) for i in (2, 3, 4, 5))
    start = dt.datetime.combine(day, dt.time(sh, sm), tzinfo=TEHRAN)
    end = dt.datetime.combine(day, dt.time(eh, em), tzinfo=TEHRAN)
    if end <= start:
        end += dt.timedelta(days=1)            # crossing midnight
    tags, proj, words = [], "", []
    for tok in m.group(6).split():
        if tok.startswith("#") and len(tok) > 1: tags.append(tok[1:])
        elif tok.startswith("@") and len(tok) > 1: proj = tok[1:]
        else: words.append(tok)
    if not words:
        raise ValueError("title is required")
    return start.astimezone(UTC), end.astimezone(UTC), " ".join(words), tags, proj


def bulk_add(db: Database, text: str) -> Dict[str, object]:
    """All-or-nothing import of many lines; returns ``{added, errors:[(line_no, message)]}`` (nothing saved if any line is bad)."""
    projects = {p.name.lower(): p.id for p in db.all(Project)}
    parsed, errors = [], []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        try:
            parsed.append(parse_line(line))
        except ValueError as exc:
            errors.append((n, str(exc)))
    if errors:
        return {"added": 0, "errors": errors}
    with db.transaction():
        for s, e, title, tags, proj in parsed:
            db.save(TimeEntry(title=title, start_utc=s, end_utc=e, tags=tags, project_id=projects.get(proj.lower()), status=Status.DONE))
    return {"added": len(parsed), "errors": []}
