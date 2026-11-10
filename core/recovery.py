"""Corrupted-database recovery: fall back to the newest healthy backup."""
from __future__ import annotations

import logging
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, Union

log = logging.getLogger("worktracker.recovery")


def is_healthy(path: Union[str, Path]) -> bool:
    try:
        c = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        try:
            return c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            c.close()
    except sqlite3.DatabaseError:
        return False


def recover(db_path: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
    """If ``db_path`` is corrupt, keep it as ``*.corrupt`` and restore the newest healthy backup. Returns the backup used."""
    db_path = Path(db_path)
    if not db_path.exists() or is_healthy(db_path):
        return None
    for b in sorted(Path(backup_dir).glob("worktracker-*.db"), reverse=True):
        if is_healthy(b):
            shutil.move(str(db_path), str(db_path.with_suffix(".corrupt")))
            for ext in ("-wal", "-shm"):
                Path(str(db_path) + ext).unlink(missing_ok=True)
            shutil.copy2(b, db_path)
            log.warning("restored %s from %s", db_path, b)
            return b
    raise RuntimeError("database is corrupt and no healthy backup exists")
