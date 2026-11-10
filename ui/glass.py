"""Liquid Glass widgets (PyQt5). Cheap by design: no live blur effects.

* ``LiquidBackground`` paints 4 soft drifting radial blobs (the "liquid"). Radial
  gradients are inherently blurred, so cards drawn translucent over it look frosted
  without any per-widget QGraphicsBlurEffect. Animation runs at <=30 fps and stops
  when the window is hidden, minimised or inactive, or when Lite mode is on.
* ``GlassCard`` = translucent fill + 1px highlight + soft shadow ring + specular top edge.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Dict, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, pyqtProperty
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient)
from PyQt5.QtWidgets import QCheckBox, QFrame, QPushButton, QWidget


# Calm, widely used palettes (Tokyo Night, Catppuccin, Rosé Pine, Nord, Latte...) - low saturation, harmonious neighbours, easy on the eyes.
# colour-psychology intent: blue/teal = focus & trust, soft green = calm & growth, warm sand/coral = approachable, violet = creativity.
THEMES: Dict[str, Dict[str, object]] = {
    "tokyo_night": {"label": "Tokyo Night", "dark": True, "bg": "#14151F", "glass": "#C0CAF5", "glass_a": "16", "text": "#C0CAF5", "muted": "#8A93B8",
                    "blobs": ("#3D59A1", "#7AA2F7", "#BB9AF7", "#1F2335"), "acc": ("#7AA2F7", "#7DCFFF", "#BB9AF7")},
    "catppuccin": {"label": "Catppuccin Mocha", "dark": True, "bg": "#181825", "glass": "#CDD6F4", "glass_a": "16", "text": "#CDD6F4", "muted": "#9399B2",
                   "blobs": ("#45475A", "#89B4FA", "#F5C2E7", "#74C7EC"), "acc": ("#89B4FA", "#94E2D5", "#CBA6F7")},
    "rose_pine": {"label": "Rosé Pine", "dark": True, "bg": "#16141F", "glass": "#E0DEF4", "glass_a": "15", "text": "#E0DEF4", "muted": "#908CAA",
                  "blobs": ("#403D52", "#C4A7E7", "#EBBCBA", "#31748F"), "acc": ("#C4A7E7", "#9CCFD8", "#EBBCBA")},
    "nord": {"label": "Nord", "dark": True, "bg": "#1B222E", "glass": "#E5E9F0", "glass_a": "15", "text": "#E5E9F0", "muted": "#9AA6BC",
             "blobs": ("#434C5E", "#81A1C1", "#88C0D0", "#5E81AC"), "acc": ("#81A1C1", "#88C0D0", "#A3BE8C")},
    "forest": {"label": "Forest Focus", "dark": True, "bg": "#101C18", "glass": "#D8F3E6", "glass_a": "15", "text": "#E6F4EC", "muted": "#8FB5A3",
               "blobs": ("#1F4D3F", "#7BC8A4", "#E2C275", "#2E6F5A"), "acc": ("#7BC8A4", "#A7D7C5", "#E2C275")},
    "paper": {"label": "Paper (light)", "dark": False, "bg": "#F3EFE7", "glass": "#FFFFFF", "glass_a": "B0", "text": "#2F2B26", "muted": "#7B7366",
              "blobs": ("#CFE0EA", "#DCE8D5", "#F2D9C9", "#E7E1D3"), "acc": ("#4C7EA8", "#6FA39A", "#D08770")},
    "latte": {"label": "Catppuccin Latte (light)", "dark": False, "bg": "#EEF0F6", "glass": "#FFFFFF", "glass_a": "B8", "text": "#3B3F5C", "muted": "#6C6F85",
              "blobs": ("#C9D3F5", "#BFE6E3", "#E3D8F5", "#E8ECF5"), "acc": ("#5B7FE8", "#3FA7A0", "#8E7CC3")},
    "sakura": {"label": "Sakura (light)", "dark": False, "bg": "#FFF3F6", "glass": "#FFFFFF", "glass_a": "B8", "text": "#43303A", "muted": "#8C6B78",
               "blobs": ("#FADADD", "#F6C1CE", "#E3D6F2", "#FFE7D6"), "acc": ("#D4688A", "#E9A3B8", "#9C8BC9")},
}
LEGACY_THEMES = {"liquid_dark": "tokyo_night", "liquid_light": "paper", "midnight": "nord", "aurora": "forest", "neon": "catppuccin", "sakura_soft": "sakura",
                 "midnight_calm": "nord", "paper_calm": "paper", "latte_light": "latte", "forest_focus": "forest", "tokyo": "tokyo_night"}
DEFAULT_THEME = "tokyo_night"
ACCENTS = THEMES[DEFAULT_THEME]["acc"]



def qcolor(hex_: str, alpha: Optional[int] = None) -> QColor:
    c = QColor(hex_)
    if alpha is not None:
        c.setAlpha(alpha)
    return c


class Theme:
    """Runtime theme holder. Switching ``name`` / ``custom_accent`` takes effect immediately (widgets read these on every paint)."""

    def __init__(self, name: str = DEFAULT_THEME, accent: Optional[str] = None, lite: bool = False, wallpaper: Optional[str] = None) -> None:
        self.name, self.custom_accent, self.lite, self.wallpaper = self.normalise(name), accent, lite, wallpaper
        self.fx = None                      # set by the main window: liquid.fx.FX (sounds + droplets)

    @staticmethod
    def normalise(name: str) -> str:
        name = LEGACY_THEMES.get(name, name)
        return name if name in THEMES else DEFAULT_THEME

    def set_name(self, name: str) -> None:
        self.name = self.normalise(name)

    @property
    def t(self) -> Dict[str, object]:
        return THEMES[self.name]

    @property
    def dark(self) -> bool:
        return bool(self.t["dark"])

    @property
    def accents(self) -> Tuple[str, str, str]:
        a = tuple(self.t["acc"])  # type: ignore[arg-type]
        return (self.custom_accent, a[1], a[2]) if self.custom_accent else a  # type: ignore[return-value]

    @property
    def accent(self) -> str:
        return self.accents[0]

    def chart_colors(self) -> List[str]:
        """Eight harmonious colours for charts, derived from the palette (never raw primaries)."""
        return list(self.accents) + [str(c) for c in self.t["blobs"][:3]] + [str(self.t["muted"]), self.accents[0], self.accents[1]]  # type: ignore[index]

    def text(self, muted: bool = False) -> QColor:
        return qcolor(str(self.t["muted" if muted else "text"]))



class LiquidBackground(QWidget):
    """Living backdrop. Cheap on purpose: the blobs are painted into a small cached image (1/5 size = 25x fewer pixels) at ~15 fps and scaled up
    smoothly (they are blurry anyway); only a handful of bubbles are drawn at full resolution. Stops when hidden/inactive or in Lite mode."""

    LAYOUT = ((0.18, 0.22, 0.50, 0.00021), (0.82, 0.18, 0.42, 0.00029), (0.72, 0.82, 0.55, 0.00017),
              (0.14, 0.80, 0.38, 0.00025), (0.50, 0.50, 0.30, 0.00033), (0.92, 0.55, 0.28, 0.00023))
    SCALE = 5

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from .liquid import goo, physics
        self._goo, self.theme = goo, theme
        self.field = physics.BubbleField(9)
        self._t = 0.0
        self._wall = None
        self._wall_scaled = None
        self._cache = None
        self._timer = QTimer(self)
        self._timer.setInterval(66)
        self._timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.reload_wallpaper()

    def reload_wallpaper(self) -> None:
        from PyQt5.QtGui import QPixmap
        pm = QPixmap(self.theme.wallpaper) if self.theme.wallpaper else None
        self._wall = pm if pm is not None and not pm.isNull() else None
        self._wall_scaled = None
        self.update()

    def start(self) -> None:
        if not self.theme.lite and not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        self._t += 66
        self.field.step(0.066)
        self.update()

    def try_pop(self, pos) -> bool:
        """Pop the bubble under ``pos`` (window coordinates). Returns True if one was hit."""
        w, h = self.width(), self.height()
        for i, b in enumerate(self.field.items):
            x, y = self.field.position(b, w, h)
            if (pos.x() - x) ** 2 + (pos.y() - y) ** 2 <= (b.r + 8) ** 2:
                self.field.items[i] = self.field._new()
                if self.theme.fx is not None:
                    self.theme.fx.pop_at(float(x), float(y))
                return True
        return False

    def _render_blobs(self, w: int, h: int) -> None:
        from PyQt5.QtGui import QImage
        sw, sh = max(2, w // self.SCALE), max(2, h // self.SCALE)
        if self._cache is None or self._cache.width() != sw or self._cache.height() != sh:
            self._cache = QImage(sw, sh, QImage.Format_ARGB32_Premultiplied)
        self._cache.fill(Qt.transparent)
        q = QPainter(self._cache)
        q.setRenderHint(QPainter.Antialiasing)
        q.scale(sw / float(w), sh / float(h))
        strength = 120 if self.theme.dark else 85
        blobs = list(self.theme.t["blobs"])
        t = self._t / 1000.0
        for i, (x, y, r, speed) in enumerate(self.LAYOUT):
            col = blobs[i % len(blobs)]
            k = speed * 1000.0
            cx = (x + 0.11 * math.sin(t * k * 0.9 + x * 9)) * w
            cy = (y + 0.11 * math.cos(t * k * 1.2 + y * 7)) * h
            rad = r * max(w, h) * 0.62
            pts = self._goo.blob_outline(cx, cy, rad, t * (0.5 + i * 0.13), amp=0.13, n=24, squash=0.06 * math.sin(t * 0.7 + i))
            g = QRadialGradient(QPointF(cx, cy), rad * 1.25)
            g.setColorAt(0, qcolor(col, strength)); g.setColorAt(0.65, qcolor(col, int(strength * 0.55))); g.setColorAt(1, qcolor(col, 0))
            path = QPainterPath(QPointF(*pts[0]))
            for pt in pts[1:]:
                path.lineTo(QPointF(*pt))
            path.closeSubpath()
            q.setPen(Qt.NoPen); q.setBrush(QBrush(g)); q.drawPath(path)
        q.end()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        w, h = self.width(), self.height()
        if w < 4 or h < 4:
            return
        bg = str(self.theme.t["bg"])
        p.fillRect(self.rect(), qcolor(bg))
        if self._wall is not None:
            if self._wall_scaled is None or self._wall_scaled.size() != self.size():
                self._wall_scaled = self._wall.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.drawPixmap((w - self._wall_scaled.width()) // 2, (h - self._wall_scaled.height()) // 2, self._wall_scaled)
            p.fillRect(self.rect(), qcolor(bg, 150))
        self._render_blobs(w, h)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.drawImage(self.rect(), self._cache)
        if self.theme.lite:
            return
        p.setRenderHint(QPainter.Antialiasing)
        a = 0.9 if self.theme.dark else 0.7
        for b in self.field.items:                                      # soap bubbles
            x, y = self.field.position(b, w, h)
            p.setBrush(qcolor("#FFFFFF", int(14 * a))); p.setPen(QPen(qcolor("#FFFFFF", int(90 * a)), 1.2))
            p.drawEllipse(QPointF(x, y), b.r, b.r)
            p.setPen(Qt.NoPen); p.setBrush(qcolor("#FFFFFF", int(150 * a)))
            p.drawEllipse(QPointF(x - b.r * 0.35, y - b.r * 0.38), b.r * 0.2, b.r * 0.14)


class GlassCard(QFrame):
    """Translucent jelly card: wobbles when you touch it, a soft light follows the cursor, a bright specular edge on top."""

    def __init__(self, theme: Theme, radius: int = 22, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from .liquid.physics import Spring
        self.theme, self.radius = theme, radius
        self._spring = Spring(0.0, 0.0, stiffness=260.0, damping=11.0)
        self._light: Optional[QPointF] = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(16)
        self._tick_timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WA_Hover, True)
        self.setMouseTracking(True)

    def _tick(self) -> None:
        self._spring.step(0.016)
        self.update()
        if self._spring.settled:
            self._tick_timer.stop()

    def _wobble(self, impulse: float) -> None:
        if self.theme.lite:
            return
        self._spring.kick(impulse)
        if not self._tick_timer.isActive():
            self._tick_timer.start()

    def enterEvent(self, e) -> None:  # noqa: N802
        self._wobble(5.5); super().enterEvent(e)

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._light = None; self._wobble(-3.0); self.update(); super().leaveEvent(e)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if not self.theme.lite:
            self._light = QPointF(e.pos()); self.update()
        super().mouseMoveEvent(e)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = max(-3.0, min(3.0, self._spring.value))                 # jelly inflation in px
        r = QRectF(self.rect()).adjusted(3 - w, 3 - w, -3 + w, -3 + w)
        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        t = self.theme.t
        alpha = int(str(t["glass_a"]), 16)
        for i, a in enumerate((12, 8, 4)):                          # soft shadow rings
            p.setPen(QPen(QColor(0, 0, 0, a), 1)); p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(-i - 1, -i - 1 + 2, i + 1, i + 1 + 2), self.radius + i, self.radius + i)
        fill = QLinearGradient(r.topLeft(), r.bottomRight())
        fill.setColorAt(0, qcolor(str(t["glass"]), min(255, alpha + 16))); fill.setColorAt(1, qcolor(str(t["glass"]), max(0, alpha - 8)))
        p.fillPath(path, QBrush(fill))
        p.setClipPath(path)
        if self._light is not None:                                 # cursor-following light
            g = QRadialGradient(self._light, max(r.width(), r.height()) * 0.55)
            g.setColorAt(0, qcolor(self.theme.accents[1], 46 if self.theme.dark else 36)); g.setColorAt(1, qcolor(self.theme.accents[1], 0))
            p.fillRect(r, QBrush(g))
        spec = QLinearGradient(r.topLeft(), QPointF(r.left(), r.top() + 40))
        spec.setColorAt(0, qcolor("#FFFFFF", 46)); spec.setColorAt(1, qcolor("#FFFFFF", 0))
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 40), QBrush(spec))
        p.setClipping(False)
        p.setPen(QPen(qcolor("#FFFFFF", 70 + (30 if self._light is not None else 0)), 1)); p.setBrush(Qt.NoBrush)
        p.drawPath(path)


class GlassButton(QPushButton):
    """Liquid pill button. Its size hint is computed from the (bold) text + icon so the label can never be bigger than the button; if the layout
    squeezes it, the text is elided with an ellipsis. A wet fill grows from the cursor, it squishes on press, bubbles burst on click (with sound)."""

    def __init__(self, text: str, theme: Theme, primary: bool = False, parent: Optional[QWidget] = None, icon: Optional[str] = None, danger: bool = False) -> None:
        super().__init__(text, parent)
        from .liquid.physics import Spring
        self.theme, self.primary, self.icon_name, self.danger = theme, primary, icon, danger
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setAttribute(Qt.WA_Hover, True)
        self.setMouseTracking(True)
        self._hover = Spring(0.0, 0.0, stiffness=170.0, damping=15.0)
        self._press = Spring(0.0, 0.0, stiffness=300.0, damping=12.0)
        self._center = QPointF(0, 0)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    # ---- sizing: the fix for "text bigger than the button"
    def _metrics(self):
        from PyQt5.QtGui import QFontMetrics
        f = QFont(self.font()); f.setBold(True)
        return f, QFontMetrics(f)

    def _text_width(self, fm, text: str) -> int:
        return fm.horizontalAdvance(text) if hasattr(fm, "horizontalAdvance") else fm.width(text)

    def sizeHint(self):  # noqa: N802
        from PyQt5.QtCore import QSize
        _f, fm = self._metrics()
        t = self.text()
        iw = (18 + (8 if t else 0)) if self.icon_name else 0
        return QSize(max(44, self._text_width(fm, t) + iw + 40), max(40, fm.height() + 22))

    def minimumSizeHint(self):  # noqa: N802
        from PyQt5.QtCore import QSize
        return QSize(44 if (not self.text() or self.icon_name) else 72, 40)

    def _go(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self) -> None:
        self._hover.step(0.016); self._press.step(0.016); self.update()
        if self._hover.settled and self._press.settled:
            self._timer.stop()

    def enterEvent(self, e) -> None:  # noqa: N802
        self._center = QPointF(e.pos()); self._hover.target = 1.0; self._go(); super().enterEvent(e)

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._hover.target = 0.0; self._go(); super().leaveEvent(e)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        self._center = QPointF(e.pos()); self.update(); super().mouseMoveEvent(e)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._press.target = 1.0; self._go()
        fx = self.theme.fx
        if fx is not None:
            fx.splash_at(self, e.pos(), 0.55, "bloop" if self.primary else "click")
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._press.target = 0.0; self._press.kick(-6.0); self._go(); super().mouseReleaseEvent(e)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sq = 1.0 - 0.05 * max(-0.4, min(1.4, self._press.value)) + 0.015 * self._hover.value
        c = QPointF(self.width() / 2, self.height() / 2)
        p.translate(c); p.scale(sq, 1.0 / (0.5 + 0.5 * sq)); p.translate(-c)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(r, r.height() / 2, r.height() / 2)
        a0, a1 = self.theme.accents[0], self.theme.accents[1]
        hv = max(0.0, min(1.2, self._hover.value))
        if self.danger:
            p.fillPath(path, qcolor("#E5626F", 215 if hv > 0.3 else 185))
        elif self.primary:
            g = QLinearGradient(r.topLeft(), r.topRight())                 # two neighbouring palette colours, never a rainbow
            g.setColorAt(0, qcolor(a0, 235)); g.setColorAt(1, qcolor(a1, 235))
            p.fillPath(path, QBrush(g))
        else:
            p.fillPath(path, qcolor("#FFFFFF", 26 if self.theme.dark else 150))
        if hv > 0.01:                                                      # liquid fill spreading from the cursor
            p.save(); p.setClipPath(path)
            g = QRadialGradient(self._center, hv * max(r.width(), r.height()) * 1.05)
            g.setColorAt(0, qcolor("#FFFFFF" if self.primary else a1, 110 if self.primary else 90)); g.setColorAt(1, qcolor("#FFFFFF", 0))
            p.fillRect(r, QBrush(g)); p.restore()
        hl = QLinearGradient(r.topLeft(), QPointF(r.left(), r.top() + r.height() * 0.55))
        hl.setColorAt(0, qcolor("#FFFFFF", 60)); hl.setColorAt(1, qcolor("#FFFFFF", 0))
        p.save(); p.setClipPath(path); p.fillRect(r, QBrush(hl)); p.restore()
        p.setPen(QPen(qcolor("#FFFFFF" if self.theme.dark else "#6A6A90", 70), 1)); p.setBrush(Qt.NoBrush); p.drawPath(path)
        col = QColor("#FFFFFF") if (self.primary or self.danger) else self.theme.text()
        f, fm = self._metrics()
        p.setFont(f)
        text = self.text()
        isz = 18.0
        pad = 20.0
        avail = max(0.0, self.width() - 2 * pad - ((isz + 8) if (self.icon_name and text) else (isz if self.icon_name else 0)))
        text = fm.elidedText(text, Qt.ElideRight, int(avail)) if text else ""
        tw = self._text_width(fm, text)
        total = tw + ((isz + (8 if text else 0)) if self.icon_name else 0)
        x0 = (self.width() - total) / 2
        rtl = self.layoutDirection() == Qt.RightToLeft
        if self.icon_name:
            from . import icons
            ix = x0 + (total - isz if (rtl and text) else 0)
            icons.draw(self.icon_name, p, QRectF(ix, (self.height() - isz) / 2, isz, isz), col, 2.0)
        if text:
            tx = x0 + (0 if (rtl or not self.icon_name) else isz + 8)
            p.setPen(col)
            p.drawText(QRectF(tx, 0, tw + 4, self.height()), Qt.AlignVCenter | Qt.AlignLeft, text)


class Heatmap(QWidget):
    """GitHub-style year heatmap (weeks as columns, Saturday-first like the Persian week)."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.levels: Dict[dt.date, int] = {}
        self.start: Optional[dt.date] = None
        self.days = 365
        self.hover: Optional[Tuple[dt.date, QRectF]] = None
        self.setMouseTracking(True)
        self.setMinimumHeight(130)

    def set_data(self, start: dt.date, days: int, levels: Dict[dt.date, int]) -> None:
        self.start, self.days, self.levels = start, days, levels
        self.update()

    def _cell(self, i: int, off: int) -> QRectF:
        size = max(6.0, min(18.0, (self.width() - 8) / (self.days / 7 + 2)))
        col, row = divmod(i + off, 7)
        if self.layoutDirection() == Qt.RightToLeft:
            cols = int((self.days + 6) // 7) + 2
            col = cols - 1 - col
        return QRectF(4 + col * size, 4 + row * size, size - 3, size - 3)

    def paintEvent(self, _event) -> None:  # noqa: N802
        if self.start is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        off = (self.start.weekday() + 2) % 7  # Saturday = 0
        for i in range(self.days):
            d = self.start + dt.timedelta(days=i)
            r = self._cell(i, off)
            lv = self.levels.get(d, 0)
            col = qcolor("#FFFFFF", 22) if lv == 0 else qcolor(self.theme.accents[0] if lv < 3 else self.theme.accents[1], 70 + lv * 45)
            p.setBrush(QBrush(col))
            p.setPen(qcolor("#FFFFFF", 90) if self.hover and self.hover[0] == d else Qt.NoPen)
            p.drawRoundedRect(r, 3, 3)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self.start is None:
            return
        off = (self.start.weekday() + 2) % 7
        for i in range(self.days):
            r = self._cell(i, off)
            if r.contains(e.pos()):
                d = self.start + dt.timedelta(days=i)
                self.hover = (d, r)
                self.setToolTip(f"{d.isoformat()}  ·  level {self.levels.get(d, 0)}")
                self.update()
                return
        self.hover = None


class Donut(QWidget):
    """Animated donut chart of {label: seconds}."""

    PALETTE = ("#6D5DFC", "#00E5FF", "#FF3D71", "#FFB020", "#2ED573", "#C56CF0", "#7EFFF5", "#FF9F43")

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.data: List[Tuple[str, int]] = []
        self._k = 1.0
        self.setMinimumSize(170, 170)

    def _g(self) -> float:
        return self._k

    def _s(self, v: float) -> None:
        self._k = v
        self.update()

    progress = pyqtProperty(float, _g, _s)

    def set_data(self, d: Dict[str, int]) -> None:
        items = sorted(d.items(), key=lambda kv: -kv[1])
        top, rest = items[:7], sum(v for _, v in items[7:])
        self.data = top + ([("…", rest)] if rest else [])
        if not self.theme.lite:
            a = QPropertyAnimation(self, b"progress", self)
            a.setDuration(700); a.setStartValue(0.0); a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.OutCubic)
            a.start(QPropertyAnimation.DeleteWhenStopped)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 16
        r = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        total = sum(v for _, v in self.data)
        if total <= 0:
            p.setPen(self.theme.text(True)); p.drawText(self.rect(), Qt.AlignCenter, "—")
            return
        pen_w = side * 0.14
        a0 = 90 * 16
        for i, (_, v) in enumerate(self.data):
            span = int(-v / total * 360 * 16 * self._k)
            p.setPen(QPen(qcolor(self.theme.chart_colors()[i % 8], 225), pen_w, Qt.SolidLine, Qt.FlatCap))
            p.drawArc(r.adjusted(pen_w, pen_w, -pen_w, -pen_w), a0, span)
            a0 += span


