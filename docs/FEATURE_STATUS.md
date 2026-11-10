# v6.3 additions
Hourly ledger ✅ · hour-aligned prompt ✅🖥 · hour strip ✅🖥 · lists page ✅🖥 · Google Tasks sync ✅ (tested against a faithful in-memory fake of the API, **not against the real Google service**) ·
checklist mode in the bubble ✅🖥 · project breakdown / task split / project split ✅🖥 · dialog placement + scrolling pages ✅🖥 (fixed by reasoning about the cause; not seen on a real display).
Still open: learning/news page, personal-growth page, week view, hamburger drawer and sliding nav indicator, full localisation of the remaining Persian-only strings in the code.

# v6.2 additions
Floating bubble + quick panel ✅🖥 · formal daily report ✅🖥 · routines (scheduled check boxes + notifications) ✅🖥 · sprint lifecycle/burndown/velocity ✅🖥 · exact export/restore + config export/import ✅🖥 ·
English/LTR/Gregorian mode ✅🖥 · live theme switching ✅🖥 · engagement model ✅ · Google Calendar/Tasks sync: Calendar ✅ (needs your Google credentials), **Tasks sync not implemented yet**.
Services behind every item above are covered by automated tests (274 non-UI + 24 UI-stand-in tests); 🖥 = Qt rendering not verified on a real display.

# v6.1 additions
Liquid look (morphing blobs, poppable bubbles, jelly cards, liquid buttons/switch, drips while dragging, procedural sounds) ✅🖥 · IRANSans from `assets/fonts` ✅ · 64 vector icons ✅ ·
responsive sidebar/dashboard ✅🖥 · full task/project/habit/client/member/goal forms ✅🖥 · forced work-report prompt ✅🖥 · auto work detection ✅ · hourly zipped screenshots ✅🖥 ·
tip of the hour ✅🖥 · full report builder (8 kinds, 20 sections, 5 formats) ✅🖥 · 10-section settings ✅🖥 · INSERT-OR-REPLACE data-loss bug fixed ✅.
**Not verified on a real display:** everything marked 🖥. The logic behind each (✅) is covered by 251 tests; the Qt rendering is only exercised by a stand-in.

# Feature status vs. the 100-feature spec

Legend: **✅** logic built and unit-tested here · **🖥** has a UI screen/control (written, runs against a fake-Qt harness here; **needs a run on real PyQt5**) · **◐** partial · **⛔** not built

