"""Catch-up: a complete way to deal with overdue and postponed work - and to stop postponing it.

* ``scan`` finds what slipped: tasks past their due date, planned blocks whose day has gone, tasks you pushed more than once, and missed routine check boxes.
* ``score`` ranks them (priority, importance, how late, how many times postponed, effort) and ``recommend`` picks one of five actions:
  **now** (a quick win or a task postponed 3+ times: do it first thing), **today**, **schedule**, **split** (a big task that keeps slipping) or **drop** (a low-value task postponed 4+ times:
  decide, do not carry it around forever).
* ``plan`` fits everything into the next working days *within your real daily capacity* (minus what is already scheduled) and ``apply_plan`` writes the new slots.
* ``postpone`` is the one honest way to push a task: it is counted and logged, and the 3rd push raises a chronic-procrastination flag with advice.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, to_tehran, tr
from . import routines

PRIORITY_WEIGHT = {1: 50, 2: 35, 3: 20, 4: 10, 5: 4}
QUICK_MIN, BIG_MIN = 15, 120
CHRONIC_AT = 3
DEFAULT_CAPACITY = 360


def _open(e: TimeEntry) -> bool:
    return e.column not in ("done", "cancelled") and e.status != Status.DONE and e.status != Status.RUNNING


def _today_start(now: dt.datetime) -> dt.datetime:
    return dt.datetime.combine(to_tehran(now).date(), dt.time(), tzinfo=TEHRAN)


def _est(e: TimeEntry) -> int:
    return e.estimated_min or (int((e.end_utc - e.start_utc).total_seconds() // 60) if e.end_utc and e.status == Status.PLANNED else 0) or 30


def off_weekdays(db: Database) -> List[int]:
    return list(db.get_setting("prompt_config", {}).get("off_weekdays", [4]))


# ------------------------------------------------------------------ scoring
def score(it: Dict[str, Any]) -> float:
    s = PRIORITY_WEIGHT.get(it["priority"], 20) + (15 if it["important"] else 0)
    s += min(30, 3 * it["days_overdue"]) + min(40, 8 * it["postponed"])
    s += 12 if it["est_min"] <= QUICK_MIN else (-8 if it["est_min"] >= 180 else 0)
    return round(s, 1)


def recommend(it: Dict[str, Any]) -> str:
    n, est, pr = it["postponed"], it["est_min"], it["priority"]
    if n >= 4 and pr >= 4:
        return "drop"
    if n >= CHRONIC_AT and est > BIG_MIN:
        return "split"
    if n >= CHRONIC_AT and est <= 30:
        return "now"
    if est <= QUICK_MIN:
        return "now"
    if pr <= 2 or it["days_overdue"] >= 7:
        return "today"
    return "schedule"


def _item(db: Database, e: TimeEntry, kind: str, today: dt.datetime, names: Dict[str, str]) -> Dict[str, Any]:
    ref = e.due_utc if kind == "overdue" and e.due_utc else e.start_utc
    late = max(0, (today.date() - to_tehran(ref).date()).days) if kind != "postponed" else (max(0, (today.date() - to_tehran(e.due_utc).date()).days) if e.due_utc else 0)
    it = {"id": e.id, "title": e.title, "project_id": e.project_id, "project": names.get(e.project_id or "", ""), "due": e.due_utc, "days_overdue": late, "postponed": int(e.extra.get("postponed", 0)),
          "est_min": _est(e), "priority": e.priority, "important": e.important, "kind": kind, "parent_id": e.parent_id}
    it["score"], it["action"] = score(it), recommend(it)
    return it


def scan(db: Database, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    now = now or now_utc()
    today = _today_start(now)
    names = {p.id: p.name for p in db.all(Project)}
    items: Dict[str, Dict[str, Any]] = {}
    for r in db.conn.execute("SELECT * FROM entries WHERE column NOT IN ('done','cancelled') AND status='planned'"):
        e = TimeEntry.from_row(r)
        if not _open(e) or e.source in ("auto", "prompt", "quick"):
            continue
        kind = None
        if e.due_utc and e.due_utc < today:
            kind = "overdue"
        elif e.end_utc and e.start_utc < today:                       # a scheduled block whose day passed without being done
            kind = "missed_block"
        elif int(e.extra.get("postponed", 0)) >= 1:
            kind = "postponed"
        if kind:
            items[e.id] = _item(db, e, kind, today, names)
    ranked = sorted(items.values(), key=lambda i: -i["score"])
    miss = routines.missed(db, now)
    return {"items": ranked, "overdue": [i for i in ranked if i["kind"] == "overdue"], "missed_blocks": [i for i in ranked if i["kind"] == "missed_block"],
            "postponed": [i for i in ranked if i["postponed"] >= 1], "chronic": [i for i in ranked if i["postponed"] >= CHRONIC_AT], "missed_routines": miss,
            "counts": {"overdue": sum(i["kind"] == "overdue" for i in ranked), "missed_blocks": sum(i["kind"] == "missed_block" for i in ranked), "postponed": sum(i["postponed"] >= 1 for i in ranked),
                       "chronic": sum(i["postponed"] >= CHRONIC_AT for i in ranked), "missed_routines": len(miss), "total": len(ranked) + len(miss)}}


# ------------------------------------------------------------------ planning
def _next_days(db: Database, start: dt.date, n: int) -> List[dt.date]:
    off, out, d = set(off_weekdays(db)), [], start
    while len(out) < n and (d - start).days < 21:
        if d.weekday() not in off:
            out.append(d)
        d += dt.timedelta(days=1)
    return out or [start]


def _already_planned_min(db: Database, day: dt.date, skip_ids: set) -> int:
    lo = dt.datetime.combine(day, dt.time(), tzinfo=TEHRAN).astimezone(UTC)
    hi = lo + dt.timedelta(days=1)
    total = 0
    for r in db.conn.execute("SELECT * FROM entries WHERE status='planned' AND column NOT IN ('done','cancelled') AND end_utc IS NOT NULL AND start_utc>=? AND start_utc<?", (lo.isoformat(), hi.isoformat())):
        e = TimeEntry.from_row(r)
        if e.id not in skip_ids:
            total += int((e.end_utc - e.start_utc).total_seconds() // 60)
    return total


def plan(db: Database, now: Optional[dt.datetime] = None, capacity_min: Optional[int] = None, days: Optional[int] = None, work_start_hour: Optional[int] = None) -> Dict[str, Any]:
    """Fit the slipped work into the next working days. Quick wins and chronic tasks go first (``now``), the rest by score; what does not fit is reported as ``later``."""
    now = now or now_utc()
    g = db.get_setting
    cap = int(capacity_min or g("catchup_capacity_min", DEFAULT_CAPACITY))
    ndays = int(days or g("catchup_days", 3))
    start_h = int(work_start_hour if work_start_hour is not None else g("catchup_work_start", 9))
    sc = scan(db, now)
    todo = [i for i in sc["items"] if not i["parent_id"] or True]
    decide = [i for i in todo if i["action"] == "drop"]
    split = [i for i in todo if i["action"] == "split"]
    movable = [i for i in todo if i["action"] not in ("drop", "split")]
    movable.sort(key=lambda i: (0 if i["action"] == "now" else 1, -i["score"]))
    ids = {i["id"] for i in movable}
    day_list = _next_days(db, to_tehran(now).date(), ndays)
    out_days = [{"date": d, "capacity": max(0, cap - _already_planned_min(db, d, ids)), "minutes": 0, "items": []} for d in day_list]
    later: List[Dict[str, Any]] = []
    for it in movable:
        placed = False
        for d in out_days:
            fits = d["minutes"] + it["est_min"] <= d["capacity"] or (not d["items"] and it["est_min"] > d["capacity"] > 0)      # an oversized task still gets a day of its own
            if fits:
                base = dt.datetime.combine(d["date"], dt.time(start_h), tzinfo=TEHRAN) + dt.timedelta(minutes=d["minutes"] + _already_planned_min(db, d["date"], ids))
                it = {**it, "slot_start": base.astimezone(UTC), "slot_end": (base + dt.timedelta(minutes=it["est_min"])).astimezone(UTC)}
                d["items"].append(it); d["minutes"] += it["est_min"]; placed = True
                break
        if not placed:
            later.append(it)
    total_min = sum(i["est_min"] for i in movable)
    return {"days": out_days, "decide": decide, "split": split, "later": later, "missed_routines": sc["missed_routines"], "scan": sc,
            "summary": {"to_schedule": len(movable), "minutes": total_min, "capacity_per_day": cap, "days_needed": round(total_min / cap, 1) if cap else None, "fits": not later,
                        "chronic": sc["counts"]["chronic"], "decide": len(decide), "split": len(split)}}


def apply_plan(db: Database, plan_: Dict[str, Any], now: Optional[dt.datetime] = None) -> int:
    """Write the plan: every placed task gets its slot (original time remembered in ``extra['rescheduled_from']``). One transaction."""
    now = now or now_utc()
    n = 0
    with db.transaction():
        for d in plan_["days"]:
            for it in d["items"]:
                e = db.get(TimeEntry, it["id"])
                if e is None:
                    continue
                log = list(e.extra.get("postpone_log", [])) + [{"at": now.isoformat(), "to": it["slot_start"].isoformat(), "by": "plan"}]
                e.extra = {**e.extra, "rescheduled_from": e.extra.get("rescheduled_from") or e.start_utc.isoformat(), "postpone_log": log[-30:]}
                e.start_utc, e.end_utc = it["slot_start"], it["slot_end"]
                e.status, e.column = Status.PLANNED, ("in_progress" if e.column == "delayed" else e.column)
                e.updated_at = now
                db.save(e, touch=False)
                n += 1
    return n


# ------------------------------------------------------------------ the individual actions
def _target_date(db: Database, to: Any, now: dt.datetime) -> dt.date:
    today = to_tehran(now).date()
    if isinstance(to, dt.date):
        return to
    if to == "tomorrow":
        return _next_days(db, today + dt.timedelta(days=1), 1)[0]
    if to == "in_3_days":
        return _next_days(db, today + dt.timedelta(days=3), 1)[0]
    if to == "next_week":
        return _next_days(db, today + dt.timedelta(days=7), 1)[0]
    raise ValueError("unknown target")


def postpone(db: Database, entry_id: str, to: Any = "tomorrow", reason: str = "", now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Push a task to ``tomorrow`` / ``in_3_days`` / ``next_week`` / a date. Counted and logged; from the 3rd push on, advice is returned."""
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    now = now or now_utc()
    day = _target_date(db, to, now)
    old = to_tehran(e.start_utc)
    new_start = dt.datetime.combine(day, old.time(), tzinfo=TEHRAN).astimezone(UTC)
    delta = new_start - e.start_utc
    n = int(e.extra.get("postponed", 0)) + 1
    log = list(e.extra.get("postpone_log", [])) + [{"at": now.isoformat(), "from": e.start_utc.isoformat(), "to": new_start.isoformat(), "reason": reason.strip()[:200]}]
    e.extra = {**e.extra, "postponed": n, "postpone_log": log[-30:]}
    e.start_utc = new_start
    if e.end_utc:
        e.end_utc = e.end_utc + delta
    if e.due_utc:
        e.due_utc = dt.datetime.combine(day, to_tehran(e.due_utc).time(), tzinfo=TEHRAN).astimezone(UTC)
    e.updated_at = now
    db.save(e, touch=False)
    it = {"postponed": n, "est_min": _est(e), "priority": e.priority, "days_overdue": 0, "important": e.important}
    chronic = n >= CHRONIC_AT
    advice = ""
    if chronic:
        act = recommend(it)
        advice = {"now": tr("این را اول صبح انجام بده؛ کوتاه است و هر بار که عقب می‌اندازی‌اش گران‌تر می‌شود.", "Do this first thing tomorrow: it is short and every push makes it more expensive."),
                  "split": tr("بزرگ است و مدام عقب می‌افتد؛ به زیرتسک‌های کوچک بشکنش و فقط اولی را انجام بده.", "It is big and keeps slipping: split it into small sub-tasks and do only the first."),
                  "drop": tr("چهار بار عقب افتاده و اولویتش پایین است؛ یا حذفش کن یا همین حالا تعهدش کن.", "Pushed four times and low priority: delete it or commit to it right now.")}.get(act,
                  tr("چند بار عقب افتاده؛ برایش یک ساعت مشخص در تقویم بگذار.", "Pushed several times: put a fixed time slot in the calendar."))
    return {"entry": e, "count": n, "chronic": chronic, "advice": advice, "date": day}


