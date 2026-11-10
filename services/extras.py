"""Templates, batch operations, saved filters, custom fields and safe formulas."""
from __future__ import annotations

import ast
import operator
from typing import Any, Dict, Iterable, List, Optional

from ..core.database import Database
from ..core.models import SavedFilter, Status, Template, TimeEntry
from ..core.persian import now_utc
from . import search


# ---- templates ---------------------------------------------------------
def from_template(db: Database, template_id: str, project_id: Optional[str] = None) -> TimeEntry:
    """Create a planned entry from a template."""
    t = db.get(Template, template_id)
    if t is None:
        raise KeyError(template_id)
    e = TimeEntry(title=t.title or t.name, start_utc=now_utc(), status=Status.PLANNED, category=t.category,
                  tags=list(t.tags), estimated_min=t.estimated_min, billable=t.billable, project_id=project_id)
    db.save(e)
    return e


# ---- batch operations ----------------------------------------------------
def batch_update(db: Database, ids: Iterable[str], add_tags: Iterable[str] = (), category: Optional[str] = None,
                 project_id: Optional[str] = None, billable: Optional[bool] = None) -> int:
    """Apply changes to many entries atomically; returns number changed."""
    n = 0
    with db.transaction():
        for i in ids:
            e = db.get(TimeEntry, i)
            if e is None:
                continue
            for t in add_tags:
                if t not in e.tags:
                    e.tags.append(t)
            if category is not None: e.category = category
            if project_id is not None: e.project_id = project_id
            if billable is not None: e.billable = billable
            db.save(e)
            n += 1
    return n


def batch_delete(db: Database, ids: Iterable[str]) -> int:
    with db.transaction():
        return sum(db.delete(TimeEntry, i) for i in ids)


# ---- saved filters ---------------------------------------------------------
def save_filter(db: Database, name: str, query: str) -> SavedFilter:
    search.parse(query)   # validate
    f = SavedFilter(name=name.strip(), query=query)
    if not f.name:
        raise ValueError("name required")
    db.save(f)
    return f


def run_filter(db: Database, filter_id: str) -> List[TimeEntry]:
    f = db.get(SavedFilter, filter_id)
    if f is None:
        raise KeyError(filter_id)
    return search.run(db, f.query)


# ---- custom fields + formulas ---------------------------------------------------
FIELD_TYPES = ("text", "number", "date", "select")
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Mod: operator.mod, ast.Pow: operator.pow}
_FUNCS = {"min": min, "max": max, "round": round, "abs": abs}


def define_field(db: Database, name: str, ftype: str, options: Optional[List[str]] = None) -> Dict[str, Any]:
    if ftype not in FIELD_TYPES:
        raise ValueError("bad field type")
    fields = db.get_setting("custom_fields", {})
    if name in fields:
        raise ValueError("field exists")
    fields[name] = {"type": ftype, "options": options or []}
    db.set_setting("custom_fields", fields)
    return fields[name]


def set_field(db: Database, entry_id: str, name: str, value: Any) -> TimeEntry:
    """Validate against the field definition and store in ``entry.extra['fields']``."""
    spec = db.get_setting("custom_fields", {}).get(name)
    if spec is None:
        raise KeyError(name)
    t = spec["type"]
    if t == "number":
        value = float(value)
    elif t == "select" and value not in spec["options"]:
        raise ValueError("not an allowed option")
    elif t == "date":
        import datetime as dt
        value = dt.date.fromisoformat(str(value)).isoformat()
    else:
        value = str(value)
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    e.extra.setdefault("fields", {})[name] = value
    db.save(e)
    return e


def evaluate_formula(expr: str, variables: Dict[str, float]) -> float:
    """Evaluate arithmetic like ``hours * rate * 1.09`` safely (no names except variables, no calls except min/max/round/abs)."""
    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool): return n.value
        if isinstance(n, ast.Name):
            if n.id in variables: return float(variables[n.id])
            raise ValueError(f"unknown variable {n.id}")
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            r = ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(r) > 10: raise ValueError("exponent too large")
            return _BIN[type(n.op)](ev(n.left), r)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            return -ev(n.operand) if isinstance(n.op, ast.USub) else ev(n.operand)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS and not n.keywords:
            return float(_FUNCS[n.func.id](*[ev(a) for a in n.args]))
        raise ValueError("unsupported expression")
    if len(expr) > 200:
        raise ValueError("expression too long")
    try:
        return float(ev(ast.parse(expr, mode="eval")))
    except ZeroDivisionError:
        raise ValueError("division by zero") from None
    except SyntaxError:
        raise ValueError("syntax error") from None


def entry_formula(db: Database, entry_id: str, expr: str) -> float:
    """Formula over an entry: variables hours, minutes, rate (extra.rate or 0), and any numeric custom field."""
    e = db.get(TimeEntry, entry_id)
    if e is None:
        raise KeyError(entry_id)
    v: Dict[str, float] = {"hours": e.duration_sec / 3600, "minutes": e.duration_sec / 60, "rate": float(e.extra.get("rate", 0)),
                           "estimate_hours": e.estimated_min / 60}
    for k, val in e.extra.get("fields", {}).items():
        if isinstance(val, (int, float)):
            v[k] = float(val)
    return evaluate_formula(expr, v)
