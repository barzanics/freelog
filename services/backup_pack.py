"""Accurate export / restore of EVERYTHING (data + configuration) and of the configuration alone.

Package (``.wtpack``, a zip; optionally AES-256-GCM encrypted):
    manifest.json   format, versions, counts and the SHA-256 of every file
    data/<table>.jsonl   one JSON object per row, every table, lossless
    settings.json   the whole settings table
    screenshots/*.zip    (optional) the daily screenshot archives

Restore is verified first (format, schema version, checksums, columns) and then applied in ONE transaction, so it either fully succeeds or leaves the
database untouched. A safety copy of the current database is made before ``replace``. ``merge`` upserts by id (newer ``updated_at`` wins).
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import io
import json
import logging
import re
import shutil
import sqlite3
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from .. import __version__
from ..core.database import Database
from ..core.persian import now_utc
from . import security

log = logging.getLogger("worktracker.backup")
FORMAT, FORMAT_VERSION = "worktracker-package", 1
CONFIG_FORMAT, CONFIG_VERSION = "worktracker-config", 1
TABLE_ORDER = ("clients", "projects", "members", "entries", "dependencies", "milestones", "sprints", "comments", "invoices", "habits", "goals", "templates", "rules",
               "saved_filters", "activity_events", "screenshots", "hour_log", "prompt_log", "audit_log")
# settings that describe live state or this particular machine - never part of a *configuration* export
VOLATILE_KEYS = {"fired_reminders", "reminder_last", "prompter_state", "pomodoro_state", "notifications", "invoice_seq", "float_pos", "wallpaper", "sync_folder", "tips_online", "nb_category"}
SECRET_KEYS = {"api_token", "tg_token", "slack_url", "webhook_url"}
_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
MAX_VALUE_BYTES = 512 * 1024


class PackageError(Exception):
    """The file is not a valid / compatible WorkTracker package."""


class VerificationError(PackageError):
    """A checksum or structure check failed (corrupt or tampered file)."""


class RestoreError(Exception):
    """Applying the package failed; the database was rolled back."""


@dataclass
class RestoreReport:
    mode: str
    tables: Dict[str, Dict[str, int]] = field(default_factory=dict)      # table -> {inserted, updated, skipped}
    settings_applied: int = 0
    screenshots_copied: int = 0
    safety_backup: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_rows(self) -> int:
        return sum(v["inserted"] + v["updated"] for v in self.tables.values())


# ------------------------------------------------------------------------ helpers
def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _jsonable(v: Any) -> Any:
    return {"__b64__": base64.b64encode(v).decode("ascii")} if isinstance(v, (bytes, bytearray)) else v


def _unjson(v: Any) -> Any:
    return base64.b64decode(v["__b64__"]) if isinstance(v, dict) and "__b64__" in v else v


def user_tables(conn: sqlite3.Connection) -> List[str]:
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    ordered = [t for t in TABLE_ORDER if t in names]
    return ordered + sorted(n for n in names if n not in ordered and n != "settings")


def columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]


def dump_table(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    cur = conn.execute(f'SELECT * FROM "{table}"')
    names = [d[0] for d in cur.description]
    return [dict(zip(names, (_jsonable(v) for v in row))) for row in cur.fetchall()]


def snapshot(db: Database, include_history: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """Every table as plain dicts (also used by the tests to prove a restore is exact)."""
    out = {t: dump_table(db.conn, t) for t in user_tables(db.conn) if include_history or t != "audit_log"}
    out["settings"] = dump_table(db.conn, "settings")
    return out


# ------------------------------------------------------------------------ export
def export_package(db: Database, dest: Union[str, Path], include_history: bool = False, screenshots_dir: Optional[Union[str, Path]] = None,
                   password: Optional[str] = None, note: str = "") -> Path:
    """Write a complete, verifiable backup. ``include_history`` adds the audit log (version history); ``screenshots_dir`` adds the daily zips."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    files: Dict[str, bytes] = {}
    counts: Dict[str, int] = {}
    db.conn.commit()
    db.conn.execute("BEGIN")                                    # one consistent read snapshot for every table
    try:
        for t in user_tables(db.conn):
            if t == "audit_log" and not include_history:
                continue
            rows = dump_table(db.conn, t)
            counts[t] = len(rows)
            files[f"data/{t}.jsonl"] = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows).encode("utf-8")
        settings = {r["key"]: r["value"] for r in dump_table(db.conn, "settings")}
        files["settings.json"] = json.dumps(settings, ensure_ascii=False, indent=1).encode("utf-8")
        schema = int(db.conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        db.conn.rollback()
    shots = 0
    if screenshots_dir and Path(screenshots_dir).exists():
        for z in sorted(Path(screenshots_dir).glob("*.zip")):
            files[f"screenshots/{z.name}"] = z.read_bytes(); shots += 1
    manifest = {"format": FORMAT, "format_version": FORMAT_VERSION, "app_version": __version__, "schema_version": schema, "created_at": now_utc().isoformat(),
                "include_history": include_history, "tables": counts, "settings_keys": len(settings), "screenshot_archives": shots, "note": note,
                "files": {name: {"sha256": _sha(b), "bytes": len(b)} for name, b in files.items()}}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        for name, b in files.items():
            z.writestr(name, b)
    data = security.encrypt_bytes(password, buf.getvalue()) if password else buf.getvalue()
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)                                           # atomic: a crash never leaves a half-written backup
    return dest


