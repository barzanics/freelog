"""Vector icon set drawn with QPainter (crisp at any size, tinted by the theme, no files needed).

Drop a file named ``<icon>.svg`` / ``<icon>.png`` into ``assets/icons`` to override any built-in icon.
Every icon is drawn in a 24x24 box with round caps - the same visual language as common line-icon sets.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

Draw = Callable[[QPainter], None]
_REG: Dict[str, Draw] = {}
_CACHE: Dict[Tuple[str, str, int], QIcon] = {}
_OVERRIDE_DIRS: List[Path] = []


def reg(name: str):
    def deco(fn: Draw) -> Draw:
        _REG[name] = fn
        return fn
    return deco


def _ln(p: QPainter, *pts: float) -> None:
    """Independent segments: every 4 numbers (x1, y1, x2, y2) are one line."""
    for i in range(0, len(pts) - 3, 4):
        p.drawLine(QPointF(pts[i], pts[i + 1]), QPointF(pts[i + 2], pts[i + 3]))


def _poly(p: QPainter, pts: Iterable[Tuple[float, float]], close: bool = False) -> None:
    pts = list(pts)
    path = QPainterPath(QPointF(*pts[0]))
    for x, y in pts[1:]:
        path.lineTo(x, y)
    if close:
        path.closeSubpath()
    p.drawPath(path)


def _rr(p: QPainter, x: float, y: float, w: float, h: float, r: float = 3) -> None:
    p.drawRoundedRect(QRectF(x, y, w, h), r, r)


def _circle(p: QPainter, x: float, y: float, r: float, fill: bool = False) -> None:
    if fill:
        p.save(); p.setBrush(p.pen().color()); p.drawEllipse(QPointF(x, y), r, r); p.restore()
    else:
        p.drawEllipse(QPointF(x, y), r, r)


@reg("dashboard")
def _(p): _rr(p, 3, 3, 8, 8); _rr(p, 13, 3, 8, 5); _rr(p, 13, 11, 8, 10); _rr(p, 3, 13, 8, 8)
@reg("today")
def _(p):
    _circle(p, 12, 12, 4)
    for a in range(8):
        t = a * math.pi / 4; _ln(p, 12 + 7 * math.cos(t), 12 + 7 * math.sin(t), 12 + 9.5 * math.cos(t), 12 + 9.5 * math.sin(t))
@reg("tasks")
def _(p):
    _poly(p, [(3.5, 6.5), (5, 8), (8, 4.5)]); _poly(p, [(3.5, 12.5), (5, 14), (8, 10.5)]); _circle(p, 5.5, 19, 1.4); _ln(p, 11, 6.5, 21, 6.5, 11, 12.5, 21, 12.5, 11, 19, 21, 19)
@reg("board")
def _(p): _rr(p, 3, 4, 5, 16); _rr(p, 9.5, 4, 5, 10); _rr(p, 16, 4, 5, 13)
@reg("calendar")
def _(p): _rr(p, 3, 5, 18, 16, 3.5); _ln(p, 3, 10, 21, 10, 8, 3, 8, 7, 16, 3, 16, 7); _circle(p, 8, 15, 1, True); _circle(p, 12, 15, 1, True); _circle(p, 16, 15, 1, True)
@reg("planner")
def _(p): _ln(p, 7, 4, 7, 20); _circle(p, 7, 6, 2); _circle(p, 7, 12, 2); _circle(p, 7, 18, 2); _ln(p, 12, 6, 21, 6, 12, 12, 18, 12, 12, 18, 20, 18)
@reg("matrix")
def _(p): _rr(p, 3, 3, 18, 18, 3.5); _ln(p, 12, 3, 12, 21, 3, 12, 21, 12); _circle(p, 7.5, 7.5, 1, True)
@reg("projects")
def _(p): _poly(p, [(3, 7), (3, 18.5), (5, 20), (19, 20), (21, 18.5), (21, 9), (19, 7.5), (11, 7.5), (9.5, 5), (5, 5), (3, 7)], True)
@reg("pm")
def _(p): _rr(p, 3, 4.5, 10, 3.5, 1.7); _rr(p, 8, 10.5, 13, 3.5, 1.7); _rr(p, 5, 16.5, 9, 3.5, 1.7)
@reg("habits")
def _(p):
    path = QPainterPath(QPointF(12, 3)); path.cubicTo(18, 10, 19, 12.5, 19, 15); path.cubicTo(19, 18.9, 15.9, 21.5, 12, 21.5); path.cubicTo(8.1, 21.5, 5, 18.9, 5, 15); path.cubicTo(5, 12.5, 6, 10, 12, 3)
    p.drawPath(path); p.drawArc(QRectF(8.5, 13, 7, 6), 200 * 16, 110 * 16)
_REG["droplet"] = _REG["habits"]
@reg("goals")
def _(p): _circle(p, 12, 12, 9); _circle(p, 12, 12, 5); _circle(p, 12, 12, 1.2, True)
@reg("team")
def _(p):
    _circle(p, 9, 8, 3.5); p.drawArc(QRectF(2.5, 13.5, 13, 10), 0, 180 * 16); _circle(p, 17, 9, 2.6); p.drawArc(QRectF(14, 14.5, 8, 7), 20 * 16, 140 * 16)
@reg("billing")
def _(p): _rr(p, 2.5, 5, 19, 14, 3); _ln(p, 2.5, 10, 21.5, 10, 6, 15, 10, 15)
@reg("reports")
def _(p): _poly(p, [(6, 3), (14, 3), (19, 8), (19, 21), (6, 21), (6, 3)], True); _ln(p, 14, 3, 14, 8, 14, 8, 19, 8, 9, 17, 9, 14, 12, 17, 12, 11, 15, 17, 15, 13)
@reg("analytics")
def _(p): _ln(p, 6, 20, 6, 12, 12, 20, 12, 5, 18, 20, 18, 14, 3, 21, 21, 21)
@reg("screenshots")
def _(p): _rr(p, 3, 4.5, 18, 12.5, 2.5); _ln(p, 8.5, 21, 15.5, 21, 12, 17, 12, 21); _circle(p, 12, 10.7, 2.7)
@reg("tools")
def _(p): _ln(p, 4, 7, 20, 7, 4, 12, 20, 12, 4, 17, 20, 17); _circle(p, 9, 7, 2.2, True); _circle(p, 15.5, 12, 2.2, True); _circle(p, 8, 17, 2.2, True)
@reg("settings")
def _(p):
    _circle(p, 12, 12, 3); _circle(p, 12, 12, 6.8)
    for a in range(8):
        t = a * math.pi / 4; _ln(p, 12 + 6.8 * math.cos(t), 12 + 6.8 * math.sin(t), 12 + 9.3 * math.cos(t), 12 + 9.3 * math.sin(t))
@reg("plus")
def _(p): _ln(p, 12, 5, 12, 19, 5, 12, 19, 12)
@reg("minus")
def _(p): _ln(p, 5, 12, 19, 12)
@reg("close")
def _(p): _ln(p, 6, 6, 18, 18, 18, 6, 6, 18)
@reg("check")
def _(p): _poly(p, [(4.5, 12.5), (10, 18), (19.5, 6.5)])
@reg("play")
def _(p): _poly(p, [(7, 4.5), (19, 12), (7, 19.5)], True)
@reg("pause")
def _(p): _rr(p, 6, 5, 4, 14, 1.5); _rr(p, 14, 5, 4, 14, 1.5)
@reg("stop")
def _(p): _rr(p, 6, 6, 12, 12, 2.5)
@reg("search")
def _(p): _circle(p, 10.5, 10.5, 6.5); _ln(p, 15.5, 15.5, 20.5, 20.5)
@reg("bell")
def _(p):
    path = QPainterPath(QPointF(6, 17)); path.cubicTo(7, 15, 7, 13, 7, 10); path.cubicTo(7, 7, 9, 5.5, 12, 5.5); path.cubicTo(15, 5.5, 17, 7, 17, 10); path.cubicTo(17, 13, 17, 15, 18, 17); path.closeSubpath()
    p.drawPath(path); _ln(p, 10, 20, 14, 20)
@reg("tag")
def _(p): _poly(p, [(3, 12), (12, 3), (21, 3), (21, 12), (12, 21), (3, 12)], True); _circle(p, 16.5, 7.5, 1.3, True)
@reg("flag")
def _(p): _ln(p, 5, 21, 5, 3); _poly(p, [(5, 4), (18, 4), (15, 8.5), (18, 13), (5, 13)], True)
@reg("clock")
def _(p): _circle(p, 12, 12, 9); _poly(p, [(12, 6.5), (12, 12), (16, 14)])
@reg("trash")
def _(p): _ln(p, 4, 7, 20, 7, 10, 3.5, 14, 3.5); _poly(p, [(6, 7), (7, 20), (17, 20), (18, 7)]); _ln(p, 10, 11, 10, 16, 14, 11, 14, 16)
@reg("edit")
def _(p): _poly(p, [(4, 20), (4, 16), (16, 4), (20, 8), (8, 20), (4, 20)], True); _ln(p, 13, 7, 17, 11)
@reg("chevron_down")
def _(p): _poly(p, [(6, 9), (12, 15), (18, 9)])
@reg("chevron_up")
def _(p): _poly(p, [(6, 15), (12, 9), (18, 15)])
@reg("chevron_left")
def _(p): _poly(p, [(15, 6), (9, 12), (15, 18)])
@reg("chevron_right")
def _(p): _poly(p, [(9, 6), (15, 12), (9, 18)])
@reg("drag")
def _(p):
    for x in (9, 15):
        for y in (6, 12, 18):
            _circle(p, x, y, 1.3, True)
@reg("bubble")
def _(p): _circle(p, 12, 12, 8.5); p.drawArc(QRectF(7.5, 7.5, 6, 6), 100 * 16, 80 * 16)
@reg("moon")
def _(p):
    path = QPainterPath(QPointF(20, 14.5)); path.cubicTo(13, 18, 6, 12, 9.5, 4); path.cubicTo(3, 5, 1.5, 15, 8.5, 20); path.cubicTo(13, 23, 19, 20, 20, 14.5); p.drawPath(path)
@reg("sound")
def _(p): _poly(p, [(4, 10), (8, 10), (13, 5.5), (13, 18.5), (8, 14), (4, 14)], True); p.drawArc(QRectF(13.5, 8, 6, 8), -60 * 16, 120 * 16)
@reg("mute")
def _(p): _poly(p, [(4, 10), (8, 10), (13, 5.5), (13, 18.5), (8, 14), (4, 14)], True); _ln(p, 16, 9, 21, 15, 21, 9, 16, 15)
@reg("refresh")
def _(p): p.drawArc(QRectF(4, 4, 16, 16), 40 * 16, 270 * 16); _poly(p, [(16, 3), (19.5, 6.5), (15, 8.5)])
@reg("download")
def _(p): _ln(p, 12, 4, 12, 15); _poly(p, [(7, 11), (12, 16), (17, 11)]); _ln(p, 5, 20, 19, 20)
@reg("upload")
def _(p): _ln(p, 12, 16, 12, 5); _poly(p, [(7, 9), (12, 4), (17, 9)]); _ln(p, 5, 20, 19, 20)
@reg("star")
def _(p): _poly(p, [(12, 3), (14.8, 9), (21, 9.7), (16.3, 14), (17.6, 20.5), (12, 17.3), (6.4, 20.5), (7.7, 14), (3, 9.7), (9.2, 9)], True)
@reg("link")
def _(p): _rr(p, 3, 9, 11, 6, 3); _rr(p, 10, 9, 11, 6, 3)
@reg("lock")
def _(p): _rr(p, 5, 11, 14, 10, 2.5); p.drawArc(QRectF(8, 3, 8, 10), 0, 180 * 16); _circle(p, 12, 16, 1.3, True)
@reg("user")
def _(p): _circle(p, 12, 8, 4); p.drawArc(QRectF(4, 13, 16, 14), 0, 180 * 16)
@reg("bolt")
def _(p): _poly(p, [(13, 2.5), (5, 13.5), (11, 13.5), (10, 21.5), (19, 10), (13, 10), (13, 2.5)], True)
@reg("flame")
def _(p):
    path = QPainterPath(QPointF(12, 2.5)); path.cubicTo(14, 7, 19, 9, 19, 15); path.cubicTo(19, 19, 16, 21.5, 12, 21.5); path.cubicTo(8, 21.5, 5, 19, 5, 15); path.cubicTo(5, 12, 7, 11, 8, 8.5); path.cubicTo(9.5, 10, 10.5, 10.5, 11, 10); path.cubicTo(11.5, 8, 11, 5, 12, 2.5)
    p.drawPath(path)
@reg("image")
def _(p): _rr(p, 3, 4, 18, 16, 3); _circle(p, 8.5, 9.5, 1.8); _poly(p, [(3.5, 18), (9.5, 12.5), (13.5, 16), (16, 13.5), (20.5, 18)])
@reg("pin")
def _(p): _poly(p, [(9, 3), (15, 3), (14.5, 10), (18, 14), (6, 14), (9.5, 10), (9, 3)], True); _ln(p, 12, 14, 12, 21)
@reg("filter")
def _(p): _poly(p, [(3, 5), (21, 5), (14, 13), (14, 20), (10, 18), (10, 13), (3, 5)], True)
@reg("list")
def _(p): _ln(p, 8, 6, 21, 6, 8, 12, 21, 12, 8, 18, 21, 18); _circle(p, 4, 6, 1.2, True); _circle(p, 4, 12, 1.2, True); _circle(p, 4, 18, 1.2, True)
@reg("grid")
def _(p): _rr(p, 3, 3, 8, 8, 2); _rr(p, 13, 3, 8, 8, 2); _rr(p, 3, 13, 8, 8, 2); _rr(p, 13, 13, 8, 8, 2)
@reg("note")
def _(p): _rr(p, 4, 3, 16, 18, 3); _ln(p, 8, 8, 16, 8, 8, 12, 16, 12, 8, 16, 13, 16)
@reg("eye")
def _(p):
    path = QPainterPath(QPointF(2.5, 12)); path.cubicTo(6, 5, 18, 5, 21.5, 12); path.cubicTo(18, 19, 6, 19, 2.5, 12); p.drawPath(path); _circle(p, 12, 12, 3)
@reg("sparkle")
def _(p): _poly(p, [(12, 3), (14, 10), (21, 12), (14, 14), (12, 21), (10, 14), (3, 12), (10, 10)], True)
@reg("lightbulb")
def _(p): p.drawArc(QRectF(6, 3, 12, 12), -40 * 16, 260 * 16); _ln(p, 9.5, 18, 14.5, 18, 10.5, 21, 13.5, 21, 9.5, 14.5, 9.5, 18, 14.5, 14.5, 14.5, 18)
@reg("copy")
def _(p): _rr(p, 8, 8, 12, 12, 2.5); _poly(p, [(16, 8), (16, 5), (5, 5), (4, 6), (4, 16), (8, 16)])
@reg("camera")
def _(p): _rr(p, 3, 7, 18, 13, 3); _poly(p, [(8, 7), (9.5, 4), (14.5, 4), (16, 7)]); _circle(p, 12, 13.5, 3.2)
@reg("sun")
def _(p): _REG["today"](p)
@reg("home")
def _(p): _poly(p, [(3, 11), (12, 3.5), (21, 11)]); _poly(p, [(5.5, 9.5), (5.5, 20), (18.5, 20), (18.5, 9.5)]); _ln(p, 10, 20, 10, 14, 14, 14, 14, 20)

NAMES = tuple(sorted(_REG))


def set_override_dirs(dirs: Iterable[Path]) -> None:
    """Folders searched for ``<name>.svg|png`` overrides (e.g. ``assets/icons``)."""
    _OVERRIDE_DIRS[:] = [Path(d) for d in dirs]
    _CACHE.clear()


def _override(name: str) -> Optional[Path]:
    for d in _OVERRIDE_DIRS:
        for ext in (".svg", ".png"):
            f = d / f"{name}{ext}"
            if f.exists():
                return f
    return None


def draw(name: str, p: QPainter, rect: QRectF, color: QColor, width: float = 1.9) -> None:
    """Draw icon ``name`` into ``rect`` with ``p`` (used by buttons that paint themselves)."""
    fn = _REG.get(name)
    if fn is None:
        return
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(rect.topLeft())
    p.scale(rect.width() / 24.0, rect.height() / 24.0)
    pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    fn(p)
    p.restore()


def pixmap(name: str, color: str = "#FFFFFF", size: int = 24, dpr: float = 2.0) -> QPixmap:
    ov = _override(name)
    if ov is not None:
        pm = QPixmap(str(ov))
        if not pm.isNull():
            return pm.scaled(int(size * dpr), int(size * dpr), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    pm.setDevicePixelRatio(dpr)
    p = QPainter(pm)
    draw(name, p, QRectF(0, 0, size, size), QColor(color))
    p.end()
    return pm


def icon(name: str, color: str = "#FFFFFF", size: int = 24) -> QIcon:
    key = (name, color, size)
    if key not in _CACHE:
        _CACHE[key] = QIcon(pixmap(name, color, size))
    return _CACHE[key]


def export_pngs(folder: Path, arrow_color: str = "#A9A9C4") -> Path:
    """Render the few glyphs the stylesheet needs as PNG files (Qt style sheets cannot draw shapes, only load images)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, color, w in (("chevron_down", arrow_color, 2.4), ("chevron_up", arrow_color, 2.4), ("check", "#FFFFFF", 3.0)):
        pm = QPixmap(48, 48)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        draw(name, p, QRectF(6, 6, 36, 36), QColor(color), w)
        p.end()
        pm.save(str(folder / f"{name}.png"), "PNG")
    return folder
