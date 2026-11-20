"""Report data builders (daily / weekly / milestone / invoice / snapshot). Pure functions: database in, JSON-safe dict out - no HTML, no UI.

Privacy first: what a client may see is decided in ONE place (``visible``): billable entries and entries you flagged ``visible_to_client`` - never entries tagged ``internal`` -
and only the *client note* of a task is ever shown, never your internal notes or description.
"""
from __future__ import annotations

import base64
import datetime as dt
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from ..core.crm import Store
from ..core.database import Database
from ..core.models import Client, Project, Status, TimeEntry
from ..core.persian import UTC, now_utc
from ..services import client_ops as ops, project_health as ph
from . import digest, locale_us as us

KINDS = ("daily", "weekly", "milestone", "invoice", "snapshot")
PREFIX = {"daily": "DD", "weekly": "WR", "milestone": "MR", "invoice": "INV", "snapshot": "SN"}
CHARTS = {"daily": [], "weekly": ["burnup", "donut", "trend", "heatmap"], "milestone": ["gantt"], "invoice": [], "snapshot": ["gantt", "burndown", "donut", "velocity"]}


class ReportError(ValueError):
    """The report cannot be built (message is user-facing)."""


# ------------------------------------------------------------------ settings & profile
def company_profile(db: Database) -> Dict[str, Any]:
    g = db.get_setting
    return {"name": g("company_name", "") or g("author_name", "") or "barzanics", "email": g("company_email", ""), "phone": g("company_phone", ""), "website": g("company_website", ""),
            "tax_id": g("company_tax_id", ""), "terms_url": g("terms_url", ""), "signature": g("author_name", "") or g("company_name", ""), "logo": _logo_uri(g("company_logo", "")),
            "payment_instructions": g("payment_instructions", "")}


def _logo_uri(path: str) -> Optional[str]:
    try:
        p = Path(path) if path else None
        if not p or not p.is_file() or p.stat().st_size > 300_000:
            return None
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}.get(p.suffix.lower())
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}" if mime else None
    except OSError:
        return None


def client_prefs(db: Database, client_id: Optional[str]) -> Dict[str, Any]:
    c = (Store(db).get("clients", client_id) if client_id else None) or {}
    s = dict(c.get("settings") or {})
    return {"name": c.get("name", ""), "company": c.get("company", ""), "contact": c.get("contact_name", "") or c.get("name", ""), "email": c.get("email", ""), "tz": c.get("timezone") or "America/New_York",
            "country": c.get("country") or "US", "currency": c.get("currency") or "USD", "rate": float(c.get("default_rate") or 0), "billing_model": c.get("billing_model") or "hourly",
            "rounding_min": int(c.get("rounding_min") or 0), "logo": _logo_uri(c.get("logo_path", "")), "tone": s.get("tone", "we"), "week_start": s.get("week_start", "sun"),
            "terms_days": int(s.get("terms_days", 15)), "tax_percent": float(s.get("tax_percent", 0)), "visibility": s.get("visibility", "billable"), "show_scope": bool(s.get("show_scope", False))}


# ------------------------------------------------------------------ time helpers
def round_seconds(sec: int, step_min: int, mode: str = "up") -> int:
    """Round one entry's duration to the client's billing increment (6 / 15 minutes ...). ``up`` is the usual professional rule."""
    if step_min <= 0 or sec <= 0:
        return sec
    step = step_min * 60
    return (math.ceil(sec / step) if mode == "up" else round(sec / step)) * step


def window(start: dt.date, end: dt.date, tz: str) -> Tuple[dt.datetime, dt.datetime]:
    z = ZoneInfo(tz)
    return (dt.datetime.combine(start, dt.time(), tzinfo=z).astimezone(UTC), dt.datetime.combine(end + dt.timedelta(days=1), dt.time(), tzinfo=z).astimezone(UTC))


