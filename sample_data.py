"""Deterministic sample-data generator: 10 projects, 5 clients, 500 entries, 20 invoices."""
from __future__ import annotations

import datetime as dt
import random
from typing import Dict

from .core.database import Database
from .core.models import Client, Invoice, InvoiceStatus, Project, Status, TimeEntry
from .core.persian import TEHRAN, UTC

TITLES = ["طراحی صفحه اصلی", "رفع باگ ورود", "جلسه با مشتری", "نوشتن مستندات", "بازبینی کد", "تحلیل نیازمندی‌ها",
          "پیاده‌سازی API", "تست یکپارچگی", "پاسخ به ایمیل‌ها", "برنامه‌ریزی اسپرینت"]
CATS = ["development", "design", "meeting", "docs", "review", "analysis"]


def generate(db: Database, seed: int = 1, entries: int = 500, projects: int = 10, clients: int = 5, invoices: int = 20,
             end: dt.date = dt.date(2026, 3, 15)) -> Dict[str, int]:
    rnd = random.Random(seed)
    cl = [Client(name=f"مشتری {i + 1}", default_rate=rnd.choice([300000, 450000, 600000]), tags=["sample"]) for i in range(clients)]
    pr = [Project(name=f"پروژه {i + 1}", client_id=cl[i % clients].id, rate_per_hour=rnd.choice([0, 500000, 700000]),
                  estimated_hours=rnd.choice([40, 80, 160]), color=rnd.choice(["#6D5DFC", "#00E5FF", "#FF3D71"])) for i in range(projects)]
    with db.transaction():
        for o in (*cl, *pr):
            db.save(o)
        for _ in range(entries):
            day = end - dt.timedelta(days=rnd.randint(0, 365))
            hour, minutes = rnd.randint(8, 18), rnd.choice([30, 45, 60, 90, 120])
            start = dt.datetime.combine(day, dt.time(hour, rnd.choice([0, 15, 30])), tzinfo=TEHRAN).astimezone(UTC)
            p = rnd.choice(pr)
            db.save(TimeEntry(title=rnd.choice(TITLES), start_utc=start, end_utc=start + dt.timedelta(minutes=minutes),
                              project_id=p.id, category=rnd.choice(CATS), tags=rnd.sample(["urgent", "bug", "client", "internal"], rnd.randint(0, 2)),
                              billable=rnd.random() < 0.7, status=Status.DONE, energy=rnd.randint(0, 5),
                              estimated_min=rnd.choice([0, 60, 120])))
        for i in range(invoices):
            c = cl[i % clients]
            inv = Invoice(client_id=c.id, number=f"INV-S-{i + 1:04d}", currency=c.currency, tax_percent=rnd.choice([0, 9]),
                          items=[{"desc": f"پروژه {rnd.randint(1, projects)}", "hours": rnd.randint(2, 40), "rate": c.default_rate}])
            st = rnd.choice(["paid", "partial", "sent", "draft"])
            if st == "paid":
                inv.apply_payment(inv.total)
            elif st == "partial":
                inv.apply_payment(round(inv.total / 2, 2))
            else:
                inv.status = InvoiceStatus(st)
            db.save(inv)
    return {"clients": clients, "projects": projects, "entries": entries, "invoices": invoices}
