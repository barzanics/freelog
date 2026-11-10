"""Auto-detect that you are *really working* and record the time for you.

Feed it one sample every few seconds (foreground app/title + OS idle seconds). It decides between WORK, NEUTRAL and AWAY, and
keeps an automatic time entry (source="auto") running while you work: it starts once you have worked for ``start_after`` seconds
(back-dated to the real start), and stops after ``stop_after`` seconds of being away/non-work, trimming that tail.
A manual timer always wins: while one is running, auto-tracking only observes.
"""
from __future__ import annotations

import datetime as dt
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Set

from ..core.database import Database
from ..core.models import HourLog, Status, TimeEntry
from ..core.persian import to_fa_digits, to_tehran, now_utc
from .activity import classify
from .engagement import EngagementConfig, EngagementModel

log = logging.getLogger("worktracker.auto")
WORK, NEUTRAL, AWAY = "work", "neutral", "away"
DEFAULT_WORK = {"development", "design", "documents", "communication", "email"}
NEUTRAL_CATS = {"browsing", "other"}


@dataclass
class AutoConfig:
    enabled: bool = True
    work_categories: Set[str] = field(default_factory=lambda: set(DEFAULT_WORK))
    extra_work_apps: Set[str] = field(default_factory=set)       # app names you always count as work (lower-case substrings)
    idle_limit: int = 120            # seconds without input => away
    start_after: int = 180           # continuous work before an entry is created
    stop_after: int = 300            # away/non-work before it is closed
    neutral_grace: int = 150         # browsing/other tolerated inside a work stretch
    min_session: int = 120           # shorter automatic sessions are discarded

    def to_dict(self) -> dict:
        return {**self.__dict__, "work_categories": sorted(self.work_categories), "extra_work_apps": sorted(self.extra_work_apps)}

    @classmethod
    def from_dict(cls, d: dict) -> "AutoConfig":
        c = cls()
        for k, v in (d or {}).items():
            if k in ("work_categories", "extra_work_apps"):
                setattr(c, k, set(v))
            elif hasattr(c, k):
                setattr(c, k, v)
        return c


def judge(cfg: AutoConfig, app: str, title: str, idle_sec: int) -> str:
    """WORK / NEUTRAL / AWAY for one sample."""
    if idle_sec >= cfg.idle_limit:
        return AWAY
    if any(a in app.lower() for a in cfg.extra_work_apps if a):
        return WORK
    cat = classify(app, title)
    if cat in cfg.work_categories:
        return WORK
    if cat in NEUTRAL_CATS:
        return NEUTRAL
    return AWAY                       # entertainment etc.


def hour_summary(apps: Dict[str, int]) -> str:
    top = sorted(apps.items(), key=lambda kv: -kv[1])[:3]
    return to_fa_digits("، ".join(f"{a} ({max(1, s // 60)} دقیقه)" for a, s in top if s >= 30)) or "فعالیتی ثبت نشد"


