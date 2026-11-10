"""Rich form widgets: chips, priority, segmented choice, Jalali date picker, date+time, duration, checklist, colours, icons.

Everything here is a plain widget with ``value()/setValue()``-style accessors so dialogs stay small and the pure rules live in
``services.taskform``.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractItemView, QColorDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QListWidget, QListWidgetItem,
                             QPushButton, QSizePolicy, QSpinBox, QTimeEdit, QVBoxLayout, QWidget)

from ..core import taxonomy
from ..core import persian as _persian
from ..core.persian import MONTHS_FA, TEHRAN, UTC, format_jalali, jalali_to_date, parse_jalali, to_en_digits, to_fa_digits, to_tehran, date_to_jalali, tr
from ..services import views
from . import icons

# soft, harmonious swatches (Tokyo-Night / Catppuccin family) - saturated primaries look cheap next to glass
PALETTE = ("#7AA2F7", "#7DCFFF", "#BB9AF7", "#9ECE6A", "#E0AF68", "#F7768E", "#73DACA", "#FF9E64", "#89B4FA", "#F5C2E7", "#A6ADC8", "#94E2D5")
EMOJI = tuple("📁💼🧩🚀🎯📊🛠️💡🔬🎨📝📚🏠🛒✈️🏋️🧘💧☕🌱🔥⭐❤️🎵📷💻🧠📞📅🔔⚡🏆🔑🧾🤝🎓🌍")


def parse_date_text(text: str) -> Optional[dt.date]:
    """Jalali ``1405/02/12`` (year < 1700) or Gregorian ``2026-05-02``; Persian or Latin digits. Empty -> None, junk -> ValueError."""
    t = to_en_digits(text).strip().replace("-", "/").replace(".", "/")
    if not t:
        return None
    parts = t.split("/")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(tr("تاریخ نامعتبر است", "Invalid date"))
    y, m, d = (int(x) for x in parts)
    return parse_jalali(t) if y < 1700 else dt.date(y, m, d)


class FlowLayout(QLayout):
    """Wraps children onto new lines (used for chips)."""

    def __init__(self, parent: Optional[QWidget] = None, spacing: int = 6) -> None:
        super().__init__(parent)
        self._items: list = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:  # noqa: N802
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, i: int):  # noqa: N802
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i: int):  # noqa: N802
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientations(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, w: int) -> int:  # noqa: N802
        return self._do(QRect(0, 0, w, 0), True)

    def setGeometry(self, rect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._do(rect, False)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return s + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do(self, rect, test: bool) -> int:
        x, y, line_h, sp = rect.x(), rect.y(), 0, self.spacing()
        rtl = self.parentWidget() is not None and self.parentWidget().layoutDirection() == Qt.RightToLeft
        for it in self._items:
            w, h = it.sizeHint().width(), it.sizeHint().height()
            if x + w > rect.right() + 1 and line_h > 0:
                x, y, line_h = rect.x(), y + line_h + sp, 0
            if not test:
                px = rect.right() - (x - rect.x()) - w + 1 if rtl else x
                it.setGeometry(QRect(QPoint(px, y), it.sizeHint()))
            x += w + sp
            line_h = max(line_h, h)
        return y + line_h - rect.y()


def chip_button(text: str, checkable: bool = False, parent: Optional[QWidget] = None) -> QPushButton:
    b = QPushButton(text, parent)
    b.setProperty("chip", True)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


class ChipInput(QWidget):
    """Tags: type and press Enter/comma to add, click a chip to remove it; optional suggestions shown as one-click chips."""
    changed = pyqtSignal()

    def __init__(self, placeholder: str = "", suggestions: Sequence[str] = (), parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tags: List[str] = []
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.edit = QLineEdit(placeholderText=placeholder or tr("برچسب… (Enter)", "Tag… (Enter)"))
        self.edit.returnPressed.connect(self._commit)
        self.edit.textEdited.connect(lambda t: self._commit() if t.endswith((",", "،")) else None)
        lay.addWidget(self.edit)
        self.chips_host = QWidget(); self.flow = FlowLayout(self.chips_host); lay.addWidget(self.chips_host)
        self.sug_host = QWidget(); self.sug_flow = FlowLayout(self.sug_host); lay.addWidget(self.sug_host)
        self.set_suggestions(suggestions)

    def set_suggestions(self, items: Sequence[str]) -> None:
        self._suggestions = list(items)[:14]
        self._rebuild()

    def tags(self) -> List[str]:
        return list(self._tags)

    def setTags(self, tags: Sequence[str]) -> None:  # noqa: N802
        self._tags = []
        for t in tags:
            self._add(t, emit=False)
        self._rebuild(); self.changed.emit()

    def _add(self, text: str, emit: bool = True) -> None:
        t = text.strip().strip(",،").strip()
        if t and t not in self._tags and len(t) <= 40:
            self._tags.append(t)
            if emit:
                self._rebuild(); self.changed.emit()

    def _commit(self) -> None:
        for part in self.edit.text().replace("،", ",").split(","):
            self._add(part)
        self.edit.clear()

    def _remove(self, t: str) -> None:
        if t in self._tags:
            self._tags.remove(t); self._rebuild(); self.changed.emit()

    def _rebuild(self) -> None:
        for lay, host in ((self.flow, self.chips_host), (self.sug_flow, self.sug_host)):
            while lay.count():
                it = lay.takeAt(0)
                if it is not None and it.widget() is not None:
                    it.widget().deleteLater()
        for t in self._tags:
            b = chip_button(f"{t}  ✕"); b.setChecked(True); b.setCheckable(True); b.clicked.connect(lambda _c=False, x=t: self._remove(x)); self.flow.addWidget(b)
        for s in self._suggestions:
            if s not in self._tags:
                b = chip_button(f"+ {s}"); b.setProperty("ghost", True); b.setProperty("chip", False); b.clicked.connect(lambda _c=False, x=s: self._add(x)); self.sug_flow.addWidget(b)


class Segmented(QWidget):
    """Single-choice pills. ``options`` = [(label, data)]."""
    changed = pyqtSignal(object)

    def __init__(self, options: Sequence[Tuple[str, Any]], parent: Optional[QWidget] = None, wrap: bool = True) -> None:
        super().__init__(parent)
        self._buttons: List[Tuple[QPushButton, Any]] = []
        self._value: Any = options[0][1] if options else None
        lay = FlowLayout(self) if wrap else QHBoxLayout(self)
        if not wrap:
            lay.setContentsMargins(0, 0, 0, 0)
        for label, data in options:
            b = chip_button(label, True); b.clicked.connect(lambda _c=False, d=data: self.setValue(d)); lay.addWidget(b); self._buttons.append((b, data))
        self.setValue(self._value, emit=False)

    def value(self) -> Any:
        return self._value

    def setValue(self, data: Any, emit: bool = True) -> None:  # noqa: N802
        self._value = data
        for b, d in self._buttons:
            b.setChecked(d == data)
        if emit:
            self.changed.emit(data)


class PriorityPicker(Segmented):
    """The five priorities as colour-coded chips (text + palette colour, no emoji)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__([(p["name"], k) for k, p in taxonomy.PRIORITIES.items()], parent)
        for btn, k in self._buttons:
            col = taxonomy.PRIORITIES[k]["color"]
            btn.setStyleSheet(f"QPushButton{{border:1px solid {col};border-left:5px solid {col};}} QPushButton:checked{{background:{col};color:#10101c;font-weight:bold;}}")
        self.setValue(3, emit=False)


