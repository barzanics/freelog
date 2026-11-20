"""PDF output. WeasyPrint (HTML -> PDF, pixel-identical to the web version) when it is installed; otherwise a ReportLab layout of the same data - A4, header / footer with
"Page X of Y", professional fonts if found in ``assets/fonts`` (Inter / Source Sans), DejaVu Sans as a wide-coverage fallback."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, Optional

from . import locale_us as us
from .render import RAG

BLUE, INK, GRAY, LIGHT = "#2F5D8C", "#1F2A37", "#6B7A8F", "#DDE3EA"


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except Exception:  # noqa: BLE001 - also raised when its native libraries are missing
        return False


def _fonts(assets: Optional[Path]) -> Dict[str, str]:
    """Register a regular + bold TTF pair; returns the font names to use."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    cands = []
    for d in [p for p in (assets,) if p]:
        for fam in ("Inter", "SourceSans3", "SourceSansPro", "SourceSans"):
            cands += [(fam, next(iter(d.rglob(f"{fam}*Regular*.ttf")), None), next(iter(d.rglob(f"{fam}*Bold*.ttf")), None))]
    try:
        import matplotlib
        mp = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        cands.append(("DejaVuSans", mp / "DejaVuSans.ttf", mp / "DejaVuSans-Bold.ttf"))
    except Exception:  # noqa: BLE001
        pass
    for fam, reg, bold in cands:
        if reg and bold and Path(reg).exists() and Path(bold).exists():
            try:
                pdfmetrics.registerFont(TTFont(fam, str(reg))); pdfmetrics.registerFont(TTFont(fam + "-Bold", str(bold)))
                return {"regular": fam, "bold": fam + "-Bold"}
            except Exception:  # noqa: BLE001
                continue
    return {"regular": "Helvetica", "bold": "Helvetica-Bold"}


