"""Floating quick-access bubble: a draggable liquid-glass orb that stays above every other program.

* drag it anywhere, it glides to the nearest screen edge with a springy overshoot and remembers where it was (also across monitors);
* click -> a quick panel opens beside it: ONE line ("fix login #bug @web 45m" or "standup 09:30-10:00"), live preview, three modes
  (task / log finished time / start timer), duration + project chips. Enter submits; the panel stays open for rapid-fire entries;
* shows how many timers are running; fades when you are not near it (zero idle cost: the animation timer only runs while something moves).
All the rules (parsing, project matching, time ranges, geometry) are in tested services; this file only draws and routes events.
"""
from __future__ import annotations

import logging
import math
from typing import List, Optional, Tuple

from PyQt5.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QVBoxLayout, QWidget

from ..core.models import Project
from ..services import geometry as geo, lists as LS, quick, quickadd
from . import icons
from .forms import FlowLayout, Segmented, chip_button
from .glass import GlassButton, LiquidCheck, qcolor
from .liquid.physics import Spring
from .strings import S

log = logging.getLogger("worktracker.floating")
SIZES = {"s": 56, "m": 66, "l": 78}
DURATIONS = (15, 30, 45, 60, 90, 120)


def _screen_rect(point: QPoint) -> Tuple[int, int, int, int]:
    """Available geometry (without task bar) of the screen containing ``point``; a sane default when the platform reports nothing."""
    try:
        scr = QApplication.screenAt(point) if hasattr(QApplication, "screenAt") else None
        scr = scr or QApplication.primaryScreen()
        g = scr.availableGeometry()
        r = (int(g.x()), int(g.y()), int(g.width()), int(g.height()))
        return r if r[2] > 100 and r[3] > 100 else (0, 0, 1920, 1080)
    except Exception:  # noqa: BLE001
        return (0, 0, 1920, 1080)