class CalendarPopup(QFrame):
    """Month grid in a popup - Jalali (Saturday first) in Persian mode, Gregorian (Monday first) in English mode. Emits ``picked(date)``."""
    picked = pyqtSignal(object)

    def __init__(self, start: Optional[dt.date] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setObjectName("calpop")
        self.setStyleSheet("#calpop{background:#15152b;border:1px solid rgba(255,255,255,60);border-radius:16px;} QPushButton{color:#fff;} QLabel{color:#fff;background:transparent;}")
        today = to_tehran(dt.datetime.now(UTC)).date()
        self.sel, self.today = start, today
        self.y, self.m = views.today_ym(start or today)
        self.box = QVBoxLayout(self); self.box.setContentsMargins(12, 12, 12, 12)
        self._draw()

    def _draw(self) -> None:
        while self.box.count():
            it = self.box.takeAt(0)
            if it is not None and it.widget() is not None:
                it.widget().deleteLater()
            elif it is not None and it.layout() is not None:
                self._wipe(it.layout())
        lay = views.month_layout(self.y, self.m)
        rtl = self.layoutDirection() == Qt.RightToLeft
        head = QHBoxLayout()
        nxt = chip_button("‹" if rtl else "›"); prv = chip_button("›" if rtl else "‹"); nxt.clicked.connect(lambda: self._shift(1)); prv.clicked.connect(lambda: self._shift(-1))
        title = QLabel(to_fa_digits(str(lay["title"]))); title.setAlignment(Qt.AlignCenter); title.setStyleSheet("color:#fff;font-weight:700;background:transparent;")
        head.addWidget(prv); head.addWidget(title, 1); head.addWidget(nxt); self.box.addLayout(head)
        grid = QGridLayout(); grid.setSpacing(4)
        for c, w in enumerate(_persian.weekday_names(short=True)):
            l = QLabel(w); l.setAlignment(Qt.AlignCenter); l.setStyleSheet("color:#9a9ac0;background:transparent;"); grid.addWidget(l, 0, c)
        for r, week in enumerate(lay["weeks"], 1):
            for c, date in enumerate(week):
                if date is None:
                    continue
                label = to_fa_digits(str(date.day) if _persian.is_gregorian() else str(date_to_jalali(date)[2]))
                b = chip_button(label, True); b.setFixedSize(34, 30); b.setChecked(date == self.sel)
                if date == self.today and date != self.sel:
                    b.setStyleSheet("border:1px solid #7DCFFF;")
                b.clicked.connect(lambda _c=False, x=date: self._pick(x)); grid.addWidget(b, r, c)
        self.box.addLayout(grid)
        foot = QHBoxLayout(); t = chip_button(tr("امروز", "Today")); t.clicked.connect(lambda: self._pick(self.today)); cl = chip_button(tr("پاک", "Clear")); cl.clicked.connect(lambda: self._pick(None))
        foot.addWidget(t); foot.addStretch(); foot.addWidget(cl); self.box.addLayout(foot)

    def _wipe(self, lay) -> None:
        while lay.count():
            it = lay.takeAt(0)
            if it is not None and it.widget() is not None:
                it.widget().deleteLater()

    def _shift(self, d: int) -> None:
        self.y, self.m = views.shift_month(self.y, self.m, d); self._draw()

    def _pick(self, d: Optional[dt.date]) -> None:
        self.picked.emit(d); self.close()


class JalaliDateEdit(QWidget):
    """Text field (accepts Jalali or Gregorian, Persian or Latin digits) + a calendar button."""
    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None, placeholder: str = "") -> None:
        super().__init__(parent)
        placeholder = placeholder or tr("۱۴۰۵/۰۲/۱۲", "2026-05-12")
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.edit = QLineEdit(placeholderText=placeholder); self.edit.setMaximumWidth(150)
        self.btn = QPushButton(); self.btn.setProperty("ghost", True); self.btn.setIcon(icons.icon("calendar", "#A9A9C4", 20)); self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self._popup); self.edit.editingFinished.connect(self._normalise)
        lay.addWidget(self.edit); lay.addWidget(self.btn)

    def date(self) -> Optional[dt.date]:
        return parse_date_text(self.edit.text())

    def isValid(self) -> bool:  # noqa: N802
        try:
            self.date(); return True
        except ValueError:
            return False

    def setDate(self, d: Optional[dt.date]) -> None:  # noqa: N802
        self.edit.setText(format_jalali(d) if d else ""); self.changed.emit()

    def _normalise(self) -> None:
        try:
            d = self.date()
            self.edit.setStyleSheet("")
            if d:
                self.edit.setText(format_jalali(d))
        except ValueError:
            self.edit.setStyleSheet("border:1px solid #FF4757;")
        self.changed.emit()

    def _popup(self) -> None:
        try:
            cur = self.date()
        except ValueError:
            cur = None
        pop = CalendarPopup(cur, self)
        pop.picked.connect(self.setDate)
        pop.move(self.mapToGlobal(QPoint(0, self.height() + 4)))
        pop.show()
        self._pop = pop


