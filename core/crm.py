"""Tiny, safe data access for the client-reporting tables (clients' extras, reports, feedback, promises, meetings, risks, deliverables, ...).

Table and column names are validated against the live schema (never interpolated from input), values are bound parameters, JSON columns are encoded/decoded transparently and
datetimes are stored as ISO-8601 strings - so services stay short and a wrong column name fails loudly instead of corrupting data.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Sequence

from .database import Database
from .models import new_id

JSON_COLUMNS = {"settings", "report_settings", "baseline", "payload", "recipients", "action_items", "attendees", "deliverables", "reminders", "exdates", "recurrence"}


class Store:
    def __init__(self, db: Database) -> None:
        self.db = db
        self._cols: Dict[str, List[str]] = {}

    def columns(self, table: str) -> List[str]:
        if table not in self._cols:
            names = {r[0] for r in self.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if table not in names:
                raise ValueError(f"unknown table: {table}")
            self._cols[table] = [r[1] for r in self.db.conn.execute(f'PRAGMA table_info("{table}")')]
        return self._cols[table]

    @staticmethod
    def _enc(col: str, v: Any) -> Any:
        if isinstance(v, (dt.datetime, dt.date)):
            return v.isoformat()
        if isinstance(v, bool):
            return int(v)
        if col in JSON_COLUMNS and not isinstance(v, str):
            return json.dumps(v, ensure_ascii=False)
        return v

    @staticmethod
    def _dec(row: Any) -> Dict[str, Any]:
        d = dict(row)
        for k in JSON_COLUMNS & set(d):
            try:
                d[k] = json.loads(d[k]) if isinstance(d[k], str) else d[k]
            except ValueError:
                pass
        return d

    def _check(self, table: str, fields: Dict[str, Any]) -> None:
        bad = set(fields) - set(self.columns(table))
        if bad:
            raise ValueError(f"unknown column(s) for {table}: {sorted(bad)}")

    def add(self, table: str, **f: Any) -> Dict[str, Any]:
        f.setdefault("id", new_id())
        self._check(table, f)
        with self.db.transaction() as c:
            c.execute(f'INSERT INTO "{table}" ({",".join(chr(34) + k + chr(34) for k in f)}) VALUES ({",".join("?" * len(f))})', [self._enc(k, v) for k, v in f.items()])
        return self.get(table, f["id"]) or {}

    def get(self, table: str, row_id: str) -> Optional[Dict[str, Any]]:
        self.columns(table)
        r = self.db.conn.execute(f'SELECT * FROM "{table}" WHERE id=?', (row_id,)).fetchone()
        return self._dec(r) if r else None

    def update(self, table: str, row_id: str, **f: Any) -> Dict[str, Any]:
        self._check(table, f)
        if not f:
            return self.get(table, row_id) or {}
        with self.db.transaction() as c:
            cur = c.execute(f'UPDATE "{table}" SET {",".join(chr(34) + k + chr(34) + "=?" for k in f)} WHERE id=?', [self._enc(k, v) for k, v in f.items()] + [row_id])
            if cur.rowcount == 0:
                raise KeyError(row_id)
        return self.get(table, row_id) or {}

    def rows(self, table: str, where: str = "", params: Sequence[Any] = (), order: str = "", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """``where`` / ``order`` are developer-written SQL fragments (never user input); values always go through ``params``."""
        self.columns(table)
        q = f'SELECT * FROM "{table}"' + (f" WHERE {where}" if where else "") + (f" ORDER BY {order}" if order else "") + (f" LIMIT {int(limit)}" if limit else "")
        return [self._dec(r) for r in self.db.conn.execute(q, tuple(params)).fetchall()]

    def delete(self, table: str, row_id: str) -> bool:
        self.columns(table)
        with self.db.transaction() as c:
            return c.execute(f'DELETE FROM "{table}" WHERE id=?', (row_id,)).rowcount > 0