class BarChart(QWidget):
    """Compact gradient bar chart (e.g. 12 Jalali months)."""

    def __init__(self, theme: Theme, labels: Sequence[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme, self.labels = theme, list(labels)
        self.values: List[float] = [0.0] * len(labels)
        self.setMinimumHeight(140)

    def set_values(self, v: Sequence[float]) -> None:
        self.values = list(v)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        n = max(1, len(self.values))
        mx = max(self.values) if any(self.values) else 1
        bw = self.width() / n
        base = self.height() - 22
        rtl = self.layoutDirection() == Qt.RightToLeft
        for i, v in enumerate(self.values):
            h = (v / mx) * (base - 8)
            xi = (n - 1 - i) if rtl else i
            r = QRectF(xi * bw + bw * 0.18, base - h, bw * 0.64, max(2.0, h))
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, qcolor(self.theme.accents[1], 230)); g.setColorAt(1, qcolor(self.theme.accents[0], 200))
            p.setBrush(QBrush(g)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 6, 6)
            p.setPen(self.theme.text(True))
            f = QFont(self.font()); f.setPointSize(7); p.setFont(f)
            p.drawText(QRectF(xi * bw, base + 4, bw, 16), Qt.AlignCenter, self.labels[i])


class PomodoroOrb(QWidget):
    """A glass sphere of water. The water level shows the time left, two layered waves roll across it, bubbles rise inside, a thin glowing ring
    shows progress and a highlight sits on the glass. Animates (~30 fps) only while a phase runs and the widget is visible."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        import random
        self.theme = theme
        self.level, self.text, self.phase, self.sub = 0.0, "25:00", "idle", ""
        self._t = 0.0
        self._rnd = random.Random(7)
        self._bub = [[self._rnd.random(), self._rnd.random(), 2 + self._rnd.random() * 4, 0.05 + self._rnd.random() * 0.12] for _ in range(9)]
        self._timer = QTimer(self); self._timer.setInterval(33); self._timer.timeout.connect(self._anim)
        self.setMinimumSize(220, 220)

    def set_state(self, level: float, text: str, phase: str, sub: str = "") -> None:
        self.level, self.text, self.phase, self.sub = max(0.0, min(1.0, level)), text, phase, sub
        if phase != "idle" and self.isVisible() and not self.theme.lite:
            if not self._timer.isActive():
                self._timer.start()
        elif self._timer.isActive():
            self._timer.stop()
        self.update()

    def showEvent(self, e) -> None:  # noqa: N802
        if self.phase != "idle" and not self.theme.lite:
            self._timer.start()
        super().showEvent(e)

    def hideEvent(self, e) -> None:  # noqa: N802
        self._timer.stop(); super().hideEvent(e)

    def _anim(self) -> None:
        self._t += 0.033
        for b in self._bub:
            b[1] -= b[3] * 0.033 * 3.0
            if b[1] < -0.05:
                b[0], b[1] = self._rnd.random(), 1.05
        self.update()

    def _color(self) -> str:
        a = self.theme.accents
        return {"work": a[0], "short_break": a[2], "long_break": a[1]}.get(self.phase, str(self.theme.t["muted"]))

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 26
        r = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        col = self._color()
        idle = self.phase == "idle"
        # glow + progress ring
        ring = r.adjusted(-8, -8, 8, 8)
        p.setPen(QPen(qcolor("#FFFFFF", 22 if self.theme.dark else 70), 5)); p.setBrush(Qt.NoBrush); p.drawEllipse(ring)
        if not idle:
            for wdt, al in ((13, 28), (8, 60), (4, 230)):
                p.setPen(QPen(qcolor(col, al), wdt, Qt.SolidLine, Qt.RoundCap)); p.drawArc(ring, 90 * 16, int(-(1.0 - self.level) * 360 * 16) or -16)
        # sphere
        clip = QPainterPath(); clip.addEllipse(r)
        base = QRadialGradient(QPointF(r.center().x() - r.width() * 0.2, r.top() + r.height() * 0.2), r.width() * 0.9)
        base.setColorAt(0, qcolor("#FFFFFF", 54 if self.theme.dark else 190)); base.setColorAt(1, qcolor("#FFFFFF", 12 if self.theme.dark else 70))
        p.fillPath(clip, QBrush(base))
        # water
        p.save(); p.setClipPath(clip)
        lvl = 0.22 if idle else max(0.04, self.level)
        top = r.bottom() - r.height() * lvl
        for amp, spd, ph, al, tint in ((7.0, 1.4, 0.0, 120, col), (5.0, -1.9, 1.7, 150, self.theme.accents[1])):
            wave = QPainterPath(); wave.moveTo(r.left(), r.bottom()); wave.lineTo(r.left(), top)
            steps = 36
            for i in range(steps + 1):
                x = r.left() + r.width() * i / steps
                wave.lineTo(x, top + math.sin(i / 3.4 + self._t * spd + ph) * amp * (0.5 if self.theme.lite else 1.0))
            wave.lineTo(r.right(), r.bottom()); wave.closeSubpath()
            g = QLinearGradient(r.topLeft(), r.bottomLeft()); g.setColorAt(0, qcolor(tint, al)); g.setColorAt(1, qcolor(tint, int(al * 0.55)))
            p.fillPath(wave, QBrush(g))
        if not idle and not self.theme.lite:
            p.setPen(QPen(qcolor("#FFFFFF", 150), 1.1)); p.setBrush(qcolor("#FFFFFF", 28))
            for bx, by, br, _s in self._bub:
                y = r.top() + r.height() * by
                if y > top:
                    p.drawEllipse(QPointF(r.left() + r.width() * (0.12 + 0.76 * bx), y), br, br)
        p.restore()
        # glass: rim + highlights
        p.setPen(QPen(qcolor("#FFFFFF", 90 if self.theme.dark else 150), 1.6)); p.setBrush(Qt.NoBrush); p.drawEllipse(r)
        p.setPen(QPen(qcolor("#FFFFFF", 170), 3.2, Qt.SolidLine, Qt.RoundCap)); p.drawArc(r.adjusted(14, 14, -14, -14), 112 * 16, 36 * 16)
        p.setPen(Qt.NoPen); p.setBrush(qcolor("#FFFFFF", 150)); p.drawEllipse(QPointF(r.left() + r.width() * 0.26, r.top() + r.height() * 0.2), 4.2, 2.8)
        # text
        f = QFont(self.font()); f.setBold(True); f.setPointSizeF(max(14.0, side / 8.2)); p.setFont(f)
        p.setPen(self.theme.text() if not (self.theme.dark is False and lvl > 0.5) else QColor("#FFFFFF"))
        p.drawText(QRectF(r.left(), r.center().y() - r.height() * 0.17, r.width(), r.height() * 0.3), Qt.AlignCenter, self.text)
        if self.sub:
            f2 = QFont(self.font()); f2.setPointSizeF(max(8.0, side / 20)); p.setFont(f2); p.setPen(self.theme.text(True))
            p.drawText(QRectF(r.left(), r.center().y() + r.height() * 0.1, r.width(), r.height() * 0.15), Qt.AlignCenter, self.sub)


class Toast(QFrame):
    """Liquid-drop notification: slides down from the top edge of its parent, then fades away."""

    ACTIVE: List["Toast"] = []

    def __init__(self, parent: QWidget, theme: Theme, text: str) -> None:
        super().__init__(parent)
        from PyQt5.QtWidgets import QLabel, QHBoxLayout
        self.theme = theme
        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 12, 22, 12)
        lab = QLabel(text)
        lab.setStyleSheet(f"color:{theme.text().name()};background:transparent;font-size:11pt;")
        lay.addWidget(lab)
        self.adjustSize()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, r.height() / 2, r.height() / 2)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, qcolor(self.theme.accents[0], 120))
        g.setColorAt(1, qcolor(self.theme.accents[1], 120))
        p.fillPath(path, qcolor(str(self.theme.t["bg"]), 215))
        p.fillPath(path, QBrush(g))
        p.setPen(QPen(qcolor("#FFFFFF", 90), 1))
        p.drawPath(path)

    @classmethod
    def show_message(cls, parent: QWidget, theme: Theme, text: str, ms: int = 3200) -> "Toast":
        t = cls(parent, theme, text)
        if theme.fx is not None:
            theme.fx.play("drop_in")
        x = max(8, (parent.width() - t.width()) // 2)
        t.move(x, -t.height())
        t.show()
        t.raise_()
        cls.ACTIVE.append(t)
        slide = QPropertyAnimation(t, b"pos", t)
        slide.setDuration(0 if theme.lite else 450)
        slide.setEndValue(type(t.pos())(x, 16))
        slide.setEasingCurve(QEasingCurve.OutBack)         # springy overshoot = "drop" feel
        slide.start()
        t._slide = slide

        def done() -> None:
            if t in cls.ACTIVE:
                cls.ACTIVE.remove(t)
            t.close()
            t.deleteLater()
        QTimer.singleShot(ms, done)
        return t


# ---------------------------------------------------------------- project-management visuals
class GanttWidget(QWidget):
    """Horizontal liquid bars on a day axis. rows: [(title, start_date, end_date, done)], links: [(row_i, row_j)] (i must finish before j)."""

    ROW_H, LABEL_W = 30, 150

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.rows: List[Tuple[str, dt.date, dt.date, bool]] = []
        self.links: List[Tuple[int, int]] = []
        self.setMinimumHeight(120)

    def set_data(self, rows, links) -> None:
        self.rows, self.links = list(rows), list(links)
        self.setMinimumHeight(40 + self.ROW_H * max(1, len(self.rows)))
        self.update()

    def _x(self, d: dt.date, lo: dt.date, span: int) -> float:
        return self.LABEL_W + (self.width() - self.LABEL_W - 12) * ((d - lo).days / span)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.rows:
            p.setPen(self.theme.text(True))
            p.drawText(self.rect(), Qt.AlignCenter, "—")
            return
        lo = min(r[1] for r in self.rows)
        hi = max(r[2] for r in self.rows) + dt.timedelta(days=1)
        span = max(1, (hi - lo).days)
        f = QFont(self.font()); f.setPointSize(8); p.setFont(f)
        for i, (title, s, e, done) in enumerate(self.rows):
            y = 8 + i * self.ROW_H
            p.setPen(self.theme.text(True))
            p.drawText(QRectF(4, y, self.LABEL_W - 8, self.ROW_H - 6), Qt.AlignVCenter | Qt.AlignLeft, title[:22])
            x1, x2 = self._x(s, lo, span), self._x(e + dt.timedelta(days=1), lo, span)
            r = QRectF(x1, y + 3, max(6.0, x2 - x1), self.ROW_H - 12)
            g = QLinearGradient(r.topLeft(), r.topRight())
            a0, a1 = (self.theme.accents[0], self.theme.accents[1]) if not done else ("#2ED573", "#7EFFB2")
            g.setColorAt(0, qcolor(a0, 210)); g.setColorAt(1, qcolor(a1, 210))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(g))
            p.drawRoundedRect(r, 7, 7)
        p.setPen(QPen(qcolor("#FFFFFF", 110), 1.2))
        for i, j in self.links:                      # dependency arrows: end of i -> start of j
            if i < len(self.rows) and j < len(self.rows):
                xa = self._x(self.rows[i][2] + dt.timedelta(days=1), lo, span)
                xb = self._x(self.rows[j][1], lo, span)
                ya, yb = 8 + i * self.ROW_H + self.ROW_H / 2 - 3, 8 + j * self.ROW_H + self.ROW_H / 2 - 3
                path = QPainterPath(QPointF(xa, ya))
                path.cubicTo(QPointF(xa + 14, ya), QPointF(xb - 14, yb), QPointF(xb, yb))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)


class Ring(QWidget):
    """Progress ring (milestones, goals)."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme, self.value, self.text = theme, 0.0, ""
        self.setMinimumSize(96, 96)

    def set_value(self, v: float, text: str = "") -> None:
        self.value, self.text = max(0.0, min(1.0, v)), text
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 14
        r = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        w = side * 0.13
        rr = r.adjusted(w / 2, w / 2, -w / 2, -w / 2)
        p.setPen(QPen(qcolor("#FFFFFF", 36), w, Qt.SolidLine, Qt.FlatCap))
        p.drawEllipse(rr)
        p.setPen(QPen(qcolor(self.theme.accents[1], 235), w, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rr, 90 * 16, int(-self.value * 360 * 16))
        p.setPen(self.theme.text())
        p.drawText(r, Qt.AlignCenter, self.text or f"{int(self.value * 100)}%")


class SankeyWidget(QWidget):
    """Two-column Sankey: left nodes (projects) -> right nodes (categories) with curved ribbons sized by hours."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.links: List[Dict[str, object]] = []
        self.setMinimumHeight(200)

    def set_links(self, links: List[Dict[str, object]]) -> None:
        self.links = list(links)[:24]
        self.update()

    @staticmethod
    def layout_nodes(totals: Dict[str, float], height: float, gap: float = 6.0) -> Dict[str, Tuple[float, float]]:
        """Stack nodes vertically; returns name -> (y, h). Pure function (unit-tested)."""
        total = sum(totals.values()) or 1.0
        avail = max(1.0, height - gap * max(0, len(totals) - 1))
        out, y = {}, 0.0
        for name, v in totals.items():
            h = avail * v / total
            out[name] = (y, h)
            y += h + gap
        return out

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self.links:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        left: Dict[str, float] = {}
        right: Dict[str, float] = {}
        for l in self.links:
            left[str(l["source"])] = left.get(str(l["source"]), 0) + float(l["hours"])
            right[str(l["target"])] = right.get(str(l["target"]), 0) + float(l["hours"])
        H = self.height() - 8
        ln, rn = self.layout_nodes(left, H), self.layout_nodes(right, H)
        x0, x1, bar = 110.0, self.width() - 110.0, 10.0
        lcur = {k: v[0] for k, v in ln.items()}
        rcur = {k: v[0] for k, v in rn.items()}
        pal = self.theme.chart_colors()
        names = list(left)
        f = QFont(self.font()); f.setPointSize(8); p.setFont(f)
        for l in self.links:
            s, t, h = str(l["source"]), str(l["target"]), float(l["hours"])
            hs = ln[s][1] * h / left[s]
            ht = rn[t][1] * h / right[t]
            ys, yt = lcur[s] + 4, rcur[t] + 4
            lcur[s] += hs; rcur[t] += ht
            path = QPainterPath(QPointF(x0 + bar, ys))
            mid = (x0 + x1) / 2
            path.cubicTo(QPointF(mid, ys), QPointF(mid, yt), QPointF(x1, yt))
            path.lineTo(QPointF(x1, yt + ht))
            path.cubicTo(QPointF(mid, yt + ht), QPointF(mid, ys + hs), QPointF(x0 + bar, ys + hs))
            path.closeSubpath()
            p.fillPath(path, qcolor(pal[names.index(s) % len(pal)], 120))
        p.setPen(self.theme.text())
        for k, (y, h) in ln.items():
            p.fillRect(QRectF(x0, y + 4, bar, max(2.0, h)), qcolor(pal[names.index(k) % len(pal)], 230))
            p.drawText(QRectF(2, y + 4, x0 - 6, max(14.0, h)), Qt.AlignVCenter | Qt.AlignRight, k[:16])
        for k, (y, h) in rn.items():
            p.fillRect(QRectF(x1, y + 4, bar, max(2.0, h)), qcolor("#FFFFFF", 150))
            p.drawText(QRectF(x1 + bar + 4, y + 4, 100, max(14.0, h)), Qt.AlignVCenter | Qt.AlignLeft, k[:14])


def make_icon(text: str, color: str):
    """Dynamic tray icon: coloured disc with up to 3 characters (e.g. elapsed minutes)."""
    from PyQt5.QtGui import QIcon, QPixmap
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(qcolor(color)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(1, 1, 30, 30)
    p.setPen(QColor("#FFFFFF"))
    f = QFont()
    f.setBold(True)
    f.setPixelSize(13 if len(text) <= 2 else 10)
    p.setFont(f)
    p.drawText(QRectF(0, 0, 32, 32), Qt.AlignCenter, text[:3])
    p.end()
    return QIcon(pm)


class LiquidSwitch(QWidget):
    """Toggle with a gooey knob: stretches while travelling, settles with a little overshoot, glass track that fills with the accent, check mark inside
    the knob when on. Same API as QCheckBox (isChecked / setChecked / toggled)."""

    from PyQt5.QtCore import pyqtSignal as _sig
    toggled = _sig(bool)

    def __init__(self, theme: Theme, checked: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from .liquid.physics import Spring
        self.theme, self._on = theme, checked
        self._pos = Spring(1.0 if checked else 0.0, 1.0 if checked else 0.0, stiffness=240.0, damping=13.0)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(58, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._hover = False

    def isChecked(self) -> bool:  # noqa: N802
        return self._on

    def setChecked(self, v: bool) -> None:  # noqa: N802
        if v != self._on:
            self._on = v; self._pos.target = 1.0 if v else 0.0; self._run()

    def _run(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self) -> None:
        self._pos.step(0.016); self.update()
        if self._pos.settled:
            self._timer.stop()

    def enterEvent(self, e) -> None:  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._on = not self._on
        self._pos.target = 1.0 if self._on else 0.0
        self._run()
        fx = self.theme.fx
        if fx is not None:
            fx.play("toggle_on" if self._on else "toggle_off"); fx.splash_at(self, QPointF(self._pos.target * 26 + 16, 16), 0.45, None)
        self.toggled.emit(self._on)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 4, -2, -4)
        k = max(0.0, min(1.0, self._pos.value))
        track = QPainterPath(); track.addRoundedRect(r, r.height() / 2, r.height() / 2)
        off = qcolor("#FFFFFF", 38) if self.theme.dark else qcolor("#7A7AA0", 70)
        p.fillPath(track, off)
        if k > 0.01:
            g = QLinearGradient(r.topLeft(), r.topRight())
            g.setColorAt(0, qcolor(self.theme.accents[0], int(235 * k))); g.setColorAt(1, qcolor(self.theme.accents[1], int(235 * k)))
            p.fillPath(track, QBrush(g))
        p.setPen(QPen(qcolor("#FFFFFF" if self.theme.dark else "#6A6A90", 75 if not self._hover else 130), 1)); p.setBrush(Qt.NoBrush); p.drawPath(track)
        stretch = min(9.0, abs(self._pos.vel) * 3.0)
        d = r.height() - 6 + (1.0 if self._hover else 0.0)
        x = r.left() + 3 + (r.width() - d - 6) * self._pos.value
        knob = QRectF(x - stretch / 2, r.top() + (r.height() - d) / 2, d + stretch, d)
        p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 55)); p.drawRoundedRect(knob.translated(0, 1.6), d / 2, d / 2)     # soft shadow
        p.setBrush(QColor("#FFFFFF")); p.drawRoundedRect(knob, d / 2, d / 2)
        if k > 0.55:
            from . import icons
            icons.draw("check", p, QRectF(knob.center().x() - 6, knob.center().y() - 6, 12, 12), qcolor(self.theme.accents[0]), 2.6)


class LiquidCheck(QCheckBox):
    """Rounded check box with an animated check mark (pops in with a spring). Drop-in for QCheckBox."""

    def __init__(self, text: str, theme: Theme, checked: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        from .liquid.physics import Spring
        self.theme = theme
        self.setChecked(checked)
        self._k = Spring(1.0 if checked else 0.0, 1.0 if checked else 0.0, stiffness=300.0, damping=12.0)
        self._timer = QTimer(self); self._timer.setInterval(16); self._timer.timeout.connect(self._tick)
        self.setCursor(Qt.PointingHandCursor)
        self.toggled.connect(self._changed)

    def _changed(self, on: bool) -> None:
        self._k.target = 1.0 if on else 0.0
        if not self._timer.isActive():
            self._timer.start()
        if self.theme.fx is not None:
            self.theme.fx.play("toggle_on" if on else "toggle_off", 0.6)

    def _tick(self) -> None:
        self._k.step(0.016); self.update()
        if self._k.settled:
            self._timer.stop()

    def sizeHint(self):  # noqa: N802
        from PyQt5.QtCore import QSize
        from PyQt5.QtGui import QFontMetrics
        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(self.text()) if hasattr(fm, "horizontalAdvance") else fm.width(self.text())
        return QSize(tw + 40, 30)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rtl = self.layoutDirection() == Qt.RightToLeft
        s = 22.0
        bx = self.width() - s - 2 if rtl else 2.0
        box = QRectF(bx, (self.height() - s) / 2, s, s)
        k = max(0.0, min(1.15, self._k.value))
        path = QPainterPath(); path.addRoundedRect(box, 7, 7)
        p.fillPath(path, qcolor("#FFFFFF", 30) if self.theme.dark else qcolor("#FFFFFF", 190))
        if k > 0.02:
            g = QLinearGradient(box.topLeft(), box.bottomRight())
            g.setColorAt(0, qcolor(self.theme.accents[0], int(min(1.0, k) * 240))); g.setColorAt(1, qcolor(self.theme.accents[1], int(min(1.0, k) * 240)))
            c = box.center(); p.save(); p.translate(c); p.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k); p.translate(-c); p.fillPath(path, QBrush(g)); p.restore()
        p.setPen(QPen(qcolor("#FFFFFF" if self.theme.dark else "#6A6A90", 90), 1)); p.setBrush(Qt.NoBrush); p.drawPath(path)
        if k > 0.1:
            from . import icons
            icons.draw("check", p, box.adjusted(4, 4, -4, -4), QColor("#FFFFFF"), 2.8)
        p.setPen(self.theme.text())
        tx = 0.0 if rtl else box.right() + 10
        w = self.width() - s - 14
        p.drawText(QRectF(tx, 0, w, self.height()), Qt.AlignVCenter | (Qt.AlignRight if rtl else Qt.AlignLeft), self.text())

