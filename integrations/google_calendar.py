"""Optional two-way Google Calendar sync. Never required, never raises into the app.

The plugin talks to anything shaped like the Google API ``service`` object, so it is fully testable offline.
``build_service`` lazily imports the Google libraries and returns None when libraries/credentials are missing.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Union

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import UTC

log = logging.getLogger("worktracker.gcal")
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def build_service(data_dir: Union[str, Path]) -> Optional[Any]:
    """Return an authenticated Calendar service or None (missing libs / no credentials.json / auth failure)."""
    data_dir = Path(data_dir)
    creds_file = data_dir / "credentials.json"
    if not creds_file.exists():
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        log.info("google libraries not installed")
        return None
    try:
        token = data_dir / "token.json"
        creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES).run_local_server(port=0)
            token.write_text(creds.to_json(), encoding="utf-8")
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception:  # noqa: BLE001 - optional integration must not break the app
        log.exception("google auth failed")
        return None


@dataclass
class SyncResult:
    pushed: int = 0
    pulled: int = 0
    errors: List[str] = field(default_factory=list)


def _event_body(e: TimeEntry) -> dict:
    end = e.end_utc or e.start_utc + dt.timedelta(minutes=e.estimated_min or 30)
    return {"summary": e.title, "description": e.notes, "start": {"dateTime": e.start_utc.astimezone(UTC).isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.astimezone(UTC).isoformat(), "timeZone": "UTC"}, "extendedProperties": {"private": {"wt_id": e.id}}}


class GoogleCalendarPlugin:
    def __init__(self, db: Database, service: Optional[Any], calendar_id: str = "primary") -> None:
        self.db, self.service, self.calendar_id = db, service, calendar_id

    @property
    def available(self) -> bool:
        return self.service is not None

    def push(self, entry_ids: Optional[List[str]] = None) -> SyncResult:
        """Create/update events for finished or planned entries (skips entries that came *from* Google)."""
        res = SyncResult()
        if not self.available:
            return res
        ents = [self.db.get(TimeEntry, i) for i in entry_ids] if entry_ids else self.db.all(TimeEntry, "start_utc")
        for e in filter(None, ents):
            if e.status == Status.RUNNING or e.extra.get("source") == "google":
                continue
            try:
                ev = e.extra.get("calendar_event_id")
                if ev:
                    self.service.events().update(calendarId=self.calendar_id, eventId=ev, body=_event_body(e)).execute()
                else:
                    made = self.service.events().insert(calendarId=self.calendar_id, body=_event_body(e)).execute()
                    e.extra["calendar_event_id"] = made["id"]
                    self.db.save(e)
                res.pushed += 1
            except Exception as exc:  # noqa: BLE001
                res.errors.append(f"{e.id}: {exc}")
        return res

    def pull(self, since: dt.datetime, until: dt.datetime) -> SyncResult:
        """Import events not yet known locally as planned entries."""
        res = SyncResult()
        if not self.available:
            return res
        try:
            items = self.service.events().list(calendarId=self.calendar_id, timeMin=since.astimezone(UTC).isoformat(),
                                               timeMax=until.astimezone(UTC).isoformat(), singleEvents=True).execute().get("items", [])
        except Exception as exc:  # noqa: BLE001
            res.errors.append(str(exc))
            return res
        known = {e.extra.get("calendar_event_id") for e in self.db.all(TimeEntry)}
        for it in items:
            if it["id"] in known or "dateTime" not in it.get("start", {}):
                continue
            if it.get("extendedProperties", {}).get("private", {}).get("wt_id"):
                continue                     # one of our own events
            s = dt.datetime.fromisoformat(it["start"]["dateTime"].replace("Z", "+00:00")).astimezone(UTC)
            en = dt.datetime.fromisoformat(it["end"]["dateTime"].replace("Z", "+00:00")).astimezone(UTC)
            if en <= s:
                continue
            self.db.save(TimeEntry(title=it.get("summary", "(no title)"), start_utc=s, end_utc=en, status=Status.PLANNED,
                                   category="meeting", extra={"calendar_event_id": it["id"], "source": "google"}))
            res.pulled += 1
        return res

    def delete_remote(self, entry_id: str) -> bool:
        e = self.db.get(TimeEntry, entry_id)
        if not self.available or e is None or not e.extra.get("calendar_event_id"):
            return False
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=e.extra["calendar_event_id"]).execute()
            return True
        except Exception:  # noqa: BLE001
            log.exception("delete failed")
            return False
