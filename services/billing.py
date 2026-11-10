"""Billing: rates, invoices from tracked time, payments, retainers, currencies, HTML/PDF output."""
from __future__ import annotations

import datetime as dt
import html
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.database import Database
from ..core.models import Client, Invoice, InvoiceStatus, Project, TimeEntry
from ..core.persian import date_to_jalali, format_jalali, now_utc, to_fa_digits, to_tehran

DEFAULT_RATES = {"IRR": 1.0, "USD": 600000.0, "EUR": 650000.0}  # value of 1 unit in IRR; user-editable, offline


def convert(amount: float, src: str, dst: str, rates: Dict[str, float]) -> float:
    """Convert via the IRR-based manual rate table."""
    if src == dst:
        return amount
    try:
        return round(amount * rates[src] / rates[dst], 2)
    except KeyError as exc:
        raise ValueError(f"no rate for {exc.args[0]}") from None


class Billing:
    def __init__(self, db: Database) -> None:
        self.db = db

    @property
    def rates(self) -> Dict[str, float]:
        return {**DEFAULT_RATES, **self.db.get_setting("rates", {})}

    def set_rate(self, currency: str, irr_value: float) -> None:
        if irr_value <= 0:
            raise ValueError("rate must be positive")
        self.db.set_setting("rates", {**self.db.get_setting("rates", {}), currency: irr_value})

    def rate_for(self, e: TimeEntry, project: Optional[Project], client: Optional[Client]) -> float:
        """Priority: per-entry override > project rate > client default rate."""
        if "rate" in e.extra:
            return float(e.extra["rate"])
        if project and project.rate_per_hour:
            return project.rate_per_hour
        return client.default_rate if client else 0.0

    def unbilled(self, client_id: str, until: Optional[dt.datetime] = None) -> List[TimeEntry]:
        rows = self.db.conn.execute(
            "SELECT e.* FROM entries e JOIN projects p ON p.id=e.project_id WHERE p.client_id=? AND e.billable=1 "
            "AND e.status='done' AND e.invoice_id IS NULL" + (" AND e.start_utc<?" if until else "") + " ORDER BY e.start_utc",
            (client_id, until.isoformat()) if until else (client_id,))
        return [TimeEntry.from_row(r) for r in rows]

    def next_number(self) -> str:
        n = int(self.db.get_setting("invoice_seq", 0)) + 1
        self.db.set_setting("invoice_seq", n)
        return f"INV-{date_to_jalali(to_tehran(now_utc()).date())[0]}-{n:04d}"

    def create_invoice(self, client_id: str, until: Optional[dt.datetime] = None, tax_percent: float = 0.0,
                       discount: float = 0.0) -> Invoice:
        """Group unbilled billable entries per project into line items and mark them invoiced (atomic)."""
        client = self.db.get(Client, client_id)
        if client is None:
            raise KeyError(client_id)
        entries = self.unbilled(client_id, until)
        if not entries:
            raise ValueError("nothing to invoice")
        projects = {p.id: p for p in self.db.all(Project)}
        buckets: Dict[tuple, float] = defaultdict(float)
        for e in entries:
            rate = self.rate_for(e, projects.get(e.project_id or ""), client)
            buckets[(e.project_id, rate)] += e.duration_sec / 3600
        items = [{"desc": projects[pid].name if pid in projects else "—", "hours": round(h, 2), "rate": rate}
                 for (pid, rate), h in buckets.items()]
        with self.db.transaction():
            inv = Invoice(client_id=client_id, number=self.next_number(), items=items, tax_percent=tax_percent,
                          discount=discount, currency=client.currency)
            self.db.save(inv)
            for e in entries:
                e.invoice_id = inv.id
                self.db.save(e)
        return inv

    def create_retainer(self, client_id: str, description: str, hours: float, rate: float, tax_percent: float = 0.0) -> Invoice:
        """Fixed monthly retainer invoice with no time entries attached."""
        client = self.db.get(Client, client_id)
        if client is None:
            raise KeyError(client_id)
        if hours <= 0 or rate < 0:
            raise ValueError("hours must be positive and rate non-negative")
        inv = Invoice(client_id=client_id, number=self.next_number(), items=[{"desc": description, "hours": hours, "rate": rate}],
                      tax_percent=tax_percent, currency=client.currency)
        self.db.save(inv)
        return inv

    def pay(self, invoice_id: str, amount: float) -> Invoice:
        inv = self.db.get(Invoice, invoice_id)
        if inv is None:
            raise KeyError(invoice_id)
        if amount > inv.balance + 1e-9:
            raise ValueError("payment exceeds balance")
        inv.apply_payment(amount)
        self.db.save(inv)
        return inv

    def void(self, invoice_id: str) -> None:
        """Delete a draft invoice and release its entries."""
        inv = self.db.get(Invoice, invoice_id)
        if inv is None:
            raise KeyError(invoice_id)
        if inv.status != InvoiceStatus.DRAFT or inv.paid:
            raise ValueError("only unpaid draft invoices can be voided")
        with self.db.transaction() as c:
            c.execute("UPDATE entries SET invoice_id=NULL WHERE invoice_id=?", (invoice_id,))
        self.db.delete(Invoice, invoice_id)

    def outstanding(self, currency: Optional[str] = None) -> float:
        total = 0.0
        for inv in self.db.all(Invoice):
            if currency is None:
                total += convert(inv.balance, inv.currency, "IRR", self.rates)
            elif inv.currency == currency:
                total += inv.balance
        return round(total, 2)

    # ---- rendering ----------------------------------------------------
    def to_html(self, invoice_id: str) -> str:
        """RTL Persian invoice (open in a browser and print to PDF with perfect shaping)."""
        inv = self.db.get(Invoice, invoice_id)
        client = self.db.get(Client, inv.client_id) if inv else None
        if inv is None or client is None:
            raise KeyError(invoice_id)
        e = html.escape
        rows = "".join(f"<tr><td>{e(str(i['desc']))}</td><td>{i['hours']}</td><td>{i['rate']:,.0f}</td>"
                       f"<td>{float(i['hours']) * float(i['rate']):,.0f}</td></tr>" for i in inv.items)
        date = format_jalali(to_tehran(inv.issued_at).date())
        body = (f"<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'><title>{e(inv.number)}</title>"
                "<style>body{font-family:Vazirmatn,Tahoma,sans-serif;margin:40px;color:#111}table{width:100%;border-collapse:collapse}"
                "td,th{border-bottom:1px solid #ddd;padding:8px;text-align:right}.tot{font-weight:700}</style>"
                f"<h1>فاکتور {e(inv.number)}</h1><p>مشتری: {e(client.name)} — تاریخ: {date}</p>"
                f"<table><tr><th>شرح</th><th>ساعت</th><th>نرخ</th><th>مبلغ</th></tr>{rows}</table>"
                f"<p>جمع: {inv.subtotal:,.0f} {inv.currency} | تخفیف: {inv.discount:,.0f} | مالیات: {inv.tax_percent}%</p>"
                f"<p class='tot'>قابل پرداخت: {inv.total:,.0f} {inv.currency} | پرداخت‌شده: {inv.paid:,.0f} | مانده: {inv.balance:,.0f}</p></html>")
        return to_fa_digits(body)

    def to_pdf(self, invoice_id: str, dest: Union[str, Path]) -> Path:
        """Simple PDF via reportlab (Latin text; use ``to_html`` for full Persian shaping)."""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        inv = self.db.get(Invoice, invoice_id)
        client = self.db.get(Client, inv.client_id) if inv else None
        if inv is None or client is None:
            raise KeyError(invoice_id)
        c = canvas.Canvas(str(dest), pagesize=A4)
        y = 800
        c.setFont("Helvetica-Bold", 16); c.drawString(50, y, f"Invoice {inv.number}")
        c.setFont("Helvetica", 10); y -= 24
        c.drawString(50, y, f"Date: {to_tehran(inv.issued_at):%Y-%m-%d}   Currency: {inv.currency}"); y -= 30
        for i in inv.items:
            line = f"{str(i['desc']).encode('ascii', 'replace').decode()[:50]:<50} {i['hours']:>8} h x {float(i['rate']):>12,.0f}"
            c.drawString(50, y, line); y -= 16
        y -= 10
        for label, val in (("Subtotal", inv.subtotal), ("Discount", inv.discount), ("Tax %", inv.tax_percent), ("Total", inv.total),
                           ("Paid", inv.paid), ("Balance", inv.balance)):
            c.drawString(50, y, f"{label}: {val:,.2f}"); y -= 16
        c.save()
        return Path(dest)