def render_reportlab(d: Dict[str, Any], charts: Dict[str, Dict[str, Any]], path: Path, assets: Optional[Path] = None) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import Flowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    f = _fonts(assets)
    st = {"p": ParagraphStyle("p", fontName=f["regular"], fontSize=9.5, leading=13.5, textColor=colors.HexColor(INK)),
          "h1": ParagraphStyle("h1", fontName=f["bold"], fontSize=20, leading=24, textColor=colors.HexColor(INK)),
          "h2": ParagraphStyle("h2", fontName=f["bold"], fontSize=10.5, leading=14, textColor=colors.HexColor(BLUE), spaceBefore=14, spaceAfter=4),
          "m": ParagraphStyle("m", fontName=f["regular"], fontSize=8.5, leading=11, textColor=colors.HexColor(GRAY)),
          "sum": ParagraphStyle("sum", fontName=f["regular"], fontSize=10.5, leading=15, textColor=colors.HexColor(INK), backColor=colors.HexColor("#F4F7FB"), borderPadding=(8, 10, 8, 10), leftIndent=6)}
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    P = lambda s, k="p": Paragraph(esc(s), st[k])
    h = d["header"]

    class Bar(Flowable):
        def __init__(self, pct: float, w: float) -> None:
            super().__init__(); self.pct, self.w, self.height = pct, w, 8
        def wrap(self, aw, ah):
            return self.w, self.height
        def draw(self):
            self.canv.setFillColor(colors.HexColor(LIGHT)); self.canv.roundRect(0, 0, self.w, 7, 3.5, stroke=0, fill=1)
            self.canv.setFillColor(colors.HexColor(BLUE)); self.canv.roundRect(0, 0, max(7, self.w * self.pct / 100), 7, 3.5, stroke=0, fill=1)

    def table(rows, widths, right=()):
        t = Table(rows, colWidths=widths, repeatRows=1)
        ts = [("FONTNAME", (0, 0), (-1, 0), f["bold"]), ("FONTNAME", (0, 1), (-1, -1), f["regular"]), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(GRAY)),
              ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(LIGHT)), ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#EEF1F5")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        ts += [("ALIGN", (c, 0), (c, -1), "RIGHT") for c in right]
        t.setStyle(TableStyle(ts))
        return t

    W = A4[0] - 30 * mm
    story: list = [P(h["title"], "h1"), P(f"{d['project']['name']} · {d['client'].get('company') or d['client'].get('name', '')} · {h['period_label']}", "m"), Spacer(1, 8), P(d["summary"], "sum"), Spacer(1, 10)]
    pr, hl, t = d["progress"], d["health"], d["time"]
    story += [P("PROGRESS", "h2"), Bar(pr["pct"], W), Spacer(1, 4), P(f"{pr['pct']:.0f}% complete · {us.fmt_hours(t['total_sec'])} logged · {len(d['done'])} task(s) completed · {RAG[hl['status']][1]}"),
              P(" ".join(r["text"] for r in hl["reasons"]), "m")]
    if d["progress"]["milestones"]:
        story.append(table([["Milestone", "Due", "Progress"]] + [[m["name"], us.fmt_date(__import__("datetime").datetime.fromisoformat(m["due"]).date()) if m.get("due") else "—", f"{m['pct']:.0f}%"] for m in pr["milestones"]], [W * .6, W * .22, W * .18], (2,)))
    if d["waiting_on_client"] or d["decisions"]:
        story += [P("WAITING ON YOU", "h2")] + [P("• " + w["title"] + (f" — {w['reason']}" if w["reason"] else "") + f" ({w['days']} d)") for w in d["waiting_on_client"]] + [P("• " + x["title"]) for x in d["decisions"]]
    if d["done"]:
        story += [P("WHAT GOT DONE", "h2"), table([["Task", "Completed", "Time"]] + [[Paragraph(esc(x["title"]), st["p"]), us.fmt_date(__import__("datetime").date.fromisoformat(x["completed_on"])), us.fmt_hm(x["hours"] * 3600)] for x in d["done"]], [W * .6, W * .24, W * .16], (2,))]
    if d["in_progress"]:
        story += [P("IN PROGRESS", "h2"), table([["Task", "Progress", "ETA", "Time"]] + [[Paragraph(esc(x["title"]), st["p"]), f"{x['progress']}%", us.fmt_date(__import__("datetime").date.fromisoformat(x["eta"])) if x["eta"] else "—", us.fmt_hm(x["hours"] * 3600)] for x in d["in_progress"]], [W * .5, W * .13, W * .22, W * .15], (1, 3))]
    if t["by_task"]:
        story += [P("TIME BREAKDOWN", "h2"), P(f"Total {us.fmt_hours(t['total_sec'])} · billable {us.fmt_hours(t['billable_sec'])} ({t['billable_pct']}%) · non-billable {us.fmt_hours(t['non_billable_sec'])}", "m"),
                  table([["Task", "Time"]] + [[Paragraph(esc(x["title"]) + ("" if x["billable"] else " (non-billable)"), st["p"]), us.fmt_hm(x["sec"])] for x in t["by_task"]], [W * .8, W * .2], (1,))]
    for name, c in charts.items():
        img = Image(io.BytesIO(c["png"])); ratio = img.imageHeight / float(img.imageWidth); w = W * (0.62 if name == "donut" else 0.95)
        img.drawWidth, img.drawHeight = w, w * ratio
        story.append(KeepTogether([P(name.upper(), "h2"), img]))
    if d.get("milestone"):
        m = d["milestone"]
        story += [P("MILESTONE: " + m["name"].upper(), "h2"), P(m["description"]), P(f"Due {m['due_label'] or '—'} · {m['hours']} h spent" + (f" · completed {m['completed_label']}" if m["completed_label"] else ""), "m")]
        story += [P("• " + c) for c in m["criteria"]] + ([table([["Task", "Status", "Time"]] + [[Paragraph(esc(x["title"]), st["p"]), "Done" if x["done"] else "Open", us.fmt_hm(x["hours"] * 3600)] for x in m["tasks"]], [W * .6, W * .2, W * .2], (2,))] if m["tasks"] else [])
    if d.get("invoice"):
        i = d["invoice"]; money = lambda v: us.fmt_money(v, i["currency"])
        rows = [["Description", "Hours", "Rate", "Amount"]] + [[Paragraph(esc(r["description"]), st["p"]), f"{r['hours']:.2f}", money(r["rate"]), money(r["amount"])] for r in i["items"]]
        rows += [["", "", "Subtotal", money(i["subtotal"])]] + ([["", "", "Discount", "-" + money(i["discount"])]] if i["discount"] else []) + ([["", "", f"Tax ({i['tax_percent']}%)", money(i["tax"])]] if i["tax_percent"] else []) + [["", "", "Total due", money(i["total"])]]
        story += [P(f"INVOICE {i['number']}", "h2"), P(f"Issued {i['issue_label']} · Due {i['due_label']} ({i['terms']})", "m"), table(rows, [W * .5, W * .14, W * .18, W * .18], (1, 2, 3))]
        if i["payment_instructions"]:
            story.append(P(i["payment_instructions"], "m"))
    for title, key, fmt in (("NEXT PERIOD PLAN", "next_plan", lambda x: x["title"] + (f" · due {us.fmt_date(__import__('datetime').date.fromisoformat(x['due']))}" if x["due"] else "")),
                            ("DELIVERABLES", "deliverables", lambda x: x["title"] + f" — {x['status'].replace('_', ' ')}"), ("OUR COMMITMENTS", "commitments", lambda x: x["text"]),
                            ("CHANGE LOG", "changes", lambda x: f"{x['at']}: {x['text']}"), ("RISKS", "risks", lambda x: f"{x['title']} ({x['level']})")):
        if d.get(key):
            story += [P(title, "h2")] + [P("• " + fmt(x)) for x in d[key]]

    class Numbered(rl_canvas.Canvas):
        def __init__(self, *a, **k):
            super().__init__(*a, **k); self._pages = []
        def showPage(self):
            self._pages.append(dict(self.__dict__)); self._startPage()
        def save(self):
            n = len(self._pages)
            for s in self._pages:
                self.__dict__.update(s); self._chrome(n); super().showPage()
            super().save()
        def _chrome(self, n):
            self.setFont(f["bold"], 8.5); self.setFillColor(colors.HexColor(BLUE)); self.drawString(15 * mm, A4[1] - 11 * mm, h["company"]["name"])
            self.setFont(f["regular"], 8); self.setFillColor(colors.HexColor(GRAY)); self.drawRightString(A4[0] - 15 * mm, A4[1] - 11 * mm, f"{h['number']} · {h['period_label']}")
            self.setStrokeColor(colors.HexColor(LIGHT)); self.line(15 * mm, A4[1] - 13 * mm, A4[0] - 15 * mm, A4[1] - 13 * mm); self.line(15 * mm, 13 * mm, A4[0] - 15 * mm, 13 * mm)
            self.drawString(15 * mm, 8 * mm, f"{h['company']['signature']} · {h['company'].get('email', '')}".strip(" ·")); self.drawRightString(A4[0] - 15 * mm, 8 * mm, f"Page {self._pageNumber} of {n}")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=20 * mm, bottomMargin=20 * mm, title=f"{h['title']} {h['number']}", author=h["company"]["name"]).build(story, canvasmaker=Numbered)
    return path


def render_pdf(d: Dict[str, Any], rendered: Dict[str, Any], path: Path, assets: Optional[Path] = None, prefer_weasyprint: bool = True) -> Path:
    """Write the PDF; returns the path. Uses WeasyPrint when available, ReportLab otherwise."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if prefer_weasyprint and weasyprint_available():
        try:
            from weasyprint import HTML
            HTML(string=rendered["html"]).write_pdf(str(path))
            return path
        except Exception:  # noqa: BLE001 - fall through to ReportLab
            import logging
            logging.getLogger("worktracker.pdf").exception("weasyprint failed; using reportlab")
    return render_reportlab(d, rendered.get("charts", {}), path, assets)
