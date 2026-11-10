"""Hourly screenshots, stored small: downscaled JPEG, appended to one ZIP per day, indexed in the database.

Privacy first: off by default, local only, never uploaded, blocked-app list, pause switch, retention (days) and a hard size cap.
The pixel grabbing is injected (``grab`` returns ``(jpeg_bytes, width, height)``) so this module has no Qt dependency and is unit-tested.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import logging
import zipfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from ..core.database import Database
from ..core.models import Screenshot
from ..core.persian import now_utc, to_tehran

log = logging.getLogger("worktracker.shots")
Grab = Callable[[], Optional[Tuple[bytes, int, int]]]
DEFAULT_BLOCKED = ("keepass", "bitwarden", "1password", "lastpass", "password", "بانک", "bank", "پرداخت", "payment", "incognito", "private browsing")


def should_capture(now: dt.datetime, last_at: Optional[dt.datetime], interval_min: int, engaged: bool, require_engaged: bool = True) -> bool:
    """Pure schedule rule: one shot per interval; with ``require_engaged`` nothing is captured while the user is away."""
    if interval_min < 1:
        raise ValueError("interval must be >= 1 minute")
    if require_engaged and not engaged:
        return False
    return last_at is None or now - last_at >= dt.timedelta(minutes=interval_min)


class ScreenshotStore:
    def __init__(self, db: Database, folder: Union[str, Path], grab: Grab, clock: Callable[[], dt.datetime] = now_utc) -> None:
        self.db, self.folder, self.grab, self.clock = db, Path(folder), grab, clock

    # ---- settings -----------------------------------------------------
    @property
    def blocked(self) -> List[str]:
        return [b.lower() for b in self.db.get_setting("shots_blocked", list(DEFAULT_BLOCKED))]

    @property
    def paused(self) -> bool:
        return bool(self.db.get_setting("shots_paused", False))

    def is_blocked(self, app: str, title: str) -> bool:
        text = f"{app} {title}".lower()
        return any(b and b in text for b in self.blocked)

    # ---- capture -------------------------------------------------------
    def last(self) -> Optional[Screenshot]:
        r = self.db.conn.execute("SELECT * FROM screenshots ORDER BY at DESC LIMIT 1").fetchone()
        return Screenshot.from_row(r) if r else None

    def capture(self, app: str = "", title: str = "", force: bool = False) -> Optional[Screenshot]:
        """Take, compress and store one screenshot. Returns None when paused/blocked/duplicate/unavailable (see ``capture_result`` for why)."""
        return self.capture_result(app, title, force)[0]

    def capture_result(self, app: str = "", title: str = "", force: bool = False) -> "tuple[Optional[Screenshot], str]":
        """Like ``capture`` but also says why nothing was stored: ``ok`` / ``paused`` / ``blocked`` / ``no_screen`` / ``duplicate`` / ``error``."""
        if self.paused and not force:
            return None, "paused"
        if self.is_blocked(app, title):
            log.info("screenshot skipped: blocked window")
            return None, "blocked"
        try:
            got = self.grab()
        except Exception:  # noqa: BLE001 - a broken grabber must not crash the caller
            log.exception("grab failed")
            return None, "error"
        if not got:
            return None, "no_screen"
        data, w, h = got
        sig = hashlib.blake2b(data, digest_size=8).hexdigest()
        prev = self.last()
        if prev is not None and prev.sig == sig and not force:
            return None, "duplicate"                       # screen unchanged since last shot: store nothing
        now = self.clock()
        local = to_tehran(now)
        self.folder.mkdir(parents=True, exist_ok=True)
        zpath = self.folder / f"{local:%Y-%m-%d}.zip"
        member = f"{local:%H%M%S}.jpg"
        with zipfile.ZipFile(zpath, "a", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            if member in z.namelist():                     # two shots in one second: keep both
                member = f"{local:%H%M%S}_{sig[:4]}.jpg"
            z.writestr(member, data)
        shot = Screenshot(at=now, path=zpath.name, member=member, app=app[:100], title=title[:200], bytes=len(data), width=w, height=h, sig=sig)
        self.db.save(shot)
        return shot, "ok"

    # ---- read ------------------------------------------------------------
    def read(self, shot: Screenshot) -> bytes:
        with zipfile.ZipFile(self.folder / shot.path) as z:
            return z.read(shot.member)

    def for_day(self, day: dt.date) -> List[Screenshot]:
        from ..core.persian import TEHRAN
        lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN)
        rows = self.db.conn.execute("SELECT * FROM screenshots WHERE at>=? AND at<? ORDER BY at",
                                    (lo.isoformat(), (lo + dt.timedelta(days=1)).isoformat())).fetchall()
        return [Screenshot.from_row(r) for r in rows]

    def near(self, moment: dt.datetime, within_min: int = 40) -> Optional[Screenshot]:
        """Closest screenshot to ``moment`` (used to attach a picture to a work-report prompt)."""
        rows = self.db.conn.execute("SELECT * FROM screenshots WHERE at>=? AND at<=?",
                                    ((moment - dt.timedelta(minutes=within_min)).isoformat(), (moment + dt.timedelta(minutes=within_min)).isoformat())).fetchall()
        shots = [Screenshot.from_row(r) for r in rows]
        return min(shots, key=lambda s: abs((s.at - moment).total_seconds())) if shots else None

    # ---- maintenance -------------------------------------------------------
    def total_bytes(self) -> int:
        return sum(p.stat().st_size for p in self.folder.glob("*.zip")) if self.folder.exists() else 0

    def delete(self, shot_id: str) -> bool:
        """Remove one picture (rewrites that day's zip without it)."""
        r = self.db.conn.execute("SELECT * FROM screenshots WHERE id=?", (shot_id,)).fetchone()
        if r is None:
            return False
        shot = Screenshot.from_row(r)
        zpath = self.folder / shot.path
        if zpath.exists():
            tmp = zpath.with_suffix(".tmp")
            with zipfile.ZipFile(zpath) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
                for item in zin.infolist():
                    if item.filename != shot.member:
                        zout.writestr(item, zin.read(item.filename))
            tmp.replace(zpath)
        self.db.delete(Screenshot, shot_id)
        return True

    def cleanup(self, keep_days: int = 30, max_total_mb: int = 500) -> int:
        """Delete whole daily zips older than ``keep_days``, then oldest zips until under the size cap. Returns zips removed."""
        removed = 0
        cutoff = to_tehran(self.clock()).date() - dt.timedelta(days=keep_days)
        zips = sorted(self.folder.glob("*.zip")) if self.folder.exists() else []
        for z in list(zips):
            try:
                day = dt.date.fromisoformat(z.stem)
            except ValueError:
                continue
            if day < cutoff:
                self._drop_zip(z); zips.remove(z); removed += 1
        while zips and self.total_bytes() > max_total_mb * 1024 * 1024:
            self._drop_zip(zips.pop(0)); removed += 1
        return removed

    def _drop_zip(self, z: Path) -> None:
        with self.db.transaction() as c:
            c.execute("DELETE FROM screenshots WHERE path=?", (z.name,))
        z.unlink(missing_ok=True)

    def export_day_zip(self, day: dt.date, dest: Union[str, Path]) -> Path:
        """Copy one day's archive (already a zip) to ``dest`` for sharing/backup."""
        src = self.folder / f"{day:%Y-%m-%d}.zip"
        if not src.exists():
            raise FileNotFoundError(src)
        Path(dest).write_bytes(src.read_bytes())
        return Path(dest)