class DateTimeField(QWidget):
    """Jalali date + HH:MM -> timezone-aware datetime (Tehran). ``value()`` is None when the date is empty."""
    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None, with_time: bool = True) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.date_edit = JalaliDateEdit(); self.time_edit = QTimeEdit(); self.time_edit.setDisplayFormat("HH:mm"); self.time_edit.setMaximumWidth(86)
        self.with_time = with_time
        lay.addWidget(self.date_edit); lay.addWidget(self.time_edit); lay.addStretch()
        self.time_edit.setVisible(with_time)
        self.date_edit.changed.connect(self.changed); self.time_edit.timeChanged.connect(lambda _t: self.changed.emit())

    def value(self) -> Optional[dt.datetime]:
        d = self.date_edit.date()
        if d is None:
            return None
        t = self.time_edit.time()
        return dt.datetime.combine(d, dt.time(t.hour(), t.minute()) if self.with_time else dt.time(), tzinfo=TEHRAN).astimezone(UTC)

    def setValue(self, v: Optional[dt.datetime]) -> None:  # noqa: N802
        if v is None:
            self.date_edit.setDate(None); return
        loc = to_tehran(v)
        self.date_edit.setDate(loc.date())
        from PyQt5.QtCore import QTime
        self.time_edit.setTime(QTime(loc.hour, loc.minute))

    def isValid(self) -> bool:  # noqa: N802
        return self.date_edit.isValid()


