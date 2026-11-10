"""Operational pages: full Reports builder, hourly Screenshots gallery, sectioned Settings, and the tip-of-the-hour widgets."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                             QScrollArea, QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from ..core import taxonomy
from ..core.models import Project, Screenshot
from ..core.persian import MONTHS_FA, format_jalali, now_utc, to_fa_digits, to_tehran, tr
from ..services import report_builder as rb
from ..services.autotrack import DEFAULT_WORK, AutoConfig
from ..services.prompter import PromptConfig
from ..services.reminders import DEFAULTS as REMINDER_DEFAULTS, Reminders
from ..services.screenshots import ScreenshotStore
from ..services.tips import CATEGORIES as TIP_CATS, Tips
from . import icons
from .dialogs import PopDialog, confirm
from .forms import ChipInput, ColorSwatches, FlowLayout, JalaliDateEdit, Section, Segmented, chip_button
from .glass import BarChart, Donut, GlassButton, LiquidSwitch
from .strings import S

log = logging.getLogger("worktracker.ops")
_SECTION_FA = {"summary": "خلاصه و مقایسه", "by_project": "پروژه‌ها", "by_category": "دسته‌ها", "by_subcategory": "زیردسته‌ها", "by_tag": "برچسب‌ها", "by_client": "مشتریان",
                  "by_day": "هر روز", "by_weekday": "روزهای هفته", "by_hour": "ساعت‌های روز", "by_month": "ماه‌ها", "top_tasks": "پرزمان‌ترین کارها",
                  "estimates": "تخمین/واقعی", "billing": "صورتحساب", "apps": "برنامه‌ها", "habits": "عادت‌ها", "goals": "اهداف", "health": "سلامت پروژه‌ها",
                  "compliance": "پایبندی به ثبت کار", "screenshots": "اسکرین‌شات‌ها", "entries": "فهرست کامل"}
_KIND_FA = {"daily": "روزانه", "weekly": "هفتگی", "monthly": "ماهانه", "yearly": "سالانه", "custom": "دلخواه", "summary": "خلاصه", "detailed": "تفصیلی", "company": "برگه‌ی ساعت"}


_SECTION_EN = {"summary": "Summary & comparison", "by_project": "Projects", "by_category": "Categories", "by_subcategory": "Sub-categories", "by_tag": "Tags", "by_client": "Clients",
               "by_day": "Each day", "by_weekday": "Weekdays", "by_hour": "Hours of the day", "by_month": "Months", "top_tasks": "Most time-consuming tasks",
               "estimates": "Estimate vs actual", "billing": "Billing", "apps": "Applications", "habits": "Habits", "goals": "Goals", "health": "Project health",
               "compliance": "Work-report compliance", "screenshots": "Screenshots", "entries": "Full list"}
_KIND_EN = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly", "yearly": "Yearly", "custom": "Custom", "summary": "Summary", "detailed": "Detailed", "company": "Timesheet"}


class _Labels(dict):
    """dict-like view that resolves the label in the active language at access time."""

    def __init__(self, fa, en):
        super().__init__(); self._fa, self._en = fa, en

    def __getitem__(self, k):
        return (self._fa if tr("fa", "en") == "fa" else self._en)[k]


SECTION_LABELS = _Labels(_SECTION_FA, _SECTION_EN)
KIND_LABELS = _Labels(_KIND_FA, _KIND_EN)


def _page(win):
    w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12); return w, lay


def _scroll(widget: QWidget) -> QScrollArea:
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(widget); sa.setFrameShape(QFrame.NoFrame); return sa


# ===================================================================== TIPS
def tip_now(win, offset: int = 0) -> Dict[str, str]:
    return Tips(win.db).for_time(to_tehran(now_utc()).replace(tzinfo=None), offset)


class TipDialog(PopDialog):
    def __init__(self, win) -> None:
        super().__init__(win, S["tip_title"], "lightbulb", 560)
        self.offset = 0
        self.cat = QLabel(); self.cat.setStyleSheet("color:#00E5FF;font-weight:700;background:transparent;")
        self.text = QLabel(); self.text.setWordWrap(True); self.text.setStyleSheet("font-size:13pt;background:transparent;"); self.text.setMinimumHeight(110)
        self.body.addWidget(self.cat); self.body.addWidget(self.text)
        nxt = GlassButton(S["next_tip"], self.theme, primary=True, icon="refresh"); nxt.clicked.connect(self._next)
        self.fav = GlassButton(S["favorite"], self.theme, icon="star"); self.fav.clicked.connect(self._fav)
        self.buttons(self.fav, nxt)
        self._show()

    def _show(self) -> None:
        t = tip_now(self.win, self.offset)
        self.cur = t; self.cat.setText(TIP_CATS.get(t["cat"], t["cat"])); self.text.setText(t["text"])
        self.fav.setText(S["unfavorite"] if t["text"] in Tips(self.db).favorites() else S["favorite"])

    def _next(self) -> None:
        self.offset += 1; self._show()
        if self.theme.fx is not None:
            self.theme.fx.play("bloop")

    def _fav(self) -> None:
        tips = Tips(self.db); tips.favorite(self.cur["text"], self.cur["text"] not in tips.favorites()); self._show()


def build_tip_card(win) -> QWidget:
    c = win.card(); v = QVBoxLayout(c); v.setContentsMargins(18, 14, 18, 14); v.setSpacing(6)
    head = QHBoxLayout(); ic = QLabel(); ic.setPixmap(icons.pixmap("lightbulb", "#FFB020", 22)); head.addWidget(ic); win.tip_cat = win.label("", 10, True); head.addWidget(win.tip_cat, 1)
    nb = GlassButton("", win.theme, icon="refresh"); nb.setFixedSize(38, 36); nb.clicked.connect(lambda: _tip_next(win)); head.addWidget(nb); v.addLayout(head)
    win.tip_text = win.label("", 11); win.tip_text.setWordWrap(True); v.addWidget(win.tip_text, 1)
    win.tip_offset = 0
    c.setMinimumHeight(150)
    refresh_tip(win)
    return c


def _tip_next(win) -> None:
    win.tip_offset += 1; refresh_tip(win)
    if win.theme.fx is not None:
        win.theme.fx.play("bloop")


def refresh_tip(win) -> None:
    if not Tips(win.db).db.get_setting("tips_enabled", True):
        win.tip_cat.setText(""); win.tip_text.setText(S["tips_off"]); return
    t = tip_now(win, getattr(win, "tip_offset", 0))
    win.tip_cat.setText(TIP_CATS.get(t["cat"], t["cat"])); win.tip_text.setText(t["text"])
    if hasattr(win, "tip_btn"):
        txt = t["text"]
        win.tip_btn.setText(("  " + txt[:70] + ("…" if len(txt) > 70 else "")))
        win.tip_btn.setToolTip(txt)


# ===================================================================== REPORTS
def build_reports(win) -> None:
    page, lay = _page(win)
    top = QHBoxLayout(); top.addWidget(win.label(S["reports"], 17, True), 1)
    gen = GlassButton(S["generate"], win.theme, primary=True, icon="refresh"); gen.clicked.connect(lambda: refresh_reports(win)); top.addWidget(gen); lay.addLayout(top)
    body = QHBoxLayout(); body.setSpacing(12)
    # ---- options
    opt = QWidget(); ol = QVBoxLayout(opt); ol.setContentsMargins(0, 0, 8, 0); ol.setSpacing(10)
    win.rp_kind = Segmented([(KIND_LABELS[k], k) for k in rb.KINDS]); win.rp_kind.changed.connect(lambda k: _rp_preset(win, k))
    win.rp_from, win.rp_to = JalaliDateEdit(), JalaliDateEdit()
    s1 = Section(S["rp_period"]); s1.add(S["rp_type"], win.rp_kind); s1.pair(S["rp_from"], win.rp_from, S["rp_to"], win.rp_to)
    win.rp_sections = QListWidget(); win.rp_sections.setMinimumHeight(230)
    for k in rb.ALL_SECTIONS:
        it = QListWidgetItem(SECTION_LABELS[k]); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, k); win.rp_sections.addItem(it)
    s2 = Section(S["rp_sections"]); s2.add("", win.rp_sections)
    win.rp_projects = QListWidget(); win.rp_projects.setMinimumHeight(110)
    win.rp_tags = ChipInput(); win.rp_billable = Segmented([(S["any"], None), (S["billable_only"], True), (S["non_billable"], False)], wrap=False)
    win.rp_min = QSpinBox(); win.rp_min.setRange(0, 600); win.rp_min.setSuffix(" " + S["min"])
    win.rp_notes, win.rp_digits, win.rp_prev = LiquidSwitch(win.theme, True), LiquidSwitch(win.theme, True), LiquidSwitch(win.theme, True)
    s3 = Section(S["rp_filters"]); s3.add(S["projects"], win.rp_projects); s3.add(S["tags"], win.rp_tags); s3.add(S["billable"], win.rp_billable); s3.add(S["rp_min"], win.rp_min)
    for lab, sw in ((S["rp_notes"], win.rp_notes), (S["rp_digits"], win.rp_digits), (S["rp_compare"], win.rp_prev)):
        r = QWidget(); rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(sw); rl.addWidget(QLabel(lab)); rl.addStretch(); s3.add("", r)
    for s in (s1, s2, s3):
        ol.addWidget(s)
    ol.addStretch(); osa = _scroll(opt); osa.setMinimumWidth(380); osa.setMaximumWidth(460); body.addWidget(osa)
    # ---- preview
    pv = win.card(); pl = QVBoxLayout(pv); pl.setContentsMargins(16, 14, 16, 14)
    win.rp_summary = win.label("", 11); win.rp_summary.setWordWrap(True); win.rp_summary.setTextFormat(Qt.RichText); pl.addWidget(win.rp_summary)
    win.rp_bars = BarChart(win.theme, [str(i) for i in range(1, 32)]); pl.addWidget(win.rp_bars)
    win.rp_donut = Donut(win.theme); pl.addWidget(win.rp_donut)
    win.rp_note = win.label("", 9, muted=True); win.rp_note.setWordWrap(True); pl.addWidget(win.rp_note)
    pl.addStretch(1)
    row = QHBoxLayout()
    for label, fmt, ic in ((S["open_in_browser"], "browser", "reports"), ("HTML", "html", "download"), ("Markdown", "md", "download"), ("CSV", "csv", "download"), ("Excel", "xlsx", "download"), ("JSON", "json", "download")):
        b = GlassButton(label, win.theme, primary=(fmt == "browser"), icon=ic); b.clicked.connect(lambda _c=False, f=fmt: _rp_export(win, f)); row.addWidget(b)
    pl.addLayout(row); body.addWidget(pv, 1); lay.addLayout(body, 1)
    win.rp_data = None
    win.pages.addWidget(page)
    _rp_preset(win, "monthly")


def _rp_preset(win, kind: str) -> None:
    spec = rb.ReportSpec.preset(kind, to_tehran(now_utc()).date())
    win.rp_from.setDate(spec.start); win.rp_to.setDate(spec.end)
    for i in range(win.rp_sections.count()):
        it = win.rp_sections.item(i); it.setCheckState(Qt.Checked if it.data(Qt.UserRole) in spec.sections else Qt.Unchecked)
    win.rp_title = spec.title


def _rp_spec(win) -> rb.ReportSpec:
    kind = win.rp_kind.value()
    a, b = win.rp_from.date(), win.rp_to.date()
    if a is None or b is None:
        raise ValueError(S["bad_date"])
    spec = rb.ReportSpec.preset(kind, a)
    spec.start, spec.end = a, b
    spec.sections = {win.rp_sections.item(i).data(Qt.UserRole) for i in range(win.rp_sections.count()) if win.rp_sections.item(i).checkState() == Qt.Checked}
    spec.projects = [win.rp_projects.item(i).data(Qt.UserRole) for i in range(win.rp_projects.count()) if win.rp_projects.item(i).checkState() == Qt.Checked]
    spec.tags, spec.billable, spec.min_minutes = win.rp_tags.tags(), win.rp_billable.value(), win.rp_min.value()
    spec.include_notes, spec.persian_digits, spec.compare_previous = win.rp_notes.isChecked(), win.rp_digits.isChecked(), win.rp_prev.isChecked()
    return spec


def refresh_reports(win) -> None:
    if win.rp_projects.count() != len(win.db.all(Project)):
        win.rp_projects.clear()
        for p in win.db.all(Project, "name"):
            it = QListWidgetItem(f"{p.icon} {p.name}"); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, p.id); win.rp_projects.addItem(it)
    try:
        spec = _rp_spec(win)
        data = rb.build(win.db, spec)
    except ValueError as exc:
        win.toast(str(exc)); return
    win.rp_data = data
    s = data["summary"]; prev = data.get("previous") or {}
    chg = "" if prev.get("change_pct") is None else f" ({'▲' if prev['change_pct'] >= 0 else '▼'} {abs(prev['change_pct'])}٪)"
    win.rp_summary.setText(to_fa_digits(
        f"<b style='font-size:15pt'>{data['title']}</b><br>"
        f"⏱ <b>{rb.format_duration(s['total_sec'])}</b> ساعت{chg} &nbsp;·&nbsp; 📅 {s['days_worked']} روز کاری &nbsp;·&nbsp; 📈 میانگین {rb.format_duration(s['avg_per_worked_day_sec'])}"
        f" &nbsp;·&nbsp; 💰 {s['billable_pct']}٪ قابل صورتحساب &nbsp;·&nbsp; 🏆 امتیاز {data['productivity_score']}"))
    days = data["by_day"]
    win.rp_bars.labels = [d[-2:] for d, _ in days][:62] or ["—"]; win.rp_bars.set_values([v / 3600 for _, v in days][:62] or [0])
    win.rp_donut.set_data({n: int(v) for n, v in data["by_project"]})
    win.rp_note.setText(to_fa_digits(f"{len(data['entries'])} ثبت · {data['start']} → {data['end']}"))


def _rp_export(win, fmt: str) -> None:
    try:
        if win.rp_data is None:
            refresh_reports(win)
        data = win.rp_data
        if data is None:
            return
        fa = win.rp_digits.isChecked()
        if fmt == "browser":
            folder = win.data_dir / "reports"; folder.mkdir(parents=True, exist_ok=True)
            f = folder / f"report-{now_utc():%Y%m%d-%H%M%S}.html"; rb.save(data, f, "html", fa)
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(f))); return
        path, _ = QFileDialog.getSaveFileName(win, S["reports"], f"report.{fmt}")
        if path:
            rb.save(data, path, fmt, fa); win.toast(S["saved"])
    except Exception as exc:  # noqa: BLE001 - UI boundary
        log.exception("report export failed"); QMessageBox.warning(win, S["error"], str(exc))


# ===================================================================== SCREENSHOTS
class ShotViewer(PopDialog):
    def __init__(self, win, store: ScreenshotStore, shot: Screenshot) -> None:
        super().__init__(win, to_fa_digits(to_tehran(shot.at).strftime("%H:%M:%S")) + "  " + shot.app, "camera", 980)
        self.store, self.shot, self.deleted = store, shot, False
        from PyQt5.QtGui import QPixmap
        pm = QPixmap(); pm.loadFromData(store.read(shot))
        lab = QLabel(); lab.setAlignment(Qt.AlignCenter)
        lab.setPixmap(pm.scaledToWidth(min(900, max(400, win.width() - 140)), Qt.SmoothTransformation) if not pm.isNull() else QPixmap())
        self.body.addWidget(lab); self.body.addWidget(win.label(shot.title or "", 9, muted=True))
        dl = GlassButton(S["delete"], self.theme, danger=True, icon="trash"); dl.clicked.connect(self._del)
        sv = GlassButton(S["save_as"], self.theme, icon="download"); sv.clicked.connect(self._save)
        self.buttons(dl, sv)

    def _del(self) -> None:
        if confirm(self, S["confirm_delete"]):
            self.store.delete(self.shot.id); self.deleted = True; self.accept()

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, S["save_as"], "screenshot.jpg", "JPEG (*.jpg)")
        if path:
            Path(path).write_bytes(self.store.read(self.shot))


def build_screenshots(win) -> None:
    page, lay = _page(win)
    top = QHBoxLayout(); top.addWidget(win.label(S["screenshots"], 17, True), 1)
    now_b = GlassButton(S["capture_now"], win.theme, primary=True, icon="camera"); now_b.clicked.connect(lambda: _shot_now(win)); top.addWidget(now_b); lay.addLayout(top)
    bar = QHBoxLayout()
    from .pages_new import arrow_icon
    prv = GlassButton("", win.theme, icon=arrow_icon(win, False)); prv.setFixedSize(40, 40); prv.clicked.connect(lambda: _shot_shift(win, -1))
    nxt = GlassButton("", win.theme, icon=arrow_icon(win, True)); nxt.setFixedSize(40, 40); nxt.clicked.connect(lambda: _shot_shift(win, 1))
    win.sh_day = JalaliDateEdit(); win.sh_day.setDate(to_tehran(now_utc()).date()); win.sh_day.changed.connect(lambda: refresh_screenshots(win))
    win.sh_info = win.label("", 9, muted=True)
    exp = GlassButton(S["export_day_zip"], win.theme, icon="download"); exp.clicked.connect(lambda: _shot_export(win))
    cl = GlassButton(S["cleanup_now"], win.theme, icon="trash"); cl.clicked.connect(lambda: _shot_cleanup(win))
    for w in (prv, win.sh_day, nxt):
        bar.addWidget(w)
    bar.addWidget(win.sh_info, 1); bar.addWidget(exp); bar.addWidget(cl); lay.addLayout(bar)
    win.sh_host = QWidget(); win.sh_lay = QVBoxLayout(win.sh_host); win.sh_lay.setSpacing(10); win.sh_lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(_scroll(win.sh_host), 1); win.pages.addWidget(page)


def _store(win) -> ScreenshotStore:
    return win.runtime.shots


def _shot_now(win) -> None:
    s = win.runtime.capture_now()
    win.toast(S["saved"] if s else S.get("cap_" + win.runtime.last_capture_reason, S["capture_failed"])); refresh_screenshots(win)


def _shot_shift(win, d: int) -> None:
    cur = win.sh_day.date() or to_tehran(now_utc()).date()
    win.sh_day.setDate(cur + dt.timedelta(days=d))


def _shot_export(win) -> None:
    day = win.sh_day.date()
    if day is None:
        return
    path, _ = QFileDialog.getSaveFileName(win, S["export_day_zip"], f"screens-{day}.zip")
    if path:
        try:
            _store(win).export_day_zip(day, path); win.toast(S["saved"])
        except FileNotFoundError:
            win.toast(S["no_shots"])


def _shot_cleanup(win) -> None:
    n = _store(win).cleanup(int(win.db.get_setting("shots_keep_days", 30)), int(win.db.get_setting("shots_max_mb", 500)))
    win.toast(to_fa_digits(f"{n} {S['days_removed']}")); refresh_screenshots(win)


def refresh_screenshots(win) -> None:
    from PyQt5.QtCore import QSize
    from PyQt5.QtGui import QIcon, QPixmap
    store = _store(win)
    while win.sh_lay.count():
        it = win.sh_lay.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    day = win.sh_day.date() or to_tehran(now_utc()).date()
    shots = store.for_day(day)
    mb = store.total_bytes() / 1048576
    win.sh_info.setText(to_fa_digits(f"{len(shots)} {S['shots_today']}  ·  {mb:.1f} MB {S['total_used']}"))
    from ..core.models import HourLog
    logs = {to_tehran(h.hour_start).hour: h for h in (HourLog.from_row(r) for r in win.db.conn.execute("SELECT * FROM hour_log"))
            if to_tehran(h.hour_start).date() == day}
    by_hour: Dict[int, List[Screenshot]] = {}
    for s in shots:
        by_hour.setdefault(to_tehran(s.at).hour, []).append(s)
    hours = sorted(set(by_hour) | set(logs))
    if not hours:
        l = win.label(S["no_shots"], 12, muted=True); l.setAlignment(Qt.AlignCenter); win.sh_lay.addWidget(l); return
    for h in hours:
        c = win.card(); row = QHBoxLayout(c); row.setContentsMargins(14, 10, 14, 10)
        row.addWidget(win.label(to_fa_digits(f"{h:02d}:00"), 14, True))
        for s in by_hour.get(h, []):
            b = QPushButton(); b.setCursor(Qt.PointingHandCursor); b.setProperty("ghost", True)
            pm = QPixmap(); pm.loadFromData(store.read(s))
            if not pm.isNull():
                b.setIcon(QIcon(pm.scaledToWidth(220, Qt.SmoothTransformation))); b.setIconSize(QSize(220, 124)); b.setFixedSize(232, 136)
            b.setToolTip(to_fa_digits(f"{to_tehran(s.at):%H:%M}  {s.app}  {s.title}"))
            b.clicked.connect(lambda _c=False, ss=s: _open_shot(win, ss)); row.addWidget(b)
        info = QVBoxLayout(); lg = logs.get(h)
        info.addWidget(win.label(lg.summary if lg else "", 10)); 
        if lg:
            info.addWidget(win.label(to_fa_digits(f"{S['engaged']}: {lg.engaged_sec // 60} {S['min']}  ·  {S['idle']}: {lg.idle_sec // 60} {S['min']}"), 9, muted=True))
        done = [e for e in _entries_in_hour(win, day, h)]
        for e in done[:4]:
            info.addWidget(win.label("• " + e, 9, muted=True))
        info.addStretch(); row.addLayout(info, 1); win.sh_lay.addWidget(c)
    win.sh_lay.addStretch()


def _entries_in_hour(win, day: dt.date, hour: int) -> List[str]:
    tz = to_tehran(now_utc()).tzinfo
    lo = dt.datetime.combine(day, dt.time(hour), tzinfo=tz); hi = lo + dt.timedelta(hours=1)
    from ..core.models import TimeEntry
    return [e.title for e in win.db.entries_between(lo - dt.timedelta(hours=6), hi) if e.end_utc and e.start_utc < hi and e.end_utc > lo]


def _open_shot(win, s: Screenshot) -> None:
    dlg = ShotViewer(win, _store(win), s)
    dlg.exec_()
    if dlg.deleted:
        refresh_screenshots(win)


# ===================================================================== SETTINGS
def _save(win, key: str, value: Any) -> None:
    win.db.set_setting(key, value)
    rt = getattr(win, "runtime", None)
    if rt is not None:
        rt.reload()
    win.on_setting_changed(key, value)


def _bind(win, key: str, w: QWidget, default: Any) -> QWidget:
    v = win.db.get_setting(key, default)
    sv = lambda x: _save(win, key, x)
    if isinstance(w, LiquidSwitch):
        w.setChecked(bool(v)); w.toggled.connect(sv)
    elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
        w.setValue(v); w.valueChanged.connect(sv)
    elif isinstance(w, QSlider):
        w.setValue(int(v)); w.valueChanged.connect(sv)
    elif isinstance(w, QComboBox):
        w.setCurrentIndex(max(0, w.findData(v))); w.currentIndexChanged.connect(lambda _i: sv(w.currentData()))
    elif isinstance(w, QLineEdit):
        w.setText(str(v or "")); w.editingFinished.connect(lambda: sv(w.text().strip()))
    elif isinstance(w, ChipInput):
        w.setTags(v or []); w.changed.connect(lambda: sv(w.tags()))
    return w


def _bind_dict(win, key: str, field: str, w: QWidget, default_cfg: dict, conv_in: Callable = lambda v: v, conv_out: Callable = lambda v: v) -> QWidget:
    cfg = {**default_cfg, **win.db.get_setting(key, {})}
    def sv(x) -> None:
        c = {**default_cfg, **win.db.get_setting(key, {})}; c[field] = conv_out(x); _save(win, key, c)
    v = conv_in(cfg.get(field))
    if isinstance(w, LiquidSwitch):
        w.setChecked(bool(v)); w.toggled.connect(sv)
    elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
        w.setValue(v); w.valueChanged.connect(sv)
    elif isinstance(w, QComboBox):
        w.setCurrentIndex(max(0, w.findData(v))); w.currentIndexChanged.connect(lambda _i: sv(w.currentData()))
    elif isinstance(w, ChipInput):
        w.setTags(v or []); w.changed.connect(lambda: sv(w.tags()))
    return w


def _sw(win, key: str, default: bool = False) -> LiquidSwitch:
    return _bind(win, key, LiquidSwitch(win.theme), default)  # type: ignore[return-value]


def _spin(win, key: str, default: int, lo: int, hi: int, suffix: str = "") -> QSpinBox:
    s = QSpinBox(); s.setRange(lo, hi); s.setSuffix(suffix); return _bind(win, key, s, default)  # type: ignore[return-value]


def _row(label_w: str, widget: QWidget) -> QWidget:
    r = QWidget(); l = QHBoxLayout(r); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(12); l.addWidget(widget, 0)
    lab = QLabel(label_w); lab.setWordWrap(True); lab.setMinimumWidth(0); l.addWidget(lab, 1); return r


def _sec_general(win, sec: Section) -> None:
    lang = QComboBox(); lang.addItem("فارسی", "fa"); lang.addItem("English", "en")
    sec.add(S["language"], _bind(win, "lang", lang, "fa")); sec.add("", win.label(S["restart_note"], 9, muted=True))
    lang.currentIndexChanged.connect(lambda _i: win.ask_restart_for_language())
    s2 = Section(S["working_hours"]); a = _spin(win, "work_start", 9, 0, 23, ":00"); b = _spin(win, "work_end", 17, 1, 24, ":00")
    s2.pair(S["from_hour"], a, S["to_hour"], b)
    wd = ChipInput(); s2.add(S["off_weekdays"], wd)
    win._settings_extra.append(s2)
    d = Section(S["defaults"])
    cats = taxonomy.categories(win.db.get_setting("custom_categories", {}))
    c = QComboBox()
    for k, v in cats.items():
        c.addItem(f"{v.get('icon', '📋')}  {v['name']}", k)
    d.add(S["default_category"], _bind(win, "default_category", c, "general"))
    pr = QComboBox()
    for k, p in taxonomy.PRIORITIES.items():
        pr.addItem(f"{p['icon']} {p['name']}", k)
    d.pair(S["default_priority"], _bind(win, "default_priority", pr, 3), S["default_estimate"], _spin(win, "default_estimate", 30, 0, 1440, " " + S["min"]))
    d.add("", _row(S["confirm_deletes"], _sw(win, "confirm_deletes", True)))
    win._settings_extra.append(d)


def _sec_quick(win, sec: Section) -> None:
    sec.add("", win.label(S["float_explain"], 10, muted=True))
    sec.add("", _row(S["float_enabled"], _bind(win, "float_enabled", LiquidSwitch(win.theme), True)))
    sz = QComboBox()
    for k, label in (("s", S["size_s"]), ("m", S["size_m"]), ("l", S["size_l"])):
        sz.addItem(label, k)
    sec.pair(S["float_size"], _bind(win, "float_size", sz, "m"), "", QWidget())
    op, idle = QSlider(Qt.Horizontal), QSlider(Qt.Horizontal)
    op.setRange(30, 100); idle.setRange(20, 100)
    sec.pair(S["float_opacity"], _bind(win, "float_opacity", op, 95), S["float_idle_opacity"], _bind(win, "float_idle_opacity", idle, 55))
    sec.add("", _row(S["float_snap"], _bind(win, "float_snap", LiquidSwitch(win.theme), True)))


def _sec_appearance(win, sec: Section) -> None:
    from ..themes_list import THEME_NAMES
    from .glass import THEMES
    th = QComboBox()
    for n in THEME_NAMES:
        th.addItem(THEMES[n]["label"], n)
    from .glass import Theme as _T
    th.setCurrentIndex(max(0, th.findData(_T.normalise(win.db.get_setting("theme", "tokyo_night")))))
    th.currentIndexChanged.connect(lambda _i: win.apply_theme(th.currentData()))                # live: no restart needed
    sec.add(S["theme"], th)
    ac = ColorSwatches(); ac.setColor(win.db.get_setting("accent", "") or ""); ac.changed.connect(lambda c: (_save(win, "accent", c or None), win.apply_accent(c)))
    sec.add(S["accent"], ac)
    wp = QPushButton(S["wallpaper"]); wp.setProperty("chip", True); wp.setCursor(Qt.PointingHandCursor); wp.clicked.connect(win._pick_wallpaper)
    rm = QPushButton(S["remove_wallpaper"]); rm.setProperty("chip", True); rm.setCursor(Qt.PointingHandCursor); rm.clicked.connect(lambda: (_save(win, "wallpaper", None), win.set_wallpaper(None)))
    r = QWidget(); rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(wp); rl.addWidget(rm); rl.addStretch(); sec.add(S["wallpaper"], r)
    fx = Section(S["liquid_fx"])
    fx.add("", _row(S["lite_mode"], _bind(win, "lite", LiquidSwitch(win.theme), False)))
    fx.add("", _row(S["drips_fx"], _bind(win, "fx_enabled", LiquidSwitch(win.theme), True)))
    fx.add("", _row(S["sound_on"], _bind(win, "sound_enabled", LiquidSwitch(win.theme), True)))
    vol = QSlider(Qt.Horizontal); vol.setRange(0, 100); fx.add(S["volume"], _bind(win, "sound_volume", vol, 55))
    test = GlassButton(S["test_sound"], win.theme, icon="sound"); test.clicked.connect(lambda: win.theme.fx.play("success") if win.theme.fx else None); fx.add("", test)
    win._settings_extra.append(fx)
    ft = Section(S["font"]); info = win.font_info
    ft.add("", win.label(to_fa_digits(S["font_loaded"].format(f=info.primary if info else "—")), 10))
    ft.add("", win.label(S["font_hint"], 9, muted=True)); win._settings_extra.append(ft)


def _sec_tracking(win, sec: Section) -> None:
    rd = QComboBox()
    for x in (0, 5, 15, 30):
        rd.addItem(str(x) if x else S["off"], x)
    sec.pair(S["round"], _bind(win, "round", rd, 0), S["min_duration"], _spin(win, "tracker_min_sec", 60, 0, 3600, " s"))
    sec.pair(S["idle_threshold"], _spin(win, "tracker_idle_sec", 300, 30, 7200, " s"), S["max_session"], _spin(win, "tracker_max_hours", 4, 1, 24, " h"))
    pm_ = Section(S["pomodoro"]); pm_.pair(S["work"], _spin(win, "pomo_work", 25, 1, 180, " " + S["min"]), S["short_break"], _spin(win, "pomo_short", 5, 1, 60, " " + S["min"]))
    pm_.pair(S["long_break"], _spin(win, "pomo_long", 15, 1, 90, " " + S["min"]), S["cycles"], _spin(win, "pomo_cycles", 4, 1, 12))
    pm_.add("", _row(S["auto_next"], _sw(win, "pomo_auto", False))); win._settings_extra.append(pm_)
    hl = Section(S["health_reminders"]); hl.add("", _row(S["reminders_on"], _sw(win, "health_on", True)))
    for kind, lab in (("eyes", S["rem_eyes"]), ("posture", S["rem_posture"]), ("water", S["rem_water"])):
        hl.add(lab, _bind(win, f"rem_{kind}", QSpinBox(), REMINDER_DEFAULTS[kind]) if False else _rem_spin(win, kind))
    win._settings_extra.append(hl)


def _rem_spin(win, kind: str) -> QSpinBox:
    s = QSpinBox(); s.setRange(1, 480); s.setSuffix(" " + S["min"]); s.setValue(Reminders(win.db).intervals()[kind])
    s.valueChanged.connect(lambda v: Reminders(win.db).set_interval(kind, v)); return s


def _sec_auto(win, sec: Section) -> None:
    d = AutoConfig().to_dict()
    sec.add("", win.label(S["auto_explain"], 10, muted=True))
    sec.add("", _row(S["auto_enabled"], _bind_dict(win, "auto_config", "enabled", LiquidSwitch(win.theme), d)))
    cats = Section(S["auto_cats"])
    host = QWidget(); fl = FlowLayout(host)
    cur = set(win.db.get_setting("auto_config", d).get("work_categories", d["work_categories"]))
    for k, label in (("development", "برنامه‌نویسی"), ("design", "طراحی"), ("documents", "اسناد"), ("communication", "ارتباطات"), ("email", "ایمیل"), ("browsing", "مرورگر"), ("other", "سایر")):
        b = chip_button(label, True); b.setChecked(k in cur)
        def toggle(_c=False, key=k, btn=b) -> None:
            c = {**d, **win.db.get_setting("auto_config", {})}; s = set(c["work_categories"]); (s.add if btn.isChecked() else s.discard)(key); c["work_categories"] = sorted(s); _save(win, "auto_config", c)
        b.clicked.connect(toggle); fl.addWidget(b)
    cats.add("", host)
    cats.add(S["auto_extra_apps"], _bind_dict(win, "auto_config", "extra_work_apps", ChipInput(placeholder=S["app_name_hint"]), d))
    win._settings_extra.append(cats)
    t = Section(S["auto_timing"])
    t.pair(S["idle_limit"], _bind_dict(win, "auto_config", "idle_limit", _plain_spin(10, 3600, " s"), d), S["start_after"], _bind_dict(win, "auto_config", "start_after", _plain_spin(10, 3600, " s"), d))
    t.pair(S["stop_after"], _bind_dict(win, "auto_config", "stop_after", _plain_spin(30, 7200, " s"), d), S["min_session"], _bind_dict(win, "auto_config", "min_session", _plain_spin(10, 3600, " s"), d))
    sec_act = Section(S["activity_capture"]); sec_act.add("", _row(S["activity_capture"], _sw(win, "activity_capture", False))); win._settings_extra += [t, sec_act]


def _plain_spin(lo: int, hi: int, suffix: str) -> QSpinBox:
    s = QSpinBox(); s.setRange(lo, hi); s.setSuffix(suffix); return s


def _sec_prompt(win, sec: Section) -> None:
    d = PromptConfig().to_dict()
    sec.add("", win.label(S["prompt_explain"], 10, muted=True))
    sec.add("", _row(S["prompt_enabled"], _bind_dict(win, "prompt_config", "enabled", LiquidSwitch(win.theme), d)))
    sec.add("", _row(S["prompt_forced"], _bind_dict(win, "prompt_config", "forced", LiquidSwitch(win.theme), d)))
    sec.add("", _row(S["prompt_aligned"], _bind_dict(win, "prompt_config", "aligned", LiquidSwitch(win.theme), d)))
    sec.pair(S["prompt_interval"], _bind_dict(win, "prompt_config", "interval_min", _plain_spin(5, 480, " " + S["min"]), d), S["prompt_snoozes"], _bind_dict(win, "prompt_config", "max_snoozes", _plain_spin(0, 10, ""), d))
    sec.pair(S["prompt_snooze_min"], _bind_dict(win, "prompt_config", "snooze_min", _plain_spin(1, 120, " " + S["min"]), d), S["prompt_min_gap"], _bind_dict(win, "prompt_config", "min_gap_min", _plain_spin(1, 240, " " + S["min"]), d))
    q = Section(S["quiet_hours"]); q.pair(S["quiet_from"], _bind_dict(win, "prompt_config", "quiet_start", _plain_spin(0, 23, ":00"), d), S["quiet_to"], _bind_dict(win, "prompt_config", "quiet_end", _plain_spin(0, 23, ":00"), d))
    q.add("", _row(S["prompt_only_engaged"], _bind_dict(win, "prompt_config", "only_when_engaged", LiquidSwitch(win.theme), d)))
    test = GlassButton(S["prompt_test"], win.theme, primary=True, icon="bell"); test.clicked.connect(lambda: win.runtime.show_prompt(force=True)); q.add("", test)
    win._settings_extra.append(q)


def _sec_shots(win, sec: Section) -> None:
    sec.add("", win.label(S["shots_explain"], 10, muted=True))
    sec.add("", _row(S["shots_enabled"], _sw(win, "shots_enabled", False)))
    sec.add("", _row(S["shots_only_working"], _sw(win, "shots_require_engaged", True)))
    sec.pair(S["shots_interval"], _spin(win, "shots_interval", 60, 5, 720, " " + S["min"]), S["shots_keep"], _spin(win, "shots_keep_days", 30, 1, 3650, " " + S["days"]))
    sec.pair(S["shots_width"], _spin(win, "shots_width", 1280, 640, 3840, " px"), S["shots_quality"], _spin(win, "shots_quality", 45, 15, 90, "%"))
    sec.pair(S["shots_max_mb"], _spin(win, "shots_max_mb", 500, 20, 100000, " MB"), "", QWidget())
    sec.add("", _row(S["shots_gray"], _sw(win, "shots_gray", False)))
    b = Section(S["shots_privacy"]); b.add(S["shots_blocked"], _bind(win, "shots_blocked", ChipInput(placeholder=S["app_name_hint"]), ["keepass", "bitwarden", "1password", "lastpass", "password", "بانک", "bank", "پرداخت", "payment", "incognito", "private browsing"]))
    b.add("", _row(S["shots_paused"], _sw(win, "shots_paused", False)))
    op = GlassButton(S["open_folder"], win.theme, icon="projects"); op.clicked.connect(lambda: _open_folder(win.data_dir / "screenshots")); b.add("", op); win._settings_extra.append(b)


def _open_folder(path: Path) -> None:
    from PyQt5.QtGui import QDesktopServices
    path.mkdir(parents=True, exist_ok=True); QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def _sec_tips(win, sec: Section) -> None:
    sec.add("", _row(S["tips_enabled"], _sw(win, "tips_enabled", True)))
    host = QWidget(); fl = FlowLayout(host); off = set(win.db.get_setting("tips_disabled_cats", []))
    for k, label in TIP_CATS.items():
        b = chip_button(label, True); b.setChecked(k not in off)
        def tg(_c=False, key=k, btn=b) -> None:
            s = set(win.db.get_setting("tips_disabled_cats", [])); (s.discard if btn.isChecked() else s.add)(key); _save(win, "tips_disabled_cats", sorted(s)); refresh_tip(win)
        b.clicked.connect(tg); fl.addWidget(b)
    sec.add(S["tip_cats"], host)
    own = QLineEdit(placeholderText=S["tip_own_hint"]); ab = GlassButton(S["add"], win.theme, icon="plus")
    def add_own() -> None:
        try:
            Tips(win.db).add_own(own.text()); own.clear(); win.toast(S["saved"]); refresh_tip(win)
        except ValueError as exc:
            win.toast(str(exc))
    ab.clicked.connect(add_own); r = QWidget(); rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(own, 1); rl.addWidget(ab); sec.add(S["tip_own"], r)
    on = Section(S["tips_online"]); on.add("", win.label(S["tips_online_explain"], 10, muted=True))
    url = _bind(win, "tips_feed_url", QLineEdit(), ""); url.setPlaceholderText("https://example.com/tips.json"); on.add(S["tips_feed_url"], url)
    rf = GlassButton(S["tips_refresh"], win.theme, icon="refresh")
    def refresh_online() -> None:
        try:
            n = Tips(win.db).refresh_online(win.db.get_setting("tips_feed_url", "")); win.toast(to_fa_digits(f"{n} {S['tips_added']}")); refresh_tip(win)
        except Exception as exc:  # noqa: BLE001
            win.toast(str(exc))
    rf.clicked.connect(refresh_online); on.add("", rf); win._settings_extra.append(on)


def _sec_manage(win, sec: Section) -> None:
    from ..services.taskform import COLUMN_LABELS, ALL_COLUMNS_ORDER
    sec.add("", win.label(S["board_cols_explain"], 10, muted=True))
    shown = set(win.db.get_setting("board_columns", ["backlog", "in_progress", "review", "done"]))
    wip = dict(win.db.get_setting("wip_limits", {}))
    for c in ALL_COLUMNS_ORDER:
        sw = LiquidSwitch(win.theme, c in shown); spin = QSpinBox(); spin.setRange(0, 99); spin.setValue(int(wip.get(c, 0))); spin.setSpecialValueText(S["no_limit"])
        def upd(*_a, col=c, s=sw, sp=spin) -> None:
            cur = set(win.db.get_setting("board_columns", ["backlog", "in_progress", "review", "done"])); (cur.add if s.isChecked() else cur.discard)(col)
            w = dict(win.db.get_setting("wip_limits", {})); w[col] = sp.value()
            win.db.set_setting("board_columns", [x for x in ALL_COLUMNS_ORDER if x in cur]); win.db.set_setting("wip_limits", w); win.refresh_all()
        sw.toggled.connect(upd); spin.valueChanged.connect(upd)
        r = QWidget(); rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(sw); rl.addWidget(QLabel(COLUMN_LABELS[c]), 1); rl.addWidget(QLabel(S["wip_limit"])); rl.addWidget(spin); sec.add("", r)
    cc = Section(S["custom_cats"]); key, name, icon_, subs = QLineEdit(placeholderText="key"), QLineEdit(placeholderText=S["name"]), QLineEdit(placeholderText="⭐"), QLineEdit(placeholderText=S["subs_hint"])
    cc.pair("key", key, S["name"], name); cc.pair(S["icon"], icon_, S["subcategory"], subs)
    add = GlassButton(S["add"], win.theme, primary=True, icon="plus")
    def add_cat() -> None:
        try:
            cur = win.db.get_setting("custom_categories", {})
            cur = taxonomy.add_custom_category(cur, key.text().strip(), name.text().strip(), icon_.text().strip() or "📋", [s.strip() for s in subs.text().split("،") if s.strip()] or [s.strip() for s in subs.text().split(",") if s.strip()])
            win.db.set_setting("custom_categories", cur); win.toast(S["saved"]); key.clear(); name.clear(); subs.clear()
        except ValueError as exc:
            win.toast(str(exc))
    add.clicked.connect(add_cat); cc.add("", add)
    bl = Section(S["billing_defaults"]); cur = QComboBox()
    for c in ("IRR", "USD", "EUR"):
        cur.addItem(c, c)
    tax = QComboBox(); tax.addItem(S["tax_none"], 0.0); tax.addItem("10٪", 10.0); tax.addItem("9٪", 9.0)
    bl.pair(S["currency"], _bind(win, "default_currency", cur, "IRR"), S["tax"], _bind(win, "default_tax", tax, 0.0)); bl.add(S["invoice_prefix"], _bind(win, "invoice_prefix", QLineEdit(), "INV"))
    it = Section(S["integrations"]); it.add(S["webhook_url"], _bind(win, "webhook_url", QLineEdit(), "")); it.add("Slack webhook", _bind(win, "slack_url", QLineEdit(), ""))
    it.pair("Telegram token", _bind(win, "tg_token", QLineEdit(), ""), "Telegram chat id", _bind(win, "tg_chat", QLineEdit(), ""))
    it.add("", _row(S["tg_poll"], _sw(win, "tg_poll", False)))
    it.add("", _row(S["api_enabled"], _sw(win, "api_enabled", False))); it.add(S["api_token"], _bind(win, "api_token", QLineEdit(), ""))
    win._settings_extra += [cc, bl, it]


def _sec_data(win, sec: Section) -> None:
    from . import backup_ui as bk
    sec.add("", win.label(S["bk_export_note"], 10, muted=True))
    last = win.db.get_setting("last_backup_at")
    sec.add(S["bk_last"], win.label(to_fa_digits(format_jalali(to_tehran(__import__("datetime").datetime.fromisoformat(last)).date()) + " " + to_tehran(__import__("datetime").datetime.fromisoformat(last)).strftime("%H:%M")) if last else S["bk_never"], 10))
    host = QWidget(); fl = FlowLayout(host)
    for label, fn, primary, ic in ((S["bk_package_btn"], lambda: bk.export_package_ui(win), True, "download"), (S["bk_restore_btn"], lambda: bk.restore_package_ui(win), False, "upload"),
                                   (S["bk_cfg_export"], lambda: bk.export_config_ui(win), False, "download"), (S["bk_cfg_import"], lambda: bk.import_config_ui(win), False, "upload")):
        b = GlassButton(label, win.theme, primary=primary, icon=ic); b.clicked.connect(lambda _c=False, f=fn: f()); fl.addWidget(b)
    sec.add("", host)
    auto = Section(S["bk_auto"]); auto.add("", _row(S["bk_auto"], _sw(win, "auto_backup", True))); auto.add(S["bk_keep_n"], _spin(win, "backups_keep", 14, 1, 365))
    auto.add(S["author_name"], _bind(win, "author_name", QLineEdit(), ""))
    win._settings_extra.append(auto)
    other = Section(S["export_json"].split()[0] + " / " + S["import_legacy"]); btns = ((S["export_json"], lambda: win._export("json")), (S["export_csv"], lambda: win._export("csv")), (S["export_xlsx"], lambda: win._export("xlsx")),
                                                                                   (S["ics"], win._export_ics), (S["import_legacy"], win._import_legacy), (S["pick_sync_folder"], win._pick_sync_folder), (S["sync_now"], win._sync_now),
                                                                                   (S["open_folder"], lambda: _open_folder(win.data_dir)))
    h2 = QWidget(); f2 = FlowLayout(h2)
    for label, fn in btns:
        b = GlassButton(label, win.theme); b.clicked.connect(lambda _c=False, f=fn: f()); f2.addWidget(b)
    other.add("", h2); win._settings_extra.append(other)
    m = Section(S["maintenance"]); mh = QWidget(); mf = FlowLayout(mh)
    from ..services import maintenance
    for label, fn in ((S["compress_audit"], lambda: win.toast(to_fa_digits(f"{maintenance.compress_old_audit(win.db)} {S['rows']}"))), (S["vacuum"], lambda: (maintenance.vacuum(win.db), win.toast(S["saved"])))):
        b = GlassButton(label, win.theme); b.clicked.connect(lambda _c=False, f=fn: f()); mf.addWidget(b)
    m.add("", mh); win._settings_extra.append(m)


def _sec_about(win, sec: Section) -> None:
    from .. import __version__
    info = win.font_info
    lines = [f"WorkTracker {__version__}", S["data_folder"] + ": " + str(win.data_dir), S["font"] + ": " + (info.primary if info and info.primary else "—"),
             S["font_search"] + ": " + ("، ".join(info.searched[:3]) if info and info.searched else "—"), "", S["shortcuts"],
             "Ctrl+K — " + S["palette"], "Ctrl+Z / Ctrl+Y — " + S["undo"] + " / " + S["redo"], "Ctrl+Shift+Space — " + S["quick"], "Ctrl+Shift+F — " + S["focus"], "Ctrl+Shift+M — " + S["mini"]]
    l = win.label("\n".join(lines), 10); l.setTextInteractionFlags(Qt.TextSelectableByMouse); sec.add("", l)


SETTINGS_SECTIONS = (("general", "settings", _sec_general), ("quick", "bolt", _sec_quick), ("appearance", "sparkle", _sec_appearance), ("tracking", "clock", _sec_tracking), ("auto", "bolt", _sec_auto),
                     ("prompt", "bell", _sec_prompt), ("shots", "camera", _sec_shots), ("tips", "lightbulb", _sec_tips), ("manage", "tools", _sec_manage), ("data", "download", _sec_data), ("about", "note", _sec_about))


def build_settings_page(win) -> None:
    page, lay = _page(win)
    lay.addWidget(win.label(S["settings"], 17, True))
    body = QHBoxLayout(); body.setSpacing(12)
    win.st_list = QListWidget(); win.st_list.setFixedWidth(190); win.st_list.setCursor(Qt.PointingHandCursor)
    win.st_stack = QStackedWidget()
    for key, icon_name, builder in SETTINGS_SECTIONS:
        win._settings_extra = []
        sec = Section(S["st_" + key])
        try:
            builder(win, sec)
        except Exception:  # noqa: BLE001 - one broken section must not take down the whole page
            log.exception("settings section %s failed", key)
            sec.add("", win.label("⚠ " + S["section_failed"], 10))
        host = QWidget(); v = QVBoxLayout(host); v.setContentsMargins(2, 2, 10, 2); v.setSpacing(12); v.addWidget(sec)
        for extra in win._settings_extra:
            v.addWidget(extra)
        v.addStretch()
        win.st_stack.addWidget(_scroll(host))
        it = QListWidgetItem(icons.icon(icon_name, win.theme.text().name(), 20), "  " + S["st_" + key]); win.st_list.addItem(it)
    win.st_list.currentRowChanged.connect(win.st_stack.setCurrentIndex); win.st_list.setCurrentRow(0)
    body.addWidget(win.st_list); body.addWidget(win.st_stack, 1); lay.addLayout(body, 1)
    win.pages.addWidget(page)
