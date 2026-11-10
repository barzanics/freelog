"""Main window: glass sidebar + pages. UI never touches SQL; it calls services."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Callable, List, Optional

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, QVariant, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QAbstractItemView, QColorDialog, QScrollArea, QInputDialog, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QGridLayout,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
                             QShortcut, QSpinBox, QStackedWidget, QSystemTrayIcon, QTableView, QVBoxLayout, QWidget)

from ..core.database import Database, import_legacy
from ..core.models import KANBAN_COLUMNS, Client, Invoice, Project, Status, TimeEntry
from ..core.persian import (date_to_jalali, format_duration, format_jalali, jalali_year_bounds, now_utc, to_fa_digits,
                            to_tehran)
from ..integrations import ical
from ..services import exporter, security
from ..services.billing import Billing
from ..services.pomodoro import Pomodoro
from ..services.projects import ProjectService
from ..services.undo import UndoManager
from ..services import folder_sync, search as smart_search, sound
from ..services.automation import Automation
from ..integrations.webhook import post_json
from ..services.activity import ActivityRecorder
from ..services.hotkey import WindowsHotkey
from ..services.reminders import MESSAGES, Reminders
from ..core.persian import now_utc as _now
from ..themes_list import THEME_NAMES
from . import pages_extra as px
from . import pm_pages as pm
from .glass import make_icon
from ..services.analytics import Analytics
from ..services.idle import system_idle_seconds
from ..services.tracker import Tracker, TrackerSettings
from .glass import Toast, THEMES, ACCENTS, BarChart, Donut, GlassButton, GlassCard, Heatmap, LiquidBackground, PomodoroOrb, Theme, qcolor
from .strings import MONTHS_SHORT, S, set_language

log = logging.getLogger("worktracker.ui")
THEME_LABELS = {n: THEMES[n]["label"] for n in THEME_NAMES}
PAGES = ("dashboard", "entries", "kanban", "planner", "matrix", "pm", "billing", "analytics", "habits", "team", "projects", "tools", "settings")


class Notifier:
    """Tray balloon when the OS has a tray, otherwise an in-app liquid toast. Always truthy so callers need no checks."""

    def __init__(self, win) -> None:
        self.win = win
        self.tray = QSystemTrayIcon(win) if QSystemTrayIcon.isSystemTrayAvailable() else None
        self.set_icon("WT", "#6D5DFC")

    def set_icon(self, text: str, color: str) -> None:
        """Dynamic tray icon (elapsed minutes while tracking)."""
        if self.tray is not None:
            self.tray.setIcon(make_icon(text, color)); self.tray.show()

    def showMessage(self, title: str, text: str) -> None:  # noqa: N802 - mirrors Qt naming for drop-in use
        if self.tray is not None:
            self.tray.showMessage(title, text)
        else:
            Toast.show_message(self.win.centralWidget(), self.win.theme, text)


class KanbanList(QListWidget):
    """Drag-drop column; reports moved card ids so the service can validate (dependencies etc.)."""

    def __init__(self, column: str, on_move: Callable[[str, str], None], parent=None) -> None:
        super().__init__(parent)
        self.column, self.on_move = column, on_move
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setCursor(Qt.PointingHandCursor)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dropEvent(self, e) -> None:  # noqa: N802
        src = e.source()
        ids = [i.data(Qt.UserRole) for i in src.selectedItems()] if isinstance(src, QListWidget) else []
        super().dropEvent(e)
        for _id in ids:
            self.on_move(_id, self.column)


def safe(fn: Callable) -> Callable:
    """Decorator: show a friendly dialog instead of crashing a slot."""
    def wrapper(self, *a, **k):
        try:
            return fn(self, *a)
        except Exception as exc:  # noqa: BLE001 - boundary of the UI
            log.exception("action failed")
            QMessageBox.warning(self, S["error"], f"{exc}")
    return wrapper


class EntryModel(QAbstractTableModel):
    """Virtualised table model; Qt only asks for the visible rows."""
    COLS = ("title", "project", "start_t", "duration")

    def __init__(self, names: dict, parent=None) -> None:
        super().__init__(parent)
        self.rows: List[TimeEntry] = []
        self.names = names

    def set_rows(self, rows: List[TimeEntry]) -> None:
        self.beginResetModel(); self.rows = rows; self.endResetModel()

    def rowCount(self, _p=QModelIndex()) -> int:  # noqa: N802
        return len(self.rows)

    def columnCount(self, _p=QModelIndex()) -> int:  # noqa: N802
        return len(self.COLS)

    def headerData(self, s, o, role=Qt.DisplayRole):  # noqa: N802
        return S[self.COLS[s]] if o == Qt.Horizontal and role == Qt.DisplayRole else QVariant()

    def data(self, idx, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        e = self.rows[idx.row()]
        c = idx.column()
        if c == 0:
            return e.title
        if c == 1:
            return self.names.get(e.project_id or "", "—")
        if c == 2:
            t = to_tehran(e.start_utc)
            return to_fa_digits(f"{format_jalali(t.date(), fa_digits=False)}  {t:%H:%M}")
        return to_fa_digits(format_duration(e.duration_sec))


def QListWidgetItem_(text: str, uid: str):
    from PyQt5.QtWidgets import QListWidgetItem
    it = QListWidgetItem(text); it.setData(Qt.UserRole, uid); return it


class CommandPalette(QDialog):
    """Ctrl+K: fuzzy-filter every registered action."""

    def __init__(self, actions: dict, parent=None) -> None:
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.actions = actions
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        self.edit = QLineEdit(placeholderText=S["palette"])
        self.list = QListWidget(); self.list.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.edit); lay.addWidget(self.list)
        self.edit.textChanged.connect(self._filter)
        self.edit.returnPressed.connect(self._run)
        self.list.itemActivated.connect(lambda _i: self._run())
        self._filter("")

    def _filter(self, text: str) -> None:
        self.list.clear()
        letters = text.lower().replace(" ", "")
        for name in self.actions:
            it = iter(name.lower())
            if all(ch in it for ch in letters):  # subsequence match
                self.list.addItem(name)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _run(self) -> None:
        it = self.list.currentItem()
        if it:
            self.accept()
            self.actions[it.text()]()


class MainWindow(QMainWindow):
    quick_requested = pyqtSignal()   # emitted from the global-hotkey thread; handled on the GUI thread

    def __init__(self, db: Database, data_dir: Path) -> None:
        super().__init__()
        self.db, self.data_dir = db, Path(data_dir)
        set_language(db.get_setting("lang", "fa"))
        self.theme = Theme(lite=bool(db.get_setting("lite", False)), name=db.get_setting("theme", "liquid_dark"),
                           accent=db.get_setting("accent", None), wallpaper=db.get_setting("wallpaper", None))
        self.focus_mode = False
        self.tracker = Tracker(db, TrackerSettings(round_to_min=int(db.get_setting("round", 0))))
        self.analytics = Analytics(db)
        self.jy = date_to_jalali(to_tehran(now_utc()).date())[0]
        self.setWindowTitle(S["app"]); self.resize(1200, 780)
        self.setLayoutDirection(Qt.RightToLeft if db.get_setting("lang", "fa") == "fa" else Qt.LeftToRight)

        self.bg = LiquidBackground(self.theme, self)
        root = QWidget(self); self.setCentralWidget(root)
        self.bg.setParent(root); self.bg.lower()
        lay = QHBoxLayout(root); lay.setContentsMargins(18, 18, 18, 18); lay.setSpacing(16)

        self.side = GlassCard(self.theme, parent=root); self.side.setFixedWidth(190)
        sl = QVBoxLayout(self.side); sl.setContentsMargins(14, 18, 14, 18); sl.setSpacing(8)
        self.pages = QStackedWidget()
        self.nav: List[GlassButton] = []
        for i, key in enumerate(PAGES):
            b = GlassButton(S[key], self.theme, primary=(i == 0))
            b.clicked.connect(lambda _c, n=i: self.goto(n)); sl.addWidget(b); self.nav.append(b)
        sl.addStretch()
        lay.addWidget(self.pages, 1); lay.addWidget(self.side)

        self.projects_svc, self.billing, self.undo = ProjectService(db), Billing(db), UndoManager(db)
        self.pomo = Pomodoro(db); self.pomo.restore()
        self.pomo_timer = QTimer(self); self.pomo_timer.setInterval(1000); self.pomo_timer.timeout.connect(self._pomo_tick)
        self._detached: dict = {}
        self._build_dashboard(); self._build_entries(); self._build_kanban(); px.build_planner(self); pm.build_matrix(self); pm.build_pm(self)
        self._build_billing(); px.build_analytics(self); px.build_habits(self); px.build_team(self); self._build_projects(); pm.build_tools(self); self._build_settings()
        if self.pomo.running:
            self.pomo_timer.start()

        self.clock = QTimer(self); self.clock.setInterval(1000); self.clock.timeout.connect(self._tick)
        self.idle_timer = QTimer(self); self.idle_timer.setInterval(15000); self.idle_timer.timeout.connect(self._check_idle)
        self.reminder_timer = QTimer(self); self.reminder_timer.setInterval(60000); self.reminder_timer.timeout.connect(self._reminder_tick)
        self.act = ActivityRecorder(db, idle=system_idle_seconds)
        self.act_timer = QTimer(self); self.act_timer.setInterval(5000); self.act_timer.timeout.connect(self.act.sample)
        if db.get_setting("activity_capture", False):
            self.act_timer.start()
        self.ambient = pm.AmbientWindow(self)
        self.ambient_timer = QTimer(self); self.ambient_timer.setInterval(30000); self.ambient_timer.timeout.connect(self._ambient_tick)
        if db.get_setting("ambient_mode", False):
            self.ambient_timer.start()
        self.mini = px.MiniTimer(self.toggle_timer); self.sfx = None; self.hotkey: Optional[WindowsHotkey] = None
        self.quick_requested.connect(lambda: px.quick_capture(self))
        QShortcut(QKeySequence("Ctrl+Shift+Space"), self, activated=lambda: px.quick_capture(self))
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, activated=self.toggle_focus)
        QShortcut(QKeySequence("Ctrl+Shift+M"), self, activated=self.toggle_mini)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_palette)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=lambda: (self.undo.undo(), self.refresh_all()))
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=lambda: (self.undo.redo(), self.refresh_all()))
        self.tray = Notifier(self)

        self.tracker.recover_after_crash()
        self.refresh_all()
        if db.get_setting("global_hotkey", False):
            self._set_hotkey(True)
        if self.tracker.running():
            self.clock.start(); self.idle_timer.start(); self.reminder_timer.start()

    # ---- window plumbing ------------------------------------------
    def resizeEvent(self, e) -> None:  # noqa: N802
        self.bg.setGeometry(self.centralWidget().rect()); super().resizeEvent(e)

    def showEvent(self, e) -> None:  # noqa: N802
        self.bg.start(); super().showEvent(e)

    def hideEvent(self, e) -> None:  # noqa: N802
        self.bg.stop(); super().hideEvent(e)

    def changeEvent(self, e) -> None:  # noqa: N802
        (self.bg.start if self.isActiveWindow() and not self.isMinimized() else self.bg.stop)()
        super().changeEvent(e)

    def closeEvent(self, e) -> None:  # noqa: N802
        for w in list(self._detached.values()):
            w.close()
        self.ambient.close()
        for t in (self.clock, self.idle_timer, self.pomo_timer, self.reminder_timer, self.act_timer, self.ambient_timer):
            t.stop()
        self.act.flush(); self.mini.close()
        if self.hotkey:
            self.hotkey.stop()
        if self.sfx:
            self.sfx.stop()
        self.bg.stop()
        super().closeEvent(e)

    def goto(self, n: int) -> None:
        if n in self._detached:                      # page lives in its own window: just raise it
            self._detached[n].raise_(); self._detached[n].activateWindow(); return
        self.pages.setCurrentIndex(n)
        for i, b in enumerate(self.nav):
            b.primary = (i == n); b.update()
        refresh = {"entries": self.refresh_entries, "kanban": self.refresh_board, "planner": lambda: px.refresh_planner(self),
                   "billing": self.refresh_billing, "analytics": lambda: px.refresh_analytics(self),
                   "habits": lambda: px.refresh_habits(self), "team": lambda: px.refresh_team(self),
                   "matrix": lambda: pm.refresh_matrix(self), "pm": lambda: pm.refresh_pm(self), "tools": lambda: pm.refresh_tools(self)}.get(PAGES[n])
        if refresh:
            refresh()

    def card(self) -> GlassCard:
        c = GlassCard(self.theme); return c

    def label(self, text="", size=11, bold=False, muted=False) -> QLabel:
        """Plain label. Colour comes from the global stylesheet (muted=True -> secondary colour), so switching themes restyles it live."""
        l = QLabel(text)
        f = l.font(); f.setPointSizeF(float(size)); f.setBold(bool(bold)); l.setFont(f)
        l.setProperty("muted", bool(muted))
        if len(str(text)) > 32:
            l.setWordWrap(True)
        return l

    def _field_style(self) -> str:
        c = self.theme.text().name()
        return (f"QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox{{color:{c};background:rgba(255,255,255,26);border:1px solid rgba(255,255,255,70);"
                f"border-radius:12px;padding:8px;}}QTableView{{color:{c};background:transparent;border:none;gridline-color:transparent;}}"
                f"QHeaderView::section{{color:{self.theme.text(True).name()};background:transparent;border:none;padding:6px;}}"
                f"QListWidget{{color:{c};background:rgba(255,255,255,20);border:none;}}QCheckBox{{color:{c};}}"
                f"QComboBox QAbstractItemView{{color:{c};background:#1b1b33;}}")

    # ---- dashboard ---------------------------------------------------
    def _build_dashboard(self) -> None:
        page = QWidget(); page.setStyleSheet(self._field_style()); g = QGridLayout(page); g.setSpacing(16)
        hero = self.card(); hl = QVBoxLayout(hero); hl.setContentsMargins(24, 18, 24, 18)
        self.hero_hours = self.label("۰", 40, True)
        hl.addWidget(self.label(S["hours_year"], 11, muted=True)); hl.addWidget(self.hero_hours)
        self.hero_stats = self.label("", 10, muted=True); hl.addWidget(self.hero_stats)

        tc = self.card(); tl = QVBoxLayout(tc); tl.setContentsMargins(24, 18, 24, 18)
        self.timer_lbl = self.label("0:00:00", 30, True)
        self.t_title = QLineEdit(placeholderText=S["what"]); self.t_proj = QComboBox(); self.t_energy = QComboBox()
        self.t_energy.addItem(S["energy"], 0)
        for lv in range(1, 6):
            self.t_energy.addItem(to_fa_digits(str(lv)), lv)
        self.t_btn = GlassButton(S["start"], self.theme, primary=True); self.t_btn.clicked.connect(self.toggle_timer)
        self.t_title.returnPressed.connect(self.toggle_timer)
        self.t_par = GlassButton(S["parallel"], self.theme); self.t_par.clicked.connect(self.start_parallel)
        for w in (self.timer_lbl, self.t_title, self.t_proj, self.t_energy, self.t_btn, self.t_par):
            tl.addWidget(w)

        hm = self.card(); ml = QVBoxLayout(hm); self.heat = Heatmap(self.theme); ml.addWidget(self.heat)
        dc = self.card(); dl = QVBoxLayout(dc); dl.addWidget(self.label(S["by_project"], 11, True))
        self.donut = Donut(self.theme); dl.addWidget(self.donut)
        bc = self.card(); bl = QVBoxLayout(bc); bl.addWidget(self.label(S["by_month"], 11, True))
        self.bars = BarChart(self.theme, MONTHS_SHORT); bl.addWidget(self.bars)
        pc = self.card(); pl = QHBoxLayout(pc); pl.setContentsMargins(18, 12, 18, 12)
        self.orb = PomodoroOrb(self.theme); pl.addWidget(self.orb)
        pcol = QVBoxLayout(); pcol.addWidget(self.label(S["pomo"], 11, True))
        self.pomo_btn = GlassButton(S["pomo_start"], self.theme, primary=True); self.pomo_btn.clicked.connect(self.pomo_toggle)
        self.pomo_reset = GlassButton(S["pomo_reset"], self.theme); self.pomo_reset.clicked.connect(self.pomo_do_reset)
        pcol.addWidget(self.pomo_btn); pcol.addWidget(self.pomo_reset); pcol.addStretch(); pl.addLayout(pcol)
        self.dash_grid = g
        self.dash_cards = {"hero": (hero, 1), "timer": (tc, 1), "heatmap": (hm, 2), "donut": (dc, 1), "bars": (bc, 1), "pomodoro": (pc, 2)}
        g.setColumnStretch(0, 1); g.setColumnStretch(1, 1)
        self.pages.addWidget(page)
        self.layout_dashboard()
        self._pomo_tick()

    def layout_dashboard(self) -> None:
        """Flow the cards in their saved order into 1-3 columns. A card with span 2 takes two columns (clamped to the column count); rows never squash a card
        below its minimum height because the page lives in a scroll area."""
        from ..services import metrics
        order = metrics.get_dashboard(self.db, "default")
        ncols = max(1, min(3, int(getattr(self, "dash_cols", 2))))
        g = self.dash_grid
        for w, _span in self.dash_cards.values():
            g.removeWidget(w); w.setVisible(False)
        for r in range(32):
            g.setRowStretch(r, 0)
        for c in range(4):
            g.setColumnStretch(c, 1 if c < ncols else 0)
            g.setColumnMinimumWidth(c, 0)
        row = col = 0
        for key in order:
            if key not in self.dash_cards:
                continue
            w, span = self.dash_cards[key]
            span = max(1, min(int(span), ncols))
            if col + span > ncols:
                row, col = row + 1, 0
            g.addWidget(w, row, col, 1, span)
            w.setVisible(True)
            col += span
            if col >= ncols:
                row, col = row + 1, 0
        for r in range(row + 1):
            g.setRowStretch(r, 1)

    # ---- pomodoro ---------------------------------------------------
    @safe
    def pomo_toggle(self, *_: object) -> None:
        p = self.pomo
        if p.phase == "idle":
            p.start(); self.pomo_timer.start()
        elif p.paused:
            p.resume(); self.pomo_timer.start()
        else:
            p.pause()
        self._pomo_tick()

    @safe
    def pomo_do_reset(self, *_: object) -> None:
        self.pomo.reset(); self.pomo_timer.stop(); self._pomo_tick()

    def _pomo_tick(self) -> None:
        p = self.pomo
        new = p.tick()
        if new and self.tray:
            self.tray.showMessage(S["app"], S["pomo"] + ": " + new)
        if p.phase == "idle":
            self.pomo_timer.stop()
        r = p.remaining() if p.phase != "idle" else p.cfg.work_min * 60
        sub = {"work": S["work"], "short_break": S["short_break"], "long_break": S["long_break"]}.get(p.phase, "")
        self.orb.set_state(p.fill_level(), to_fa_digits(f"{r // 60}:{r % 60:02d}"), p.phase, to_fa_digits(sub + (f" · {p.completed_work}/{p.cfg.cycles_before_long}" if p.phase != "idle" else "")))
        self.pomo_btn.setText(S["pomo_resume"] if p.paused else S["pomo_pause"] if p.phase != "idle" else S["pomo_start"])

    def _timers_on(self) -> None:
        self.t_btn.setText(S["stop_all"] if len(self.tracker.running()) > 1 else S["stop"])
        self.clock.start(); self.idle_timer.start(); self.reminder_timer.start()

    def _timers_off(self) -> None:
        for t in (self.clock, self.idle_timer, self.reminder_timer):
            t.stop()
        self.t_btn.setText(S["start"]); self.timer_lbl.setText("0:00:00"); self.mini.set_state("—", 0); self.tray.set_icon("WT", "#6D5DFC")

    @safe
    def toggle_timer(self, *_: object) -> None:
        running = self.tracker.running()
        if running:
            for r in running:
                self._finish(self.tracker.stop(entry_id=r.id))
            self._timers_off()
        else:
            title = self.t_title.text().strip()
            if not title:
                raise ValueError(S["need_title"])
            e = self.tracker.start(title, project_id=self.t_proj.currentData())
            if self.t_energy.currentData():
                e.energy = int(self.t_energy.currentData()); self.db.save(e)
            self._timers_on(); self.t_title.clear()
        self.t_btn.update(); self.refresh_all()

    @safe
    def start_parallel(self, *_: object) -> None:
        title = self.t_title.text().strip()
        if not title:
            raise ValueError(S["need_title"])
        self.tracker.start(title, project_id=self.t_proj.currentData(), exclusive=False)
        self._timers_on(); self.t_title.clear(); self.refresh_all()

    def _finish(self, entry) -> None:
        """Run automation rules on a freshly stopped entry (webhooks fire only if a rule asks for one)."""
        if entry is not None:
            Automation(self.db, webhook=post_json).apply(entry)

    def _tick(self) -> None:
        s = self.tracker.elapsed()
        text = to_fa_digits(f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}")
        self.timer_lbl.setText(text)
        cur = self.tracker.current
        self.mini.set_state(cur.title if cur else "—", s)
        if s % 60 == 0:
            self.tray.set_icon(str(s // 60) if s < 6000 else f"{s // 3600}h", "#FF3D71")

    def _check_idle(self) -> None:
        idle = system_idle_seconds()
        running = self.tracker.running()
        if running and idle >= self.tracker.settings.idle_threshold_sec:
            for r in running:
                self._finish(self.tracker.stop(idle_seconds=idle, entry_id=r.id))
            self._timers_off()
            if self.tray:
                self.tray.showMessage(S["app"], S["idle_stopped"])
            self.refresh_all()

    def _reminder_tick(self) -> None:
        for kind in Reminders(self.db).due(working=bool(self.tracker.running()), focus_mode=self.focus_mode):
            if self.tray:
                self.tray.showMessage(S["app"], MESSAGES[kind])

    def toggle_focus(self) -> None:
        """Focus mode: hide the sidebar, jump to the dashboard and silence reminders."""
        self.focus_mode = not self.focus_mode
        self.side.setVisible(not self.focus_mode)
        if self.focus_mode:
            self.goto(0)
            if self.tray:
                self.tray.showMessage(S["app"], S["focus_on"])

    def _ambient_tick(self) -> None:
        """Show the screensaver after 10 idle minutes; keep it fresh while visible."""
        if self.ambient.isVisible():
            self.ambient.refresh()
        elif system_idle_seconds() >= 600:
            self.ambient.refresh(); self.ambient.showFullScreen()

    def show_ambient(self) -> None:
        self.ambient.refresh(); self.ambient.showFullScreen()

    def detach_current(self) -> None:
        """Multi-window: move the current page into its own window; closing it puts the page back."""
        i = self.pages.currentIndex()
        if i in self._detached or i == len(PAGES) - 1 and False:
            return
        page = self.pages.widget(i)
        self.pages.removeWidget(page)

        def back(w, idx=i) -> None:
            self.pages.insertWidget(idx, w); self._detached.pop(idx, None); self.pages.setCurrentIndex(idx)
        win = pm.DetachedWindow(page, S[PAGES[i]], back)
        self._detached[i] = win
        win.show()
        self.pages.setCurrentIndex(0 if i else min(1, self.pages.count() - 1))

    def toggle_mini(self) -> None:
        if self.mini.isVisible():
            self.mini.hide()
        else:
            self.mini.show()

    def refresh_all(self) -> None:
        names = {p.id: p.name for p in self.db.all(Project)}
        self.t_proj.clear(); self.t_proj.addItem(S["no_project"], None)
        for pid, n in names.items():
            self.t_proj.addItem(n, pid)
        today = to_tehran(now_utc()).date()
        s = self.analytics.year_summary(self.jy, today)
        self.hero_hours.setText(to_fa_digits(f"{s.total_hours:.1f}"))
        self.hero_stats.setText(to_fa_digits(
            f"{S['days_worked']}: {s.days_worked}   ·   {S['streak']}: {s.current_streak}   ·   {S['avg_day']}: {s.avg_hours_per_worked_day}h   ·   "
            f"{S['forecast']}: {self.analytics.forecast_year_total_hours(self.jy, today)}h"))
        a, b = jalali_year_bounds(self.jy)
        self.heat.set_data(to_tehran(a).date(), (to_tehran(b).date() - to_tehran(a).date()).days, Analytics.heatmap_levels(s.daily))
        self.donut.set_data(s.by_project)
        self.bars.set_values([x / 3600 for x in s.by_month])
        self.entry_model.names = names
        self.refresh_entries(); self.refresh_projects()

    # ---- entries ------------------------------------------------------
    def _build_entries(self) -> None:
        page = QWidget(); page.setStyleSheet(self._field_style()); l = QVBoxLayout(page)
        self.search = QLineEdit(placeholderText=S["search"]); self.search.textChanged.connect(self.refresh_entries)
        c = self.card(); cl = QVBoxLayout(c)
        self.entry_model = EntryModel({}); v = QTableView(); v.setModel(self.entry_model)
        v.setSelectionBehavior(QAbstractItemView.SelectRows); v.setEditTriggers(QAbstractItemView.NoEditTriggers)
        v.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); v.verticalHeader().hide(); v.setShowGrid(False)
        v.setCursor(Qt.PointingHandCursor)
        cl.addWidget(v); l.addWidget(self.search); l.addWidget(c, 1); self.pages.addWidget(page)

    def refresh_entries(self, *_: object) -> None:
        q = self.search.text().strip()
        if q:
            rows = smart_search.run(self.db, q, 500)        # supports tag:/project:/>2h/after: operators + fuzzy text
        else:
            rows = self.db.all(TimeEntry, "start_utc DESC")[:500]
        self.entry_model.set_rows(rows)

    # ---- kanban ---------------------------------------------------------
    def _build_kanban(self) -> None:
        page = QWidget(); page.setStyleSheet(self._field_style()); l = QVBoxLayout(page)
        top = QHBoxLayout(); self.k_title = QLineEdit(placeholderText=S["add_task"]); self.k_title.returnPressed.connect(self.add_kanban_task)
        add = GlassButton(S["add_task"], self.theme, primary=True); add.clicked.connect(self.add_kanban_task)
        top.addWidget(self.k_title, 1); top.addWidget(add); l.addLayout(top)
        cols = QHBoxLayout(); cols.setSpacing(12); self.k_lists = {}
        for c in KANBAN_COLUMNS:
            card = self.card(); cl = QVBoxLayout(card); cl.addWidget(self.label(S[c], 11, True))
            lw = KanbanList(c, self._kanban_moved); self.k_lists[c] = lw; cl.addWidget(lw); cols.addWidget(card, 1)
        l.addLayout(cols, 1); self.pages.addWidget(page)

    @safe
    def add_kanban_task(self, *_: object) -> None:
        t = self.k_title.text().strip()
        if not t:
            raise ValueError(S["need_title"])
        self.undo.save(TimeEntry(title=t, start_utc=now_utc(), status=Status.PLANNED))
        self.k_title.clear(); self.refresh_board()

    def _kanban_moved(self, entry_id: str, column: str) -> None:
        try:
            self.projects_svc.move(entry_id, column)
        except ValueError:
            QMessageBox.information(self, S["app"], S["blocked"])
        except Exception as exc:  # noqa: BLE001
            log.exception("move failed"); QMessageBox.warning(self, S["error"], str(exc))
        self.refresh_board(); self.refresh_all_stats()

    def refresh_board(self) -> None:
        board = self.projects_svc.board()
        for c, lw in self.k_lists.items():
            lw.clear()
            for e in board.get(c, []):
                from PyQt5.QtWidgets import QListWidgetItem
                it = QListWidgetItem(e.title); it.setData(Qt.UserRole, e.id); lw.addItem(it)

    def refresh_all_stats(self) -> None:
        self.refresh_all()

    # ---- billing --------------------------------------------------------
    def _build_billing(self) -> None:
        page = QWidget(); page.setStyleSheet(self._field_style()); l = QVBoxLayout(page)
        c = self.card(); cl = QHBoxLayout(c); cl.setContentsMargins(18, 14, 18, 14)
        self.b_client = QComboBox(); self.b_new = QLineEdit(placeholderText=S["new_client"])
        addc = GlassButton(S["add_client"], self.theme); addc.clicked.connect(self.add_client)
        self.b_tax = QDoubleSpinBox(); self.b_tax.setRange(0, 100); self.b_tax.setPrefix(S["tax"] + " ")
        mk = GlassButton(S["make_invoice"], self.theme, primary=True); mk.clicked.connect(self.make_invoice)
        for w in (self.b_client, self.b_new, addc, self.b_tax, mk):
            cl.addWidget(w)
        self.b_list = QListWidget(); self.b_list.setCursor(Qt.PointingHandCursor)
        row = QHBoxLayout(); pay = GlassButton(S["pay_full"], self.theme); pay.clicked.connect(self.pay_selected)
        html_b = GlassButton(S["save_html"], self.theme); html_b.clicked.connect(self.save_invoice_html)
        row.addWidget(pay); row.addWidget(html_b)
        l.addWidget(c); l.addWidget(self.b_list, 1); l.addLayout(row); self.pages.addWidget(page)

    def refresh_billing(self) -> None:
        cur = self.b_client.currentData()
        self.b_client.clear()
        for c in self.db.all(Client):
            self.b_client.addItem(c.name, c.id)
        if cur:
            self.b_client.setCurrentIndex(max(0, self.b_client.findData(cur)))
        self.b_list.clear()
        names = {c.id: c.name for c in self.db.all(Client)}
        for inv in self.db.all(Invoice, "rowid"):
            it = QListWidgetItem_(to_fa_digits(f"{inv.number} — {names.get(inv.client_id, '?')} — {inv.total:,.0f} {inv.currency} — {inv.status.value} ({inv.balance:,.0f})"), inv.id)
            self.b_list.addItem(it)

    @safe
    def add_client(self, *_: object) -> None:
        n = self.b_new.text().strip()
        if not n:
            raise ValueError(S["need_title"])
        self.db.save(Client(name=n)); self.b_new.clear(); self.refresh_billing()

    @safe
    def make_invoice(self, *_: object) -> None:
        cid = self.b_client.currentData()
        if not cid:
            raise ValueError(S["client"])
        try:
            self.billing.create_invoice(cid, tax_percent=self.b_tax.value())
        except ValueError:
            QMessageBox.information(self, S["app"], S["nothing_invoice"]); return
        self.refresh_billing()

    def _selected_invoice(self) -> Optional[str]:
        it = self.b_list.currentItem()
        return it.data(Qt.UserRole) if it else None

    @safe
    def pay_selected(self, *_: object) -> None:
        iid = self._selected_invoice()
        if iid:
            inv = self.db.get(Invoice, iid)
            if inv and inv.balance > 0:
                self.billing.pay(iid, inv.balance)
            self.refresh_billing()

    @safe
    def save_invoice_html(self, *_: object) -> None:
        iid = self._selected_invoice()
        if iid:
            path, _ = QFileDialog.getSaveFileName(self, S["save_html"], "invoice.html", "HTML (*.html)")
            if path:
                Path(path).write_text(self.billing.to_html(iid), encoding="utf-8")
                QMessageBox.information(self, S["app"], S["saved"])

    # ---- projects -------------------------------------------------------
    def _build_projects(self) -> None:
        page = QWidget(); page.setStyleSheet(self._field_style()); l = QVBoxLayout(page)
        c = self.card(); cl = QHBoxLayout(c); cl.setContentsMargins(18, 14, 18, 14)
        self.p_name = QLineEdit(placeholderText=S["name"])
        self.p_rate = QDoubleSpinBox(); self.p_rate.setRange(0, 1e12); self.p_rate.setPrefix(S["rate"] + " ")
        self.p_est = QSpinBox(); self.p_est.setRange(0, 100000); self.p_est.setPrefix(S["est"] + " ")
        add = GlassButton(S["add_project"], self.theme, primary=True); add.clicked.connect(self.add_project)
        for w in (self.p_name, self.p_rate, self.p_est, add):
            cl.addWidget(w)
        self.p_list = QListWidget(); self.p_list.setCursor(Qt.PointingHandCursor)
        l.addWidget(c); l.addWidget(self.p_list, 1); self.pages.addWidget(page)

    @safe
    def add_project(self, *_: object) -> None:
        name = self.p_name.text().strip()
        if not name:
            raise ValueError(S["need_title"])
        self.db.save(Project(name=name, rate_per_hour=self.p_rate.value(), estimated_hours=float(self.p_est.value()),
                             color=ACCENTS[len(self.db.all(Project)) % 3]))
        self.p_name.clear(); self.refresh_all()

    def refresh_projects(self) -> None:
        self.p_list.clear()
        for p in self.db.all(Project):
            st = self.analytics.project_budget_status(p.id)
            self.p_list.addItem(to_fa_digits(f"{p.icon} {p.name} — {st['hours']}h / {p.estimated_hours or '∞'}h"))

    # ---- settings ---------------------------------------------------------
    def _build_settings(self) -> None:
        inner = QWidget(); inner.setStyleSheet(self._field_style()); l = QVBoxLayout(inner)
        c = self.card(); cl = QVBoxLayout(c); cl.setContentsMargins(24, 18, 24, 18); cl.setSpacing(12)

        def check(text: str, value: bool, handler) -> QCheckBox:
            cb = QCheckBox(text); cb.setChecked(value); cb.setCursor(Qt.PointingHandCursor); cb.toggled.connect(handler); return cb

        def combo(items, current, handler) -> QComboBox:
            cb = QComboBox(); cb.setCursor(Qt.PointingHandCursor)
            for label, data in items:
                cb.addItem(label, data)
            cb.setCurrentIndex(max(0, cb.findData(current)))
            cb.currentIndexChanged.connect(lambda _i, w=cb: handler(w.currentData()))
            return cb

        cl.addWidget(check(S["lite"], self.theme.lite, self._set_lite))
        cl.addWidget(check(S["activity_capture"], bool(self.db.get_setting("activity_capture", False)), self._set_activity))
        cl.addWidget(check(S["ambient"], bool(self.db.get_setting("ambient_mode", False)), self._set_ambient))
        cl.addWidget(check(S["global_hotkey"], bool(self.db.get_setting("global_hotkey", False)), self._set_hotkey))
        cl.addWidget(self.label(S["theme"], 10, muted=True))
        cl.addWidget(combo([(THEME_LABELS[n], n) for n in THEME_NAMES], self.theme.name, self._set_theme))
        cl.addWidget(self.label(S["language"], 10, muted=True))
        cl.addWidget(combo([("فارسی", "fa"), ("English", "en")], self.db.get_setting("lang", "fa"), self._set_lang))
        cl.addWidget(self.label(S["round"], 10, muted=True))
        cl.addWidget(combo([(str(x), x) for x in (0, 5, 15, 30)], self.tracker.settings.round_to_min, self._set_round))
        cl.addWidget(self.label(S["sound"], 10, muted=True))
        cl.addWidget(combo([(S["none"], "none")] + [(k, k) for k in sound.KINDS], "none", self._set_sound))
        actions = ((S["accent"], self._pick_accent), (S["wallpaper"], self._pick_wallpaper), (S["sync_folder"], self._pick_sync_folder),
                   (S["sync_now"], self._sync_now), (S["mini"], self.toggle_mini), (S["focus"], self.toggle_focus),
                   (S["export_json"], lambda: self._export("json")), (S["export_csv"], lambda: self._export("csv")),
                   (S["export_xlsx"], lambda: self._export("xlsx")), (S["backup"], self._backup), (S["ics"], self._export_ics),
                   (S["enc_backup"], self._enc_backup), (S["import_legacy"], self._import_legacy))
        for text, fn in actions:
            b = GlassButton(text, self.theme); b.clicked.connect(lambda _c=False, f=fn: f()); cl.addWidget(b)
        l.addWidget(c); l.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(inner)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}"); inner.setAutoFillBackground(False)
        self.pages.addWidget(scroll)

    def _info(self, key: str) -> None:
        QMessageBox.information(self, S["app"], S[key])

    def _set_theme(self, name: str) -> None:
        self.db.set_setting("theme", name); self._info("restart")

    def _set_lang(self, lang: str) -> None:
        self.db.set_setting("lang", lang); self._info("restart")

    def _pick_accent(self) -> None:
        col = QColorDialog.getColor()
        if col.isValid():
            self.db.set_setting("accent", col.name()); self.theme.custom_accent = col.name()
            for w in self.findChildren(QWidget):
                w.update()

    @safe
    def _pick_wallpaper(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, S["wallpaper"], "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self.db.set_setting("wallpaper", path); self.theme.wallpaper = path; self.bg.reload_wallpaper()

    @safe
    def _set_sound(self, kind: str) -> None:
        if self.sfx:
            self.sfx.stop(); self.sfx = None
        if kind == "none":
            return
        from PyQt5.QtCore import QUrl
        from PyQt5.QtMultimedia import QSoundEffect      # optional module; imported only when the feature is used
        wav = self.data_dir / "sounds" / f"{kind}.wav"
        if not wav.exists():
            wav.parent.mkdir(parents=True, exist_ok=True); sound.write_wav(kind, wav)
        self.sfx = QSoundEffect(self); self.sfx.setSource(QUrl.fromLocalFile(str(wav)))
        self.sfx.setLoopCount(QSoundEffect.Infinite); self.sfx.setVolume(0.35); self.sfx.play()

    def _set_activity(self, on: bool) -> None:
        self.db.set_setting("activity_capture", on)
        if on:
            self.act_timer.start()
        else:
            self.act_timer.stop(); self.act.flush()

    def _set_ambient(self, on: bool) -> None:
        self.db.set_setting("ambient_mode", on)
        (self.ambient_timer.start if on else self.ambient_timer.stop)()

    def _set_hotkey(self, on: bool) -> None:
        self.db.set_setting("global_hotkey", on)
        if self.hotkey:
            self.hotkey.stop(); self.hotkey = None
        if on:
            hk = WindowsHotkey("Ctrl+Shift+Space", self.quick_requested.emit)
            self.hotkey = hk if hk.start() else None     # False on non-Windows: the in-app shortcut still works

    @safe
    def _pick_sync_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, S["pick_folder"])
        if d:
            self.db.set_setting("sync_folder", d); self._info("saved")

    @safe
    def _sync_now(self) -> None:
        folder = self.db.get_setting("sync_folder")
        if not folder:
            self._pick_sync_folder(); folder = self.db.get_setting("sync_folder")
        if folder:
            import platform                     # machine name only; no networking
            folder_sync.sync(self.db, folder, platform.node() or "device"); self.refresh_all(); self._info("sync_done")

    def _set_lite(self, v: bool) -> None:
        self.theme.lite = v; self.db.set_setting("lite", v)
        (self.bg.stop if v else self.bg.start)()

    def _set_round(self, v: int) -> None:
        self.tracker.settings.round_to_min = int(v); self.db.set_setting("round", int(v))

    @safe
    def _export(self, kind: str) -> None:
        path, _ = QFileDialog.getSaveFileName(self, S["export_" + kind], f"worktracker.{kind}")
        if path:
            {"json": exporter.export_json, "csv": exporter.export_csv, "xlsx": exporter.export_xlsx}[kind](self.db, path)
            QMessageBox.information(self, S["app"], S["saved"])

    @safe
    def _export_ics(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, S["ics"], "worktracker.ics")
        if path:
            ical.export_ics(self.db.all(TimeEntry, "start_utc"), path); QMessageBox.information(self, S["app"], S["saved"])

    @safe
    def _enc_backup(self) -> None:
        pw, ok = QInputDialog.getText(self, S["password"], S["password"], QLineEdit.Password)
        if ok and pw:
            security.encrypted_backup(self.db, self.data_dir / "backups" / "backup.wtbackup", pw)
            QMessageBox.information(self, S["app"], S["saved"])

    @safe
    def _backup(self) -> None:
        self.db.rotate_backups(self.data_dir / "backups"); QMessageBox.information(self, S["app"], S["saved"])

    @safe
    def _import_legacy(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, S["import_legacy"], "", "SQLite (*.db *.sqlite);;All (*)")
        if path:
            st = import_legacy(self.db, path, backup_dir=self.data_dir / "backups")
            self.refresh_all(); QMessageBox.information(self, S["app"], f"{st}")

    # ---- palette ----------------------------------------------------------
    def open_palette(self) -> None:
        acts = {S[k]: (lambda n=i: self.goto(n)) for i, k in enumerate(PAGES)}
        acts[S["undo"]] = self.undo.undo; acts[S["redo"]] = self.undo.redo
        acts[S["start"] + " / " + S["stop"]] = self.toggle_timer
        acts[S["backup"]] = self._backup; acts[S["quick"]] = lambda: px.quick_capture(self)
        acts[S["ambient"]] = self.show_ambient; acts[S["detach"]] = self.detach_current; acts[S["focus"]] = self.toggle_focus; acts[S["mini"]] = self.toggle_mini; acts[S["year_review"]] = lambda: px.show_year_review(self)
        CommandPalette(acts, self).exec_()
