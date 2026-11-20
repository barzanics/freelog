"""The hourly check-in: at the top of every working hour a forced popup asks two things - what did you do in the last hour, and what will you do in the next one.

* The **last hour** part is exact: measured active minutes, apps, what is already logged, and the tasks you *planned* at the previous check-in (tick = done, untick = carried over).
* The **next hour** part is a plan, not a wish: pick from today's tasks / what slipped (catch-up) / what you were just doing, or type lines; each becomes a planned block in the calendar,
  so the next check-in can tell you whether you kept your plan.
* It never fires while you are away or in quiet hours, it can be snoozed only a few times, and after three hours without a break it suggests one.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from ..core.database import Database
from ..core.models import Project, Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc, tr
from . import calendar_events as ce, catchup
from .ledger import Ledger, hour_floor
from .prompter import Prompter

ANSWERED, SNOOZE, CONFIG = "checkin_answered", "checkin_snooze", "checkin_config"
DEFAULTS = {"enabled": True, "mode": "both", "forced": True, "max_snooze": 2, "snooze_min": 10, "min_unlogged_min": 5, "break_after_min": 150, "break_min": 10, "default_plan_min": 20}


class CheckinError(ValueError):
    """The check-in cannot be submitted yet (message is user-facing)."""


def config(db: Database) -> Dict[str, Any]:
    return {**DEFAULTS, **db.get_setting(CONFIG, {})}


def set_config(db: Database, **kw: Any) -> Dict[str, Any]:
    cur = config(db)
    bad = set(kw) - set(DEFAULTS)
    if bad:
        raise CheckinError(f"Unknown setting: {sorted(bad)}")
    if "mode" in kw and kw["mode"] not in ("both", "past", "future"):
        raise CheckinError("Mode must be both, past or future")
    cur.update(kw)
    db.set_setting(CONFIG, cur)
    return cur


def due(db: Database, now: Optional[dt.datetime] = None, engaged_recently: bool = True) -> Optional[dt.datetime]:
    """The hour (start) whose check-in is due, or None: disabled, already answered, snoozed, you are away, or quiet hours / a day off."""
    now = now or now_utc()
    cfg = config(db)
    h = hour_floor(now)
    if not cfg["enabled"] or not engaged_recently or h.isoformat() in db.get_setting(ANSWERED, {}):
        return None
    sn = db.get_setting(SNOOZE, {})
    if sn.get("hour") == h.isoformat() and dt.datetime.fromisoformat(sn["until"]) > now:
        return None
    if Prompter(db, clock=lambda: now).in_quiet_time():
        return None
    return h


def snooze(db: Database, h: dt.datetime, now: Optional[dt.datetime] = None) -> bool:
    """Postpone this hour's check-in; False when the allowed number of snoozes is used up (then it is forced)."""
    now = now or now_utc()
    cfg, sn = config(db), db.get_setting(SNOOZE, {})
    n = sn.get("n", 0) if sn.get("hour") == h.isoformat() else 0
    if n >= cfg["max_snooze"]:
        return False
    db.set_setting(SNOOZE, {"hour": h.isoformat(), "n": n + 1, "until": (now + dt.timedelta(minutes=cfg["snooze_min"])).isoformat()})
    return True


def snoozes_left(db: Database, h: dt.datetime) -> int:
    sn = db.get_setting(SNOOZE, {})
    return max(0, config(db)["max_snooze"] - (sn.get("n", 0) if sn.get("hour") == h.isoformat() else 0))


