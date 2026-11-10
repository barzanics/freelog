"""Recurring (retainer) invoices: define once, generate once per Jalali month (idempotent)."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from ..core.database import Database
from ..core.models import Client, Invoice
from ..core.persian import date_to_jalali, now_utc, to_tehran
from .billing import Billing


def define(db: Database, client_id: str, description: str, hours: float, rate: float, day_of_month: int = 1, tax_percent: float = 0.0) -> None:
    if db.get(Client, client_id) is None:
        raise KeyError(client_id)
    if hours <= 0 or rate < 0 or not 1 <= day_of_month <= 29 or not description.strip():
        raise ValueError("invalid retainer")
    d = db.get_setting("retainers", {})
    d[client_id] = {"description": description, "hours": hours, "rate": rate, "day": day_of_month, "tax": tax_percent, "last": None}
    db.set_setting("retainers", d)


def run_due(db: Database, today: Optional[dt.date] = None) -> List[Invoice]:
    """Create the invoice of each retainer whose day has arrived this Jalali month and that was not yet invoiced this month."""
    today = today or to_tehran(now_utc()).date()
    jy, jm, jd = date_to_jalali(today)
    key = f"{jy}-{jm:02d}"
    made: List[Invoice] = []
    cfg: Dict[str, dict] = db.get_setting("retainers", {})
    b = Billing(db)
    with db.transaction():
        for cid, r in cfg.items():
            if r["last"] == key or jd < r["day"]:
                continue
            made.append(b.create_retainer(cid, f"{r['description']} {key}", r["hours"], r["rate"], r["tax"]))
            r["last"] = key
        db.set_setting("retainers", cfg)
    return made
