"""Habits with streaks, plus helpers for OKR goals."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from ..core.database import Database
from ..core.models import Goal, Habit
from ..core.persian import now_utc, to_tehran
from .analytics import streaks


class HabitService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def check_in(self, habit_id: str, day: Optional[dt.date] = None) -> Habit:
        """Idempotent daily check-in (Tehran day)."""
        h = self.db.get(Habit, habit_id)
        if h is None:
            raise KeyError(habit_id)
        day = day or to_tehran(now_utc()).date()
        if day > to_tehran(now_utc()).date():
            raise ValueError("cannot check in the future")
        if day.isoformat() not in h.log:
            h.log = sorted([*h.log, day.isoformat()])
            self.db.save(h)
        return h

    def undo_check_in(self, habit_id: str, day: dt.date) -> Habit:
        h = self.db.get(Habit, habit_id)
        if h is None:
            raise KeyError(habit_id)
        h.log = [d for d in h.log if d != day.isoformat()]
        self.db.save(h)
        return h

    def streak(self, habit_id: str, today: Optional[dt.date] = None) -> tuple:
        h = self.db.get(Habit, habit_id)
        if h is None:
            raise KeyError(habit_id)
        return streaks([dt.date.fromisoformat(d) for d in h.log], today or to_tehran(now_utc()).date())

    def week_completion(self, habit_id: str, today: Optional[dt.date] = None) -> float:
        """Share of this week's target reached (Saturday-based week), capped at 1."""
        h = self.db.get(Habit, habit_id)
        if h is None:
            raise KeyError(habit_id)
        today = today or to_tehran(now_utc()).date()
        start = today - dt.timedelta(days=(today.weekday() + 2) % 7)
        n = sum(start <= dt.date.fromisoformat(d) <= today for d in h.log)
        return min(1.0, n / h.target_per_week) if h.target_per_week else 0.0


def update_key_result(db: Database, goal_id: str, index: int, current: float) -> Goal:
    g = db.get(Goal, goal_id)
    if g is None:
        raise KeyError(goal_id)
    if not 0 <= index < len(g.key_results):
        raise IndexError("no such key result")
    g.key_results[index]["current"] = current
    db.save(g)
    return g
