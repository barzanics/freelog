"""Parse pasted text into a tree of check-list items.

Understands what people actually paste: Markdown check lists (``- [ ] task`` / ``- [x] done``), bullets (``- * •``), numbered lines (``1.`` ``1)``), Markdown headings
(``# Phase``), and indentation (2 or 4 spaces or a tab) for nesting. Each line may carry tokens: ``#tag``, ``@project``, a duration (``45m`` ``1h30``), a due date
(``d:2026-05-03`` or ``due:1405/02/13``) and a leading ``!`` to star it. Persian digits and separators are accepted.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.persian import parse_jalali, to_en_digits
from . import quick

_MARK = re.compile(r"^(?:[-*•+]\s+)?(?:\[( |x|X|✓|✔)\]\s*)?(?:\d+[.)]\s+)?")
_HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
_DUE = re.compile(r"\b(?:d|due):(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b", re.IGNORECASE)


@dataclass
class Node:
    title: str
    depth: int = 0
    done: bool = False
    heading: bool = False
    starred: bool = False
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    minutes: int = 0
    due: Optional[dt.date] = None
    children: List["Node"] = field(default_factory=list)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def _date(s: str) -> Optional[dt.date]:
    y, m, d = (int(x) for x in re.split(r"[-/]", s))
    try:
        return parse_jalali(f"{y}/{m}/{d}") if y < 1700 else dt.date(y, m, d)
    except ValueError:
        return None


def parse(text: str, max_depth: int = 3, max_lines: int = 500) -> List[Node]:
    """Return the root nodes. Nesting deeper than ``max_depth`` levels is flattened into the deepest level. Blank / title-less lines are skipped."""
    roots: List[Node] = []
    stack: List[tuple] = []                                   # (indent, node)
    n = 0
    for raw in to_en_digits(text.replace("\t", "    ")).splitlines():
        if not raw.strip():
            continue
        n += 1
        if n > max_lines:
            break
        line = raw.rstrip()
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        heading = False
        h = _HEAD.match(body)
        if h:
            heading, body, indent = True, h.group(2), (len(h.group(1)) - 1) * 2 - 1000     # headings sit above every list indent, so the items after them nest underneath
        m = _MARK.match(body)
        done = bool(m and m.group(1) and m.group(1) in "xX✓✔")
        body = body[m.end():] if m else body
        due = None
        dm = _DUE.search(body)
        if dm:
            due, body = _date(dm.group(1)), (body[:dm.start()] + body[dm.end():])
        starred = body.startswith("!")
        body = body.lstrip("!").strip()
        try:
            cap = quick.parse(body)
        except ValueError:
            continue
        node = Node(cap.title, 0, done, heading, starred, cap.tags, cap.project, cap.minutes, due)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        depth = min(len(stack), max_depth - 1)
        node.depth = depth
        if stack:
            parent = stack[-1][1] if len(stack) < max_depth else stack[max_depth - 2][1]
            parent.children.append(node)
        else:
            roots.append(node)
        stack.append((indent, node))
    return roots
