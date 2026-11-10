"""The formal end-of-day report: what was done (exact times), totals per project, what is still in progress, blockers and tomorrow's plan.

Built only from your own entries. Output is plain text / Markdown / HTML in Persian (Jalali dates, Persian digits) or English (Gregorian, Latin digits)
depending on the active language, ready to paste into an e-mail, chat or a timesheet system.
"""
from __future__ import annotations

import datetime as dt
import html
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..core.database import Database
from ..core.models import Habit, Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, format_duration, format_jalali, to_fa_digits, to_tehran, tr
from .analytics import split_by_local_day


@dataclass
class Line:
    start: str
    end: str
    title: str
    project: str
    minutes: int
    notes: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class DailyReport:
    day: dt.date
    total_sec: int = 0
    lines: List[Line] = field(default_factory=list)
    by_project: Dict[str, int] = field(default_factory=dict)          # minutes
    in_progress: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    tomorrow: List[str] = field(default_factory=list)
    habits_done: List[str] = field(default_factory=list)
    longest_min: int = 0
    note: str = ""

    @property
    def empty(self) -> bool:
        return not self.lines


def build(db: Database, day: dt.date) -> DailyReport:
    """Collect everything for the Tehran-local ``day`` (entries crossing midnight are split at midnight)."""
    rep = DailyReport(day)
    lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN)
    hi = lo + dt.timedelta(days=1)
    names = {p.id: p.name for p in db.all(Project)}
    pieces = []
    for e in db.entries_between(lo - dt.timedelta(days=1), hi):
        for d, sec, chunk_start in split_by_local_day(e):
            if d == day and sec > 0:
                pieces.append((chunk_start, sec, e))
    pieces.sort(key=lambda x: x[0])
    for start, sec, e in pieces:
        end = start + dt.timedelta(seconds=sec)
        proj = names.get(e.project_id or "", "")
        rep.lines.append(Line(start.strftime("%H:%M"), end.strftime("%H:%M"), e.title, proj, max(1, round(sec / 60)), (e.notes or e.description or "").strip(), list(e.tags)))
        rep.total_sec += sec
        key = proj or tr("بدون پروژه", "No project")
        rep.by_project[key] = rep.by_project.get(key, 0) + round(sec / 60)
        rep.longest_min = max(rep.longest_min, round(sec / 60))
    tomorrow_lo = hi
    tomorrow_hi = hi + dt.timedelta(days=1)
    for e in db.all(TimeEntry):
        if e.parent_id or e.column in ("done", "cancelled"):
            continue
        if e.status == Status.RUNNING or e.column == "in_progress":
            rep.in_progress.append(e.title)
        if e.column == "delayed" or "blocked" in e.tags or "مسدود" in e.tags:
            rep.blockers.append(e.title + (f" — {e.notes.strip()}" if e.notes.strip() else ""))
        if (e.status == Status.PLANNED and tomorrow_lo <= e.start_utc.astimezone(TEHRAN) < tomorrow_hi) or (e.due_utc and tomorrow_lo <= e.due_utc.astimezone(TEHRAN) < tomorrow_hi):
            rep.tomorrow.append(e.title)
    if not rep.tomorrow:                                                   # nothing scheduled: suggest the most important open tasks
        open_tasks = sorted((e for e in db.all(TimeEntry) if not e.parent_id and e.status == Status.PLANNED and e.column not in ("done", "cancelled")), key=lambda e: (e.priority, e.rank))
        rep.tomorrow = [e.title for e in open_tasks[:5]]
    rep.tomorrow, rep.in_progress, rep.blockers = rep.tomorrow[:8], rep.in_progress[:8], rep.blockers[:8]
    rep.habits_done = [h.name for h in db.all(Habit) if day.isoformat() in h.log]
    return rep


def _hm(minutes: int) -> str:
    return to_fa_digits(format_duration(minutes * 60))


def to_text(rep: DailyReport, author: str = "") -> str:
    """Formal plain text."""
    date = to_fa_digits(format_jalali(rep.day, "{weekday} {d} {month_name} {y}", fa_digits=False))
    out = [tr("گزارش کار روزانه", "Daily work report") + " — " + date]
    if author:
        out.append(tr("تهیه‌کننده: ", "Prepared by: ") + author)
    out.append("")
    if rep.empty:
        out.append(tr("در این روز کاری ثبت نشده است.", "No work was logged on this day."))
    else:
        out.append(tr(f"جمع زمان کار: {_hm(rep.total_sec // 60)} ساعت در {len(rep.lines)} ثبت", f"Total time: {_hm(rep.total_sec // 60)} h in {len(rep.lines)} entries"))
        out.append(""); out.append(tr("شرح کارهای انجام‌شده:", "Work completed:"))
        for i, l in enumerate(rep.lines, 1):
            proj = f" [{l.project}]" if l.project else ""
            out.append(to_fa_digits(f"{i}. {l.start}–{l.end}  {l.title}{proj} ({l.minutes} {tr('دقیقه', 'min')})"))
            if l.notes:
                out.append("   " + l.notes.replace("\n", " ")[:200])
        if len(rep.by_project) > 1 or (rep.by_project and "" not in rep.by_project):
            out.append(""); out.append(tr("به تفکیک پروژه:", "By project:"))
            for k, m in sorted(rep.by_project.items(), key=lambda kv: -kv[1]):
                out.append(f"- {k}: {_hm(m)}")
    for title_fa, title_en, items in ((" کارهای در جریان:", "In progress:", rep.in_progress), ("موانع و مشکلات:", "Blockers:", rep.blockers),
                                     ("برنامه‌ی روز بعد:", "Plan for tomorrow:", rep.tomorrow), ("عادت‌های انجام‌شده:", "Habits completed:", rep.habits_done)):
        if items:
            out.append(""); out.append(tr(title_fa.strip(), title_en))
            out += [f"- {i}" for i in items]
    return to_fa_digits("\n".join(out))


def to_markdown(rep: DailyReport, author: str = "") -> str:
    text = to_text(rep, author).split("\n")
    out = ["# " + text[0]]
    for line in text[1:]:
        out.append(("## " + line.rstrip(":：")) if line.endswith((":", "：")) and not line.startswith("-") and len(line) < 40 else line)
    return "\n".join(out)


def to_html(rep: DailyReport, author: str = "") -> str:
    rtl = tr("rtl", "ltr")
    body = "".join(f"<p>{html.escape(l)}</p>" if l else "" for l in to_text(rep, author).split("\n"))
    return (f"<!doctype html><html lang='{tr('fa', 'en')}' dir='{rtl}'><meta charset='utf-8'><title>{html.escape(tr('گزارش روزانه', 'Daily report'))}</title>"
            "<style>body{font-family:'IRANSans',Tahoma,sans-serif;max-width:760px;margin:30px auto;line-height:1.9}p{margin:2px 0}</style>" + body + "</html>")
