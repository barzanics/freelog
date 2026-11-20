"""Catch-up page: everything that slipped, ranked, with a realistic plan to clear it and one-click honest actions (done / start / tomorrow / +3 days / next week / split / drop).
All the rules are in services/catchup.py; this file only shows them."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QScrollArea, QSpinBox, QVBoxLayout, QWidget

from ..core.models import TimeEntry
from ..core.persian import format_jalali, to_fa_digits, to_tehran, tr
from ..services import catchup as cu, routines as rt
from .glass import GlassButton
from .strings import S

log = logging.getLogger("worktracker.catchup_ui")
ACTION_KEY = {"now": "cu_a_now", "today": "cu_a_today", "schedule": "cu_a_schedule", "split": "cu_a_split", "drop": "cu_a_drop"}


def _line(it: Dict[str, Any]) -> str:
    bits = [it["title"]]
    if it["project"]:
        bits.append(it["project"])
    if it["days_overdue"]:
        bits.append(f"{it['days_overdue']} {S['cu_days_late']}")
    if it["postponed"]:
        bits.append(f"↻ {it['postponed']}×")
    bits.append(f"{it['est_min']}{S['min'][0]}")
    return to_fa_digits("  ·  ".join(bits) + f"   →  {S[ACTION_KEY[it['action']]]}")


def build_catchup(win) -> None:
    page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12)
    head = QHBoxLayout(); head.addWidget(win.label(S["catchup"], 17, True), 1)
    win.cu_cap = QSpinBox(); win.cu_cap.setRange(60, 900); win.cu_cap.setSingleStep(30); win.cu_cap.setSuffix(" " + S["min"]); win.cu_cap.setValue(int(win.db.get_setting("catchup_capacity_min", cu.DEFAULT_CAPACITY)))
    win.cu_days = QSpinBox(); win.cu_days.setRange(1, 14); win.cu_days.setSuffix(" " + S["days"]); win.cu_days.setValue(int(win.db.get_setting("catchup_days", 3)))
    for w in (win.cu_cap, win.cu_days):
        w.valueChanged.connect(lambda _v: (win.db.set_setting("catchup_capacity_min", win.cu_cap.value()), win.db.set_setting("catchup_days", win.cu_days.value()), refresh_catchup(win)))
        head.addWidget(w)
    apply_b = GlassButton(S["cu_apply"], win.theme, primary=True, icon="check"); apply_b.clicked.connect(lambda: apply_plan(win)); head.addWidget(apply_b)
    lay.addLayout(head)
    win.cu_summary = win.label("", 10); win.cu_summary.setWordWrap(True); lay.addWidget(win.cu_summary)
    body = QHBoxLayout(); body.setSpacing(12)
    left = win.card(); ll = QVBoxLayout(left); ll.setContentsMargins(14, 12, 14, 12); ll.addWidget(win.label(S["cu_slipped"], 11, True))
    win.cu_list = QListWidget(); win.cu_list.setMinimumHeight(260); win.cu_list.setWordWrap(True); ll.addWidget(win.cu_list, 1)
    row = QHBoxLayout(); row.setSpacing(6)
    for key, ic, fn in (("cu_done", "check", lambda i: cu.complete(win.db, i)), ("cu_start", "play", lambda i: _start(win, i)), ("cu_tomorrow", "calendar", lambda i: _push(win, i, "tomorrow")),
                        ("cu_3days", "calendar", lambda i: _push(win, i, "in_3_days")), ("cu_week", "calendar", lambda i: _push(win, i, "next_week")), ("cu_split", "tasks", lambda i: _split(win, i)),
                        ("cu_drop", "trash", lambda i: cu.drop(win.db, i, "catch-up"))):
        b = GlassButton(S[key], win.theme, icon=ic); b.clicked.connect(lambda _c=False, f=fn: _act(win, f)); row.addWidget(b)
    ll.addLayout(row); body.addWidget(left, 3)
    right = win.card(); rl = QVBoxLayout(right); rl.setContentsMargins(14, 12, 14, 12); rl.addWidget(win.label(S["cu_plan"], 11, True))
    win.cu_plan = QListWidget(); win.cu_plan.setMinimumHeight(260); win.cu_plan.setWordWrap(True); rl.addWidget(win.cu_plan, 1)
    win.cu_decide = win.label("", 9, muted=True); win.cu_decide.setWordWrap(True); rl.addWidget(win.cu_decide); body.addWidget(right, 2)
    lay.addLayout(body, 1)
    bottom = win.card(); bl = QVBoxLayout(bottom); bl.setContentsMargins(14, 12, 14, 12); bl.addWidget(win.label(S["cu_missed_routines"], 11, True))
    win.cu_routines = QListWidget(); win.cu_routines.setMaximumHeight(130); bl.addWidget(win.cu_routines)
    rr = QHBoxLayout(); t = GlassButton(S["cu_tick_late"], win.theme, icon="check"); t.clicked.connect(lambda: _routine(win, True)); s = GlassButton(S["cu_skip"], win.theme, icon="close"); s.clicked.connect(lambda: _routine(win, False))
    rr.addWidget(t); rr.addWidget(s); rr.addStretch(); bl.addLayout(rr)
    win.cu_stats = win.label("", 9, muted=True); win.cu_stats.setWordWrap(True); bl.addWidget(win.cu_stats); lay.addWidget(bottom)
    win.pages.addWidget(page)


def _selected(win) -> Optional[str]:
    it = win.cu_list.currentItem()
    return it.data(Qt.UserRole) if it is not None else None


def _act(win, fn) -> None:
    i = _selected(win)
    if not i:
        win.toast(S["cu_pick"]); return
    try:
        fn(i)
    except (KeyError, ValueError) as exc:
        win.toast(str(exc)); return
    if win.theme.fx is not None:
        win.theme.fx.play("success", 0.8)
    win.refresh_all()


def _push(win, entry_id: str, to: str) -> None:
    r = cu.postpone(win.db, entry_id, to)
    if r["chronic"]:
        win.toast("⚠ " + r["advice"])


def _start(win, entry_id: str) -> None:
    e = win.db.get(TimeEntry, entry_id)
    if e is not None:
        win.quick_start(e.title, e.project_id, e.category)


def _split(win, entry_id: str) -> None:
    from .lists_ui import SplitTaskDialog
    e = win.db.get(TimeEntry, entry_id)
    if e is not None:
        SplitTaskDialog(win, e).exec_()


def apply_plan(win) -> None:
    pl = cu.plan(win.db, capacity_min=win.cu_cap.value(), days=win.cu_days.value())
    n = cu.apply_plan(win.db, pl)
    win.toast(to_fa_digits(f"{n} {S['cu_applied']}")); win.refresh_all()


def _routine(win, tick: bool) -> None:
    it = win.cu_routines.currentItem()
    if it is None:
        win.toast(S["cu_pick"]); return
    rid, key = it.data(Qt.UserRole)
    (rt.check if tick else rt.skip)(win.db, rid, key)
    win.refresh_all()


def refresh_catchup(win) -> None:
    pl = cu.plan(win.db, capacity_min=win.cu_cap.value(), days=win.cu_days.value())
    sc, s = pl["scan"], pl["summary"]
    keep = _selected(win)
    win.cu_list.clear()
    for it in sc["items"]:
        li = QListWidgetItem(_line(it)); li.setData(Qt.UserRole, it["id"]); win.cu_list.addItem(li)
        if it["id"] == keep:
            win.cu_list.setCurrentItem(li)
    c = sc["counts"]
    win.cu_summary.setText(to_fa_digits(S["cu_summary"].format(o=c["overdue"], m=c["missed_blocks"], p=c["postponed"], c=c["chronic"], r=c["missed_routines"], d=s["days_needed"] or 0)) if c["total"] else S["cu_clear"])
    win.cu_plan.clear()
    for d in pl["days"]:
        h = QListWidgetItem(to_fa_digits(f"{format_jalali(d['date'])}   {d['minutes']}/{d['capacity']} {S['min']}")); h.setFlags(Qt.NoItemFlags); win.cu_plan.addItem(h)
        for it in d["items"]:
            win.cu_plan.addItem(to_fa_digits(f"   {to_tehran(it['slot_start']).strftime('%H:%M')}  {it['title']}  ({it['est_min']}{S['min'][0]})"))
    extra = []
    if pl["later"]:
        extra.append(to_fa_digits(f"{len(pl['later'])} {S['cu_later']}"))
    if pl["split"]:
        extra.append(S["cu_split_hint"] + ": " + "، ".join(i["title"] for i in pl["split"][:3]))
    if pl["decide"]:
        extra.append(S["cu_drop_hint"] + ": " + "، ".join(i["title"] for i in pl["decide"][:3]))
    win.cu_decide.setText("\n".join(extra))
    win.cu_routines.clear()
    for m in sc["missed_routines"]:
        li = QListWidgetItem(to_fa_digits(f"{m['routine']['title']}  ·  {format_jalali(m['due'].date())}")); li.setData(Qt.UserRole, (m["routine"]["id"], m["key"])); win.cu_routines.addItem(li)
    st = cu.stats(win.db)
    win.cu_stats.setText(to_fa_digits(S["cu_stats"].format(p=st["pushes"], f=(st["finished_pct"] if st["finished_pct"] is not None else "—"), a=st["avg_days_overdue"])) + (("\n" + S["cu_chronic"] + ": " + "، ".join(st["chronic"][:4])) if st["chronic"] else ""))
