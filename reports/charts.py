"""Charts for client reports (matplotlib, Agg backend): burndown, burnup, velocity, cumulative flow, Gantt, donut, activity heatmap, billable trend, period comparison.
Every function returns ``{"svg": str, "png": bytes}`` or None when there is not enough data - the templates simply skip a missing chart. Light, print-friendly palette."""
from __future__ import annotations

import datetime as dt
import io
from typing import Any, Dict, List, Optional, Sequence

PALETTE = {"blue": "#2F5D8C", "green": "#3E9B6A", "amber": "#E0A030", "red": "#C94C4C", "gray": "#6B7A8F", "light": "#DDE3EA", "ink": "#1F2A37"}
SERIES = ["#2F5D8C", "#3E9B6A", "#E0A030", "#8A6FBF", "#C94C4C", "#2A9DB0", "#6B7A8F", "#B9783F"]


def have_matplotlib() -> bool:
    try:
        import matplotlib  # noqa: F401
        return True
    except ImportError:
        return False


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.fonttype": "path", "font.size": 9, "axes.edgecolor": PALETTE["light"], "axes.labelcolor": PALETTE["ink"], "xtick.color": PALETTE["gray"], "ytick.color": PALETTE["gray"],
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#EEF1F5", "grid.linewidth": 0.8, "figure.facecolor": "white", "axes.facecolor": "white"})
    return plt


