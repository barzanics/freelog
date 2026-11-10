"""Local team: members, assignment, threaded comments, @mentions (all local, no accounts)."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..core.database import Database
from ..core.models import Comment, Member, TimeEntry
from ..core.persian import now_utc

_MENTION = re.compile(r"@([\w\u0600-\u06FF]+)")


class Team:
    NOTIF_KEY = "notifications"

    def __init__(self, db: Database) -> None:
        self.db = db

    def add_member(self, name: str, **kw: object) -> Member:
        name = name.strip()
        if not name or " " in name:
            raise ValueError("member handle must be a single word (used for @mentions)")
        if any(m.name.lower() == name.lower() for m in self.db.all(Member)):
            raise ValueError("duplicate member")
        m = Member(name=name, **kw)  # type: ignore[arg-type]
        self.db.save(m)
        return m

    def assign(self, entry_id: str, member_id: Optional[str]) -> TimeEntry:
        e = self.db.get(TimeEntry, entry_id)
        if e is None:
            raise KeyError(entry_id)
        if member_id and self.db.get(Member, member_id) is None:
            raise KeyError(member_id)
        if member_id:
            e.extra["assignee"] = member_id
        else:
            e.extra.pop("assignee", None)
        self.db.save(e)
        return e

    def tasks_of(self, member_id: str) -> List[TimeEntry]:
        return [e for e in self.db.all(TimeEntry) if e.extra.get("assignee") == member_id]

    def workload_hours(self) -> Dict[str, float]:
        """Hours logged on tasks assigned to each member name."""
        names = {m.id: m.name for m in self.db.all(Member)}
        out: Dict[str, float] = {}
        for e in self.db.all(TimeEntry):
            a = e.extra.get("assignee")
            if a in names:
                out[names[a]] = round(out.get(names[a], 0.0) + e.duration_sec / 3600, 2)
        return out

    def comment(self, entry_id: str, author_id: str, text: str, parent_id: Optional[str] = None) -> Comment:
        text = text.strip()
        if not text:
            raise ValueError("empty comment")
        if self.db.get(TimeEntry, entry_id) is None:
            raise KeyError(entry_id)
        if parent_id:
            parent = self.db.get(Comment, parent_id)
            if parent is None or parent.entry_id != entry_id:
                raise ValueError("parent comment not on this task")
        by_name = {m.name.lower(): m.id for m in self.db.all(Member)}
        mentions = sorted({by_name[n.lower()] for n in _MENTION.findall(text) if n.lower() in by_name})
        c = Comment(entry_id=entry_id, author_id=author_id, text=text, parent_id=parent_id, mentions=mentions)
        with self.db.transaction():
            self.db.save(c)
            if mentions:
                notes = self.db.get_setting(self.NOTIF_KEY, [])
                notes += [{"member": m, "comment": c.id, "entry": entry_id, "at": now_utc().isoformat(), "read": False}
                          for m in mentions if m != author_id]
                self.db.set_setting(self.NOTIF_KEY, notes[-500:])
        return c

    def thread(self, entry_id: str) -> List[dict]:
        """Comments as a flat, depth-annotated, chronological tree walk."""
        rows = [Comment.from_row(r) for r in self.db.conn.execute(
            "SELECT * FROM comments WHERE entry_id=? ORDER BY created_at, rowid", (entry_id,))]
        kids: Dict[Optional[str], List[Comment]] = {}
        for c in rows:
            kids.setdefault(c.parent_id, []).append(c)
        out: List[dict] = []

        def walk(pid: Optional[str], depth: int) -> None:
            for c in kids.get(pid, []):
                out.append({"comment": c, "depth": depth})
                walk(c.id, depth + 1)
        walk(None, 0)
        return out

    def unread(self, member_id: str) -> List[dict]:
        return [n for n in self.db.get_setting(self.NOTIF_KEY, []) if n["member"] == member_id and not n["read"]]

    def mark_read(self, member_id: str) -> int:
        notes = self.db.get_setting(self.NOTIF_KEY, [])
        n = 0
        for x in notes:
            if x["member"] == member_id and not x["read"]:
                x["read"] = True
                n += 1
        self.db.set_setting(self.NOTIF_KEY, notes)
        return n
