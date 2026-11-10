"""iCalendar (.ics) export. Pure text, RFC 5545 escaping and line folding."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

from ..core.models import TimeEntry
from ..core.persian import UTC, now_utc


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _fold(line: str) -> str:
    """Fold at 75 octets without splitting UTF-8 characters."""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > 75:
            out.append(cur); cur, size = " " + ch, n + 1
        else:
            cur += ch; size += n
    out.append(cur)
    return "\r\n".join(out)


def build_ics(entries: Iterable[TimeEntry]) -> str:
    fmt = "%Y%m%dT%H%M%SZ"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WorkTracker//6.0//EN", "CALSCALE:GREGORIAN"]
    for e in entries:
        if e.end_utc is None:
            continue
        lines += ["BEGIN:VEVENT", f"UID:{e.id}@worktracker", f"DTSTAMP:{now_utc():{fmt}}",
                  f"DTSTART:{e.start_utc.astimezone(UTC):{fmt}}", f"DTEND:{e.end_utc.astimezone(UTC):{fmt}}",
                  f"SUMMARY:{_esc(e.title)}"]
        if e.notes:
            lines.append(f"DESCRIPTION:{_esc(e.notes)}")
        if e.tags:
            lines.append(f"CATEGORIES:{','.join(_esc(t) for t in e.tags)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(l) for l in lines) + "\r\n"


def export_ics(entries: Iterable[TimeEntry], dest: Union[str, Path]) -> Path:
    dest = Path(dest)
    dest.write_text(build_ics(entries), encoding="utf-8", newline="")
    return dest
