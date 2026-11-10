"""Task taxonomy ported from the v5 app: 22 categories / 384 subcategories (data/categories.json), priorities, statuses.

User-defined categories are stored in the settings table (key ``custom_categories``) and merged on top.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA = Path(__file__).resolve().parent.parent / "data" / "categories.json"

PRIORITIES: Dict[int, Dict[str, str]] = {
    1: {"name": "فوری", "color": "#F44336"}, 2: {"name": "بالا", "color": "#FF9800"}, 3: {"name": "متوسط", "color": "#FFC107"},
    4: {"name": "پایین", "color": "#4CAF50"}, 5: {"name": "خیلی پایین", "color": "#9E9E9E"},
}
STATUSES: Dict[str, Dict[str, str]] = {
    "planned": {"name": "برنامه‌ریزی‌شده", "color": "#8A8AFF"}, "running": {"name": "در حال انجام", "color": "#00E5FF"},
    "done": {"name": "انجام‌شده", "color": "#2ED573"},
}
COLUMNS: Dict[str, str] = {"backlog": "بک‌لاگ", "in_progress": "در حال انجام", "review": "بازبینی", "done": "انجام‌شده"}
PROJECT_STATUSES: Dict[str, str] = {"planning": "برنامه‌ریزی", "active": "فعال", "on_hold": "متوقف", "completed": "تکمیل‌شده", "cancelled": "لغوشده"}
RECURRENCE: Dict[str, str] = {"none": "بدون تکرار", "daily": "روزانه", "weekly": "هفتگی", "monthly": "ماهانه", "yearly": "سالانه"}
SWATCHES: List[str] = ["#6D5DFC", "#00E5FF", "#FF3D71", "#2ED573", "#FFB020", "#C56CF0", "#FF7A45", "#1E88E5", "#00BFA5", "#E91E63", "#8BC34A", "#9E9E9E"]


@lru_cache(maxsize=1)
def _base() -> Dict[str, Dict[str, Any]]:
    return json.loads(_DATA.read_text(encoding="utf-8"))


def categories(custom: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Built-in categories merged with user ones (user ids win)."""
    out = {k: dict(v) for k, v in _base().items()}
    for k, v in (custom or {}).items():
        out[k] = {"icon": v.get("icon", "🏷"), "name": v.get("name", k), "subcategories": list(v.get("subcategories", []))}
    return out


def category_name(cat_id: str, custom: Optional[dict] = None) -> str:
    c = categories(custom).get(cat_id)
    return c["name"] if c else cat_id


def subcategories(cat_id: str, custom: Optional[dict] = None) -> List[str]:
    return list(categories(custom).get(cat_id, {}).get("subcategories", []))


def add_custom_category(existing: Dict[str, Dict[str, Any]], cat_id: str, name: str, icon: str = "🏷", subs: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """Return a new custom-categories dict with one more entry (validated)."""
    cat_id = cat_id.strip().lower().replace(" ", "_")
    if not cat_id or not name.strip():
        raise ValueError("id and name required")
    if cat_id in _base() or cat_id in existing:
        raise ValueError("category exists")
    return {**existing, cat_id: {"icon": icon, "name": name.strip(), "subcategories": list(subs or [])}}


def search_subcategory(query: str, custom: Optional[dict] = None, limit: int = 12) -> List[Dict[str, str]]:
    """Substring search across all subcategories (case-insensitive) -> [{category, sub}]."""
    q = query.strip().lower()
    out: List[Dict[str, str]] = []
    if not q:
        return out
    for cid, c in categories(custom).items():
        for s in c.get("subcategories", []):
            if q in s.lower():
                out.append({"category": cid, "sub": s})
                if len(out) >= limit:
                    return out
    return out


_PRIORITY_ICONS = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "⚪"}
for _k, _v in PRIORITIES.items():          # the UI shows an emoji next to every priority name
    _v.setdefault("icon", _PRIORITY_ICONS.get(_k, "⚪"))
