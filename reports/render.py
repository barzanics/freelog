"""Rendering of report data: a self-contained print-ready HTML page (Jinja2, autoescaped), a compact e-mail version with inline styles (Gmail / Outlook safe), Markdown and JSON.
Charts are embedded as inline SVG. Nothing here talks to the database."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from jinja2 import DictLoader, Environment, select_autoescape
from markupsafe import Markup

from . import charts as ch, locale_us as us

RAG = {"on_track": ("#3E9B6A", "On track"), "at_risk": ("#E0A030", "At risk"), "off_track": ("#C94C4C", "Behind schedule")}

CSS = """
@page { size: A4; margin: 18mm 15mm 18mm 15mm; }
*{box-sizing:border-box} body{font-family:'Inter','Source Sans 3','Helvetica Neue',Arial,sans-serif;color:#1F2A37;margin:0;background:#F4F6F9;line-height:1.5;font-size:14px}
.page{max-width:860px;margin:24px auto;background:#fff;padding:40px 44px;border-radius:14px;box-shadow:0 6px 28px rgba(31,42,55,.08)}
@media print{body{background:#fff}.page{box-shadow:none;margin:0;padding:0;max-width:none;border-radius:0}.avoid{break-inside:avoid}}
header.top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:3px solid #2F5D8C;padding-bottom:16px;margin-bottom:22px}
.brand{display:flex;align-items:center;gap:12px}.brand img{max-height:46px;max-width:140px}.brand b{font-size:18px}
.meta{text-align:right;font-size:12px;color:#6B7A8F}.meta .num{font-weight:700;color:#1F2A37;font-size:13px}
h1{font-size:26px;margin:0 0 2px}h2{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:#2F5D8C;margin:28px 0 10px;border-bottom:1px solid #E3E8EF;padding-bottom:6px}
.sub{color:#6B7A8F;margin:0 0 6px}.summary{background:#F4F7FB;border-left:4px solid #2F5D8C;padding:14px 18px;border-radius:8px;font-size:15px}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;color:#fff;font-size:12px;font-weight:700}
.bar{background:#E3E8EF;border-radius:999px;height:12px;overflow:hidden}.bar i{display:block;height:100%;background:#2F5D8C}
table{width:100%;border-collapse:collapse;margin:6px 0}th{text-align:left;font-size:11px;text-transform:uppercase;color:#6B7A8F;border-bottom:1px solid #DDE3EA;padding:6px 8px}
td{padding:7px 8px;border-bottom:1px solid #EEF1F5;vertical-align:top}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:10px 0}.stat{background:#F4F7FB;border-radius:10px;padding:12px 14px}.stat b{display:block;font-size:22px}.stat span{font-size:12px;color:#6B7A8F}
.alert{background:#FFF6E5;border:1px solid #F2D79B;border-radius:10px;padding:12px 16px}.alert h3{margin:0 0 6px;font-size:14px;color:#9A6A00}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:14px}.charts .c{border:1px solid #EEF1F5;border-radius:10px;padding:8px}.charts svg{max-width:100%;height:auto}.charts .full{grid-column:1/-1}
ul.clean{margin:4px 0;padding-left:20px}.muted{color:#6B7A8F}.tot td{font-weight:700;border-top:2px solid #1F2A37}
footer{margin-top:34px;border-top:1px solid #DDE3EA;padding-top:14px;font-size:12px;color:#6B7A8F;display:flex;justify-content:space-between;gap:20px}
"""

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ d.header.title }} · {{ d.project.name }} · {{ d.header.period_label }}</title><style>{{ css }}</style></head><body><div class="page">
<header class="top"><div class="brand">{% if d.header.company.logo %}<img src="{{ d.header.company.logo }}" alt="">{% endif %}<div><b>{{ d.header.company.name }}</b>
{% if d.header.company.website %}<div class="muted">{{ d.header.company.website }}</div>{% endif %}</div></div>
<div class="meta">{% if d.header.client_logo %}<img src="{{ d.header.client_logo }}" alt="" style="max-height:34px"><br>{% endif %}<div class="num">{{ d.header.number }}</div>{{ d.header.generated_label }}</div></header>
<h1>{{ d.header.title }}</h1><p class="sub">{{ d.project.name }}{% if d.client.name %} · {{ d.client.company or d.client.name }}{% endif %} · {{ d.header.period_label }}</p>

<div class="summary avoid">{{ d.summary }}</div>

<h2>Progress</h2><div class="grid avoid">
<div class="stat"><b>{{ d.progress.pct|round|int }}%</b><span>complete</span></div>
<div class="stat"><b>{{ d.time.total_sec|hours }}</b><span>logged {{ 'today' if d.header.type == 'daily' else 'this period' }}</span></div>
<div class="stat"><b>{{ d.done|length }}</b><span>tasks completed</span></div>
<div class="stat"><b><span class="chip" style="background:{{ rag.color }}">{{ rag.label }}</span></b><span>project health</span></div></div>
<div class="bar"><i style="width:{{ d.progress.pct }}%"></i></div>
<p class="muted" style="margin:8px 0 0">{% for r in d.health.reasons %}{{ r.text }} {% endfor %}{% if d.forecast.projected_label %}Projected finish: {{ d.forecast.projected_label }}{% if d.forecast.late_days is not none %} ({{ d.forecast.late_days|abs }} day{{ '' if d.forecast.late_days|abs == 1 else 's' }} {{ 'late' if d.forecast.late_days > 0 else 'early' }}){% endif %}.{% endif %}</p>
{% if d.progress.milestones %}<table class="avoid"><tr><th>Milestone</th><th>Due</th><th class="n">Progress</th></tr>{% for m in d.progress.milestones %}
<tr><td>{{ m.name }}</td><td>{{ m.due_label or '—' }}</td><td class="n">{{ m.pct|round|int }}%</td></tr>{% endfor %}</table>{% endif %}

{% if d.waiting_on_client or d.decisions %}<h2>Waiting on you</h2><div class="alert avoid"><h3>We need your input to keep moving</h3><ul class="clean">
{% for w in d.waiting_on_client %}<li><b>{{ w.title }}</b>{% if w.reason %} — {{ w.reason }}{% endif %} <span class="muted">({{ w.days }} day{{ '' if w.days == 1 else 's' }})</span></li>{% endfor %}
{% for x in d.decisions %}<li><b>{{ x.title }}</b> <span class="muted">({{ 'approval needed' if x.kind == 'approval' else 'decision needed' }})</span></li>{% endfor %}</ul></div>{% endif %}

{% if d.done %}<h2>What got done</h2><table><tr><th>Task</th><th>Completed</th><th class="n">Time</th></tr>
{% for t in d.done %}<tr><td>{{ t.title }}{% if t.note %}<div class="muted">{{ t.note }}</div>{% endif %}</td><td>{{ t.completed_on|date }}</td><td class="n">{{ (t.hours*3600)|hm }}</td></tr>{% endfor %}</table>{% endif %}
{% if d.in_progress %}<h2>In progress</h2><table><tr><th>Task</th><th class="n">Progress</th><th>ETA</th><th class="n">Time</th></tr>
{% for t in d.in_progress %}<tr><td>{{ t.title }}{% if t.note %}<div class="muted">{{ t.note }}</div>{% endif %}</td><td class="n">{{ t.progress }}%</td><td>{{ t.eta|date }}</td><td class="n">{{ (t.hours*3600)|hm }}</td></tr>{% endfor %}</table>{% endif %}
{% if d.blockers %}<h2>Blockers</h2><ul class="clean">{% for b in d.blockers %}<li><b>{{ b.title }}</b>{% if b.reason %} — {{ b.reason }}{% endif %}</li>{% endfor %}</ul>{% endif %}

{% if d.time.total_sec %}<h2>Time breakdown</h2><div class="grid avoid" style="grid-template-columns:repeat(3,1fr)"><div class="stat"><b>{{ d.time.total_sec|hours }}</b><span>total</span></div>
<div class="stat"><b>{{ d.time.billable_sec|hours }}</b><span>billable ({{ d.time.billable_pct }}%)</span></div><div class="stat"><b>{{ d.time.non_billable_sec|hours }}</b><span>non-billable</span></div></div>
<table><tr><th>Task</th><th class="n">Time</th></tr>{% for t in d.time.by_task %}<tr><td>{{ t.title }}{% if not t.billable %} <span class="muted">(non-billable)</span>{% endif %}</td><td class="n">{{ t.sec|hm }}</td></tr>{% endfor %}</table>
{% if d.time.by_day|length > 1 %}<table><tr><th>Day</th><th class="n">Billable</th><th class="n">Non-billable</th></tr>{% for r in d.time.by_day %}<tr><td>{{ r.label }}</td><td class="n">{{ r.billable|hm }}</td><td class="n">{{ r.non_billable|hm }}</td></tr>{% endfor %}</table>{% endif %}{% endif %}

{% if charts %}<h2>Charts</h2><div class="charts">{% for name, c in charts.items() %}<div class="c avoid {{ 'full' if name in ('gantt','heatmap','burnup','burndown','trend') else '' }}">{{ c.svg|safe }}</div>{% endfor %}</div>{% endif %}

{% if d.milestone %}{% set m = d.milestone %}<h2>Milestone: {{ m.name }}</h2><p>{{ m.description }}</p><p class="muted">Due {{ m.due_label or '—' }}{% if m.completed_label %} · Completed {{ m.completed_label }}{% endif %} · {{ m.hours }} h spent</p>
{% if m.criteria %}<h3>Acceptance criteria</h3><ul class="clean">{% for c in m.criteria %}<li>{{ c }}</li>{% endfor %}</ul>{% endif %}
{% if m.tasks %}<table><tr><th>Task</th><th>Status</th><th class="n">Time</th></tr>{% for t in m.tasks %}<tr><td>{{ t.title }}</td><td>{{ 'Done' if t.done else 'Open' }}</td><td class="n">{{ (t.hours*3600)|hm }}</td></tr>{% endfor %}</table>{% endif %}
{% if m.sign_off %}<p><span class="chip" style="background:#3E9B6A">All deliverables approved</span></p>{% endif %}{% endif %}

{% if d.invoice %}{% set i = d.invoice %}<h2>Invoice {{ i.number }}</h2><p class="muted">Issued {{ i.issue_label }} · Due {{ i.due_label }} ({{ i.terms }}){% if i.rounding_min %} · time rounded up to {{ i.rounding_min }}-minute increments{% endif %}</p>
<table><tr><th>Description</th><th class="n">Hours</th><th class="n">Rate</th><th class="n">Amount</th></tr>{% for r in i['items'] %}<tr><td>{{ r.description }}</td><td class="n">{{ '%.2f'|format(r.hours) }}</td><td class="n">{{ r.rate|money(i.currency) }}</td><td class="n">{{ r.amount|money(i.currency) }}</td></tr>{% endfor %}
<tr><td colspan="3" class="n">Subtotal</td><td class="n">{{ i.subtotal|money(i.currency) }}</td></tr>{% if i.discount %}<tr><td colspan="3" class="n">Discount</td><td class="n">-{{ i.discount|money(i.currency) }}</td></tr>{% endif %}
{% if i.tax_percent %}<tr><td colspan="3" class="n">Tax ({{ i.tax_percent }}%)</td><td class="n">{{ i.tax|money(i.currency) }}</td></tr>{% endif %}<tr class="tot"><td colspan="3" class="n">Total due</td><td class="n">{{ i.total|money(i.currency) }}</td></tr></table>
{% if i.payment_instructions %}<p class="muted">{{ i.payment_instructions }}</p>{% endif %}{% if i.notes %}<p>{{ i.notes }}</p>{% endif %}{% endif %}

{% if d.next_plan %}<h2>Next period plan</h2><ul class="clean">{% for t in d.next_plan %}<li>{{ t.title }}{% if t.due %} <span class="muted">· due {{ t.due|date }}</span>{% endif %}{% if t.estimate_h %} <span class="muted">· ~{{ t.estimate_h }} h</span>{% endif %}</li>{% endfor %}</ul>{% endif %}
{% if d.deliverables %}<h2>Deliverables</h2><table><tr><th>Deliverable</th><th>Delivered</th><th>Status</th></tr>{% for x in d.deliverables %}<tr><td>{% if x.ref and x.ref.startswith('http') %}<a href="{{ x.ref }}">{{ x.title }}</a>{% else %}{{ x.title }}{% endif %}</td><td>{{ x.delivered|date }}</td><td>{{ {'pending':'Awaiting your review','approved':'Approved','changes_requested':'Changes requested'}[x.status] }}</td></tr>{% endfor %}</table>{% endif %}
{% if d.commitments %}<h2>Our commitments</h2><ul class="clean">{% for c in d.commitments %}<li>{{ c.text }}{% if c.due %} <span class="muted">· by {{ c.due|date }}</span>{% endif %}</li>{% endfor %}</ul>{% endif %}
{% if d.meetings %}<h2>Meetings</h2>{% for m in d.meetings %}<p><b>{{ m.at|date }}</b> · {{ m.minutes }} min — {{ m.summary }}</p>{% if m.actions %}<ul class="clean">{% for a in m.actions %}<li>{{ a }}</li>{% endfor %}</ul>{% endif %}{% endfor %}{% endif %}
{% if d.changes %}<h2>Change log</h2><ul class="clean">{% for c in d.changes %}<li><span class="muted">{{ c.at|date }}</span> · {{ c.text }}</li>{% endfor %}</ul>{% endif %}
{% if d.risks %}<h2>Risks</h2><table><tr><th>Risk</th><th>Level</th><th>Mitigation</th></tr>{% for r in d.risks %}<tr><td>{{ r.title }}</td><td>{{ r.level|capitalize }}</td><td>{{ r.mitigation }}</td></tr>{% endfor %}</table>{% endif %}
{% if d.holiday_warnings %}<h2>Calendar notes</h2><ul class="clean">{% for w in d.holiday_warnings %}<li>{{ w.title }} is due {{ w.date|date }} ({{ w.why }}).</li>{% endfor %}</ul>{% endif %}
{% if d.scope %}<h2>Scope</h2><p>{{ d.scope.added|length }} item(s) added since the agreed baseline (+{{ d.scope.added_hours }} h, {{ d.scope.pct }}%).</p>{% endif %}
{% if portal_url %}<p><a href="{{ portal_url }}">View this report online</a></p>{% endif %}
<footer><div><b>{{ d.header.company.signature }}</b><br>{{ d.header.company.name }}{% if d.header.company.email %} · {{ d.header.company.email }}{% endif %}{% if d.header.company.phone %} · {{ d.header.company.phone }}{% endif %}
{% if d.header.company.tax_id %}<br>Tax ID {{ d.header.company.tax_id }}{% endif %}</div><div style="text-align:right">{{ d.header.number }}{% if d.header.company.terms_url %}<br><a href="{{ d.header.company.terms_url }}">Terms</a>{% endif %}</div></footer>
</div></body></html>"""

EMAIL = """<!doctype html><html><body style="margin:0;background:#F4F6F9;font-family:Arial,Helvetica,sans-serif;color:#1F2A37"><table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F9"><tr><td align="center" style="padding:24px 12px">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:12px"><tr><td style="padding:26px 30px;border-bottom:3px solid #2F5D8C"><b style="font-size:16px">{{ d.header.company.name }}</b>
<div style="color:#6B7A8F;font-size:12px;margin-top:2px">{{ d.header.title }} · {{ d.header.number }}</div></td></tr>
<tr><td style="padding:24px 30px"><div style="font-size:20px;font-weight:700">{{ d.project.name }}</div><div style="color:#6B7A8F;font-size:13px;margin-bottom:16px">{{ d.header.period_label }}</div>
<div style="background:#F4F7FB;border-left:4px solid #2F5D8C;padding:12px 16px;font-size:15px;line-height:1.5">{{ d.summary }}</div>
<table width="100%" cellpadding="0" cellspacing="8" style="margin-top:14px"><tr>
<td style="background:#F4F7FB;border-radius:8px;padding:10px 12px"><b style="font-size:20px">{{ d.progress.pct|round|int }}%</b><br><span style="font-size:12px;color:#6B7A8F">complete</span></td>
<td style="background:#F4F7FB;border-radius:8px;padding:10px 12px"><b style="font-size:20px">{{ d.time.total_sec|hours }}</b><br><span style="font-size:12px;color:#6B7A8F">logged</span></td>
<td style="background:#F4F7FB;border-radius:8px;padding:10px 12px"><b style="font-size:20px">{{ d.done|length }}</b><br><span style="font-size:12px;color:#6B7A8F">tasks done</span></td>
<td style="background:#F4F7FB;border-radius:8px;padding:10px 12px"><b style="font-size:14px;color:{{ rag.color }}">{{ rag.label }}</b><br><span style="font-size:12px;color:#6B7A8F">health</span></td></tr></table>
{% if d.waiting_on_client or d.decisions %}<div style="background:#FFF6E5;border:1px solid #F2D79B;border-radius:8px;padding:12px 16px;margin-top:14px"><b style="color:#9A6A00">Waiting on you</b><ul style="margin:6px 0 0;padding-left:18px">
{% for w in d.waiting_on_client %}<li>{{ w.title }}</li>{% endfor %}{% for x in d.decisions %}<li>{{ x.title }}</li>{% endfor %}</ul></div>{% endif %}
{% if d.done %}<div style="margin-top:14px"><b>Done</b><ul style="margin:6px 0 0;padding-left:18px">{% for t in d.done[:6] %}<li>{{ t.title }}</li>{% endfor %}</ul></div>{% endif %}
{% if d.next_plan %}<div style="margin-top:14px"><b>Next</b><ul style="margin:6px 0 0;padding-left:18px">{% for t in d.next_plan[:5] %}<li>{{ t.title }}</li>{% endfor %}</ul></div>{% endif %}
{% if portal_url %}<div style="text-align:center;margin:24px 0 6px"><a href="{{ portal_url }}" style="background:#2F5D8C;color:#fff;text-decoration:none;padding:12px 26px;border-radius:8px;font-weight:700;display:inline-block">View the full report</a></div>{% endif %}
</td></tr><tr><td style="padding:16px 30px;border-top:1px solid #E3E8EF;font-size:12px;color:#6B7A8F">{{ d.header.company.signature }} · {{ d.header.company.name }}{% if d.header.company.email %} · {{ d.header.company.email }}{% endif %}</td></tr></table></td></tr></table>
{% if pixel_url %}<img src="{{ pixel_url }}" width="1" height="1" alt="" style="display:none">{% endif %}</body></html>"""


def _env() -> Environment:
    env = Environment(loader=DictLoader({"report.html": HTML, "email.html": EMAIL}), autoescape=select_autoescape(["html"], default=True))
    env.filters.update({"hm": lambda s: us.fmt_hm(s or 0), "hours": lambda s: us.fmt_hours(s or 0), "money": us.fmt_money,
                        "date": lambda s: us.fmt_date(__import__("datetime").date.fromisoformat(str(s)[:10])) if s else "—"})
    return env


def rag_of(d: Dict[str, Any]) -> Dict[str, str]:
    color, label = RAG[d["health"]["status"]]
    return {"color": color, "label": label}


def to_markdown(d: Dict[str, Any]) -> str:
    h, t = d["header"], d["time"]
    out = [f"# {h['title']} — {d['project']['name']}", f"*{h['period_label']} · {h['number']}*", "", f"> {d['summary']}", "",
           f"**Progress:** {d['progress']['pct']:.0f}% · **Logged:** {us.fmt_hours(t['total_sec'])} · **Health:** {RAG[d['health']['status']][1]}", ""]
    for title, rows in (("Waiting on you", [w["title"] + (f" — {w['reason']}" if w["reason"] else "") for w in d["waiting_on_client"]] + [x["title"] for x in d["decisions"]]),
                        ("What got done", [f"{x['title']} ({us.fmt_hm(x['hours'] * 3600)})" for x in d["done"]]), ("In progress", [f"{x['title']} — {x['progress']}%" for x in d["in_progress"]]),
                        ("Next period plan", [x["title"] for x in d["next_plan"]]), ("Commitments", [c["text"] for c in d["commitments"]]), ("Change log", [f"{c['at']}: {c['text']}" for c in d["changes"]])):
        if rows:
            out += [f"## {title}", ""] + [f"- {r}" for r in rows] + [""]
    if t["by_task"]:
        out += ["## Time breakdown", "", "| Task | Time |", "|---|---:|"] + [f"| {x['title']} | {us.fmt_hm(x['sec'])} |" for x in t["by_task"]] + [""]
    if d.get("invoice"):
        i = d["invoice"]
        out += [f"## Invoice {i['number']}", "", "| Description | Hours | Rate | Amount |", "|---|---:|---:|---:|"] + [f"| {r['description']} | {r['hours']:.2f} | {us.fmt_money(r['rate'], i['currency'])} | {us.fmt_money(r['amount'], i['currency'])} |" for r in i["items"]]
        out += ["", f"**Total due: {us.fmt_money(i['total'], i['currency'])}** ({i['terms']}, due {i['due_label']})", ""]
    return "\n".join(out)


def render_all(d: Dict[str, Any], portal_url: Optional[str] = None, pixel_url: Optional[str] = None, with_charts: bool = True) -> Dict[str, Any]:
    """HTML (with inline SVG charts), e-mail HTML, Markdown, JSON, plus the chart images (PNG bytes) for the PDF."""
    env = _env()
    made = ch.build_charts(d.get("series", {}), d.get("charts", [])) if with_charts else {}
    ctx = {"d": d, "css": Markup(CSS), "rag": rag_of(d), "charts": {k: {"svg": Markup(v["svg"])} for k, v in made.items()}, "portal_url": portal_url, "pixel_url": pixel_url}
    return {"html": env.get_template("report.html").render(**ctx), "email": env.get_template("email.html").render(**ctx), "md": to_markdown(d),
            "json": json.dumps(d, ensure_ascii=False, indent=1, default=str), "charts": made}
