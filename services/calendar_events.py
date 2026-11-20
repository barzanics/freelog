"""Calendar events: appointments, meetings, calls, recurring webinars - with reminders that say the *day* a day before and the *hour* two hours before, a safe join link and an
optional auto-open at the start. Recurrence is expanded on the fly (wall-clock time is kept across daylight-saving changes); one occurrence can be moved or skipped on its own."""
from __future__ import annotations

import datetime as dt
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from ..core.crm import Store
from ..core.database import Database
from ..core.persian import TEHRAN, UTC, now_utc, parse_jalali, to_en_digits, to_tehran, tr

KINDS = ("event", "meeting", "webinar", "call", "deadline", "reminder")
DEFAULT_REMINDERS = (1440, 120, 15, 0)                      # a day before, two hours before, 15 minutes before, at the start
MAX_OFFSET = 60 * 24 * 30
FIRED_KEY = "event_reminders_fired"
WEEKDAYS = {"mon": 0, "monday": 0, "tue": 1, "tuesday": 1, "wed": 2, "wednesday": 2, "thu": 3, "thursday": 3, "fri": 4, "friday": 4, "sat": 5, "saturday": 5, "sun": 6, "sunday": 6,
            "دوشنبه": 0, "سه‌شنبه": 1, "سهشنبه": 1, "چهارشنبه": 2, "پنجشنبه": 3, "جمعه": 4, "شنبه": 5, "یکشنبه": 6}


class EventError(ValueError):
    """Invalid event (message is user-facing)."""


def safe_link(url: str) -> str:
    """Only plain http(s) links with a host are accepted - never javascript:, file:, data: ... because the app can open this link for you automatically."""
    u = (url or "").strip()
    if not u:
        return ""
    p = urllib.parse.urlparse(u)
    if p.scheme.lower() not in ("http", "https") or not p.netloc or len(u) > 1000 or re.search(r"[\s\x00-\x1f]", u):
        raise EventError(tr("پیوند باید یک آدرس http یا https معتبر باشد", "The link must be a valid http or https address"))
    return u


def _norm_reminders(r: Any) -> List[int]:
    try:
        out = sorted({int(x) for x in (r if r is not None else DEFAULT_REMINDERS)}, reverse=True)
    except (TypeError, ValueError) as exc:
        raise EventError("Invalid reminders") from exc
    if any(x < 0 or x > MAX_OFFSET for x in out):
        raise EventError(tr("زمان یادآور نامعتبر است", "Invalid reminder time"))
    return out


