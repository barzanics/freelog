# Local HTTP API (off by default)
Start from code: `from worktracker.integrations.http_api import start_server; start_server(db_path, token, port=9876)`.
Binds **127.0.0.1 only**; every request needs `Authorization: Bearer <token>` (≥16 chars); no CORS headers; bodies ≤ 64 KB.

| Method | Path | Body | Result |
|---|---|---|---|
| GET | /v1/status | – | `{running, title, elapsed_sec}` |
| GET | /v1/entries?limit=50 | – | latest entries |
| POST | /v1/timer/start | `{"title": "..."}` | starts a timer (stops others) |
| POST | /v1/timer/stop | – | `{stopped, seconds}` |
| POST | /v1/activity | `{"url": "...", "seconds": 60}` | records browser activity by domain (for a browser extension) |
