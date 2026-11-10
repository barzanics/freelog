"""SQLite layer: WAL, versioned migrations, CRUD, backup, legacy import.

One connection, owned by the thread that created it (UI/main thread). Long
work should compute in workers and hand results back to the main thread.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Type, TypeVar, Union

from .models import (ActivityEvent, Client, Comment, Dependency, Goal, Habit, Invoice, Member, Milestone, Project, Rule,
                     SavedFilter, Screenshot, PromptLog, HourLog, Sprint, Status, Template, TimeEntry, new_id)
from .persian import UTC, now_utc, to_utc

log = logging.getLogger("worktracker.db")
T = TypeVar("T")

MIGRATIONS: List[str] = [
    # v1
    """
    CREATE TABLE clients (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT DEFAULT '', phone TEXT DEFAULT '',
        default_rate REAL DEFAULT 0, currency TEXT DEFAULT 'IRR', tags TEXT DEFAULT '[]',
        notes TEXT DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE projects (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, code TEXT DEFAULT '', description TEXT DEFAULT '',
        client_id TEXT REFERENCES clients(id) ON DELETE SET NULL, status TEXT DEFAULT 'active',
        color TEXT DEFAULT '#6D5DFC', icon TEXT DEFAULT '', estimated_hours REAL DEFAULT 0,
        budget REAL DEFAULT 0, rate_per_hour REAL DEFAULT 0, currency TEXT DEFAULT 'IRR',
        deadline TEXT, tags TEXT DEFAULT '[]', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE entries (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, start_utc TEXT NOT NULL, end_utc TEXT,
        duration_sec INTEGER DEFAULT 0, project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
        category TEXT DEFAULT 'general', tags TEXT DEFAULT '[]', priority INTEGER DEFAULT 3,
        status TEXT DEFAULT 'done', billable INTEGER DEFAULT 0, estimated_min INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 0, notes TEXT DEFAULT '', checklist TEXT DEFAULT '[]',
        extra TEXT DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE INDEX idx_entries_start ON entries(start_utc);
    CREATE INDEX idx_entries_project ON entries(project_id);
    CREATE INDEX idx_entries_status ON entries(status);
    CREATE TABLE invoices (
        id TEXT PRIMARY KEY, client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        number TEXT DEFAULT '', items TEXT DEFAULT '[]', tax_percent REAL DEFAULT 0,
        discount REAL DEFAULT 0, paid REAL DEFAULT 0, currency TEXT DEFAULT 'IRR',
        status TEXT DEFAULT 'draft', issued_at TEXT NOT NULL);
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
        entity TEXT NOT NULL, entity_id TEXT NOT NULL, action TEXT NOT NULL, detail TEXT DEFAULT '');
    """,
    # v2: project management, planning, habits, goals, templates, rules
    """
    ALTER TABLE entries ADD COLUMN sprint_id TEXT;
    ALTER TABLE entries ADD COLUMN milestone_id TEXT;
    ALTER TABLE entries ADD COLUMN parent_id TEXT;
    ALTER TABLE entries ADD COLUMN "column" TEXT DEFAULT 'backlog';
    ALTER TABLE entries ADD COLUMN location TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN interruptions INTEGER DEFAULT 0;
    ALTER TABLE entries ADD COLUMN mood TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN due_utc TEXT;
    ALTER TABLE entries ADD COLUMN important INTEGER DEFAULT 0;
    ALTER TABLE entries ADD COLUMN invoice_id TEXT;
    CREATE INDEX idx_entries_parent ON entries(parent_id);
    CREATE INDEX idx_entries_sprint ON entries(sprint_id);
    CREATE TABLE milestones (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        name TEXT NOT NULL, due TEXT, completed INTEGER DEFAULT 0, completed_at TEXT, deliverables TEXT DEFAULT '[]', notes TEXT DEFAULT '');
    CREATE TABLE sprints (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        name TEXT NOT NULL, start TEXT NOT NULL, "end" TEXT NOT NULL, goal TEXT DEFAULT '', status TEXT DEFAULT 'planning',
        capacity_hours REAL DEFAULT 0);
    CREATE TABLE dependencies (id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        depends_on TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE, kind TEXT DEFAULT 'finish_to_start',
        lag_days INTEGER DEFAULT 0, UNIQUE(task_id, depends_on));
    CREATE TABLE habits (id TEXT PRIMARY KEY, name TEXT NOT NULL, target_per_week INTEGER DEFAULT 7, log TEXT DEFAULT '[]', created_at TEXT NOT NULL);
    CREATE TABLE goals (id TEXT PRIMARY KEY, name TEXT NOT NULL, key_results TEXT DEFAULT '[]', deadline TEXT, notes TEXT DEFAULT '');
    CREATE TABLE templates (id TEXT PRIMARY KEY, name TEXT NOT NULL, title TEXT DEFAULT '', category TEXT DEFAULT 'general',
        tags TEXT DEFAULT '[]', estimated_min INTEGER DEFAULT 30, billable INTEGER DEFAULT 0);
    CREATE TABLE rules (id TEXT PRIMARY KEY, name TEXT NOT NULL, attr TEXT, op TEXT, value TEXT, action TEXT, arg TEXT DEFAULT '', enabled INTEGER DEFAULT 1);
    """,
    # v3: team, comments, saved filters, activity events
    """
    CREATE TABLE members (id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT DEFAULT '', email TEXT DEFAULT '',
        color TEXT DEFAULT '#00E5FF', hourly_cost REAL DEFAULT 0, active INTEGER DEFAULT 1);
    CREATE TABLE comments (id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        author_id TEXT NOT NULL, text TEXT NOT NULL, parent_id TEXT, mentions TEXT DEFAULT '[]', created_at TEXT NOT NULL);
    CREATE INDEX idx_comments_entry ON comments(entry_id);
    CREATE TABLE saved_filters (id TEXT PRIMARY KEY, name TEXT NOT NULL, query TEXT NOT NULL);
    CREATE TABLE activity_events (id TEXT PRIMARY KEY, app TEXT NOT NULL, start_utc TEXT NOT NULL, end_utc TEXT NOT NULL,
        title TEXT DEFAULT '', category TEXT DEFAULT 'other');
    CREATE INDEX idx_activity_start ON activity_events(start_utc);
    CREATE INDEX idx_audit_entity ON audit_log(entity_id, id);
    """,
    # v4: fuller project fields, completion time, private (encrypted) notes
    """
    ALTER TABLE projects ADD COLUMN priority INTEGER DEFAULT 3;
    ALTER TABLE projects ADD COLUMN start TEXT;
    ALTER TABLE projects ADD COLUMN team_members TEXT DEFAULT '[]';
    ALTER TABLE projects ADD COLUMN dependencies TEXT DEFAULT '[]';
    ALTER TABLE projects ADD COLUMN notes TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN completed_at TEXT;
    ALTER TABLE entries ADD COLUMN notes_private TEXT DEFAULT '';
    """,
    # v5: everything the v5 app's task form had + manual ordering, hourly screenshots index, hourly log, prompt compliance
    """
    ALTER TABLE entries ADD COLUMN description TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN subcategory TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN progress INTEGER DEFAULT 0;
    ALTER TABLE entries ADD COLUMN color TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN icon TEXT DEFAULT '';
    ALTER TABLE entries ADD COLUMN recurrence TEXT DEFAULT '{}';
    ALTER TABLE entries ADD COLUMN reminders TEXT DEFAULT '[]';
    ALTER TABLE entries ADD COLUMN attachments TEXT DEFAULT '[]';
    ALTER TABLE entries ADD COLUMN all_day INTEGER DEFAULT 0;
    ALTER TABLE entries ADD COLUMN rank REAL DEFAULT 0;
    ALTER TABLE entries ADD COLUMN source TEXT DEFAULT 'manual';
    ALTER TABLE entries ADD COLUMN assignee TEXT DEFAULT '';
    ALTER TABLE habits ADD COLUMN icon TEXT DEFAULT '💧';
    ALTER TABLE habits ADD COLUMN color TEXT DEFAULT '#00E5FF';
    ALTER TABLE habits ADD COLUMN days TEXT DEFAULT '[0,1,2,3,4,5,6]';
    ALTER TABLE habits ADD COLUMN note TEXT DEFAULT '';
    ALTER TABLE clients ADD COLUMN company TEXT DEFAULT '';
    ALTER TABLE clients ADD COLUMN address TEXT DEFAULT '';
    CREATE TABLE screenshots (id TEXT PRIMARY KEY, at TEXT NOT NULL, path TEXT NOT NULL, member TEXT DEFAULT '',
        app TEXT DEFAULT '', title TEXT DEFAULT '', bytes INTEGER DEFAULT 0, width INTEGER DEFAULT 0, height INTEGER DEFAULT 0, sig TEXT DEFAULT '');
    CREATE INDEX idx_shots_at ON screenshots(at);
    CREATE TABLE hour_log (id TEXT PRIMARY KEY, hour_start TEXT NOT NULL UNIQUE, summary TEXT DEFAULT '', apps TEXT DEFAULT '{}',
        engaged_sec INTEGER DEFAULT 0, idle_sec INTEGER DEFAULT 0, entry_ids TEXT DEFAULT '[]');
    CREATE TABLE prompt_log (id TEXT PRIMARY KEY, shown_at TEXT NOT NULL, answered_at TEXT, action TEXT DEFAULT '', entry_id TEXT,
        covers_from TEXT, covers_to TEXT);
    CREATE INDEX idx_prompt_time ON prompt_log(shown_at);
    """,
]

_TABLES: Dict[type, str] = {Project: "projects", Client: "clients", TimeEntry: "entries", Invoice: "invoices",
                            Milestone: "milestones", Sprint: "sprints", Dependency: "dependencies", Habit: "habits",
                            Goal: "goals", Template: "templates", Rule: "rules", Member: "members", Comment: "comments",
                            SavedFilter: "saved_filters", ActivityEvent: "activity_events", Screenshot: "screenshots", PromptLog: "prompt_log", HourLog: "hour_log"}
_QUOTED = {"column", "end", "rank"}  # SQL keywords used as column names


def _unpack(text: str) -> str:
    """Audit details older than 90 days may be gzip+base64 compressed (see services.maintenance)."""
    if text.startswith("gz:"):
        import base64, gzip
        return gzip.decompress(base64.b64decode(text[3:])).decode("utf-8")
    return text


def _q(col: str) -> str:
    return f'"{col}"' if col in _QUOTED else col


class Database:
    """Thin, explicit data-access object."""

    def __init__(self, path: Union[str, Path] = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, cached_statements=256)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        if self.path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.migrate()

    # ---- lifecycle -------------------------------------------------
    @property
    def version(self) -> int:
        return int(self.conn.execute("PRAGMA user_version").fetchone()[0])

    def migrate(self) -> None:
        """Apply pending migrations atomically, one version at a time."""
        for v in range(self.version, len(MIGRATIONS)):
            try:
                self.conn.executescript("BEGIN;" + MIGRATIONS[v] + f"PRAGMA user_version={v + 1};COMMIT;")
            except sqlite3.Error:
                self.conn.rollback()
                raise
            log.info("migrated to v%d", v + 1)

    def close(self) -> None:
        try:
            self.conn.close()
        except sqlite3.Error:  # pragma: no cover
            log.exception("close failed")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit on success, rollback on any error. Nestable: only the outermost block commits/rolls back."""
        self._depth = getattr(self, "_depth", 0) + 1
        try:
            yield self.conn
        except BaseException:
            if self._depth == 1:
                self.conn.rollback()
            raise
        else:
            if self._depth == 1:
                self.conn.commit()
        finally:
            self._depth -= 1

    # ---- generic CRUD ---------------------------------------------
    def save(self, obj: Any, touch: bool = True) -> None:
        """Insert or replace one model. ``touch=False`` keeps ``updated_at`` (used by sync/import)."""
        table = _TABLES[type(obj)]
        if touch and hasattr(obj, "updated_at"):
            obj.updated_at = now_utc()
        row = obj.to_row()
        cols = ",".join(_q(c) for c in row)
        marks = ",".join("?" * len(row))
        # A real UPSERT, never INSERT OR REPLACE: REPLACE deletes the old row first, which fires ON DELETE CASCADE / SET NULL on every
        # child row (editing a client used to delete its invoices; editing a task used to delete its dependencies and comments).
        updates = ",".join(f"{_q(c)}=excluded.{_q(c)}" for c in row if c != "id")
        sql = f"INSERT INTO {table} ({cols}) VALUES ({marks}) ON CONFLICT(id) DO UPDATE SET {updates}" if updates else f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({marks})"
        with self.transaction() as c:
            existed = c.execute(f"SELECT 1 FROM {table} WHERE id=?", (obj.id,)).fetchone()
            c.execute(sql, tuple(row.values()))
            self._audit(c, table, obj.id, "update" if existed else "create", row)

    def get(self, cls: Type[T], obj_id: str) -> Optional[T]:
        row = self.conn.execute(f"SELECT * FROM {_TABLES[cls]} WHERE id=?", (obj_id,)).fetchone()
        return cls.from_row(row) if row else None  # type: ignore[attr-defined]

    def delete(self, cls: type, obj_id: str) -> bool:
        table = _TABLES[cls]
        with self.transaction() as c:
            before = c.execute(f"SELECT * FROM {table} WHERE id=?", (obj_id,)).fetchone()
            n = c.execute(f"DELETE FROM {table} WHERE id=?", (obj_id,)).rowcount
            if n:
                self._audit(c, table, obj_id, "delete", dict(before))
        return bool(n)

    def all(self, cls: Type[T], order: str = "rowid") -> List[T]:
        if order not in {"rowid", "name", "created_at", "start_utc DESC", "start_utc", "start", "due"}:
            raise ValueError("bad order")
        rows = self.conn.execute(f"SELECT * FROM {_TABLES[cls]} ORDER BY {order}").fetchall()
        return [cls.from_row(r) for r in rows]  # type: ignore[attr-defined]

    @staticmethod
    def _audit(c: sqlite3.Connection, entity: str, eid: str, action: str, snapshot: Optional[dict] = None) -> None:
        """Append to the audit log. ``detail`` holds the row snapshot (version history / time travel)."""
        c.execute("INSERT INTO audit_log(at,entity,entity_id,action,detail) VALUES (?,?,?,?,?)",
                  (now_utc().isoformat(), entity, eid, action, json.dumps(snapshot, ensure_ascii=False, default=str) if snapshot else ""))

    def history(self, cls: type, obj_id: str) -> List[Dict[str, Any]]:
        """All recorded versions of an object, oldest first: [{at, action, row}]."""
        rows = self.conn.execute("SELECT at, action, detail FROM audit_log WHERE entity=? AND entity_id=? ORDER BY id",
                                 (_TABLES[cls], obj_id)).fetchall()
        return [{"at": r[0], "action": r[1], "row": json.loads(_unpack(r[2])) if r[2] else None} for r in rows]

    def entries_as_of(self, moment: dt.datetime) -> List[TimeEntry]:
        """Time travel: the entries as they existed at ``moment`` (reconstructed from the audit log)."""
        rows = self.conn.execute(
            "SELECT a.entity_id, a.action, a.detail FROM audit_log a JOIN (SELECT entity_id, MAX(id) mid FROM audit_log "
            "WHERE entity='entries' AND at<=? GROUP BY entity_id) m ON a.id=m.mid", (moment.astimezone(UTC).isoformat(),)).fetchall()
        out = [TimeEntry.from_row(json.loads(_unpack(r[2]))) for r in rows if r[1] != "delete" and r[2]]
        return sorted(out, key=lambda e: e.start_utc)

    def prune_audit(self, keep_days: int = 365) -> int:
        cutoff = (now_utc() - dt.timedelta(days=keep_days)).isoformat()
        with self.transaction() as c:
            return c.execute("DELETE FROM audit_log WHERE at<?", (cutoff,)).rowcount

    def running_entries(self) -> List[TimeEntry]:
        rows = self.conn.execute("SELECT * FROM entries WHERE status='running' ORDER BY start_utc").fetchall()
        return [TimeEntry.from_row(r) for r in rows]

    # ---- entry queries --------------------------------------------
    def entries_between(self, start: dt.datetime, end: dt.datetime, project_id: Optional[str] = None,
                        only_done: bool = True) -> List[TimeEntry]:
        """Entries with start in [start, end). Bounds must be aware."""
        sql = "SELECT * FROM entries WHERE start_utc>=? AND start_utc<?"
        args: List[Any] = [start.astimezone(UTC).isoformat(), end.astimezone(UTC).isoformat()]
        if project_id:
            sql += " AND project_id=?"
            args.append(project_id)
        if only_done:
            sql += " AND status='done'"
        rows = self.conn.execute(sql + " ORDER BY start_utc", args).fetchall()
        return [TimeEntry.from_row(r) for r in rows]

    def running_entry(self) -> Optional[TimeEntry]:
        row = self.conn.execute("SELECT * FROM entries WHERE status='running' ORDER BY start_utc DESC LIMIT 1").fetchone()
        return TimeEntry.from_row(row) if row else None

    def search(self, text: str, limit: int = 100) -> List[TimeEntry]:
        """Case-insensitive substring search over title/notes/tags (escaped LIKE)."""
        esc = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{esc}%"
        rows = self.conn.execute(
            "SELECT * FROM entries WHERE title LIKE ? ESCAPE '\\' OR notes LIKE ? ESCAPE '\\' "
            "OR tags LIKE ? ESCAPE '\\' ORDER BY start_utc DESC LIMIT ?", (like, like, like, limit)).fetchall()
        return [TimeEntry.from_row(r) for r in rows]

    # ---- settings --------------------------------------------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key: str, value: Any) -> None:
        with self.transaction() as c:
            c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))

    # ---- backup / integrity ---------------------------------------
    def backup(self, dest: Union[str, Path]) -> Path:
        """Consistent online backup using SQLite's backup API."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(str(dest))
        try:
            self.conn.backup(target)
        finally:
            target.close()
        return dest

    def integrity_ok(self) -> bool:
        return self.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    def rotate_backups(self, folder: Union[str, Path], keep: int = 14) -> Path:
        """Create a dated backup and prune old ones, keeping the newest ``keep``."""
        folder = Path(folder)
        out = self.backup(folder / f"worktracker-{now_utc():%Y%m%d-%H%M%S-%f}.db")
        files = sorted(folder.glob("worktracker-*.db"))
        for old in files[:-keep]:
            old.unlink(missing_ok=True)
        return out


# ---------------------------------------------------------------------
# Legacy (v5) import
# ---------------------------------------------------------------------
def _legacy_dt(value: Any) -> Optional[dt.datetime]:
    """Legacy stored naive local (Tehran) timestamps; make them aware UTC."""
    if not value:
        return None
    text = str(value).replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return to_utc(dt.datetime.strptime(text[:26], fmt))
        except ValueError:
            continue
    try:
        return to_utc(dt.datetime.fromisoformat(str(value)))
    except ValueError:
        return None


def import_legacy(db: Database, legacy_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Dict[str, int]:
    """Import projects/tasks/tags from a v5 database. Non-destructive and idempotent.

    The legacy file is opened read-only and copied first when ``backup_dir`` is given.
    Returns counts of imported/skipped rows.
    """
    legacy_path = Path(legacy_path)
    if backup_dir:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_path, Path(backup_dir) / f"legacy-{legacy_path.name}")
    src = sqlite3.connect(f"file:{legacy_path.as_posix()}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    stats = {"projects": 0, "entries": 0, "skipped": 0}
    try:
        tag_map: Dict[str, List[str]] = {}
        try:
            for r in src.execute("SELECT tt.task_id, t.name FROM task_tags tt JOIN tags t ON t.id=tt.tag_id"):
                tag_map.setdefault(r["task_id"], []).append(r["name"])
        except sqlite3.Error:
            log.info("legacy tags table not available")
        with db.transaction() as c:
            for r in src.execute("SELECT * FROM projects"):
                if c.execute("SELECT 1 FROM projects WHERE id=?", (r["id"],)).fetchone():
                    stats["skipped"] += 1
                    continue
                p = Project(id=r["id"], name=r["name"] or "?", description=r["description"] or "",
                            color=r["color"] or "#6D5DFC", icon=r["icon"] or "📁", budget=float(r["budget"] or 0),
                            deadline=_legacy_dt(r["deadline"]), created_at=_legacy_dt(r["created_at"]) or now_utc())
                row = p.to_row()
                c.execute(f"INSERT INTO projects ({','.join(_q(k) for k in row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
                stats["projects"] += 1
            for r in src.execute("SELECT * FROM tasks"):
                if c.execute("SELECT 1 FROM entries WHERE id=?", (r["id"],)).fetchone():
                    stats["skipped"] += 1
                    continue
                start, end = _legacy_dt(r["start_time"]), _legacy_dt(r["end_time"])
                if start is None:
                    stats["skipped"] += 1
                    continue
                if end is not None and end < start:
                    end = start
                actual = int(r["actual_minutes"] or 0) * 60
                done = (r["status"] or "") in ("completed", "done")
                pid = r["project_id"]
                if pid and not c.execute("SELECT 1 FROM projects WHERE id=?", (pid,)).fetchone():
                    pid = None
                e = TimeEntry(id=r["id"], title=r["title"] or "(untitled)", start_utc=start, end_utc=end,
                              duration_sec=actual or (int((end - start).total_seconds()) if end else 0),
                              project_id=pid, category=r["category"] or "general",
                              tags=tag_map.get(r["id"], []), priority=min(5, max(1, int(r["priority"] or 3))),
                              status=Status.DONE if done else Status.PLANNED,
                              estimated_min=int(r["estimated_minutes"] or 0), notes=r["notes"] or "",
                              extra={"legacy": True, "calendar_event_id": r["calendar_event_id"]} if r["calendar_event_id"] else {"legacy": True})
                row = e.to_row()
                c.execute(f"INSERT INTO entries ({','.join(_q(k) for k in row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
                stats["entries"] += 1
    finally:
        src.close()
    return stats
