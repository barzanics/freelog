"""Client relationship layer: Client Health Score, Silence Alert, Promise Tracker, onboarding checklist, meeting log, risk register, deliverables with approval,
feedback, public change log and the upsell hint. Pure functions over ``Store`` - the UI, the portal and the report builders all use the same rules."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from ..core.crm import Store
from ..core.database import Database
from ..core.models import Client, Invoice, InvoiceStatus, Project
from ..core.persian import UTC, now_utc
from . import project_health as ph

ONBOARDING = ("Contract / NDA signed", "Access & credentials received", "Kickoff call scheduled", "Brand assets received", "Payment terms & first invoice agreed",
              "Primary contact & escalation path confirmed", "Communication channel agreed (email / Slack)", "Success criteria written down", "Tools & repository access granted")


class OpsError(ValueError):
    """Invalid request (message is user-facing)."""


def _iso(t: Optional[dt.datetime]) -> str:
    return (t or now_utc()).isoformat()


def _parse(s: Optional[str]) -> Optional[dt.datetime]:
    return dt.datetime.fromisoformat(s) if s else None


def client_projects(db: Database, client_id: str, active_only: bool = False) -> List[Project]:
    q = "SELECT * FROM projects WHERE client_id=?" + (" AND status IN ('planning','active')" if active_only else "")
    return [Project.from_row(r) for r in db.conn.execute(q, (client_id,))]


# ------------------------------------------------------------------ contact / feedback
def touch_contact(db: Database, client_id: str, now: Optional[dt.datetime] = None) -> None:
    """Record that the client was in touch (a reply, a call, a comment). Drives the silence alert and the health score."""
    st = Store(db)
    c = st.get("clients", client_id)
    if c is None:
        raise KeyError(client_id)
    s = dict(c.get("settings") or {})
    s["last_contact_at"] = _iso(now)
    st.update("clients", client_id, settings=s)


def last_contact(db: Database, client_id: str) -> Optional[dt.datetime]:
    st = Store(db)
    c = st.get("clients", client_id)
    times = [_parse((c.get("settings") or {}).get("last_contact_at"))] if c else []
    for m in st.rows("meetings", "client_id=?", (client_id,)):
        times.append(_parse(m["at"]))
    for f in st.rows("client_feedback", "client_id=?", (client_id,)):
        times.append(_parse(f["received_at"]))
    for p in client_projects(db, client_id):
        for cm in st.rows("client_comments", "project_id=? AND author='client'", (p.id,)):
            times.append(_parse(cm["at"]))
    times = [t for t in times if t]
    return max(times) if times else None


def add_feedback(db: Database, report_id: str, rating: int, comment: str = "", now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    if not 1 <= int(rating) <= 5:
        raise OpsError("Rating must be between 1 and 5")
    st = Store(db)
    rep = st.get("client_reports", report_id)
    if rep is None:
        raise KeyError(report_id)
    proj = st.get("projects", rep["project_id"]) or {}
    f = st.add("client_feedback", report_id=report_id, project_id=rep["project_id"], client_id=proj.get("client_id"), rating=int(rating), comment=comment.strip()[:2000], received_at=_iso(now))
    if proj.get("client_id"):
        touch_contact(db, proj["client_id"], now)
    return f


def average_rating(db: Database, client_id: str, days: int = 180, now: Optional[dt.datetime] = None) -> Optional[float]:
    cutoff = ((now or now_utc()) - dt.timedelta(days=days)).isoformat()
    r = Store(db).rows("client_feedback", "client_id=? AND received_at>=?", (client_id, cutoff))
    return round(sum(x["rating"] for x in r) / len(r), 2) if r else None


# ------------------------------------------------------------------ health score + silence
def _bands(value: float, bands) -> float:
    for limit, score in bands:
        if value <= limit:
            return score
    return bands[-1][1]


def health_score(db: Database, client_id: str, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """0-100 per client. Responsiveness 25 %, satisfaction 25 %, delivery health 25 %, payments 15 %, waiting-on-client blockers 10 %."""
    now = now or now_utc()
    c = db.get(Client, client_id)
    if c is None:
        raise KeyError(client_id)
    reasons: List[str] = []
    lc = last_contact(db, client_id)
    if lc is None:
        resp, days = 50.0, None
        reasons.append("No contact on record yet.")
    else:
        days = (now - lc).days
        resp = _bands(days, ((3, 100), (7, 85), (14, 60), (30, 30), (10 ** 6, 10)))
        if resp < 60:
            reasons.append(f"No contact for {days} days.")
    rating = average_rating(db, client_id, 180, now)
    sat = 70.0 if rating is None else (rating - 1) / 4 * 100
    if rating is not None and sat < 60:
        reasons.append(f"Low satisfaction (average {rating}/5).")
    projects = client_projects(db, client_id, active_only=True)
    scores = {"on_track": 100.0, "at_risk": 55.0, "off_track": 15.0}
    hs = [ph.health(db, p.id, now) for p in projects]
    delivery = sum(scores[h["status"]] for h in hs) / len(hs) if hs else 70.0
    if any(h["status"] != "on_track" for h in hs):
        reasons.append("Delivery health: " + ", ".join(f"{p.name} is {h['status'].replace('_', ' ')}" for p, h in zip(projects, hs) if h["status"] != "on_track") + ".")
    overdue = [i for i in (Invoice.from_row(r) for r in db.conn.execute("SELECT * FROM invoices WHERE client_id=?", (client_id,)))
               if i.status != InvoiceStatus.PAID and i.balance > 0 and (now - i.issued_at).days > 30]
    pay = max(0.0, 100.0 - 30.0 * len(overdue))
    if overdue:
        reasons.append(f"{len(overdue)} invoice(s) overdue.")
    waiting = [b for p in projects for b in ph.blockers(db, p.id, 3, now) if b["by"] == "client" and b["aged"]]
    blk = max(0.0, 100.0 - 25.0 * len(waiting))
    if waiting:
        reasons.append(f"{len(waiting)} task(s) waiting on the client for 3+ days.")
    score = round(0.25 * resp + 0.25 * sat + 0.25 * delivery + 0.15 * pay + 0.10 * blk)
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"
    return {"score": score, "grade": grade, "alert": score < 60, "reasons": reasons, "days_since_contact": days,
            "components": {"responsiveness": round(resp), "satisfaction": round(sat), "delivery": round(delivery), "payments": round(pay), "blockers": round(blk)}}


def silence_alerts(db: Database, now: Optional[dt.datetime] = None, default_days: int = 7) -> List[Dict[str, Any]]:
    """Active clients (with an active project) we have not heard from for too long - "time to follow up"."""
    now, out = now or now_utc(), []
    for c in Store(db).rows("clients", "status='active'"):
        if not client_projects(db, c["id"], active_only=True):
            continue
        limit = int((c.get("settings") or {}).get("silence_days", default_days))
        lc = last_contact(db, c["id"])
        base = lc or _parse(c.get("created_at")) or now
        days = (now - base).days
        if days >= limit:
            out.append({"client_id": c["id"], "name": c["name"], "days": days, "limit": limit, "last_contact": lc, "never": lc is None})
    return sorted(out, key=lambda a: -a["days"])


# ------------------------------------------------------------------ promises
def add_promise(db: Database, client_id: str, text: str, due: Any, project_id: Optional[str] = None, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    if not text.strip():
        raise OpsError("Describe what you promised")
    if db.get(Client, client_id) is None:
        raise KeyError(client_id)
    d = due if isinstance(due, dt.datetime) else dt.datetime.combine(due, dt.time(17), tzinfo=UTC)
    return Store(db).add("promises", client_id=client_id, project_id=project_id, text=text.strip(), due=d.isoformat(), status="open", created_at=_iso(now), notified=0)


def promises(db: Database, client_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    w, p = [], []
    if client_id:
        w.append("client_id=?"); p.append(client_id)
    if status:
        w.append("status=?"); p.append(status)
    return Store(db).rows("promises", " AND ".join(w), p, "due")


def promise_alerts(db: Database, now: Optional[dt.datetime] = None, within_hours: int = 48) -> List[Dict[str, Any]]:
    """Open promises that are overdue or due soon (and were not flagged yet) - each with a ready-to-send heads-up if late."""
    now, out = now or now_utc(), []
    for pr in promises(db, status="open"):
        due = _parse(pr["due"])
        if pr["notified"] or due is None:
            continue
        if due < now:
            out.append({**pr, "state": "overdue", "notice": suggest_notice(db, pr["id"], now)})
        elif due - now <= dt.timedelta(hours=within_hours):
            out.append({**pr, "state": "due_soon", "notice": ""})
    return sorted(out, key=lambda x: x["due"])


def mark_promise(db: Database, promise_id: str, status: str, now: Optional[dt.datetime] = None, new_due: Any = None) -> Dict[str, Any]:
    if status not in ("open", "kept", "missed", "renegotiated"):
        raise OpsError("Unknown status")
    f: Dict[str, Any] = {"status": status, "done_at": _iso(now) if status != "open" else None}
    if status == "renegotiated" and new_due is not None:
        f.update(due=(new_due if isinstance(new_due, dt.datetime) else dt.datetime.combine(new_due, dt.time(17), tzinfo=UTC)).isoformat(), status="open", notified=0)
    return Store(db).update("promises", promise_id, **f)


def mark_promise_notified(db: Database, promise_id: str) -> None:
    Store(db).update("promises", promise_id, notified=1)


def suggest_notice(db: Database, promise_id: str, now: Optional[dt.datetime] = None) -> str:
    pr = Store(db).get("promises", promise_id)
    if pr is None:
        raise KeyError(promise_id)
    from ..reports import locale_us as us
    c = Store(db).get("clients", pr["client_id"]) or {}
    due = _parse(pr["due"])
    return (f"Hi {c.get('contact_name') or c.get('name', 'there')},\n\nA quick heads-up: we committed to “{pr['text']}” by {us.fmt_date(due)} and we are going to miss that date. "
            f"We will send a firm new date shortly, and we are sorry for the delay.\n\nBest regards")


# ------------------------------------------------------------------ onboarding / meetings / risks
def ensure_onboarding(db: Database, client_id: str) -> List[Dict[str, Any]]:
    st = Store(db)
    if not st.rows("onboarding_items", "client_id=?", (client_id,)):
        for i, t in enumerate(ONBOARDING):
            st.add("onboarding_items", client_id=client_id, title=t, done=0, ord=i)
    return st.rows("onboarding_items", "client_id=?", (client_id,), "ord")


def toggle_onboarding(db: Database, item_id: str, now: Optional[dt.datetime] = None) -> bool:
    st = Store(db)
    it = st.get("onboarding_items", item_id)
    if it is None:
        raise KeyError(item_id)
    done = not it["done"]
    st.update("onboarding_items", item_id, done=int(done), done_at=_iso(now) if done else None)
    return done


def onboarding_progress(db: Database, client_id: str) -> Dict[str, Any]:
    items = Store(db).rows("onboarding_items", "client_id=?", (client_id,))
    done = sum(1 for i in items if i["done"])
    return {"done": done, "total": len(items), "pct": round(100 * done / len(items)) if items else 0, "open": [i["title"] for i in items if not i["done"]]}


def log_meeting(db: Database, client_id: str, summary: str, minutes: int = 30, at: Optional[dt.datetime] = None, project_id: Optional[str] = None,
                action_items: Optional[List[Dict[str, Any]]] = None, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
    if db.get(Client, client_id) is None:
        raise KeyError(client_id)
    if minutes < 0 or minutes > 600:
        raise OpsError("Meeting length must be 0-600 minutes")
    m = Store(db).add("meetings", client_id=client_id, project_id=project_id, at=_iso(at), minutes=minutes, summary=summary.strip(), action_items=action_items or [], attendees=attendees or [])
    touch_contact(db, client_id, at)
    return m


def meetings_between(db: Database, project_id: str, start: dt.datetime, end: dt.datetime) -> List[Dict[str, Any]]:
    p = Store(db).get("projects", project_id) or {}
    return Store(db).rows("meetings", "(project_id=? OR (project_id IS NULL AND client_id=?)) AND at>=? AND at<?", (project_id, p.get("client_id"), start.isoformat(), end.isoformat()), "at")


def add_risk(db: Database, project_id: str, title: str, probability: int, impact: int, mitigation: str = "", visible: bool = False, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    if not title.strip():
        raise OpsError("Describe the risk")
    if not (1 <= probability <= 5 and 1 <= impact <= 5):
        raise OpsError("Probability and impact must be 1-5")
    return Store(db).add("risks", project_id=project_id, title=title.strip(), probability=probability, impact=impact, mitigation=mitigation.strip(), status="open", created_at=_iso(now), visible=int(visible))


def risk_register(db: Database, project_id: str, only_visible: bool = False, include_closed: bool = False) -> List[Dict[str, Any]]:
    w = "project_id=?" + ("" if include_closed else " AND status='open'") + (" AND visible=1" if only_visible else "")
    out = []
    for r in Store(db).rows("risks", w, (project_id,)):
        s = r["probability"] * r["impact"]
        out.append({**r, "score": s, "level": "high" if s >= 15 else "medium" if s >= 8 else "low"})
    return sorted(out, key=lambda r: -r["score"])


# ------------------------------------------------------------------ deliverables, milestones, change log
def log_change(db: Database, project_id: str, text: str, kind: str = "change", public: bool = True, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    return Store(db).add("changelog", project_id=project_id, at=_iso(now), kind=kind, text=text.strip(), public=int(public))


def public_changes(db: Database, project_id: str, start: Optional[dt.datetime] = None, end: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
    w, p = "project_id=? AND public=1", [project_id]
    if start:
        w += " AND at>=?"; p.append(start.isoformat())
    if end:
        w += " AND at<?"; p.append(end.isoformat())
    return Store(db).rows("changelog", w, p, "at DESC")


def add_deliverable(db: Database, project_id: str, title: str, kind: str = "link", ref: str = "", milestone_id: Optional[str] = None, visible: bool = True,
                    delivered_at: Optional[dt.datetime] = None) -> Dict[str, Any]:
    if not title.strip():
        raise OpsError("Name the deliverable")
    if kind not in ("file", "link", "note"):
        raise OpsError("Kind must be file, link or note")
    d = Store(db).add("deliverables", project_id=project_id, milestone_id=milestone_id, title=title.strip(), kind=kind, ref=ref.strip(), delivered_at=_iso(delivered_at), status="pending", visible=int(visible))
    log_change(db, project_id, f"Delivered: {title.strip()}", "deliverable", visible, delivered_at)
    return d


def decide_deliverable(db: Database, deliverable_id: str, decision: str, feedback: str = "", now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """The client's Approve / Request changes. Updates the change log, the last-contact time and (when all are approved) lets the milestone close."""
    if decision not in ("approved", "changes_requested"):
        raise OpsError("Decision must be approved or changes_requested")
    st = Store(db)
    d = st.get("deliverables", deliverable_id)
    if d is None:
        raise KeyError(deliverable_id)
    d = st.update("deliverables", deliverable_id, status=decision, feedback=feedback.strip()[:2000], decided_at=_iso(now))
    log_change(db, d["project_id"], ("Approved: " if decision == "approved" else "Changes requested: ") + d["title"], "approval", True, now)
    proj = st.get("projects", d["project_id"]) or {}
    if proj.get("client_id"):
        touch_contact(db, proj["client_id"], now)
    return d


