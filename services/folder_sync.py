"""Account-free sync through a shared folder (Dropbox/OneDrive/iCloud/Syncthing).

Each device writes ``worktracker-<device>.json``; merge is last-writer-wins per object by ``updated_at``.
Deletions are not propagated (documented limitation). Unreadable peer files are reported in ``conflicts``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union

from ..core.database import Database
from ..core.models import Client, Project, TimeEntry
from ..core.persian import now_utc
from . import exporter

SYNC_TYPES = (("clients", Client), ("projects", Project), ("entries", TimeEntry))


@dataclass
class SyncReport:
    pulled: int = 0
    kept_local: int = 0
    conflicts: List[str] = field(default_factory=list)


def push(db: Database, folder: Union[str, Path], device: str) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f".{device}.tmp"
    exporter.export_json(db, tmp)
    final = folder / f"worktracker-{device}.json"
    tmp.replace(final)       # atomic on the same volume: peers never see half-written files
    return final


def pull(db: Database, folder: Union[str, Path], device: str) -> SyncReport:
    rep = SyncReport()
    with db.transaction():
        for f in sorted(Path(folder).glob("worktracker-*.json")):
            if f.name == f"worktracker-{device}.json":
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                rep.conflicts.append(f"unreadable: {f.name}")
                continue
            for key, cls in SYNC_TYPES:
                for row in data.get(key, []):
                    remote = cls.from_row(row)
                    local = db.get(cls, remote.id)
                    r_t = getattr(remote, "updated_at", getattr(remote, "created_at", now_utc()))
                    if local is None or r_t > getattr(local, "updated_at", getattr(local, "created_at", r_t)):
                        db.save(remote, touch=False)
                        rep.pulled += 1
                    else:
                        rep.kept_local += 1
    return rep


def sync(db: Database, folder: Union[str, Path], device: str) -> SyncReport:
    """Pull then push, so the file we publish includes merged data."""
    rep = pull(db, folder, device)
    push(db, folder, device)
    return rep
