"""Client reports page: pick a project and a report type, generate a draft, edit the executive summary, approve it, open it in the browser or export the PDF.
Nothing is ever sent without your approval. Rules: reports/ (builders, render, pdf, service)."""
from __future__ import annotations

import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit, QVBoxLayout, QWidget

from ..core.crm import Store
from ..core.models import Project
from ..core.persian import now_utc, to_fa_digits, tr
from ..reports import builders, service
from ..reports.builders import ReportError
from .forms import DateTimeField, Segmented
from .glass import GlassButton
from .strings import S

log = logging.getLogger("worktracker.client_reports_ui")
KIND_LABEL = {"daily": "cr_daily", "weekly": "cr_weekly", "milestone": "cr_milestone", "invoice": "cr_invoice", "snapshot": "cr_snapshot"}


def build_client_reports(win) -> None:
    page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12)
    lay.addWidget(win.label(S["client_reports"], 17, True)); lay.addWidget(win.label(S["cr_hint"], 9, muted=True))
    card = win.card(); c = QVBoxLayout(card); c.setContentsMargins(16, 12, 16, 14); c.setSpacing(8)
    row = QHBoxLayout(); win.cr_proj = QComboBox(); win.cr_proj.currentIndexChanged.connect(lambda _i: _reload_milestones(win)); row.addWidget(win.cr_proj, 2)
    win.cr_ms = QComboBox(); row.addWidget(win.cr_ms, 2); c.addLayout(row)
    win.cr_kind = Segmented([(S[KIND_LABEL[k]], k) for k in builders.KINDS], wrap=True); win.cr_kind.changed.connect(lambda k: win.cr_ms.setVisible(k == "milestone")); c.addWidget(win.cr_kind)
    pr = QHBoxLayout(); win.cr_from, win.cr_to = DateTimeField(with_time=False), DateTimeField(with_time=False)
    pr.addWidget(QLabel(S["rp_from"])); pr.addWidget(win.cr_from); pr.addWidget(QLabel(S["rp_to"])); pr.addWidget(win.cr_to); pr.addStretch()
    gen = GlassButton(S["cr_generate"], win.theme, primary=True, icon="reports"); gen.clicked.connect(lambda: generate(win)); pr.addWidget(gen); c.addLayout(pr)
    lay.addWidget(card)
    body = QHBoxLayout(); body.setSpacing(12)
    left = win.card(); ll = QVBoxLayout(left); ll.setContentsMargins(16, 12, 16, 14)
    win.cr_info = win.label("", 10, True); win.cr_info.setWordWrap(True); ll.addWidget(win.cr_info)
    ll.addWidget(win.label(S["cr_summary"], 9, muted=True)); win.cr_text = QPlainTextEdit(); win.cr_text.setMinimumHeight(150); ll.addWidget(win.cr_text)
    win.cr_diff = win.label("", 9, muted=True); win.cr_diff.setWordWrap(True); ll.addWidget(win.cr_diff)
    r2 = QHBoxLayout(); r2.setSpacing(6)
    for key, ic, fn, primary in (("cr_save", "check", lambda: save_summary(win), False), ("cr_approve", "check", lambda: approve(win), True), ("cr_open", "eye", lambda: open_html(win), False),
                                 ("cr_pdf", "download", lambda: export_pdf(win), False), ("cr_copy", "copy", lambda: copy_summary(win), False)):
        b = GlassButton(S[key], win.theme, primary=primary, icon=ic); b.clicked.connect(lambda _c=False, f=fn: f()); r2.addWidget(b)
    ll.addLayout(r2); body.addWidget(left, 3)
    right = win.card(); rl = QVBoxLayout(right); rl.setContentsMargins(14, 12, 14, 12); rl.addWidget(win.label(S["cr_history"], 11, True))
    win.cr_list = QListWidget(); win.cr_list.setMinimumHeight(280); win.cr_list.currentItemChanged.connect(lambda *_a: _load_selected(win)); rl.addWidget(win.cr_list, 1); body.addWidget(right, 2)
    lay.addLayout(body, 1)
    win.pages.addWidget(page)
    win.cr_ms.hide()


def _reload_milestones(win) -> None:
    win.cr_ms.clear()
    pid = win.cr_proj.currentData()
    if pid:
        for m in Store(win.db).rows("milestones", "project_id=?", (pid,), "ord, due"):
            win.cr_ms.addItem(m["name"], m["id"])


def refresh_client_reports(win) -> None:
    keep = win.cr_proj.currentData()
    win.cr_proj.blockSignals(True); win.cr_proj.clear()
    for p in sorted(win.db.all(Project), key=lambda x: x.name.lower()):
        win.cr_proj.addItem(p.name, p.id)
    win.cr_proj.setCurrentIndex(max(0, win.cr_proj.findData(keep))); win.cr_proj.blockSignals(False)
    if not win.cr_ms.count():
        _reload_milestones(win)
    _fill_list(win)