def period_for(kind: str, now: dt.datetime, prefs: Dict[str, Any], project: Project, start: Optional[dt.date], end: Optional[dt.date]) -> Tuple[dt.date, dt.date]:
    today = us.to_client_tz(now, prefs["tz"]).date()
    if start and end:
        return start, end
    if kind == "daily":
        return today, today
    if kind == "weekly":
        return us.week_bounds(today, prefs["week_start"])
    if kind == "invoice":
        first = today.replace(day=1)
        prev_end = first - dt.timedelta(days=1)
        return prev_end.replace(day=1), prev_end
    p0 = us.to_client_tz(project.start, prefs["tz"]).date() if project.start else today - dt.timedelta(days=90)
    return p0, today


def _entry_meta(db: Database, pid: str) -> Dict[str, Tuple[int, str]]:
    return {r[0]: (r[1] or 0, r[2] or "") for r in db.conn.execute("SELECT id, visible_to_client, client_note FROM entries WHERE project_id=?", (pid,))}


def visible(e: TimeEntry, meta: Dict[str, Tuple[int, str]], policy: str = "billable") -> bool:
    """The single privacy gate for client-facing output."""
    if policy == "all":
        return True
    if "internal" in {t.lower() for t in e.tags}:
        return False
    flagged = bool(meta.get(e.id, (0, ""))[0])
    return flagged if policy == "flagged" else (flagged or e.billable)


def _chunks(e: TimeEntry, lo: dt.datetime, hi: dt.datetime, tz: str) -> List[Tuple[dt.date, int]]:
    """(local date, seconds) pieces of a finished entry inside [lo, hi); an entry crossing local midnight is split."""
    if e.status != Status.DONE or e.duration_sec <= 0:
        return []
    z = ZoneInfo(tz)
    a, b = max(e.start_utc, lo), min(e.end_utc or e.start_utc + dt.timedelta(seconds=e.duration_sec), hi)
    out, cur = [], a
    while cur < b:
        local = cur.astimezone(z)
        nxt = min(b, (dt.datetime.combine(local.date() + dt.timedelta(days=1), dt.time(), tzinfo=z)).astimezone(UTC))
        out.append((local.date(), int((nxt - cur).total_seconds())))
        cur = nxt
    return out


def _iso(d: Any) -> Any:
    return d.isoformat() if isinstance(d, (dt.date, dt.datetime)) else d


def number_for(db: Database, kind: str, on: dt.date) -> str:
    n = db.conn.execute("SELECT COUNT(*) FROM client_reports WHERE type=? AND generated_at LIKE ?", (kind, f"{on.isoformat()}%")).fetchone()[0] + 1
    return f"{PREFIX[kind]}-{on:%Y%m%d}-{n:02d}"


