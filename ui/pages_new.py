"""Task & project management pages: Today, All tasks (tree + subtasks + drag priority), Board (manual order + drips), Calendar, Projects, Habits, Goals.

Same convention as the older pages: ``build_x(win)`` creates the page and appends it to ``win.pages``; ``refresh_x(win)`` fills it.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QProgressBar,
                             QScrollArea, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ..core import taxonomy
from ..core.models import ALL_COLUMNS, Goal, Habit, Member, Project, Status, TimeEntry
from ..core.persian import (MONTHS_FA, date_to_jalali, format_duration, format_jalali, is_gregorian, jalali_month_length, jalali_to_date, now_utc, to_fa_digits, to_tehran, tr)
from ..services import extras, quick, task_reminders, taskform as tf, views
from ..services.habits import HabitService
from ..services.projects import ProjectService
from . import icons
from .dialogs import GoalDialog, HabitDialog, ProjectDialog, TaskDialog, confirm
from .forms import FlowLayout, chip_button
from .glass import GlassButton, Ring
from .strings import S

log = logging.getLogger("worktracker.pages")
PRI_COLOR = {p_id: p["color"] for p_id, p in taxonomy.PRIORITIES.items()}


def _page(win, margins: int = 4) -> tuple:
    w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(margins, margins, margins, margins); lay.setSpacing(12)
    return w, lay


def _title_row(win, title: str, *buttons: QWidget) -> QHBoxLayout:
    row = QHBoxLayout(); lab = win.label(title, 17, True); row.addWidget(lab, 1)
    for b in buttons:
        row.addWidget(b)
    return row


def _names(win) -> Dict[str, str]:
    return {p.id: p.name for p in win.db.all(Project)}


def task_line(e: TimeEntry, names: Dict[str, str], subs: Optional[tuple] = None) -> str:
    """One readable line: priority dot, title and the useful metadata."""
    bits = ["● " + e.title]
    meta = []
    if e.project_id in names:
        meta.append("📁 " + names[e.project_id])
    if e.due_utc:
        meta.append("📅 " + format_jalali(to_tehran(e.due_utc).date()))
    if e.estimated_min:
        meta.append("⏱ " + format_duration(e.estimated_min * 60))
    if subs and subs[1]:
        meta.append(f"☑ {subs[0]}/{subs[1]}")
    if e.checklist:
        meta.append(f"✔ {sum(1 for c in e.checklist if c.get('done'))}/{len(e.checklist)}")
    if e.tags:
        meta.append("#" + " #".join(e.tags[:3]))
    return to_fa_digits(bits[0] + ("\n" + "  ·  ".join(meta) if meta else ""))


def _subcount(win) -> Dict[str, tuple]:
    out: Dict[str, List[int]] = {}
    for r in win.db.conn.execute("SELECT parent_id, status FROM entries WHERE parent_id IS NOT NULL"):
        a = out.setdefault(r[0], [0, 0]); a[1] += 1; a[0] += 1 if r[1] == "done" else 0
    return {k: (v[0], v[1]) for k, v in out.items()}


def open_task(win, entry: Optional[TimeEntry] = None, defaults: Optional[dict] = None) -> Optional[TimeEntry]:
    dlg = TaskDialog(win, entry, defaults)
    ok = dlg.exec_()
    if ok:
        win.refresh_all()
    return dlg.saved if ok else None


def complete_task(win, entry_id: str) -> None:
    win.projects_svc.move(entry_id, "done")
    if win.theme.fx is not None:
        win.theme.fx.play("success")
    win.refresh_all()


# =================================================================== TODAY
def build_today(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_task"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: open_task(win))
    rep = GlassButton(S["dr_open"], win.theme, icon="reports"); rep.clicked.connect(win.open_daily_report)
    lay.addLayout(_title_row(win, S["today"], rep, add))
    win.td_date = win.label("", 11, muted=True); lay.addWidget(win.td_date)
    quick_row = QHBoxLayout(); win.td_quick = QLineEdit(placeholderText=S["quick_add_hint"]); win.td_quick.returnPressed.connect(lambda: quick_add(win))
    qb = GlassButton(S["add"], win.theme, icon="bolt"); qb.clicked.connect(lambda: quick_add(win)); quick_row.addWidget(win.td_quick, 1); quick_row.addWidget(qb); lay.addLayout(quick_row)
    cols = QHBoxLayout(); cols.setSpacing(12)
    win.td_lists = {}
    for key, title in (("overdue", S["overdue"]), ("today", S["today_tasks"]), ("running", S["in_progress"])):
        c = win.card(); cl = QVBoxLayout(c); cl.setContentsMargins(14, 12, 14, 12); cl.addWidget(win.label(title, 11, True))
        lw = QListWidget(); lw.setCursor(Qt.PointingHandCursor); lw.itemDoubleClicked.connect(lambda it: open_task(win, win.db.get(TimeEntry, it.data(Qt.UserRole))))
        lw.setContextMenuPolicy(Qt.CustomContextMenu); lw.customContextMenuRequested.connect(lambda pos, w=lw: task_menu(win, w, pos))
        win.td_lists[key] = lw; cl.addWidget(lw); cols.addWidget(c, 1)
    lay.addLayout(cols, 1)
    from .hourstrip import HourStrip
    sc = win.card(); sl = QVBoxLayout(sc); sl.setContentsMargins(14, 10, 14, 10); sl.addWidget(win.label(S["hour_strip"], 11, True))
    win.hour_strip = HourStrip(win.theme, lambda h: win.runtime.show_prompt(hour=h)); sl.addWidget(win.hour_strip); sl.addWidget(win.label(S["hour_strip_hint"], 9, muted=True)); lay.addWidget(sc)
    hb = win.card(); hl = QVBoxLayout(hb); hl.setContentsMargins(14, 10, 14, 12); hl.addWidget(win.label(S["habits_today"], 11, True))
    win.td_habits = QWidget(); win.td_habits_flow = FlowLayout(win.td_habits); hl.addWidget(win.td_habits); lay.addWidget(hb)
    win.pages.addWidget(page)


def quick_add(win) -> None:
    text = win.td_quick.text().strip()
    if not text:
        return
    try:
        cap = quick.parse(text)
        pid = next((p.id for p in win.db.all(Project) if cap.project and p.name.lower() == cap.project.lower()), None)
        now = now_utc()
        tf.apply(win.db, tf.TaskValues(title=cap.title, tags=cap.tags, project_id=pid, estimated_min=cap.minutes, start=now, end=now + dt.timedelta(minutes=cap.minutes) if cap.minutes else None), now=now)
        win.td_quick.clear(); win.toast(S["saved"]); win.refresh_all()
        if win.theme.fx is not None:
            win.theme.fx.play("success")
    except ValueError as exc:
        win.toast(str(exc))


def task_menu(win, lw: QListWidget, pos) -> None:
    it = lw.itemAt(pos)
    if it is None:
        return
    eid = it.data(Qt.UserRole)
    m = QMenu(win)
    m.addAction(S["edit"], lambda: open_task(win, win.db.get(TimeEntry, eid)))
    m.addAction(S["mark_done"], lambda: complete_task(win, eid))
    m.addAction(S["start_timer"], lambda: _start_timer(win, eid))
    m.addAction(S["add_subtask"], lambda: _add_subtask(win, eid))
    mv = m.addMenu(S["move_to"])
    for c in ALL_COLUMNS:
        mv.addAction(tf.COLUMN_LABELS[c], lambda c=c: (win.projects_svc.move(eid, c), win.refresh_all()))
    m.addAction(S["delete"], lambda: (win.db.delete(TimeEntry, eid), win.refresh_all()) if confirm(win, S["confirm_delete"]) else None)
    m.exec_(lw.viewport().mapToGlobal(pos))


def _start_timer(win, eid: str) -> None:
    e = win.db.get(TimeEntry, eid)
    if e:
        win.tracker.start(e.title, project_id=e.project_id, category=e.category, tags=e.tags); win._timers_on(); win.refresh_all()


def _add_subtask(win, parent_id: str) -> None:
    from PyQt5.QtWidgets import QInputDialog
    t, ok = QInputDialog.getText(win, S["add_subtask"], S["subtask_hint"])
    if ok and t.strip():
        try:
            win.projects_svc.add_subtask(parent_id, t.strip()); win.refresh_all()
        except ValueError as exc:
            win.toast(str(exc))


def _refresh_hour_strip(win) -> None:
    from ..services.ledger import hour_floor
    if not hasattr(win, "runtime"):
        return
    led = win.runtime.ledger
    now = now_utc()
    day0 = hour_floor(now).astimezone(to_tehran(now).tzinfo).replace(hour=0)
    start = day0.astimezone(dt.timezone.utc)
    cur = hour_floor(now)
    rows = []
    for i in range(24):
        h = start + dt.timedelta(hours=i)
        rows.append(led.hour(h, now) if h <= cur else {"hour_start": h, "engaged_sec": 0, "idle_sec": 0, "apps": [], "logged_sec": 0, "unlogged_sec": 0})
    win.hour_strip.set_rows(rows)


def refresh_today(win) -> None:
    now = now_utc(); today = to_tehran(now).date(); names = _names(win); subs = _subcount(win)
    _refresh_hour_strip(win)
    win.td_date.setText(to_fa_digits(format_jalali(today, "{weekday} {d} {month_name} {y}", fa_digits=False)))
    lo = dt.datetime.combine(today, dt.time(), tzinfo=to_tehran(now).tzinfo); hi = lo + dt.timedelta(days=1)
    over, tod, run = [], [], []
    for e in win.db.all(TimeEntry, "start_utc"):
        if e.parent_id or e.column in ("done", "cancelled"):
            continue
        if e.status == Status.RUNNING:
            run.append(e)
        elif e.is_overdue(now):
            over.append(e)
        elif (lo <= e.start_utc < hi and e.status == Status.PLANNED) or (e.due_utc and lo <= e.due_utc < hi) or e.column == "in_progress":
            tod.append(e)
    for key, items in (("overdue", over), ("today", tod), ("running", run)):
        lw = win.td_lists[key]; lw.clear()
        for e in sorted(items, key=lambda x: (x.priority, x.start_utc)):
            it = QListWidgetItem(task_line(e, names, subs.get(e.id))); it.setData(Qt.UserRole, e.id); lw.addItem(it)
    while win.td_habits_flow.count():
        x = win.td_habits_flow.takeAt(0)
        if x is not None and x.widget() is not None:
            x.widget().deleteLater()
    hs = HabitService(win.db)
    for h in win.db.all(Habit):
        if today.weekday() not in h.days:
            continue
        done = today.isoformat() in h.log
        b = chip_button(f"{h.icon} {h.name}" + (" ✓" if done else ""), True); b.setChecked(done)
        b.clicked.connect(lambda _c=False, hid=h.id, d=done: _toggle_habit(win, hid, d)); win.td_habits_flow.addWidget(b)


def _toggle_habit(win, hid: str, was_done: bool) -> None:
    hs = HabitService(win.db)
    today = to_tehran(now_utc()).date()
    (hs.undo_check_in if was_done else hs.check_in)(hid, today) if was_done else hs.check_in(hid, today)
    if win.theme.fx is not None:
        win.theme.fx.play("drop_in" if not was_done else "click")
    win.refresh_all()


# =================================================================== ALL TASKS (tree)
class TaskTree(QTreeWidget):
    """Drag to reorder (rank is saved), drag a task onto another to make it a subtask."""

    def __init__(self, on_dropped: Callable[[], None]) -> None:
        super().__init__()
        self.on_dropped = on_dropped
        self.setDragDropMode(QAbstractItemView.InternalMove); self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setCursor(Qt.PointingHandCursor); self.setAlternatingRowColors(False); self.setUniformRowHeights(False); self.setIndentation(22)

    def startDrag(self, actions) -> None:  # noqa: N802
        fx = getattr(self, "fx", None)
        if fx is not None:
            fx.drag_started()
        try:
            super().startDrag(actions)
        finally:
            if fx is not None:
                fx.drag_finished()

    def dropEvent(self, e) -> None:  # noqa: N802
        super().dropEvent(e)
        self.on_dropped()


def build_tasks(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_task"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: open_task(win))
    lay.addLayout(_title_row(win, S["tasks"], add))
    bar = QHBoxLayout(); bar.setSpacing(8)
    win.tk_search = QLineEdit(placeholderText=S["search"]); win.tk_search.textChanged.connect(lambda _t: refresh_tasks(win))
    win.tk_status = QComboBox(); win.tk_status.addItem(S["all"], "")
    win.tk_status.addItem(S["open_tasks"], "open")
    for c in ALL_COLUMNS:
        win.tk_status.addItem(tf.COLUMN_LABELS[c], c)
    win.tk_pri = QComboBox(); win.tk_pri.addItem(S["any_priority"], 0)
    for k, p in taxonomy.PRIORITIES.items():
        win.tk_pri.addItem(f"{p['icon']} {p['name']}", k)
    win.tk_proj = QComboBox(); win.tk_group = QComboBox()
    for label, key in ((S["no_group"], ""), (S["by_project"], "project"), (S["by_priority"], "priority"), (S["by_status"], "column"), (S["by_category"], "category"), (S["by_due"], "due")):
        win.tk_group.addItem(label, key)
    win.tk_sort = QComboBox()
    for label, key in ((S["sort_manual"], "rank"), (S["sort_priority"], "priority"), (S["sort_due"], "due"), (S["sort_new"], "new"), (S["sort_title"], "title")):
        win.tk_sort.addItem(label, key)
    for w in (win.tk_status, win.tk_pri, win.tk_proj, win.tk_group, win.tk_sort):
        w.currentIndexChanged.connect(lambda _i: refresh_tasks(win)); w.setCursor(Qt.PointingHandCursor)
    bar.addWidget(win.tk_search, 2)
    for w in (win.tk_status, win.tk_pri, win.tk_proj, win.tk_group, win.tk_sort):
        bar.addWidget(w, 1)
    lay.addLayout(bar)
    win.tk_tree = TaskTree(lambda: _tree_dropped(win)); win.tk_tree.setHeaderLabels([S["title"], S["project"], S["priority"], S["due"], S["progress"], S["estimate"]])
    win.tk_tree.setColumnWidth(0, 360); win.tk_tree.itemDoubleClicked.connect(lambda it, _c: open_task(win, win.db.get(TimeEntry, it.data(0, Qt.UserRole))) if it.data(0, Qt.UserRole) else None)
    win.tk_tree.setContextMenuPolicy(Qt.CustomContextMenu); win.tk_tree.customContextMenuRequested.connect(lambda pos: _tree_menu(win, pos))
    lay.addWidget(win.tk_tree, 1)
    batch = QHBoxLayout(); win.tk_info = win.label("", 10, muted=True); batch.addWidget(win.tk_info, 1)
    for label, fn in ((S["mark_done"], lambda: _batch(win, "done")), (S["set_priority_high"], lambda: _batch(win, "p1")), (S["add_tag_batch"], lambda: _batch(win, "tag")), (S["delete"], lambda: _batch(win, "delete"))):
        b = GlassButton(label, win.theme); b.clicked.connect(lambda _c=False, f=fn: f()); batch.addWidget(b)
    lay.addLayout(batch)
    win.pages.addWidget(page)


def _tree_menu(win, pos) -> None:
    it = win.tk_tree.itemAt(pos)
    if it is None or not it.data(0, Qt.UserRole):
        return
    eid = it.data(0, Qt.UserRole)
    m = QMenu(win)
    m.addAction(S["edit"], lambda: open_task(win, win.db.get(TimeEntry, eid)))
    m.addAction(S["mark_done"], lambda: complete_task(win, eid))
    m.addAction(S["start_timer"], lambda: _start_timer(win, eid))
    m.addAction(S["add_subtask"], lambda: _add_subtask(win, eid))
    pm_ = m.addMenu(S["priority"])
    for k, p in taxonomy.PRIORITIES.items():
        pm_.addAction(f"{p['icon']} {p['name']}", lambda k=k: _set_priority(win, eid, k))
    m.addAction(S["delete"], lambda: (win.db.delete(TimeEntry, eid), win.refresh_all()) if confirm(win, S["confirm_delete"]) else None)
    m.exec_(win.tk_tree.viewport().mapToGlobal(pos))


def _set_priority(win, eid: str, k: int) -> None:
    e = win.db.get(TimeEntry, eid)
    if e:
        e.priority = k; win.db.save(e); win.refresh_all()


def _selected_ids(win) -> List[str]:
    return [i.data(0, Qt.UserRole) for i in win.tk_tree.selectedItems() if i.data(0, Qt.UserRole)]


def _batch(win, action: str) -> None:
    ids = _selected_ids(win)
    if not ids:
        win.toast(S["select_first"]); return
    if action == "done":
        for i in ids:
            try:
                win.projects_svc.move(i, "done")
            except ValueError:
                pass
    elif action == "p1":
        for i in ids:
            _set_priority(win, i, 1)
    elif action == "tag":
        from PyQt5.QtWidgets import QInputDialog
        t, ok = QInputDialog.getText(win, S["add_tag_batch"], S["tags"])
        if ok and t.strip():
            extras.batch_update(win.db, ids, add_tags=[t.strip()])
    elif action == "delete" and confirm(win, S["confirm_delete"]):
        extras.batch_delete(win.db, ids)
    win.refresh_all()


def _tree_dropped(win) -> None:
    """Persist what the drag did: new manual order (rank) and, if dropped *onto* a task, a parent link (subtask)."""
    tree = win.tk_tree
    with win.db.transaction():
        n = 0
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            eid = top.data(0, Qt.UserRole)
            if not eid:                                              # group header: look inside
                for j in range(top.childCount()):
                    n += _rank_item(win, top.child(j), n)
                continue
            n += _rank_item(win, top, n)
    win.refresh_all()


def _rank_item(win, item, n: int) -> int:
    eid = item.data(0, Qt.UserRole)
    if not eid:
        return 0
    e = win.db.get(TimeEntry, eid)
    if e is None:
        return 0
    parent = item.parent()
    pid = parent.data(0, Qt.UserRole) if parent is not None else None
    if pid and pid != e.parent_id and pid != e.id:
        par = win.db.get(TimeEntry, pid)
        if par is not None and not par.parent_id and not any(True for _ in win.db.conn.execute("SELECT 1 FROM entries WHERE parent_id=?", (e.id,))):
            e.parent_id = pid                                          # one level of nesting only
    elif parent is None and e.parent_id and not pid:
        e.parent_id = None                                             # dragged out to the top level
    e.rank = float(n)
    win.db.save(e)
    count = 1
    for k in range(item.childCount()):
        count += _rank_item(win, item.child(k), n + count)
    return count


def refresh_tasks(win) -> None:
    db, names = win.db, _names(win)
    cur = win.tk_proj.currentData()
    if win.tk_proj.count() != len(names) + 1:
        win.tk_proj.blockSignals(True); win.tk_proj.clear(); win.tk_proj.addItem(S["all_projects"], None)
        for pid, n in names.items():
            win.tk_proj.addItem(n, pid)
        win.tk_proj.setCurrentIndex(max(0, win.tk_proj.findData(cur))); win.tk_proj.blockSignals(False)
    q = win.tk_search.text().strip().lower(); st = win.tk_status.currentData(); pri = win.tk_pri.currentData(); proj = win.tk_proj.currentData()
    allt = db.all(TimeEntry)
    kids: Dict[str, List[TimeEntry]] = {}
    for e in allt:
        if e.parent_id:
            kids.setdefault(e.parent_id, []).append(e)
    def keep(e: TimeEntry) -> bool:
        if st == "open" and e.column in ("done", "cancelled"):
            return False
        if st and st != "open" and e.column != st:
            return False
        if pri and e.priority != pri:
            return False
        if proj and e.project_id != proj:
            return False
        return not q or q in e.title.lower() or any(q in t.lower() for t in e.tags)
    tops = [e for e in allt if not e.parent_id and (keep(e) or any(keep(k) for k in kids.get(e.id, [])))]
    sort = win.tk_sort.currentData()
    far = dt.datetime.max.replace(tzinfo=dt.timezone.utc)
    keyf = {"rank": lambda e: (e.rank, e.priority), "priority": lambda e: (e.priority, e.rank), "due": lambda e: (e.due_utc or far, e.priority), "new": lambda e: -e.created_at.timestamp(), "title": lambda e: e.title.lower()}.get(sort or "rank") or (lambda e: (e.rank, e.priority))
    tops.sort(key=keyf)
    group = win.tk_group.currentData()
    tree = win.tk_tree; tree.clear(); tree.fx = win.theme.fx
    def gkey(e: TimeEntry) -> str:
        if group == "project": return names.get(e.project_id or "", S["no_project"])
        if group == "priority": return taxonomy.PRIORITIES[e.priority]["icon"] + " " + taxonomy.PRIORITIES[e.priority]["name"]
        if group == "column": return tf.COLUMN_LABELS.get(e.column, e.column)
        if group == "category": return taxonomy.category_name(e.category)
        if group == "due":
            if not e.due_utc: return S["no_due"]
            d = (to_tehran(e.due_utc).date() - to_tehran(now_utc()).date()).days
            return S["g_overdue"] if d < 0 else S["g_today"] if d == 0 else S["g_week"] if d <= 7 else S["g_later"]
        return ""
    holders: Dict[str, QTreeWidgetItem] = {}
    def add_row(parent, e: TimeEntry) -> QTreeWidgetItem:
        it = QTreeWidgetItem([e.title, names.get(e.project_id or "", ""), taxonomy.PRIORITIES[e.priority]["icon"] + " " + taxonomy.PRIORITIES[e.priority]["name"],
                              format_jalali(to_tehran(e.due_utc).date()) if e.due_utc else "", f"{e.progress}%", format_duration(e.estimated_min * 60) if e.estimated_min else ""])
        for c in range(6):
            it.setText(c, to_fa_digits(it.text(c)))
        it.setData(0, Qt.UserRole, e.id)
        if e.column in ("done", "cancelled"):
            f = it.font(0); f.setStrikeOut(True); it.setFont(0, f)
        if e.is_overdue():
            it.setForeground(3, Qt.red)
        (parent.addChild if parent is not None else tree.addTopLevelItem)(it)
        return it
    for e in tops:
        parent = None
        if group:
            k = gkey(e)
            if k not in holders:
                h = QTreeWidgetItem([k]); h.setFlags(h.flags() & ~Qt.ItemIsDragEnabled); f = h.font(0); f.setBold(True); h.setFont(0, f); tree.addTopLevelItem(h); holders[k] = h; h.setExpanded(True)
            parent = holders[k]
        row = add_row(parent, e)
        for k in sorted(kids.get(e.id, []), key=lambda x: (x.rank, x.created_at)):
            add_row(row, k)
        row.setExpanded(True)
    win.tk_info.setText(to_fa_digits(f"{len(tops)} {S['tasks']}  ·  {S['drag_hint']}"))


# =================================================================== BOARD
class BoardList(QListWidget):
    """One column. Dropping a card here re-ranks the column and fires the liquid effects."""

    def __init__(self, column: str, win) -> None:
        super().__init__()
        self.column, self.win = column, win
        self.setDragDropMode(QAbstractItemView.DragDrop); self.setDefaultDropAction(Qt.MoveAction); self.setCursor(Qt.PointingHandCursor)
        self.setSelectionMode(QAbstractItemView.SingleSelection); self.setSpacing(5); self.setWordWrap(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def startDrag(self, actions) -> None:  # noqa: N802
        fx = self.win.theme.fx
        if fx is not None:
            fx.drag_started()
        try:
            super().startDrag(actions)
        finally:
            if fx is not None:
                fx.drag_finished()

    def dropEvent(self, e) -> None:  # noqa: N802
        src = e.source()
        ids = [i.data(Qt.UserRole) for i in src.selectedItems()] if isinstance(src, QListWidget) else []
        super().dropEvent(e)
        db = self.win.db
        try:
            with db.transaction():
                for eid in ids:
                    t = db.get(TimeEntry, eid)
                    if t is not None and t.column != self.column:
                        self.win.projects_svc.move(eid, self.column)
                for i in range(self.count()):                          # new manual order of this column
                    eid = self.item(i).data(Qt.UserRole)
                    t = db.get(TimeEntry, eid)
                    if t is not None:
                        t.rank = float(i * 10); db.save(t)
        except ValueError:
            self.win.toast(S["blocked"])
        self.win.refresh_all()


def build_board(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_task"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: open_task(win, defaults={"column": "backlog"}))
    lay.addLayout(_title_row(win, S["board"], add))
    bar = QHBoxLayout(); win.bd_search = QLineEdit(placeholderText=S["search"]); win.bd_search.textChanged.connect(lambda _t: refresh_board(win))
    win.bd_proj = QComboBox(); win.bd_proj.currentIndexChanged.connect(lambda _i: refresh_board(win)); win.bd_proj.setCursor(Qt.PointingHandCursor)
    bar.addWidget(win.bd_search, 2); bar.addWidget(win.bd_proj, 1); lay.addLayout(bar)
    win.bd_cols = {}; win.bd_titles = {}
    host = QWidget(); hl = QHBoxLayout(host); hl.setSpacing(12); hl.setContentsMargins(0, 0, 0, 0)
    for c in ALL_COLUMNS:
        card = win.card(); cl = QVBoxLayout(card); cl.setContentsMargins(12, 10, 12, 12)
        head = QHBoxLayout(); t = win.label(tf.COLUMN_LABELS[c], 11, True); win.bd_titles[c] = t; head.addWidget(t, 1)
        ab = GlassButton("", win.theme, icon="plus"); ab.setFixedSize(34, 34); ab.clicked.connect(lambda _c=False, col=c: open_task(win, defaults={"column": col})); head.addWidget(ab)
        cl.addLayout(head)
        lw = BoardList(c, win); lw.itemDoubleClicked.connect(lambda it: open_task(win, win.db.get(TimeEntry, it.data(Qt.UserRole))))
        lw.setContextMenuPolicy(Qt.CustomContextMenu); lw.customContextMenuRequested.connect(lambda pos, w=lw: task_menu(win, w, pos))
        win.bd_cols[c] = (card, lw); cl.addWidget(lw, 1); card.setMinimumWidth(230); hl.addWidget(card, 1)
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def refresh_board(win) -> None:
    names, subs = _names(win), _subcount(win)
    cur = win.bd_proj.currentData()
    if win.bd_proj.count() != len(names) + 1:
        win.bd_proj.blockSignals(True); win.bd_proj.clear(); win.bd_proj.addItem(S["all_projects"], None)
        for pid, n in names.items():
            win.bd_proj.addItem(n, pid)
        win.bd_proj.setCurrentIndex(max(0, win.bd_proj.findData(cur))); win.bd_proj.blockSignals(False)
    proj, q = win.bd_proj.currentData(), win.bd_search.text().strip().lower()
    shown = set(win.db.get_setting("board_columns", ["backlog", "in_progress", "review", "done"]))
    wip = win.db.get_setting("wip_limits", {})
    groups: Dict[str, List[TimeEntry]] = {c: [] for c in ALL_COLUMNS}
    for e in win.db.all(TimeEntry):
        if e.parent_id or e.status == Status.RUNNING and e.column == "backlog" and False:
            continue
        if proj and e.project_id != proj or (q and q not in e.title.lower()):
            continue
        if e.source in ("auto", "prompt") and e.column in ("done",) and (now_utc() - (e.completed_at or e.start_utc)).days > 2:
            continue                                                 # old auto/prompt logs do not clutter the board
        groups.setdefault(e.column, []).append(e)
    for c, (card, lw) in win.bd_cols.items():
        card.setVisible(c in shown)
        lw.clear()
        items = sorted(groups.get(c, []), key=lambda x: (x.rank, x.priority, x.created_at))
        if c == "done":
            items = items[-60:]
        for e in items:
            it = QListWidgetItem(task_line(e, names, subs.get(e.id))); it.setData(Qt.UserRole, e.id)
            from PyQt5.QtGui import QColor
            it.setForeground(QColor(PRI_COLOR.get(e.priority, "#FFFFFF")) if e.priority <= 2 else QColor("#FFFFFF" if win.theme.dark else "#1b1b33"))
            lw.addItem(it)
        lim = int(wip.get(c, 0) or 0)
        over = lim and len(items) > lim
        win.bd_titles[c].setText(to_fa_digits(f"{tf.COLUMN_LABELS[c]}  ({len(items)}{'/' + str(lim) if lim else ''})") + ("  ⚠" if over else ""))


# =================================================================== CALENDAR
def arrow_icon(win, forward: bool) -> str:
    """Direction-correct chevron: "next" points left in RTL and right in LTR."""
    rtl = win.layoutDirection() == Qt.RightToLeft
    return "chevron_left" if forward == rtl else "chevron_right"


def build_calendar(win) -> None:
    page, lay = _page(win)
    today = to_tehran(now_utc()).date()
    win.cal_y, win.cal_m = views.today_ym(today); win.cal_sel = today
    prv = GlassButton("", win.theme, icon=arrow_icon(win, False)); prv.setFixedSize(42, 42); prv.clicked.connect(lambda: _cal_shift(win, -1))
    nxt = GlassButton("", win.theme, icon=arrow_icon(win, True)); nxt.setFixedSize(42, 42); nxt.clicked.connect(lambda: _cal_shift(win, 1))
    tod = GlassButton(S["today"], win.theme); tod.clicked.connect(lambda: _cal_today(win)); win.cal_title = win.label("", 16, True)
    head = QHBoxLayout(); head.addWidget(prv); head.addWidget(win.cal_title, 1); head.addWidget(nxt); head.addWidget(tod); lay.addLayout(head)
    body = QHBoxLayout(); body.setSpacing(12)
    gc = win.card(); win.cal_grid = QGridLayout(gc); win.cal_grid.setContentsMargins(12, 12, 12, 12); win.cal_grid.setSpacing(6); body.addWidget(gc, 3)
    side = win.card(); sl = QVBoxLayout(side); sl.setContentsMargins(14, 12, 14, 12); win.cal_day_lbl = win.label("", 12, True); sl.addWidget(win.cal_day_lbl)
    win.cal_list = QListWidget(); win.cal_list.setCursor(Qt.PointingHandCursor); win.cal_list.itemDoubleClicked.connect(lambda it: open_task(win, win.db.get(TimeEntry, it.data(Qt.UserRole)))); sl.addWidget(win.cal_list, 1)
    nb = GlassButton(S["new_task_this_day"], win.theme, primary=True, icon="plus"); nb.clicked.connect(lambda: _cal_new(win)); sl.addWidget(nb); body.addWidget(side, 1)
    lay.addLayout(body, 1); win.pages.addWidget(page)


def _cal_shift(win, d: int) -> None:
    win.cal_y, win.cal_m = views.shift_month(win.cal_y, win.cal_m, d); refresh_calendar(win)


def _cal_today(win) -> None:
    win.cal_sel = to_tehran(now_utc()).date(); win.cal_y, win.cal_m = views.today_ym(win.cal_sel); refresh_calendar(win)


def _cal_new(win) -> None:
    start = dt.datetime.combine(win.cal_sel, dt.time(9), tzinfo=to_tehran(now_utc()).tzinfo).astimezone(dt.timezone.utc)
    open_task(win, defaults={"start": start, "end": start + dt.timedelta(hours=1)})


def refresh_calendar(win) -> None:
    lay = views.month_layout(win.cal_y, win.cal_m)
    win.cal_title.setText(to_fa_digits(str(lay["title"])))
    g = win.cal_grid
    while g.count():
        it = g.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    for c, w in enumerate(lay["labels"]):
        l = win.label(w, 9, muted=True); l.setAlignment(Qt.AlignCenter); g.addWidget(l, 0, c)
        g.setColumnStretch(c, 1)
    first, n = lay["first"], lay["days"]
    by_day: Dict[dt.date, List[TimeEntry]] = {}
    for e in win.db.all(TimeEntry, "start_utc"):
        if e.parent_id:
            continue
        d = to_tehran(e.due_utc).date() if (e.due_utc and e.status == Status.PLANNED and e.end_utc is None) else to_tehran(e.start_utc).date()
        if first <= d < first + dt.timedelta(days=n):
            by_day.setdefault(d, []).append(e)
    today = to_tehran(now_utc()).date()
    greg = is_gregorian()
    for r, week in enumerate(lay["weeks"], 1):
        for c, date in enumerate(week):
            if date is None:
                continue
            items = by_day.get(date, [])
            num = date.day if greg else date_to_jalali(date)[2]
            txt = to_fa_digits(str(num)) + ("\n" + "\n".join(("• " + e.title[:14]) for e in items[:3]) + (f"\n+{len(items) - 3}" if len(items) > 3 else "") if items else "")
            b = chip_button(txt, True); b.setMinimumHeight(86); b.setChecked(date == win.cal_sel)
            css = "QPushButton{text-align:top left;}" + ("QPushButton{border:2px solid " + win.theme.accents[1] + ";}" if date == today else "")
            b.setStyleSheet(css)
            b.clicked.connect(lambda _c=False, x=date: _cal_pick(win, x)); g.addWidget(b, r, c)
    _cal_day(win)


def _cal_pick(win, d: dt.date) -> None:
    win.cal_sel = d; refresh_calendar(win)


def _cal_day(win) -> None:
    d = win.cal_sel; win.cal_day_lbl.setText(to_fa_digits(format_jalali(d, "{weekday} {d} {month_name}", fa_digits=False)))
    win.cal_list.clear(); names = _names(win)
    for e in win.db.all(TimeEntry, "start_utc"):
        if e.parent_id:
            continue
        ed = to_tehran(e.due_utc).date() if (e.due_utc and e.end_utc is None) else to_tehran(e.start_utc).date()
        if ed == d:
            hh = to_tehran(e.start_utc).strftime("%H:%M") if e.end_utc else "—"
            it = QListWidgetItem(to_fa_digits(f"{hh}  {task_line(e, names)}")); it.setData(Qt.UserRole, e.id); win.cal_list.addItem(it)


# =================================================================== PROJECTS (cards)
def build_projects(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_project"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: _open_project(win))
    lay.addLayout(_title_row(win, S["projects"], add))
    win.pr_host = QWidget(); win.pr_grid = QGridLayout(win.pr_host); win.pr_grid.setSpacing(12); win.pr_grid.setContentsMargins(0, 0, 0, 0)
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(win.pr_host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def _open_project(win, p: Optional[Project] = None) -> None:
    dlg = ProjectDialog(win, p)
    if dlg.exec_():
        win.refresh_all()


def refresh_projects(win) -> None:
    g = win.pr_grid
    while g.count():
        it = g.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    svc = win.projects_svc
    cols = max(1, min(3, (win.width() - (win.side.width() if hasattr(win, "side") else 200)) // 330))
    from .blueprints_view import summary_for
    for i, p in enumerate(win.db.all(Project, "name")):
        s = summary_for(win.db, p)
        c = win.card(); v = QVBoxLayout(c); v.setContentsMargins(18, 14, 18, 14); v.setSpacing(8)
        top = QHBoxLayout(); ic = QLabel(p.icon); ic.setStyleSheet("font-size:24pt;background:transparent;"); top.addWidget(ic)
        tt = QVBoxLayout(); tt.addWidget(win.label(p.name, 13, True)); tt.addWidget(win.label(to_fa_digits(f"{p.code}  ·  {S['ps_' + p.status.value]}"), 9, muted=True)); top.addLayout(tt, 1)
        dot = QLabel("●"); dot.setStyleSheet(f"color:{ {'on_track': '#2ED573', 'at_risk': '#FFB020', 'off_track': '#FF4757'}[s['health']] };font-size:16pt;background:transparent;"); dot.setToolTip(S["health_" + s["health"]]); top.addWidget(dot)
        v.addLayout(top)
        bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(int(s["progress"] * 100)); v.addWidget(bar)
        v.addWidget(win.label(to_fa_digits(f"{s['actual_hours']}h / {p.estimated_hours or '∞'}h  ·  {s['tasks']} {S['tasks']}" + (f"  ·  📅 {format_jalali(to_tehran(p.deadline).date())}" if p.deadline else "")), 9, muted=True))
        row = QHBoxLayout(); o = GlassButton(S["open"], win.theme, icon="pm"); o.clicked.connect(lambda _c=False, pid=p.id: _goto_pm(win, pid)); ed = GlassButton("", win.theme, icon="edit"); ed.setFixedSize(42, 40)
        ed.clicked.connect(lambda _c=False, pp=p: _open_project(win, pp)); row.addWidget(o, 1); row.addWidget(ed); v.addLayout(row)
        g.addWidget(c, i // cols, i % cols)


def _goto_pm(win, pid: str) -> None:
    from ..ui.main_window import PAGES
    win.goto(PAGES.index("pm")); idx = win.pm_project.findData(pid)
    if idx >= 0:
        win.pm_project.setCurrentIndex(idx)


# =================================================================== HABITS
def build_habits_page(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_habit"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: _open_habit(win))
    lay.addLayout(_title_row(win, S["habits"], add))
    win.hb_host = QWidget(); win.hb_grid = QGridLayout(win.hb_host); win.hb_grid.setSpacing(12); win.hb_grid.setContentsMargins(0, 0, 0, 0)
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(win.hb_host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def _open_habit(win, h: Optional[Habit] = None) -> None:
    if HabitDialog(win, h).exec_():
        win.refresh_all()


def refresh_habits_page(win) -> None:
    g = win.hb_grid
    while g.count():
        it = g.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    hs = HabitService(win.db); today = to_tehran(now_utc()).date()
    cols = max(1, min(3, (win.width() - 260) // 320))
    habits = win.db.all(Habit)
    if not habits:
        l = win.label(S["no_habits"], 12, muted=True); l.setAlignment(Qt.AlignCenter); g.addWidget(l, 0, 0)
    for i, h in enumerate(habits):
        c = win.card(); v = QVBoxLayout(c); v.setContentsMargins(18, 14, 18, 14); v.setSpacing(8)
        longest, cur = hs.streak(h.id, today)
        top = QHBoxLayout(); ic = QLabel(h.icon); ic.setStyleSheet("font-size:22pt;background:transparent;"); top.addWidget(ic)
        tt = QVBoxLayout(); tt.addWidget(win.label(h.name, 12, True)); tt.addWidget(win.label(to_fa_digits(f"🔥 {cur} {S['days']}  ·  {S['best']} {longest}"), 9, muted=True)); top.addLayout(tt, 1)
        ed = GlassButton("", win.theme, icon="edit"); ed.setFixedSize(40, 38); ed.clicked.connect(lambda _c=False, hh=h: _open_habit(win, hh)); top.addWidget(ed); v.addLayout(top)
        dots = QHBoxLayout()
        start = today - dt.timedelta(days=(today.weekday() + 2) % 7)
        for k in range(7):
            d = start + dt.timedelta(days=k); on = d.isoformat() in h.log; active = d.weekday() in h.days
            dot = QLabel("●" if on else "○"); dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet(f"font-size:15pt;background:transparent;color:{h.color if on else ('#888' if active else '#444')};")
            dot.setToolTip(format_jalali(d)); dots.addWidget(dot)
        v.addLayout(dots)
        pct = int(hs.week_completion(h.id, today) * 100); bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(pct); v.addWidget(bar)
        done = today.isoformat() in h.log
        b = GlassButton(S["done_today"] if done else S["check_in"], win.theme, primary=not done, icon="check"); b.clicked.connect(lambda _c=False, hid=h.id, dn=done: _toggle_habit(win, hid, dn)); v.addWidget(b)
        g.addWidget(c, i // cols, i % cols)


# =================================================================== GOALS
def build_goals(win) -> None:
    page, lay = _page(win)
    add = GlassButton(S["new_goal"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: _open_goal(win))
    lay.addLayout(_title_row(win, S["goals"], add))
    win.gl_host = QWidget(); win.gl_grid = QGridLayout(win.gl_host); win.gl_grid.setSpacing(12); win.gl_grid.setContentsMargins(0, 0, 0, 0)
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(win.gl_host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def _open_goal(win, g: Optional[Goal] = None) -> None:
    dlg = GoalDialog(win, g)
    if dlg.exec_():
        if getattr(dlg, "smart_problems", None):
            win.toast("SMART: " + " | ".join(dlg.smart_problems))
        win.refresh_all()


def refresh_goals(win) -> None:
    g = win.gl_grid
    while g.count():
        it = g.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    cols = max(1, min(2, (win.width() - 260) // 460))
    goals = win.db.all(Goal)
    if not goals:
        l = win.label(S["no_goals"], 12, muted=True); l.setAlignment(Qt.AlignCenter); g.addWidget(l, 0, 0)
    for i, goal in enumerate(goals):
        c = win.card(); h = QHBoxLayout(c); h.setContentsMargins(18, 14, 18, 14)
        ring = Ring(win.theme); ring.setFixedSize(104, 104); ring.set_value(goal.progress, to_fa_digits(f"{int(goal.progress * 100)}٪")); h.addWidget(ring)
        v = QVBoxLayout(); top = QHBoxLayout(); top.addWidget(win.label(goal.name, 12, True), 1)
        ed = GlassButton("", win.theme, icon="edit"); ed.setFixedSize(40, 38); ed.clicked.connect(lambda _c=False, gg=goal: _open_goal(win, gg)); top.addWidget(ed); v.addLayout(top)
        if goal.deadline:
            v.addWidget(win.label("📅 " + format_jalali(to_tehran(goal.deadline).date()), 9, muted=True))
        for k in goal.key_results[:5]:
            bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(int(min(1.0, float(k.get("current", 0)) / float(k["target"])) * 100) if float(k.get("target", 0)) else 0)
            bar.setFormat(to_fa_digits(f"{k['name']}  {k.get('current', 0)}/{k['target']} {k.get('unit', '')}")); v.addWidget(bar)
        h.addLayout(v, 1); g.addWidget(c, i // cols, i % cols)
