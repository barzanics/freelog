"""Small helper for the project cards: computed fields without importing Qt."""
from __future__ import annotations

from typing import Any, Dict

from ..core.database import Database
from ..core.models import Project
from ..services.blueprints import project_summary


def summary_for(db: Database, p: Project) -> Dict[str, Any]:
    return project_summary(db, p.id)