# ------------------------------------------------------------------------ verify
def _open(src: Union[str, Path], password: Optional[str]) -> zipfile.ZipFile:
    raw = Path(src).read_bytes()
    if raw[:4] == security.MAGIC:
        if not password:
            raise PackageError("encrypted package: a password is required")
        raw = security.decrypt_bytes(password, raw)           # raises security.DecryptError on a wrong password / tampering
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise PackageError("not a WorkTracker package")
    return zipfile.ZipFile(io.BytesIO(raw))


def verify_package(src: Union[str, Path], password: Optional[str] = None, current_schema: Optional[int] = None) -> Dict[str, Any]:
    """Check structure + every checksum. Returns the manifest. Raises PackageError / VerificationError."""
    with _open(src, password) as z:
        if "manifest.json" not in z.namelist():
            raise PackageError("manifest.json missing")
        try:
            m = json.loads(z.read("manifest.json"))
        except ValueError as exc:
            raise VerificationError("manifest is not valid JSON") from exc
        if m.get("format") != FORMAT:
            raise PackageError("unknown package format")
        if int(m.get("format_version", 0)) > FORMAT_VERSION:
            raise PackageError("package was written by a newer WorkTracker (format)")
        if current_schema is not None and int(m.get("schema_version", 0)) > current_schema:
            raise PackageError("package was written by a newer WorkTracker (database schema)")
        for name, meta in m.get("files", {}).items():
            if name not in z.namelist():
                raise VerificationError(f"missing file: {name}")
            if _sha(z.read(name)) != meta["sha256"]:
                raise VerificationError(f"checksum mismatch: {name}")
        for table, n in (m.get("tables") or {}).items():                    # a dropped table file must not silently restore as "empty"
            name = f"data/{table}.jsonl"
            if name not in z.namelist():
                raise VerificationError(f"missing table: {table}")
            if sum(1 for line in z.read(name).split(b"\n") if line.strip()) != int(n):
                raise VerificationError(f"row count mismatch: {table}")
        return m


# ------------------------------------------------------------------------ restore
def _rows(z: zipfile.ZipFile, table: str) -> List[Dict[str, Any]]:
    name = f"data/{table}.jsonl"
    if name not in z.namelist():
        return []
    text = z.read(name).decode("utf-8")
    return [json.loads(line) for line in text.split("\n") if line.strip()]