| # | Feature | Status | Notes |
|---|---|---|---|
| 1 | Auto time capture | ✅ ◐ | `services/activity` records the active window and suggests a task; settings toggle 🖥; no suggestion popup yet |
| 2 | OS idle detection | ✅ | Windows/macOS/Linux code paths (`xprintidle` needed on Linux); only no-crash verified here |
| 3 | App usage analytics | ✅ 🖥 | analytics page lists top apps |
| 4 | Website tracking | ◐ | `POST /v1/activity` endpoint + domain grouping ✅; **browser extension not built** |
| 5 | Smart categorization | ✅ | Naive Bayes, learns from corrections (not yet auto-prompted in UI) |
| 6 | Focus sessions / DND | ◐ | Focus mode 🖥 (hides sidebar, silences reminders); OS Do-Not-Disturb ⛔ |
| 7 | Time blocking | ✅ ◐ | service + planner list 🖥; no drag-onto-timeline canvas |
| 8 | Kanban | ✅ 🖥 | drag-drop columns, dependency-blocked moves |
| 9 | Gantt | ✅ 🖥 | dependency-aware dates + drawn bars/arrows (PM page) |
| 10 | Milestones | ✅ 🖥 | progress ring on PM page |
| 11 | Subtasks | ✅ 🖥 | PM page |
| 12 | Dependencies | ✅ | cycle rejection, 4 types + lag |
| 13 | Project templates | ✅ 🖥 | blueprints in Tools |
| 14 | Team members | ✅ 🖥 | |
| 15 | Time budgets | ✅ ◐ | health/budget status ✅; no over-budget warning UI |
| 16 | Sprints | ✅ 🖥 | PM page |
| 17 | Daily planner | ◐ 🖥 | free slots + auto-schedule; no morning/evening routine |
| 18 | Weekly review | ✅ 🖥 | |
| 19 | OKR tracking | ✅ 🖥 | Tools |
| 20 | Habit tracker | ✅ 🖥 | streaks, weekly completion |
| 21 | SMART goals | ✅ 🖥 | SMART validation when adding a goal |
| 22 | Estimates vs actuals | ✅ | learned per-category bias |
| 23 | Energy tracking | ✅ 🖥 | 1-5 selector on the timer; peak-energy hours service |
| 24 | Interactive/zoomable charts | ⛔ | static charts only |
| 25 | Year in Review | ✅ 🖥 | text dialog, not a styled slideshow |
| 26 | Productivity score | ✅ 🖥 | |
| 27 | Flow-state detection | ✅ | no UI surface yet |
| 28 | Distraction log | ✅ 🖥 | context switches + estimated cost |
| 29 | Comparative analytics | ✅ | week-over-week, YoY (shown), same-week-last-year (service) |
| 30 | Predictive insights | ✅ 🖥 | peak hours, early-start effect |
| 31 | Year heatmap | ✅ 🖥 | |
| 32 | Sankey | ✅ 🖥 | drawn on Analytics |
| 33 | Drag-drop report builder | ⛔ | saved dashboard *layouts* ✅ (no drag-drop UI) |
| 34 | Multi-client reports | ✅ ◐ | `reports.client_report` (service; no screen) |
| 35 | Invoicing | ✅ 🖥 | HTML (full Persian) ✅; PDF is Latin-only |
| 36 | Rate cards | ✅ | entry > project > client |
| 37 | Currencies | ✅ | manual offline rates |
| 38 | Tax | ◐ | percentage VAT ✅; Iranian-specific rules ⛔ |
| 39 | Payments | ✅ 🖥 | partial/paid |
| 40 | Recurring invoices | ✅ 🖥 | monthly generation, idempotent (button in Tools; not yet auto-run at startup) |
| 41 | Pomodoro | ✅ 🖥 | liquid orb, persisted |
| 42 | Time boxing | ✅ | adherence metric; no UI |
| 43 | Eisenhower matrix | ✅ 🖥 | drag-drop page |
| 44 | Quick capture + hotkey | ✅ 🖥 ◐ | in-app Ctrl+Shift+Space ✅; Windows global hotkey code **untested** |
| 45 | Voice input (Vosk) | ⛔ | |
| 46 | Command palette | ✅ 🖥 | |
| 47 | Keyboard-first / vim nav | ◐ | main shortcuts only |
| 48 | Focus mode | ✅ 🖥 | |
| 49–50 | Break & posture reminders | ✅ 🖥 | tray/toast |
| 51 | Field encryption | ✅ ◐ | AES-GCM + `notes_private`; no UI to enter private notes |
| 52 | Encrypted backup | ✅ 🖥 | |
| 53 | Folder sync | ✅ 🖥 | last-writer-wins; WebDAV/Dropbox/Drive APIs ⛔ (folder-based by design) |
| 54 | Exports | ✅ | JSON/CSV/XLSX/ICS + Markdown/HTML reports; PDF = invoices only |
| 55 | Imports | ✅ ◐ | v5 DB, Toggl, Clockify, RescueTime, bulk paste (UI for v5 + bulk only) |
| 56 | Version history | ✅ | per-object snapshots; no UI |
| 57 | Undo/redo | ◐ 🖥 | works for operations routed through `UndoManager` (e.g. adding kanban tasks), not every UI action |
| 58 | Audit log | ✅ | |
| 59 | Google Calendar | ✅ ◐ | plugin tested with a fake API; **real Google API untested**, no settings UI |
| 60 | CalDAV | ✅ | no UI |
| 61 | iCal export | ✅ 🖥 | |
| 62/94 | Webhooks / on rules | ✅ | fired by automation rules |
| 63 | Telegram | ✅ ◐ | handler + `poll_once` ✅ (no settings UI/timer wiring) |
| 64 | Slack | ✅ | no UI |
| 65 | Git commits | ✅ | no UI button |
| 66 | IDE API | ◐ | server ✅ (see API.md); no UI switch; **VS Code extension not built** |
| 67 | Smart task names | ✅ | `smart2.suggest_titles` (not shown in UI yet) |
| 68 | Auto-tagging | ✅ | |
| 69 | Duplicate detection | ✅ | no UI warning yet |
| 70 | Anomaly detection | ✅ | no UI warning yet |
| 71 | Summaries | ✅ | |
| 72 | Time estimation | ✅ | |
| 73 | Sentiment tagging | ◐ | `typing_mood` heuristic ✅; no keystroke capture (privacy) |
| 74 | Themes | ✅ 🖥 | 7 themes (Aurora Borealis = Aurora); applied after restart |
| 75 | Custom accent | ✅ 🖥 | live |
| 76 | Wallpaper | ✅ 🖥 | live |
| 77 | Soundscapes | ✅ 🖥 | generated white/pink/brown/rain; playback untested |
| 78 | Ambient mode | ✅ 🖥 | idle screensaver + palette action |
| 79/96/97 | Mini always-on-top timer | ✅ 🖥 | |
| 80 | Dynamic tray icon | ✅ 🖥 | shows elapsed minutes |
| 81–86 | Team: sync, profiles, assign, comments, mentions | ✅ 🖥 | activity feed service ✅ (no screen) |
| 87–88 | Templates, batch ops | ✅ ◐ | templates UI ✅; batch ops service only |
| 89 | Smart search | ✅ 🖥 | entries search box |
| 90–92 | Saved filters, custom fields, formulas | ✅ 🖥 | Tools |
| 93 | Automation rules | ✅ ◐ | run on timer stop; no editor UI |
| 95 | Multi-window | ✅ 🖥 | detach page via palette |
| 98 | Session auto-split (4 h) | ✅ | |
| 99 | Time travel | ✅ 🖥 | Tools |
| 100 | Dashboard widgets | ✅ 🖥 | drag to reorder / tick to hide (Tools), applied to the dashboard |

## Non-feature spec items
- **Reliability tests added**: two writers, kill mid-write, corrupt-DB recovery from backup, whole flows with the network blocked, cold start < 0.8 s (core).
- **Performance targets**: only the *core* was measured (open+import ≈ 0.14 s; 100k-row day query ≈ 40 ms; 10k-entry year summary < 0.5 s). **RAM/CPU/cold-start of the full Qt app are unmeasured.**
- **Coverage ≥ 90 %**: not measured (`coverage` unavailable here).
- **Line target (50k)**: see README for the current count. Not reached, deliberately.
- **Cross-platform / HiDPI / screenshot tests / installers / bundled fonts / screenshots**: not done.
- **Google Calendar, Windows hotkey, OS idle, sound playback, real Qt rendering**: need testing on real machines.
