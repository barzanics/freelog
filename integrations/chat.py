"""Telegram bot + Slack webhook (both opt-in). Commands from Telegram only work for whitelisted chat ids."""
from __future__ import annotations

import datetime as dt
import re
from typing import Callable, Iterable, Optional

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import format_duration, now_utc
from ..services import quick
from ..services.tracker import Tracker
from .webhook import post_json


def slack_send(webhook_url: str, text: str, opener: Optional[Callable] = None) -> bool:
    return post_json(webhook_url, {"text": text}, opener=opener)


def telegram_send(token: str, chat_id: int, text: str, opener: Optional[Callable] = None) -> bool:
    if not re.fullmatch(r"\d+:[\w-]{20,}", token):
        return False
    return post_json(f"https://api.telegram.org/bot{token}/sendMessage", {"chat_id": chat_id, "text": text}, opener=opener)


def daily_digest(db: Database, day_entries: Iterable[TimeEntry]) -> str:
    es = list(day_entries)
    total = sum(e.duration_sec for e in es)
    return f"Today: {format_duration(total)} h in {len(es)} entries"


def handle_update(db: Database, update: dict, allowed_chats: Iterable[int], clock: Callable[[], dt.datetime] = now_utc) -> str:
    """Process one Telegram update dict and return the reply text.

    /start <title ...>   start a timer       /stop            stop it
    /log 1h30 <title>    add a finished entry ending now       /status
    """
    msg = update.get("message") or {}
    chat = (msg.get("chat") or {}).get("id")
    if chat not in set(allowed_chats):
        return ""                                     # silently ignore strangers
    text = (msg.get("text") or "").strip()
    cmd, _, rest = text.partition(" ")
    tr = Tracker(db, clock=clock)
    try:
        if cmd == "/start" and rest:
            c = quick.parse(rest)
            tr.start(c.title, tags=c.tags)
            return f"▶ {c.title}"
        if cmd == "/stop":
            e = tr.stop()
            return f"■ {e.title} {format_duration(e.duration_sec)}" if e else "nothing running (or shorter than the minimum)"
        if cmd == "/log" and rest:
            c = quick.parse(rest)
            if c.minutes <= 0:
                return "usage: /log 1h30 title"
            end = clock()
            tr.add_manual(c.title, end - dt.timedelta(minutes=c.minutes), end, tags=c.tags)
            return f"✓ {c.title} {c.minutes} min"
        if cmd == "/status":
            cur = tr.current
            return f"running: {cur.title} ({format_duration(tr.elapsed())})" if cur else "idle"
    except ValueError as exc:
        return f"error: {exc}"
    return "commands: /start title, /stop, /log 1h30 title, /status"


def poll_once(db: Database, token: str, allowed_chats: Iterable[int], offset: int = 0, opener: Optional[Callable] = None,
              clock: Callable[[], dt.datetime] = now_utc) -> int:
    """One long-poll-free ``getUpdates`` round: handles every update and replies. Returns the next offset.

    Call it from a QTimer (e.g. every 10 s) *only if the user configured a bot token*; failures are silent.
    """
    import json
    import urllib.request
    if not re.fullmatch(r"\d+:[\w-]{20,}", token):
        return offset
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=0&offset={offset}"
    try:
        with (opener or urllib.request.urlopen)(urllib.request.Request(url), timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - offline is normal
        return offset
    for up in data.get("result", []):
        offset = max(offset, int(up["update_id"]) + 1)
        reply = handle_update(db, up, allowed_chats, clock)
        chat_id = (up.get("message") or {}).get("chat", {}).get("id")
        if reply and chat_id is not None:
            telegram_send(token, chat_id, reply, opener)
    return offset
