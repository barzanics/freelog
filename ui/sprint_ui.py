"""Sprint screens: create / assign / start / complete with carry-over, plus a live burndown chart. All rules are in ``services.sprints``."""
from __future__ import annotations

import datetime as dt
import logging
from typing import List, Optional

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QSpinBox, QWidget

from ..core.models import Project, Sprint, Status, TimeEntry
from ..core.persian import format_jalali, now_utc, to_fa_digits, to_tehran, tr
from ..services import sprints as svc
from .dialogs import PopDialog
from .forms import DateTimeField, Section, Segmented
from .glass import GlassButton, qcolor, Theme
from .strings import S

log = logging.getLogger("worktracker.sprint_ui")
STATUS_KEY = {"planning": "sp_st_planning", "active": "sp_st_active", "completed": "sp_st_completed"}


class BurndownChart(QWidget):
    """Remaining hours per day: dashed ideal line vs solid actual line (mirrored for right-to-left layouts)."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.days: List[dt.date] = []
        self.ideal: List[float] = []
        self.actual: List[Optional[float]] = []
        self.setMinimumHeight(150)

    def set_data(self, days, ideal, actual) -> None:
        self.days, self.ideal, self.actual = list(days), list(ideal), list(actual)
        self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if len(self.days) < 2:
            p.setPen(self.theme.text(True)); p.drawText(self.rect(), Qt.AlignCenter, S["sp_pick"]); return
        l, t, r, b = 34.0, 10.0, 12.0, 24.0
        w, h = self.width() - l - r, self.height() - t - b
        top = max(max(self.ideal, default=0), max((a for a in self.actual if a is not None), default=0), 0.5)
        rtl = self.layoutDirection() == Qt.RightToLeft
        n = len(self.days) - 1

        def pt(i: int, v: float) -> QPointF:
            x = (n - i if rtl else i) / n * w + l
            return QPointF(x, t + h * (1 - v / top))

        p.setPen(QPen(qcolor("#FFFFFF" if self.theme.dark else "#6A6A90", 40), 1))
        for k in range(4):
            y = t + h * k / 3; p.drawLine(QPointF(l, y), QPointF(l + w, y))
        p.setPen(self.theme.text(True))
        p.drawText(QRectF(0, t - 6, l - 4, 14), Qt.AlignRight | Qt.AlignVCenter, to_fa_digits(f"{top:.0f}h"))
        p.drawText(QRectF(0, t + h - 7, l - 4, 14), Qt.AlignRight | Qt.AlignVCenter, "0")
        dash = QPen(qcolor(self.theme.accents[2], 200), 1.8, Qt.DashLine)
        p.setPen(dash)
        path = QPainterPath(pt(0, self.ideal[0]))
        for i in range(1, len(self.ideal)):
            path.lineTo(pt(i, self.ideal[i]))
        p.setBrush(Qt.NoBrush); p.drawPath(path)
        pts = [(i, a) for i, a in enumerate(self.actual) if a is not None]
        if pts:
            p.setPen(QPen(qcolor(self.theme.accents[1], 240), 2.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            line = QPainterPath(pt(*pts[0]))
            for i, a in pts[1:]:
                line.lineTo(pt(i, a))
            p.drawPath(line)
            p.setBrush(qcolor(self.theme.accents[1], 255)); p.setPen(Qt.NoPen)
            for i, a in pts:
                p.drawEllipse(pt(i, a), 3.2, 3.2)
        p.setPen(self.theme.text(True))
        for i in (0, n):
            x = pt(i, 0).x()
            p.drawText(QRectF(x - 30, self.height() - b + 4, 60, 16), Qt.AlignCenter, to_fa_digits(format_jalali(self.days[i], "{m:02d}/{d:02d}", fa_digits=False) if True else ""))


# ======================================================================= dialogs
class SprintDialog(PopDialog):
    def __init__(self, win, project_id: str) -> None:
        super().__init__(win, S["sp_new"], "pm", 560)
        self.project_id, self.saved = project_id, None
        n = len(svc.for_project(win.db, project_id)) + 1
        self.name = QLineEdit(); self.name.setText(f"Sprint {n}"); self.goal = QLineEdit(placeholderText=S["sp_goal"])
        self.start = DateTimeField(with_time=False); self.start.setValue(now_utc())
        self.days = QSpinBox(); self.days.setRange(1, 60); self.days.setValue(14); self.days.setSuffix(" " + S["days"])
        self.cap = QDoubleSpinBox(); self.cap.setRange(0, 5000); self.cap.setSuffix(" h"); self.cap.setSpecialValueText(S["no_limit"])
        sec = Section(S["sec_basic"]); sec.add(S["name"], self.name); sec.add(S["sp_goal"], self.goal)
        sec.pair(S["sp_start_date"], self.start, S["sp_days"], self.days); sec.add(S["sp_capacity"], self.cap)
        self.body.addWidget(sec)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save); self.buttons(cancel, ok)

    def _save(self) -> None:
        if not self.start.isValid() or self.start.value() is None:
            self.show_error(S["bad_date"]); return
        try:
            self.saved = svc.create(self.db, self.project_id, self.name.text(), to_tehran(self.start.value()).date(), self.days.value(), self.goal.text(), self.cap.value())
        except svc.SprintError as exc:
            self.show_error(str(exc)); return
        self.accept()


class AssignDialog(PopDialog):
    def __init__(self, win, sprint: Sprint) -> None:
        super().__init__(win, S["sp_assign"], "tasks", 600)
        self.sprint = sprint
        self.lst = QListWidget(); self.lst.setMinimumHeight(260)
        for r in win.db.conn.execute("SELECT * FROM entries WHERE project_id=? AND parent_id IS NULL AND column NOT IN ('done','cancelled') AND (sprint_id IS NULL OR sprint_id=?) ORDER BY priority, rank",
                                     (sprint.project_id, sprint.id)):
            e = TimeEntry.from_row(r)
            it = QListWidgetItem(to_fa_digits(f"{e.title}   ({(e.estimated_min or 0) / 60:.1f}h)"))
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked if e.sprint_id == sprint.id else Qt.Unchecked); it.setData(Qt.UserRole, e.id); self.lst.addItem(it)
        self.body.addWidget(win.label(S["sp_assign_hint"], 9, muted=True)); self.body.addWidget(self.lst, 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self.accept); self.buttons(cancel, ok)

    def apply(self) -> None:
        on = [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count()) if self.lst.item(i).checkState() == Qt.Checked]
        off = [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count()) if self.lst.item(i).checkState() != Qt.Checked]
        svc.unassign(self.db, [i for i in off if (self.db.get(TimeEntry, i) or TimeEntry(title="", start_utc=now_utc())).sprint_id == self.sprint.id])
        svc.assign(self.db, self.sprint.id, on)


class CompleteDialog(PopDialog):
    def __init__(self, win, sprint: Sprint) -> None:
        super().__init__(win, S["sp_complete"], "check", 560)
        st = svc.stats(win.db, sprint.id)
        self.body.addWidget(win.label(to_fa_digits(f"{S['sp_done']}: {st['done_tasks']}/{st['tasks']}   ·   {st['completed_hours']}/{st['committed_hours']} h"), 11))
        self.carry = Segmented([(S["sp_carry_backlog"], "backlog"), (S["sp_carry_next"], "next"), (S["sp_carry_keep"], "keep")], wrap=False)
        self.nxt = QComboBox()
        for s in svc.for_project(win.db, sprint.project_id):
            if s.id != sprint.id and s.status != "completed":
                self.nxt.addItem(s.name, s.id)
        sec = Section(S["sp_carry"]); sec.add(S["sp_carry_what"], self.carry); sec.add(S["sp_next"], self.nxt); self.body.addWidget(sec)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["sp_complete"], self.theme, primary=True, icon="check"); ok.clicked.connect(self.accept); self.buttons(cancel, ok)


# ======================================================================= flows used by the PM page
def _selected(win) -> Optional[Sprint]:
    it = win.pm_sp_list.currentItem()
    return win.db.get(Sprint, it.data(Qt.UserRole)) if it is not None and it.data(Qt.UserRole) else None


def _notify(win, text: str) -> None:
    win.toast(text)


def new_sprint(win) -> Optional[Sprint]:
    pid = win.pm_project.currentData()
    if not pid:
        _notify(win, S["sp_need_project"]); return None
    dlg = SprintDialog(win, pid)
    if dlg.exec_() and dlg.saved:
        refresh_sprints(win, pid); return dlg.saved
    return None


def assign_tasks(win) -> None:
    sp = _selected(win)
    if sp is None:
        _notify(win, S["sp_pick"]); return
    dlg = AssignDialog(win, sp)
    if dlg.exec_():
        try:
            dlg.apply()
        except svc.SprintError as exc:
            _notify(win, str(exc))
        refresh_sprints(win, sp.project_id)


def start_sprint(win) -> None:
    sp = _selected(win)
    if sp is None:
        _notify(win, S["sp_pick"]); return
    try:
        svc.start(win.db, sp.id)
        if win.theme.fx is not None:
            win.theme.fx.play("success")
    except svc.SprintError as exc:
        _notify(win, str(exc))
    refresh_sprints(win, sp.project_id)


def complete_sprint(win) -> None:
    sp = _selected(win)
    if sp is None:
        _notify(win, S["sp_pick"]); return
    if sp.status != "active":
        _notify(win, S["sp_only_active"]); return
    dlg = CompleteDialog(win, sp)
    if dlg.exec_():
        try:
            r = svc.complete(win.db, sp.id, dlg.carry.value(), dlg.nxt.currentData())
            _notify(win, to_fa_digits(f"{S['sp_closed']} · {S['sp_velocity']}: {r['velocity_hours']} h · {S['sp_carried']}: {r['carried']}"))
        except svc.SprintError as exc:
            _notify(win, str(exc))
        win.refresh_all()


def refresh_sprints(win, pid: Optional[str]) -> None:
    keep = win.pm_sp_list.currentItem().data(Qt.UserRole) if win.pm_sp_list.currentItem() is not None else None
    win.pm_sp_list.clear()
    if not pid:
        win.pm_sp_chart.set_data([], [], []); win.pm_sp_info.setText(""); return
    row = 0
    for i, sp in enumerate(svc.for_project(win.db, pid)):
        st = svc.stats(win.db, sp.id)
        txt = to_fa_digits(f"{sp.name}  ·  {S[STATUS_KEY.get(sp.status, 'sp_st_planning')]}  ·  {st['completed_hours']}/{st['committed_hours']}h" + ("  ⚠" if st["over_capacity"] else ""))
        it = QListWidgetItem(txt); it.setData(Qt.UserRole, sp.id); win.pm_sp_list.addItem(it)
        if sp.id == keep:
            row = i
    if win.pm_sp_list.count():
        win.pm_sp_list.setCurrentRow(row)
    refresh_burndown(win)


def refresh_burndown(win) -> None:
    sp = _selected(win)
    if sp is None:
        win.pm_sp_chart.set_data([], [], []); win.pm_sp_info.setText(S["sp_pick"] if not win.pm_sp_list.count() else ""); return
    b = svc.burndown(win.db, sp.id)
    win.pm_sp_chart.set_data(b["days"], b["ideal"], b["actual"])
    st = svc.stats(win.db, sp.id)
    fc = svc.sprints_needed(win.db, sp.project_id)
    bits = [f"{S['sp_progress']}: {st['progress_pct']}%", f"{S['sp_velocity']}: {svc.average_velocity(win.db, sp.project_id)} h"]
    if st["capacity_pct"] is not None:
        bits.append(f"{S['sp_capacity']}: {st['capacity_pct']}%" + (" ⚠" if st["over_capacity"] else ""))
    if fc is not None:
        bits.append(f"{S['sp_forecast']}: {fc}")
    if sp.goal:
        bits.insert(0, "🎯 " + sp.goal)
    win.pm_sp_info.setText(to_fa_digits("   ·   ".join(bits)))
