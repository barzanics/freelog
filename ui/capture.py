"""Screen grabbing with Qt. Small by design: downscaled + JPEG, so an hourly shot costs ~60-150 KB (and is then zipped per day)."""
from __future__ import annotations

import logging
from typing import Optional, Tuple

log = logging.getLogger("worktracker.capture")


def grab_jpeg(max_width: int = 1280, quality: int = 45, grayscale: bool = False) -> Optional[Tuple[bytes, int, int]]:
    """Primary screen -> (jpeg_bytes, width, height), or None when no screen is available. Never raises."""
    try:
        from PyQt5.QtCore import QBuffer, QIODevice, Qt
        from PyQt5.QtGui import QGuiApplication, QImage
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        img = screen.grabWindow(0).toImage()
        if img.isNull():
            return None
        if img.width() > max_width:
            img = img.scaledToWidth(max_width, Qt.SmoothTransformation)
        if grayscale:
            img = img.convertToFormat(QImage.Format_Grayscale8)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        if not img.save(buf, "JPG", max(10, min(95, int(quality)))):
            return None
        return bytes(buf.data()), img.width(), img.height()
    except Exception:  # noqa: BLE001 - screenshots are optional
        log.info("screen capture failed", exc_info=True)
        return None


def grab_signature(w: int = 32, h: int = 18) -> Optional[bytes]:
    """A 32x18 grayscale thumbnail of the primary screen (576 bytes). Comparing two of them tells whether anything on screen changed - used to tell
    a frozen screen / mouse jiggler from a video call or a long read. ~10 ms; None when no screen can be grabbed."""
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QGuiApplication, QImage
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        img = screen.grabWindow(0).toImage()
        if img.isNull():
            return None
        img = img.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation).convertToFormat(QImage.Format_Grayscale8)
        ptr = img.constBits()
        ptr.setsize(img.byteCount())
        raw, bpl = bytes(ptr), img.bytesPerLine()
        return b"".join(raw[y * bpl:y * bpl + w] for y in range(h))
    except Exception:  # noqa: BLE001
        log.debug("signature grab failed", exc_info=True)
        return None


def signature_delta(a: Optional[bytes], b: Optional[bytes]) -> Optional[float]:
    """Mean absolute difference of two signatures, 0..1 (None if either is missing / sizes differ)."""
    if not a or not b or len(a) != len(b):
        return None
    return sum(abs(x - y) for x, y in zip(a, b)) / (255.0 * len(a))
