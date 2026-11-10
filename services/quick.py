"""Quick capture grammar (one line, any order):

    fix login #bug #urgent @WebApp 45m          title + tags + project + duration
    write docs 1h30  /  2h 15m  /  1.5h         durations
    standup 09:30-10:00  /  review 9:00-11      an exact time range (today)

Persian digits and Persian separators are accepted.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.persian import to_en_digits

_DUR = re.compile(r"(?:(\d+(?:\.\d+)?)h(?:(\d+)m?)?|(\d+)m)")
_RANGE = re.compile(r"(\d{1,2}):(\d{2})[-\u2013\u2014](\d{1,2})(?::(\d{2}))?")


@dataclass
class Captured:
    title: str
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    minutes: int = 0
    start_time: Optional[dt.time] = None     # exact range, if given
    end_time: Optional[dt.time] = None

    @property
    def has_range(self) -> bool:
        return self.start_time is not None and self.end_time is not None

    def range_minutes(self) -> int:
        """Length of the exact range (an end before the start means it crosses midnight)."""
        if not self.has_range:
            return 0
        a = self.start_time.hour * 60 + self.start_time.minute      # type: ignore[union-attr]
        b = self.end_time.hour * 60 + self.end_time.minute          # type: ignore[union-attr]
        return (b - a) % (24 * 60) or 24 * 60


def parse(text: str) -> Captured:
    cap, words = Captured(title=""), []
    for raw in to_en_digits(text.replace("،", " ").replace("#", " #")).split():
        tok = raw.strip()
        if tok.startswith("#") and len(tok) > 1:
            cap.tags.append(tok[1:])
        elif tok.startswith("@") and len(tok) > 1 and cap.project is None:
            cap.project = tok[1:]
        else:
            r = _RANGE.fullmatch(tok)
            if r:
                h1, m1, h2, m2 = int(r.group(1)), int(r.group(2)), int(r.group(3)), int(r.group(4) or 0)
                if h1 > 23 or h2 > 24 or m1 > 59 or m2 > 59:
                    raise ValueError("ساعت نامعتبر است")
                cap.start_time, cap.end_time = dt.time(h1, m1), dt.time(h2 % 24, m2)
                continue
            m = _DUR.fullmatch(tok)
            if m:
                cap.minutes += round(float(m.group(1) or 0) * 60) + int(m.group(2) or m.group(3) or 0)
            else:
                words.append(tok)
    cap.title = " ".join(words)
    if not cap.title:
        raise ValueError("title is required")
    return cap