def _out(fig, plt) -> Dict[str, Any]:
    svg, png = io.StringIO(), io.BytesIO()
    fig.savefig(svg, format="svg", bbox_inches="tight")
    fig.savefig(png, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    text = svg.getvalue()
    return {"svg": text[text.index("<svg"):], "png": png.getvalue()}


def _d(v: Any) -> dt.date:
    return v if isinstance(v, dt.date) else dt.date.fromisoformat(str(v)[:10])


def burndown(days: Sequence[Any], ideal: Sequence[float], actual: Sequence[Optional[float]]) -> Optional[Dict[str, Any]]:
    if len(days) < 2:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    xs = [_d(d) for d in days]
    ax.plot(xs, ideal, "--", color=PALETTE["gray"], lw=1.6, label="Ideal")
    pts = [(x, a) for x, a in zip(xs, actual) if a is not None]
    if pts:
        ax.plot(*zip(*pts), color=PALETTE["blue"], lw=2.4, marker="o", ms=3, label="Remaining")
        ax.fill_between([p[0] for p in pts], [p[1] for p in pts], alpha=0.08, color=PALETTE["blue"])
    ax.set_ylabel("Hours remaining"); ax.set_ylim(bottom=0); ax.legend(frameon=False, loc="upper right"); fig.autofmt_xdate()
    return _out(fig, plt)


def burnup(days: Sequence[Any], done: Sequence[float], scope: Sequence[float]) -> Optional[Dict[str, Any]]:
    if len(days) < 2:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    xs = [_d(d) for d in days]
    ax.step(xs, scope, where="post", color=PALETTE["gray"], lw=1.6, ls="--", label="Total scope")
    ax.plot(xs, done, color=PALETTE["green"], lw=2.4, marker="o", ms=3, label="Completed")
    ax.fill_between(xs, done, alpha=0.1, color=PALETTE["green"])
    ax.set_ylabel("Hours"); ax.set_ylim(bottom=0); ax.legend(frameon=False, loc="upper left"); fig.autofmt_xdate()
    return _out(fig, plt)


def velocity(weeks: Sequence[str], hours: Sequence[float]) -> Optional[Dict[str, Any]]:
    if not weeks:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.bar(weeks, hours, color=PALETTE["blue"], width=0.6)
    avg = sum(hours) / len(hours)
    ax.axhline(avg, color=PALETTE["amber"], lw=1.6, ls="--"); ax.text(len(weeks) - 0.5, avg, f" avg {avg:.1f}", color=PALETTE["amber"], va="bottom", ha="right")
    ax.set_ylabel("Hours of work completed")
    return _out(fig, plt)


def cumulative_flow(days: Sequence[Any], todo: Sequence[int], doing: Sequence[int], done: Sequence[int]) -> Optional[Dict[str, Any]]:
    if len(days) < 2:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    xs = [_d(d) for d in days]
    ax.stackplot(xs, done, doing, todo, colors=[PALETTE["green"], PALETTE["amber"], PALETTE["light"]], labels=["Done", "In progress", "To do"])
    ax.set_ylabel("Tasks"); ax.legend(frameon=False, loc="upper left", ncol=3); fig.autofmt_xdate()
    return _out(fig, plt)


def gantt(rows: Sequence[Dict[str, Any]], today: Optional[dt.date] = None) -> Optional[Dict[str, Any]]:
    """rows: {name, start, end, pct}. Bars show the plan; the darker part is the finished share."""
    rows = [r for r in rows if r.get("start") and r.get("end")]
    if not rows:
        return None
    plt = _plt()
    import matplotlib.dates as mdates
    fig, ax = plt.subplots(figsize=(6.4, 0.55 * len(rows) + 1.2))
    for i, r in enumerate(rows):
        a, b = _d(r["start"]), max(_d(r["end"]), _d(r["start"]) + dt.timedelta(days=1))
        width = (b - a).days
        ax.barh(i, width, left=mdates.date2num(a), color=PALETTE["light"], height=0.5)
        ax.barh(i, width * max(0.0, min(1.0, r.get("pct", 0) / 100)), left=mdates.date2num(a), color=PALETTE["green"] if r.get("pct", 0) >= 100 else PALETTE["blue"], height=0.5)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"] for r in rows]); ax.invert_yaxis(); ax.xaxis_date(); ax.grid(axis="y", visible=False)
    if today:
        ax.axvline(mdates.date2num(today), color=PALETTE["red"], lw=1.4); ax.text(mdates.date2num(today), -0.7, " today", color=PALETTE["red"], fontsize=8)
    fig.autofmt_xdate()
    return _out(fig, plt)


def donut(labels: Sequence[str], values: Sequence[float]) -> Optional[Dict[str, Any]]:
    pairs = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not pairs:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    pairs.sort(key=lambda p: -p[1])
    if len(pairs) > 7:
        pairs = pairs[:6] + [("Other", sum(v for _l, v in pairs[6:]))]
    ax.pie([v for _l, v in pairs], colors=SERIES[:len(pairs)], startangle=90, counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "white"})
    total = sum(v for _l, v in pairs)
    ax.text(0, 0, f"{total:.1f} h", ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["ink"])
    ax.legend([f"{l}  ({v / total * 100:.0f}%)" for l, v in pairs], loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=8)
    return _out(fig, plt)


def heatmap(day_hours: Dict[Any, float], weeks: int = 12, end: Optional[dt.date] = None) -> Optional[Dict[str, Any]]:
    """GitHub-style activity grid (columns = weeks, rows = Sun..Sat)."""
    if not day_hours:
        return None
    plt = _plt()
    from matplotlib.colors import LinearSegmentedColormap
    end = end or max(_d(k) for k in day_hours)
    start = end - dt.timedelta(days=weeks * 7 - 1 + (end.weekday() + 1) % 7)
    data = [[None] * weeks for _ in range(7)]
    d = start
    while d <= end:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        if col < weeks:
            data[row][col] = day_hours.get(d, day_hours.get(d.isoformat(), 0.0))
        d += dt.timedelta(days=1)
    import numpy as np
    arr = np.array([[np.nan if v is None else v for v in r] for r in data], dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 1.9))
    ax.imshow(arr, cmap=LinearSegmentedColormap.from_list("w", ["#EEF1F5", "#9EC5E8", PALETTE["blue"]]), aspect="equal", vmin=0, vmax=max(1.0, float(np.nanmax(arr))))
    ax.set_yticks(range(7)); ax.set_yticklabels(["Sun", "", "Tue", "", "Thu", "", "Sat"], fontsize=7); ax.set_xticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    return _out(fig, plt)


