# User guide
Start: `pip install PyQt5` then `python -m worktracker.main` (from the folder that contains `worktracker/`). Sample data: `python -c "from worktracker.core.database import Database; from worktracker import sample_data; db=Database('demo.db'); sample_data.generate(db)"`.

## Pages (sidebar)
| Page | What you can do |
|---|---|
| Dashboard | yearly hours, streak, forecast, heatmap, donut/bars, timer (+energy 1-5, +parallel timers), Pomodoro orb. Order/visibility: Tools → Dashboard layout |
| Entries | virtual table of entries; search supports `tag:bug project:app >2h <30m after:1405/01/01 billable:yes text` |
| Kanban | drag cards between Backlog → In progress → Review → Done (blocked tasks refuse to move) |
| Planner | today's free slots, planned tasks, **auto-schedule** |
| Matrix | Eisenhower: drag tasks between the four quadrants (adjusts importance/deadline) |
| PM | per project: **Gantt** with dependency arrows, milestones with progress ring, sprints with burn/velocity, tasks/subtasks/dependencies |
| Billing | clients, invoice tracked time, mark paid, save HTML invoice (print to PDF) |
| Analytics | productivity score, week/year comparison, peak hours, early-start effect, context-switch cost, weekly review, Sankey, app usage, **Year in review** |
| Habits / Team | streak habits; members, assignment, threaded comments with @mentions |
| Projects | quick project list |
| Tools | goals/OKRs (SMART check), templates, saved filters, custom fields + formulas, **time travel**, bulk entry, Markdown/HTML reports, recurring invoices, KPIs, project blueprints, dashboard layout |
| Settings | Lite mode, ambient screensaver, activity capture, global hotkey, theme (7), language (fa/en), rounding, focus sounds, accent, wallpaper, folder sync, exports (JSON/CSV/XLSX/ICS), backups (plain/encrypted), import from v5 |

## Shortcuts
Ctrl+K palette · Ctrl+Z/Y undo/redo · Ctrl+Shift+Space quick capture (`fix login #bug @App 45m`) · Ctrl+Shift+F focus mode · Ctrl+Shift+M mini timer.
Palette also has: ambient mode, detach current page into its own window.
