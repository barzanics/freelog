"""Opt-in webhook. Nothing is sent unless the user configured a URL; failures never raise."""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Callable, Optional
from urllib.parse import urlparse

log = logging.getLogger("worktracker.webhook")


def valid_url(url: str) -> bool:
    u = urlparse(url)
    return u.scheme in ("http", "https") and bool(u.netloc)


def post_json(url: str, payload: dict, timeout: float = 5.0, opener: Optional[Callable] = None) -> bool:
    """POST JSON; returns True on 2xx. ``opener`` is injectable for tests/offline."""
    if not valid_url(url):
        log.warning("rejected webhook url")
        return False
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:  # noqa: BLE001 - network is optional by design
        log.info("webhook failed", exc_info=True)
        return False