# ------------------------------------------------------------------ the builder
def build(db: Database, project_id: str, kind: str = "weekly", start: Optional[dt.date] = None, end: Optional[dt.date] = None, now: Optional[dt.datetime] = None,
          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if kind not in KINDS:
        raise ReportError(f"Unknown report type: {kind}")
    p = db.get(Project, project_id)
    if p is None:
        raise KeyError(project_id)
    opts = dict(options or {})
    now = now or now_utc()
    prefs = client_prefs(db, p.client_id)
    policy = opts.get("visibility", prefs["visibility"])
    tz = prefs["tz"]
    a, b = period_for(kind, now, prefs, p, start, end)
    if b < a:
        raise ReportError("The period ends before it starts")
    lo, hi = window(a, b, tz)
    span = (b - a).days + 1
    plo, phi = window(a - dt.timedelta(days=span), a - dt.timedelta(days=1), tz)
    meta = _entry_meta(db, project_id)
    tasks = ph.project_tasks(db, project_id)
    vis = [t for t in tasks if visible(t, meta, policy)]
    today = us.to_client_tz(now, tz).date()

    def time_in(lo_: dt.datetime, hi_: dt.datetime) -> Tuple[int, int, Dict[dt.date, List[int]], Dict[str, List[Any]]]:
        bill = nonb = 0
        by_day: Dict[dt.date, List[int]] = {}
        by_task: Dict[str, List[Any]] = {}
        for t in vis:
            for d, sec in _chunks(t, lo_, hi_, tz):
                s = round_seconds(sec, prefs["rounding_min"]) if (t.billable and kind == "invoice") else sec
                (bill if t.billable else nonb).__class__  # noqa: B018 - keep both counters ints
                if t.billable:
                    bill += s
                else:
                    nonb += s
                by_day.setdefault(d, [0, 0])[0 if t.billable else 1] += s
                row = by_task.setdefault(t.title, [0, t.billable])
                row[0] += s
        return bill, nonb, by_day, by_task

    bill, nonb, by_day, by_task = time_in(lo, hi)
    pbill, pnonb, _pd, _pt = time_in(plo, phi)
    prog = ph.weighted_progress(db, project_id)
    health = ph.health(db, project_id, now)
    done = [t for t in vis if not t.parent_id and ph.is_done(t) and t.completed_at and lo <= t.completed_at < hi]
    done_rows = [{"title": t.title, "completed_on": _iso(us.to_client_tz(t.completed_at, tz).date()), "hours": round(sum(s for _d, s in _chunks(t, lo, hi, tz)) / 3600, 2), "note": meta.get(t.id, (0, ""))[1]}
                 for t in sorted(done, key=lambda x: x.completed_at)]
    prog_rows = []
    for t in vis:
        if t.parent_id or ph.is_done(t) or t.column == "delayed":
            continue
        secs = sum(s for _d, s in _chunks(t, lo, hi, tz))
        if t.column == "in_progress" or t.status == Status.RUNNING or secs:
            kids = [k for k in tasks if k.parent_id == t.id]
            pct = round(100 * ph._frac(kids)) if kids else t.progress
            prog_rows.append({"title": t.title, "progress": pct, "eta": _iso(us.to_client_tz(t.due_utc, tz).date()) if t.due_utc else None, "hours": round(secs / 3600, 2), "note": meta.get(t.id, (0, ""))[1]})
    blk = ph.blockers(db, project_id, 3, now)
    waiting = [{"title": x["title"], "reason": x["reason"], "days": x["days"]} for x in blk if x["by"] == "client"]
    internal_blk = [{"title": x["title"], "reason": x["reason"], "days": x["days"]} for x in blk if x["by"] != "client"]
    nxt_lo, nxt_hi = window(today + dt.timedelta(days=1), today + dt.timedelta(days=7 if kind != "daily" else 1), tz)
    plan = [t for t in vis if not t.parent_id and not ph.is_done(t) and t.column not in ("delayed", "cancelled") and t.status != Status.RUNNING
            and ((t.status == Status.PLANNED and nxt_lo <= t.start_utc < nxt_hi) or (t.due_utc and nxt_lo <= t.due_utc < nxt_hi))]
    if not plan:
        plan = sorted((t for t in vis if not t.parent_id and not ph.is_done(t) and t.column not in ("delayed", "cancelled")), key=lambda t: (t.priority, t.rank))[:6]
    next_plan = [{"title": t.title, "due": _iso(us.to_client_tz(t.due_utc, tz).date()) if t.due_utc else None, "estimate_h": round((t.estimated_min or 0) / 60, 1)} for t in plan[:8]]
    store = Store(db)
    dels = [d for d in store.rows("deliverables", "project_id=? AND visible=1", (project_id,), "delivered_at")]
    pending = [d["title"] for d in dels if d["status"] == "pending"]
    commitments = [{"text": x["text"], "due": _iso(dt.datetime.fromisoformat(x["due"]).date()) if x["due"] else None} for x in ops.promises(db, p.client_id, "open")
                   if p.client_id and (not x["project_id"] or x["project_id"] == project_id)][:6]
    meetings = [{"at": _iso(us.to_client_tz(dt.datetime.fromisoformat(m["at"]), tz).date()), "minutes": m["minutes"], "summary": m["summary"], "actions": [i.get("text", "") for i in m["action_items"]]}
                for m in ops.meetings_between(db, project_id, lo, hi)] if p.client_id else []
    changes = [{"at": _iso(us.to_client_tz(dt.datetime.fromisoformat(c["at"]), tz).date()), "text": c["text"]} for c in ops.public_changes(db, project_id, lo, hi)]
    risks = [{"title": r["title"], "level": r["level"], "mitigation": r["mitigation"]} for r in ops.risk_register(db, project_id, only_visible=True)]
    fc = ph.forecast(db, project_id, now)
    scope = ph.scope_creep(db, project_id) if (prefs["show_scope"] or opts.get("include_scope")) else None
    decisions = [{"title": d["title"], "kind": "approval"} for d in dels if d["status"] == "pending"] + [{"title": t.title, "kind": "decision"} for t in vis if "decision" in {x.lower() for x in t.tags} and not ph.is_done(t)]
    comparison = [{"label": "Hours", "current": round((bill + nonb) / 3600, 1), "previous": round((pbill + pnonb) / 3600, 1)},
                  {"label": "Billable hours", "current": round(bill / 3600, 1), "previous": round(pbill / 3600, 1)},
                  {"label": "Tasks completed", "current": len(done), "previous": len([t for t in vis if not t.parent_id and ph.is_done(t) and t.completed_at and plo <= t.completed_at < phi])}]
    series = _series(db, p, vis, prog, by_task, meta, tz, now, today, plo)
    series["comparison"] = comparison
    c_company = company_profile(db)
    data: Dict[str, Any] = {
        "header": {"type": kind, "title": {"daily": "Daily Digest", "weekly": "Weekly Progress Report", "milestone": "Milestone Report", "invoice": "Invoice Summary", "snapshot": "Project Snapshot"}[kind],
                   "number": opts.get("number", number_for(db, kind, today)), "generated": _iso(today), "generated_label": us.fmt_date(today), "period_label": us.fmt_range(a, b), "company": c_company,
                   "client_logo": prefs["logo"]},
        "project": {"id": p.id, "name": p.name, "description": p.description, "status": p.status.value, "start": _iso(p.start.date()) if p.start else None, "deadline": _iso(p.deadline.date()) if p.deadline else None},
        "client": {"id": p.client_id, "name": prefs["name"], "company": prefs["company"], "contact": prefs["contact"], "email": prefs["email"], "tz": tz, "currency": prefs["currency"], "tone": prefs["tone"]},
        "period": {"start": _iso(a), "end": _iso(b), "days": span},
        "progress": prog, "health": health, "forecast": {**fc, "projected_date": _iso(fc["projected_date"]), "projected_label": us.fmt_date(fc["projected_date"]) if fc["projected_date"] else None},
        "time": {"total_sec": bill + nonb, "billable_sec": bill, "non_billable_sec": nonb, "billable_pct": round(100 * bill / (bill + nonb)) if bill + nonb else 0,
                 "by_day": [{"date": _iso(d), "label": us.fmt_date(d), "billable": v[0], "non_billable": v[1]} for d, v in sorted(by_day.items())],
                 "by_task": [{"title": k, "sec": v[0], "billable": v[1]} for k, v in sorted(by_task.items(), key=lambda kv: -kv[1][0])][:15]},
        "done": done_rows, "in_progress": prog_rows, "waiting_on_client": waiting, "blockers": internal_blk, "next_plan": next_plan,
        "deliverables": [{"title": d["title"], "kind": d["kind"], "ref": d["ref"], "status": d["status"], "delivered": _iso(dt.datetime.fromisoformat(d["delivered_at"]).date()) if d["delivered_at"] else None} for d in dels],
        "pending_approvals": pending, "decisions": decisions, "commitments": commitments, "meetings": meetings, "changes": changes, "risks": risks, "scope": scope,
        "holiday_warnings": [{"title": w["title"], "date": _iso(w["date"]), "why": w["why"]} for w in ph.holiday_warnings(db, project_id, tz)],
        "series": series, "charts": opts.get("charts", CHARTS[kind]), "invoice": None, "milestone": None, "options": {k: v for k, v in opts.items() if k not in ("summary",)},
    }
    if kind == "milestone":
        data["milestone"] = _milestone(db, project_id, opts.get("milestone_id"), tasks, meta, tz, policy)
    if kind == "invoice":
        data["invoice"] = _invoice(db, p, prefs, vis, lo, hi, tz, today, opts)
    data["comparison"] = comparison
    data["summary"] = opts.get("summary") or digest.template_digest(data, prefs["tone"])
    return data


def _series(db: Database, p: Project, vis: List[TimeEntry], prog: Dict[str, Any], by_task: Dict[str, List[Any]], meta: Dict[str, Any], tz: str, now: dt.datetime, today: dt.date, plo: dt.datetime) -> Dict[str, Any]:
    leaf = ph.leaves([t for t in vis if True])
    scope_h = round(sum(ph.size_min(t) for t in leaf) / 60, 1)
    start = us.to_client_tz(p.start, tz).date() if p.start else today - dt.timedelta(days=56)
    start = max(start, today - dt.timedelta(days=7 * 16))
    weeks, d = [], us.week_bounds(start)[0]
    while d <= today:
        weeks.append(d)
        d += dt.timedelta(days=7)
    z = ZoneInfo(tz)

    def done_by(day: dt.date) -> float:
        cut = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), tzinfo=z).astimezone(UTC)
        return round(sum(ph.size_min(t) for t in leaf if ph.is_done(t) and t.completed_at and t.completed_at < cut) / 60, 1)
    wk_end = [min(w + dt.timedelta(days=6), today) for w in weeks]
    done_cum = [done_by(e) for e in wk_end]
    s: Dict[str, Any] = {}
    if len(weeks) >= 2:
        s["burnup"] = {"days": [_iso(e) for e in wk_end], "done": done_cum, "scope": [scope_h] * len(wk_end)}
        ideal_end = us.to_client_tz(p.deadline, tz).date() if p.deadline else None
        span = max(1, (ideal_end - weeks[0]).days) if ideal_end else None
        s["burndown"] = {"days": [_iso(e) for e in wk_end], "actual": [round(scope_h - x, 1) for x in done_cum],
                         "ideal": [round(max(0.0, scope_h * (1 - ((e - weeks[0]).days / span))), 1) if span else round(scope_h * (1 - i / max(1, len(wk_end) - 1)), 1) for i, e in enumerate(wk_end)]}
        s["velocity"] = {"weeks": [f"{us.MONTHS[w.month - 1]} {w.day}" for w in weeks[-6:]], "hours": [round(done_cum[i] - (done_cum[i - 1] if i else 0), 1) for i in range(len(weeks))][-6:]}
        s["cfd"] = {"days": [_iso(e) for e in wk_end],
                    "done": [sum(1 for t in leaf if ph.is_done(t) and t.completed_at and t.completed_at < dt.datetime.combine(e + dt.timedelta(days=1), dt.time(), tzinfo=z).astimezone(UTC)) for e in wk_end],
                    "doing": [0] * len(wk_end), "todo": [0] * len(wk_end)}
        s["cfd"]["todo"] = [len(leaf) - x for x in s["cfd"]["done"]]
    s["donut"] = {"labels": [k for k, _v in sorted(by_task.items(), key=lambda kv: -kv[1][0])][:12], "values": [round(v[0] / 3600, 2) for _k, v in sorted(by_task.items(), key=lambda kv: -kv[1][0])][:12]}
    hist: Dict[str, float] = {}
    lo84, hi84 = window(today - dt.timedelta(days=83), today, tz)
    wk_hours: Dict[dt.date, List[float]] = {w: [0.0, 0.0] for w in weeks[-8:]}
    for t in vis:
        for day, sec in _chunks(t, lo84, hi84, tz):
            hist[day.isoformat()] = hist.get(day.isoformat(), 0.0) + sec / 3600
            w0 = us.week_bounds(day)[0]
            if w0 in wk_hours:
                wk_hours[w0][0 if t.billable else 1] += sec / 3600
    s["heatmap"] = {"days": {k: round(v, 2) for k, v in hist.items()}, "end": _iso(today)}
    if len(wk_hours) >= 2:
        s["trend"] = {"labels": [f"{us.MONTHS[w.month - 1]} {w.day}" for w in wk_hours], "billable": [round(v[0], 1) for v in wk_hours.values()], "non_billable": [round(v[1], 1) for v in wk_hours.values()]}
    rows, prev = [], (us.to_client_tz(p.start, tz).date() if p.start else today)
    for m in prog["milestones"]:
        due = dt.datetime.fromisoformat(m["due"]).date() if m.get("due") else None
        if due:
            rows.append({"name": m["name"], "start": _iso(min(prev, due)), "end": _iso(due), "pct": m["pct"]})
            prev = due
    s["gantt"] = {"rows": rows, "today": _iso(today)}
    return s