def trend(labels: Sequence[str], billable: Sequence[float], non_billable: Optional[Sequence[float]] = None) -> Optional[Dict[str, Any]]:
    if len(labels) < 2:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.plot(labels, billable, color=PALETTE["blue"], lw=2.4, marker="o", ms=4, label="Billable")
    ax.fill_between(labels, billable, alpha=0.08, color=PALETTE["blue"])
    if non_billable and any(non_billable):
        ax.plot(labels, non_billable, color=PALETTE["gray"], lw=1.6, ls="--", label="Non-billable")
    ax.set_ylabel("Hours per week"); ax.set_ylim(bottom=0); ax.legend(frameon=False)
    return _out(fig, plt)


def comparison(items: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """items: {label, current, previous}. Horizontal bars of the change in %, green up / red down."""
    items = [i for i in items if i.get("previous") or i.get("current")]
    if not items:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.0, 0.5 * len(items) + 1.0))
    deltas = [((i["current"] - i["previous"]) / i["previous"] * 100) if i["previous"] else (100.0 if i["current"] else 0.0) for i in items]
    ax.barh(range(len(items)), deltas, color=[PALETTE["green"] if d >= 0 else PALETTE["red"] for d in deltas], height=0.5)
    ax.set_yticks(range(len(items))); ax.set_yticklabels([i["label"] for i in items]); ax.invert_yaxis(); ax.axvline(0, color=PALETTE["gray"], lw=1); ax.grid(axis="y", visible=False)
    for k, d in enumerate(deltas):
        ax.text(d, k, f" {d:+.0f}%", va="center", ha="left" if d >= 0 else "right", fontsize=8, color=PALETTE["ink"])
    ax.set_xlabel("Change vs previous period")
    return _out(fig, plt)


def build_charts(series: Dict[str, Any], wanted: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Make the requested charts from the numeric ``series`` stored in a report's data. A failing chart never breaks the report."""
    if not have_matplotlib():
        return {}
    makers = {"burndown": lambda s: burndown(s["burndown"]["days"], s["burndown"]["ideal"], s["burndown"]["actual"]) if s.get("burndown") else None,
              "burnup": lambda s: burnup(s["burnup"]["days"], s["burnup"]["done"], s["burnup"]["scope"]) if s.get("burnup") else None,
              "velocity": lambda s: velocity(s["velocity"]["weeks"], s["velocity"]["hours"]) if s.get("velocity") else None,
              "cfd": lambda s: cumulative_flow(s["cfd"]["days"], s["cfd"]["todo"], s["cfd"]["doing"], s["cfd"]["done"]) if s.get("cfd") else None,
              "gantt": lambda s: gantt(s["gantt"]["rows"], _d(s["gantt"]["today"]) if s["gantt"].get("today") else None) if s.get("gantt") else None,
              "donut": lambda s: donut(s["donut"]["labels"], s["donut"]["values"]) if s.get("donut") else None,
              "heatmap": lambda s: heatmap({_d(k): v for k, v in s["heatmap"]["days"].items()}, 12, _d(s["heatmap"]["end"])) if s.get("heatmap") else None,
              "trend": lambda s: trend(s["trend"]["labels"], s["trend"]["billable"], s["trend"].get("non_billable")) if s.get("trend") else None,
              "comparison": lambda s: comparison(s["comparison"]) if s.get("comparison") else None}
    out: Dict[str, Dict[str, Any]] = {}
    for name in wanted:
        try:
            r = makers[name](series)
            if r:
                out[name] = r
        except Exception:  # noqa: BLE001 - a chart problem must never block sending a report
            import logging
            logging.getLogger("worktracker.charts").exception("chart %s failed", name)
    return out
