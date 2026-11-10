"""Glass pop-up dialogs. Every form is a real multi-section form, not a single input.

``PopDialog`` gives each one the liquid pop-in (spring + fade), a dimmed backdrop, a shake on validation errors and sounds.
Business rules live in ``services.taskform`` / ``services.prompter``; this file only collects widget values.
"""
from __future__ import annotations

import datetime as dt
import logging
from collections import Counter
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QPlainTextEdit, QScrollArea, QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from ..core import taxonomy
from ..core.models import Client, Goal, Habit, Member, Project, ProjectStatus, Status, TimeEntry
from ..core.persian import now_utc, to_fa_digits, to_tehran
from ..services import smart2, taskform as tf
from . import icons
from .forms import (ChecklistEditor, ChipInput, ColorSwatches, DateTimeField, DurationEdit, FlowLayout, IconPicker, JalaliDateEdit, PriorityPicker, Section, Segmented,
                    chip_button)
from .glass import GlassButton, LiquidSwitch, qcolor
from .liquid.physics import Spring
from .strings import S

log = logging.getLogger("worktracker.dialogs")


def confirm(parent: QWidget, text: str) -> bool:
    return QMessageBox.question(parent, S["app"], text) == QMessageBox.Yes


class Scrim(QWidget):
    """Dim layer over the main window while a pop-up is open."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.hide()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self); p.fillRect(self.rect(), QColor(5, 5, 15, 120))

    def fit(self) -> None:
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())


class PopDialog(QDialog):
    """Frameless glass panel that springs in. Subclasses fill ``self.body`` and ``self.footer``."""

    def __init__(self, win, title: str, icon_name: str = "plus", width: int = 780, top: bool = False, closable: bool = True) -> None:
        flags = Qt.Dialog | Qt.FramelessWindowHint | (Qt.WindowStaysOnTopHint if top else 0)
        super().__init__(None if top else win, flags)
        self.win, self.theme, self.db = win, win.theme, win.db
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setLayoutDirection(win.layoutDirection())
        self._closable, self._drag = closable, None
        self._spring = Spring(0.0, 1.0, stiffness=190.0, damping=11.5)
        self._timer = QTimer(self); self._timer.setInterval(16); self._timer.timeout.connect(self._tick)
        self.resize(width, 200)
        self.setMinimumWidth(min(width, max(360, win.width() - 60)))
        root = QVBoxLayout(self); root.setContentsMargins(26, 24, 26, 22); root.setSpacing(12)
        head = QHBoxLayout(); head.setSpacing(10)
        ic = QLabel(); ic.setPixmap(icons.pixmap(icon_name, self.theme.accents[1], 26)); head.addWidget(ic)
        self.title_lbl = QLabel(title); self.title_lbl.setStyleSheet("font-size:15pt;font-weight:700;background:transparent;"); head.addWidget(self.title_lbl, 1)
        if closable:
            x = GlassButton("", self.theme, icon="close"); x.setFixedSize(38, 38); x.clicked.connect(self.reject); head.addWidget(x)
        root.addLayout(head)
        self.error_lbl = QLabel(""); self.error_lbl.setStyleSheet("color:#FF6B81;font-weight:600;background:transparent;"); self.error_lbl.setWordWrap(True); self.error_lbl.hide()
        self.body = QVBoxLayout(); self.body.setSpacing(10); root.addLayout(self.body, 1); root.addWidget(self.error_lbl)
        self.footer = QHBoxLayout(); self.footer.setSpacing(10); root.addLayout(self.footer)

    # ---- liquid entrance ----------------------------------------------------------
    def _tick(self) -> None:
        self._spring.step(0.016); self.update()
        if self._spring.settled:
            self._timer.stop()

    def showEvent(self, e) -> None:  # noqa: N802
        self._spring.value, self._spring.vel = 0.0, 0.0
        if not self.theme.lite:
            self._timer.start()
            self.setWindowOpacity(0.0)
            self._fade = QPropertyAnimation(self, b"windowOpacity", self); self._fade.setDuration(240); self._fade.setStartValue(0.0); self._fade.setEndValue(1.0); self._fade.start()
        if self.theme.fx is not None:
            self.theme.fx.play("open")
        self._center()
        super().showEvent(e)

    def _screen_rect(self):
        try:
            from .floating import _screen_rect
            ref = self.win.geometry().center() if self.win is not None else QPoint(0, 0)
            return _screen_rect(ref)
        except Exception:  # noqa: BLE001
            return (0, 0, 1920, 1080)

    def _center(self) -> None:
        """Compute the real size from the layout FIRST, cap it to the screen, then centre on the main window and clamp so every edge (and the footer buttons) is visible."""
        sx, sy, sw, sh = self._screen_rect()
        lay = self.layout()
        if lay is not None:
            lay.activate()
        self.setMaximumSize(max(360, sw - 24), max(300, sh - 24))
        self.adjustSize()
        w, h = min(self.width(), sw - 24), min(self.height(), sh - 24)
        self.resize(w, h)
        ref = self.win.geometry().center() if self.win is not None else QPoint(sx + sw // 2, sy + sh // 2)
        x = max(sx + 12, min(ref.x() - w // 2, sx + sw - w - 12))
        y = max(sy + 12, min(ref.y() - h // 2, sy + sh - h - 12))
        self.move(x, y)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        k = max(0.0, min(1.12, self._spring.value))
        s = 0.9 + 0.1 * k
        r = QRectF(self.rect()).adjusted(12, 12, -12, -12)
        c = r.center(); p.translate(c); p.scale(s, s); p.translate(-c)
        for i, a in enumerate((26, 16, 9, 4)):                                   # soft shadow
            p.setPen(QPen(QColor(0, 0, 0, a), 1)); p.setBrush(Qt.NoBrush); p.drawRoundedRect(r.adjusted(-i * 2, -i * 2 + 4, i * 2, i * 2 + 4), 26 + i * 2, 26 + i * 2)
        path = QPainterPath(); path.addRoundedRect(r, 26, 26)
        dark = self.theme.dark
        p.fillPath(path, QColor(18, 18, 36, 244) if dark else QColor(250, 250, 255, 246))
        p.setClipPath(path)
        for (fx_, fy_), col in (((0.0, 0.0), self.theme.accents[0]), ((1.0, 1.0), self.theme.accents[2]), ((1.0, 0.0), self.theme.accents[1])):   # liquid glows in the corners
            g = QRadialGradient(QPointF(r.left() + r.width() * fx_, r.top() + r.height() * fy_), r.width() * 0.5)
            g.setColorAt(0, qcolor(col, 64 if dark else 40)); g.setColorAt(1, qcolor(col, 0)); p.fillRect(r, QBrush(g))
        bar = QLinearGradient(r.topLeft(), r.topRight())
        for i, col in enumerate(self.theme.accents):
            bar.setColorAt(i / 2, qcolor(col, 230))
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 4), QBrush(bar))
        p.setClipping(False)
        p.setPen(QPen(qcolor("#FFFFFF", 70 if dark else 120), 1.2)); p.setBrush(Qt.NoBrush); p.drawPath(path)

    # ---- feedback ----------------------------------------------------------------------
    def shake(self) -> None:
        if self.theme.lite:
            return
        x0 = self.pos()
        a = QPropertyAnimation(self, b"pos", self); a.setDuration(380)
        for t, dx in ((0.0, 0), (0.15, -14), (0.3, 12), (0.45, -9), (0.6, 7), (0.8, -3), (1.0, 0)):
            a.setKeyValueAt(t, QPoint(x0.x() + dx, x0.y()))
        a.start(); self._shake = a
        if self.theme.fx is not None:
            self.theme.fx.play("warn")

    def show_error(self, text: str) -> None:
        self.error_lbl.setText("⚠ " + text); self.error_lbl.show(); self.shake()

    def clear_error(self) -> None:
        self.error_lbl.hide()

    def exec_(self) -> int:  # noqa: N802
        scrim = getattr(self.win, "scrim", None)
        if scrim is not None:
            scrim.fit(); scrim.show(); scrim.raise_()
        try:
            return super().exec_()
        finally:
            if scrim is not None:
                scrim.hide()

    def done(self, r: int) -> None:
        if self.theme.fx is not None:
            self.theme.fx.play("close" if r == 0 else "success")
        super().done(r)

    def reject(self) -> None:
        if self._closable:
            super().reject()

    def keyPressEvent(self, e) -> None:  # noqa: N802
        if e.key() == Qt.Key_Escape and not self._closable:
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.pos().y() < 78:
            self._drag = e.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._drag = None

    # ---- helpers -------------------------------------------------------------------------
    def scroll_page(self, *sections: QWidget) -> QScrollArea:
        host = QWidget(); v = QVBoxLayout(host); v.setContentsMargins(2, 2, 8, 2); v.setSpacing(12)
        for s in sections:
            v.addWidget(s)
        v.addStretch()
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(host); sa.setFrameShape(QFrame.NoFrame)
        avail = self._screen_rect()[3]
        sa.setMinimumHeight(max(150, min(420, avail - 400)))           # leaves room for header, tabs and footer even on a 768-px laptop screen
        return sa

    def buttons(self, *btns: GlassButton) -> None:
        self.footer.addStretch()
        for b in btns:
            self.footer.addWidget(b)


def _combo(items: List[tuple], current: Any = None) -> QComboBox:
    c = QComboBox()
    for label, data in items:
        c.addItem(label, data)
    if current is not None:
        c.setCurrentIndex(max(0, c.findData(current)))
    return c


# ====================================================================================== TASK
class TaskDialog(PopDialog):
    """Add / edit a task - four sections: Info, Time, Details, Repeat & reminders."""

    def __init__(self, win, entry: Optional[TimeEntry] = None, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(win, S["edit_task"] if entry else S["new_task"], "tasks", 860)
        self.entry, self.saved, self._sync = entry, None, False
        self.defaults = defaults or {}
        db = self.db
        projects = db.all(Project, "name")
        members = db.all(Member)
        tag_counts: Counter = Counter(t for e in db.all(TimeEntry)[-1500:] for t in e.tags)

        # ---- tab 1: info
        self.title = QLineEdit(placeholderText=S["task_title_hint"]); self.title.textChanged.connect(self._suggest)
        self.suggest_row = QWidget(); self.suggest_flow = FlowLayout(self.suggest_row)
        self.desc = QPlainTextEdit(); self.desc.setPlaceholderText(S["description"]); self.desc.setFixedHeight(92)
        self.project = _combo([(S["no_project"], None)] + [(f"{p.icon} {p.name}", p.id) for p in projects])
        newp = chip_button(S["new_project"]); newp.clicked.connect(self._new_project)
        cats = taxonomy.categories(db.get_setting("custom_categories", {}))
        self.category = _combo([(f"{v.get('icon', '📋')}  {v['name']}", k) for k, v in cats.items()])
        self.subcategory = QComboBox(); self.subcategory.setEditable(True)
        self.category.currentIndexChanged.connect(self._fill_sub)
        self.priority = PriorityPicker()
        self.column = Segmented([(tf.COLUMN_LABELS[c], c) for c in tf.ALL_COLUMNS_ORDER])
        self.tags = ChipInput(suggestions=[t for t, _ in tag_counts.most_common(12)])
        self.assignee = _combo([(S["nobody"], "")] + [(m.name, m.id) for m in members])
        self.color = ColorSwatches(); self.icon_pick = IconPicker()
        s1 = Section(S["sec_basic"]); s1.add(S["title"], self.title); s1.add("", self.suggest_row); s1.add(S["description"], self.desc)
        row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(self.project, 1); rl.addWidget(newp); s1.add(S["project"], row)
        s1.pair(S["category"], self.category, S["subcategory"], self.subcategory)
        s2 = Section(S["sec_status"]); s2.add(S["priority"], self.priority); s2.add(S["status"], self.column); s2.add(S["tags"], self.tags)
        s2.pair(S["assignee"], self.assignee, "", QWidget())
        s3 = Section(S["sec_look"]); s3.add(S["color"], self.color); s3.add(S["icon"], self.icon_pick)
        page1 = self.scroll_page(s1, s2, s3)

        # ---- tab 2: time
        quick_host = QWidget(); qf = FlowLayout(quick_host)
        for label, kind in ((S["q_now"], "now"), (S["q_30"], "in30"), (S["q_60"], "in60"), (S["q_tonight"], "tonight"), (S["q_tomorrow"], "tomorrow")):
            b = chip_button(label); b.clicked.connect(lambda _c=False, k=kind: self._quick(k)); qf.addWidget(b)
        self.all_day = LiquidSwitch(self.theme); self.start = DateTimeField(); self.end = DateTimeField(); self.duration = DurationEdit((15, 30, 45, 60, 90, 120, 180, 240))
        self.due = DateTimeField(); self.estimate = DurationEdit((15, 30, 60, 120, 240))
        self.start.changed.connect(self._from_start); self.end.changed.connect(self._from_end); self.duration.changed.connect(self._from_duration)
        self.energy = Segmented([(S["none"], 0)] + [(to_fa_digits(str(i)), i) for i in range(1, 6)], wrap=False)
        self.location = _combo([(S.get("loc_" + (l or "none"), l or "—"), l) for l in tf.LOCATIONS])
        self.billable = LiquidSwitch(self.theme); self.rate = QDoubleSpinBox(); self.rate.setRange(0, 1e12); self.rate.setSpecialValueText(S["default_rate"]); self.rate.setGroupSeparatorShown(True)
        self.timer_now = LiquidSwitch(self.theme)
        t1 = Section(S["sec_when"]); t1.add(S["quick_time"], quick_host)
        sw = QWidget(); swl = QHBoxLayout(sw); swl.setContentsMargins(0, 0, 0, 0); swl.addWidget(self.all_day); swl.addWidget(QLabel(S["all_day"])); swl.addStretch(); t1.add("", sw)
        t1.add(S["start"], self.start); t1.add(S["end"], self.end); t1.add(S["duration"], self.duration); t1.add(S["due"], self.due); t1.add(S["estimate"], self.estimate)
        t2 = Section(S["sec_context"]); t2.add(S["energy"], self.energy); t2.add(S["location"], self.location)
        bl = QWidget(); bll = QHBoxLayout(bl); bll.setContentsMargins(0, 0, 0, 0); bll.addWidget(self.billable); bll.addWidget(QLabel(S["billable"])); bll.addWidget(self.rate, 1); t2.add("", bl)
        tm = QWidget(); tml = QHBoxLayout(tm); tml.setContentsMargins(0, 0, 0, 0); tml.addWidget(self.timer_now); tml.addWidget(QLabel(S["start_timer_now"])); tml.addStretch(); t2.add("", tm)
        page2 = self.scroll_page(t1, t2)

        # ---- tab 3: details
        self.checklist = ChecklistEditor(); self.subs = ChecklistEditor(S["subtask_hint"]); self.progress = QSlider(Qt.Horizontal); self.progress.setRange(0, 100); self.progress.setSingleStep(5)
        self.progress_lbl = QLabel("0٪"); self.progress.valueChanged.connect(lambda v: self.progress_lbl.setText(to_fa_digits(f"{v}٪")))
        self.deps = QListWidget(); self.deps.setMinimumHeight(110); self.deps_filter = QLineEdit(placeholderText=S["search"]); self.deps_filter.textChanged.connect(self._filter_deps)
        self.notes = QPlainTextEdit(); self.notes.setPlaceholderText(S["notes"]); self.notes.setFixedHeight(84)
        self.attach = QListWidget(); self.attach.setFixedHeight(76); ab = chip_button(S["add_file"]); ab.clicked.connect(self._add_file); rb = chip_button(S["remove"]); rb.clicked.connect(lambda: [self.attach.takeItem(self.attach.row(i)) for i in self.attach.selectedItems()])
        d1 = Section(S["checklist"]); d1.add("", self.checklist)
        d2 = Section(S["subtasks"]); d2.add("", self.subs)
        if entry is not None and not entry.parent_id:
            sp = GlassButton(S["ls_split"], self.theme, icon="tasks"); sp.clicked.connect(self._split_task); d2.add("", sp)
        pr = QWidget(); prl = QHBoxLayout(pr); prl.setContentsMargins(0, 0, 0, 0); prl.addWidget(self.progress, 1); prl.addWidget(self.progress_lbl)
        d3 = Section(S["progress_deps"]); d3.add(S["progress"], pr); d3.add(S["depends_on"], self.deps_filter); d3.add("", self.deps)
        d4 = Section(S["notes_files"]); d4.add(S["notes"], self.notes); fr = QWidget(); frl = QHBoxLayout(fr); frl.setContentsMargins(0, 0, 0, 0); frl.addWidget(self.attach, 1); col = QVBoxLayout(); col.addWidget(ab); col.addWidget(rb); frl.addLayout(col); d4.add(S["attachments"], fr)
        page3 = self.scroll_page(d1, d2, d3, d4)

        # ---- tab 4: repeat + reminders
        self.rec_type = _combo([(S["rec_none"], ""), (S["rec_daily"], "daily"), (S["rec_weekly"], "weekly"), (S["rec_monthly"], "monthly"), (S["rec_custom"], "custom")])
        self.rec_interval = QSpinBox(); self.rec_interval.setRange(1, 365); self.rec_interval.setPrefix(S["every"] + " ")
        self.rec_until = DateTimeField(with_time=False)
        self.reminders = QListWidget(); self.reminders.setMinimumHeight(190)
        for mins in tf.REMINDER_CHOICES:
            it = QListWidgetItem(S["at_start"] if mins == 0 else to_fa_digits(DurationEdit.fmt(mins) + " " + S["before"]))
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, mins); self.reminders.addItem(it)
        self.important = LiquidSwitch(self.theme)
        r1 = Section(S["sec_repeat"]); r1.add(S["rec_type"], self.rec_type); r1.pair(S["rec_interval"], self.rec_interval, S["rec_until"], self.rec_until)
        r2 = Section(S["sec_reminders"]); r2.add("", self.reminders)
        r3 = Section(S["sec_matrix"]); iw = QWidget(); il = QHBoxLayout(iw); il.setContentsMargins(0, 0, 0, 0); il.addWidget(self.important); il.addWidget(QLabel(S["important"])); il.addStretch(); r3.add("", iw)
        page4 = self.scroll_page(r1, r2, r3)

        # ---- assemble
        self.stack = QStackedWidget()
        for pg in (page1, page2, page3, page4):
            self.stack.addWidget(pg)
        self.tabs = Segmented([(S["tab_info"], 0), (S["tab_time"], 1), (S["tab_details"], 2), (S["tab_repeat"], 3)], wrap=False)
        self.tabs.changed.connect(self.stack.setCurrentIndex)
        self.body.addWidget(self.tabs); self.body.addWidget(self.stack, 1)
        self._fill_sub(); self._load_deps()
        self._load(entry)
        self.title.setFocus()
        btns = []
        if entry:
            d = GlassButton(S["delete"], self.theme, danger=True, icon="trash"); d.clicked.connect(self._delete); self.footer.addWidget(d)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        new = GlassButton(S["save_new"], self.theme, icon="plus"); new.clicked.connect(lambda: self._save(True))
        ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(lambda: self._save(False))
        if entry:
            new.hide()
        self.buttons(cancel, new, ok)
        ok.setDefault(True)

    # ---- behaviour -----------------------------------------------------------------------
    def _fill_sub(self) -> None:
        cats = taxonomy.categories(self.db.get_setting("custom_categories", {}))
        cur = self.subcategory.currentText()
        self.subcategory.clear(); self.subcategory.addItem("")
        for s in cats.get(self.category.currentData(), {}).get("subcategories", []):
            self.subcategory.addItem(s)
        self.subcategory.setEditText(cur)

    def _suggest(self, text: str) -> None:
        while self.suggest_flow.count():
            it = self.suggest_flow.takeAt(0)
            if it is not None and it.widget() is not None:
                it.widget().deleteLater()
        try:
            for s in smart2.suggest_titles(self.db, text, self.project.currentData(), 3):
                b = chip_button("💡 " + s); b.clicked.connect(lambda _c=False, x=s: self.title.setText(x)); self.suggest_flow.addWidget(b)
        except Exception:  # noqa: BLE001 - suggestions are a nicety
            log.debug("suggest failed", exc_info=True)

    def _new_project(self) -> None:
        dlg = ProjectDialog(self.win)
        if dlg.exec_() and dlg.saved:
            self.project.addItem(f"{dlg.saved.icon} {dlg.saved.name}", dlg.saved.id); self.project.setCurrentIndex(self.project.count() - 1)

    def _quick(self, kind: str) -> None:
        t = tf.quick_time(kind)
        self.start.setValue(t.astimezone(dt.timezone.utc))
        if self.duration.minutes() == 0:
            self.duration.setMinutes(self.estimate.minutes() or 30)
        self._from_start()

    def _from_start(self) -> None:
        if self._sync or self.start.value() is None:
            return
        self._sync = True
        s = self.start.value()
        if self.duration.minutes():
            self.end.setValue(tf.end_from_minutes(s, self.duration.minutes()))
        self._sync = False

    def _from_duration(self, mins: int) -> None:
        if self._sync or self.start.value() is None:
            return
        self._sync = True; self.end.setValue(tf.end_from_minutes(self.start.value(), mins)); self._sync = False

    def _from_end(self) -> None:
        if self._sync or self.start.value() is None or self.end.value() is None:
            return
        self._sync = True; self.duration.setMinutes(tf.minutes_between(self.start.value(), self.end.value())); self._sync = False

    def _load_deps(self) -> None:
        own = {self.entry.id} if self.entry else set()
        for e in self.db.all(TimeEntry, "start_utc DESC")[:400]:
            if e.id in own or e.parent_id or e.column in ("done", "cancelled"):
                continue
            it = QListWidgetItem(e.title); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, e.id); self.deps.addItem(it)

    def _filter_deps(self, text: str) -> None:
        for i in range(self.deps.count()):
            it = self.deps.item(i); it.setHidden(bool(text) and text.lower() not in it.text().lower())

    def _add_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, S["add_file"])
        for p in paths:
            self.attach.addItem(p)

    def _load(self, e: Optional[TimeEntry]) -> None:
        d = self.defaults
        v = tf.from_entry(self.db, e) if e else tf.TaskValues(**{k: d[k] for k in d if k in tf.TaskValues.__dataclass_fields__})
        self.title.setText(v.title); self.desc.setPlainText(v.description)
        self.project.setCurrentIndex(max(0, self.project.findData(v.project_id)))
        self.category.setCurrentIndex(max(0, self.category.findData(v.category))); self._fill_sub(); self.subcategory.setEditText(v.subcategory)
        self.priority.setValue(v.priority, emit=False); self.column.setValue(v.column, emit=False); self.tags.setTags(v.tags)
        self.assignee.setCurrentIndex(max(0, self.assignee.findData(v.assignee))); self.color.setColor(v.color); self.icon_pick.setIcon(v.icon)
        self.all_day.setChecked(v.all_day); self._sync = True
        self.start.setValue(v.start); self.end.setValue(v.end); self.due.setValue(v.due); self.duration.setMinutes(tf.minutes_between(v.start, v.end)); self._sync = False
        self.estimate.setMinutes(v.estimated_min); self.energy.setValue(v.energy, emit=False); self.location.setCurrentIndex(max(0, self.location.findData(v.location)))
        self.billable.setChecked(v.billable); self.rate.setValue(v.rate or 0.0)
        self.checklist.setItems(v.checklist); self.progress.setValue(v.progress); self.notes.setPlainText(v.notes)
        for p in v.attachments:
            self.attach.addItem(p)
        for i in range(self.deps.count()):
            self.deps.item(i).setCheckState(Qt.Checked if self.deps.item(i).data(Qt.UserRole) in v.depends_on else Qt.Unchecked)
        rec = v.recurrence or {}
        self.rec_type.setCurrentIndex(max(0, self.rec_type.findData(rec.get("type", "")))); self.rec_interval.setValue(int(rec.get("interval", 1) or 1))
        if rec.get("until"):
            self.rec_until.setValue(dt.datetime.fromisoformat(rec["until"]))
        for i in range(self.reminders.count()):
            self.reminders.item(i).setCheckState(Qt.Checked if self.reminders.item(i).data(Qt.UserRole) in v.reminders else Qt.Unchecked)
        self.important.setChecked(v.important)
        if e is not None and e.parent_id is None:
            kids = [k.title for k in self.db.all(TimeEntry) if k.parent_id == e.id]
            self.subs.setItems([{"text": k, "done": True} for k in kids]); self.subs.list.setEnabled(False); self.subs.edit.setPlaceholderText(S["subs_existing"])

    def values(self) -> tf.TaskValues:
        rec_until = self.rec_until.value()
        rec = {"type": self.rec_type.currentData(), "interval": self.rec_interval.value(), "until": rec_until.isoformat() if rec_until else None} if self.rec_type.currentData() else {}
        rate = self.rate.value()
        return tf.TaskValues(
            title=self.title.text(), description=self.desc.toPlainText(), project_id=self.project.currentData(), category=self.category.currentData() or "general",
            subcategory=self.subcategory.currentText().strip(), priority=self.priority.value(), column=self.column.value(), tags=self.tags.tags(),
            assignee=self.assignee.currentData() or "", color=self.color.color(), icon=self.icon_pick.icon(), all_day=self.all_day.isChecked(),
            start=self.start.value(), end=self.end.value(), due=self.due.value(), estimated_min=self.estimate.minutes(), energy=self.energy.value() or 0,
            location=self.location.currentData() or "", billable=self.billable.isChecked(), rate=rate if rate > 0 else None, start_timer_now=self.timer_now.isChecked(),
            checklist=self.checklist.items(), subtasks=[] if self.entry else [c["text"] for c in self.subs.items() if c["text"]],
            depends_on=[self.deps.item(i).data(Qt.UserRole) for i in range(self.deps.count()) if self.deps.item(i).checkState() == Qt.Checked],
            progress=self.progress.value(), notes=self.notes.toPlainText(), attachments=[self.attach.item(i).text() for i in range(self.attach.count())],
            recurrence=rec, reminders=[self.reminders.item(i).data(Qt.UserRole) for i in range(self.reminders.count()) if self.reminders.item(i).checkState() == Qt.Checked],
            important=self.important.isChecked())

    _FIELD_TAB = {"title": 0, "priority": 0, "column": 0, "start": 1, "end": 1, "due": 1, "estimated_min": 1, "energy": 1, "rate": 1, "start_timer_now": 1,
                  "checklist": 2, "progress": 2, "recurrence": 3, "reminders": 3}

    def _save(self, again: bool) -> None:
        self.clear_error()
        for name, f in (("start", self.start), ("end", self.end), ("due", self.due)):
            if not f.isValid():
                self.tabs.setValue(1); self.show_error(S["bad_date"]); return
        v = self.values()
        errors = tf.validate(v)
        if errors:
            field, msg = next(iter(errors.items()))
            self.tabs.setValue(self._FIELD_TAB.get(field, 0)); self.show_error(msg); return
        try:
            self.saved = tf.apply(self.db, v, entry=self.entry)
        except Exception as exc:  # noqa: BLE001 - show it in the dialog instead of crashing
            log.exception("task save failed"); self.show_error(str(exc)); return
        if self.theme.fx is not None:
            self.theme.fx.play("success")
        if again:
            self.win.refresh_all(); self.title.clear(); self.subs.setItems([]); self.checklist.setItems([]); self.title.setFocus(); self.tabs.setValue(0); self.win.toast(S["saved_new"])
            return
        self.accept()

    def _split_task(self) -> None:
        from .lists_ui import SplitTaskDialog
        dlg = SplitTaskDialog(self.win, self.entry)
        if dlg.exec_():
            self.win.refresh_all(); self.win.toast(S["saved"])

    def _delete(self) -> None:
        if self.entry and confirm(self, S["confirm_delete"]):
            self.db.delete(TimeEntry, self.entry.id); self.saved = None; self.deleted = True; self.accept()


# ====================================================================================== PROJECT
class ProjectDialog(PopDialog):
    def __init__(self, win, project: Optional[Project] = None) -> None:
        super().__init__(win, S["edit_project"] if project else S["new_project"], "projects", 820)
        self.project, self.saved = project, None
        db = self.db
        self.name = QLineEdit(placeholderText=S["name"]); self.code = QLineEdit(placeholderText="PRJ-001")
        self.icon_pick = IconPicker(); self.color = ColorSwatches(allow_none=False); self.desc = QPlainTextEdit(); self.desc.setFixedHeight(80)
        self.client = _combo([(S["no_client"], None)] + [(c.name, c.id) for c in db.all(Client, "name")]); newc = chip_button(S["new_client"]); newc.clicked.connect(self._new_client)
        self.status = _combo([(S["ps_" + s.value], s.value) for s in ProjectStatus]); self.priority = PriorityPicker()
        self.start = DateTimeField(with_time=False); self.deadline = DateTimeField(with_time=False)
        self.est = QDoubleSpinBox(); self.est.setRange(0, 100000); self.est.setSuffix(" " + S["hours"]); self.budget = QDoubleSpinBox(); self.budget.setRange(0, 1e13); self.budget.setGroupSeparatorShown(True)
        self.rate = QDoubleSpinBox(); self.rate.setRange(0, 1e12); self.rate.setGroupSeparatorShown(True)
        self.currency = _combo([("IRR ریال", "IRR"), ("USD", "USD"), ("EUR", "EUR")])
        self.tags = ChipInput(); self.notes = QPlainTextEdit(); self.notes.setFixedHeight(70)
        self.members = QListWidget(); self.members.setFixedHeight(100)
        for m in db.all(Member):
            it = QListWidgetItem(m.name); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, m.id); self.members.addItem(it)
        self.deps = QListWidget(); self.deps.setFixedHeight(100)
        for p in db.all(Project, "name"):
            if not project or p.id != project.id:
                it = QListWidgetItem(p.name); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked); it.setData(Qt.UserRole, p.id); self.deps.addItem(it)
        a = Section(S["sec_basic"]); a.pair(S["name"], self.name, S["code"], self.code); a.add(S["description"], self.desc)
        crow = QWidget(); cl = QHBoxLayout(crow); cl.setContentsMargins(0, 0, 0, 0); cl.addWidget(self.client, 1); cl.addWidget(newc); a.add(S["client"], crow)
        b = Section(S["sec_look"]); b.add(S["icon"], self.icon_pick); b.add(S["color"], self.color)
        c = Section(S["sec_status"]); c.pair(S["status"], self.status, S["currency"], self.currency); c.add(S["priority"], self.priority); c.pair(S["start"], self.start, S["deadline"], self.deadline); c.add(S["tags"], self.tags)
        d = Section(S["sec_money"]); d.pair(S["est_hours"], self.est, S["budget"], self.budget); d.add(S["hourly_rate"], self.rate)
        e = Section(S["sec_team"]); e.add(S["members"], self.members); e.add(S["depends_on_projects"], self.deps); e.add(S["notes"], self.notes)
        self.body.addWidget(self.scroll_page(a, b, c, d, e), 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject); ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save)
        if project:
            dl = GlassButton(S["delete"], self.theme, danger=True, icon="trash"); dl.clicked.connect(self._delete); self.footer.addWidget(dl)
        self.buttons(cancel, ok)
        self._load(project)

    def _new_client(self) -> None:
        dlg = ClientDialog(self.win)
        if dlg.exec_() and dlg.saved:
            self.client.addItem(dlg.saved.name, dlg.saved.id); self.client.setCurrentIndex(self.client.count() - 1)

    def _load(self, p: Optional[Project]) -> None:
        if p is None:
            n = len(self.db.all(Project)) + 1
            self.code.setText(f"PRJ-{n:03d}"); self.icon_pick.setIcon("📁"); self.color.setColor("#6D5DFC"); return
        self.name.setText(p.name); self.code.setText(p.code); self.desc.setPlainText(p.description); self.icon_pick.setIcon(p.icon); self.color.setColor(p.color)
        self.client.setCurrentIndex(max(0, self.client.findData(p.client_id))); self.status.setCurrentIndex(max(0, self.status.findData(p.status.value)))
        self.priority.setValue(p.priority, emit=False); self.start.setValue(p.start); self.deadline.setValue(p.deadline)
        self.est.setValue(p.estimated_hours); self.budget.setValue(p.budget); self.rate.setValue(p.rate_per_hour); self.currency.setCurrentIndex(max(0, self.currency.findData(p.currency)))
        self.tags.setTags(p.tags); self.notes.setPlainText(p.notes)
        for lst, ids in ((self.members, p.team_members), (self.deps, p.dependencies)):
            for i in range(lst.count()):
                lst.item(i).setCheckState(Qt.Checked if lst.item(i).data(Qt.UserRole) in ids else Qt.Unchecked)

    def _save(self) -> None:
        self.clear_error()
        name = self.name.text().strip()
        if not name:
            self.show_error(S["need_title"]); return
        if not (self.start.isValid() and self.deadline.isValid()):
            self.show_error(S["bad_date"]); return
        try:
            p = self.project or Project(name=name)
            p.name, p.code, p.description, p.icon, p.color = name, self.code.text().strip(), self.desc.toPlainText(), self.icon_pick.icon() or "📁", self.color.color() or "#6D5DFC"
            p.client_id, p.status, p.priority = self.client.currentData(), ProjectStatus(self.status.currentData() or "active"), self.priority.value()
            p.start, p.deadline = self.start.value(), self.deadline.value()
            if p.start and p.deadline and p.deadline < p.start:
                self.show_error(S["deadline_before_start"]); return
            p.estimated_hours, p.budget, p.rate_per_hour, p.currency = self.est.value(), self.budget.value(), self.rate.value(), self.currency.currentData() or "IRR"
            p.tags, p.notes = self.tags.tags(), self.notes.toPlainText()
            p.team_members = [self.members.item(i).data(Qt.UserRole) for i in range(self.members.count()) if self.members.item(i).checkState() == Qt.Checked]
            p.dependencies = [self.deps.item(i).data(Qt.UserRole) for i in range(self.deps.count()) if self.deps.item(i).checkState() == Qt.Checked]
            self.db.save(p); self.saved = p
        except ValueError as exc:
            self.show_error(str(exc)); return
        self.accept()

    def _delete(self) -> None:
        if self.project and confirm(self, S["confirm_delete_project"]):
            self.db.delete(Project, self.project.id); self.saved = None; self.deleted = True; self.accept()


# ====================================================================================== HABIT
class HabitDialog(PopDialog):
    def __init__(self, win, habit: Optional[Habit] = None) -> None:
        super().__init__(win, S["edit_habit"] if habit else S["new_habit"], "habits", 640)
        self.habit, self.saved = habit, None
        self.name = QLineEdit(placeholderText=S["habit_name_hint"]); self.note = QPlainTextEdit(); self.note.setFixedHeight(70); self.note.setPlaceholderText(S["habit_note_hint"])
        self.icon_pick = IconPicker(); self.color = ColorSwatches(allow_none=False)
        self.target = QSlider(Qt.Horizontal); self.target.setRange(1, 7); self.target_lbl = QLabel(); self.target.valueChanged.connect(lambda v: self.target_lbl.setText(to_fa_digits(f"{v} {S['times_per_week']}")))
        self.days = Segmented([(d, i) for i, d in enumerate(("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"))])
        self.selected_days: set = set(range(7))
        self.days_row = QWidget(); fl = FlowLayout(self.days_row); self._day_btns = []
        for i, name in enumerate(("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")):
            b = chip_button(name, True); b.setChecked(True); b.clicked.connect(lambda _c=False, k=i, bb=b: self._toggle_day(k, bb.isChecked())); fl.addWidget(b); self._day_btns.append(b)
        a = Section(S["sec_basic"]); a.add(S["name"], self.name); a.add(S["notes"], self.note)
        b = Section(S["sec_look"]); b.add(S["icon"], self.icon_pick); b.add(S["color"], self.color)
        row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(self.target, 1); rl.addWidget(self.target_lbl)
        c = Section(S["sec_schedule"]); c.add(S["weekly_target"], row); c.add(S["active_days"], self.days_row)
        self.body.addWidget(self.scroll_page(a, b, c), 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject); ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save)
        if habit:
            dl = GlassButton(S["delete"], self.theme, danger=True, icon="trash"); dl.clicked.connect(self._delete); self.footer.addWidget(dl)
        self.buttons(cancel, ok)
        if habit:
            self.name.setText(habit.name); self.note.setPlainText(habit.note); self.icon_pick.setIcon(habit.icon); self.color.setColor(habit.color); self.target.setValue(habit.target_per_week)
            self.selected_days = set(habit.days)
            for i, bt in enumerate(self._day_btns):
                bt.setChecked(i in self.selected_days)
        else:
            self.icon_pick.setIcon("💧"); self.color.setColor("#00E5FF"); self.target.setValue(7)
        self.target_lbl.setText(to_fa_digits(f"{self.target.value()} {S['times_per_week']}"))

    def _toggle_day(self, k: int, on: bool) -> None:
        (self.selected_days.add if on else self.selected_days.discard)(k)

    def _save(self) -> None:
        n = self.name.text().strip()
        if not n:
            self.show_error(S["need_title"]); return
        if not self.selected_days:
            self.show_error(S["pick_a_day"]); return
        h = self.habit or Habit(name=n)
        h.name, h.note, h.icon, h.color, h.target_per_week, h.days = n, self.note.toPlainText(), self.icon_pick.icon() or "💧", self.color.color() or "#00E5FF", self.target.value(), sorted(self.selected_days)
        self.db.save(h); self.saved = h; self.accept()

    def _delete(self) -> None:
        if self.habit and confirm(self, S["confirm_delete"]):
            self.db.delete(Habit, self.habit.id); self.deleted = True; self.accept()


# ====================================================================================== CLIENT / MEMBER / GOAL
class ClientDialog(PopDialog):
    def __init__(self, win, client: Optional[Client] = None) -> None:
        super().__init__(win, S["edit_client"] if client else S["new_client"], "billing", 620)
        self.client, self.saved = client, None
        self.name = QLineEdit(); self.company = QLineEdit(); self.email = QLineEdit(); self.phone = QLineEdit(); self.address = QPlainTextEdit(); self.address.setFixedHeight(64)
        self.rate = QDoubleSpinBox(); self.rate.setRange(0, 1e12); self.rate.setGroupSeparatorShown(True); self.currency = _combo([("IRR ریال", "IRR"), ("USD", "USD"), ("EUR", "EUR")])
        self.tags = ChipInput(); self.notes = QPlainTextEdit(); self.notes.setFixedHeight(64)
        a = Section(S["sec_basic"]); a.pair(S["name"], self.name, S["company"], self.company); a.pair(S["email"], self.email, S["phone"], self.phone); a.add(S["address"], self.address)
        b = Section(S["sec_money"]); b.pair(S["hourly_rate"], self.rate, S["currency"], self.currency); b.add(S["tags"], self.tags); b.add(S["notes"], self.notes)
        self.body.addWidget(self.scroll_page(a, b), 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject); ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save); self.buttons(cancel, ok)
        if client:
            self.name.setText(client.name); self.company.setText(client.company); self.email.setText(client.email); self.phone.setText(client.phone); self.address.setPlainText(client.address)
            self.rate.setValue(client.default_rate); self.currency.setCurrentIndex(max(0, self.currency.findData(client.currency))); self.tags.setTags(client.tags); self.notes.setPlainText(client.notes)

    def _save(self) -> None:
        if not self.name.text().strip():
            self.show_error(S["need_title"]); return
        em = self.email.text().strip()
        if em and ("@" not in em or "." not in em.split("@")[-1]):
            self.show_error(S["bad_email"]); return
        c = self.client or Client(name=self.name.text().strip())
        c.name, c.company, c.email, c.phone, c.address = self.name.text().strip(), self.company.text().strip(), em, self.phone.text().strip(), self.address.toPlainText()
        c.default_rate, c.currency, c.tags, c.notes = self.rate.value(), self.currency.currentData() or "IRR", self.tags.tags(), self.notes.toPlainText()
        self.db.save(c); self.saved = c; self.accept()


class MemberDialog(PopDialog):
    def __init__(self, win, member: Optional[Member] = None) -> None:
        super().__init__(win, S["new_member"], "team", 560)
        self.member, self.saved = member, None
        self.name = QLineEdit(placeholderText=S["handle_hint"]); self.role = QLineEdit(); self.email = QLineEdit(); self.cost = QDoubleSpinBox(); self.cost.setRange(0, 1e12); self.color = ColorSwatches(allow_none=False)
        a = Section(S["sec_basic"]); a.pair(S["handle"], self.name, S["role"], self.role); a.pair(S["email"], self.email, S["hourly_cost"], self.cost); a.add(S["color"], self.color)
        self.body.addWidget(a)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject); ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save); self.buttons(cancel, ok)
        self.color.setColor("#00E5FF")

    def _save(self) -> None:
        from ..services.team import Team
        try:
            self.saved = Team(self.db).add_member(self.name.text(), role=self.role.text().strip(), email=self.email.text().strip(), color=self.color.color() or "#00E5FF", hourly_cost=self.cost.value())
        except ValueError as exc:
            self.show_error(str(exc)); return
        self.accept()


class GoalDialog(PopDialog):
    def __init__(self, win, goal: Optional[Goal] = None) -> None:
        super().__init__(win, S["new_goal"], "goals", 700)
        self.goal, self.saved = goal, None
        self.name = QLineEdit(placeholderText=S["goal_name"]); self.deadline = DateTimeField(with_time=False); self.notes = QPlainTextEdit(); self.notes.setFixedHeight(60)
        self.kr_name = QLineEdit(placeholderText=S["kr_name"]); self.kr_target = QDoubleSpinBox(); self.kr_target.setRange(0, 1e9); self.kr_cur = QDoubleSpinBox(); self.kr_cur.setRange(0, 1e9); self.kr_unit = QLineEdit(placeholderText=S["unit"])
        self.krs = QListWidget(); self.krs.setMinimumHeight(110); self._items: List[Dict[str, Any]] = []
        add = chip_button(S["add"]); add.clicked.connect(self._add_kr); rm = chip_button(S["remove"]); rm.clicked.connect(self._rm_kr)
        a = Section(S["sec_basic"]); a.add(S["goal_name"], self.name); a.add(S["deadline"], self.deadline); a.add(S["notes"], self.notes)
        b = Section(S["key_results"]); b.add("", self.krs); b.pair(S["kr_name"], self.kr_name, S["unit"], self.kr_unit); b.pair(S["target"], self.kr_target, S["current"], self.kr_cur)
        r = QWidget(); rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(add); rl.addWidget(rm); rl.addStretch(); b.add("", r)
        self.body.addWidget(self.scroll_page(a, b), 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject); ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save); self.buttons(cancel, ok)
        if goal:
            self.name.setText(goal.name); self.deadline.setValue(goal.deadline); self.notes.setPlainText(goal.notes); self._items = [dict(k) for k in goal.key_results]; self._redraw()

    def _redraw(self) -> None:
        self.krs.clear()
        for k in self._items:
            self.krs.addItem(to_fa_digits(f"{k['name']}: {k.get('current', 0)} / {k['target']} {k.get('unit', '')}"))

    def _add_kr(self) -> None:
        n = self.kr_name.text().strip() or f"KR{len(self._items) + 1}"
        if self.kr_target.value() <= 0:
            self.show_error(S["kr_target_positive"]); return
        self._items.append({"name": n, "target": self.kr_target.value(), "current": self.kr_cur.value(), "unit": self.kr_unit.text().strip()}); self._redraw(); self.kr_name.clear(); self.clear_error()

    def _rm_kr(self) -> None:
        r = self.krs.currentRow()
        if 0 <= r < len(self._items):
            self._items.pop(r); self._redraw()

    def _save(self) -> None:
        if not self.name.text().strip():
            self.show_error(S["need_title"]); return
        g = self.goal or Goal(name=self.name.text().strip())
        g.name, g.key_results, g.deadline, g.notes = self.name.text().strip(), self._items, self.deadline.value(), self.notes.toPlainText()
        problems = smart2.validate_smart(g)
        self.db.save(g); self.saved = g; self.smart_problems = problems; self.accept()


# ====================================================================================== THE NAG: "what did you do?"
class WorkReportDialog(PopDialog):
    """Pops over every other program at the configured interval and asks you to account for the unlogged time."""

    def __init__(self, win, prompter, suggestion: Dict[str, Any], screenshot_bytes: Optional[bytes] = None) -> None:
        super().__init__(win, S["report_title"], "bell", 700, top=True, closable=not prompter.cfg.forced)
        self.prompter, self.sug, self.result = prompter, suggestion, None
        start, end = suggestion["from"], suggestion["to"]
        info = QLabel(to_fa_digits(S["report_gap"].format(a=to_tehran(start).strftime("%H:%M"), b=to_tehran(end).strftime("%H:%M"), m=suggestion["minutes"])))
        info.setProperty("accent", True); info.setWordWrap(True); self.body.addWidget(info)
        if "engaged_min" in suggestion:                              # measured by the hourly ledger, not guessed
            m = QLabel(to_fa_digits(S["report_measured"].format(e=suggestion["engaged_min"], l=suggestion["logged_min"], u=suggestion["minutes"])))
            m.setProperty("muted", True); m.setWordWrap(True); self.body.addWidget(m)
        if suggestion.get("apps"):
            apps = QWidget(); fl = FlowLayout(apps)
            for app, sec in suggestion["apps"]:
                b = chip_button(to_fa_digits(f"{app.replace('.exe', '')} · {max(1, sec // 60)} {S['min']}")); b.clicked.connect(lambda _c=False, a=app: self.title.setText(self.title.text() or f"کار با {a.replace('.exe', '')}")); fl.addWidget(b)
            self.body.addWidget(apps)
        if screenshot_bytes:
            from PyQt5.QtGui import QPixmap
            pm = QPixmap(); pm.loadFromData(screenshot_bytes)
            if not pm.isNull():
                th = QLabel(); th.setPixmap(pm.scaledToWidth(260, Qt.SmoothTransformation)); th.setAlignment(Qt.AlignCenter); self.body.addWidget(th)
        self.title = QLineEdit(placeholderText=S["report_what"]); self.title.setText(str(suggestion.get("title_hint", "")))
        db = self.db
        self.project = _combo([(S["no_project"], None)] + [(f"{p.icon} {p.name}", p.id) for p in db.all(Project, "name")])
        last = db.conn.execute("SELECT project_id FROM entries WHERE project_id IS NOT NULL ORDER BY start_utc DESC LIMIT 1").fetchone()
        if last:
            self.project.setCurrentIndex(max(0, self.project.findData(last[0])))
        cats = taxonomy.categories(db.get_setting("custom_categories", {}))
        self.category = _combo([(f"{v.get('icon', '📋')}  {v['name']}", k) for k, v in cats.items()], suggestion.get("category"))
        self.minutes = DurationEdit((15, 30, 45, 60)); self.minutes.setMinutes(int(suggestion["minutes"]))
        self.tags = ChipInput(); self.notes = QPlainTextEdit(); self.notes.setPlaceholderText(S["notes"]); self.notes.setFixedHeight(60)
        a = Section(""); a.add(S["report_what"], self.title); a.pair(S["project"], self.project, S["category"], self.category); a.add(S["duration"], self.minutes); a.add(S["tags"], self.tags); a.add(S["notes"], self.notes)
        self.body.addWidget(a)
        ok = GlassButton(S["report_log"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._log)
        away = GlassButton(S["report_away"], self.theme, icon="moon"); away.clicked.connect(self._away)
        same = GlassButton(S["report_same"], self.theme, icon="refresh"); same.clicked.connect(self._same_as_previous); self.footer.addWidget(same)
        self.buttons(away, ok)
        if prompter.can_snooze():
            sn = GlassButton(S["report_snooze"].format(m=prompter.cfg.snooze_min), self.theme, icon="clock"); sn.clicked.connect(self._snooze); self.footer.insertWidget(0, sn)
        if prompter.cfg.forced:
            f = QLabel(S["report_forced"]); f.setStyleSheet("color:#FFB020;background:transparent;"); self.body.addWidget(f)
        self.title.setFocus()

    def _same_as_previous(self) -> None:
        """One click: continue what you logged last (title, project, category, tags)."""
        r = self.db.conn.execute("SELECT title, project_id, category, tags FROM entries WHERE status='done' AND source!='auto' ORDER BY end_utc DESC LIMIT 1").fetchone()
        if r is None:
            return
        import json as _json
        self.title.setText(r[0]); self.project.setCurrentIndex(max(0, self.project.findData(r[1]))); self.category.setCurrentIndex(max(0, self.category.findData(r[2])))
        try:
            self.tags.setTags(_json.loads(r[3] or "[]"))
        except ValueError:
            pass

    def _log(self) -> None:
        t = self.title.text().strip()
        if not t:
            self.show_error(S["need_title"]); return
        mins = self.minutes.minutes()
        if mins <= 0:
            self.show_error(S["bad_duration"]); return
        if "hour_start" in self.sug:                                  # an hour-aligned prompt: put the work into the real free slot of that hour
            start = self.sug["from"]
            end = min(start + dt.timedelta(minutes=mins), self.sug["hour_start"] + dt.timedelta(hours=1))
            if end <= start:
                start, end = self.sug["hour_start"], self.sug["hour_start"] + dt.timedelta(minutes=mins)
        else:
            end = self.sug["to"]
            start = end - dt.timedelta(minutes=mins)
        e = TimeEntry(title=t, start_utc=start, end_utc=end, project_id=self.project.currentData(), category=self.category.currentData() or "general", tags=self.tags.tags(),
                      notes=self.notes.toPlainText(), source="prompt", status=Status.DONE, column="done", completed_at=end)
        self.db.save(e)
        self.prompter.answer("logged", e.id); self.outcome = "logged"; self.accept()

    def _away(self) -> None:
        self.prompter.answer("away"); self.outcome = "away"; self.accept()

    def _snooze(self) -> None:
        self.prompter.snooze(); self.outcome = "snoozed"; self.reject()

    def reject(self) -> None:
        if self.outcome is None and not self.prompter.cfg.forced:
            self.prompter.answer("skipped"); self.outcome = "skipped"
        super().reject()