def _milestone(db: Database, pid: str, mid: Optional[str], tasks: List[TimeEntry], meta: Dict[str, Any], tz: str, policy: str) -> Dict[str, Any]:
    st = Store(db)
    m = st.get("milestones", mid) if mid else None
    if m is None or m["project_id"] != pid:
        raise ReportError("Choose a milestone for this report")
    own = [t for t in tasks if t.extra.get("phase") == mid and visible(t, meta, policy)]
    dels = st.rows("deliverables", "project_id=? AND milestone_id=? AND visible=1", (pid, mid), "delivered_at")
    secs = sum(t.duration_sec for t in own if t.status == Status.DONE)
    return {"id": mid, "name": m["name"], "description": m.get("description", ""), "criteria": [l.strip("-• ").strip() for l in (m.get("acceptance_criteria") or "").splitlines() if l.strip()],
            "due": m.get("due"), "due_label": us.fmt_date(dt.datetime.fromisoformat(m["due"]).date()) if m.get("due") else None, "completed": bool(m.get("completed")),
            "completed_label": us.fmt_date(dt.datetime.fromisoformat(m["completed_at"]).date()) if m.get("completed_at") else None, "status": m.get("status", "pending"),
            "tasks": [{"title": t.title, "done": ph.is_done(t), "hours": round(t.duration_sec / 3600, 2), "note": meta.get(t.id, (0, ""))[1]} for t in own if not t.parent_id],
            "hours": round(secs / 3600, 1), "deliverables": [{"title": d["title"], "kind": d["kind"], "ref": d["ref"], "status": d["status"], "feedback": d["feedback"]} for d in dels],
            "sign_off": bool(dels) and all(d["status"] == "approved" for d in dels)}