def drop(db: Database, entry_id: str, reason: str = "", now: Optional[dt.datetime] = None) -> TimeEntry:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.column = "cancelled"
    e.extra = {**e.extra, "dropped_at": (now or now_utc()).isoformat(), "dropped_reason": reason.strip()[:200]}
    db.save(e)
    return e


def complete(db: Database, entry_id: str, now: Optional[dt.datetime] = None) -> TimeEntry:
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, now or now_utc(), 100
    db.save(e)
    return e


# ------------------------------------------------------------------ insight & the morning briefing
def stats(db: Database, now: Optional[dt.datetime] = None, days: int = 30) -> Dict[str, Any]:
    """How you postpone: pushes in the window, tasks pushed 3+ times, the share of postponed tasks that eventually got done, the average lateness of what is still open."""
    now = now or now_utc()
    cutoff = (now - dt.timedelta(days=days)).isoformat()
    pushes, ever, finished = 0, 0, 0
    chronic: List[str] = []
    for r in db.conn.execute("SELECT * FROM entries WHERE extra LIKE '%postponed%'"):
        e = TimeEntry.from_row(r)
        n = int(e.extra.get("postponed", 0))
        if not n:
            continue
        ever += 1
        finished += 1 if (e.column == "done" or e.status == Status.DONE) else 0
        pushes += sum(1 for l in e.extra.get("postpone_log", []) if l.get("by") != "plan" and l.get("at", "") >= cutoff)
        if n >= CHRONIC_AT and e.column not in ("done", "cancelled"):
            chronic.append(e.title)
    sc = scan(db, now)
    late = [i["days_overdue"] for i in sc["overdue"]]
    return {"pushes": pushes, "postponed_tasks": ever, "finished_pct": round(100 * finished / ever) if ever else None, "chronic": sorted(chronic), "avg_days_overdue": round(sum(late) / len(late), 1) if late else 0.0}