def pending_approvals(db: Database, project_id: str) -> List[Dict[str, Any]]:
    return Store(db).rows("deliverables", "project_id=? AND visible=1 AND status='pending'", (project_id,), "delivered_at")


def set_milestone(db: Database, milestone_id: str, **fields: Any) -> Dict[str, Any]:
    """Edit weight / order / status / description / acceptance criteria / due / deliverables of a milestone."""
    allowed = {"name", "ord", "weight", "status", "description", "acceptance_criteria", "due", "deliverables", "notes"}
    bad = set(fields) - allowed
    if bad:
        raise OpsError(f"Cannot set {sorted(bad)}")
    if "weight" in fields and float(fields["weight"]) <= 0:
        raise OpsError("Weight must be positive")
    return Store(db).update("milestones", milestone_id, **fields)


def complete_milestone(db: Database, milestone_id: str, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    st = Store(db)
    m = st.get("milestones", milestone_id)
    if m is None:
        raise KeyError(milestone_id)
    m = st.update("milestones", milestone_id, completed=1, completed_at=_iso(now), status="done")
    log_change(db, m["project_id"], f"Milestone completed: {m['name']}", "milestone", True, now)
    return m


# ------------------------------------------------------------------ upsell
def upsell_suggestion(db: Database, project_id: str, now: Optional[dt.datetime] = None) -> Optional[Dict[str, Any]]:
    """"Now is a good moment to propose the next phase": project >= 80 % done, healthy, client happy (or silent-neutral) and nothing overdue to pay."""
    now = now or now_utc()
    p = db.get(Project, project_id)
    if p is None or not p.client_id:
        raise KeyError(project_id)
    h = ph.health(db, project_id, now)
    if h["actual_pct"] < 80 or h["status"] != "on_track":
        return None
    rating = average_rating(db, p.client_id, 180, now)
    if rating is not None and rating < 4:
        return None
    if health_score(db, p.client_id, now)["components"]["payments"] < 100:
        return None
    why = [f"{p.name} is {h['actual_pct']:.0f}% complete and on track."]
    if rating is not None:
        why.append(f"The client rated recent reports {rating}/5.")
    return {"project": p.name, "headline": "Good moment to propose the next phase", "reasons": why}