def _norm_rule(r: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not r or not r.get("type"):
        return {}
    t = r["type"]
    if t not in ("daily", "weekly", "monthly"):
        raise EventError("Unknown recurrence")
    out: Dict[str, Any] = {"type": t, "interval": max(1, int(r.get("interval", 1)))}
    if t == "weekly":
        out["weekdays"] = sorted({int(x) for x in r.get("weekdays", [])}) or []
        if any(not 0 <= x <= 6 for x in out["weekdays"]):
            raise EventError("Invalid weekdays")
    if r.get("until"):
        out["until"] = str(r["until"])[:10]
    if r.get("count"):
        out["count"] = max(1, int(r["count"]))
    return out


def add_event(db: Database, title: str, start: dt.datetime, end: Optional[dt.datetime] = None, kind: str = "event", **f: Any) -> Dict[str, Any]:
    title = (title or "").strip()
    if not title:
        raise EventError(tr("عنوان را وارد کنید", "Enter a title"))
    if kind not in KINDS:
        raise EventError("Unknown kind")
    end = end or start + dt.timedelta(minutes=60)
    if end <= start:
        raise EventError(tr("پایان باید بعد از شروع باشد", "The end must be after the start"))
    now = now_utc()
    row = dict(title=title[:200], kind=kind, start_utc=start.astimezone(UTC), end_utc=end.astimezone(UTC), all_day=int(bool(f.get("all_day"))), project_id=f.get("project_id"), client_id=f.get("client_id"),
               location=(f.get("location") or "")[:300], link=safe_link(f.get("link", "")), notes=(f.get("notes") or "")[:4000], reminders=_norm_reminders(f.get("reminders")),
               recurrence=_norm_rule(f.get("recurrence")), exdates=[], auto_open=int(bool(f.get("auto_open"))), color=f.get("color") or "", status="confirmed", created_at=now, updated_at=now)
    if row["auto_open"] and not row["link"]:
        raise EventError(tr("برای باز شدن خودکار، پیوند لازم است", "Auto-open needs a link"))
    return Store(db).add("events", **row)


def get_event(db: Database, event_id: str) -> Dict[str, Any]:
    e = Store(db).get("events", event_id)
    if e is None:
        raise KeyError(event_id)
    return e


def update_event(db: Database, event_id: str, **f: Any) -> Dict[str, Any]:
    cur = get_event(db, event_id)
    allowed = {"title", "kind", "start_utc", "end_utc", "all_day", "project_id", "client_id", "location", "link", "notes", "reminders", "recurrence", "auto_open", "color", "status"}
    bad = set(f) - allowed
    if bad:
        raise EventError(f"Cannot set {sorted(bad)}")
    if "link" in f:
        f["link"] = safe_link(f["link"])
    if "reminders" in f:
        f["reminders"] = _norm_reminders(f["reminders"])
    if "recurrence" in f:
        f["recurrence"] = _norm_rule(f["recurrence"])
    if "kind" in f and f["kind"] not in KINDS:
        raise EventError("Unknown kind")
    s, e = f.get("start_utc", dt.datetime.fromisoformat(cur["start_utc"])), f.get("end_utc", dt.datetime.fromisoformat(cur["end_utc"]))
    if isinstance(s, str): s = dt.datetime.fromisoformat(s)
    if isinstance(e, str): e = dt.datetime.fromisoformat(e)
    if e <= s:
        raise EventError(tr("پایان باید بعد از شروع باشد", "The end must be after the start"))
    f["updated_at"] = now_utc()
    if (f.get("auto_open", cur["auto_open"])) and not f.get("link", cur["link"]):
        raise EventError(tr("برای باز شدن خودکار، پیوند لازم است", "Auto-open needs a link"))
    return Store(db).update("events", event_id, **f)


def delete_event(db: Database, event_id: str) -> bool:
    return Store(db).delete("events", event_id)


# ------------------------------------------------------------------ recurrence
def _local(t: dt.datetime) -> dt.datetime:
    return to_tehran(t)


def _expand(ev: Dict[str, Any], lo: dt.datetime, hi: dt.datetime) -> List[Tuple[dt.datetime, dt.datetime]]:
    s, e = dt.datetime.fromisoformat(ev["start_utc"]), dt.datetime.fromisoformat(ev["end_utc"])
    rule, dur = ev.get("recurrence") or {}, e - s
    if not rule:
        return [(s, e)] if s < hi and e > lo else []
    out: List[Tuple[dt.datetime, dt.datetime]] = []
    ls = _local(s)
    until = dt.date.fromisoformat(rule["until"]) if rule.get("until") else None
    n_max = int(rule.get("count", 10 ** 6))
    step = int(rule.get("interval", 1))
    produced, day, guard = 0, ls.date(), 0
    t = rule["type"]
    weekdays = rule.get("weekdays") or [ls.weekday()]
    week0 = ls.date() - dt.timedelta(days=ls.weekday())
    while guard < 4000:
        guard += 1
        if t == "daily":
            cand = [day]; day += dt.timedelta(days=step)
        elif t == "weekly":
            cand = [week0 + dt.timedelta(days=w) for w in weekdays]; week0 += dt.timedelta(weeks=step)
        else:
            m = ls.month - 1 + (guard - 1) * step
            y, mo = ls.year + m // 12, m % 12 + 1
            try:
                cand = [dt.date(y, mo, ls.day)]
            except ValueError:
                cand = []
        for d in cand:
            if d < ls.date():
                continue
            if until and d > until:
                return out
            start = dt.datetime.combine(d, ls.timetz().replace(tzinfo=None), tzinfo=TEHRAN).astimezone(UTC)
            produced += 1
            if produced > n_max:
                return out
            if start < hi and start + dur > lo:
                out.append((start, start + dur))
        first = min(cand) if cand else None
        if (first and dt.datetime.combine(first, dt.time(), tzinfo=TEHRAN).astimezone(UTC) > hi) or (t == "monthly" and guard > 600):
            return out
    return out


def occurrences(db: Database, start: dt.datetime, end: dt.datetime, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every occurrence overlapping [start, end): single events and the expanded recurring ones (skipped dates removed)."""
    out = []
    for ev in Store(db).rows("events", "status!='cancelled'" + (" AND project_id=?" if project_id else ""), (project_id,) if project_id else (), "start_utc"):
        ex = set(ev.get("exdates") or [])
        for s, e in _expand(ev, start.astimezone(UTC), end.astimezone(UTC)):
            if s.isoformat() in ex:
                continue
            out.append({"event_id": ev["id"], "occ_id": f"{ev['id']}@{s.isoformat()}", "title": ev["title"], "kind": ev["kind"], "start": s, "end": e, "all_day": bool(ev["all_day"]), "link": ev["link"],
                        "project_id": ev["project_id"], "color": ev["color"], "location": ev["location"], "recurring": bool(ev.get("recurrence")), "auto_open": bool(ev["auto_open"]),
                        "reminders": ev["reminders"]})
    return sorted(out, key=lambda o: o["start"])


def move_occurrence(db: Database, event_id: str, occ_start: dt.datetime, new_start: dt.datetime, new_end: dt.datetime, scope: str = "this") -> Dict[str, Any]:
    """Drag / resize. Non-recurring: just move. Recurring + ``all``: shift the whole series. Recurring + ``this``: skip this date and create a one-off at the new time."""
    ev = get_event(db, event_id)
    if new_end <= new_start:
        raise EventError(tr("پایان باید بعد از شروع باشد", "The end must be after the start"))
    if not ev.get("recurrence"):
        return update_event(db, event_id, start_utc=new_start.astimezone(UTC), end_utc=new_end.astimezone(UTC))
    if scope == "all":
        delta = new_start - occ_start
        base_s = dt.datetime.fromisoformat(ev["start_utc"])
        return update_event(db, event_id, start_utc=(base_s + delta).astimezone(UTC), end_utc=(base_s + delta + (new_end - new_start)).astimezone(UTC))
    ex = list(ev.get("exdates") or []) + [occ_start.astimezone(UTC).isoformat()]
    Store(db).update("events", event_id, exdates=ex, updated_at=now_utc())
    return add_event(db, ev["title"], new_start, new_end, ev["kind"], project_id=ev["project_id"], client_id=ev["client_id"], location=ev["location"], link=ev["link"], notes=ev["notes"],
                     reminders=ev["reminders"], auto_open=bool(ev["auto_open"]), color=ev["color"])


def skip_occurrence(db: Database, event_id: str, occ_start: dt.datetime) -> None:
    ev = get_event(db, event_id)
    if not ev.get("recurrence"):
        delete_event(db, event_id); return
    Store(db).update("events", event_id, exdates=list(ev.get("exdates") or []) + [occ_start.astimezone(UTC).isoformat()])


# ------------------------------------------------------------------ reminders
def reminder_text(title: str, start: dt.datetime, minutes_before: int, now: Optional[dt.datetime] = None) -> Tuple[str, str]:
    """(kind, text). A day before says the DAY ("Tomorrow ... Tue, Nov 17 at 15:00"), two hours before says the HOUR ("In 2 hours ... at 15:00")."""
    from ..reports import locale_us as us
    ls = _local(start)
    hhmm = ls.strftime("%H:%M")
    if minutes_before >= 1440:
        d = (ls.date() - _local(now or now_utc()).date()).days
        when = tr("فردا", "Tomorrow") if d == 1 else (tr("امروز", "Today") if d == 0 else tr(f"{d} روز دیگر", f"In {d} days"))
        from ..core.persian import format_jalali
        return "day", f"{when}: {title} — {format_jalali(ls.date(), '{weekday} {d} {month_name}', fa_digits=False) if True else ''} {tr('ساعت', 'at')} {hhmm}"
    if minutes_before >= 60:
        h = minutes_before // 60
        return "hours", tr(f"{h} ساعت دیگر: {title} — ساعت {hhmm}", f"In {h} hour{'s' if h != 1 else ''}: {title} — at {hhmm}")
    if minutes_before > 0:
        return "minutes", tr(f"{minutes_before} دقیقه دیگر شروع می‌شود: {title}", f"Starting in {minutes_before} minutes: {title}")
    return "start", tr(f"همین الان شروع شد: {title}", f"Starting now: {title}")


def due_reminders(db: Database, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    """Reminders whose moment has come and were not shown yet. A reminder missed while the app was closed still appears once (up to a few hours late for 'a day before')."""
    now = now or now_utc()
    fired = set(db.get_setting(FIRED_KEY, []))
    out: List[Dict[str, Any]] = []
    for occ in occurrences(db, now - dt.timedelta(hours=1), now + dt.timedelta(days=MAX_OFFSET // 1440 + 1)):
        for m in occ["reminders"]:
            key = f"{occ['occ_id']}:{m}"
            when = occ["start"] - dt.timedelta(minutes=m)
            grace = dt.timedelta(hours=6) if m >= 1440 else (dt.timedelta(minutes=45) if m >= 60 else dt.timedelta(minutes=10))
            if when <= now < when + grace and now < occ["end"] and key not in fired:
                kind, text = reminder_text(occ["title"], occ["start"], m, now)
                out.append({"key": key, "occ": occ, "minutes_before": m, "kind": kind, "text": text, "link": occ["link"], "auto_open": occ["auto_open"] and m == 0})
    return sorted(out, key=lambda r: (r["occ"]["start"], -r["minutes_before"]))


def mark_fired(db: Database, items: List[Dict[str, Any]], now: Optional[dt.datetime] = None) -> None:
    fired = list(db.get_setting(FIRED_KEY, []))
    fired += [i["key"] for i in items]
    db.set_setting(FIRED_KEY, fired[-600:])


def upcoming(db: Database, now: Optional[dt.datetime] = None, limit: int = 5, days: int = 14) -> List[Dict[str, Any]]:
    now = now or now_utc()
    return [o for o in occurrences(db, now, now + dt.timedelta(days=days)) if o["end"] > now][:limit]


# ------------------------------------------------------------------ quick text -> event
_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_DUR = re.compile(r"(?<![\w:])(?:(\d+(?:\.\d+)?)h(?:(\d+)m?)?|(\d+)\s?(?:m|min|mins|minutes|دقیقه))(?![\w:])", re.IGNORECASE)
_TIME = re.compile(r"(?<![\d:/-])(\d{1,2})(?::(\d{2}))?\s?(am|pm|AM|PM)?(?![\d/-])")
_REMIND = re.compile(r"(?:remind|یادآوری)\s+([0-9dhmwDHMW,\s]+)", re.IGNORECASE)


def _offsets(s: str) -> List[int]:
    out = []
    for n, u in re.findall(r"(\d+)\s*([dhmw])", s.lower()):
        out.append(int(n) * {"w": 10080, "d": 1440, "h": 60, "m": 1}[u])
    return out


def parse_quick(text: str, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """"Call with Acme tomorrow 15:00 1h https://meet.example/x @Site remind 1d,2h" -> a ready event. Understands English and Persian words; ``every <weekday>`` makes it weekly."""
    now = now or now_utc()
    local = _local(now)
    t = to_en_digits(text.replace("،", ","))
    res: Dict[str, Any] = {"kind": "event", "link": "", "project": None, "reminders": None, "recurrence": None}
    m = _URL.search(t)
    if m:
        res["link"] = m.group(0).rstrip(".,)"); t = t.replace(m.group(0), " ")
    m = _REMIND.search(t)
    if m:
        res["reminders"] = sorted(set(_offsets(m.group(1))), reverse=True) or None; t = t.replace(m.group(0), " ")
    pm = re.search(r"@(\S+)", t)
    if pm:
        res["project"] = pm.group(1); t = t.replace(pm.group(0), " ")
    low = t.lower()
    if re.search(r"webinar|وبینار", low): res["kind"] = "webinar"
    elif re.search(r"meeting|call|جلسه|قرار|تماس", low): res["kind"] = "meeting"
    minutes = 0
    dm = _DUR.search(t)
    if dm:
        minutes = round(float(dm.group(1) or 0) * 60) + int(dm.group(2) or dm.group(3) or 0); t = t.replace(dm.group(0), " ")
    date: Optional[dt.date] = None
    rec_day: Optional[int] = None
    em = re.search(r"(?:every|هر)\s+(\S+)", t, re.IGNORECASE)
    if em:
        w = em.group(1).lower().strip(",.")
        if w in WEEKDAYS:
            rec_day = WEEKDAYS[w]; res["recurrence"] = {"type": "weekly", "interval": 1, "weekdays": [rec_day]}; t = t.replace(em.group(0), " ")
        elif w in ("day", "روز"):
            res["recurrence"] = {"type": "daily", "interval": 1}; t = t.replace(em.group(0), " ")
    for word, fn in (("daily", lambda: {"type": "daily", "interval": 1}), ("weekly", lambda: {"type": "weekly", "interval": 1, "weekdays": []}), ("monthly", lambda: {"type": "monthly", "interval": 1}),
                     ("هفتگی", lambda: {"type": "weekly", "interval": 1, "weekdays": []}), ("ماهانه", lambda: {"type": "monthly", "interval": 1}), ("روزانه", lambda: {"type": "daily", "interval": 1})):
        if res["recurrence"] is None and re.search(rf"\b{word}\b" if word.isascii() else word, t, re.IGNORECASE):
            res["recurrence"] = fn(); t = re.sub(rf"\b{word}\b" if word.isascii() else word, " ", t, flags=re.IGNORECASE)
    dmatch = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if dmatch:
        y, mo, d = (int(x) for x in dmatch.groups())
        try:
            date = parse_jalali(f"{y}/{mo}/{d}") if y < 1700 else dt.date(y, mo, d)
        except ValueError as exc:
            raise EventError(tr("تاریخ نامعتبر است", "Invalid date")) from exc
        t = t.replace(dmatch.group(0), " ")
    for word, off in (("tomorrow", 1), ("فردا", 1), ("today", 0), ("امروز", 0), ("پس‌فردا", 2)):
        if date is None and re.search(rf"\b{word}\b" if word.isascii() else word, t, re.IGNORECASE):
            date = local.date() + dt.timedelta(days=off); t = re.sub(rf"\b{word}\b" if word.isascii() else word, " ", t, flags=re.IGNORECASE)
    nxt = bool(re.search(r"\bnext\b|بعدی", t, re.IGNORECASE))
    wd = None
    for w, i in sorted(WEEKDAYS.items(), key=lambda kv: -len(kv[0])):            # longest names first: "سه‌شنبه" before "شنبه"
        if re.search(rf"\b{w}\b" if w.isascii() else w, t, re.IGNORECASE):
            wd = i; t = re.sub(rf"\b{w}\b" if w.isascii() else w, " ", t, count=1, flags=re.IGNORECASE); break
    if wd is not None:
        t = re.sub(r"\bnext\b|بعدی", " ", t, flags=re.IGNORECASE)
    if date is None and wd is not None:
        ahead = (wd - local.weekday()) % 7
        date = local.date() + dt.timedelta(days=ahead if ahead else (7 if nxt else 0))       # "Tuesday" on a Tuesday means today, "next Tuesday" a week later
    sh = None
    for cand in _TIME.finditer(t):
        h, mi, ap = int(cand.group(1)), int(cand.group(2) or 0), (cand.group(3) or "").lower()
        if cand.group(2) is None and not ap and "ساعت" not in t and not re.search(r"\bat\s*" + cand.group(1), t, re.IGNORECASE):
            continue                                                         # a bare number is part of the title, not a time
        if ap == "pm" and h < 12: h += 12
        if ap == "am" and h == 12: h = 0
        if 0 <= h <= 23 and 0 <= mi <= 59:
            sh = (h, mi); t = t.replace(cand.group(0), " ", 1); break
    t = re.sub(r"\b(at|on|with the|the)\b\s*$", "", re.sub(r"(?:ساعت|\bat\b)", " ", t, flags=re.IGNORECASE)).strip()
    title = re.sub(r"\s+", " ", re.sub(r"#\S+", " ", t)).strip(" ,-—:")
    if not title:
        raise EventError(tr("عنوان را بنویس", "Write a title"))
    if sh is None:
        sh = (9, 0) if date is not None else (local.hour + 1 if local.hour < 22 else 23, 0)
    if date is None:
        date = local.date()
        if dt.datetime.combine(date, dt.time(*sh), tzinfo=TEHRAN) <= local:
            date += dt.timedelta(days=1)
    if rec_day is not None and res["recurrence"]:
        date = date if date.weekday() == rec_day else date + dt.timedelta(days=(rec_day - date.weekday()) % 7)
    start = dt.datetime.combine(date, dt.time(*sh), tzinfo=TEHRAN).astimezone(UTC)
    res.update(title=title, start=start, end=start + dt.timedelta(minutes=minutes or (60 if res["kind"] != "reminder" else 15)))
    if res["recurrence"] and res["recurrence"].get("type") == "weekly" and not res["recurrence"].get("weekdays"):
        res["recurrence"]["weekdays"] = [to_tehran(start).weekday()]
    if res["link"]:
        res["link"] = safe_link(res["link"])
    return res
