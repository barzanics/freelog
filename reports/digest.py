"""Smart Digest: a short, natural executive summary written from the numbers (deterministic template; an optional local LLM via Ollama can polish it).

The template always works offline. If ``ollama_model`` is configured and the local Ollama server answers, its text replaces the template - you still read and edit it before it is sent.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from . import locale_us as us

log = logging.getLogger("worktracker.digest")


def _list(items: List[str], limit: int = 3) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    shown = items[:limit]
    more = len(items) - len(shown)
    s = ", ".join(shown[:-1]) + (" and " if len(shown) > 1 else "") + shown[-1] if len(shown) > 1 else shown[0]
    return s + (f" and {more} more" if more > 0 else "")


def template_digest(d: Dict[str, Any], tone: str = "we") -> str:
    """Two to four plain sentences. ``tone``: 'we' (agency voice, default) or 'i'."""
    we = tone != "i"
    subj, verb_have = ("we", "have") if we else ("I", "have")
    t = d["time"]
    prog, health = d["progress"], d["health"]
    parts: List[str] = []
    hrs = t["total_sec"] / 3600
    kind = d["header"]["type"]
    span = {"daily": "today", "weekly": "this week", "snapshot": "to date"}.get(kind, "in this period")
    if hrs > 0:
        done = [x["title"] for x in d["done"]]
        s = f"{subj.capitalize()} logged {hrs:.1f} hours {span}"
        s += f" and completed {len(done)} task{'s' if len(done) != 1 else ''} ({_list(done)})." if done else "."
        parts.append(s)
    else:
        parts.append(f"No billable work was logged {span}.")
    status = {"on_track": "on track", "at_risk": "at risk", "off_track": "behind schedule"}[health["status"]]
    parts.append(f"The project is {prog['pct']:.0f}% complete and {status}" + (f" — {health['reasons'][0]['text'][0].lower() + health['reasons'][0]['text'][1:]}" if health["status"] != "on_track" else "."))
    if d["waiting_on_client"]:
        parts.append(f"{subj.capitalize()} {verb_have} {len(d['waiting_on_client'])} item{'s' if len(d['waiting_on_client']) != 1 else ''} waiting on you: {_list([w['title'] for w in d['waiting_on_client']])}.")
    elif d["next_plan"]:
        parts.append(f"Next up: {_list([x['title'] for x in d['next_plan']])}.")
    return " ".join(p if p.endswith((".", "!", "?")) else p + "." for p in parts).replace("..", ".")


def llm_digest(d: Dict[str, Any], model: str, tone: str = "we", opener: Optional[Callable[..., Any]] = None, url: str = "http://127.0.0.1:11434/api/generate", timeout: int = 20) -> Optional[str]:
    """Ask a local Ollama model to rewrite the template summary more naturally. Returns None on any failure (caller keeps the template)."""
    base = template_digest(d, tone)
    prompt = ("Rewrite this project status update for a client: concise, confident, friendly, no hype, no apologies, keep every number and name exactly. "
              f"Voice: {'we' if tone != 'i' else 'I'}. At most 4 sentences.\n\n{base}")
    try:
        req = urllib.request.Request(url, data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(), headers={"Content-Type": "application/json"})
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            text = json.loads(r.read().decode("utf-8")).get("response", "").strip()
        return text if 20 <= len(text) <= 1200 else None
    except Exception:  # noqa: BLE001 - optional enhancement
        log.info("local LLM digest unavailable", exc_info=True)
        return None
