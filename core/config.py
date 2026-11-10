"""Central constants (no magic numbers elsewhere)."""
from __future__ import annotations

APP_NAME = "WorkTracker"
DEFAULT_TZ = "Asia/Tehran"
MAX_SESSION_SEC = 4 * 3600
MIN_DURATION_SEC = 60
IDLE_THRESHOLD_SEC = 300
API_PORT = 9876
API_MAX_BODY = 64 * 1024
AUDIT_COMPRESS_AFTER_DAYS = 90
BACKUPS_KEPT = 14
LISTS_PAGE_SIZE = 500
# Value-added-tax presets in percent. These are *user-editable defaults*, not legal advice: verify the current rate for your jurisdiction.
TAX_PRESETS = {"none": 0.0, "vat_ir": 10.0}