class DurationEdit(QWidget):
    """Hours + minutes with one-click presets. ``minutes()`` / ``setMinutes()``."""
    changed = pyqtSignal(int)

    def __init__(self, presets: Sequence[int] = (15, 30, 60, 90, 120), parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        row = QHBoxLayout(); row.setSpacing(6)
        self.h = QSpinBox(); self.h.setRange(0, 999); self.h.setSuffix(" " + tr("ساعت", "h"))
        self.m = QSpinBox(); self.m.setRange(0, 59); self.m.setSingleStep(5); self.m.setSuffix(" " + tr("دقیقه", "min"))
        row.addWidget(self.h); row.addWidget(self.m); row.addStretch(); lay.addLayout(row)
        host = QWidget(); fl = FlowLayout(host)
        for mins in presets:
            b = chip_button(self.fmt(mins)); b.clicked.connect(lambda _c=False, x=mins: self.setMinutes(x)); fl.addWidget(b)
        lay.addWidget(host)
        self.h.valueChanged.connect(lambda _v: self.changed.emit(self.minutes())); self.m.valueChanged.connect(lambda _v: self.changed.emit(self.minutes()))

    @staticmethod
    def fmt(mins: int) -> str:
        h, m = divmod(mins, 60)
        return to_fa_digits((f"{h}{tr('س', 'h')} " if h else "") + (f"{m}{tr('د', 'm')}" if m or not h else "")).strip()

    def minutes(self) -> int:
        return self.h.value() * 60 + self.m.value()

    def setMinutes(self, mins: int) -> None:  # noqa: N802
        mins = max(0, int(mins))
        for w in (self.h, self.m):
            w.blockSignals(True)
        self.h.setValue(mins // 60); self.m.setValue(mins % 60)
        for w in (self.h, self.m):
            w.blockSignals(False)
        self.changed.emit(mins)


class ChecklistEditor(QWidget):
    """Editable, re-orderable, checkable list (double-click to rename, drag to reorder)."""
    changed = pyqtSignal()

    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.list = QListWidget(); self.list.setDragDropMode(QAbstractItemView.InternalMove); self.list.setMinimumHeight(120); self.list.setCursor(Qt.PointingHandCursor)
        self.list.itemChanged.connect(lambda _i: self.changed.emit())
        row = QHBoxLayout(); self.edit = QLineEdit(placeholderText=placeholder or tr("آیتم تازه… (Enter)", "New item… (Enter)")); self.edit.returnPressed.connect(self._add)
        add = chip_button(tr("افزودن", "Add")); add.clicked.connect(self._add); rm = chip_button(tr("حذف انتخاب‌شده", "Remove selected")); rm.clicked.connect(self._remove)
        row.addWidget(self.edit, 1); row.addWidget(add); row.addWidget(rm)
        lay.addWidget(self.list); lay.addLayout(row)

    def _add(self) -> None:
        raw = self.edit.text()
        parts = [x.strip().lstrip("-*•").strip() for x in raw.replace(";", "\n").splitlines()] if raw.strip() else []
        added = False
        for t in parts:
            if t.startswith("[") and "]" in t[:4]:
                t = t.split("]", 1)[1].strip()
            if t:
                self._append(t, False); added = True
        if added:
            self.edit.clear(); self.changed.emit()

    def _append(self, text: str, done: bool) -> None:
        it = QListWidgetItem(text)
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        it.setCheckState(Qt.Checked if done else Qt.Unchecked)
        self.list.addItem(it)

    def _remove(self) -> None:
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self.changed.emit()

    def items(self) -> List[Dict[str, Any]]:
        return [{"text": self.list.item(i).text().strip(), "done": self.list.item(i).checkState() == Qt.Checked} for i in range(self.list.count())]

    def setItems(self, items: Sequence[Dict[str, Any]]) -> None:  # noqa: N802
        self.list.clear()
        for c in items:
            self._append(str(c.get("text", "")), bool(c.get("done")))


class ColorSwatches(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, colors: Sequence[str] = PALETTE, allow_none: bool = True, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._c = ""
        self._btns: List[Tuple[QPushButton, str]] = []
        lay = FlowLayout(self)
        opts = ([""] if allow_none else []) + list(colors)
        for col in opts:
            b = QPushButton("∅" if col == "" else ""); b.setFixedSize(26, 26); b.setCursor(Qt.PointingHandCursor); b.setCheckable(True)
            b.clicked.connect(lambda _c=False, x=col: self.setColor(x)); lay.addWidget(b); self._btns.append((b, col))
        more = QPushButton("＋"); more.setFixedSize(26, 26); more.setCursor(Qt.PointingHandCursor); more.clicked.connect(self._custom); lay.addWidget(more)
        self._paint()

    def _paint(self) -> None:
        for b, col in self._btns:
            ring = "2px solid #FFFFFF" if col == self._c else "1px solid rgba(255,255,255,70)"
            b.setStyleSheet(f"QPushButton{{background:{col or 'transparent'};border:{ring};border-radius:13px;color:#aaa;}}")
            b.setChecked(col == self._c)

    def color(self) -> str:
        return self._c

    def setColor(self, c: str) -> None:  # noqa: N802
        self._c = c or ""; self._paint(); self.changed.emit(self._c)

    def _custom(self) -> None:
        col = QColorDialog.getColor(QColor(self._c or "#6D5DFC"), self)
        if col.isValid():
            self.setColor(col.name())


class IconPicker(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, icons_: Sequence[str] = EMOJI, columns: int = 10, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._v = ""
        self._btns: List[Tuple[QPushButton, str]] = []
        g = QGridLayout(self); g.setSpacing(4); g.setContentsMargins(0, 0, 0, 0)
        for i, e in enumerate(icons_):
            b = QPushButton(e); b.setFixedSize(42, 40); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor); b.setProperty("chip", True)
            b.setStyleSheet("QPushButton{font-size:17pt;padding:0px;border-radius:12px;}")
            b.clicked.connect(lambda _c=False, x=e: self.setIcon(x)); g.addWidget(b, i // columns, i % columns); self._btns.append((b, e))

    def icon(self) -> str:
        return self._v

    def setIcon(self, v: str) -> None:  # noqa: N802
        self._v = v
        for b, e in self._btns:
            b.setChecked(e == v)
        self.changed.emit(v)


class Section(QFrame):
    """Titled block inside a dialog/page. Styled by the global stylesheet (QFrame[card="true"]) so it follows the active theme."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.box = QVBoxLayout(self); self.box.setContentsMargins(16, 12, 16, 14); self.box.setSpacing(10)
        if title:
            t = QLabel(title); t.setProperty("accent", True); t.setWordWrap(True); self.box.addWidget(t)
        self.grid = QGridLayout(); self.grid.setHorizontalSpacing(14); self.grid.setVerticalSpacing(8)
        self.grid.setColumnStretch(0, 1); self.grid.setColumnStretch(1, 1); self.box.addLayout(self.grid)
        self._row = 0

    def add(self, label: str, widget: QWidget, span: int = 2, col: int = 0) -> QWidget:
        """Label above the field; ``span`` 1 = half width (two fields per row), 2 = full width."""
        cell = QWidget(); v = QVBoxLayout(cell); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
        if label:
            l = QLabel(label); l.setProperty("muted", True); l.setWordWrap(True); v.addWidget(l)
        v.addWidget(widget)
        cell.setMinimumWidth(0)
        if span == 2:
            self.grid.addWidget(cell, self._row, 0, 1, 2); self._row += 1
        else:
            self.grid.addWidget(cell, self._row, col)
            if col == 1:
                self._row += 1
        return widget

    def pair(self, l1: str, w1: QWidget, l2: str, w2: QWidget) -> None:
        self.add(l1, w1, 1, 0); self.add(l2, w2, 1, 1)
