"""Turn git commits into work entries (read-only, local, injectable runner)."""
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Union

from ..core.models import Status, TimeEntry
from ..core.persian import UTC

SEP = "\x1f"


def _run(repo: Path, since: Optional[str]) -> str:
    cmd = ["git", "-C", str(repo), "log", f"--pretty=format:%H{SEP}%at{SEP}%s", "--no-merges"]
    if since:
        cmd.append(f"--since={since}")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True).stdout


def commits_to_entries(repo: Union[str, Path], since: Optional[str] = None, gap_min: int = 120, lead_min: int = 15,
                       project_id: Optional[str] = None, runner: Callable[[Path, Optional[str]], str] = _run) -> List[TimeEntry]:
    """Group commits into sessions (gap <= ``gap_min``); each session starts ``lead_min`` before its first commit."""
    out = runner(Path(repo), since)
    commits = sorted((dt.datetime.fromtimestamp(int(p[1]), UTC), p[2], p[0]) for p in
                     (l.split(SEP, 2) for l in out.splitlines() if l.count(SEP) == 2))
    sessions: List[list] = []
    for when, msg, sha in commits:
        if sessions and when - sessions[-1][-1][0] <= dt.timedelta(minutes=gap_min):
            sessions[-1].append((when, msg, sha))
        else:
            sessions.append([(when, msg, sha)])
    entries = []
    for s in sessions:
        start = s[0][0] - dt.timedelta(minutes=lead_min)
        end = s[-1][0]
        title = s[0][1] if len(s) == 1 else f"{s[0][1]} (+{len(s) - 1} commits)"
        entries.append(TimeEntry(id=f"git{s[0][2][:12]}", title=title[:200], start_utc=start, end_utc=end, project_id=project_id,
                                 category="development", tags=["git"], status=Status.DONE, extra={"commits": [c[2] for c in s]}))
    return entries