def morning_briefing(db: Database, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """The text for the start-of-day notification: what slipped, what to do first, what today can hold."""
    pl = plan(db, now)
    c = pl["scan"]["counts"]
    if not c["total"]:
        return {"has_work": False, "title": tr("هیچ کار عقب‌افتاده‌ای نداری 🎉", "Nothing is overdue 🎉"), "lines": []}
    first = pl["days"][0]["items"][:3] if pl["days"] else []
    lines = [tr(f"{c['overdue']} کار از موعد گذشته، {c['missed_blocks']} بلوک از دست‌رفته، {c['missed_routines']} روتین ناتمام", f"{c['overdue']} overdue, {c['missed_blocks']} missed blocks, {c['missed_routines']} missed routines")]
    if c["chronic"]:
        lines.append(tr(f"{c['chronic']} کار بیش از ۲ بار عقب افتاده — امروز تکلیفشان را روشن کن", f"{c['chronic']} task(s) postponed 3+ times — settle them today"))
    if first:
        lines.append(tr("اول این‌ها: ", "Start with: ") + "؛ ".join(f"{i['title']} ({i['est_min']}m)" for i in first))
    s = pl["summary"]
    lines.append(tr(f"برای همه‌اش حدود {s['days_needed']} روز کاری لازم است", f"About {s['days_needed']} working day(s) to clear it all"))
    return {"has_work": True, "title": tr("برنامه‌ی جبران امروز", "Today's recovery plan"), "lines": lines, "plan": pl}


def should_show_briefing(db: Database, now: Optional[dt.datetime] = None) -> bool:
    now = now or now_utc()
    lt = to_tehran(now)
    return lt.hour >= int(db.get_setting("catchup_briefing_hour", 6)) and db.get_setting("catchup_last_briefing") != lt.date().isoformat() and bool(db.get_setting("catchup_briefing", True))


def mark_briefing_shown(db: Database, now: Optional[dt.datetime] = None) -> None:
    db.set_setting("catchup_last_briefing", to_tehran(now or now_utc()).date().isoformat())
