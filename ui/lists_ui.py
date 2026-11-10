"""Lists page (Google-Tasks style, but with more): columns of check lists - tick to complete, drag a task into another list or to a new position, star, sub-tasks, paste a whole
check list at once, sort by due date, clear completed, and two-way Google Tasks sync when connected. Rules live in services/lists.py."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QPlainTextEdit, QScrollArea, QVBoxLayout,
                             QWidget)

from ..core.models import TimeEntry
from ..core.persian import format_jalali, now_utc, to_fa_digits, to_tehran, tr
from ..services import lists as L, outline, project_split as ps
from .dialogs import PopDialog, confirm
from .forms import FlowLayout, Section, Segmented, chip_button
from .glass import GlassButton
from .strings import S

log = logging.getLogger("worktracker.lists_ui")


class BulkDialog(PopDialog):
    """Paste a check list; see how it will be read before adding."""

    def __init__(self, win, list_id: str) -> None:
        super().__init__(win, S["ls_bulk_title"], "tasks", 640)
        self.list_id, self.created = list_id, []
        self.text = QPlainTextEdit(); self.text.setMinimumHeight(220); self.text.setPlaceholderText(S["ls_bulk_example"]); self.text.textChanged.connect(self._preview)
        self.info = QLabel(""); self.info.setProperty("muted", True); self.info.setWordWrap(True)
        self.body.addWidget(win.label(S["ls_bulk_hint"], 9, muted=True)); self.body.addWidget(self.text, 1); self.body.addWidget(self.info)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["add"], self.theme, primary=True, icon="plus"); ok.clicked.connect(self._ok); self.buttons(cancel, ok)

    def _preview(self) -> None:
        roots = outline.parse(self.text.toPlainText(), max_depth=2)
        n = sum(1 for r in roots for _ in r.walk())
        subs = sum(len(r.children) for r in roots)
        done = sum(1 for r in roots for x in r.walk() if x.done)
        self.info.setText(to_fa_digits(S["ls_bulk_preview"].format(n=n, s=subs, d=done)) if n else "")

    def _ok(self) -> None:
        try:
            self.created = L.bulk_add(self.db, self.list_id, self.text.toPlainText())
        except L.ListError as exc:
            self.show_error(str(exc)); return
        self.accept()


class SplitTaskDialog(PopDialog):
    """Split one big task into sub-tasks (the estimate is shared)."""

    def __init__(self, win, entry: TimeEntry) -> None:
        super().__init__(win, S["ls_split_title"], "tasks", 600)
        self.entry, self.created = entry, []
        self.text = QPlainTextEdit(); self.text.setMinimumHeight(180); self.text.setPlaceholderText(S["ls_split_example"])
        self.body.addWidget(win.label(to_fa_digits(f"{entry.title}  ·  {entry.estimated_min} {S['min']}"), 11, True)); self.body.addWidget(win.label(S["ls_split_hint"], 9, muted=True)); self.body.addWidget(self.text, 1)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["ls_split_go"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._ok); self.buttons(cancel, ok)

    def _ok(self) -> None:
        lines = [l.strip().lstrip("-*•[] xX").strip() for l in self.text.toPlainText().splitlines()]
        try:
            self.created = ps.split_task(self.db, self.entry.id, lines)
        except ps.SplitError as exc:
            self.show_error(str(exc)); return
        self.accept()


class BreakdownDialog(PopDialog):
    """Project from an outline: phases -> tasks -> sub-tasks, with a live preview and ready templates."""

    def __init__(self, win, project_id: str) -> None:
        super().__init__(win, S["bd_title"], "pm", 760)
        self.project_id, self.result = project_id, None
        tmpl = QWidget(); fl = FlowLayout(tmpl)
        for key, label in (("book", S["bd_book"]), ("product", S["bd_product"]), ("course", S["bd_course"])):
            b = chip_button(label); b.clicked.connect(lambda _c=False, k=key: self.text.setPlainText(ps.template(k))); fl.addWidget(b)
        self.text = QPlainTextEdit(); self.text.setMinimumHeight(240); self.text.setPlaceholderText(S["bd_example"]); self.text.textChanged.connect(self._preview)
        from PyQt5.QtWidgets import QSpinBox
        self.days = QSpinBox(); self.days.setRange(1, 365); self.days.setValue(14); self.days.setSuffix(" " + S["days"])
        self.info = QLabel(""); self.info.setWordWrap(True); self.info.setProperty("accent", True)
        sec = Section(S["bd_templates"]); sec.add("", tmpl); sec.add(S["bd_phase_days"], self.days)
        self.body.addWidget(sec); self.body.addWidget(win.label(S["bd_hint"], 9, muted=True)); self.body.addWidget(self.text, 1); self.body.addWidget(self.info)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["bd_go"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._ok); self.buttons(cancel, ok)

    def _preview(self) -> None:
        pv = ps.preview(self.text.toPlainText())
        self.info.setText(to_fa_digits(S["bd_preview"].format(p=pv["phases"], t=pv["tasks"], s=pv["subtasks"], h=pv["estimate_hours"])) if (pv["tasks"] or pv["phases"]) else "")

    def _ok(self) -> None:
        try:
            self.result = ps.apply_outline(self.db, self.project_id, self.text.toPlainText(), phase_days=self.days.value())
        except ps.SplitError as exc:
            self.show_error(str(exc)); return
        self.accept()


# ======================================================================= the page
class ListColumn(QListWidget):
    """One list. Tick = complete, drag = reorder or move to another list."""

    def __init__(self, win, list_id: str) -> None:
        super().__init__()
        self.win, self.list_id, self._loading = win, list_id, False
        self.setDragDropMode(QAbstractItemView.DragDrop); self.setDefaultDropAction(Qt.MoveAction); self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setCursor(Qt.PointingHandCursor); self.setSpacing(2); self.setWordWrap(True); self.setMinimumWidth(260); self.setMinimumHeight(220)
        self.setContextMenuPolicy(Qt.CustomContextMenu); self.customContextMenuRequested.connect(self._menu)
        self.itemChanged.connect(self._ticked); self.itemDoubleClicked.connect(self._edit)

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
        moved = [i.data(Qt.UserRole) for i in src.selectedItems() if i.data(Qt.UserRole)] if isinstance(src, ListColumn) else []
        super().dropEvent(e)
        db = self.win.db
        order = [self.item(i).data(Qt.UserRole) for i in range(self.count()) if self.item(i).data(Qt.UserRole + 1) is None and self.item(i).data(Qt.UserRole)]
        try:
            for eid in moved:
                if src is not self and eid in order:
                    L.move(db, eid, self.list_id, order.index(eid))
            L.reorder(db, self.list_id, order)
        except (L.ListError, KeyError) as exc:
            self.win.toast(str(exc))
        refresh_lists(self.win)

    def _ticked(self, item: QListWidgetItem) -> None:
        if self._loading or not item.data(Qt.UserRole):
            return
        now_done = item.checkState() == Qt.Checked
        try:
            if L.is_done(self.win.db.get(TimeEntry, item.data(Qt.UserRole))) != now_done:
                L.toggle(self.win.db, item.data(Qt.UserRole))
        except KeyError:
            pass
        if self.win.theme.fx is not None:
            self.win.theme.fx.play("success" if now_done else "click", 0.8)
        self._loading = True
        refresh_lists(self.win)

    def _edit(self, item: QListWidgetItem) -> None:
        from .pages_new import open_task
        e = self.win.db.get(TimeEntry, item.data(Qt.UserRole)) if item.data(Qt.UserRole) else None
        if e is not None and open_task(self.win, e) is not None:
            refresh_lists(self.win)

    def _menu(self, pos) -> None:
        it = self.itemAt(pos)
        if it is None or not it.data(Qt.UserRole):
            return
        eid, db, win = it.data(Qt.UserRole), self.win.db, self.win
        m = QMenu(win)
        m.addAction(S["edit"], lambda: self._edit(it))
        m.addAction(S["ls_star"], lambda: (L.star(db, eid), refresh_lists(win)))
        m.addAction(S["add_subtask"], lambda: _add_sub(win, eid))
        m.addAction(S["ls_split"], lambda: _split(win, eid))
        m.addAction(S["ls_indent"], lambda: (L.indent(db, eid), refresh_lists(win)))
        m.addAction(S["ls_outdent"], lambda: (L.outdent(db, eid), refresh_lists(win)))
        mv = m.addMenu(S["move_to"])
        for l in L.lists(db):
            if l["id"] != self.list_id:
                mv.addAction(l["name"], lambda lid=l["id"]: (L.move(db, eid, lid, 0), refresh_lists(win)))
        m.addAction(S["delete"], lambda: (L.delete_task(db, eid), refresh_lists(win)))
        m.exec_(self.viewport().mapToGlobal(pos))


def _add_sub(win, parent_id: str) -> None:
    t, ok = QInputDialog.getText(win, S["add_subtask"], S["subtask_hint"])
    if ok and t.strip():
        p = win.db.get(TimeEntry, parent_id)
        try:
            L.add_task(win.db, p.extra.get("list", "default"), t, parent_id=parent_id)
        except L.ListError as exc:
            win.toast(str(exc))
        refresh_lists(win)


def _split(win, eid: str) -> None:
    e = win.db.get(TimeEntry, eid)
    if e is not None:
        dlg = SplitTaskDialog(win, e)
        if dlg.exec_():
            refresh_lists(win)


def build_lists(win) -> None:
    page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12)
    head = QHBoxLayout(); head.addWidget(win.label(S["lists"], 17, True), 1)
    win.ls_sync = GlassButton(S["ls_sync"], win.theme, icon="refresh"); win.ls_sync.clicked.connect(lambda: sync_google(win)); head.addWidget(win.ls_sync)
    add = GlassButton(S["ls_new_list"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: new_list(win)); head.addWidget(add)
    lay.addLayout(head)
    win.ls_status = win.label("", 9, muted=True); lay.addWidget(win.ls_status)
    win.ls_host = QWidget(); win.ls_row = QHBoxLayout(win.ls_host); win.ls_row.setSpacing(12); win.ls_row.setContentsMargins(0, 0, 0, 0)
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(win.ls_host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def new_list(win) -> None:
    t, ok = QInputDialog.getText(win, S["ls_new_list"], S["name"])
    if ok:
        try:
            L.add_list(win.db, t)
        except L.ListError as exc:
            win.toast(str(exc))
        refresh_lists(win)


def _quick_add(win, list_id: str, edit: QLineEdit) -> None:
    t = edit.text().strip()
    if not t:
        return
    try:
        L.bulk_add(win.db, list_id, t.replace(";", "\n"))
    except L.ListError as exc:
        win.toast(str(exc)); return
    edit.clear()
    if win.theme.fx is not None:
        win.theme.fx.play("drop_in", 0.8)
    refresh_lists(win)


def _bulk(win, list_id: str) -> None:
    dlg = BulkDialog(win, list_id)
    if dlg.exec_():
        win.toast(to_fa_digits(f"{len(dlg.created)} {S['ls_added']}")); refresh_lists(win)


def _rename(win, l: Dict) -> None:
    t, ok = QInputDialog.getText(win, S["ls_rename"], S["name"], text=l["name"])
    if ok:
        try:
            L.rename_list(win.db, l["id"], t)
        except L.ListError as exc:
            win.toast(str(exc))
        refresh_lists(win)


def _delete_list(win, l: Dict) -> None:
    items = [x for x in L.lists(win.db) if x["id"] != l["id"]]
    if not items:
        win.toast(S["ls_last_list"]); return
    if confirm(win, S["ls_delete_confirm"]):
        L.delete_list(win.db, l["id"], move_to=items[0]["id"]); refresh_lists(win)


def refresh_lists(win) -> None:
    db = win.db
    L.ensure_default(db)
    while win.ls_row.count():
        it = win.ls_row.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
    from PyQt5.QtGui import QColor, QFont
    for l in L.lists(db):
        card = win.card(); v = QVBoxLayout(card); v.setContentsMargins(12, 10, 12, 12); v.setSpacing(8); card.setMinimumWidth(290)
        o, d = L.counts(db, l["id"])
        top = QHBoxLayout(); top.addWidget(win.label(to_fa_digits(f"{l['name']}  ({o})"), 12, True), 1)
        for ic, tip, fn in (("note", S["ls_bulk_title"], lambda _c=False, x=l: _bulk(win, x["id"])), ("edit", S["ls_rename"], lambda _c=False, x=l: _rename(win, x)),
                            ("trash", S["ls_delete"], lambda _c=False, x=l: _delete_list(win, x))):
            b = GlassButton("", win.theme, icon=ic); b.setFixedSize(34, 34); b.setToolTip(tip); b.clicked.connect(fn); top.addWidget(b)
        v.addLayout(top)
        edit = QLineEdit(placeholderText=S["ls_add_hint"]); edit.returnPressed.connect(lambda ed=edit, x=l: _quick_add(win, x["id"], ed)); v.addWidget(edit)
        col = ListColumn(win, l["id"]); col._loading = True
        for e in L.tasks(db, l["id"]):
            for sub, depth in [(e, 0)] + [(c, 1) for c in L.children(db, e.id) if c.column != "cancelled"]:
                due = f"   ·   {format_jalali(to_tehran(sub.due_utc).date())}" if sub.due_utc else ""
                est = f"   ·   {sub.estimated_min}{S['min'][0]}" if sub.estimated_min else ""
                item = QListWidgetItem(to_fa_digits(("      ↳ " if depth else "") + ("★ " if sub.important else "") + sub.title + est + due))
                item.setData(Qt.UserRole, sub.id)
                if depth:
                    item.setData(Qt.UserRole + 1, "child")
                flags = item.flags() | Qt.ItemIsUserCheckable
                item.setFlags((flags | Qt.ItemIsDragEnabled) if not depth else (flags & ~Qt.ItemIsDragEnabled))
                item.setCheckState(Qt.Checked if L.is_done(sub) else Qt.Unchecked)
                if L.is_done(sub):
                    f = QFont(item.font()); f.setStrikeOut(True); item.setFont(f); item.setForeground(QColor("#8A93B8"))
                col.addItem(item)
        col._loading = False
        v.addWidget(col, 1)
        foot = QHBoxLayout()
        sort = GlassButton(S["ls_sort_due"], win.theme, icon="calendar"); sort.clicked.connect(lambda _c=False, x=l: (L.sort_by_due(db, x["id"]), refresh_lists(win)))
        clear = GlassButton(to_fa_digits(f"{S['ls_clear']} ({d})"), win.theme, icon="trash"); clear.setEnabled(d > 0)
        clear.clicked.connect(lambda _c=False, x=l: (L.clear_completed(db, x["id"]), refresh_lists(win)) if confirm(win, S["confirm_delete"]) else None)
        foot.addWidget(sort); foot.addWidget(clear); v.addLayout(foot)
        win.ls_row.addWidget(card)
    last = db.get_setting("gtasks_last_sync")
    win.ls_status.setText(to_fa_digits(S["ls_last_sync"] + ": " + (format_jalali(to_tehran(__import__("datetime").datetime.fromisoformat(last)).date()) if last else S["bk_never"])))


def sync_google(win) -> None:
    """Two-way sync with Google Tasks, in a worker thread so the window never freezes."""
    import threading
    from PyQt5.QtCore import QTimer
    from ..integrations.google_tasks import GoogleTasksSync, build_tasks_service
    svc = win._gtasks_service or build_tasks_service(win.data_dir)
    if svc is None:
        win.toast(S["ls_google_missing"]); return
    win._gtasks_service = svc
    result: Dict = {}

    def work() -> None:
        try:
            from ..core.database import Database
            db2 = Database(win.db.path)                          # SQLite connections belong to their thread: the worker opens its own
            result["rep"] = GoogleTasksSync(db2, svc).sync(); db2.close()
        except Exception as exc:  # noqa: BLE001
            log.exception("google tasks sync failed"); result["err"] = str(exc)
    threading.Thread(target=work, daemon=True).start()
    timer = QTimer(win); timer.setInterval(400)

    def poll() -> None:
        if result:
            timer.stop()
            win.toast(("⚠ " + result["err"]) if "err" in result else to_fa_digits(f"{S['ls_synced']} · {result['rep'].changes}"))
            refresh_lists(win)
    timer.timeout.connect(poll); timer.start(); win._gsync_timer = timer
