"""Human-readable reports: Markdown and HTML (year, month, per-client). Persian digits, RTL HTML."""
from __future__ import annotations

import datetime as dt
import html
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.database import Database
from ..core.models import Client, Invoice, Project, TimeEntry
from ..core.persian import MONTHS_FA, TEHRAN, format_duration, jalali_to_date, jalali_year_bounds, to_fa_digits, to_tehran
from .analytics import Analytics


def _table(rows: List[List[str]], head: List[str]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def year_markdown(db: Database, jalali_year: int) -> str:
    s = Analytics(db).year_summary(jalali_year)
    lines = [f"# گزارش سال {jalali_year}", "", f"- جمع ساعت: **{s.total_hours}**", f"- روزهای کاری: **{s.days_worked}**",
             f"- طولانی‌ترین رشته: **{s.longest_streak}** روز", f"- ساعت قابل صورتحساب: **{round(s.billable_sec / 3600, 2)}**", "",
             "## به تفکیک پروژه", _table([[html.escape(k), f"{v / 3600:.1f}"] for k, v in sorted(s.by_project.items(), key=lambda kv: -kv[1])], ["پروژه", "ساعت"]), "",
             "## به تفکیک ماه", _table([[MONTHS_FA[i], f"{v / 3600:.1f}"] for i, v in enumerate(s.by_month)], ["ماه", "ساعت"])]
    return to_fa_digits("\n".join(lines))


def month_markdown(db: Database, jy: int, jm: int) -> str:
    first = jalali_to_date(jy, jm, 1)
    nxt = jalali_to_date(jy + (jm == 12), jm % 12 + 1, 1)
    lo, hi = (dt.datetime.combine(d, dt.time(), tzinfo=TEHRAN) for d in (first, nxt))
    es = db.entries_between(lo, hi)
    names = {p.id: p.name for p in db.all(Project)}
    rows = [[to_tehran(e.start_utc).strftime("%m/%d %H:%M"), e.title.replace("|", "/"), names.get(e.project_id or "", "—"), format_duration(e.duration_sec)] for e in es]
    total = sum(e.duration_sec for e in es)
    return to_fa_digits(f"# {MONTHS_FA[jm - 1]} {jy}\n\nجمع: **{format_duration(total)}** ساعت در {len(es)} ثبت\n\n" + _table(rows, ["زمان", "عنوان", "پروژه", "مدت"]))


def client_report(db: Database, client_id: str) -> Dict[str, object]:
    """Hours per project, billed/paid/outstanding for one client."""
    c = db.get(Client, client_id)
    if c is None:
        raise KeyError(client_id)
    projects = [p for p in db.all(Project) if p.client_id == client_id]
    per = []
    for p in projects:
        sec = db.conn.execute("SELECT COALESCE(SUM(duration_sec),0) FROM entries WHERE project_id=? AND status='done'", (p.id,)).fetchone()[0]
        per.append({"project": p.name, "hours": round(sec / 3600, 2), "value": round(sec / 3600 * (p.rate_per_hour or c.default_rate), 2)})
    invs = [i for i in db.all(Invoice) if i.client_id == client_id]
    return {"client": c.name, "projects": per, "total_hours": round(sum(x["hours"] for x in per), 2),  # type: ignore[misc]
            "billed": round(sum(i.total for i in invs), 2), "paid": round(sum(i.paid for i in invs), 2),
            "outstanding": round(sum(i.balance for i in invs), 2), "invoices": len(invs)}


def to_html(markdown: str, title: str = "گزارش") -> str:
    """Tiny, safe Markdown->HTML (headings, bullets, bold, tables). Everything is escaped first."""
    out, in_table, in_list = [], False, False
    for raw in markdown.splitlines():
        line = html.escape(raw)
        bold = lambda t: __import__("re").sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= {"-"} for c in cells):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                out.append("<table>")
            in_table = True
            out.append("<tr>" + "".join(f"<{tag}>{bold(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>"); in_table = False
        if line.startswith("- "):
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{bold(line[2:])}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        if line.startswith("## "): out.append(f"<h2>{bold(line[3:])}</h2>")
        elif line.startswith("# "): out.append(f"<h1>{bold(line[2:])}</h1>")
        elif line.strip(): out.append(f"<p>{bold(line)}</p>")
    if in_table: out.append("</table>")
    if in_list: out.append("</ul>")
    return (f"<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Vazirmatn,Tahoma,sans-serif;"
            "margin:40px;max-width:800px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:right}</style>" + "\n".join(out) + "</html>")


def save(text: str, dest: Union[str, Path]) -> Path:
    dest = Path(dest)
    dest.write_text(text, encoding="utf-8")
    return dest