class QuickPanel(QFrame):
    """The popup: type one line, press Enter."""

    def __init__(self, win, bubble: "FloatingBubble") -> None:
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.win, self.bubble, self.theme, self.db = win, bubble, win.theme, win.db
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(win.layoutDirection())
        self.setFixedWidth(440)
        self.minutes, self.project_id = 0, None
        root = QVBoxLayout(self); root.setContentsMargins(24, 22, 24, 20); root.setSpacing(10)
        head = QHBoxLayout(); ic = QLabel(); ic.setPixmap(icons.pixmap("bolt", self.theme.accents[1], 24)); head.addWidget(ic)
        t = QLabel(S["qa_title"]); f = t.font(); f.setPointSizeF(13.5); f.setBold(True); t.setFont(f); head.addWidget(t, 1)
        op = GlassButton("", self.theme, icon="home"); op.setFixedSize(38, 38); op.setToolTip(S["qa_open"]); op.clicked.connect(self._open_app); head.addWidget(op)
        root.addLayout(head)
        self.mode = Segmented([(S["qa_task"], "task"), (S["qa_log"], "log"), (S["qa_timer"], "timer"), (S["qa_list"], "list")], wrap=False)
        self.mode.setValue(self.db.get_setting("float_mode", "task"), emit=False); self.mode.changed.connect(self._mode_changed)
        root.addWidget(self.mode)
        self.edit = QLineEdit(placeholderText=S["qa_hint"]); self.edit.textChanged.connect(self._preview); self.edit.returnPressed.connect(self.submit)
        root.addWidget(self.edit)
        self.info = QLabel(""); self.info.setProperty("muted", True); self.info.setWordWrap(True); root.addWidget(self.info)
        host = QWidget(); fl = FlowLayout(host, 6); self._dur_chips = []
        for m in DURATIONS:
            b = chip_button(f"{m}'", True); b.clicked.connect(lambda _c=False, x=m: self._pick_minutes(x)); fl.addWidget(b); self._dur_chips.append((b, m))
        self.dur_host = host; root.addWidget(host)
        ph = QWidget(); pl = FlowLayout(ph, 6); self._proj_chips = []
        none = chip_button(S["no_project"], True); none.setChecked(True); none.clicked.connect(lambda: self._pick_project(None)); pl.addWidget(none); self._proj_chips.append((none, None))
        for p in self._recent_projects():
            b = chip_button(p.name if len(p.name) < 16 else p.name[:15] + "…", True); b.clicked.connect(lambda _c=False, pid=p.id: self._pick_project(pid)); pl.addWidget(b); self._proj_chips.append((b, p.id))
        self.proj_host = ph; root.addWidget(ph)
        self.list_id = LS.ensure_default(self.db)["id"]                                  # check-list mode: tick tasks and add several at once, right from the bubble
        self.list_row = QWidget(); self.list_flow = FlowLayout(self.list_row, 6); root.addWidget(self.list_row)
        self.check_host = QWidget(); self.check_lay = QVBoxLayout(self.check_host); self.check_lay.setContentsMargins(0, 0, 0, 0); self.check_lay.setSpacing(2); root.addWidget(self.check_host)
        self.feedback = QLabel(""); self.feedback.setWordWrap(True); root.addWidget(self.feedback)
        row = QHBoxLayout(); row.addStretch()
        self.go = GlassButton(S["qa_add"], self.theme, primary=True, icon="check"); self.go.clicked.connect(self.submit); row.addWidget(self.go); root.addLayout(row)
        self._mode_changed(self.mode.value())

    # ---- data helpers ------------------------------------------------------------------
    def _recent_projects(self) -> List[Project]:
        rows = self.db.conn.execute("SELECT project_id FROM entries WHERE project_id IS NOT NULL GROUP BY project_id ORDER BY MAX(start_utc) DESC LIMIT 4").fetchall()
        out = []
        for r in rows:
            p = self.db.get(Project, r[0])
            if p is not None:
                out.append(p)
        return out

    def _mode_changed(self, mode) -> None:
        self.db.set_setting("float_mode", mode)
        self.go.setText({"task": S["qa_add"], "log": S["qa_log_it"], "timer": S["qa_start"], "list": S["qa_add"]}.get(mode, S["qa_add"]))
        self.edit.setPlaceholderText({"task": S["qa_hint"], "log": S["qa_hint_log"], "timer": S["qa_hint_timer"], "list": S["qa_hint_list"]}.get(mode, S["qa_hint"]))
        is_list = mode == "list"
        self.dur_host.setVisible(not is_list); self.proj_host.setVisible(not is_list); self.list_row.setVisible(is_list); self.check_host.setVisible(is_list)
        if is_list:
            self._rebuild_lists()
        self._preview()
        if self.isVisible():
            self.adjustSize()

    # ---- check-list mode ---------------------------------------------------------------------
    def _clear(self, layout) -> None:
        while layout.count():
            it = layout.takeAt(0)
            if it is not None and it.widget() is not None:
                it.widget().deleteLater()

    def _rebuild_lists(self) -> None:
        self._clear(self.list_flow)
        lists = LS.lists(self.db)
        if not any(l["id"] == self.list_id for l in lists):
            self.list_id = lists[0]["id"]
        for l in lists:
            o, _d = LS.counts(self.db, l["id"])
            b = chip_button(f"{l['name']} ({o})", True); b.setChecked(l["id"] == self.list_id)
            b.clicked.connect(lambda _c=False, i=l["id"]: self._pick_list(i)); self.list_flow.addWidget(b)
        self._refresh_checks()

    def _pick_list(self, list_id: str) -> None:
        self.list_id = list_id; self._rebuild_lists()

    def _refresh_checks(self) -> None:
        self._clear(self.check_lay)
        open_tasks = LS.tasks(self.db, self.list_id, include_done=False)
        for e in open_tasks[:8]:
            chk = LiquidCheck(("★ " if e.important else "") + e.title, self.theme, False)
            chk.toggled.connect(lambda on, eid=e.id: self._tick(eid, on)); self.check_lay.addWidget(chk)
        if len(open_tasks) > 8:
            more = QLabel(f"+{len(open_tasks) - 8}"); more.setProperty("muted", True); self.check_lay.addWidget(more)
        if not open_tasks:
            empty = QLabel(S["qa_list_empty"]); empty.setProperty("muted", True); self.check_lay.addWidget(empty)

    def _tick(self, entry_id: str, on: bool) -> None:
        try:
            LS.toggle(self.db, entry_id)
        except KeyError:
            return
        if self.theme.fx is not None:
            self.theme.fx.play("success", 0.8)
        QTimer.singleShot(280, self._rebuild_lists)                                      # let the tick animation play before the row leaves
        self.win.refresh_all()

    def _pick_minutes(self, m: int) -> None:
        self.minutes = 0 if self.minutes == m else m
        for b, x in self._dur_chips:
            b.setChecked(x == self.minutes)
        self._preview()

    def _pick_project(self, pid: Optional[str]) -> None:
        self.project_id = pid
        for b, x in self._proj_chips:
            b.setChecked(x == pid)
        self._preview()

    def _preview(self, *_a) -> None:
        """Live reading of what Enter will do - so you never have to guess."""
        text = self.edit.text().strip()
        if not text:
            self.info.setText(S["qa_empty"] if self.mode.value() != "list" else S["qa_hint_list"]); return
        if self.mode.value() == "list":
            n = len([x for x in "\n".join(x.strip() for x in text.replace("؛", ";").split(";")).splitlines() if x.strip()])
            self.info.setText(__import__("worktracker.core.persian", fromlist=["x"]).to_fa_digits(f"{n} {S['qa_done_list']}")); return
        try:
            c = quick.parse(text)
        except ValueError as exc:
            self.info.setText("⚠ " + str(exc)); return
        pid = self.project_id or quickadd.resolve_project(self.db, c.project)
        proj = self.db.get(Project, pid).name if pid else S["no_project"]
        bits = [f"{S['title']}: {c.title}", f"{S['project']}: {proj}"]
        if c.has_range:
            bits.append(f"{c.start_time:%H:%M}–{c.end_time:%H:%M}")
        elif (self.minutes or c.minutes):
            bits.append(f"{self.minutes or c.minutes} {S['min']}")
        if c.tags:
            bits.append("#" + " #".join(c.tags))
        from ..core.persian import to_fa_digits
        self.info.setText(to_fa_digits("  ·  ".join(bits)))

    # ---- actions ----------------------------------------------------------------------------
    def _submit_list(self, text: str) -> None:
        try:
            made = LS.bulk_add(self.db, self.list_id, "\n".join(x.strip() for x in text.replace("؛", ";").split(";")))
        except LS.ListError as exc:
            self.feedback.setStyleSheet("color:#FF8A9B;font-weight:bold;"); self.feedback.setText("⚠ " + str(exc)); self._shake(); return
        self.feedback.setStyleSheet("color:#8FD8A8;font-weight:bold;")
        from ..core.persian import to_fa_digits
        self.feedback.setText("✓ " + to_fa_digits(f"{len(made)} {S['qa_done_list']}"))
        self.edit.clear()
        if self.theme.fx is not None:
            self.theme.fx.play("success")
        self._rebuild_lists(); self.win.refresh_all(); self.edit.setFocus()

    def submit(self) -> None:
        text = self.edit.text().strip()
        if self.mode.value() == "list":
            self._submit_list(text); return
        try:
            r = quickadd.create(self.db, text, self.mode.value(), self.project_id, self.minutes)
        except ValueError as exc:
            self.feedback.setStyleSheet("color:#FF8A9B;font-weight:bold;"); self.feedback.setText("⚠ " + str(exc)); self._shake(); return
        self.feedback.setStyleSheet("color:#8FD8A8;font-weight:bold;")
        verb = {"task": S["qa_done_task"], "log": S["qa_done_log"], "timer": S["qa_done_timer"]}[r.kind]
        from ..core.persian import to_fa_digits
        self.feedback.setText("✓ " + to_fa_digits(f"{verb}: {r.entry.title}" + (f"  ({r.minutes} {S['min']})" if r.minutes else "")))
        self.edit.clear(); self.minutes = 0
        for b, _m in self._dur_chips:
            b.setChecked(False)
        if self.theme.fx is not None:
            self.theme.fx.play("success")
        if r.kind == "timer":
            self.win._timers_on()
        self.win.refresh_all()
        self.bubble.refresh_state()
        self.edit.setFocus()

    def _open_app(self) -> None:
        self.close(); self.win.showNormal(); self.win.raise_(); self.win.activateWindow()

    def _shake(self) -> None:
        if self.theme.lite:
            return
        x0 = self.pos(); a = QPropertyAnimation(self, b"pos", self); a.setDuration(320)
        for t, dx in ((0.0, 0), (0.2, -10), (0.4, 9), (0.6, -6), (0.8, 3), (1.0, 0)):
            a.setKeyValueAt(t, QPoint(x0.x() + dx, x0.y()))
        a.start(); self._anim = a
        if self.theme.fx is not None:
            self.theme.fx.play("warn")

    # ---- window ---------------------------------------------------------------------------------
    def popup_at_bubble(self) -> None:
        self.adjustSize()
        b = self.bubble
        bx, by = b.x() + 12, b.y() + 12
        screen = _screen_rect(b.pos())
        x, y = geo.panel_position((bx, by, b.orb_size, b.orb_size), self.width(), self.sizeHint().height(), screen)
        self.move(x, y); self.show(); self.edit.setFocus()
        if self.theme.fx is not None:
            self.theme.fx.play("open")

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        for i, a in enumerate((26, 16, 9, 4)):
            p.setPen(QPen(QColor(0, 0, 0, a), 1)); p.setBrush(Qt.NoBrush); p.drawRoundedRect(r.adjusted(-i * 2, -i * 2 + 4, i * 2, i * 2 + 4), 24 + i * 2, 24 + i * 2)
        path = QPainterPath(); path.addRoundedRect(r, 24, 24)
        dark = self.theme.dark
        p.fillPath(path, QColor(str(self.theme.t["bg"])) if dark else QColor(252, 252, 255))
        p.setClipPath(path)
        for (fx_, fy_), col in (((0.0, 0.0), self.theme.accents[0]), ((1.0, 1.0), self.theme.accents[2])):
            g = QRadialGradient(QPointF(r.left() + r.width() * fx_, r.top() + r.height() * fy_), r.width() * 0.55)
            g.setColorAt(0, qcolor(col, 70 if dark else 44)); g.setColorAt(1, qcolor(col, 0)); p.fillRect(r, QBrush(g))
        bar = QLinearGradient(r.topLeft(), r.topRight()); bar.setColorAt(0, qcolor(self.theme.accents[0], 230)); bar.setColorAt(1, qcolor(self.theme.accents[1], 230))
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 4), QBrush(bar))
        p.setClipping(False)
        p.setPen(QPen(qcolor("#FFFFFF" if dark else "#6A6A90", 80), 1.2)); p.setBrush(Qt.NoBrush); p.drawPath(path)


