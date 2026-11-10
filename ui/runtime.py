"""The always-on brain: samples the active window, auto-tracks work, nags for the work report, takes hourly screenshots, fires task reminders and rotates tips.

All decisions live in tested services (autotrack, prompter, screenshots, task_reminders, tips); this class only owns the timers and shows the results.
Every tick is wrapped so a failure in one feature can never freeze the UI or stop the others.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Callable, Optional, Tuple

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ..core.persian import now_utc, to_tehran
from ..services import routines as routines_svc, task_reminders
from ..services.activity import foreground_window
from ..services.activity import classify
from ..services.autotrack import AutoConfig, AutoTracker
from ..services.engagement import AWAY, EngagementModel, WORK
from ..services.ledger import ACTIVE, IDLE, PASSIVE, Ledger, hour_floor
from ..services.idle import system_idle_seconds
from ..services.pomodoro import PomodoroConfig
from ..services.prompter import PromptConfig, Prompter
from ..services.screenshots import ScreenshotStore, should_capture
from .strings import S

log = logging.getLogger("worktracker.runtime")
ENGAGED_IDLE_SEC = 120


def _safe(fn: Callable[[], None]) -> Callable[[], None]:
    def run() -> None:
        try:
            fn()
        except Exception:  # noqa: BLE001 - one failing feature must never take the app down
            log.exception("runtime tick failed: %s", getattr(fn, "__name__", fn))
    return run


class Runtime:
    def __init__(self, win) -> None:
        self.win, self.db = win, win.db
        self.auto = AutoTracker(self.db, AutoConfig.from_dict(self.db.get_setting("auto_config", {})))
        self.prompter = Prompter(self.db, self._prompt_cfg())
        self.shots = ScreenshotStore(self.db, win.data_dir / "screenshots", self._grab)
        self.ledger = Ledger(self.db)
        self.engage = EngagementModel()
        self.auto.write_hour_numbers = False                      # the ledger owns the per-hour numbers
        self._sig, self._sig_t, self.screen_delta = None, None, None
        self.last_engaged = now_utc()
        self.last_win: Tuple[str, str] = ("", "")
        self._busy = False
        self._last_tip_hour: Optional[int] = None
        self._last_day: Optional[dt.date] = None
        self.timers = {}
        for name, ms, fn in (("sample", 5000, self._sample), ("prompt", 30000, self._prompt_tick), ("shot", 60000, self._shot_tick),
                             ("remind", 30000, self._remind_tick), ("routine", 30000, self._routine_tick), ("hour", 60000, self._hour_tick)):
            t = QTimer(win); t.setInterval(ms); t.timeout.connect(_safe(fn)); self.timers[name] = t
        self.reload()

    # ---- configuration ------------------------------------------------------------
    def _prompt_cfg(self) -> PromptConfig:
        try:
            return PromptConfig.from_dict(self.db.get_setting("prompt_config", {}))
        except ValueError:
            return PromptConfig()

    def reset_state(self) -> None:
        """After a restore the in-memory schedulers must forget their old state and read the restored one."""
        self.auto = AutoTracker(self.db, AutoConfig.from_dict(self.db.get_setting("auto_config", {})))
        self.prompter = Prompter(self.db, self._prompt_cfg())
        self.reload()

    def reload(self) -> None:
        """Re-read every setting that affects background behaviour (called after any setting changes)."""
        db, win = self.db, self.win
        self.auto.cfg = AutoConfig.from_dict(db.get_setting("auto_config", {}))
        self.prompter.cfg = self._prompt_cfg()
        ts = win.tracker.settings
        ts.round_to_min = int(db.get_setting("round", 0)); ts.min_duration_sec = int(db.get_setting("tracker_min_sec", 60)); ts.idle_threshold_sec = int(db.get_setting("tracker_idle_sec", 300))
        if not win.pomo.running and not win.pomo.paused:
            try:
                win.pomo.cfg = PomodoroConfig(work_min=int(db.get_setting("pomo_work", 25)), short_min=int(db.get_setting("pomo_short", 5)), long_min=int(db.get_setting("pomo_long", 15)),
                                              cycles_before_long=int(db.get_setting("pomo_cycles", 4)), auto_start_next=bool(db.get_setting("pomo_auto", False)))
            except ValueError:
                pass
        fx = win.theme.fx
        if fx is not None:
            fx.lite = bool(db.get_setting("lite", False))
            if fx.layer is not None:
                fx.layer.enabled = bool(db.get_setting("fx_enabled", True)) and not fx.lite
            if fx.sound is not None:
                fx.sound.enabled = bool(db.get_setting("sound_enabled", True)); fx.sound.volume = max(0.0, min(1.0, int(db.get_setting("sound_volume", 55)) / 100))
        self.shots.folder = win.data_dir / "screenshots"

    def start(self) -> None:
        for t in self.timers.values():
            t.start()
        self.prompter.arm() if self.prompter.next_due is None else None
        QTimer.singleShot(4000, _safe(self._startup_shot))                    # the very first picture is taken right after launch
        QTimer.singleShot(25000, _safe(self.auto_backup))

    def stop(self) -> None:
        for t in self.timers.values():
            t.stop()
        try:
            self.ledger.flush(); self.auto.finish(); self.auto.flush_hour()
        except Exception:  # noqa: BLE001
            log.exception("shutdown flush failed")

    # ---- the sampler ---------------------------------------------------------------------
    def _update_screen_delta(self, now: dt.datetime) -> None:
        """Every 30 s compare a tiny screen thumbnail with the previous one (cheap); the result feeds the engagement model."""
        if self._sig_t is not None and (now - self._sig_t).total_seconds() < 30:
            return
        from .capture import grab_signature, signature_delta
        sig = grab_signature()
        self.screen_delta = signature_delta(self._sig, sig) if sig else None
        self._sig, self._sig_t = sig, now

    def _sample(self) -> None:
        now = now_utc()
        idle = system_idle_seconds()
        w = foreground_window() or ("", "")
        self.last_win = w
        if idle < ENGAGED_IDLE_SEC:
            self.last_engaged = now
        self._update_screen_delta(now)
        base = WORK if idle < ENGAGED_IDLE_SEC else AWAY
        st, reason = self.engage.refine(base, idle, self.screen_delta, classify(w[0], w[1]), now, ENGAGED_IDLE_SEC)
        state = PASSIVE if reason == "passive" else (ACTIVE if st == WORK else IDLE)
        self.ledger.sample(state, w[0], now)                        # exact per-hour accounting (active / passive / idle, per app)
        self.state, self.state_reason = state, reason
        t = self.timers["sample"]
        want = 5000 if state != IDLE else 15000                     # sample slowly while you are away: lighter on the CPU
        if t.interval() != want:
            t.setInterval(want)
        if self.db.get_setting("activity_capture", False):
            self.win.act.sample()
        if w[0] or idle:
            ev = self.auto.sample(w[0], w[1], idle, screen_delta=self.screen_delta)
            if ev == "started":
                self.win.toast(S["auto_started"]); self.win.refresh_all()
            elif ev == "stopped":
                self.win.toast(S["auto_stopped"]); self.win.refresh_all()
        self._flush_n = getattr(self, "_flush_n", 0) + 1
        if self._flush_n % 12 == 0:                                 # about once a minute
            self.ledger.flush()

    state, state_reason = IDLE, "idle"

    def engaged_within(self, minutes: float) -> bool:
        return (now_utc() - self.last_engaged) < dt.timedelta(minutes=minutes)

    # ---- the work-report nag --------------------------------------------------------------
    def _prompt_tick(self) -> None:
        if self._busy:
            return
        pr, cfg = self.prompter, self.prompter.cfg
        if cfg.aligned:                                             # once per finished hour, about the measured and still unlogged part of it
            if not cfg.enabled or pr.open_log_id or pr.in_quiet_time():
                return
            if pr.next_due and now_utc() < pr.next_due and pr.snoozes:   # snoozed
                return
            pend = self.ledger.pending(min_unlogged_sec=max(60, cfg.min_gap_min * 60), lookback_hours=max(2, min(12, cfg.max_gap_hours * 2)))
            if pend:
                self.show_prompt(hour=pend[0]["hour_start"])
            return
        if pr.due(self.engaged_within(max(5, cfg.interval_min))):
            self.show_prompt()

    def show_prompt(self, force: bool = False, hour: Optional[dt.datetime] = None) -> None:
        if self._busy or (self.prompter.open_log_id and not force and hour is None):
            return
        self._busy = True
        try:
            from .dialogs import WorkReportDialog
            self.ledger.flush()
            if hour is None and force:
                hour = hour_floor(now_utc()) - dt.timedelta(hours=1)
            sug, ctx = None, None
            if hour is not None:
                rep = self.ledger.hour(hour)
                if rep["unlogged_sec"] >= 60 or not force:
                    sug, ctx = self.ledger.suggest(rep), hour
            if sug is None:
                sug = self.prompter.suggestion()
            data = None
            shot = self.shots.near(sug["to"])
            if shot is not None:
                try:
                    data = self.shots.read(shot)
                except (OSError, KeyError):
                    data = None
            if self.prompter.open_log_id:
                self.prompter.open_log_id = None
            self.prompter.hour_context = ctx
            self.prompter.show()
            dlg = WorkReportDialog(self.win, self.prompter, sug, data)
            QApplication.alert(self.win, 0)
            dlg.show(); dlg.raise_(); dlg.activateWindow()
            dlg.exec_()
            self.win.refresh_all()
        finally:
            self._busy = False

    # ---- screenshots -----------------------------------------------------------------------
    def _grab(self):
        from .capture import grab_jpeg
        return grab_jpeg(int(self.db.get_setting("shots_width", 1280)), int(self.db.get_setting("shots_quality", 45)), bool(self.db.get_setting("shots_gray", False)))

    def _shot_tick(self) -> None:
        if not self.db.get_setting("shots_enabled", False):
            return
        last = self.shots.last()
        if should_capture(now_utc(), last.at if last else None, int(self.db.get_setting("shots_interval", 60)), self.engaged_within(2), bool(self.db.get_setting("shots_require_engaged", True))):
            self.capture_now(force=False)

    def _startup_shot(self) -> None:
        if not self.db.get_setting("shots_enabled", False):
            return
        last = self.shots.last()
        if last is None or (now_utc() - last.at) > dt.timedelta(minutes=2):
            shot, why = self.shots.capture_result(self.last_win[0], self.last_win[1], force=False)
            self.last_capture_reason = why
            log.info("startup screenshot: %s", why)

    last_capture_reason = "ok"

    def capture_now(self, force: bool = True):
        s, why = self.shots.capture_result(self.last_win[0], self.last_win[1], force=force)
        self.last_capture_reason = why
        if s is not None and self.win.theme.fx is not None:
            self.win.theme.fx.play("pop", 0.5)
        return s

    def auto_backup(self) -> Optional[str]:
        """One plain SQLite copy per day into backups/ (the newest N are kept). Returns the file name when one was made."""
        db = self.db
        if not db.get_setting("auto_backup", True):
            return None
        last = db.get_setting("last_backup_at")
        if last and (now_utc() - dt.datetime.fromisoformat(last)) < dt.timedelta(hours=20):
            return None
        out = db.rotate_backups(self.win.data_dir / "backups", keep=max(1, int(db.get_setting("backups_keep", 14))))
        db.set_setting("last_backup_at", now_utc().isoformat())
        return out.name

    # ---- reminders, tips, daily chores --------------------------------------------------------
    def _remind_tick(self) -> None:
        due = task_reminders.due(self.db)
        for e, off in due:
            self.win.toast(f"⏰ {e.title}" + ("" if off == 0 else f"  ({off} {S['min']})"))
            if self.win.theme.fx is not None:
                self.win.theme.fx.play("warn")
        if due:
            task_reminders.mark_fired(self.db, due)

    def _routine_tick(self) -> None:
        """Scheduled check boxes that came due and are not ticked yet: toast + sound once (and again every ``repeat_min`` if the routine asks)."""
        due = routines_svc.due_notifications(self.db)
        for it in due:
            self.win.toast(f"✅ {S['rt_notify_msg']}: {it['routine']['title']}")
            if self.win.theme.fx is not None:
                self.win.theme.fx.play("warn")
        if due:
            routines_svc.mark_notified(self.db, due)
            if self.win.current_key() == "routines":
                self.win.refresh_visible()

    def _hour_tick(self) -> None:
        now = to_tehran(now_utc())
        if self._last_tip_hour != now.hour:
            first = self._last_tip_hour is None
            self._last_tip_hour = now.hour
            from .pages_ops import refresh_tip
            refresh_tip(self.win)
            if not first and self.db.get_setting("tips_enabled", True) and self.db.get_setting("tips_toast", True):
                self.win.toast("💡 " + self.win.tip_text.text()[:120])
        if self._last_day != now.date():
            self._last_day = now.date()
            self.shots.cleanup(int(self.db.get_setting("shots_keep_days", 30)), int(self.db.get_setting("shots_max_mb", 500)))
            self.auto_backup()
            if self.db.get_setting("auto_report", False):
                self._auto_report(now.date() - dt.timedelta(days=1))

    def _auto_report(self, day: dt.date) -> None:
        from ..services import report_builder as rb
        f = self.win.data_dir / "reports" / f"daily-{day}.html"
        if f.exists():
            return
        f.parent.mkdir(parents=True, exist_ok=True)
        rb.save(rb.build(self.db, rb.ReportSpec.preset("daily", day)), f, "html")
