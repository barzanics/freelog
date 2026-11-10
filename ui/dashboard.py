"""Dashboard widgets: hero stats, timer card with live parallel-timer pills + one-click recent tasks, Pomodoro water-orb, heatmap/donut/bars."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from ..core.models import Project, TimeEntry
from ..core.persian import format_duration, format_jalali, jalali_year_bounds, now_utc, to_fa_digits, to_tehran
from ..services.analytics import Analytics
from . import icons
from .forms import FlowLayout, chip_button
from .glass import BarChart, Donut, GlassButton, Heatmap, PomodoroOrb
from .strings import MONTHS_SHORT, S


def _header(win, icon_name: str, title: str, right: Optional[QWidget] = None) -> QHBoxLayout:
    row = QHBoxLayout(); row.setSpacing(8)
    ic = QLabel(); ic.setPixmap(icons.pixmap(icon_name, win.theme.accents[1], 22)); row.addWidget(ic)
    row.addWidget(win.label(title, 11, True), 1)
    if right is not None:
        row.addWidget(right)
    return row


def _tile(win, caption: str) -> tuple:
    f = QFrame(); f.setProperty("card", True)
    v = QVBoxLayout(f); v.setContentsMargins(14, 10, 14, 10); v.setSpacing(2)
    val = win.label("—", 15, True); cap = win.label(caption, 9, muted=True)
    v.addWidget(val); v.addWidget(cap)
    return f, val


def build_dashboard(win) -> None:
    page = QWidget(); g = QGridLayout(page); g.setSpacing(14); g.setContentsMargins(4, 4, 4, 4)

    # ---------------------------------------------------------------- hero
    hero = win.card(); hl = QVBoxLayout(hero); hl.setContentsMargins(22, 16, 22, 16); hl.setSpacing(8)
    hl.addLayout(_header(win, "analytics", S["hours_year"]))
    win.hero_hours = win.label("۰", 40, True); hl.addWidget(win.hero_hours)
    tiles = QWidget(); tf = FlowLayout(tiles, 8)
    win.tiles = {}
    for key, cap in (("days", S["days_worked"]), ("streak", S["streak"]), ("avg", S["avg_day"]), ("forecast", S["forecast"])):
        frame, val = _tile(win, cap); win.tiles[key] = val; tf.addWidget(frame)
    hl.addWidget(tiles)

    # ---------------------------------------------------------------- timer
    tc = win.card(); tl = QVBoxLayout(tc); tl.setContentsMargins(20, 16, 20, 16); tl.setSpacing(10)
    tl.addLayout(_header(win, "clock", S["timer"]))
    win.timer_lbl = win.label("0:00:00", 30, True); tl.addWidget(win.timer_lbl)
    win.t_title = QLineEdit(placeholderText=S["what"]); win.t_title.returnPressed.connect(win.toggle_timer); tl.addWidget(win.t_title)
    row = QHBoxLayout(); row.setSpacing(8)
    win.t_proj = QComboBox(); win.t_proj.setCursor(Qt.PointingHandCursor)
    win.t_energy = QComboBox(); win.t_energy.addItem(S["energy"], 0)
    for lv in range(1, 6):
        win.t_energy.addItem(to_fa_digits(str(lv)), lv)
    win.t_energy.setCursor(Qt.PointingHandCursor); win.t_energy.setMaximumWidth(120)
    row.addWidget(win.t_proj, 1); row.addWidget(win.t_energy); tl.addLayout(row)
    brow = QHBoxLayout(); brow.setSpacing(8)
    win.t_btn = GlassButton(S["start"], win.theme, primary=True, icon="play"); win.t_btn.clicked.connect(win.toggle_timer)
    win.t_par = GlassButton(S["parallel"], win.theme, icon="plus"); win.t_par.clicked.connect(win.start_parallel)
    brow.addWidget(win.t_btn, 1); brow.addWidget(win.t_par); tl.addLayout(brow)
    win.pill_host = QWidget(); win.pill_lay = QVBoxLayout(win.pill_host); win.pill_lay.setContentsMargins(0, 0, 0, 0); win.pill_lay.setSpacing(6); tl.addWidget(win.pill_host)
    win._pill_ids, win._pill_labels = [], {}
    tl.addWidget(win.label(S["recent_tasks"], 9, muted=True))
    rec = QWidget(); win.recent_flow = FlowLayout(rec, 6); tl.addWidget(rec)

    # ---------------------------------------------------------------- pomodoro
    pc = win.card(); pl = QHBoxLayout(pc); pl.setContentsMargins(18, 14, 18, 14); pl.setSpacing(14)
    win.orb = PomodoroOrb(win.theme); pl.addWidget(win.orb, 1)
    col = QVBoxLayout(); col.setSpacing(8); col.addLayout(_header(win, "clock", S["pomo"]))
    win.pomo_btn = GlassButton(S["pomo_start"], win.theme, primary=True, icon="play"); win.pomo_btn.clicked.connect(win.pomo_toggle)
    win.pomo_reset = GlassButton(S["pomo_reset"], win.theme, icon="refresh"); win.pomo_reset.clicked.connect(win.pomo_do_reset)
    col.addWidget(win.pomo_btn); col.addWidget(win.pomo_reset); col.addStretch(); pl.addLayout(col)

    # ---------------------------------------------------------------- charts
    hm = win.card(); ml = QVBoxLayout(hm); ml.setContentsMargins(16, 12, 16, 12); ml.addLayout(_header(win, "calendar", S["heatmap"]))
    win.heat = Heatmap(win.theme); ml.addWidget(win.heat)
    dc = win.card(); dl = QVBoxLayout(dc); dl.setContentsMargins(16, 12, 16, 12); dl.addLayout(_header(win, "projects", S["by_project"]))
    win.donut = Donut(win.theme); dl.addWidget(win.donut)
    bc = win.card(); bl = QVBoxLayout(bc); bl.setContentsMargins(16, 12, 16, 12); bl.addLayout(_header(win, "analytics", S["by_month"]))
    win.bars = BarChart(win.theme, MONTHS_SHORT); bl.addWidget(win.bars)

    for card, h in ((hero, 200), (tc, 360), (pc, 290), (hm, 250), (dc, 290), (bc, 260)):
        card.setMinimumHeight(h)
    win.heat.setMinimumHeight(170); win.donut.setMinimumHeight(190); win.bars.setMinimumHeight(150); win.orb.setMinimumSize(200, 200)
    win.dash_grid = g
    win.dash_cards = {"hero": (hero, 1), "timer": (tc, 1), "pomodoro": (pc, 1), "heatmap": (hm, 2), "donut": (dc, 1), "bars": (bc, 1)}
    win.pages.addWidget(page)
    win._pomo_tick()


def refresh_dashboard(win) -> None:
    db = win.db
    names: Dict[str, str] = {p.id: p.name for p in db.all(Project)}
    cur = win.t_proj.currentData()
    win.t_proj.blockSignals(True); win.t_proj.clear(); win.t_proj.addItem(S["no_project"], None)
    for pid, n in names.items():
        win.t_proj.addItem(n, pid)
    win.t_proj.setCurrentIndex(max(0, win.t_proj.findData(cur))); win.t_proj.blockSignals(False)
    today = to_tehran(now_utc()).date()
    s = win.analytics.year_summary(win.jy, today)
    win.hero_hours.setText(to_fa_digits(f"{s.total_hours:.1f}"))
    win.tiles["days"].setText(to_fa_digits(str(s.days_worked))); win.tiles["streak"].setText(to_fa_digits(str(s.current_streak)))
    win.tiles["avg"].setText(to_fa_digits(f"{s.avg_hours_per_worked_day}h")); win.tiles["forecast"].setText(to_fa_digits(f"{win.analytics.forecast_year_total_hours(win.jy, today)}h"))
    a, b = jalali_year_bounds(win.jy)
    win.heat.set_data(to_tehran(a).date(), (to_tehran(b).date() - to_tehran(a).date()).days, Analytics.heatmap_levels(s.daily))
    win.donut.set_data(s.by_project)
    win.bars.set_values([x / 3600 for x in s.by_month])
    win.entry_model.names = names
    _refresh_recent(win)
    update_running(win)


def _refresh_recent(win) -> None:
    while win.recent_flow.count():
        it = win.recent_flow.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    seen: List[str] = []
    rows = win.db.conn.execute("SELECT title, project_id, category FROM entries WHERE source!='auto' ORDER BY start_utc DESC LIMIT 60").fetchall()
    for r in rows:
        if r[0] in seen:
            continue
        seen.append(r[0])
        b = chip_button("▶  " + (r[0] if len(r[0]) <= 26 else r[0][:25] + "…"))
        b.setToolTip(r[0]); b.clicked.connect(lambda _c=False, t=r[0], p=r[1], c=r[2]: win.quick_start(t, p, c)); win.recent_flow.addWidget(b)
        if len(seen) >= 6:
            break


def update_running(win) -> None:
    """Keep the live pills in sync: rebuild only when the set of running timers changed, otherwise just refresh the clocks (cheap, once a second)."""
    running = win.tracker.running()
    ids = [r.id for r in running]
    if hasattr(win, "bubble"):
        win.bubble.set_running(len(running), max(0, int((now_utc() - running[-1].start_utc).total_seconds())) if running else 0)
    if ids != win._pill_ids:
        while win.pill_lay.count():
            it = win.pill_lay.takeAt(0)
            if it is not None and it.widget() is not None:
                it.widget().deleteLater()
        win._pill_labels = {}
        for r in running:
            f = QFrame(); f.setProperty("card", True)
            h = QHBoxLayout(f); h.setContentsMargins(12, 6, 8, 6); h.setSpacing(8)
            dot = QLabel("●"); dot.setStyleSheet(f"color:{win.theme.accents[2]};background:transparent;"); h.addWidget(dot)
            title = win.label(r.title if len(r.title) <= 30 else r.title[:29] + "…", 10, True); h.addWidget(title, 1)
            t = win.label("0:00", 10, True); h.addWidget(t)
            stop = GlassButton("", win.theme, danger=True, icon="stop"); stop.setFixedSize(36, 36); stop.clicked.connect(lambda _c=False, i=r.id: win.stop_timer(i)); h.addWidget(stop)
            win.pill_lay.addWidget(f); win._pill_labels[r.id] = t
        win._pill_ids = ids
        win.t_btn.setText(S["stop_all"] if len(ids) > 1 else (S["stop"] if ids else S["start"]))
        win.t_btn.icon_name = "stop" if ids else "play"; win.t_btn.update()
    now = now_utc()
    for r in running:
        lab = win._pill_labels.get(r.id)
        if lab is not None:
            sec = max(0, int((now - r.start_utc).total_seconds()))
            lab.setText(to_fa_digits(f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"))
