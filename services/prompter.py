"""The "what did you do?" nag: decides *when* to pop the work-report window over everything and what to pre-fill.

Pure logic (clock injected). The UI shows the window; this module owns the schedule, snoozing, quiet hours and the suggested
entry for the unlogged gap, plus compliance statistics for reports.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import PromptLog, Status, TimeEntry
from ..core.persian import now_utc, to_tehran


@dataclass
class PromptConfig:
    enabled: bool = True
    interval_min: int = 60
    forced: bool = False             # cannot be dismissed: you must log, or say you were away
    max_snoozes: int = 2
    snooze_min: int = 10
    quiet_start: int = 22            # Tehran hour; no prompts from here ...
    quiet_end: int = 7               # ... until here
    off_weekdays: List[int] = field(default_factory=lambda: [4])      # Friday
    only_when_engaged: bool = True   # skip the prompt if you were away the whole interval
    min_gap_min: int = 10            # do not nag for gaps shorter than this
    max_gap_hours: int = 6           # never suggest a bigger gap than this
    aligned: bool = True             # ask once per finished clock hour about the *measured, unlogged* part of it (ledger); False = classic fixed interval

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "PromptConfig":
        c = cls()
        for k, v in (d or {}).items():
            if hasattr(c, k):
                setattr(c, k, v)
        if c.interval_min < 5 or c.snooze_min < 1 or c.max_snoozes < 0:
            raise ValueError("invalid prompt settings")
        return c


class Prompter:
    KEY = "prompter_state"

    def __init__(self, db: Database, cfg: Optional[PromptConfig] = None, clock: Callable[[], dt.datetime] = now_utc) -> None:
        self.db, self.clock = db, clock
        self.cfg = cfg or PromptConfig.from_dict(db.get_setting("prompt_config", {}))
        st = db.get_setting(self.KEY, {})
        self.next_due: Optional[dt.datetime] = dt.datetime.fromisoformat(st["next_due"]) if st.get("next_due") else None
        self.snoozes: int = st.get("snoozes", 0)
        self.open_log_id: Optional[str] = st.get("open")
        self.hour_context: Optional[dt.datetime] = None        # set by the runtime when the prompt is about one specific clock hour

    def _save(self) -> None:
        self.db.set_setting(self.KEY, {"next_due": self.next_due.isoformat() if self.next_due else None, "snoozes": self.snoozes, "open": self.open_log_id})

    def save_config(self) -> None:
        self.db.set_setting("prompt_config", self.cfg.to_dict())

    # ---- schedule ------------------------------------------------------------
    def in_quiet_time(self, now: Optional[dt.datetime] = None) -> bool:
        t = to_tehran(now or self.clock())
        if t.weekday() in self.cfg.off_weekdays:
            return True
        s, e = self.cfg.quiet_start, self.cfg.quiet_end
        return (t.hour >= s or t.hour < e) if s > e else (s <= t.hour < e)

    def arm(self, now: Optional[dt.datetime] = None) -> None:
        """Schedule the next prompt ``interval_min`` from now (call on app start and after each answer)."""
        self.next_due = (now or self.clock()) + dt.timedelta(minutes=self.cfg.interval_min)
        self.snoozes = 0
        self._save()

    def due(self, engaged_recently: bool = True) -> bool:
        now = self.clock()
        if not self.cfg.enabled or self.open_log_id:
            return False
        if self.next_due is None:
            self.arm(now); return False
        if now < self.next_due:
            return False
        if self.in_quiet_time(now):
            self.next_due = now + dt.timedelta(minutes=15); self._save(); return False
        if self.cfg.only_when_engaged and not engaged_recently:
            self.next_due = now + dt.timedelta(minutes=self.cfg.interval_min); self._save(); return False
        gap = self.gap(now)
        if gap is None:                                   # everything already logged: nothing to ask
            self.next_due = now + dt.timedelta(minutes=self.cfg.interval_min); self._save(); return False
        return True

    # ---- the unlogged gap ---------------------------------------------------------
    def last_covered(self) -> Optional[dt.datetime]:
        """Latest moment already accounted for: end of any finished/running entry or the end of an answered prompt."""
        ends: List[dt.datetime] = []
        r = self.db.conn.execute("SELECT MAX(COALESCE(end_utc, start_utc)) FROM entries WHERE status IN ('done','running')").fetchone()[0]
        if r:
            ends.append(dt.datetime.fromisoformat(r))
        r = self.db.conn.execute("SELECT MAX(covers_to) FROM prompt_log WHERE action IN ('logged','away')").fetchone()[0]
        if r:
            ends.append(dt.datetime.fromisoformat(r))
        return max(ends) if ends else None

    def gap(self, now: Optional[dt.datetime] = None) -> Optional[Tuple[dt.datetime, dt.datetime]]:
        now = now or self.clock()
        floor = now - dt.timedelta(hours=self.cfg.max_gap_hours)
        start = max(self.last_covered() or floor, floor)
        if self.db.running_entries():                     # a running timer already covers "now"
            return None
        if (now - start) < dt.timedelta(minutes=self.cfg.min_gap_min):
            return None
        return start, now

    def suggestion(self, now: Optional[dt.datetime] = None) -> Dict[str, object]:
        """Pre-fill for the dialog: gap bounds, minutes, apps used in it (from activity events) and a guessed title/category."""
        now = now or self.clock()
        g = self.gap(now) or (now - dt.timedelta(minutes=self.cfg.interval_min), now)
        apps: Dict[str, int] = {}
        for r in self.db.conn.execute("SELECT app, start_utc, end_utc FROM activity_events WHERE end_utc>? AND start_utc<?", (g[0].isoformat(), g[1].isoformat())):
            a, b = max(dt.datetime.fromisoformat(r[1]), g[0]), min(dt.datetime.fromisoformat(r[2]), g[1])
            if b > a:
                apps[r[0]] = apps.get(r[0], 0) + int((b - a).total_seconds())
        top = sorted(apps.items(), key=lambda kv: -kv[1])
        from .activity import classify
        cat_map = {"development": "development", "design": "ui_ux_design", "documents": "documentation", "communication": "communication"}
        cat = cat_map.get(classify(top[0][0]), "development") if top else "development"
        return {"from": g[0], "to": g[1], "minutes": int((g[1] - g[0]).total_seconds() // 60), "apps": top[:5],
                "title_hint": (f"کار با {top[0][0].replace('.exe', '')}" if top else ""), "category": cat}

    # ---- lifecycle ---------------------------------------------------------------------
    def show(self) -> PromptLog:
        """Record that the dialog was shown."""
        now = self.clock()
        g = self.gap(now)
        log = PromptLog(shown_at=now, covers_from=g[0] if g else None, covers_to=g[1] if g else None)
        self.db.save(log)
        self.open_log_id = log.id
        self._save()
        return log

    def can_snooze(self) -> bool:
        return not self.cfg.forced and self.snoozes < self.cfg.max_snoozes

    def snooze(self) -> bool:
        if not self.can_snooze():
            return False
        self._finish("snoozed")
        self.snoozes += 1
        self.next_due = self.clock() + dt.timedelta(minutes=self.cfg.snooze_min)
        self._save()
        return True

    def answer(self, action: str, entry_id: Optional[str] = None) -> None:
        """action: logged | away | skipped. ``skipped`` is refused in forced mode."""
        if action not in ("logged", "away", "skipped"):
            raise ValueError("bad action")
        if action == "skipped" and self.cfg.forced:
            raise PermissionError("forced mode: log your work or mark yourself as away")
        self._finish(action, entry_id)
        self.arm()

    def _finish(self, action: str, entry_id: Optional[str] = None) -> None:
        if not self.open_log_id:
            return
        log = self.db.get(PromptLog, self.open_log_id)
        if log:
            log.action, log.answered_at, log.entry_id = action, self.clock(), entry_id
            self.db.save(log)
        if self.hour_context is not None and action in ("logged", "away", "skipped"):
            from .ledger import Ledger                                  # an answered hour is never asked about again
            Ledger(self.db, self.clock).mark_answered(self.hour_context, action)
            self.hour_context = None
        self.open_log_id = None

    # ---- statistics ---------------------------------------------------------------------
    def compliance(self, start: dt.datetime, end: dt.datetime) -> Dict[str, float]:
        counts = {"logged": 0, "snoozed": 0, "away": 0, "skipped": 0, "unanswered": 0}
        for r in self.db.conn.execute("SELECT action FROM prompt_log WHERE shown_at>=? AND shown_at<?", (start.isoformat(), end.isoformat())):
            counts[r[0] or "unanswered"] = counts.get(r[0] or "unanswered", 0) + 1
        total = sum(counts.values())
        return {**counts, "total": total, "rate_pct": round(100 * (counts["logged"] + counts["away"]) / total, 1) if total else 0.0}
