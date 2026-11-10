"""Automation rules: "if duration > 4h then add tag long-task". Webhooks are injected, never implicit."""
from __future__ import annotations

import logging
import operator
from typing import Callable, List, Optional, Tuple

from ..core.database import Database
from ..core.models import Rule, TimeEntry

log = logging.getLogger("worktracker.rules")
_OPS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le, "==": operator.eq, "!=": operator.ne}
ATTRS = {"duration_sec", "title", "category", "tags", "billable", "project_id", "priority", "notes"}
ACTIONS = {"add_tag", "set_category", "set_billable", "webhook"}


def matches(rule: Rule, e: TimeEntry) -> bool:
    if rule.attr not in ATTRS:
        return False
    actual = getattr(e, rule.attr)
    try:
        if rule.op == "contains":
            return str(rule.value).lower() in (str(x).lower() for x in actual) if isinstance(actual, list) \
                else str(rule.value).lower() in str(actual).lower()
        return bool(_OPS[rule.op](actual, rule.value))
    except (KeyError, TypeError):
        return False


class Automation:
    def __init__(self, db: Database, webhook: Optional[Callable[[str, dict], object]] = None) -> None:
        self.db, self.webhook = db, webhook

    def add(self, rule: Rule) -> Rule:
        if rule.attr not in ATTRS or rule.action not in ACTIONS or rule.op not in {*_OPS, "contains"}:
            raise ValueError("invalid rule")
        self.db.save(rule)
        return rule

    def apply(self, e: TimeEntry, save: bool = True) -> List[str]:
        """Run all enabled rules; returns names of fired rules. Rules never re-trigger within one pass."""
        fired: List[str] = []
        for r in self.db.all(Rule):
            if not r.enabled or not matches(r, e):
                continue
            if r.action == "add_tag" and r.arg and r.arg not in e.tags:
                e.tags.append(r.arg)
            elif r.action == "set_category" and r.arg:
                e.category = r.arg
            elif r.action == "set_billable":
                e.billable = r.arg.lower() in ("1", "true", "yes", "")
            elif r.action == "webhook" and self.webhook and r.arg:
                try:
                    self.webhook(r.arg, {"rule": r.name, "entry": e.to_row()})
                except Exception:  # noqa: BLE001 - a broken webhook must never block saving
                    log.exception("webhook failed")
            fired.append(r.name)
        if fired and save:
            self.db.save(e)
        return fired
