"""Housekeeping: compress old audit snapshots (gzip+base64) to keep the database small."""
from __future__ import annotations

import base64
import datetime as dt
import gzip

from ..core.database import Database
from ..core.persian import now_utc

PREFIX = "gz:"


def pack(text: str) -> str:
    return PREFIX + base64.b64encode(gzip.compress(text.encode("utf-8"), 9)).decode("ascii")


def unpack(text: str) -> str:
    return gzip.decompress(base64.b64decode(text[len(PREFIX):])).decode("utf-8") if text.startswith(PREFIX) else text


def compress_old_audit(db: Database, older_than_days: int = 90) -> int:
    """Compress audit ``detail`` older than N days; returns rows changed (idempotent)."""
    cutoff = (now_utc() - dt.timedelta(days=older_than_days)).isoformat()
    n = 0
    with db.transaction() as c:
        for rid, detail in c.execute("SELECT id, detail FROM audit_log WHERE at<? AND detail!='' AND detail NOT LIKE 'gz:%'", (cutoff,)).fetchall():
            c.execute("UPDATE audit_log SET detail=? WHERE id=?", (pack(detail), rid))
            n += 1
    return n


def vacuum(db: Database) -> None:
    db.conn.commit()
    db.conn.execute("VACUUM")
