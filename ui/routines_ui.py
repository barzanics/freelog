"""Routines page: scheduled check boxes (hourly / every N minutes / daily / weekly / monthly) with streaks and notifications. Rules: services/routines.py."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QScrollArea, QSpinBox, QTimeEdit, QVBoxLayout, QWidget

from ..core import persian as _p
from ..core.persian import now_utc, to_fa_digits, to_tehran, tr
from ..services import routines as rt
from .dialogs import PopDialog, confirm
from .forms import ColorSwatches, FlowLayout, Section, Segmented, chip_button
from .glass import GlassButton, LiquidCheck, LiquidSwitch, Ring
from .strings import S

log = logging.getLogger("worktracker.routines_ui")
SECTIONS = (("hourly", ("hourly", "interval")), ("daily", ("daily",)), ("weekly", ("weekly",)), ("monthly", ("monthly",)))


class RoutineDialog(PopDialog):
    def __init__(self, win, routine: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(win, S["rt_edit"] if routine else S["rt_new"], "bell", 640)
        self.routine, self.saved = routine, None
        self.title_in = QLineEdit(placeholderText=S["rt_title_hint"]); self.note = QPlainTextEdit(); self.note.setFixedHeight(58)
        self.kind = Segmented([(S["rt_kind_" + k], k) for k in rt.KINDS], wrap=True); self.kind.changed.connect(self._kind_changed)
        self.time = QTimeEdit(); self.time.setDisplayFormat("HH:mm")
        order = [0, 1, 2, 3, 4, 5, 6] if _p.is_gregorian() else [5, 6, 0, 1, 2, 3, 4]
        names = _p.weekday_names(short=False, first="mon")
        self.wd_host = QWidget(); fl = FlowLayout(self.wd_host); self.wd_chips = {}
        for idx in order:
            b = chip_button(names[idx], True); fl.addWidget(b); self.wd_chips[idx] = b
        self.day = QSpinBox(); self.day.setRange(1, 31); self.day.setValue(1)
        self.every_h = QSpinBox(); self.every_h.setRange(1, 12); self.every_h.setValue(1); self.every_h.setSuffix(" h")
        self.every_m = QSpinBox(); self.every_m.setRange(5, 720); self.every_m.setValue(30); self.every_m.setSingleStep(5); self.every_m.setSuffix(" " + S["min"])
        self.from_h = QSpinBox(); self.from_h.setRange(0, 22); self.from_h.setValue(9); self.from_h.setSuffix(":00")
        self.to_h = QSpinBox(); self.to_h.setRange(1, 23); self.to_h.setValue(18); self.to_h.setSuffix(":00")
        self.notify = LiquidSwitch(win.theme, True); self.active = LiquidSwitch(win.theme, True)
        self.repeat = QSpinBox(); self.repeat.setRange(0, 1440); self.repeat.setSuffix(" " + S["min"]); self.repeat.setSpecialValueText(S["rt_once"])
        self.color = ColorSwatches()
        from .pages_ops import _row
        a = Section(S["sec_basic"]); a.add(S["title"], self.title_in); a.add(S["notes"], self.note)
        b = Section(S["rt_when"]); b.add(S["rt_kind"], self.kind)
        self.f_time = b.add(S["rt_time"], self.time); self.f_wd = b.add(S["rt_weekdays"], self.wd_host); self.f_day = b.add(S["rt_day"], self.day)
        self.f_eh = b.add(S["rt_every_hours"], self.every_h); self.f_em = b.add(S["rt_every_min"], self.every_m)
        self.f_win = QWidget(); wl = QHBoxLayout(self.f_win); wl.setContentsMargins(0, 0, 0, 0); wl.addWidget(self.from_h); wl.addWidget(QLabel("→")); wl.addWidget(self.to_h); b.add(S["rt_window"], self.f_win)
        c = Section(S["rt_alerts"]); c.add("", _row(S["rt_notify"], self.notify)); c.add(S["rt_repeat"], self.repeat); c.add("", _row(S["rt_active"], self.active)); c.add(S["color"], self.color)
        self.body.addWidget(self.scroll_page(a, b, c), 1)
        self._cells = {"time": self.time, "wd": self.wd_host, "day": self.day, "eh": self.every_h, "em": self.every_m, "win": self.f_win}
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["save"], self.theme, primary=True, icon="check"); ok.clicked.connect(self._save)
        if routine:
            d = GlassButton(S["delete"], self.theme, danger=True, icon="trash"); d.clicked.connect(self._delete); self.footer.addWidget(d)
        self.buttons(cancel, ok)
        self._load(routine)

    def _kind_changed(self, kind) -> None:
        show = {"hourly": ("eh", "win"), "interval": ("em", "win"), "daily": ("time",), "weekly": ("time", "wd"), "monthly": ("time", "day")}.get(kind, ())
        for name, w in self._cells.items():
            parent = w.parentWidget()
            (parent if parent is not None and parent is not self else w).setVisible(name in show)

    def _load(self, r: Optional[Dict[str, Any]]) -> None:
        r = r or {"kind": "daily", "time": "09:00", "weekdays": [5], "notify": True, "active": True}
        self.title_in.setText(r.get("title", "")); self.note.setPlainText(r.get("note", "")); self.kind.setValue(r["kind"], emit=False)
        from PyQt5.QtCore import QTime
        h, m = (int(x) for x in r.get("time", "09:00").split(":")); self.time.setTime(QTime(h, m))
        for idx, b in self.wd_chips.items():
            b.setChecked(idx in r.get("weekdays", []))
        self.day.setValue(int(r.get("day", 1))); self.every_h.setValue(int(r.get("every_hours", 1))); self.every_m.setValue(int(r.get("every_min", 30)))
        self.from_h.setValue(int(r.get("from_hour", 9))); self.to_h.setValue(int(r.get("to_hour", 18)))
        self.notify.setChecked(bool(r.get("notify", True))); self.active.setChecked(bool(r.get("active", True))); self.repeat.setValue(int(r.get("repeat_min", 0))); self.color.setColor(r.get("color", ""))
        self._kind_changed(r["kind"])

    def fields(self) -> Dict[str, Any]:
        t = self.time.time()
        return {"title": self.title_in.text(), "note": self.note.toPlainText(), "kind": self.kind.value(), "time": f"{t.hour():02d}:{t.minute():02d}",
                "weekdays": [i for i, b in self.wd_chips.items() if b.isChecked()], "day": self.day.value(), "every_hours": self.every_h.value(), "every_min": self.every_m.value(),
                "from_hour": self.from_h.value(), "to_hour": self.to_h.value(), "notify": self.notify.isChecked(), "active": self.active.isChecked(), "repeat_min": self.repeat.value(),
                "color": self.color.color()}

    def _save(self) -> None:
        try:
            self.saved = rt.update(self.db, self.routine["id"], **self.fields()) if self.routine else rt.add(self.db, **self.fields())
        except rt.RoutineError as exc:
            self.show_error(str(exc)); return
        self.accept()

    def _delete(self) -> None:
        if self.routine and confirm(self, S["confirm_delete"]):
            rt.delete(self.db, self.routine["id"]); self.deleted = True; self.accept()


# ======================================================================== page
def build_routines(win) -> None:
    page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12)
    head = QHBoxLayout(); head.addWidget(win.label(S["routines"], 17, True), 1)
    win.rt_ring = Ring(win.theme); win.rt_ring.setFixedSize(58, 58); head.addWidget(win.rt_ring)
    win.rt_progress = win.label("", 10, muted=True); head.addWidget(win.rt_progress)
    add = GlassButton(S["rt_new"], win.theme, primary=True, icon="plus"); add.clicked.connect(lambda: open_routine(win)); head.addWidget(add)
    lay.addLayout(head)
    lay.addWidget(win.label(S["rt_explain"], 9, muted=True))
    host = QWidget(); hl = QVBoxLayout(host); hl.setSpacing(12); hl.setContentsMargins(0, 0, 0, 0)
    win.rt_boxes = {}
    for key, _kinds in SECTIONS:
        card = win.card(); cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12); cl.setSpacing(6); cl.addWidget(win.label(S["rt_sec_" + key], 11, True))
        body = QVBoxLayout(); body.setSpacing(4); cl.addLayout(body); win.rt_boxes[key] = (card, body); hl.addWidget(card)
    hl.addStretch()
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(host); sa.setFrameShape(QFrame.NoFrame); lay.addWidget(sa, 1)
    win.pages.addWidget(page)


def open_routine(win, routine: Optional[Dict[str, Any]] = None) -> None:
    dlg = RoutineDialog(win, routine)
    if dlg.exec_():
        win.refresh_all()


def _clear(layout) -> None:
    while layout.count():
        it = layout.takeAt(0)
        if it is not None and it.widget() is not None:
            it.widget().deleteLater()
        elif it is not None and it.layout() is not None:
            _clear(it.layout())


def _on_toggle(win, rid: str, key: str, on: bool) -> None:
    (rt.check if on else rt.uncheck)(win.db, rid, key, now_utc()) if on else rt.uncheck(win.db, rid, key)
    if on and win.theme.fx is not None:
        win.theme.fx.play("success", 0.8)
    refresh_routines(win)


def refresh_routines(win) -> None:
    now = now_utc()
    items = rt.today_items(win.db, now)
    seen = {(i["routine"]["id"], i["key"]) for i in items}
    items += [i for i in rt.this_month_items(win.db, now) if (i["routine"]["id"], i["key"]) not in seen]
    done = sum(1 for i in items if i["checked"])
    win.rt_ring.set_value(done / len(items) if items else 0.0, to_fa_digits(f"{done}/{len(items)}"))
    win.rt_progress.setText(to_fa_digits(f"{S['rt_today']}: {done}/{len(items)}"))
    inactive = [r for r in rt.all_routines(win.db) if not r["active"]]
    for key, kinds in SECTIONS:
        card, body = win.rt_boxes[key]
        _clear(body)
        rows = [i for i in items if i["routine"]["kind"] in kinds]
        for it in rows:
            r = it["routine"]
            line = QFrame(); line.setProperty("card", True); h = QHBoxLayout(line); h.setContentsMargins(10, 4, 8, 4); h.setSpacing(8)
            time_txt = to_tehran(it["due"]).strftime("%H:%M") if r["kind"] != "monthly" else _p.format_jalali(it["due"].date(), "{m:02d}/{d:02d}", fa_digits=False) + " " + it["due"].strftime("%H:%M")
            chk = LiquidCheck(f"{r['title']}", win.theme, it["checked"]); chk.toggled.connect(lambda on, rid=r["id"], k=it["key"]: _on_toggle(win, rid, k, on))
            h.addWidget(chk, 1)
            when = QLabel(to_fa_digits(time_txt)); when.setProperty("muted", not it["overdue"]); when.setProperty("danger", bool(it["overdue"] and not it["checked"])); h.addWidget(when)
            n = rt.streak(win.db, r["id"], now)
            if n >= 2:
                st = QLabel(to_fa_digits(f"🔥 {n}")); st.setToolTip(S["rt_streak"]); h.addWidget(st)
            ed = GlassButton("", win.theme, icon="edit"); ed.setFixedSize(34, 34); ed.clicked.connect(lambda _c=False, rr=r: open_routine(win, rr)); h.addWidget(ed)
            body.addWidget(line)
        if not rows:
            body.addWidget(win.label(S["rt_none"], 9, muted=True))
        if key == "hourly" and inactive:
            body.addWidget(win.label(to_fa_digits(f"{len(inactive)} {S['rt_paused']}"), 9, muted=True))
