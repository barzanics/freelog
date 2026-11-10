"""Export everything (the user owns the data). Heavy libs are imported lazily."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Union

from ..core.database import Database
from ..core.models import Client, Invoice, Project, TimeEntry
from ..core.persian import to_tehran

CSV_HEADER = ["id", "title", "project", "category", "tags", "start_tehran", "end_tehran",
              "duration_min", "billable", "notes"]


def export_json(db: Database, dest: Union[str, Path]) -> Path:
    """Full lossless dump of every entity."""
    dest = Path(dest)
    data = {"version": 1,
            "projects": [p.to_row() for p in db.all(Project)],
            "clients": [c.to_row() for c in db.all(Client)],
            "entries": [e.to_row() for e in db.all(TimeEntry)],
            "invoices": [i.to_row() for i in db.all(Invoice)]}
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return dest


def _rows(db: Database):
    names = {p.id: p.name for p in db.all(Project)}
    for e in db.all(TimeEntry, "start_utc"):
        yield [e.id, e.title, names.get(e.project_id or "", ""), e.category, ";".join(e.tags),
               to_tehran(e.start_utc).strftime("%Y-%m-%d %H:%M"),
               to_tehran(e.end_utc).strftime("%Y-%m-%d %H:%M") if e.end_utc else "",
               round(e.duration_sec / 60, 1), int(e.billable), e.notes]


def _safe(cell):
    """Neutralise spreadsheet formula injection (=, +, -, @ at start)."""
    return "'" + cell if isinstance(cell, str) and cell[:1] in ("=", "+", "-", "@") else cell


def export_csv(db: Database, dest: Union[str, Path]) -> Path:
    """UTF-8 (with BOM so Excel shows Persian correctly)."""
    dest = Path(dest)
    with dest.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_HEADER)
        for row in _rows(db):
            w.writerow([_safe(c) for c in row])
    return dest


def export_xlsx(db: Database, dest: Union[str, Path]) -> Path:
    """Excel export (requires openpyxl, imported lazily)."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Entries"
    ws.sheet_view.rightToLeft = True
    ws.append(CSV_HEADER)
    for row in _rows(db):
        ws.append([_safe(c) for c in row])
    wb.save(str(dest))
    return Path(dest)


def import_json(db: Database, src: Union[str, Path]) -> int:
    """Re-import an ``export_json`` dump (idempotent; existing ids are overwritten)."""
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    n = 0
    with db.transaction():
        for key, cls in (("clients", Client), ("projects", Project), ("entries", TimeEntry), ("invoices", Invoice)):
            for row in data.get(key, []):
                db.save(cls.from_row(row))
                n += 1
    return n
