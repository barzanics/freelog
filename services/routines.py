"""Routines: check boxes that come back on a schedule (hourly / every N minutes / daily / weekly / monthly) and notify you until you tick them.

Stored in the settings table (so backups and configuration export carry them). Times are Tehran local time; "monthly" uses the active calendar
(Jalali day-of-month in Persian mode, Gregorian in English mode; day 31 means "the last day" and is clamped to the month length).
An *occurrence* is one due moment with a stable key, e.g. ``d:2026-05-02`` or ``h:2026-05-02-14``; ticking stores the key, so history and streaks are exact.
"""
from __future__ import annotations

import calendar as _cal
import datetime as dt
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from ..core import persian as _p
from ..core.database import Database
from ..core.models import new_id
from ..core.persian import TEHRAN, date_to_jalali, jalali_month_length, jalali_to_date, now_utc, to_tehran

KINDS = ("hourly", "interval", "daily", "weekly", "monthly")
Occ = Tuple[str, dt.datetime]                      # (key, due time in Tehran local time)
_HHMM = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
KEEP_DAYS = 400


class RoutineError(ValueError):
    """Invalid routine definition."""


# ------------------------------------------------------------------ storage
def all_routines(db: Database) -> List[Dict[str, Any]]:
    return list(db.get_setting("routines", []))


def _save(db: Database, items: List[Dict[str, Any]]) -> None:
    db.set_setting("routines", items)


def get(db: Database, rid: str) -> Optional[Dict[str, Any]]:
    return next((r for r in all_routines(db) if r["id"] == rid), None)


def _parse_time(t: str) -> dt.time:
    m = _HHMM.match(str(t).strip())
    if not m:
        raise RoutineError("زمان باید به شکل HH:MM باشد")
    return dt.time(int(m.group(1)), int(m.group(2)))


