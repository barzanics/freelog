"""Project-management screens (Gantt/milestones/sprints/subtasks), Eisenhower matrix, Tools hub, ambient & detached windows."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QMessageBox, QPlainTextEdit, QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from ..core.models import Client, Goal, Milestone, Project, Sprint, Status, Template, TimeEntry
from ..core.persian import date_to_jalali, format_jalali, now_utc, parse_jalali, to_en_digits, to_fa_digits, to_tehran
from ..services import blueprints, bulk, extras, metrics, planner as planner_svc, recurring, reports, smart2
from ..services.habits import update_key_result
from ..services.insights import sankey
from ..services.projects import ProjectService
from . import sprint_ui as su
from .glass import GanttWidget, GlassButton, Ring, SankeyWidget
from .strings import S

log = logging.getLogger("worktracker.ui.pm")


def parse_date(text: str) -> dt.date:
    """``YYYY-MM-DD`` (Gregorian) or ``YYYY/MM/DD`` with year < 1700 (Jalali, Persian or Latin digits)."""
    t = to_en_digits(text).strip().replace("-", "/")
    y = int(t.split("/")[0])
    return parse_jalali(t) if y < 1700 else dt.date(*(int(x) for x in t.split("/")))


def _item(text: str, uid: Optional[str] = None):
    from PyQt5.QtWidgets import QListWidgetItem
    it = QListWidgetItem(text)
    if uid is not None:
        it.setData(Qt.UserRole, uid)
    return it


def _guard(win, fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - UI boundary
        log.exception("tools action failed")
        QMessageBox.warning(win, S["error"], str(exc))


def _btn(win, text: str, fn: Callable[[], None], primary: bool = False) -> GlassButton:
    b = GlassButton(text, win.theme, primary=primary)
    b.clicked.connect(lambda _c=False: _guard(win, fn))
    return b


def _row(*widgets) -> QHBoxLayout:
    h = QHBoxLayout()
    for w in widgets:
        h.addWidget(w, 1 if isinstance(w, (QLineEdit, QComboBox, QPlainTextEdit)) else 0)
    return h


# ====================================================================== PM page
def build_pm(win) -> None:
    page = QWidget(); page.setStyleSheet(win._field_style()); lay = QVBoxLayout(page)
    win.pm_project = QComboBox(); win.pm_project.currentIndexChanged.connect(lambda _i=0: refresh_pm(win))
    lay.addWidget(win.pm_project)
    gc = win.card(); gl = QVBoxLayout(gc); gl.addWidget(win.label(S["gantt"], 11, True))
    win.pm_gantt = GanttWidget(win.theme); gl.addWidget(win.pm_gantt)
    lay.addWidget(gc, 2)
    row = QHBoxLayout()
    # milestones
    mc = win.card(); ml = QVBoxLayout(mc); ml.addWidget(win.label(S["milestones"], 11, True))
    win.pm_ring = Ring(win.theme); win.pm_ms_list = QListWidget(); win.pm_ms_list.setCursor(Qt.PointingHandCursor)
    win.pm_ms_name = QLineEdit(placeholderText=S["milestone_name"]); win.pm_ms_due = QLineEdit(placeholderText=S["due_hint"])
    ml.addWidget(win.pm_ring); ml.addWidget(win.pm_ms_list)
    ml.addLayout(_row(win.pm_ms_name, win.pm_ms_due, _btn(win, S["add"], lambda: add_milestone(win), True), _btn(win, S["complete"], lambda: complete_milestone(win))))
    # sprints (lifecycle, burndown, velocity - see sprint_ui)
    sc = win.card(); sl = QVBoxLayout(sc); sl.addWidget(win.label(S["sprints"], 11, True))
    win.pm_sp_list = QListWidget(); win.pm_sp_list.setCursor(Qt.PointingHandCursor); win.pm_sp_list.setMaximumHeight(130)
    win.pm_sp_list.currentItemChanged.connect(lambda *_a: su.refresh_burndown(win))
    win.pm_sp_chart = su.BurndownChart(win.theme); win.pm_sp_info = win.label("", 9, muted=True); win.pm_sp_info.setWordWrap(True)
    sl.addWidget(win.pm_sp_list); sl.addWidget(win.pm_sp_chart, 1); sl.addWidget(win.pm_sp_info)
    sl.addLayout(_row(_btn(win, S["pm_breakdown"], lambda: breakdown(win), True), _btn(win, S["pm_split_project"], lambda: split_project_ui(win))))
    sl.addLayout(_row(_btn(win, S["sp_new"], lambda: su.new_sprint(win), False), _btn(win, S["sp_assign"], lambda: su.assign_tasks(win)),
                      _btn(win, S["sp_start"], lambda: su.start_sprint(win)), _btn(win, S["sp_complete"], lambda: su.complete_sprint(win))))
    # tasks / subtasks
    tc = win.card(); tl = QVBoxLayout(tc); tl.addWidget(win.label(S["subtasks"], 11, True))
    win.pm_tasks = QListWidget(); win.pm_tasks.setCursor(Qt.PointingHandCursor); win.pm_task_new = QLineEdit(placeholderText=S["add_task"])
    win.pm_sub_new = QLineEdit(placeholderText=S["subtask_name"]); win.pm_dep = QComboBox()
    tl.addWidget(win.pm_tasks)
    tl.addLayout(_row(win.pm_task_new, _btn(win, S["add_task"], lambda: add_task(win), True)))
    tl.addLayout(_row(win.pm_sub_new, _btn(win, S["subtasks"], lambda: add_subtask(win))))
    tl.addLayout(_row(win.pm_dep, _btn(win, S["depends_on"], lambda: add_dependency(win))))
    for c in (mc, sc, tc):
        row.addWidget(c, 1)
    lay.addLayout(row, 2)
    win.pages.addWidget(page)


def _project_id(win) -> Optional[str]:
    return win.pm_project.currentData()


def refresh_pm(win) -> None:
    cur = win.pm_project.currentData()
    win.pm_project.blockSignals(True)
    win.pm_project.clear()
    for p in win.db.all(Project):
        win.pm_project.addItem(f"{p.icon} {p.name}", p.id)
    if cur:
        win.pm_project.setCurrentIndex(max(0, win.pm_project.findData(cur)))
    win.pm_project.blockSignals(False)
    pid = _project_id(win)
    win.pm_ms_list.clear(); win.pm_tasks.clear(); win.pm_dep.clear()
    if not pid:
        win.pm_gantt.set_data([], []); win.pm_ring.set_value(0.0, "—"); su.refresh_sprints(win, None); return
    svc: ProjectService = win.projects_svc
    tasks = [e for e in win.db.all(TimeEntry, "start_utc") if e.project_id == pid and not e.parent_id]
    sched = svc.gantt(pid, dt.date.today())
    order = [t for t in tasks if t.id in sched]
    idx = {t.id: i for i, t in enumerate(order)}
    links = [(idx[r[1]], idx[r[0]]) for r in win.db.conn.execute("SELECT task_id, depends_on FROM dependencies") if r[0] in idx and r[1] in idx]
    win.pm_gantt.set_data([(t.title, sched[t.id][0], sched[t.id][1], t.status == Status.DONE) for t in order], links)
    for t in tasks:
        sub_p = svc.progress(t.id)
        blocked = " 🔒" if svc.blockers(t.id) else ""
        win.pm_tasks.addItem(_item(to_fa_digits(f"{t.title}{blocked}  —  {int(sub_p * 100)}٪"), t.id))
        win.pm_dep.addItem(t.title, t.id)
    done, total = svc.milestone_progress(pid)
    win.pm_ring.set_value(done / total if total else 0.0, to_fa_digits(f"{done}/{total}"))
    for m in win.db.conn.execute("SELECT * FROM milestones WHERE project_id=? ORDER BY due", (pid,)).fetchall():
        ms = Milestone.from_row(m)
        due = format_jalali(to_tehran(ms.due).date()) if ms.due else "—"
        win.pm_ms_list.addItem(_item(("✅ " if ms.completed else "⬜ ") + f"{ms.name}  ({due})", ms.id))
    su.refresh_sprints(win, pid)


def add_milestone(win) -> None:
    pid, name = _project_id(win), win.pm_ms_name.text().strip()
    if not pid or not name:
        raise ValueError(S["need_title"])
    due = win.pm_ms_due.text().strip()
    when = dt.datetime.combine(parse_date(due), dt.time(12), tzinfo=to_tehran(now_utc()).tzinfo) if due else None
    win.db.save(Milestone(project_id=pid, name=name, due=when)); win.pm_ms_name.clear(); win.pm_ms_due.clear(); refresh_pm(win)


def complete_milestone(win) -> None:
    it = win.pm_ms_list.currentItem()
    if it:
        win.projects_svc.complete_milestone(it.data(Qt.UserRole)); refresh_pm(win)


def add_sprint(win) -> None:
    pid, name = _project_id(win), win.pm_sp_name.text().strip()
    if not pid or not name:
        raise ValueError(S["need_title"])
    start = now_utc()
    win.db.save(Sprint(project_id=pid, name=name, start=start, end=start + dt.timedelta(days=win.pm_sp_days.value()),
                       capacity_hours=win.pm_sp_cap.value(), status="active"))
    win.pm_sp_name.clear(); refresh_pm(win)


def add_task(win) -> None:
    pid, t = _project_id(win), win.pm_task_new.text().strip()
    if not pid or not t:
        raise ValueError(S["need_title"])
    win.db.save(TimeEntry(title=t, start_utc=now_utc(), status=Status.PLANNED, project_id=pid, estimated_min=240))
    win.pm_task_new.clear(); refresh_pm(win)


def add_subtask(win) -> None:
    it, t = win.pm_tasks.currentItem(), win.pm_sub_new.text().strip()
    if it and t:
        win.projects_svc.add_subtask(it.data(Qt.UserRole), t); win.pm_sub_new.clear(); refresh_pm(win)


def add_dependency(win) -> None:
    it, dep = win.pm_tasks.currentItem(), win.pm_dep.currentData()
    if it and dep:
        win.projects_svc.add_dependency(it.data(Qt.UserRole), dep); refresh_pm(win)


# ====================================================================== Eisenhower
class QuadrantList(QListWidget):
    def __init__(self, quadrant: str, on_drop: Callable[[str, str], None]) -> None:
        super().__init__()
        self.quadrant, self.on_drop = quadrant, on_drop
        self.setDragDropMode(QAbstractItemView.DragDrop); self.setDefaultDropAction(Qt.MoveAction); self.setCursor(Qt.PointingHandCursor)

    def dropEvent(self, e) -> None:  # noqa: N802
        src = e.source()
        ids = [i.data(Qt.UserRole) for i in src.selectedItems()] if isinstance(src, QListWidget) else []
        super().dropEvent(e)
        for i in ids:
            self.on_drop(i, self.quadrant)


def build_matrix(win) -> None:
    page = QWidget(); page.setStyleSheet(win._field_style()); lay = QVBoxLayout(page)
    win.mx_lists = {}
    grid = [("do", "schedule"), ("delegate", "eliminate")]
    for pair in grid:
        row = QHBoxLayout()
        for q in pair:
            c = win.card(); cl = QVBoxLayout(c); cl.addWidget(win.label(S["q_" + q], 11, True))
            lw = QuadrantList(q, lambda eid, quad: matrix_drop(win, eid, quad)); win.mx_lists[q] = lw; cl.addWidget(lw); row.addWidget(c, 1)
        lay.addLayout(row, 1)
    win.pages.addWidget(page)


def matrix_drop(win, entry_id: str, quadrant: str) -> None:
    _guard(win, lambda: planner_svc.set_quadrant(win.db, entry_id, quadrant))
    refresh_matrix(win)


def refresh_matrix(win) -> None:
    for q, tasks in planner_svc.quadrants(win.db).items():
        lw = win.mx_lists[q]; lw.clear()
        for t in tasks:
            lw.addItem(_item(t.title, t.id))


# ====================================================================== Tools hub
def _section(win, title: str):
    c = win.card(); l = QVBoxLayout(c); l.setContentsMargins(18, 12, 18, 12); l.addWidget(win.label(title, 11, True)); return c, l


def build_tools(win) -> None:
    inner = QWidget(); inner.setStyleSheet(win._field_style()); lay = QVBoxLayout(inner)
    win.tools_msg = win.label("", 10, muted=True); win.tools_msg.setWordWrap(True); lay.addWidget(win.tools_msg)

    # --- goals / OKR (SMART validation) ---
    c, l = _section(win, S["okr"]); win.g_list = QListWidget(); win.g_list.setCursor(Qt.PointingHandCursor)
    win.g_name = QLineEdit(placeholderText=S["goal_name"]); win.g_kr = QLineEdit(placeholderText=S["kr_name"])
    win.g_target = QDoubleSpinBox(); win.g_target.setRange(0, 1e9); win.g_target.setPrefix(S["target"] + " ")
    win.g_cur = QDoubleSpinBox(); win.g_cur.setRange(0, 1e9); win.g_cur.setPrefix(S["current"] + " ")
    win.g_due = QLineEdit(placeholderText=S["due_hint"])
    l.addWidget(win.g_list); l.addLayout(_row(win.g_name, win.g_kr, win.g_target, win.g_due, _btn(win, S["add"], lambda: add_goal(win), True)))
    l.addLayout(_row(win.g_cur, _btn(win, S["update_kr"], lambda: update_goal(win)))); lay.addWidget(c)

    # --- templates ---
    c, l = _section(win, S["templates"]); win.t_list = QListWidget(); win.t_list.setCursor(Qt.PointingHandCursor)
    win.t_name = QLineEdit(placeholderText=S["name"]); win.t_min = QSpinBox(); win.t_min.setRange(1, 1440); win.t_min.setValue(30)
    l.addWidget(win.t_list); l.addLayout(_row(win.t_name, win.t_min, _btn(win, S["add"], lambda: add_template(win), True), _btn(win, S["use_template"], lambda: use_template(win)))); lay.addWidget(c)

    # --- saved filters ---
    c, l = _section(win, S["saved_filters"]); win.f_list = QListWidget(); win.f_list.setCursor(Qt.PointingHandCursor)
    win.f_name = QLineEdit(placeholderText=S["name"]); win.f_query = QLineEdit(placeholderText="tag:bug project:app >2h")
    l.addWidget(win.f_list); l.addLayout(_row(win.f_name, win.f_query, _btn(win, S["add"], lambda: add_filter(win), True), _btn(win, S["run"], lambda: run_filter(win)))); lay.addWidget(c)

    # --- custom fields + formula ---
    c, l = _section(win, S["custom_fields"]); win.cf_name = QLineEdit(placeholderText=S["name"]); win.cf_type = QComboBox()
    for t in extras.FIELD_TYPES:
        win.cf_type.addItem(t, t)
    win.cf_formula = QLineEdit(placeholderText="hours * rate"); win.cf_out = win.label("", 10, muted=True)
    l.addLayout(_row(win.cf_name, win.cf_type, _btn(win, S["add"], lambda: define_field(win), True)))
    l.addLayout(_row(win.cf_formula, _btn(win, S["calc"], lambda: calc_formula(win)))); l.addWidget(win.cf_out); lay.addWidget(c)

    # --- time travel ---
    c, l = _section(win, S["time_travel"]); win.tt_date = QLineEdit(placeholderText=S["due_hint"]); win.tt_list = QListWidget()
    l.addLayout(_row(win.tt_date, _btn(win, S["show"], lambda: time_travel(win), True))); l.addWidget(win.tt_list); lay.addWidget(c)

    # --- bulk entry ---
    c, l = _section(win, S["bulk_entry"]); win.bulk_text = QPlainTextEdit(); win.bulk_text.setPlaceholderText("2026-05-01 09:00-10:30 write docs #docs @Project")
    l.addWidget(win.bulk_text); l.addWidget(_btn(win, S["import"], lambda: do_bulk(win), True)); lay.addWidget(c)

    # --- reports ---
    c, l = _section(win, S["reports"])
    l.addLayout(_row(_btn(win, S["year_md"], lambda: save_report(win, "year", "md")), _btn(win, S["year_html"], lambda: save_report(win, "year", "html")),
                     _btn(win, S["month_md"], lambda: save_report(win, "month", "md")))); lay.addWidget(c)

    # --- retainers + KPIs + blueprints ---
    c, l = _section(win, S["retainers"]); win.r_client = QComboBox(); win.r_desc = QLineEdit(placeholderText=S["name"])
    win.r_hours = QDoubleSpinBox(); win.r_hours.setRange(0, 1000); win.r_hours.setValue(10); win.r_rate = QDoubleSpinBox(); win.r_rate.setRange(0, 1e12)
    win.r_day = QSpinBox(); win.r_day.setRange(1, 29); win.r_day.setValue(1)
    l.addLayout(_row(win.r_client, win.r_desc, win.r_hours, win.r_rate, win.r_day, _btn(win, S["add"], lambda: define_retainer(win), True), _btn(win, S["run_due"], lambda: run_retainers(win)))); lay.addWidget(c)
    c, l = _section(win, S["kpis"]); win.k_name = QLineEdit(placeholderText=S["name"]); win.k_formula = QLineEdit(placeholderText="billable_hours / total_hours * 100"); win.k_out = win.label("", 10, muted=True)
    l.addLayout(_row(win.k_name, win.k_formula, _btn(win, S["add"], lambda: define_kpi(win), True))); l.addWidget(win.k_out); lay.addWidget(c)
    c, l = _section(win, S["blueprints"]); win.bp_name = QLineEdit(placeholderText=S["name"]); win.bp_tasks = QPlainTextEdit(); win.bp_tasks.setPlaceholderText("title | minutes")
    win.bp_proj = QLineEdit(placeholderText=S["name"]); win.bp_list = QComboBox()
    l.addLayout(_row(win.bp_name, _btn(win, S["add"], lambda: save_blueprint(win), True))); l.addWidget(win.bp_tasks)
    l.addLayout(_row(win.bp_list, win.bp_proj, _btn(win, S["create_project"], lambda: make_from_blueprint(win)))); lay.addWidget(c)

    # --- dashboard layout (drag to reorder, tick to show) ---
    c, l = _section(win, S["dash_layout"]); win.dl_list = QListWidget(); win.dl_list.setDragDropMode(QAbstractItemView.InternalMove); win.dl_list.setCursor(Qt.PointingHandCursor)
    l.addWidget(win.dl_list); l.addWidget(_btn(win, S["save"], lambda: save_layout(win), True)); lay.addWidget(c)

    lay.addStretch()
    scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(inner); scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
    win.pages.addWidget(scroll)


def _msg(win, text: str) -> None:
    win.tools_msg.setText(to_fa_digits(text))


def refresh_tools(win) -> None:
    win.g_list.clear()
    for g in win.db.all(Goal):
        win.g_list.addItem(_item(to_fa_digits(f"{g.name} — {int(g.progress * 100)}٪"), g.id))
    win.t_list.clear()
    for t in win.db.all(Template):
        win.t_list.addItem(_item(f"{t.name} ({t.estimated_min}m)", t.id))
    from ..core.models import SavedFilter
    win.f_list.clear()
    for f in win.db.all(SavedFilter):
        win.f_list.addItem(_item(f"{f.name}: {f.query}", f.id))
    win.r_client.clear()
    for c in win.db.all(Client):
        win.r_client.addItem(c.name, c.id)
    win.bp_list.clear()
    for n in win.db.get_setting("blueprints", {}):
        win.bp_list.addItem(n, n)
    layout = metrics.get_dashboard(win.db, "default")
    win.dl_list.clear()
    for k in layout + [w for w in win.dash_cards if w not in layout]:
        it = _item(S.get("w_" + k, k), k)
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        it.setCheckState(Qt.Checked if k in layout else Qt.Unchecked)
        win.dl_list.addItem(it)
    k = metrics.evaluate_kpis(win.db, win.jy)
    win.k_out.setText(to_fa_digits("  |  ".join(f"{n}: {v}" for n, v in k.items())))


def add_goal(win) -> None:
    due = win.g_due.text().strip()
    g = Goal(name=win.g_name.text().strip(), key_results=[{"name": win.g_kr.text().strip() or "KR1", "target": win.g_target.value(), "current": 0.0}],
             deadline=dt.datetime.combine(parse_date(due), dt.time(12), tzinfo=to_tehran(now_utc()).tzinfo) if due else None)
    problems = smart2.validate_smart(g)
    win.db.save(g); win.g_name.clear()
    _msg(win, ("SMART: " + " | ".join(problems)) if problems else "SMART ✓")
    refresh_tools(win)


def update_goal(win) -> None:
    it = win.g_list.currentItem()
    if it:
        update_key_result(win.db, it.data(Qt.UserRole), 0, win.g_cur.value()); refresh_tools(win)


def add_template(win) -> None:
    n = win.t_name.text().strip()
    if not n:
        raise ValueError(S["need_title"])
    win.db.save(Template(name=n, title=n, estimated_min=win.t_min.value())); win.t_name.clear(); refresh_tools(win)


def use_template(win) -> None:
    it = win.t_list.currentItem()
    if it:
        extras.from_template(win.db, it.data(Qt.UserRole)); _msg(win, S["saved"])


def add_filter(win) -> None:
    extras.save_filter(win.db, win.f_name.text(), win.f_query.text()); win.f_name.clear(); refresh_tools(win)


def run_filter(win) -> None:
    it = win.f_list.currentItem()
    if it:
        rows = extras.run_filter(win.db, it.data(Qt.UserRole)); _msg(win, f"{len(rows)} نتیجه: " + "، ".join(e.title for e in rows[:8]))


def define_field(win) -> None:
    extras.define_field(win.db, win.cf_name.text().strip(), win.cf_type.currentData()); win.cf_name.clear(); _msg(win, S["saved"])


def calc_formula(win) -> None:
    last = win.db.all(TimeEntry, "start_utc DESC")[:1]
    if not last:
        raise ValueError("no entries")
    win.cf_out.setText(to_fa_digits(f"{last[0].title}: {extras.entry_formula(win.db, last[0].id, win.cf_formula.text())}"))


def time_travel(win) -> None:
    day = parse_date(win.tt_date.text())
    moment = dt.datetime.combine(day, dt.time(23, 59, 59), tzinfo=to_tehran(now_utc()).tzinfo)
    win.tt_list.clear()
    for e in win.db.entries_as_of(moment)[-200:]:
        win.tt_list.addItem(to_fa_digits(f"{to_tehran(e.start_utc):%Y-%m-%d %H:%M}  {e.title}"))


def do_bulk(win) -> None:
    r = bulk.bulk_add(win.db, win.bulk_text.toPlainText())
    _msg(win, f"✓ {r['added']}" if not r["errors"] else "خطا: " + " | ".join(f"خط {n}: {m}" for n, m in r["errors"][:5]))
    win.refresh_all()


def save_report(win, kind: str, fmt: str) -> None:
    jy, jm, _ = date_to_jalali(to_tehran(now_utc()).date())
    md = reports.year_markdown(win.db, jy) if kind == "year" else reports.month_markdown(win.db, jy, jm)
    text = md if fmt == "md" else reports.to_html(md, f"{jy}")
    path, _ = QFileDialog.getSaveFileName(win, S["reports"], f"report.{fmt}")
    if path:
        reports.save(text, path); _msg(win, S["saved"])


def define_retainer(win) -> None:
    recurring.define(win.db, win.r_client.currentData(), win.r_desc.text(), win.r_hours.value(), win.r_rate.value(), win.r_day.value()); _msg(win, S["saved"])


def run_retainers(win) -> None:
    _msg(win, f"{len(recurring.run_due(win.db))} فاکتور صادر شد")


def define_kpi(win) -> None:
    metrics.define_kpi(win.db, win.k_name.text().strip(), win.k_formula.text()); refresh_tools(win)


def save_blueprint(win) -> None:
    tasks = []
    for line in win.bp_tasks.toPlainText().splitlines():
        if line.strip():
            title, _, mins = line.partition("|")
            tasks.append({"title": title.strip(), "estimated_min": int(mins.strip() or 0) if mins.strip().isdigit() or not mins.strip() else 0})
    blueprints.save_blueprint(win.db, win.bp_name.text().strip(), tasks); refresh_tools(win)


def make_from_blueprint(win) -> None:
    blueprints.create_from_blueprint(win.db, win.bp_list.currentData(), win.bp_proj.text().strip() or win.bp_list.currentText()); win.refresh_all(); _msg(win, S["saved"])


def save_layout(win) -> None:
    keys = [win.dl_list.item(i).data(Qt.UserRole) for i in range(win.dl_list.count()) if win.dl_list.item(i).checkState() == Qt.Checked]
    metrics.save_dashboard(win.db, "default", [k for k in keys if k in metrics.WIDGETS])
    win.layout_dashboard(); _msg(win, S["saved"])


# ====================================================================== sankey for analytics
def build_sankey(win, layout) -> None:
    c = win.card(); l = QVBoxLayout(c); l.addWidget(win.label(S["sankey"], 11, True))
    win.an_sankey = SankeyWidget(win.theme); l.addWidget(win.an_sankey); layout.addWidget(c, 1)


def refresh_sankey(win, jy: int) -> None:
    win.an_sankey.set_links(sankey(win.db, jy)["links"])


# ====================================================================== ambient + detached windows
class AmbientWindow(QWidget):
    """Full-screen idle screensaver: big clock, today's hours, current task. Any click/key closes it."""

    def __init__(self, win) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.win = win
        self.setStyleSheet("background:#07070f;")
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter)
        self.clock = QLabel(); self.info = QLabel()
        self.clock.setStyleSheet("color:#F2F2FA;font-size:72pt;font-weight:700;background:transparent;")
        self.info.setStyleSheet("color:#A9A9C4;font-size:18pt;background:transparent;")
        for w in (self.clock, self.info):
            w.setAlignment(Qt.AlignCenter); lay.addWidget(w)

    def refresh(self) -> None:
        now = to_tehran(now_utc())
        today = self.win.analytics.year_summary(self.win.jy, now.date()).daily.get(now.date(), 0)
        cur = self.win.tracker.current
        self.clock.setText(to_fa_digits(now.strftime("%H:%M")))
        self.info.setText(to_fa_digits(f"امروز {today // 3600}:{today % 3600 // 60:02d}" + (f"   ·   ▶ {cur.title}" if cur else "")))

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self.close()

    def keyPressEvent(self, e) -> None:  # noqa: N802
        self.close()