class AutoTracker:
    def __init__(self, db: Database, cfg: Optional[AutoConfig] = None, clock: Callable[[], dt.datetime] = now_utc) -> None:
        self.db, self.cfg, self.clock = db, cfg or AutoConfig(), clock
        self.active_id: Optional[str] = None
        self._cand_start: Optional[dt.datetime] = None      # start of a possible work stretch
        self._cand_work = 0.0
        self._last_work: Optional[dt.datetime] = None
        self._away_since: Optional[dt.datetime] = None
        self._neutral_since: Optional[dt.datetime] = None
        self._last_t: Optional[dt.datetime] = None
        self._apps: Counter = Counter()
        self._titles: Counter = Counter()
        self._cats: Counter = Counter()
        self._hour: Optional[dt.datetime] = None
        self._hour_apps: Counter = Counter()
        self._hour_engaged = 0
        self._hour_idle = 0
        self.model = EngagementModel()
        self.last_reason = ""
        self.write_hour_numbers = True

    # ------------------------------------------------------------------
    def manual_running(self) -> bool:
        return any(e.source != "auto" for e in self.db.running_entries())

    def sample(self, app: str, title: str, idle_sec: int, now: Optional[dt.datetime] = None, screen_delta: Optional[float] = None) -> Optional[str]:
        """Process one observation. Returns "started" / "stopped" / "discarded" when something changed, else None.

        ``screen_delta`` (0..1, optional) is how much the screen changed since the last sample; with it the engagement model can spot a frozen screen
        and count a video call / long read as work."""
        now = now or self.clock()
        dt_s = min(60.0, (now - self._last_t).total_seconds()) if self._last_t else 0.0
        self._last_t = now
        state = judge(self.cfg, app, title, idle_sec)
        state, self.last_reason = self.model.refine(state, idle_sec, screen_delta, classify(app, title), now, self.cfg.idle_limit)
        self.last_state = state
        self._hour_tick(now, app, state, dt_s)
        if not self.cfg.enabled:
            return None
        if self.manual_running():
            self._reset_candidate()
            return None
        if self.active_id is not None:
            return self._active(state, app, title, now, dt_s)
        return self._candidate(state, app, title, now, dt_s)

    # ---- before an entry exists ------------------------------------------
    def _candidate(self, state: str, app: str, title: str, now: dt.datetime, dt_s: float) -> Optional[str]:
        if state == AWAY:
            self._reset_candidate(); return None
        if state == NEUTRAL:
            self._neutral_since = self._neutral_since or now
            if (now - self._neutral_since).total_seconds() > self.cfg.neutral_grace:
                self._reset_candidate()
            return None
        self._neutral_since = None
        if self._cand_start is None:
            self._cand_start = now - dt.timedelta(seconds=dt_s)
        self._cand_work += dt_s
        self._note(app, title, dt_s)
        self._last_work = now
        if (now - self._cand_start).total_seconds() >= self.cfg.start_after and self._cand_work >= 0.6 * self.cfg.start_after:
            return self._start(self._cand_start)
        return None

    def _start(self, start: dt.datetime) -> str:
        e = TimeEntry(title=self._guess_title(), start_utc=start, status=Status.RUNNING, category=self._dominant_cat(), source="auto",
                      extra={"auto": True}, tags=["خودکار"])
        self.db.save(e)
        self.active_id = e.id
        self._away_since = None
        return "started"

    # ---- while an entry runs ------------------------------------------------
    def _active(self, state: str, app: str, title: str, now: dt.datetime, dt_s: float) -> Optional[str]:
        if state == WORK:
            self._last_work, self._away_since, self._neutral_since = now, None, None
            self._note(app, title, dt_s)
            return None
        if state == NEUTRAL and self._last_work and (now - self._last_work).total_seconds() <= self.cfg.neutral_grace:
            return None
        self._away_since = self._away_since or now
        if (now - self._away_since).total_seconds() >= self.cfg.stop_after:
            return self.finish()
        return None

    def finish(self) -> Optional[str]:
        """Close the automatic entry now (trimmed to the last moment of real work)."""
        if self.active_id is None:
            return None
        e = self.db.get(TimeEntry, self.active_id)
        end = self._last_work or self._last_t or self.clock()
        result = "stopped"
        if e is None or e.status != Status.RUNNING:
            result = None
        else:
            secs = int((end - e.start_utc).total_seconds())
            if secs < self.cfg.min_session:
                self.db.delete(TimeEntry, e.id); result = "discarded"
            else:
                e.title, e.category = self._guess_title(), self._dominant_cat()
                e.end_utc, e.duration_sec, e.status, e.completed_at = end, secs, Status.DONE, end
                e.extra = {**e.extra, "apps": dict(self._apps.most_common(6))}
                self.db.save(e)
        self.active_id = None
        self._reset_candidate()
        return result

    # ---- helpers ---------------------------------------------------------------
    def _reset_candidate(self) -> None:
        self._cand_start, self._cand_work, self._neutral_since = None, 0.0, None
        if self.active_id is None:
            self._apps.clear(); self._titles.clear(); self._cats.clear(); self._last_work = None

    def _note(self, app: str, title: str, secs: float) -> None:
        self._apps[app] += secs
        if title:
            self._titles[title[:80]] += secs
        self._cats[classify(app, title)] += secs

    def _dominant_cat(self) -> str:
        return {"development": "development", "design": "ui_ux_design", "documents": "documentation", "communication": "communication"}.get(
            self._cats.most_common(1)[0][0], "development") if self._cats else "general"

    def _guess_title(self) -> str:
        if not self._apps:
            return "کار خودکار"
        app = self._apps.most_common(1)[0][0].replace(".exe", "")
        t = self._titles.most_common(1)[0][0] if self._titles else ""
        return f"{t} — {app}" if t else f"کار با {app}"

    # ---- hourly log -----------------------------------------------------------------
    def _hour_tick(self, now: dt.datetime, app: str, state: str, dt_s: float) -> None:
        h = to_tehran(now).replace(minute=0, second=0, microsecond=0)
        if self._hour is not None and h != self._hour:
            self.flush_hour()
        self._hour = h
        if state == AWAY:
            self._hour_idle += int(dt_s)
        else:
            self._hour_engaged += int(dt_s)
            self._hour_apps[app] += int(dt_s)

    def flush_hour(self) -> Optional[HourLog]:
        """Persist the finished hour (apps, engaged/idle seconds, a one-line summary). Idempotent per hour."""
        if self._hour is None or (not self._hour_engaged and not self._hour_idle):
            return None
        row = self.db.conn.execute("SELECT * FROM hour_log WHERE hour_start=?", (self._hour.astimezone(dt.timezone.utc).isoformat(),)).fetchone()
        hl = HourLog.from_row(row) if row else HourLog(hour_start=self._hour)
        if self.write_hour_numbers:                                   # the hourly ledger owns these numbers when it is running
            for a, s in self._hour_apps.items():
                hl.apps[a] = hl.apps.get(a, 0) + s
            hl.engaged_sec += self._hour_engaged
            hl.idle_sec += self._hour_idle
        hl.summary = hour_summary(hl.apps)
        if self.active_id and self.active_id not in hl.entry_ids:
            hl.entry_ids.append(self.active_id)
        self.db.save(hl)
        self._hour_apps.clear(); self._hour_engaged = self._hour_idle = 0
        return hl
