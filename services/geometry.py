"""Pure geometry for the floating quick-access bubble (no Qt, so it is unit-tested)."""
from __future__ import annotations

from typing import Tuple

Rect = Tuple[int, int, int, int]       # x, y, width, height


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def snap_to_edge(x: int, y: int, w: int, h: int, screen: Rect, margin: int = 6) -> Tuple[int, int]:
    """After a drag the bubble glides to the nearest left/right screen edge (top/bottom are clamped)."""
    sx, sy, sw, sh = screen
    left = x + w / 2 < sx + sw / 2
    nx = sx + margin if left else sx + sw - w - margin
    ny = int(clamp(y, sy + margin, sy + sh - h - margin))
    return int(nx), ny


def keep_on_screen(x: int, y: int, w: int, h: int, screen: Rect) -> Tuple[int, int]:
    """Used on start-up: a saved position from a monitor that is gone must not leave the bubble invisible."""
    sx, sy, sw, sh = screen
    return int(clamp(x, sx, sx + sw - w)), int(clamp(y, sy, sy + sh - h))


def panel_position(bubble: Rect, panel_w: int, panel_h: int, screen: Rect, gap: int = 10) -> Tuple[int, int]:
    """Where the quick panel opens: beside the bubble, on the side that has room, vertically centred on it, never off screen."""
    bx, by, bw, bh = bubble
    sx, sy, sw, sh = screen
    on_left_half = bx + bw / 2 < sx + sw / 2
    x = bx + bw + gap if on_left_half else bx - panel_w - gap
    if x < sx or x + panel_w > sx + sw:                      # no room to the side: open above/below instead
        x = int(clamp(bx + bw / 2 - panel_w / 2, sx + 6, sx + sw - panel_w - 6))
        below = by + bh + gap + panel_h <= sy + sh
        y = by + bh + gap if below else by - panel_h - gap
    else:
        y = by + bh / 2 - panel_h / 2
    return int(x), int(clamp(y, sy + 6, sy + sh - panel_h - 6))