def normalise(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and fill defaults. Raises RoutineError with a message fit for the UI."""
    title = str(fields.get("title", "")).strip()
    kind = fields.get("kind", "daily")
    if not title:
        raise RoutineError("عنوان را وارد کنید")
    if kind not in KINDS:
        raise RoutineError("نوع تکرار نامعتبر است")
    r: Dict[str, Any] = {"id": fields.get("id") or new_id(), "title": title[:120], "kind": kind, "note": str(fields.get("note", ""))[:400], "notify": bool(fields.get("notify", True)),
                         "repeat_min": int(fields.get("repeat_min", 0) or 0), "active": bool(fields.get("active", True)), "color": str(fields.get("color", "")),
                         "created": fields.get("created") or now_utc().isoformat()}
    if r["repeat_min"] < 0 or r["repeat_min"] > 1440:
        raise RoutineError("فاصله‌ی یادآوری مجدد نامعتبر است")
    if kind in ("daily", "weekly", "monthly"):
        r["time"] = _parse_time(fields.get("time", "09:00")).strftime("%H:%M")
    if kind == "weekly":
        wd = sorted({int(x) for x in fields.get("weekdays", [])})
        if not wd or any(not 0 <= x <= 6 for x in wd):
            raise RoutineError("حداقل یک روز هفته را انتخاب کنید")
        r["weekdays"] = wd
    if kind == "monthly":
        day = int(fields.get("day", 1))
        if not 1 <= day <= 31:
            raise RoutineError("روز ماه باید بین ۱ و ۳۱ باشد")
        r["day"] = day
    if kind in ("hourly", "interval"):
        a, b = int(fields.get("from_hour", 9)), int(fields.get("to_hour", 18))
        if not (0 <= a < b <= 23):
            raise RoutineError("بازه‌ی ساعت‌های فعال نامعتبر است")
        r["from_hour"], r["to_hour"] = a, b
        if kind == "hourly":
            n = int(fields.get("every_hours", 1))
            if not 1 <= n <= 12:
                raise RoutineError("فاصله‌ی ساعتی باید بین ۱ و ۱۲ باشد")
            r["every_hours"] = n
        else:
            m = int(fields.get("every_min", 30))
            if not 5 <= m <= 720:
                raise RoutineError("فاصله‌ی دقیقه‌ای باید بین ۵ و ۷۲۰ باشد")
            r["every_min"] = m
    return r


def add(db: Database, **fields: Any) -> Dict[str, Any]:
    r = normalise(fields)
    items = all_routines(db)
    items.append(r)
    _save(db, items)
    return r


def update(db: Database, rid: str, **fields: Any) -> Dict[str, Any]:
    items = all_routines(db)
    for i, old in enumerate(items):
        if old["id"] == rid:
            items[i] = normalise({**old, **fields, "id": rid, "created": old["created"]})
            _save(db, items)
            return items[i]
    raise KeyError(rid)


def delete(db: Database, rid: str) -> bool:
    items = all_routines(db)
    keep = [r for r in items if r["id"] != rid]
    if len(keep) == len(items):
        return False
    _save(db, keep)
    for key in ("routine_checks", "routine_notified"):
        d = db.get_setting(key, {})
        if d.pop(rid, None) is not None:
            db.set_setting(key, d)
    return True


# ------------------------------------------------------------------ schedule math
def _local(d: dt.date, t: dt.time) -> dt.datetime:
    return dt.datetime.combine(d, t, tzinfo=TEHRAN)


def _month_day(d: dt.date, day: int) -> Optional[dt.date]:
    """The date of "day N of the month" for the month containing ``d`` in the active calendar (clamped), or None if that month is impossible."""
    if _p.is_gregorian():
        return dt.date(d.year, d.month, min(day, _cal.monthrange(d.year, d.month)[1]))
    jy, jm, _ = date_to_jalali(d)
    return jalali_to_date(jy, jm, min(day, jalali_month_length(jy, jm)))


def occurrences(r: Dict[str, Any], start: dt.datetime, end: dt.datetime) -> List[Occ]:
    """Due moments of one routine inside [start, end) (both converted to Tehran time), oldest first."""
    s, e = to_tehran(start), to_tehran(end)
    out: List[Occ] = []
    d = s.date() - dt.timedelta(days=1)
    last = e.date() + dt.timedelta(days=1)
    kind = r["kind"]
    seen_months = set()
    while d <= last:
        if kind == "daily":
            out.append((f"d:{d}", _local(d, _parse_time(r["time"]))))
        elif kind == "weekly" and d.weekday() in r["weekdays"]:
            out.append((f"w:{d}", _local(d, _parse_time(r["time"]))))
        elif kind == "monthly":
            md = _month_day(d, r["day"])
            if md is not None and md not in seen_months:
                seen_months.add(md)
                out.append((f"m:{md}", _local(md, _parse_time(r["time"]))))
        elif kind == "hourly":
            for h in range(r["from_hour"], r["to_hour"] + 1, r["every_hours"]):
                out.append((f"h:{d}-{h:02d}", _local(d, dt.time(h, 0))))
        elif kind == "interval":
            t = r["from_hour"] * 60
            while t <= r["to_hour"] * 60:
                out.append((f"i:{d}-{t // 60:02d}{t % 60:02d}", _local(d, dt.time(t // 60, t % 60))))
                t += r["every_min"]
        d += dt.timedelta(days=1)
    return sorted({k: v for k, v in out if s <= v < e}.items(), key=lambda kv: kv[1])


# ------------------------------------------------------------------ checking
def _checks(db: Database) -> Dict[str, Dict[str, str]]:
    return db.get_setting("routine_checks", {})


def is_checked(db: Database, rid: str, key: str) -> bool:
    return key in _checks(db).get(rid, {})


def check(db: Database, rid: str, key: str, now: Optional[dt.datetime] = None) -> None:
    if get(db, rid) is None:
        raise KeyError(rid)
    d = _checks(db)
    d.setdefault(rid, {})[key] = (now or now_utc()).isoformat()
    cutoff = ((now or now_utc()) - dt.timedelta(days=KEEP_DAYS)).isoformat()
    d[rid] = {k: v for k, v in d[rid].items() if v >= cutoff}
    db.set_setting("routine_checks", d)


def uncheck(db: Database, rid: str, key: str) -> None:
    d = _checks(db)
    if d.get(rid, {}).pop(key, None) is not None:
        db.set_setting("routine_checks", d)


def toggle(db: Database, rid: str, key: str, now: Optional[dt.datetime] = None) -> bool:
    """Flip a check box; returns the new state."""
    if is_checked(db, rid, key):
        uncheck(db, rid, key)
        return False
    check(db, rid, key, now)
    return True


# ------------------------------------------------------------------ what to show / what to notify
def today_items(db: Database, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    """Every occurrence of today for active routines, with state: checked / overdue / upcoming."""
    now = now or now_utc()
    lt = to_tehran(now)
    lo = dt.datetime.combine(lt.date(), dt.time(), tzinfo=TEHRAN)
    out = []
    for r in all_routines(db):
        if not r["active"]:
            continue
        for key, due in occurrences(r, lo, lo + dt.timedelta(days=1)):
            checked = is_checked(db, r["id"], key)
            out.append({"routine": r, "key": key, "due": due, "checked": checked, "overdue": (not checked) and due <= lt, "upcoming": due > lt})
    return sorted(out, key=lambda x: (x["due"], x["routine"]["title"]))


def this_month_items(db: Database, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    """The occurrence of every active *monthly* routine that falls in the current month of the active calendar (shown even when it is not today)."""
    now = now or now_utc()
    lt = to_tehran(now)
    out = []
    for r in all_routines(db):
        if r["active"] and r["kind"] == "monthly":
            md = _month_day(lt.date(), r["day"])
            due = _local(md, _parse_time(r["time"]))
            key = f"m:{md}"
            checked = is_checked(db, r["id"], key)
            out.append({"routine": r, "key": key, "due": due, "checked": checked, "overdue": (not checked) and due <= lt, "upcoming": due > lt})
    return sorted(out, key=lambda x: x["due"])


def due_notifications(db: Database, now: Optional[dt.datetime] = None, grace_hours: float = 12.0) -> List[Dict[str, Any]]:
    """Occurrences that are due and unchecked and should (re)notify now. Each is notified once, then again every ``repeat_min`` if set."""
    now = now or now_utc()
    lt = to_tehran(now)
    notified = db.get_setting("routine_notified", {})
    out = []
    for r in all_routines(db):
        if not (r["active"] and r["notify"]):
            continue
        for key, due in occurrences(r, lt - dt.timedelta(hours=grace_hours), lt + dt.timedelta(seconds=1)):
            if is_checked(db, r["id"], key):
                continue
            last = notified.get(r["id"], {}).get(key)
            if last is None or (r["repeat_min"] and lt - to_tehran(dt.datetime.fromisoformat(last)) >= dt.timedelta(minutes=r["repeat_min"])):
                out.append({"routine": r, "key": key, "due": due})
    return out


def mark_notified(db: Database, items: List[Dict[str, Any]], now: Optional[dt.datetime] = None) -> None:
    now = now or now_utc()
    d = db.get_setting("routine_notified", {})
    cutoff = (now - dt.timedelta(days=3)).isoformat()
    for it in items:
        d.setdefault(it["routine"]["id"], {})[it["key"]] = now.isoformat()
    for rid in list(d):
        d[rid] = {k: v for k, v in d[rid].items() if v >= cutoff}
    db.set_setting("routine_notified", d)


# ------------------------------------------------------------------ statistics
def streak(db: Database, rid: str, now: Optional[dt.datetime] = None, look_back_days: int = 90) -> int:
    """Consecutive checked occurrences counting back from the most recent one that is already due (an unchecked, still-fresh one does not break it)."""
    r = get(db, rid)
    if r is None:
        raise KeyError(rid)
    now = now or now_utc()
    past = [o for o in occurrences(r, now - dt.timedelta(days=look_back_days), now) if o[1] <= to_tehran(now)]
    n = 0
    for i, (key, _due) in enumerate(reversed(past)):
        if is_checked(db, rid, key):
            n += 1
        elif i == 0:
            continue
        else:
            break
    return n


def completion(db: Database, rid: str, days: int = 30, now: Optional[dt.datetime] = None) -> float:
    """Percent of occurrences due in the last ``days`` that were ticked (0 when none were due)."""
    r = get(db, rid)
    if r is None:
        raise KeyError(rid)
    now = now or now_utc()
    past = [o for o in occurrences(r, now - dt.timedelta(days=days), now) if o[1] <= to_tehran(now)]
    return round(100 * sum(is_checked(db, rid, k) for k, _ in past) / len(past), 1) if past else 0.0
