# WorkTracker 6 (rewrite of work_tracker.py v5)

Offline-first, lightweight Persian work tracker. Answers: **"How many hours did I work this year, and on what?"**

## Run
    pip install PyQt5            # only dependency needed to run
    python -m worktracker.main   # from the folder that contains `worktracker/`
Data lives in `%APPDATA%/WorkTracker` (Windows) or `~/.local/share/worktracker`; override with `WORKTRACKER_HOME`.

## Tests
    python -m unittest discover -s worktracker/tests -t .      # 173 tests (3 smoke tests need real PyQt5; a fake-Qt harness covers UI code paths otherwise)
    QT_QPA_PLATFORM=offscreen python -m unittest ...           # headless UI smoke tests

## Layout
- `core/` persian (Jalali, Tehran time), models (single JSON/UTC serialization point), database (WAL, migrations, backup, legacy v5 import)
- `services/` tracker (timer, rounding, min duration, idle trim, 4h auto-split), analytics (year summary, heatmap, streaks, score, forecast, budgets), exporter (JSON/CSV/XLSX + re-import), idle (OS idle APIs)
- `ui/` Liquid Glass widgets (animated blob background, glass cards, heatmap, donut, bars), main window, command palette (Ctrl+K)

## Guarantees
No network calls anywhere; Google Calendar is not required (and not yet ported - see ROADMAP). No telemetry. One-click export of everything.

See docs/ (FEATURE_STATUS = honest per-feature status, API, USER_GUIDE, DEVELOPER, CHANGELOG, ROADMAP). Benchmark: `python -m worktracker.tools.bench`.

## ROADMAP (not yet built) — full list in docs/ROADMAP.md
Kanban/Gantt/sprints/milestones, planner views, Pomodoro orb, invoices UI + PDF, Google Calendar/CalDAV plugins, AES backups,
global hotkey, multi-timer, themes beyond dark/light, packaging scripts, screenshot tests, bundled Vazirmatn font.


## Size
~7295 source lines + ~2148 test lines (the 50k target was not padded to).

## Packaging
`packaging/` has PyInstaller scripts for Windows (+Inno Setup), Linux and macOS — written but **not executed here**; run them on each OS.