def restore_package(db: Database, src: Union[str, Path], mode: str = "replace", password: Optional[str] = None, backup_dir: Optional[Union[str, Path]] = None,
                    screenshots_dir: Optional[Union[str, Path]] = None, include_settings: bool = True, conflict: str = "newer") -> RestoreReport:
    """Apply a package atomically.

    mode      replace = make the database identical to the package; merge = add/update by id.
    conflict  (merge only) newer = keep whichever row has the later ``updated_at``; package = package wins; keep = existing wins.
    """
    if mode not in ("replace", "merge") or conflict not in ("newer", "package", "keep"):
        raise ValueError("bad mode/conflict")
    manifest = verify_package(src, password, current_schema=db.version)
    rep = RestoreReport(mode=mode, manifest=manifest)
    if backup_dir and db.path != ":memory:":
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        rep.safety_backup = str(db.backup(Path(backup_dir) / f"pre-restore-{now_utc():%Y%m%d-%H%M%S-%f}.db"))
    with _open(src, password) as z:
        plan: List[Tuple[str, List[Dict[str, Any]], List[str]]] = []
        have = user_tables(db.conn)
        for t in [t for t in have if t != "audit_log" or manifest.get("include_history")]:
            rows = _rows(z, t)
            cols = columns(db.conn, t)
            if rows:
                extra = sorted({k for r in rows for k in r} - set(cols))
                if extra:
                    rep.warnings.append(f"{t}: ignored unknown columns {extra}")
            plan.append((t, rows, cols))
        settings = json.loads(z.read("settings.json")) if "settings.json" in z.namelist() else {}
        shot_files = [n for n in z.namelist() if n.startswith("screenshots/") and n.endswith(".zip")]
        conn = db.conn
        conn.commit()
        conn.execute("PRAGMA foreign_keys=OFF")                 # parents/children are inserted in dependency order; integrity is re-checked before COMMIT
        try:
            conn.execute("BEGIN IMMEDIATE")
            if mode == "replace":
                for t, _r, _c in reversed(plan):
                    conn.execute(f'DELETE FROM "{t}"')
                if include_settings:
                    conn.execute("DELETE FROM settings")
            for t, rows, cols in plan:
                st = rep.tables.setdefault(t, {"inserted": 0, "updated": 0, "skipped": 0})
                for r in rows:
                    data = {k: _unjson(v) for k, v in r.items() if k in cols}
                    if not data:
                        continue
                    names = list(data)
                    ph = ",".join("?" * len(names))
                    q = ",".join(f'"{n}"' for n in names)
                    existing = conn.execute(f'SELECT * FROM "{t}" WHERE id=?', (data["id"],)).fetchone() if ("id" in data and mode == "merge") else None
                    if existing is None:
                        conn.execute(f'INSERT OR REPLACE INTO "{t}" ({q}) VALUES ({ph})', [data[n] for n in names]); st["inserted"] += 1
                        continue
                    if conflict == "keep" or (conflict == "newer" and "updated_at" in data and str(data["updated_at"]) < str(existing["updated_at"] if "updated_at" in existing.keys() else "")):
                        st["skipped"] += 1; continue
                    sets = ",".join(f'"{n}"=?' for n in names if n != "id")
                    if sets:
                        conn.execute(f'UPDATE "{t}" SET {sets} WHERE id=?', [data[n] for n in names if n != "id"] + [data["id"]])
                    st["updated"] += 1
            if include_settings:
                for k, v in settings.items():
                    if mode == "merge" and conflict == "keep" and conn.execute("SELECT 1 FROM settings WHERE key=?", (k,)).fetchone():
                        continue
                    conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, v)); rep.settings_applied += 1
            bad = conn.execute("PRAGMA foreign_key_check").fetchall()
            if bad:
                raise RestoreError(f"package breaks referential integrity ({len(bad)} broken links, e.g. in {bad[0][0]})")
            conn.commit()
        except BaseException as exc:
            conn.rollback()
            if isinstance(exc, RestoreError):
                raise
            raise RestoreError(f"restore failed and was rolled back: {exc}") from exc
        finally:
            conn.execute("PRAGMA foreign_keys=ON")
        if screenshots_dir and shot_files:
            out = Path(screenshots_dir)
            out.mkdir(parents=True, exist_ok=True)
            for n in shot_files:
                target = out / Path(n).name
                data = z.read(n)
                if not target.exists() or target.stat().st_size != len(data):
                    target.write_bytes(data); rep.screenshots_copied += 1
    if not db.integrity_ok():
        raise RestoreError("integrity check failed after restore")
    return rep


# ------------------------------------------------------------------------ configuration only
def export_config(db: Database, dest: Union[str, Path], include_secrets: bool = False) -> Path:
    """Preferences/rules/templates/lists as one readable JSON file. Machine-specific and live-state keys are left out; secrets only on request."""
    cfg: Dict[str, Any] = {}
    for r in dump_table(db.conn, "settings"):
        k = r["key"]
        if k in VOLATILE_KEYS or (k in SECRET_KEYS and not include_secrets):
            continue
        cfg[k] = json.loads(r["value"])
    doc = {"format": CONFIG_FORMAT, "format_version": CONFIG_VERSION, "app_version": __version__, "created_at": now_utc().isoformat(), "includes_secrets": include_secrets, "settings": cfg}
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(dest)
    return dest


def _read_config(src: Union[str, Path]) -> Dict[str, Any]:
    try:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PackageError(f"cannot read configuration file: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("format") != CONFIG_FORMAT or not isinstance(doc.get("settings"), dict):
        raise PackageError("not a WorkTracker configuration file")
    if int(doc.get("format_version", 0)) > CONFIG_VERSION:
        raise PackageError("configuration was written by a newer WorkTracker")
    return doc


def diff_config(db: Database, src: Union[str, Path]) -> Dict[str, List[str]]:
    """What importing would do: keys that are new, changed, unchanged, ignored."""
    doc = _read_config(src)
    out: Dict[str, List[str]] = {"new": [], "changed": [], "same": [], "ignored": []}
    for k, v in doc["settings"].items():
        if not _KEY_RE.match(k) or k in VOLATILE_KEYS or len(json.dumps(v)) > MAX_VALUE_BYTES:
            out["ignored"].append(k); continue
        cur = db.get_setting(k, "__missing__")
        out["new" if cur == "__missing__" else ("same" if cur == v else "changed")].append(k)
    return out


def import_config(db: Database, src: Union[str, Path], mode: str = "merge") -> Dict[str, List[str]]:
    """Apply a configuration file atomically. ``merge`` sets the keys in the file; ``replace`` also removes other (non-volatile) keys."""
    if mode not in ("merge", "replace"):
        raise ValueError("bad mode")
    doc = _read_config(src)
    plan = diff_config(db, src)
    with db.transaction() as c:
        if mode == "replace":
            for r in c.execute("SELECT key FROM settings").fetchall():
                if r[0] not in VOLATILE_KEYS and r[0] not in doc["settings"] and r[0] not in SECRET_KEYS:
                    c.execute("DELETE FROM settings WHERE key=?", (r[0],))
        for k in plan["new"] + plan["changed"]:
            c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, json.dumps(doc["settings"][k], ensure_ascii=False)))
    return plan