class DetachedWindow(QWidget):
    """Hosts a page in its own top-level window; returns it to the main stack when closed."""

    def __init__(self, page: QWidget, title: str, on_close: Callable[[QWidget], None]) -> None:
        super().__init__(None)
        self.page, self.on_close = page, on_close
        self.setWindowTitle(title); self.resize(900, 640)
        self.box = QVBoxLayout(self); self.box.addWidget(page)

    def closeEvent(self, e) -> None:  # noqa: N802
        self.box.removeWidget(self.page)
        self.page.setParent(None)
        self.on_close(self.page)
        super().closeEvent(e)


def breakdown(win) -> None:
    """Create phases (milestones), tasks and sub-tasks for the selected project from one pasted outline."""
    pid = win.pm_project.currentData()
    if not pid:
        win.toast(S["sp_need_project"]); return
    from .lists_ui import BreakdownDialog
    dlg = BreakdownDialog(win, pid)
    if dlg.exec_() and dlg.result:
        r = dlg.result
        win.toast(to_fa_digits(f"{r['phases']} {S['bd_phases']} · {r['tasks']} {S['tasks']} · {r['subtasks']} {S['subtasks']}"))
        win.refresh_all()


def split_project_ui(win) -> None:
    """Move the tasks selected in the task list of this page into a new project."""
    from PyQt5.QtWidgets import QInputDialog
    from ..services import project_split as ps
    pid = win.pm_project.currentData()
    ids = [it.data(Qt.UserRole) for it in win.pm_tasks.selectedItems() if it.data(Qt.UserRole)]
    if not pid or not ids:
        win.toast(S["pm_split_none"]); return
    name, ok = QInputDialog.getText(win, S["pm_split_project"], S["pm_split_name"])
    if ok:
        try:
            ps.split_project(win.db, pid, ids, name); win.refresh_all()
        except ps.SplitError as exc:
            win.toast(str(exc))