class FloatingBubble(QWidget):
    """The orb. Frameless, translucent, always on top, hidden from the task bar."""

    def __init__(self, win) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        self.win, self.theme, self.db = win, win.theme, win.db
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        if hasattr(Qt, "WA_MacAlwaysShowToolWindow"):
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.panel: Optional[QuickPanel] = None
        self._press: Optional[QPoint] = None
        self._origin = QPoint()
        self._moved = False
        self._running, self._elapsed = 0, 0
        self._hover = Spring(0.0, 0.0, stiffness=190.0, damping=13.0)
        self._t = 0.0
        self._timer = QTimer(self); self._timer.setInterval(33); self._timer.timeout.connect(self._tick)
        self._fade_timer = QTimer(self); self._fade_timer.setSingleShot(True); self._fade_timer.setInterval(2600); self._fade_timer.timeout.connect(self._fade_out)
        self.orb_size = 66
        self.reload()

    # ---- settings -------------------------------------------------------------------------------
    def reload(self) -> None:
        db = self.db
        self.orb_size = SIZES.get(db.get_setting("float_size", "m"), 66)
        self.setFixedSize(self.orb_size + 24, self.orb_size + 24)
        self._opacity_active = max(0.3, min(1.0, int(db.get_setting("float_opacity", 95)) / 100))
        self._opacity_idle = max(0.2, min(self._opacity_active, int(db.get_setting("float_idle_opacity", 55)) / 100))
        self.setWindowOpacity(self._opacity_idle)
        self._restore_pos()
        self.refresh_state()

    def _restore_pos(self) -> None:
        saved = self.db.get_setting("float_pos")
        if isinstance(saved, (list, tuple)) and len(saved) == 2:
            x, y = int(saved[0]), int(saved[1])
        else:
            sr = _screen_rect(QPoint(0, 0))
            x, y = sr[0] + sr[2] - self.width() - 6, sr[1] + sr[3] // 2
        x, y = geo.keep_on_screen(x, y, self.width(), self.height(), _screen_rect(QPoint(x, y)))
        self.move(x, y)

    def _save_pos(self) -> None:
        self.db.set_setting("float_pos", [self.x(), self.y()])

    # ---- state ------------------------------------------------------------------------------------
    def set_running(self, count: int, elapsed_sec: int) -> None:
        changed = count != self._running
        self._running, self._elapsed = count, elapsed_sec
        if changed:
            self.refresh_state()

    def refresh_state(self) -> None:
        if self._running and self.isVisible() and not self.theme.lite:
            if not self._timer.isActive():
                self._timer.start()
        elif not self._running and self._hover.settled and self._timer.isActive():
            self._timer.stop()
        self.update()

    def _tick(self) -> None:
        self._t += 0.033
        self._hover.step(0.033)
        self.update()
        if not self._running and self._hover.settled:
            self._timer.stop()

    # ---- fading -------------------------------------------------------------------------------------
    def _fade(self, to: float) -> None:
        a = QPropertyAnimation(self, b"windowOpacity", self); a.setDuration(220); a.setStartValue(self.windowOpacity()); a.setEndValue(to); a.start(); self._fa = a

    def _fade_out(self) -> None:
        if self._press is None and (self.panel is None or not self.panel.isVisible()):
            self._fade(self._opacity_idle)

    def enterEvent(self, e) -> None:  # noqa: N802
        self._hover.target = 1.0; self._fade_timer.stop(); self._fade(self._opacity_active)
        if not self._timer.isActive() and not self.theme.lite:
            self._timer.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._hover.target = 0.0; self._fade_timer.start(); super().leaveEvent(e)

    # ---- mouse: drag / click ------------------------------------------------------------------------
    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._press, self._origin, self._moved = e.globalPos(), self.pos(), False
            if self.theme.fx is not None:
                self.theme.fx.play("bloop", 0.6)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self._press is not None and (e.buttons() & Qt.LeftButton):
            d = e.globalPos() - self._press
            if not self._moved and abs(d.x()) + abs(d.y()) > 6:
                self._moved = True
                if self.panel is not None:
                    self.panel.close()
                if self.theme.fx is not None:
                    self.theme.fx.drag_started()
            if self._moved:
                self.move(self._origin + d)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        was_drag, self._press = self._moved, None
        if was_drag:
            self._snap()
            if self.theme.fx is not None:
                self.theme.fx.drag_finished()
        elif e.button() == Qt.LeftButton:
            self.open_panel()
        super().mouseReleaseEvent(e)

    def _snap(self) -> None:
        sr = _screen_rect(self.pos() + QPoint(self.width() // 2, self.height() // 2))
        if self.db.get_setting("float_snap", True):
            x, y = geo.snap_to_edge(self.x(), self.y(), self.width(), self.height(), sr, 0)
        else:
            x, y = geo.keep_on_screen(self.x(), self.y(), self.width(), self.height(), sr)
        a = QPropertyAnimation(self, b"pos", self); a.setDuration(0 if self.theme.lite else 340); a.setStartValue(self.pos()); a.setEndValue(QPoint(x, y))
        a.setEasingCurve(QEasingCurve.OutBack); a.finished.connect(self._save_pos); a.start(); self._snap_anim = a

    def contextMenuEvent(self, e) -> None:  # noqa: N802
        m = QMenu(self)
        m.addAction(S["qa_title"], self.open_panel)
        m.addAction(S["qa_open"], self._show_app)
        m.addAction(S["start"] + " / " + S["stop"], self.win.toggle_timer)
        m.addSeparator()
        m.addAction(S["qa_hide"], lambda: self.win.set_bubble(False))
        m.exec_(e.globalPos())

    def _show_app(self) -> None:
        self.win.showNormal(); self.win.raise_(); self.win.activateWindow()

    def open_panel(self) -> None:
        if self.panel is None:
            self.panel = QuickPanel(self.win, self)
        self._fade(self._opacity_active)
        self.panel.popup_at_bubble()

    # ---- painting -------------------------------------------------------------------------------------------
    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        d = float(self.orb_size)
        hv = max(0.0, min(1.3, self._hover.value))
        breathe = 0.0 if self.theme.lite else (math.sin(self._t * 2.2) * 1.2 if self._running else 0.0)
        r = QRectF((self.width() - d) / 2 - hv * 1.5 - breathe, (self.height() - d) / 2 - hv * 1.5 - breathe, d + 3 * hv + 2 * breathe, d + 3 * hv + 2 * breathe)
        a0, a1, a2 = self.theme.accents
        glow = QRadialGradient(r.center(), r.width() * 0.95)
        glow.setColorAt(0.55, qcolor(a1, int(70 + 50 * hv))); glow.setColorAt(1, qcolor(a1, 0))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(glow)); p.drawEllipse(r.center(), r.width() * 0.95, r.height() * 0.95)
        p.setBrush(QColor(0, 0, 0, 60)); p.drawEllipse(r.translated(0, 3))                                   # soft shadow
        g = QRadialGradient(QPointF(r.left() + r.width() * 0.32, r.top() + r.height() * 0.25), r.width() * 0.95)
        g.setColorAt(0, qcolor(a1, 255)); g.setColorAt(0.65, qcolor(a0, 245)); g.setColorAt(1, qcolor(a0, 215))
        p.setBrush(QBrush(g)); p.drawEllipse(r)
        if self._running and not self.theme.lite:                                                           # rotating ring while timers run
            p.setBrush(Qt.NoBrush); p.setPen(QPen(qcolor("#FFFFFF", 200), 2.4, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(r.adjusted(-5, -5, 5, 5), int(-self._t * 90 * 16) % (360 * 16), 100 * 16)
        p.setPen(QPen(QColor(255, 255, 255, 90), 1.2)); p.setBrush(Qt.NoBrush); p.drawEllipse(r)
        p.setPen(QPen(QColor(255, 255, 255, 190), 2.6, Qt.SolidLine, Qt.RoundCap)); p.drawArc(r.adjusted(7, 7, -7, -7), 110 * 16, 42 * 16)   # glass highlight
        icons.draw("clock" if self._running else "plus", p, QRectF(r.center().x() - d * 0.2, r.center().y() - d * 0.2, d * 0.4, d * 0.4), QColor("#FFFFFF"), 2.6)
        if self._running > 1:                                                                                # badge
            br = QRectF(r.right() - 16, r.top() - 2, 20, 20)
            p.setPen(Qt.NoPen); p.setBrush(qcolor(a2, 255)); p.drawEllipse(br)
            p.setPen(QColor("#10101c")); f = self.font(); f.setPointSizeF(8.5); f.setBold(True); p.setFont(f); p.drawText(br, Qt.AlignCenter, str(self._running))
