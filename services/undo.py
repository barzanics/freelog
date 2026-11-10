"""Undo/redo for saves and deletes, via row snapshots."""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

from ..core.database import Database

Op = Tuple[type, Optional[dict], Optional[dict]]  # (class, before_row, after_row)


class UndoManager:
    def __init__(self, db: Database, limit: int = 100) -> None:
        self.db, self.limit = db, limit
        self._undo: List[Op] = []
        self._redo: List[Op] = []

    def save(self, obj: Any) -> None:
        before = self.db.get(type(obj), obj.id)
        self.db.save(obj)
        after = self.db.get(type(obj), obj.id)
        self._push((type(obj), before.to_row() if before else None, after.to_row()))

    def delete(self, obj: Any) -> None:
        before = self.db.get(type(obj), obj.id)
        if before and self.db.delete(type(obj), obj.id):
            self._push((type(obj), before.to_row(), None))

    def _push(self, op: Op) -> None:
        self._undo.append(op)
        del self._undo[:-self.limit]
        self._redo.clear()

    def _apply(self, cls: type, row: Optional[dict], other: Optional[dict]) -> None:
        if row is None:
            self.db.delete(cls, other["id"])  # type: ignore[index]
        else:
            self.db.save(cls.from_row(row))  # type: ignore[attr-defined]

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> bool:
        if not self._undo:
            return False
        op = self._undo.pop()
        self._apply(op[0], op[1], op[2])
        self._redo.append(op)
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        op = self._redo.pop()
        self._apply(op[0], op[2], op[1])
        self._undo.append(op)
        return True
