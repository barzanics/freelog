"""Effects hub: droplets that fall from the cursor while you drag, splashes, bubbles and the sound player.

Every widget talks to ``theme.fx`` (an :class:`FX`); if it is missing or disabled the call is a silent no-op, so widgets never crash
on a machine without audio or with effects turned off.
"""
from __future__ import annotations

import logging
import random
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QCursor, QPainter, QPen, QRadialGradient
from PyQt5.QtWidgets import QWidget

from . import physics, sounds

log = logging.getLogger("worktracker.fx")


class SoundPlayer:
    """Plays the procedurally generated UI sounds. Missing QtMultimedia / no audio device => silent, never an exception."""

    MIN_GAP = {"drip": 0.09, "bloop": 0.05, "click": 0.03}

    def __init__(self, folder: Path, enabled: bool = True, volume: float = 0.5) -> None:
        self.folder, self.enabled, self.volume = Path(folder), enabled, max(0.0, min(1.0, volume))
        self._fx: Dict[str, object] = {}
        self._last: Dict[str, float] = {}
        self._ok: Optional[bool] = None

    def _ensure(self) -> bool:
        if self._ok is not None:
            return self._ok
        try:
            from PyQt5.QtCore import QUrl
            from PyQt5.QtMultimedia import QSoundEffect
            self.folder.mkdir(parents=True, exist_ok=True)
            for kind, data in sounds.build_all().items():
                f = self.folder / f"{kind}.wav"
                if not f.exists() or f.stat().st_size != len(data):
                    f.write_bytes(data)
                e = QSoundEffect()
                e.setSource(QUrl.fromLocalFile(str(f)))
                self._fx[kind] = e
            self._ok = True
        except Exception:  # noqa: BLE001 - audio is optional
            log.info("sound disabled (QtMultimedia unavailable)", exc_info=True)
            self._ok = False
        return self._ok

    def play(self, kind: str, volume: float = 1.0) -> None:
        if not self.enabled or self.volume <= 0:
            return
        now = time.monotonic()
        if now - self._last.get(kind, 0.0) < self.MIN_GAP.get(kind, 0.02):
            return
        self._last[kind] = now
        if not self._ensure():
            return
        e = self._fx.get(kind)
        if e is not None:
            try:
                e.setVolume(max(0.0, min(1.0, self.volume * volume)))  # type: ignore[attr-defined]
                e.play()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                log.debug("play failed", exc_info=True)


