"""Tip/fact of the hour: bundled offline collection (original Persian text) + your own tips + an *opt-in* online feed.

Nothing is fetched unless you configure a feed URL and press refresh; the app stays 100% offline by default.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..core.database import Database

_DATA = Path(__file__).resolve().parent.parent / "data" / "tips.json"
CATEGORIES = {"focus": "تمرکز", "productivity": "بهره‌وری", "health": "سلامتی", "learning": "یادگیری", "science": "علم", "history": "تاریخ",
              "tech": "دنیای فناوری", "wisdom": "حکمت", "fun": "سرگرمی", "own": "نکته‌ی من"}
MAX_ONLINE_BYTES = 256 * 1024


def bundled() -> List[Dict[str, str]]:
    return json.loads(_DATA.read_text(encoding="utf-8"))


class Tips:
    def __init__(self, db: Database) -> None:
        self.db = db

    def all(self, categories: Optional[List[str]] = None) -> List[Dict[str, str]]:
        items = bundled() + [{"cat": "own", "text": t} for t in self.db.get_setting("tips_own", [])] + self.db.get_setting("tips_online", [])
        disabled = set(self.db.get_setting("tips_disabled_cats", []))
        want = set(categories) if categories else None
        return [i for i in items if i.get("cat") not in disabled and (want is None or i.get("cat") in want)]

    def for_time(self, now: dt.datetime, offset: int = 0) -> Dict[str, str]:
        """Deterministic tip for the current hour (changes every hour; ``offset`` = user pressed 'next')."""
        items = self.all()
        if not items:
            return {"cat": "own", "text": "برای دیدن نکته‌ها، یک دسته را در تنظیمات فعال کنید."}
        idx = (now.date().toordinal() * 24 + now.hour + offset * 7) % len(items)
        return items[idx]

    def add_own(self, text: str) -> None:
        text = text.strip()
        if len(text) < 5:
            raise ValueError("tip too short")
        own = self.db.get_setting("tips_own", [])
        if text not in own:
            self.db.set_setting("tips_own", own + [text[:400]])

    def favorite(self, text: str, on: bool = True) -> None:
        fav = [f for f in self.db.get_setting("tips_fav", []) if f != text]
        self.db.set_setting("tips_fav", fav + [text] if on else fav)

    def favorites(self) -> List[str]:
        return self.db.get_setting("tips_fav", [])

    def refresh_online(self, url: str, opener: Optional[Callable] = None) -> int:
        """Opt-in: download a JSON list ``[{"cat": "...", "text": "..."}]`` from a URL *you* provide. Returns items stored."""
        from urllib.parse import urlparse
        import urllib.request
        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError("http(s) URL required")
        with (opener or urllib.request.urlopen)(urllib.request.Request(url, headers={"User-Agent": "WorkTracker"}), timeout=10) as r:
            raw = r.read(MAX_ONLINE_BYTES + 1)
        if len(raw) > MAX_ONLINE_BYTES:
            raise ValueError("feed too large")
        data = json.loads(raw.decode("utf-8"))
        clean = []
        for it in data if isinstance(data, list) else []:
            text = str(it.get("text", "")).strip()
            if 5 <= len(text) <= 400:
                clean.append({"cat": it.get("cat") if it.get("cat") in CATEGORIES else "fun", "text": text})
        self.db.set_setting("tips_online", clean[:300])
        return len(clean[:300])
