"""The application window (v6.1): icon sidebar that collapses on small windows, header with the tip-of-the-hour and live timer, liquid effects layer,
19 pages, and the always-on runtime. It reuses the helper methods of the older ``MainWindow`` but builds its own shell.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QShortcut, QStackedWidget, QVBoxLayout, QWidget)

from ..core.database import Database
from ..core.persian import date_to_jalali, now_utc, to_fa_digits, to_tehran
from ..services.activity import ActivityRecorder
from ..services.billing import Billing
from ..services.idle import system_idle_seconds
from ..services.pomodoro import Pomodoro
from ..services.projects import ProjectService
from ..services.tracker import Tracker, TrackerSettings
from ..services.undo import UndoManager
from . import icons
from . import pages_new as pn
from . import pages_ops as po
from . import pm_pages as pm
from . import dashboard as dash
from . import routines_ui as ru
from . import lists_ui as lu
from . import pages_extra as px
from .dialogs import PopDialog, Scrim, TaskDialog
from .floating import FloatingBubble
from .glass import GlassButton, GlassCard, LiquidBackground, Theme, Toast, qcolor
from .liquid.fx import FX, DripLayer, SoundPlayer
from .main_window import CommandPalette, MainWindow, Notifier
from .qss import build_qss
from .runtime import Runtime
from .strings import S, set_language

log = logging.getLogger("worktracker.app")

# (page key, icon). The order is also the order pages are built and stacked.
NAV = (("dashboard", "dashboard"), ("today", "today"), ("tasks", "tasks"), ("lists", "check"), ("board", "board"), ("calendar", "calendar"), ("planner", "planner"), ("matrix", "matrix"),
       ("projects", "projects"), ("pm", "pm"), ("habits", "habits"), ("routines", "bell"), ("goals", "goals"), ("team", "team"), ("billing", "billing"), ("reports", "reports"),
       ("analytics", "analytics"), ("screenshots", "screenshots"), ("entries", "list"), ("tools", "tools"), ("settings", "settings"))
PAGE_KEYS = tuple(k for k, _ in NAV)
COLLAPSE_BELOW = 1060
ONE_COLUMN_BELOW = 900


class Root(QWidget):
    """Central widget; forwards clicks on empty space to the bubble field so the background bubbles can be popped."""

    def __init__(self, on_click) -> None:
        super().__init__()
        self.on_click = on_click

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self.on_click(e.pos())
        super().mousePressEvent(e)


class App(MainWindow):
    def __init__(self, db: Database, data_dir: Path, font_info=None) -> None:
        QMainWindow.__init__(self)                       # deliberately NOT MainWindow.__init__: the shell below replaces it
        self.db, self.data_dir, self.font_info = db, Path(data_dir), font_info
        lang = db.get_setting("lang", "fa")
        set_language(lang)
        self.theme = Theme(lite=bool(db.get_setting("lite", False)), name=db.get_setting("theme", "liquid_dark"), accent=db.get_setting("accent", None), wallpaper=db.get_setting("wallpaper", None))
        self.focus_mode = False
        self._lang_loaded = lang
        self._gtasks_service = None
        self.tracker = Tracker(db, TrackerSettings(round_to_min=int(db.get_setting("round", 0)), min_duration_sec=int(db.get_setting("tracker_min_sec", 60)),
                                                   idle_threshold_sec=int(db.get_setting("tracker_idle_sec", 300))))
        from ..services.analytics import Analytics
        self.analytics = Analytics(db)
        self.jy = date_to_jalali(to_tehran(now_utc()).date())[0]
        self.setWindowTitle(S["app"]); self.resize(1280, 820); self.setMinimumSize(760, 560)
        self.setLayoutDirection(Qt.RightToLeft if lang == "fa" else Qt.LeftToRight)
        self.dash_cols, self._collapsed, self._detached = 2, False, {}
        self.apply_style()

        # ---- shell: background, content, effects layer
        self.root = Root(self._bg_click); self.setCentralWidget(self.root)
        self.bg = LiquidBackground(self.theme, self.root); self.bg.lower()
        self.drip = DripLayer(self.root)
        self.sounds = SoundPlayer(self.data_dir / "sounds", bool(db.get_setting("sound_enabled", True)), int(db.get_setting("sound_volume", 55)) / 100)
        self.fx = FX(self.drip, self.sounds, self.theme.lite); self.theme.fx = self.fx
        self.drip.enabled = bool(db.get_setting("fx_enabled", True)) and not self.theme.lite
        lay = QHBoxLayout(self.root); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(14)
        self.side = GlassCard(self.theme, parent=self.root); self.side.setFixedWidth(214)
        self._build_sidebar()
        main = QVBoxLayout(); main.setSpacing(12)
        main.addLayout(self._build_header())
        self.pages = QStackedWidget(); main.addWidget(self.pages, 1)
        lay.addWidget(self.side); lay.addLayout(main, 1)                   # sidebar first => on the right in Persian (RTL), on the left in English

        # ---- services used by the pages
        self.projects_svc, self.billing, self.undo = ProjectService(db), Billing(db), UndoManager(db)
        self.pomo = Pomodoro(db); self.pomo.restore()
        self.pomo_timer = QTimer(self); self.pomo_timer.setInterval(1000); self.pomo_timer.timeout.connect(self._pomo_tick)
        self.clock = QTimer(self); self.clock.setInterval(1000); self.clock.timeout.connect(self._tick)
        self.idle_timer = QTimer(self); self.idle_timer.setInterval(15000); self.idle_timer.timeout.connect(self._check_idle)
        self.reminder_timer = QTimer(self); self.reminder_timer.setInterval(60000); self.reminder_timer.timeout.connect(self._reminder_tick)
        self.act = ActivityRecorder(db, idle=system_idle_seconds); self.act_timer = QTimer(self)
        self.ambient = pm.AmbientWindow(self)
        self.ambient_timer = QTimer(self); self.ambient_timer.setInterval(30000); self.ambient_timer.timeout.connect(self._ambient_tick)
        if db.get_setting("ambient_mode", False):
            self.ambient_timer.start()
        self.mini = px.MiniTimer(self.toggle_timer); self.sfx = None; self.hotkey = None
        self.tray = Notifier(self)
        self.scrim = Scrim(self.root)

        # ---- pages (order == NAV)
        self._build_dashboard()
        self.dash_cards["tip"] = (po.build_tip_card(self), 1)
        self.layout_dashboard()
        pn.build_today(self); pn.build_tasks(self); lu.build_lists(self); pn.build_board(self); pn.build_calendar(self); px.build_planner(self); pm.build_matrix(self)
        pn.build_projects(self); pm.build_pm(self); pn.build_habits_page(self); ru.build_routines(self); pn.build_goals(self); px.build_team(self); self._build_billing()
        po.build_reports(self); px.build_analytics(self); po.build_screenshots(self); self._build_entries(); pm.build_tools(self); po.build_settings_page(self)
        assert self.pages.count() == len(NAV), "page order must match NAV"
        self._wrap_pages_in_scroll_areas()
        self.nav_buttons[0][0].primary = True
        if self.pomo.running:
            self.pomo_timer.start()

        # ---- shortcuts
        self.quick_requested.connect(self.open_quick_panel)
        for seq, fn in (("Ctrl+Shift+Space", self.open_quick_panel), ("Ctrl+Shift+F", self.toggle_focus), ("Ctrl+Shift+M", self.toggle_mini), ("Ctrl+K", self.open_palette),
                        ("Ctrl+N", self.new_task), ("Ctrl+Z", lambda: (self.undo.undo(), self.refresh_all())), ("Ctrl+Y", lambda: (self.undo.redo(), self.refresh_all()))):
            QShortcut(QKeySequence(seq), self, activated=fn)

        self.tracker.recover_after_crash()
        self.runtime = Runtime(self)
        self.bubble = FloatingBubble(self)
        self.refresh_all()
        self.runtime.start()
        if db.get_setting("global_hotkey", False):
            self._set_hotkey(True)
        if self.tracker.running():
            self.clock.start(); self.idle_timer.start(); self.reminder_timer.start()
        self.goto(0)
        if db.get_setting("float_enabled", True):
            self.bubble.show()

    # ================================================================== backup / restore aftermath, language restart, daily report
    def after_restore(self) -> None:
        """Everything that cached the old data/settings is rebuilt from the database (called after a restore or a configuration import)."""
        db = self.db
        self.theme.set_name(db.get_setting("theme", "tokyo_night")); self.theme.custom_accent = db.get_setting("accent", None)
        self.theme.lite = bool(db.get_setting("lite", False)); self.theme.wallpaper = db.get_setting("wallpaper", None)
        self.bg.reload_wallpaper(); self.bg._cache = None
        self.undo = UndoManager(db); self.pomo = Pomodoro(db); self.pomo.restore()
        self.runtime.reset_state()
        self.apply_style()
        self.set_bubble(bool(db.get_setting("float_enabled", True)), persist=False)      # a restore must not write settings of its own
        self.refresh_all()
        for w in self.findChildren(QWidget):
            w.update()
        if db.get_setting("lang", "fa") != self._lang_loaded:
            self.ask_restart_for_language()

    def ask_restart_for_language(self) -> None:
        if self.db.get_setting("lang", "fa") == self._lang_loaded:
            return
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, S["app"], S["restart_ask"]) == QMessageBox.Yes:
            self.restart_app()

    def restart_app(self) -> None:
        """Start a fresh process (new language / direction) and quit this one."""
        import sys
        from PyQt5.QtCore import QProcess
        QProcess.startDetached(sys.executable, sys.argv)
        QApplication.quit()

    def open_daily_report(self) -> None:
        from .daily_ui import DailyReportDialog
        DailyReportDialog(self).exec_()

    # ================================================================== floating quick-access bubble
    def set_bubble(self, on: bool, persist: bool = True) -> None:
        if persist:
            self.db.set_setting("float_enabled", bool(on))
        if on:
            self.bubble.reload(); self.bubble.show()
        else:
            self.bubble.hide()
            if self.bubble.panel is not None:
                self.bubble.panel.close()

    def open_quick_panel(self) -> None:
        """Ctrl+Shift+Space / global hotkey / palette: the quick-add panel next to the bubble (the bubble is shown if it was hidden)."""
        if not self.bubble.isVisible():
            self.bubble.reload(); self.bubble.show()
        self.bubble.open_panel()

    # ================================================================== styling
    def apply_style(self) -> None:
        stack = self.font_info.stack() if self.font_info is not None else "'IRANSans', 'Vazirmatn', Tahoma, sans-serif"
        asset_dir = None
        try:
            asset_dir = icons.export_pngs(self.data_dir / "ui", self.theme.t["muted"])           # arrows / check mark images the stylesheet needs
        except Exception:  # noqa: BLE001 - cosmetic
            log.exception("could not export stylesheet images")
        sheet = build_qss(self.theme, stack, asset_dir)
        app = QApplication.instance()
        (app.setStyleSheet if app is not None else self.setStyleSheet)(sheet)

    def apply_theme(self, name: str) -> None:
        """Switch palette live: stylesheet, background, every custom-painted widget and the open page are refreshed immediately."""
        self.theme.set_name(name)
        self.db.set_setting("theme", self.theme.name)
        self.apply_style()
        self.bg._cache = None
        for w in self.findChildren(QWidget):
            w.update()
        self.refresh_visible()
        if self.theme.fx is not None:
            self.theme.fx.play("drop_in", 0.7)

    def _field_style(self) -> str:                       # older page builders call this; the global stylesheet already covers everything
        return ""

    def apply_accent(self, color: Optional[str]) -> None:
        self.theme.custom_accent = color or None
        self.apply_style()
        for w in self.findChildren(QWidget):
            w.update()

    def set_wallpaper(self, path: Optional[str]) -> None:
        self.theme.wallpaper = path
        self.bg.reload_wallpaper()

    def on_setting_changed(self, key: str, value) -> None:
        if key == "lite":
            self.theme.lite = bool(value); self.fx.lite = bool(value)
            (self.bg.stop if value else self.bg.start)()
        elif key in ("tips_enabled", "tips_disabled_cats"):
            po.refresh_tip(self)
        elif key == "activity_capture" and not value:
            self.act.flush()
        elif key == "float_enabled":
            self.set_bubble(bool(value))
        elif key.startswith("float_"):
            self.bubble.reload()

    # ================================================================== shell widgets
    def _build_dashboard(self) -> None:
        dash.build_dashboard(self)

    def _wrap_pages_in_scroll_areas(self) -> None:
        """A page never gets squeezed below the size its content needs: if the window is small the page scrolls instead (widgetResizable keeps it
        stretching to fill a big window)."""
        for i in range(self.pages.count()):
            page = self.pages.widget(i)
            self.pages.removeWidget(page)
            sa = QScrollArea(); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.NoFrame); sa.setWidget(page)
            sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.pages.insertWidget(i, sa)

    def quick_start(self, title: str, project_id=None, category: str = "general") -> None:
        """One click from a recent-task chip: start (and switch to) that task."""
        self.tracker.start(title, project_id=project_id, category=category)
        self._timers_on(); self.refresh_all()
        if self.theme.fx is not None:
            self.theme.fx.play("bloop")

    def stop_timer(self, entry_id: str) -> None:
        self._finish(self.tracker.stop(entry_id=entry_id))
        if not self.tracker.running():
            self._timers_off()
        self.refresh_all()

    def _build_sidebar(self) -> None:
        v = QVBoxLayout(self.side); v.setContentsMargins(10, 14, 10, 12); v.setSpacing(6)
        head = QHBoxLayout(); logo = QLabel(); logo.setPixmap(icons.pixmap("bubble", self.theme.accents[1], 30)); head.addWidget(logo)
        self.brand = self.label(S["app"], 14, True); head.addWidget(self.brand, 1)
        v.addLayout(head)
        host = QWidget(); hl = QVBoxLayout(host); hl.setContentsMargins(0, 4, 0, 4); hl.setSpacing(5)
        self.nav_buttons: List[tuple] = []
        for i, (key, ic) in enumerate(NAV):
            b = GlassButton(S[key], self.theme, icon=ic); b.setMinimumHeight(42); b.setToolTip(S[key])
            b.clicked.connect(lambda _c=False, n=i: self.goto(n)); hl.addWidget(b); self.nav_buttons.append((b, key))
        hl.addStretch()
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(host); sa.setFrameShape(QFrame.NoFrame); v.addWidget(sa, 1)
        self.collapse_btn = GlassButton(S["collapse"], self.theme, icon="chevron_right"); self.collapse_btn.clicked.connect(lambda: self.set_sidebar(not self._collapsed)); v.addWidget(self.collapse_btn)

    def set_sidebar(self, collapsed: bool) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.side.setFixedWidth(72 if collapsed else 214)
        self.brand.setVisible(not collapsed)
        for b, key in self.nav_buttons:
            b.setText("" if collapsed else S[key])
        self.collapse_btn.setText("" if collapsed else S["collapse"])
        self.collapse_btn.icon_name = "chevron_left" if collapsed else "chevron_right"
        if self.theme.fx is not None:
            self.theme.fx.play("click")
        self.refresh_visible()

    def _build_header(self) -> QHBoxLayout:
        h = QHBoxLayout(); h.setSpacing(10)
        self.hd_title = self.label(S["dashboard"], 18, True); h.addWidget(self.hd_title, 1)
        self.tip_btn = QPushButton(); self.tip_btn.setProperty("ghost", True); self.tip_btn.setCursor(Qt.PointingHandCursor); self.tip_btn.setMaximumWidth(460)
        self.tip_btn.setIcon(icons.icon("lightbulb", "#FFB020", 20)); self.tip_btn.clicked.connect(lambda: po.TipDialog(self).exec_()); h.addWidget(self.tip_btn)
        self.hd_timer = QPushButton(); self.hd_timer.setProperty("chip", True); self.hd_timer.setCursor(Qt.PointingHandCursor); self.hd_timer.clicked.connect(self.toggle_timer); self.hd_timer.hide(); h.addWidget(self.hd_timer)
        self.snd_btn = GlassButton("", self.theme, icon="sound"); self.snd_btn.setFixedSize(42, 42); self.snd_btn.clicked.connect(self.toggle_sound); h.addWidget(self.snd_btn)
        sb = GlassButton("", self.theme, icon="search"); sb.setFixedSize(42, 42); sb.setToolTip("Ctrl+K"); sb.clicked.connect(self.open_palette); h.addWidget(sb)
        nb = GlassButton(S["new_task"], self.theme, primary=True, icon="plus"); nb.clicked.connect(self.new_task); self.new_btn = nb; h.addWidget(nb)
        return h

    # ================================================================== actions
    def toast(self, text: str) -> None:
        Toast.show_message(self.root, self.theme, text)

    def new_task(self, defaults: Optional[dict] = None) -> None:
        pn.open_task(self, defaults=defaults if isinstance(defaults, dict) else None)

    def toggle_sound(self) -> None:
        on = not bool(self.db.get_setting("sound_enabled", True))
        self.db.set_setting("sound_enabled", on); self.sounds.enabled = on
        self.snd_btn.icon_name = "sound" if on else "mute"; self.snd_btn.update()
        if on:
            self.sounds.play("bloop")

    def _bg_click(self, pos) -> None:
        self.bg.try_pop(pos)

    # ================================================================== navigation / refresh
    def goto(self, n) -> None:                           # accepts an index or a page key
        if isinstance(n, str):
            n = PAGE_KEYS.index(n)
        key = PAGE_KEYS[n]
        if n in self._detached:
            self._detached[n].raise_(); self._detached[n].activateWindow(); return
        self.pages.setCurrentIndex(n)
        for i, (b, _k) in enumerate(self.nav_buttons):
            b.primary = (i == n); b.update()
        self.hd_title.setText(S[key])
        self.refresh_visible()
        if self.theme.fx is not None and self.isVisible():
            self.theme.fx.play("bloop", 0.4)

    def current_key(self) -> str:
        return PAGE_KEYS[max(0, self.pages.currentIndex())]

    def refresh_visible(self) -> None:
        key = self.current_key()
        fn = {"today": lambda: pn.refresh_today(self), "tasks": lambda: pn.refresh_tasks(self), "lists": lambda: lu.refresh_lists(self), "board": lambda: pn.refresh_board(self), "calendar": lambda: pn.refresh_calendar(self),
              "planner": lambda: px.refresh_planner(self), "matrix": lambda: pm.refresh_matrix(self), "projects": lambda: pn.refresh_projects(self), "pm": lambda: pm.refresh_pm(self),
              "habits": lambda: pn.refresh_habits_page(self), "routines": lambda: ru.refresh_routines(self), "goals": lambda: pn.refresh_goals(self), "team": lambda: px.refresh_team(self), "billing": self.refresh_billing,
              "reports": lambda: po.refresh_reports(self), "analytics": lambda: px.refresh_analytics(self), "screenshots": lambda: po.refresh_screenshots(self),
              "entries": self.refresh_entries, "tools": lambda: pm.refresh_tools(self)}.get(key)
        if fn is not None:
            try:
                fn()
            except Exception:  # noqa: BLE001 - one broken page must never blank the whole app
                log.exception("refresh of page %s failed", key)

    def refresh_projects(self) -> None:                  # the old project list widget no longer exists; kept so older code paths stay valid
        return None

    def refresh_all(self) -> None:
        dash.refresh_dashboard(self)
        self.refresh_entries()
        self.refresh_visible()
        po.refresh_tip(self)

    def _tick(self) -> None:
        super()._tick()
        dash.update_running(self)
        cur = self.tracker.current
        if cur is not None:
            s = self.tracker.elapsed()
            self.hd_timer.setText("⏱  " + to_fa_digits(f"{cur.title[:22]}  {s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}")); self.hd_timer.show()
        else:
            self.hd_timer.hide()

    def _timers_off(self) -> None:
        super()._timers_off()
        self.hd_timer.hide()

    # ================================================================== responsiveness
    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        r = self.root.rect()
        self.drip.setGeometry(r); self.scrim.fit()
        w = self.width()
        if w < COLLAPSE_BELOW and not self._collapsed and not getattr(self, "_user_expanded", False):
            self.set_sidebar(True)
        elif w >= COLLAPSE_BELOW + 160 and self._collapsed and not getattr(self, "_user_collapsed", False):
            self.set_sidebar(False)
        self.tip_btn.setVisible(w >= 1000)
        cols = 1 if w < ONE_COLUMN_BELOW else (2 if w < 1560 else 3)
        if cols != self.dash_cols:
            self.dash_cols = cols; self.layout_dashboard()
            QTimer.singleShot(120, self.refresh_visible)

    # ================================================================== palette + lifecycle
    def open_palette(self) -> None:
        acts: Dict[str, object] = {S[k]: (lambda n=i: self.goto(n)) for i, (k, _ic) in enumerate(NAV)}
        acts[S["new_task"]] = self.new_task
        acts[S["quick"]] = self.open_quick_panel
        acts[S["float_toggle"]] = lambda: self.set_bubble(not self.bubble.isVisible())
        acts[S["start"] + " / " + S["stop"]] = self.toggle_timer
        acts[S["capture_now"]] = lambda: po._shot_now(self)
        acts[S["prompt_test"]] = lambda: self.runtime.show_prompt(force=True)
        acts[S["backup"]] = self._backup
        acts[S["undo"]] = self.undo.undo; acts[S["redo"]] = self.undo.redo
        acts[S["focus"]] = self.toggle_focus; acts[S["mini"]] = self.toggle_mini; acts[S["ambient"]] = self.show_ambient; acts[S["detach"]] = self.detach_current
        acts[S["year_review"]] = lambda: px.show_year_review(self)
        acts[S["dr_open"]] = self.open_daily_report
        CommandPalette(acts, self).exec_()

    def detach_current(self) -> None:
        i = self.pages.currentIndex()
        if i in self._detached or self.pages.count() < 2:
            return
        page = self.pages.widget(i)
        self.pages.removeWidget(page)
        def back(w, idx=i) -> None:
            self.pages.insertWidget(idx, w); self._detached.pop(idx, None); self.pages.setCurrentIndex(idx)
        win = pm.DetachedWindow(page, S[PAGE_KEYS[i]], back)
        self._detached[i] = win; win.show()
        self.pages.setCurrentIndex(0 if i else 1)

    def closeEvent(self, e) -> None:  # noqa: N802
        try:
            self.runtime.stop()
        except Exception:  # noqa: BLE001
            log.exception("runtime stop failed")
        for w in list(self._detached.values()):
            w.close()
        self.ambient.close(); self.mini.close()
        if self.bubble.panel is not None:
            self.bubble.panel.close()
        self.bubble.close()
        for t in (self.clock, self.idle_timer, self.pomo_timer, self.reminder_timer, self.ambient_timer):
            t.stop()
        self.bg.stop()
        QMainWindow.closeEvent(self, e)