class DripLayer(QWidget):
    """Transparent overlay above the whole window that draws and animates the particles. It only runs a timer while something moves."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.ps = physics.ParticleSystem(rng=random.Random(11))
        self.tint: Tuple[int, int, int] = (110, 200, 255)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._follow = QTimer(self)
        self._follow.setInterval(24)
        self._follow.timeout.connect(self._follow_cursor)
        self._last_pos: Optional[QPointF] = None
        self._last_t = time.monotonic()
        self.enabled = True
        self.raise_()

    # ---- public effects ---------------------------------------------------------
    def _local(self, global_pos) -> QPointF:
        return QPointF(self.mapFromGlobal(global_pos))

    def _kick(self) -> None:
        if self.enabled and not self._timer.isActive():
            self._last_t = time.monotonic()
            self._timer.start()
        self.raise_()

    def splash(self, x: float, y: float, strength: float = 1.0) -> None:
        if self.enabled:
            self.ps.splash(x, y, strength, self.tint); self.ps.bubbles(x, y, 4); self._kick()

    def pop(self, x: float, y: float) -> None:
        if self.enabled:
            self.ps.bubbles(x, y, 9, spread=30.0); self.ps.splash(x, y, 0.7, (190, 235, 255), n=10); self._kick()

    def drip(self, x: float, y: float, n: int = 1) -> None:
        if self.enabled:
            self.ps.drip(x, y, self.tint, n=n); self._kick()

    def start_following(self) -> None:
        """While a drag is running the cursor leaves a trail of drops (Qt delivers no mouse moves during QDrag, so we poll the cursor)."""
        if not self.enabled:
            return
        self._last_pos = None
        self._follow.start()
        self._kick()

    def stop_following(self) -> None:
        self._follow.stop()
        if self._last_pos is not None:
            self.splash(self._last_pos.x(), self._last_pos.y(), 1.1)       # land with a splash where you drop it
        self._last_pos = None

    def _follow_cursor(self) -> None:
        pos = self._local(QCursor.pos())
        now = time.monotonic()
        if self._last_pos is not None:
            dt_s = max(1e-3, now - self._last_t)
            vx, vy = (pos.x() - self._last_pos.x()) / dt_s, (pos.y() - self._last_pos.y()) / dt_s
            self.ps.trail(pos.x(), pos.y(), vx, vy, self.tint, chance=0.7)
            if abs(vx) + abs(vy) < 60 and random.random() < 0.18:           # hovering still: it drips, like a wet finger
                self.ps.drip(pos.x(), pos.y() + 6, self.tint, n=1)
        self._last_pos, self._last_t = pos, now
        self._kick()

    # ---- simulation + paint --------------------------------------------------------
    def _tick(self) -> None:
        now = time.monotonic()
        dt_s = min(0.05, now - self._last_t)
        self._last_t = now
        self.ps.step(dt_s, floor=self.height() + 40)
        self.update()
        if not self.ps.active and not self._follow.isActive():
            self._timer.stop()

    def paintEvent(self, _e) -> None:  # noqa: N802
        if not self.ps.items:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        for d in self.ps.items:
            a = d.alpha
            rx, ry, ang = d.shape()
            r, g, b = d.color
            p.save()
            p.translate(d.x, d.y)
            p.rotate(ang * 57.29578)
            if d.kind == "bubble":
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(QColor(255, 255, 255, int(170 * a)), 1.4))
                p.drawEllipse(QPointF(0, 0), rx, ry)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, int(190 * a)))
                p.drawEllipse(QPointF(-rx * 0.35, -ry * 0.35), max(1.0, rx * 0.22), max(1.0, ry * 0.22))
            else:
                grad = QRadialGradient(QPointF(-rx * 0.3, -ry * 0.3), max(rx, ry) * 1.4)
                grad.setColorAt(0.0, QColor(255, 255, 255, int(235 * a)))
                grad.setColorAt(0.35, QColor(r, g, b, int(215 * a)))
                grad.setColorAt(1.0, QColor(max(0, r - 50), max(0, g - 40), min(255, b), int(160 * a)))
                p.setBrush(QBrush(grad))
                p.drawEllipse(QPointF(0, 0), rx, ry)
            p.restore()


class FX:
    """What widgets call. Holds the sound player and the drip layer; both optional."""

    def __init__(self, layer: Optional[DripLayer], sound: Optional[SoundPlayer], lite: bool = False) -> None:
        self.layer, self.sound, self.lite = layer, sound, lite

    def _to_layer(self, widget: QWidget, pos) -> Tuple[float, float]:
        p = widget.mapTo(self.layer.parentWidget(), pos.toPoint() if hasattr(pos, "toPoint") else pos)
        return float(p.x()), float(p.y())

    def play(self, kind: str, volume: float = 1.0) -> None:
        if self.sound is not None:
            self.sound.play(kind, volume)

    def splash_at(self, widget: QWidget, pos, strength: float = 1.0, sound: Optional[str] = "bloop") -> None:
        if self.layer is not None and not self.lite:
            x, y = self._to_layer(widget, pos); self.layer.splash(x, y, strength)
        if sound:
            self.play(sound)

    def pop_at(self, x: float, y: float) -> None:
        if self.layer is not None and not self.lite:
            self.layer.pop(x, y)
        self.play("pop")

    def drag_started(self) -> None:
        self.play("bloop", 0.7)
        if self.layer is not None and not self.lite:
            self.layer.start_following()

    def drag_finished(self) -> None:
        if self.layer is not None:
            self.layer.stop_following()
        self.play("splash", 0.8)