def _fill_list(win, select: Optional[str] = None) -> None:
    pid = win.cr_proj.currentData()
    win.cr_list.blockSignals(True); win.cr_list.clear()
    for r in service.list_reports(win.db, pid):
        it = QListWidgetItem(to_fa_digits(f"{r['number']}   ·   {S['cr_st_' + r['status']]}   ·   {r['generated_at'][:10]}")); it.setData(Qt.UserRole, r["id"]); win.cr_list.addItem(it)
        if r["id"] == select:
            win.cr_list.setCurrentItem(it)
    win.cr_list.blockSignals(False)


def _current(win, report_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if report_id:
        return service.get(win.db, report_id)
    it = win.cr_list.currentItem()
    return service.get(win.db, it.data(Qt.UserRole)) if it is not None else None


def _show(win, r: Dict[str, Any]) -> None:
    d = r["payload"]
    h = d["health"]["status"].replace("_", " ")
    win.cr_info.setText(to_fa_digits(f"{r['number']}  ·  {S['cr_st_' + r['status']]}  ·  {d['header']['period_label']}  ·  {d['progress']['pct']:.0f}%  ·  {h}  ·  {len(d['waiting_on_client'])} {S['cr_waiting']}"))
    win.cr_text.setPlainText(r["summary"])
    win.cr_diff.setText("\n".join(service.diff(win.db, r["id"])["lines"]))


def _load_selected(win) -> None:
    r = _current(win)
    if r is not None:
        _show(win, r)


def generate(win, pid: Optional[str] = None, kind: Optional[str] = None, start: Optional[dt.date] = None, end: Optional[dt.date] = None, milestone_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Build a draft report. Arguments default to what the widgets show (they are explicit so the logic is testable without a display)."""
    pid = pid or win.cr_proj.currentData()
    if not pid:
        win.toast(S["sp_need_project"]); return None
    kind = kind or win.cr_kind.value()
    opts: Dict[str, Any] = {}
    if kind == "milestone":
        opts["milestone_id"] = milestone_id or win.cr_ms.currentData()
    if start is None and end is None:
        a, b = win.cr_from.value(), win.cr_to.value()
        start, end = (a.date() if a else None), (b.date() if b else None)
    try:
        r = service.generate(win.db, win.data_dir, pid, kind, start, end, now_utc(), opts)
    except (ReportError, KeyError, ValueError) as exc:
        win.toast(str(exc)); return None
    if win.theme.fx is not None:
        win.theme.fx.play("success")
    _fill_list(win, r["id"]); _show(win, r)
    return r


def save_summary(win, report_id: Optional[str] = None, text: Optional[str] = None) -> None:
    r = _current(win, report_id)
    if r is None:
        win.toast(S["cu_pick"]); return
    try:
        service.update_summary(win.db, win.data_dir, r["id"], win.cr_text.toPlainText() if text is None else text)
    except service.ReportStateError as exc:
        win.toast(str(exc)); return
    win.toast(S["saved"]); _fill_list(win, r["id"])


def approve(win, report_id: Optional[str] = None, text: Optional[str] = None) -> None:
    r = _current(win, report_id)
    if r is None:
        win.toast(S["cu_pick"]); return
    try:
        service.update_summary(win.db, win.data_dir, r["id"], win.cr_text.toPlainText() if text is None else text)
        service.approve(win.db, r["id"])
    except service.ReportStateError as exc:
        win.toast(str(exc)); return
    win.toast(S["cr_approved"]); _fill_list(win, r["id"])


def open_html(win, report_id: Optional[str] = None) -> None:
    r = _current(win, report_id)
    if r is None:
        win.toast(S["cu_pick"]); return
    from PyQt5.QtGui import QDesktopServices
    QDesktopServices.openUrl(QUrl.fromLocalFile(r["html_path"]))


def export_pdf(win, dest: Optional[str] = None, report_id: Optional[str] = None) -> Optional[Path]:
    r = _current(win, report_id)
    if r is None:
        win.toast(S["cu_pick"]); return None
    try:
        out = service.ensure_pdf(win.db, win.data_dir, r["id"], win.data_dir / "assets")
    except Exception as exc:  # noqa: BLE001 - UI boundary
        log.exception("pdf failed"); win.toast(str(exc)); return None
    if dest is None:
        dest, _ = QFileDialog.getSaveFileName(win, S["cr_pdf"], f"{r['number']}.pdf", "PDF (*.pdf)")
    if dest:
        shutil.copyfile(out, dest); win.toast(S["saved"])
        return Path(dest)
    return out


def copy_summary(win) -> None:
    from PyQt5.QtWidgets import QApplication
    QApplication.clipboard().setText(win.cr_text.toPlainText()); win.toast(S["dr_copied"])
