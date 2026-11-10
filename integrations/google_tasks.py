"""Two-way sync between the local task lists and Google Tasks.

* ``build_tasks_service`` returns an authenticated Google Tasks service, or None when the libraries / ``credentials.json`` are missing (the rest of the app is unaffected).
* ``GoogleTasksSync`` talks to any object with the same shape as the Google client (so it is fully unit-tested with a fake service).

Rules: a remote list is matched to a local list by remote id, else by name (created locally if new); a task is linked by ``extra["gid"]``. If only one side changed since the last
sync, that side wins; if both changed, the newer ``updated`` time wins. A task deleted remotely is hidden locally (cancelled); a task deleted locally is deleted remotely (tombstone).
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.database import Database
from ..core.models import Status, TimeEntry
from ..core.persian import TEHRAN, UTC, now_utc
from ..services import lists as L

log = logging.getLogger("worktracker.gtasks")
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def build_tasks_service(data_dir: Union[str, Path]) -> Optional[Any]:
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
        token = data_dir / "token_tasks.json"
        creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES).run_local_server(port=0)
            token.write_text(creds.to_json(), encoding="utf-8")
        return build("tasks", "v1", credentials=creds, cache_discovery=False)
    except Exception:  # noqa: BLE001 - optional integration must never break the app
        log.exception("google tasks auth failed")
        return None


@dataclass
class SyncReport:
    lists_created_local: int = 0
    lists_created_remote: int = 0
    pulled_new: int = 0
    pulled_updated: int = 0
    pushed_new: int = 0
    pushed_updated: int = 0
    deleted_remote: int = 0
    hidden_local: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def changes(self) -> int:
        return (self.lists_created_local + self.lists_created_remote + self.pulled_new + self.pulled_updated + self.pushed_new + self.pushed_updated + self.deleted_remote + self.hidden_local)


def _due_to_remote(e: TimeEntry) -> Optional[str]:
    return e.due_utc.astimezone(TEHRAN).date().isoformat() + "T00:00:00.000Z" if e.due_utc else None


def _due_from_remote(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    d = dt.date.fromisoformat(s[:10])
    return dt.datetime.combine(d, dt.time(), tzinfo=TEHRAN).astimezone(UTC)


def _body(e: TimeEntry) -> Dict[str, Any]:
    b: Dict[str, Any] = {"title": e.title, "notes": e.description or "", "status": "completed" if L.is_done(e) else "needsAction"}
    due = _due_to_remote(e)
    if due:
        b["due"] = due
    return b


def _is_404(exc: Exception) -> bool:
    status = getattr(getattr(exc, "resp", None), "status", None)
    return status in (404, 410) or "404" in str(exc)


class GoogleTasksSync:
    def __init__(self, db: Database, service: Optional[Any], clock=now_utc) -> None:
        self.db, self.svc, self.clock = db, service, clock

    @property
    def available(self) -> bool:
        return self.svc is not None

    # ---- remote helpers ----------------------------------------------------------------
    def _remote_lists(self) -> List[Dict[str, Any]]:
        out, token = [], None
        while True:
            r = self.svc.tasklists().list(maxResults=100, pageToken=token).execute()
            out += r.get("items", [])
            token = r.get("nextPageToken")
            if not token:
                return out

    def _remote_tasks(self, gid: str) -> List[Dict[str, Any]]:
        out, token = [], None
        while True:
            r = self.svc.tasks().list(tasklist=gid, showCompleted=True, showHidden=True, maxResults=100, pageToken=token).execute()
            out += r.get("items", [])
            token = r.get("nextPageToken")
            if not token:
                return out

    @staticmethod
    def _mark(e: TimeEntry, remote_updated: str) -> None:
        e.extra = {**e.extra, "gupdated": remote_updated, "glocal": e.updated_at.isoformat()}

    def _flush_tombstones(self, rep: SyncReport) -> None:
        """Delete on Google what was deleted here. Runs BEFORE the pull so a just-deleted task cannot come back from the remote copy."""
        for tomb in list(self.db.get_setting("gtasks_deleted", [])):
            try:
                if tomb.get("list_gid"):
                    self.svc.tasks().delete(tasklist=tomb["list_gid"], task=tomb["gid"]).execute(); rep.deleted_remote += 1
            except Exception as exc:  # noqa: BLE001
                if not _is_404(exc):
                    rep.errors.append(f"delete {tomb['gid']}: {exc}"); continue
            tombs = self.db.get_setting("gtasks_deleted", [])
            if tomb in tombs:
                tombs.remove(tomb); self.db.set_setting("gtasks_deleted", tombs)

    # ---- pull -----------------------------------------------------------------------------
    def pull(self, rep: Optional[SyncReport] = None) -> SyncReport:
        rep = rep or SyncReport()
        db = self.db
        L.ensure_default(db)
        for rl in self._remote_lists():
            local = next((l for l in L.lists(db) if l.get("gid") == rl["id"]), None) or next((l for l in L.lists(db) if l["name"].lower() == rl["title"].lower() and not l.get("gid")), None)
            if local is None:
                try:
                    local = L.add_list(db, rl["title"])
                except L.ListError:
                    local = L.add_list(db, f"{rl['title']} (Google)")
                rep.lists_created_local += 1
            L.set_remote_id(db, local["id"], rl["id"])
            skip = {t["gid"] for t in db.get_setting("gtasks_deleted", [])}            # deletions that could not be sent yet must not be re-imported
            remote = [t for t in self._remote_tasks(rl["id"]) if t["id"] not in skip]
            seen_gids = set()
            id_by_gid: Dict[str, str] = {}
            for rt in sorted(remote, key=lambda t: (t.get("parent") is not None, t.get("position", ""))):
                seen_gids.add(rt["id"])
                e = next((x for x in L._all_in(db, local["id"], with_children=True) if x.extra.get("gid") == rt["id"]), None)
                done = rt.get("status") == "completed"
                if e is None:
                    e = L.add_task(db, local["id"], rt.get("title") or "(untitled)", due=None, notes=rt.get("notes", ""), now=self.clock())
                    e.updated_at = self.clock()
                    e.due_utc = _due_from_remote(rt.get("due"))
                    if rt.get("parent") and rt["parent"] in id_by_gid:
                        e.parent_id = id_by_gid[rt["parent"]]
                    if done:
                        e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, self.clock(), 100
                    e.extra = {**e.extra, "gid": rt["id"]}
                    self._mark(e, rt.get("updated", ""))
                    db.save(e, touch=False); rep.pulled_new += 1
                else:
                    local_changed = e.updated_at.isoformat() != e.extra.get("glocal")
                    remote_changed = rt.get("updated", "") != e.extra.get("gupdated")
                    if remote_changed and (not local_changed or rt.get("updated", "") >= e.updated_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")):
                        e.title, e.description, e.due_utc = rt.get("title") or e.title, rt.get("notes", ""), _due_from_remote(rt.get("due"))
                        if done != L.is_done(e):
                            e.column, e.status, e.completed_at, e.progress = ("done", Status.DONE, self.clock(), 100) if done else ("backlog", Status.PLANNED, None, 0)
                        e.updated_at = self.clock()
                        self._mark(e, rt.get("updated", ""))
                        db.save(e, touch=False); rep.pulled_updated += 1
                id_by_gid[rt["id"]] = e.id
            for e in L._all_in(db, local["id"], with_children=True):            # removed remotely -> hide locally
                g = e.extra.get("gid")
                if g and g not in seen_gids and e.column != "cancelled":
                    e.column = "cancelled"; e.updated_at = self.clock(); e.extra = {**e.extra, "glocal": e.updated_at.isoformat()}
                    db.save(e, touch=False); rep.hidden_local += 1
        return rep

    # ---- push -----------------------------------------------------------------------------
    def push(self, rep: Optional[SyncReport] = None) -> SyncReport:
        rep = rep or SyncReport()
        db = self.db
        L.ensure_default(db)
        self._flush_tombstones(rep)
        for lst in L.lists(db):
            if not lst.get("gid"):
                made = self.svc.tasklists().insert(body={"title": lst["name"]}).execute()
                L.set_remote_id(db, lst["id"], made["id"]); lst["gid"] = made["id"]; rep.lists_created_remote += 1
            members = L._all_in(db, lst["id"], with_children=True)
            for e in sorted(members, key=lambda x: (x.parent_id is not None, x.rank)):
                if e.column == "cancelled" and e.extra.get("gid"):
                    continue
                try:
                    gid = e.extra.get("gid")
                    if not gid:
                        kw: Dict[str, Any] = {}
                        parent = db.get(TimeEntry, e.parent_id) if e.parent_id else None
                        if parent is not None and parent.extra.get("gid"):
                            kw["parent"] = parent.extra["gid"]
                        made = self.svc.tasks().insert(tasklist=lst["gid"], body=_body(e), **kw).execute()
                        e.extra = {**e.extra, "gid": made["id"]}; self._mark(e, made.get("updated", ""))
                        db.save(e, touch=False); rep.pushed_new += 1
                    elif e.updated_at.isoformat() != e.extra.get("glocal"):
                        body = _body(e)
                        if not L.is_done(e):
                            body["completed"] = None                              # un-complete on the remote side as well
                        made = self.svc.tasks().patch(tasklist=lst["gid"], task=gid, body=body).execute()
                        self._mark(e, made.get("updated", "")); db.save(e, touch=False); rep.pushed_updated += 1
                except Exception as exc:  # noqa: BLE001 - one bad task must not stop the rest
                    log.exception("push failed")
                    rep.errors.append(f"{e.title}: {exc}")
        return rep

    def sync(self) -> SyncReport:
        """Pull then push; records the time of the last successful run."""
        if not self.available:
            raise RuntimeError("Google Tasks is not connected")
        rep = SyncReport()
        self._flush_tombstones(rep)
        self.pull(rep)
        self.push(rep)
        if not rep.errors:
            self.db.set_setting("gtasks_last_sync", self.clock().isoformat())
        return rep
