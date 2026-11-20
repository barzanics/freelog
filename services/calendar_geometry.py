"""Pure geometry for the calendar time grid (no Qt): snapping, overlap lanes (Google-Calendar style), hit zones for move / resize, drag-to-create ranges."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

DAY_MIN = 24 * 60


def snap(minutes: float, step: int = 15, lo: int = 0, hi: int = DAY_MIN) -> int:
    """Round to the nearest ``step`` minutes and keep inside [lo, hi]."""
    return int(max(lo, min(hi, round(minutes / step) * step)))


def y_to_minutes(y: float, hour_h: float, top: float = 0.0) -> float:
    return (y - top) / hour_h * 60.0


def minutes_to_y(minutes: float, hour_h: float, top: float = 0.0) -> float:
    return top + minutes / 60.0 * hour_h


def layout_lanes(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Give overlapping blocks side-by-side lanes. Each item needs ``start`` and ``end`` (minutes); returns copies with ``lane`` and ``lanes`` (how many lanes its cluster needs)."""
    out = [dict(i) for i in sorted(items, key=lambda i: (i["start"], -(i["end"] - i["start"])))]
    cluster: List[Dict[str, Any]] = []
    lane_ends: List[int] = []
    cluster_end = -1

    def close() -> None:
        for c in cluster:
            c["lanes"] = max(1, len(lane_ends))
    for it in out:
        if cluster and it["start"] >= cluster_end:
            close(); cluster, lane_ends, cluster_end = [], [], -1
        for k, end in enumerate(lane_ends):
            if it["start"] >= end:
                it["lane"], lane_ends[k] = k, it["end"]
                break
        else:
            it["lane"] = len(lane_ends); lane_ends.append(it["end"])
        cluster.append(it); cluster_end = max(cluster_end, it["end"])
    close()
    return out


def hit_zone(y: float, top: float, bottom: float, edge: float = 7.0) -> str:
    """Where inside a block the pointer is: 'top' / 'bottom' edge (resize) or 'body' (move). Tiny blocks are always 'body' so they can still be moved."""
    if bottom - top < edge * 3:
        return "body"
    if y <= top + edge:
        return "top"
    return "bottom" if y >= bottom - edge else "body"


def drag_range(y0: float, y1: float, hour_h: float, top: float = 0.0, step: int = 15, min_len: int = 15) -> Tuple[int, int]:
    """Start/end minutes of a drag-to-create selection (either direction); a plain click gets ``min_len`` minutes ... or 60 when it is a click."""
    a, b = sorted((y_to_minutes(y0, hour_h, top), y_to_minutes(y1, hour_h, top)))
    s = snap(a, step, 0, DAY_MIN - min_len)
    e = snap(b, step, s + min_len, DAY_MIN)
    if abs(y1 - y0) < 4:
        e = min(DAY_MIN, s + 60)
    return s, e


def move_resize(zone: str, start: int, end: int, delta: int, step: int = 15, min_len: int = 15) -> Tuple[int, int]:
    """New (start, end) minutes after dragging ``delta`` minutes in ``zone``; a move keeps the length and stays within the day, a resize keeps at least ``min_len``."""
    length = end - start
    if zone == "body":
        s = snap(start + delta, step, 0, DAY_MIN - length)
        return s, s + length
    if zone == "top":
        s = snap(start + delta, step, 0, end - min_len)
        return s, end
    e = snap(end + delta, step, start + min_len, DAY_MIN)
    return start, e
