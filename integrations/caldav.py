"""Minimal CalDAV client (Nextcloud/Fastmail): PUT/DELETE one .ics resource per entry. Opt-in, injectable transport."""
from __future__ import annotations

import base64
import logging
import urllib.request
from typing import Callable, Optional

from ..core.models import TimeEntry
from .ical import build_ics
from .webhook import valid_url

log = logging.getLogger("worktracker.caldav")


def _request(method: str, url: str, user: str, password: str, body: Optional[bytes], opener: Optional[Callable]) -> bool:
    if not valid_url(url):
        return False
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode())
    if body:
        req.add_header("Content-Type", "text/calendar; charset=utf-8")
    try:
        with (opener or urllib.request.urlopen)(req, timeout=10) as r:
            return 200 <= getattr(r, "status", 200) < 300
    except Exception:  # noqa: BLE001
        log.info("caldav %s failed", method, exc_info=True)
        return False


def resource_url(calendar_url: str, entry: TimeEntry) -> str:
    return calendar_url.rstrip("/") + f"/{entry.id}.ics"


def put_event(calendar_url: str, user: str, password: str, entry: TimeEntry, opener: Optional[Callable] = None) -> bool:
    if entry.end_utc is None:
        return False
    return _request("PUT", resource_url(calendar_url, entry), user, password, build_ics([entry]).encode("utf-8"), opener)


def delete_event(calendar_url: str, user: str, password: str, entry: TimeEntry, opener: Optional[Callable] = None) -> bool:
    return _request("DELETE", resource_url(calendar_url, entry), user, password, None, opener)