def _invoice(db: Database, p: Project, prefs: Dict[str, Any], vis: List[TimeEntry], lo: dt.datetime, hi: dt.datetime, tz: str, today: dt.date, opts: Dict[str, Any]) -> Dict[str, Any]:
    rate = float(opts.get("rate") or p.rate_per_hour or prefs["rate"])
    lines: Dict[str, Dict[str, Any]] = {}
    for t in vis:
        if not t.billable:
            continue
        sec = sum(round_seconds(s, prefs["rounding_min"]) for _d, s in _chunks(t, lo, hi, tz))
        if sec:
            row = lines.setdefault(t.title, {"description": t.title, "seconds": 0})
            row["seconds"] += sec
    items = []
    for row in sorted(lines.values(), key=lambda r: r["description"].lower()):
        h = round(row["seconds"] / 3600, 2)
        items.append({"description": row["description"], "hours": h, "rate": rate, "amount": round(h * rate, 2)})
    subtotal = round(sum(i["amount"] for i in items), 2)
    discount = round(float(opts.get("discount", 0)), 2)
    tax_pct = float(opts.get("tax_percent", prefs["tax_percent"]))
    tax = round((subtotal - discount) * tax_pct / 100, 2)
    terms = int(opts.get("terms_days", prefs["terms_days"]))
    return {"number": opts.get("invoice_number", "DRAFT"), "issue_date": today.isoformat(), "issue_label": us.fmt_date(today), "due_date": (today + dt.timedelta(days=terms)).isoformat(),
            "due_label": us.fmt_date(today + dt.timedelta(days=terms)), "terms": f"Net {terms}", "currency": prefs["currency"], "rate": rate, "rounding_min": prefs["rounding_min"], "items": items,
            "hours": round(sum(i["hours"] for i in items), 2), "subtotal": subtotal, "discount": discount, "tax_percent": tax_pct, "tax": tax, "total": round(subtotal - discount + tax, 2),
            "payment_instructions": company_profile(db)["payment_instructions"], "notes": opts.get("notes", "")}
