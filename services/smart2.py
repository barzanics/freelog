"""More offline helpers: task-name suggestions, typing-pattern mood, energy analysis, SMART goal validation, same-week-last-year."""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from statistics import mean, pstdev
from typing import Dict, List, Optional

from ..core.database import Database
from ..core.models import Goal, TimeEntry
from ..core.persian import to_tehran
from .insights import compare_periods


def suggest_titles(db: Database, typed: str, project_id: Optional[str] = None, top: int = 3) -> List[str]:
    """Longer, more descriptive past titles that start with / contain what you typed ("fix bug" -> "Fix login validation bug")."""
    t = typed.strip().lower()
    if len(t) < 3:
        return []
    c: Counter = Counter()
    for e in db.all(TimeEntry, "start_utc DESC")[:3000]:
        title = e.title.strip()
        if len(title) > len(t) and (title.lower().startswith(t) or all(w in title.lower() for w in t.split())):
            c[title] += 2 if project_id and e.project_id == project_id else 1
    return [k for k, _ in c.most_common(top)]


def typing_mood(intervals_ms: List[float], backspaces: int = 0) -> str:
    """Optional heuristic from inter-key intervals: 'flow' (fast, steady), 'stressed' (erratic, many corrections), else 'calm'."""
    if len(intervals_ms) < 10:
        return "unknown"
    m, sd = mean(intervals_ms), pstdev(intervals_ms)
    cv = sd / m if m else 0.0
    corrections = backspaces / len(intervals_ms)
    if m < 250 and cv < 0.6 and corrections < 0.1:
        return "flow"
    if cv > 1.0 or corrections > 0.25:
        return "stressed"
    return "calm"


def energy_by_hour(db: Database) -> Dict[int, float]:
    """Average energy (1-5) per Tehran clock hour, from entries that have an energy rating."""
    acc: Dict[int, List[int]] = defaultdict(list)
    for e in db.all(TimeEntry):
        if e.energy:
            acc[to_tehran(e.start_utc).hour].append(e.energy)
    return {h: round(mean(v), 2) for h, v in sorted(acc.items())}


def peak_energy_hours(db: Database, top: int = 3, min_samples: int = 1) -> List[int]:
    acc: Dict[int, List[int]] = defaultdict(list)
    for e in db.all(TimeEntry):
        if e.energy:
            acc[to_tehran(e.start_utc).hour].append(e.energy)
    ranked = sorted(((mean(v), h) for h, v in acc.items() if len(v) >= min_samples), reverse=True)
    return [h for _, h in ranked[:top]]


def validate_smart(goal: Goal) -> List[str]:
    """Return the SMART criteria the goal fails (empty = good)."""
    problems = []
    if len(goal.name.strip()) < 5:
        problems.append("specific: give the goal a descriptive name")
    if not goal.key_results or any(float(k.get("target", 0)) <= 0 for k in goal.key_results):
        problems.append("measurable: every key result needs a positive target")
    if goal.deadline is None:
        problems.append("time-bound: set a deadline")
    if len(goal.key_results) > 5:
        problems.append("achievable/relevant: more than 5 key results dilutes focus")
    return problems


def same_week_last_year(db: Database, today: dt.date) -> Dict[str, float]:
    """This week-to-date vs the same Saturday-based week 52 weeks ago."""
    start = today - dt.timedelta(days=(today.weekday() + 2) % 7)
    n = (today - start).days + 1
    prev = start - dt.timedelta(weeks=52)
    return compare_periods(db, (start, start + dt.timedelta(days=n)), (prev, prev + dt.timedelta(days=n)))


_LABEL_COL = {"entries": "title", "projects": "name", "clients": "name", "members": "name", "habits": "name", "goals": "name"}


def activity_feed(db: Database, limit: int = 50) -> List[Dict[str, str]]:
    """Latest changes from the audit log (entity names resolved when the row still exists)."""
    out = []
    for r in db.conn.execute("SELECT at, entity, entity_id, action FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall():
        label = ""
        col = _LABEL_COL.get(r[1])
        if col:
            row = db.conn.execute(f"SELECT {col} FROM {r[1]} WHERE id=?", (r[2],)).fetchone()
            label = row[0] if row else ""
        out.append({"at": r[0], "entity": r[1], "action": r[3], "label": label})
    return out
