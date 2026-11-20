"""Report lifecycle: generate -> draft -> (edit the summary) -> approve -> PDF / e-mail / portal. Files live in ``<data>/client_reports/<project>/<number>.*``; the row in
``client_reports`` keeps the data (JSON) so a report can be re-rendered, diffed against the previous one and shown in the portal."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.crm import Store
from ..core.database import Database
from ..core.models import Invoice, InvoiceStatus
from ..core.persian import UTC, now_utc
from . import builders, pdf, render


class ReportStateError(ValueError):
    """Illegal status change (e.g. approving something already sent)."""


def next_invoice_number(db: Database, now: Optional[dt.datetime] = None) -> str:
    """Reserve the next invoice number: ``<prefix>-<year>-<seq>``; the sequence only ever moves forward."""
    seq = int(db.get_setting("invoice_seq", 0)) + 1
    db.set_setting("invoice_seq", seq)
    return f"{db.get_setting('invoice_prefix', 'INV') or 'INV'}-{(now or now_utc()).year}-{seq:04d}"


def _dir(data_dir: Path, project_id: str) -> Path:
    d = Path(data_dir) / "client_reports" / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write(data_dir: Path, project_id: str, number: str, rendered: Dict[str, Any]) -> str:
    base = _dir(data_dir, project_id) / number
    base.with_suffix(".html").write_text(rendered["html"], encoding="utf-8")
    base.with_suffix(".md").write_text(rendered["md"], encoding="utf-8")
    base.with_suffix(".json").write_text(rendered["json"], encoding="utf-8")
    return str(base.with_suffix(".html"))


def generate(db: Database, data_dir: Path, project_id: str, kind: str = "weekly", start: Optional[dt.date] = None, end: Optional[dt.date] = None, now: Optional[dt.datetime] = None,
             options: Optional[Dict[str, Any]] = None, portal_url: Optional[str] = None) -> Dict[str, Any]:
    now = now or now_utc()
    opts = dict(options or {})
    if kind == "invoice" and "invoice_number" not in opts:
        opts["invoice_number"] = next_invoice_number(db, now)
    data = builders.build(db, project_id, kind, start, end, now, opts)
    if kind == "invoice":
        data["header"]["number"] = opts["invoice_number"]
    rendered = render.render_all(data, portal_url)
    html_path = _write(data_dir, project_id, data["header"]["number"], rendered)
    return Store(db).add("client_reports", project_id=project_id, type=kind, number=data["header"]["number"], period_start=data["period"]["start"], period_end=data["period"]["end"],
                         generated_at=now.isoformat(), payload=data, html_path=html_path, summary=data["summary"], status="draft", recipients=[])


def get(db: Database, report_id: str) -> Dict[str, Any]:
    r = Store(db).get("client_reports", report_id)
    if r is None:
        raise KeyError(report_id)
    return r


def list_reports(db: Database, project_id: Optional[str] = None, status: Optional[str] = None, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    w, p = [], []
    for col, v in (("project_id", project_id), ("status", status), ("type", kind)):
        if v:
            w.append(f"{col}=?"); p.append(v)
    return Store(db).rows("client_reports", " AND ".join(w), p, "generated_at DESC")


def update_summary(db: Database, data_dir: Path, report_id: str, text: str, portal_url: Optional[str] = None) -> Dict[str, Any]:
    """Edit the executive summary of a draft and re-render every file. A sent report is frozen."""
    r = get(db, report_id)
    if r["status"] not in ("draft", "approved"):
        raise ReportStateError("A sent report cannot be edited; generate a new one")
    data = r["payload"]
    data["summary"] = text.strip()
    _write(data_dir, r["project_id"], r["number"], render.render_all(data, portal_url))
    pdf_path = Path(r["pdf_path"]) if r["pdf_path"] else None
    if pdf_path and pdf_path.exists():
        pdf_path.unlink()                                                   # the PDF is rebuilt on demand from the edited data
    return Store(db).update("client_reports", report_id, payload=data, summary=data["summary"], pdf_path="", status="draft")


def approve(db: Database, report_id: str) -> Dict[str, Any]:
    """The mandatory human step before anything is e-mailed."""
    r = get(db, report_id)
    if r["status"] == "sent":
        raise ReportStateError("Already sent")
    return Store(db).update("client_reports", report_id, status="approved")


def ensure_pdf(db: Database, data_dir: Path, report_id: str, assets: Optional[Path] = None, portal_url: Optional[str] = None) -> Path:
    r = get(db, report_id)
    if r["pdf_path"] and Path(r["pdf_path"]).exists():
        return Path(r["pdf_path"])
    rendered = render.render_all(r["payload"], portal_url)
    out = pdf.render_pdf(r["payload"], rendered, _dir(data_dir, r["project_id"]) / f"{r['number']}.pdf", assets)
    Store(db).update("client_reports", report_id, pdf_path=str(out))
    return out


def diff(db: Database, report_id: str) -> Dict[str, Any]:
    """This report against the previous one of the same type and project - for you, not the client."""
    r = get(db, report_id)
    prev = [x for x in Store(db).rows("client_reports", "project_id=? AND type=? AND generated_at<?", (r["project_id"], r["type"], r["generated_at"]), "generated_at DESC", 1)]
    if not prev:
        return {"has_previous": False, "lines": ["First report of this type for the project."]}
    a, b = r["payload"], prev[0]["payload"]
    hours = lambda d: d["time"]["total_sec"] / 3600
    lines = []
    for label, x, y, unit in (("Hours logged", hours(a), hours(b), " h"), ("Progress", a["progress"]["pct"], b["progress"]["pct"], " pts"), ("Tasks completed", len(a["done"]), len(b["done"]), "")):
        d = round(x - y, 1)
        lines.append(f"{label}: {x:.1f}{unit} ({'+' if d >= 0 else ''}{d}{unit} vs {prev[0]['number']})")
    if a["health"]["status"] != b["health"]["status"]:
        lines.append(f"Health changed: {b['health']['status'].replace('_', ' ')} → {a['health']['status'].replace('_', ' ')}")
    new_wait = {w["title"] for w in a["waiting_on_client"]} - {w["title"] for w in b["waiting_on_client"]}
    cleared = {w["title"] for w in b["waiting_on_client"]} - {w["title"] for w in a["waiting_on_client"]}
    lines += [f"Newly waiting on the client: {t}" for t in sorted(new_wait)] + [f"No longer waiting: {t}" for t in sorted(cleared)]
    return {"has_previous": True, "previous": prev[0]["number"], "lines": lines}


def create_invoice_record(db: Database, report_id: str) -> Invoice:
    """Turn an invoice report into a tracked ``Invoice`` (payment status, overdue days) - idempotent per report."""
    r = get(db, report_id)
    if r["type"] != "invoice":
        raise ReportStateError("Only invoice reports can become invoices")
    existing = db.conn.execute("SELECT id FROM invoices WHERE number=?", (r["number"],)).fetchone()
    if existing:
        return db.get(Invoice, existing[0])
    i = r["payload"]["invoice"]
    proj = Store(db).get("projects", r["project_id"]) or {}
    inv = Invoice(client_id=proj.get("client_id"), number=r["number"], items=[{"description": x["description"], "hours": x["hours"], "rate": x["rate"], "amount": x["amount"]} for x in i["items"]],
                  tax_percent=i["tax_percent"], discount=i["discount"], currency=i["currency"], issued_at=dt.datetime.fromisoformat(i["issue_date"]).replace(tzinfo=UTC), status=InvoiceStatus.SENT)
    db.save(inv)
    return inv
