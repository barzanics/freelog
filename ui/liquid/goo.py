"""Liquid geometry (pure math): metaball bridge between two circles, wobbling blobs, wave lines.

The bridge is the classic Hiroyuki Sato metaball construction; it returns cubic-Bezier control points so any painter can draw it.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

Pt = Tuple[float, float]


def _polar(c: Pt, r: float, a: float) -> Pt:
    return c[0] + r * math.cos(a), c[1] + r * math.sin(a)


def metaball(c1: Pt, r1: float, c2: Pt, r2: float, v: float = 0.5, handle: float = 2.4, reach: float = 2.5) -> Optional[Dict[str, Pt]]:
    """Bridge outline between two circles, or None when they are too far apart / one swallows the other.

    Returns points: p1a, p1b (on circle 1), p2a, p2b (circle 2) and handles h1..h4, ready for
    ``moveTo(p1a); cubicTo(h1, h2, p2a); lineTo(p2b); cubicTo(h3, h4, p1b); close``.
    """
    d = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
    if r1 <= 0 or r2 <= 0 or d > r1 + r2 * reach or d <= abs(r1 - r2) + 1e-6:
        return None
    u1 = u2 = 0.0
    if d < r1 + r2:
        u1 = math.acos(max(-1.0, min(1.0, (r1 * r1 + d * d - r2 * r2) / (2 * r1 * d))))
        u2 = math.acos(max(-1.0, min(1.0, (r2 * r2 + d * d - r1 * r1) / (2 * r2 * d))))
    base = math.atan2(c2[1] - c1[1], c2[0] - c1[0])
    a2 = math.acos(max(-1.0, min(1.0, (r1 - r2) / d)))
    a1a = base + u1 + (a2 - u1) * v
    a1b = base - u1 - (a2 - u1) * v
    a2a = base + math.pi - u2 - (math.pi - u2 - a2) * v
    a2b = base - math.pi + u2 + (math.pi - u2 - a2) * v
    p1a, p1b, p2a, p2b = _polar(c1, r1, a1a), _polar(c1, r1, a1b), _polar(c2, r2, a2a), _polar(c2, r2, a2b)
    total = r1 + r2
    d2 = min(v * handle, math.hypot(p1a[0] - p2a[0], p1a[1] - p2a[1]) / total)
    d2 *= min(1.0, d * 2 / total)
    hr1, hr2 = r1 * d2, r2 * d2
    h1 = _polar(p1a, hr1, a1a - math.pi / 2)
    h2 = _polar(p2a, hr2, a2a + math.pi / 2)
    h3 = _polar(p2b, hr2, a2b - math.pi / 2)
    h4 = _polar(p1b, hr1, a1b + math.pi / 2)
    return {"p1a": p1a, "p1b": p1b, "p2a": p2a, "p2b": p2b, "h1": h1, "h2": h2, "h3": h3, "h4": h4}


def bezier(p0: Pt, p1: Pt, p2: Pt, p3: Pt, n: int = 16) -> List[Pt]:
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                    mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def bridge_polygon(m: Dict[str, Pt], n: int = 16) -> List[Pt]:
    """Sampled outline of the bridge (for tests / raster previews)."""
    return bezier(m["p1a"], m["h1"], m["h2"], m["p2a"], n) + bezier(m["p2b"], m["h3"], m["h4"], m["p1b"], n)


def blob_outline(cx: float, cy: float, r: float, t: float, amp: float = 0.08, n: int = 40, squash: float = 0.0) -> List[Pt]:
    """Organic wobbling circle: radius modulated by 3 travelling sine harmonics. ``squash`` (-1..1) flattens/stretches vertically."""
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        k = 1 + amp * (0.55 * math.sin(2 * th + t * 1.7) + 0.3 * math.sin(3 * th - t * 1.1 + 1.3) + 0.15 * math.sin(5 * th + t * 2.3))
        pts.append((cx + r * k * math.cos(th) * (1 + 0.5 * squash), cy + r * k * math.sin(th) * (1 - 0.5 * squash)))
    return pts


def wave_line(x0: float, x1: float, y: float, amp: float, phase: float, wavelength: float = 90.0, n: int = 28) -> List[Pt]:
    """Water surface from x0 to x1 at height y (use with the container's bottom corners to make a fill polygon)."""
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        out.append((x, y + amp * math.sin((x - x0) / wavelength * 2 * math.pi + phase) + amp * 0.45 * math.sin((x - x0) / (wavelength * 0.57) * 2 * math.pi - phase * 1.4)))
    return out


def teardrop(r: float, n: int = 28) -> List[Pt]:
    """Hanging drop pointing up (tip at (0,-2.2r)); scale/rotate when drawing."""
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        s = math.sin(th / 2)
        k = (1 - math.cos(th)) / 2
        pts.append((r * math.sin(th) * (s ** 1.0) * 1.15, -r * math.cos(th) * (1 + 0.6 * k) - r * 0.0))
    return pts


def goo_indicator(y_head: float, y_tail: float, x: float, r: float) -> Tuple[Pt, float, Pt, float]:
    """Two circles (head leads, tail follows) for a sidebar indicator; the bridge between them forms the stretch."""
    shrink = max(0.55, 1 - abs(y_head - y_tail) / (r * 14))
    return (x, y_head), r, (x, y_tail), r * shrink
