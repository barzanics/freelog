# Changelog
## 6.0.0
- Full rewrite: modular package, UTC storage + Tehran display, JSON-only list serialization, WAL SQLite with versioned migrations (v1, v2).
- Tracker, analytics (year summary/heatmap/streaks/score/forecast), Pomodoro (persistent), projects (kanban, dependencies w/ cycle check, Gantt, milestones, sprints, health), planner (free slots, auto-schedule, buffers, Eisenhower, estimate learning).
- Billing (rates, invoices from time, payments, retainers, currencies, HTML/PDF), search operators, offline smart suggestions, automation rules, habits/OKRs, undo/redo, AES-256-GCM backups.
- Integrations: ICS export, webhook (opt-in), Toggl/Clockify import, git commits, legacy v5 import.
- Liquid Glass UI (PyQt5).

## 6.0.1 (this build)
- Migrations v3/v4: team, comments, activity events, saved filters, fuller project fields, completion time, private notes.
- Version history + time travel (audit snapshots, gzip compression of old ones), nestable transactions.
- Multi-timer, quick capture, recurrence, reminders (20-20-20/posture/water), folder sync, soundscapes, hotkey parsing.
- Insights: WoW/YoY, flow sessions, context switches, early-start effect, Sankey data, year-in-review, weekly review, funnels, cohorts, KPIs, saved dashboards, week/month planner views, time-box adherence.
- Integrations: Google Calendar plugin, CalDAV, Telegram/Slack, local HTTP API (+ web activity), RescueTime import, autostart.
- UI: 7 themes, accent, wallpaper, English/Persian, planner/analytics/habits/team pages, mini timer, focus mode, toasts, button ripple.
- Fake-Qt harness so UI code paths run in CI without a display.

## 6.0.2 (this build)
- New screens: PM (Gantt with dependency arrows, milestone rings, sprints, subtasks/dependencies), Eisenhower matrix (drag-drop), Tools hub (OKR/SMART, templates, saved filters, custom fields/formulas, time travel, bulk entry, reports, recurring invoices, KPIs, blueprints, dashboard layout).
- Analytics: Sankey diagram. Dashboard: configurable order/visibility. Timer: energy 1-5.
- Ambient screensaver, multi-window (detach page), dynamic tray icon (elapsed minutes).
- Services: reports (Markdown/HTML/per-client), recurring invoices, bulk entry, resume-after-idle, Telegram polling, smart task names, typing-mood heuristic, energy analysis, SMART validation, same-week-last-year, activity feed, Eisenhower setters, config + DB recovery.
- Reliability tests: 2 concurrent writers, kill mid-write, corrupt DB recovery, network blocked, cold start.

## 6.1.0 - Liquid
- New shell (`ui/app.py`), 19 pages, liquid effects engine, icon set, IRANSans loader, global stylesheet, responsive layout.
- Rich dialogs, forced work-report prompt, auto-tracking, hourly zipped screenshots, tips, full report builder, sectioned settings.
- Data: migration v5 (task form fields, rank, source, screenshots, hour log, prompt log). **Fixed: INSERT OR REPLACE cascade deleted child rows on every edit.**

## 6.2.0
- Floating quick-access bubble + quick panel (one-line grammar with time ranges), formal daily report (fa/en), routines (hourly/daily/weekly/monthly check boxes with notifications),
  full sprint lifecycle (carry-over, burndown, velocity, forecast), accurate export/restore (.wtpack with SHA-256 manifest, atomic restore, safety backup, merge, optional AES-256) and
  settings export/import, automatic daily backup, English/LTR + Gregorian mode, live palette switching, engagement model (frozen screen / passive presence), screenshot at start-up with reasons.
- Fixed: infinite loop in hour spreading for entries with fractional seconds crossing an hour; restore no longer writes settings of its own.

## 6.3.0
- Hourly ledger (exact active/passive/idle seconds per clock hour and app, sleep gaps ignored), screen-signature frozen-screen detection, hour-aligned prompts about the measured *unlogged* part of each hour,
  hour strip on Today, "same as last" in the prompt. Lists page (Google-Tasks style) + two-way Google Tasks sync, check-list mode in the floating panel, Markdown outline parser, bulk paste,
  project breakdown from an outline (phases/tasks/sub-tasks, templates), task split with shared estimate, project split. Dialogs are sized before they are placed (footer buttons stay inside the window);
  pages scroll instead of squashing cards; dashboard has 1-3 columns and minimum card heights.
- Fixed: a task deleted locally could be re-imported from Google before the remote delete was sent; semicolon-separated quick lists were read as sub-tasks.
