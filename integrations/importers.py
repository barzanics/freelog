"""Import from Toggl / Clockify CSV exports (all times assumed Tehran unless ``tz`` given)."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC

_DATE = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d.%m.%Y")
_TIME = ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p")


def _parse_dt(d: str, t: str, tz: dt.tzinfo) -> dt.datetime:
    for df in _DATE:
        for tf in _TIME:
            try:
                return dt.datetime.strptime(f"{d.strip()} {t.strip()}", f"{df} {tf}").replace(tzinfo=tz).astimezone(UTC)
            except ValueError:
                continue
    raise ValueError(f"bad date/time: {d} {t}")


def _import(db: Database, path: Union[str, Path], cols: Dict[str, str], tz: dt.tzinfo) -> Dict[str, int]:
    stats = {"entries": 0, "skipped": 0, "projects": 0}
    by_name: Dict[str, str] = {p.name: p.id for p in db.all(Project)}
    with Path(path).open(encoding="utf-8-sig", newline="") as fh, db.transaction():
        for row in csv.DictReader(fh):
            try:
                start = _parse_dt(row[cols["sd"]], row[cols["st"]], tz)
                end = _parse_dt(row[cols["ed"]], row[cols["et"]], tz)
                if end <= start:
                    raise ValueError("non-positive duration")
            except (KeyError, ValueError):
                stats["skipped"] += 1
                continue
            pname = (row.get(cols["project"]) or "").strip()
            pid = None
            if pname:
                if pname not in by_name:
                    p = Project(name=pname)
                    db.save(p)
                    by_name[pname] = p.id
                    stats["projects"] += 1
                pid = by_name[pname]
            tags = [t.strip() for t in (row.get(cols["tags"]) or "").split(",") if t.strip()]
            billable = (row.get(cols["billable"]) or "").strip().lower() in ("yes", "true", "1")
            db.save(TimeEntry(title=(row.get(cols["desc"]) or "(no description)").strip(), start_utc=start, end_utc=end,
                              project_id=pid, tags=tags, billable=billable, status=Status.DONE, extra={"imported": cols["name"]}))
            stats["entries"] += 1
    return stats


def import_toggl(db: Database, path: Union[str, Path], tz: dt.tzinfo = TEHRAN) -> Dict[str, int]:
    return _import(db, path, {"name": "toggl", "sd": "Start date", "st": "Start time", "ed": "End date", "et": "End time",
                              "project": "Project", "desc": "Description", "tags": "Tags", "billable": "Billable"}, tz)


def import_clockify(db: Database, path: Union[str, Path], tz: dt.tzinfo = TEHRAN) -> Dict[str, int]:
    return _import(db, path, {"name": "clockify", "sd": "Start Date", "st": "Start Time", "ed": "End Date", "et": "End Time",
                              "project": "Project", "desc": "Description", "tags": "Tags", "billable": "Billable"}, tz)


def import_rescuetime(db: Database, path: Union[str, Path], tz: dt.tzinfo = TEHRAN) -> Dict[str, int]:
    """RescueTime CSV (Date, Time Spent (seconds), Activity, Category) -> activity events.

    The export has no clock times, so events are laid out back-to-back starting 09:00 local on each date (documented approximation).
    """
    from ..core.models import ActivityEvent
    from ..services.activity import classify
    stats = {"events": 0, "skipped": 0}
    cursor: Dict[str, dt.datetime] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as fh, db.transaction():
        for row in csv.DictReader(fh):
            try:
                day = (row["Date"] or "").strip()[:10]
                secs = int(float(row["Time Spent (seconds)"]))
                app = (row["Activity"] or "").strip()
                if secs <= 0 or not app:
                    raise ValueError
                start = cursor.get(day) or dt.datetime.strptime(day, "%Y-%m-%d").replace(hour=9, tzinfo=tz).astimezone(UTC)
            except (KeyError, ValueError):
                stats["skipped"] += 1
                continue
            end = start + dt.timedelta(seconds=secs)
            cursor[day] = end
            db.save(ActivityEvent(app=app[:100], start_utc=start, end_utc=end, category=classify(app, row.get("Category", ""))))
            stats["events"] += 1
    return stats
