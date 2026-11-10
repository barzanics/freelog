"""Local HTTP API for IDE extensions. 127.0.0.1 only, bearer-token protected, off by default.

Each request opens its own SQLite connection (the main-thread connection is not shared across threads).
No CORS headers are sent, so browsers cannot call it from web pages.
"""
from __future__ import annotations

import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple, Union
from urllib.parse import parse_qs, urlparse

import datetime as dt

from ..core.database import Database
from ..core.models import ActivityEvent, TimeEntry
from ..core.persian import now_utc
from ..services.tracker import Tracker

MAX_BODY = 64 * 1024


def domain_of(url: str) -> str:
    """Host of an http(s) URL without www., or ''."""
    u = urlparse(url if "://" in url else "//" + url)
    host = (u.hostname or "").lower()
    return host[4:] if host.startswith("www.") else host if u.scheme in ("", "http", "https") else ""


def make_handler(db_path: str, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "WorkTracker"

        def log_message(self, *a) -> None:   # silence default stderr logging
            pass

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _auth(self) -> bool:
            given = self.headers.get("Authorization", "")
            return given.startswith("Bearer ") and hmac.compare_digest(given[7:], token)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("body too large")
            return json.loads(self.rfile.read(n) or b"{}")

        def _route(self, method: str) -> None:
            if not self._auth():
                return self._send(401, {"error": "unauthorized"})
            url = urlparse(self.path)
            db = Database(db_path)
            try:
                tr = Tracker(db)
                if method == "GET" and url.path == "/v1/status":
                    cur = tr.current
                    return self._send(200, {"running": bool(cur), "title": cur.title if cur else None, "elapsed_sec": tr.elapsed()})
                if method == "GET" and url.path == "/v1/entries":
                    limit = min(500, int(parse_qs(url.query).get("limit", ["50"])[0]))
                    rows = db.all(TimeEntry, "start_utc DESC")[:limit]
                    return self._send(200, {"entries": [{"id": e.id, "title": e.title, "start": e.start_utc, "seconds": e.duration_sec} for e in rows]})
                if method == "POST" and url.path == "/v1/timer/start":
                    e = tr.start(str(self._body().get("title", "")), category="development")
                    return self._send(200, {"id": e.id, "title": e.title})
                if method == "POST" and url.path == "/v1/timer/stop":
                    e = tr.stop()
                    return self._send(200, {"stopped": bool(e), "seconds": e.duration_sec if e else 0})
                if method == "POST" and url.path == "/v1/activity":
                    body = self._body()
                    dom = domain_of(str(body.get("url", "")))
                    secs = max(1, min(3600, int(body.get("seconds", 0))))
                    if not dom:
                        raise ValueError("url required")
                    end = now_utc()
                    db.save(ActivityEvent(app="web:" + dom, title=dom, start_utc=end - dt.timedelta(seconds=secs), end_utc=end, category="browsing"))
                    return self._send(200, {"domain": dom})
                self._send(404, {"error": "not found"})
            except (ValueError, KeyError) as exc:
                self._send(400, {"error": str(exc)})
            finally:
                db.close()

        def do_GET(self) -> None:  # noqa: N802
            self._route("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._route("POST")

    return Handler


def start_server(db_path: Union[str, Path], token: str, port: int = 9876) -> Tuple[ThreadingHTTPServer, threading.Thread]:
    """Start in a daemon thread. Pass port=0 for an ephemeral port (``server.server_address[1]``)."""
    if len(token) < 16:
        raise ValueError("token must be at least 16 characters")
    if str(db_path) == ":memory:":
        raise ValueError("API needs a file database")
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(str(db_path), token))
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv, th
