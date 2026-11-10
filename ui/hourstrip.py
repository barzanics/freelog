"""A 24-bar strip for today: per clock hour the measured engaged time (outer bar) and what is already logged (inner bar). An hour with unlogged work is marked;
click it and the app asks about exactly that hour."""
from __future__ import annotations

import datetime as dt
from typing import Callable, List, Optional

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QWidget

from ..core.persian import now_utc, to_fa_digits, to_tehran, tr
from ..services.ledger import hour_floor
from .glass import Theme, qcolor


class HourStrip(QWidget):
    def __init__(self, theme: Theme, on_click: Callable[[dt.datetime], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme, self.on_click = theme, on_click
        self.rows: List[dict] = []
        self.setMinimumHeight(96)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def set_rows(self, rows: List[dict]) -> None:
        self.rows = rows
        self.update()

    def _cell(self, i: int) -> QRectF:
        w = (self.width() - 8) / 24.0
        slot = 23 - i if self.layoutDirection() == Qt.RightToLeft else i
        return QRectF(4 + slot * w, 6, w, self.height() - 30)

    def _index_at(self, x: float) -> int:
        w = (self.width() - 8) / 24.0
        slot = int((x - 4) // w) if w > 0 else -1
        return (23 - slot if self.layoutDirection() == Qt.RightToLeft else slot)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        i = self._index_at(e.x())
        if 0 <= i < len(self.rows):
            r = self.rows[i]
            self.setToolTip(to_fa_digits(f"{i:02d}:00  ·  {tr('فعال', 'active')} {r['engaged_sec'] // 60}'  ·  {tr('ثبت‌شده', 'logged')} {r['logged_sec'] // 60}'  ·  {tr('ثبت‌نشده', 'unlogged')} {r['unlogged_sec'] // 60}'"))
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        i = self._index_at(e.x())
        if 0 <= i < len(self.rows) and self.rows[i]["unlogged_sec"] >= 60:
            self.on_click(self.rows[i]["hour_start"])
        super().mousePressEvent(e)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        now_h = to_tehran(now_utc()).hour
        a0, a1, a2 = self.theme.accents
        for i in range(24):
            c = self._cell(i)
            bar = QRectF(c.left() + 2, c.top(), max(2.0, c.width() - 4), c.height())
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor("#FFFFFF" if self.theme.dark else "#6A6A90", 22)); p.drawRoundedRect(bar, 4, 4)
            r = self.rows[i] if i < len(self.rows) else None
            if r and r["engaged_sec"] > 0:
                h = bar.height() * min(1.0, r["engaged_sec"] / 3600.0)
                p.setBrush(qcolor(a1, 120 if r["unlogged_sec"] >= 300 else 215)); p.drawRoundedRect(QRectF(bar.left(), bar.bottom() - h, bar.width(), h), 4, 4)
                lg = bar.height() * min(1.0, r["logged_sec"] / 3600.0)
                if lg > 0:
                    p.setBrush(qcolor(a0, 245)); p.drawRoundedRect(QRectF(bar.left() + bar.width() * 0.25, bar.bottom() - lg, bar.width() * 0.5, lg), 3, 3)
                if r["unlogged_sec"] >= 300 and i != now_h:
                    p.setBrush(qcolor(a2, 255)); p.drawEllipse(QRectF(bar.center().x() - 3, bar.top() - 5, 6, 6))
            if i == now_h:
                p.setBrush(Qt.NoBrush); p.setPen(QPen(qcolor(a1, 255), 1.6)); p.drawRoundedRect(bar, 4, 4)
            if i % 3 == 0:
                p.setPen(self.theme.text(True)); p.drawText(QRectF(c.left() - 6, self.height() - 20, c.width() + 12, 16), Qt.AlignCenter, to_fa_digits(f"{i}"))
