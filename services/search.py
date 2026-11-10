"""Smart search: `tag:bug project:app >2h <30m after:1405/01/01 billable:yes fix login`."""
from __future__ import annotations

import datetime as dt
import difflib
import re
import shlex
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.database import Database
from ..core.models import Project, TimeEntry
from ..core.persian import TEHRAN, UTC, parse_jalali, to_en_digits

_DUR = re.compile(r"^([<>]=?)(\d+(?:\.\d+)?)([hm])$")


@dataclass
class Query:
    terms: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    billable: Optional[bool] = None
    min_sec: Optional[float] = None
    max_sec: Optional[float] = None
    after: Optional[dt.datetime] = None
    before: Optional[dt.datetime] = None


def _date(text: str) -> dt.datetime:
    text = to_en_digits(text).replace("-", "/")
    y = int(text.split("/")[0])
    d = parse_jalali(text) if y < 1700 else dt.date(*(int(x) for x in text.split("/")))
    return dt.datetime.combine(d, dt.time(), tzinfo=TEHRAN).astimezone(UTC)


def parse(text: str) -> Query:
    q = Query()
    try:
        parts = shlex.split(to_en_digits(text))
    except ValueError:
        parts = text.split()
    for tok in parts:
        m = _DUR.match(tok)
        if m:
            sec = float(m.group(2)) * (3600 if m.group(3) == "h" else 60)
            if m.group(1).startswith(">"):
                q.min_sec = sec
            else:
                q.max_sec = sec
        elif ":" in tok and tok.split(":", 1)[0] in ("tag", "project", "category", "status", "billable", "after", "before"):
            k, v = tok.split(":", 1)
            if k == "tag": q.tags.append(v.lower())
            elif k == "project": q.project = v.lower()
            elif k == "category": q.category = v.lower()
            elif k == "status": q.status = v.lower()
            elif k == "billable": q.billable = v.lower() in ("yes", "true", "1", "y")
            elif k == "after": q.after = _date(v)
            elif k == "before": q.before = _date(v)
        else:
            q.terms.append(tok.lower())
    return q


def _fuzzy(term: str, text: str) -> bool:
    text = text.lower()
    if term in text:
        return True
    return any(difflib.SequenceMatcher(None, term, w).ratio() >= 0.8 for w in re.split(r"\W+", text) if w)


def run(db: Database, text: str, limit: int = 200) -> List[TimeEntry]:
    q = parse(text)
    names = {p.id: p.name.lower() for p in db.all(Project)}
    out: List[TimeEntry] = []
    for e in db.all(TimeEntry, "start_utc DESC"):
        if q.after and e.start_utc < q.after: continue
        if q.before and e.start_utc >= q.before: continue
        if q.min_sec is not None and e.duration_sec <= q.min_sec: continue
        if q.max_sec is not None and e.duration_sec >= q.max_sec: continue
        if q.billable is not None and e.billable != q.billable: continue
        if q.status and e.status.value != q.status: continue
        if q.category and e.category.lower() != q.category: continue
        if q.project and q.project not in names.get(e.project_id or "", ""): continue
        if q.tags and not all(t in [x.lower() for x in e.tags] for t in q.tags): continue
        hay = f"{e.title} {e.notes} {' '.join(e.tags)}"
        if not all(_fuzzy(t, hay) for t in q.terms): continue
        out.append(e)
        if len(out) >= limit:
            break
    return out
