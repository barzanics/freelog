"""Pomodoro state machine. Wall-clock based, so it survives restarts and sleeps.

State is persisted in the settings table; ``restore`` recomputes the phase from
timestamps (no ticking thread required — the UI just calls ``tick``).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Optional

from ..core.database import Database
from ..core.persian import now_utc

WORK, SHORT, LONG, IDLE = "work", "short_break", "long_break", "idle"


@dataclass
class PomodoroConfig:
    work_min: int = 25
    short_min: int = 5
    long_min: int = 15
    cycles_before_long: int = 4
    auto_start_next: bool = False

    def __post_init__(self) -> None:
        if min(self.work_min, self.short_min, self.long_min, self.cycles_before_long) < 1:
            raise ValueError("all durations must be >= 1")


class Pomodoro:
    KEY = "pomodoro_state"

    def __init__(self, db: Database, config: Optional[PomodoroConfig] = None,
                 clock: Callable[[], dt.datetime] = now_utc) -> None:
        self.db, self.cfg, self.clock = db, config or PomodoroConfig(), clock
        self.phase = IDLE
        self.completed_work = 0          # finished work phases in the current set
        self.total_completed = 0
        self.phase_started: Optional[dt.datetime] = None
        self.paused_at: Optional[dt.datetime] = None
        self.paused_total = 0.0
        self.log: list = []              # (phase, finished_at iso)

    # ---- helpers -----------------------------------------------------
    def duration(self, phase: Optional[str] = None) -> int:
        phase = phase or self.phase
        return {WORK: self.cfg.work_min, SHORT: self.cfg.short_min, LONG: self.cfg.long_min, IDLE: 0}[phase] * 60

    @property
    def running(self) -> bool:
        return self.phase != IDLE and self.paused_at is None

    @property
    def paused(self) -> bool:
        return self.paused_at is not None

    def elapsed(self) -> float:
        if self.phase == IDLE or self.phase_started is None:
            return 0.0
        ref = self.paused_at or self.clock()
        return max(0.0, (ref - self.phase_started).total_seconds() - self.paused_total)

    def remaining(self) -> int:
        return max(0, int(round(self.duration() - self.elapsed())))

    def fill_level(self) -> float:
        """0..1 for the liquid-orb animation (1 = full / just started)."""
        d = self.duration()
        return 0.0 if d == 0 else max(0.0, min(1.0, 1 - self.elapsed() / d))

    # ---- transitions -------------------------------------------------
    def start(self) -> None:
        """Start a work phase from idle."""
        if self.phase != IDLE:
            raise RuntimeError("already running")
        self._begin(WORK)

    def _begin(self, phase: str) -> None:
        self.phase, self.phase_started, self.paused_at, self.paused_total = phase, self.clock(), None, 0.0
        self.save()

    def pause(self) -> None:
        if self.phase == IDLE or self.paused:
            raise RuntimeError("nothing to pause")
        self.paused_at = self.clock()
        self.save()

    def resume(self) -> None:
        if not self.paused:
            raise RuntimeError("not paused")
        self.paused_total += (self.clock() - self.paused_at).total_seconds()  # type: ignore[operator]
        self.paused_at = None
        self.save()

    def reset(self) -> None:
        self.phase, self.phase_started, self.paused_at, self.paused_total = IDLE, None, None, 0.0
        self.completed_work = 0
        self.save()

    def skip(self) -> str:
        """Finish the current phase early (a skipped work phase does not count)."""
        if self.phase == IDLE:
            raise RuntimeError("idle")
        return self._advance(counted=False)

    def tick(self) -> Optional[str]:
        """Advance if the phase elapsed. Returns the *new* phase name when it changed."""
        if self.phase == IDLE or self.paused or self.remaining() > 0:
            return None
        return self._advance(counted=True)

    def _advance(self, counted: bool) -> str:
        finished, now = self.phase, self.clock()
        if finished == WORK and counted:
            self.completed_work += 1
            self.total_completed += 1
            self.log.append((WORK, now.isoformat()))
        if finished == WORK:
            nxt = LONG if (self.completed_work and self.completed_work % self.cfg.cycles_before_long == 0 and counted) else SHORT
            if nxt == LONG:
                self.completed_work = 0
        else:
            nxt = WORK
        if self.cfg.auto_start_next:
            self._begin(nxt)
        else:
            self.phase, self.phase_started, self.paused_at, self.paused_total = IDLE, None, None, 0.0
            self.next_phase = nxt
            self.save()
        return nxt

    # ---- persistence --------------------------------------------------
    def state(self) -> Dict[str, object]:
        return {"phase": self.phase, "completed_work": self.completed_work, "total": self.total_completed,
                "started": self.phase_started.isoformat() if self.phase_started else None,
                "paused_at": self.paused_at.isoformat() if self.paused_at else None,
                "paused_total": self.paused_total, "cfg": asdict(self.cfg), "log": self.log[-200:]}

    def save(self) -> None:
        self.db.set_setting(self.KEY, self.state())

    def restore(self) -> bool:
        st = self.db.get_setting(self.KEY)
        if not st:
            return False
        self.cfg = PomodoroConfig(**st["cfg"])
        self.phase, self.completed_work, self.total_completed = st["phase"], st["completed_work"], st["total"]
        self.phase_started = dt.datetime.fromisoformat(st["started"]) if st["started"] else None
        self.paused_at = dt.datetime.fromisoformat(st["paused_at"]) if st["paused_at"] else None
        self.paused_total, self.log = st["paused_total"], st.get("log", [])
        return True