def past_report(db: Database, h: dt.datetime, now: Optional[dt.datetime] = None, ledger: Optional[Ledger] = None) -> Dict[str, Any]:
    """Everything the 'last hour' half needs: measurement + suggested entry + the blocks you planned for that hour."""
    now = now or now_utc()
    led = ledger or Ledger(db, lambda: now)
    prev = h - dt.timedelta(hours=1)
    rep = led.hour(prev, now)
    sug = led.suggest(rep, now) if rep["unlogged_sec"] >= 60 else None
    planned = [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE source='checkin' AND status='planned' AND start_utc>=? AND start_utc<?", (prev.isoformat(), h.isoformat()))]
    return {"hour": prev, "report": rep, "suggestion": sug, "planned": planned, "needs_answer": rep["unlogged_sec"] >= config(db)["min_unlogged_min"] * 60 or bool(planned)}


def next_hour_candidates(db: Database, h: dt.datetime, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Ideas for the coming hour: slipped work worth doing now, today's tasks, the thing you were just doing, and meetings that are coming up."""
    now = now or now_utc()
    cands: List[Dict[str, Any]] = []
    seen = set()
    for it in catchup.scan(db, now)["items"][:6]:
        if it["id"] not in seen:
            seen.add(it["id"]); cands.append({"id": it["id"], "title": it["title"], "minutes": min(it["est_min"], 60), "why": tr("عقب‌افتاده", "slipped"), "project_id": it["project_id"]})
    lo, hi = h, h + dt.timedelta(days=1)
    for r in db.conn.execute("SELECT * FROM entries WHERE status='planned' AND column NOT IN ('done','cancelled') AND due_utc>=? AND due_utc<? AND source NOT IN ('auto','prompt','quick') ORDER BY priority", (lo.isoformat(), hi.isoformat())):
        e = TimeEntry.from_row(r)
        if e.id not in seen:
            seen.add(e.id); cands.append({"id": e.id, "title": e.title, "minutes": min(e.estimated_min or 30, 60), "why": tr("موعد امروز", "due today"), "project_id": e.project_id})
    last = db.conn.execute("SELECT * FROM entries WHERE status='done' AND source!='auto' ORDER BY end_utc DESC LIMIT 1").fetchone()
    if last is not None:
        e = TimeEntry.from_row(last)
        cands.append({"id": None, "title": e.title, "minutes": 30, "why": tr("ادامه‌ی کار قبلی", "continue"), "project_id": e.project_id})
    events = [o for o in ce.occurrences(db, h, h + dt.timedelta(hours=3)) if o["end"] > now]
    return {"candidates": cands[:8], "events": events[:3]}


def needs_break(db: Database, h: dt.datetime, now: Optional[dt.datetime] = None) -> int:
    """Minutes worked without a real break, when it exceeds the limit (0 otherwise): consecutive previous hours with at least 50 engaged minutes."""
    now = now or now_utc()
    led, run, k = Ledger(db, lambda: now), 0, 1
    while k <= 6:
        rep = led.hour(h - dt.timedelta(hours=k), now)
        if rep["engaged_sec"] < 50 * 60:
            break
        run += 60; k += 1
    return run if run >= config(db)["break_after_min"] else 0


def _slot(h: dt.datetime, offset_min: int, minutes: int) -> tuple:
    s = h + dt.timedelta(minutes=offset_min)
    return s, s + dt.timedelta(minutes=minutes)


def submit(db: Database, h: dt.datetime, *, done_ids: Optional[List[str]] = None, carry_ids: Optional[List[str]] = None, logged: Optional[Dict[str, Any]] = None, away: bool = False,
           picked: Optional[List[Dict[str, Any]]] = None, new_plans: Optional[List[Dict[str, Any]]] = None, free_hour: bool = False, add_break: bool = False,
           now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Apply an answered check-in in one transaction. Rules: the hour that just passed must be accounted for (logged, ticked, away, or nothing unlogged) and the next hour needs a plan (or
    'free hour')."""
    now = now or now_utc()
    cfg = config(db)
    pr = past_report(db, h, now)
    if cfg["mode"] in ("both", "past") and pr["needs_answer"] and not (away or logged or done_ids or carry_ids):
        raise CheckinError(tr("بگو در ساعت قبل چه کرده‌ای (یا بنویس نبودی)", "Say what you did last hour (or that you were away)"))
    picked, new_plans = picked or [], new_plans or []
    if cfg["mode"] in ("both", "future") and not (picked or new_plans or free_hour or add_break):
        raise CheckinError(tr("برای ساعت بعد یک برنامه بنویس (یا «ساعت آزاد» را بزن)", "Plan the next hour (or tick 'free hour')"))
    out = {"logged": 0, "done": 0, "carried": 0, "planned": 0, "away": away}
    with db.transaction():
        if logged and logged.get("title", "").strip():
            mins = max(1, int(logged.get("minutes", 30)))
            start = logged.get("start") or (pr["hour"] + dt.timedelta(minutes=0))
            proj = db.get(Project, logged["project_id"]) if logged.get("project_id") else None
            e = TimeEntry(title=logged["title"].strip()[:200], start_utc=start, end_utc=start + dt.timedelta(minutes=mins), project_id=logged.get("project_id"), source="prompt", billable=bool(proj and proj.client_id))
            db.save(e); out["logged"] = 1
        for i in done_ids or []:
            t = db.get(TimeEntry, i)
            if t is not None:
                t.status, t.column, t.completed_at, t.progress = Status.DONE, "done", now, 100
                db.save(t); out["done"] += 1
        offset = 0
        for i in carry_ids or []:
            t = db.get(TimeEntry, i)
            if t is not None:
                m = max(15, int((t.end_utc - t.start_utc).total_seconds() // 60) if t.end_utc else cfg["default_plan_min"])
                t.start_utc, t.end_utc = _slot(h, offset, m); t.extra = {**t.extra, "postponed": int(t.extra.get("postponed", 0)) + 1, "checkin": h.isoformat()}
                db.save(t, touch=False); offset += m; out["carried"] += 1
        for p in picked:
            m = int(p.get("minutes") or cfg["default_plan_min"])
            if p.get("id"):
                t = db.get(TimeEntry, p["id"])
                if t is None:
                    continue
                t.start_utc, t.end_utc = _slot(h, offset, m); t.status = Status.PLANNED; t.estimated_min = t.estimated_min or m; t.extra = {**t.extra, "checkin": h.isoformat()}
                db.save(t, touch=False)
            else:
                s, e_ = _slot(h, offset, m)
                db.save(TimeEntry(title=p["title"][:200], start_utc=s, end_utc=e_, status=Status.PLANNED, column="backlog", project_id=p.get("project_id"), estimated_min=m, source="checkin", extra={"checkin": h.isoformat()}))
            offset += m; out["planned"] += 1
        for p in new_plans:
            title = (p.get("title") or "").strip()
            if not title:
                continue
            m = int(p.get("minutes") or cfg["default_plan_min"])
            s, e_ = _slot(h, offset, m)
            db.save(TimeEntry(title=title[:200], start_utc=s, end_utc=e_, status=Status.PLANNED, column="backlog", project_id=p.get("project_id"), estimated_min=m, source="checkin", extra={"checkin": h.isoformat()}))
            offset += m; out["planned"] += 1
        if add_break:
            s, e_ = _slot(h, offset, cfg["break_min"])
            db.save(TimeEntry(title=tr("استراحت", "Break"), start_utc=s, end_utc=e_, status=Status.PLANNED, column="backlog", source="checkin", extra={"checkin": h.isoformat(), "break": True}))
            out["planned"] += 1
    Ledger(db, lambda: now).mark_answered(pr["hour"], "away" if away else ("logged" if out["logged"] or out["done"] else "checkin"), now)
    ans = db.get_setting(ANSWERED, {})
    ans[h.isoformat()] = {"at": now.isoformat(), **{k: v for k, v in out.items() if k != "away"}, "away": away, "free": free_hour}
    cutoff = (now - dt.timedelta(days=10)).isoformat()
    db.set_setting(ANSWERED, {k: v for k, v in ans.items() if k >= cutoff})
    db.set_setting(SNOOZE, {})
    return out


def streak(db: Database, now: Optional[dt.datetime] = None) -> int:
    """Consecutive answered check-ins (quiet hours in between do not break it: gaps of up to 3 hours are tolerated)."""
    hours = sorted((dt.datetime.fromisoformat(k) for k in db.get_setting(ANSWERED, {})), reverse=True)
    n, prev = 0, None
    for x in hours:
        if prev is not None and (prev - x) > dt.timedelta(hours=3):
            break
        n += 1; prev = x
    return n


def stats(db: Database, now: Optional[dt.datetime] = None, days: int = 7) -> Dict[str, Any]:
    """Check-ins answered and how much of what you planned you really did."""
    now = now or now_utc()
    cutoff = (now - dt.timedelta(days=days)).isoformat()
    answered = [k for k in db.get_setting(ANSWERED, {}) if k >= cutoff]
    planned = [TimeEntry.from_row(r) for r in db.conn.execute("SELECT * FROM entries WHERE source='checkin' AND start_utc>=?", (cutoff,))]
    kept = sum(1 for e in planned if e.status == Status.DONE)
    return {"answered": len(answered), "planned_blocks": len(planned), "kept": kept, "follow_through_pct": round(100 * kept / len(planned)) if planned else None, "streak": streak(db, now)}
