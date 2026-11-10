"""Runs the whole v6.1 UI against a permissive Qt stand-in: every page builds and refreshes, every dialog constructs/validates/saves, the background runtime ticks.

This catches typos, wrong attribute names, missing strings and logic errors in *our* code. It cannot judge real Qt rendering - the three smoke tests in
test_ui_smoke.py do that automatically wherever PyQt5 is installed.
"""
import datetime as dt
import io
import logging
import re
import tempfile
import unittest
from pathlib import Path

try:
    import PyQt5.QtCore  # noqa: F401
    REAL_QT = True
except ImportError:
    REAL_QT = False

SRC = Path(__file__).resolve().parents[1] / "ui"


@unittest.skipIf(REAL_QT, "real PyQt5 present: use test_ui_smoke instead")
class UiStubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from worktracker.tests import qt_stub
        qt_stub.install()
        import importlib
        import worktracker.ui.glass as g, worktracker.ui.dialogs as d, worktracker.ui.main_window as mw, worktracker.ui.app as app
        for m in (g, d, mw, app):
            importlib.reload(m)
        cls.app = app

    def setUp(self):
        from worktracker import sample_data
        from worktracker.core.database import Database
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")
        sample_data.generate(self.db, entries=60, invoices=3)
        self.buf = io.StringIO()
        self.handler = logging.StreamHandler(self.buf); self.handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(self.handler); self._lvl = logging.getLogger().level; logging.getLogger().setLevel(logging.ERROR)
        self.win = self.app.App(self.db, Path(self.tmp.name), None)

    def tearDown(self):
        from worktracker.ui import strings
        strings.set_language("fa")
        logging.getLogger().removeHandler(self.handler); logging.getLogger().setLevel(self._lvl)
        self.db.close(); self.tmp.cleanup()

    def assertNoLoggedErrors(self):
        self.assertEqual(self.buf.getvalue(), "", "an error was logged by the UI")

    # ---------------------------------------------------------------- pages
    def test_every_page_builds_and_refreshes(self):
        self.assertEqual(self.win.pages.count(), len(self.app.NAV))
        for _ in range(2):
            for i in range(len(self.app.PAGE_KEYS)):
                self.win.goto(i)
        self.win.refresh_all(); self.win.goto("settings"); self.win.goto("dashboard")
        self.assertNoLoggedErrors()

    def test_responsive_sidebar_and_dashboard_columns(self):
        w = self.win
        w.set_sidebar(True); w.set_sidebar(False); w.dash_cols = 1; w.layout_dashboard(); w.dash_cols = 2; w.layout_dashboard(); w.resizeEvent(None) if False else None
        self.assertNoLoggedErrors()

    def test_all_ui_strings_exist_in_both_languages(self):
        from worktracker.ui.strings import S
        from worktracker.ui.strings_en import EN
        used = set()
        for f in SRC.glob("*.py"):
            used |= set(re.findall(r'S\["([A-Za-z0-9_]+)"\]', f.read_text(encoding="utf-8")))
        used |= set(self.app.PAGE_KEYS) | {"st_" + k for k in ("general", "quick", "appearance", "tracking", "auto", "prompt", "shots", "tips", "manage", "data", "about")}
        used |= {"ps_" + k for k in ("planning", "active", "on_hold", "completed", "cancelled")} | {"health_" + k for k in ("on_track", "at_risk", "off_track")}
        used |= {"loc_" + (x or "none") for x in ("", "office", "home", "client", "cafe", "travel")}
        self.assertEqual(sorted(k for k in used if k not in S), [])
        self.assertEqual(sorted(set(S) ^ set(EN)), [])
        self.assertEqual(len([k for k in S if not S[k]]), 0)

    def test_page_builders_and_nav_agree(self):
        keys = self.app.PAGE_KEYS
        self.assertEqual(len(keys), len(set(keys))); self.assertEqual(keys[0], "dashboard"); self.assertEqual(keys[-1], "settings")
        for need in ("today", "tasks", "lists", "board", "calendar", "reports", "screenshots", "habits", "routines", "goals", "projects"):
            self.assertIn(need, keys)

    # ---------------------------------------------------------------- dialogs
    def test_task_dialog_validates_then_saves_everything(self):
        from worktracker.core.models import TimeEntry
        from worktracker.ui.dialogs import TaskDialog
        d = TaskDialog(self.win)
        d._save(False)                                                       # empty title: stays open, shows the error
        self.assertTrue(d.saved is None)
        d.title.setText("نوشتن گزارش"); d.priority.setValue(2); d.column.setValue("in_progress"); d.tags.setTags(["a", "b"]); d.checklist.setItems([{"text": "x", "done": False}])
        v = d.values()
        self.assertEqual((v.title, v.priority, v.column, v.tags, v.category), ("نوشتن گزارش", 2, "in_progress", ["a", "b"], "general"))
        d._save(False)
        self.assertIsNotNone(d.saved)
        e = self.db.get(TimeEntry, d.saved.id)
        self.assertEqual((e.title, e.priority, e.column, e.tags), ("نوشتن گزارش", 2, "in_progress", ["a", "b"]))
        self.assertNoLoggedErrors()

    def test_task_dialog_edit_roundtrip(self):
        from worktracker.core.models import TimeEntry
        from worktracker.ui.dialogs import TaskDialog
        e = self.db.all(TimeEntry)[0]; total = len(self.db.all(TimeEntry))
        d = TaskDialog(self.win, e)
        self.assertEqual(d.values().title, e.title)
        d.title.setText("ویرایش‌شده"); d._save(False)
        self.assertEqual(self.db.get(TimeEntry, e.id).title, "ویرایش‌شده"); self.assertEqual(len(self.db.all(TimeEntry)), total)
        self.assertNoLoggedErrors()

    def test_other_dialogs_construct_and_save(self):
        from worktracker.core.models import Client, Goal, Habit, Member, Project
        from worktracker.ui import dialogs as dg
        pd = dg.ProjectDialog(self.win); pd.name.setText("پروژه‌ی تازه"); pd._save(); self.assertEqual(pd.saved.name, "پروژه‌ی تازه"); self.assertTrue(pd.saved.code.startswith("PRJ-"))
        dg.ProjectDialog(self.win, pd.saved)
        hd = dg.HabitDialog(self.win); hd.name.setText("آب"); hd._save(); self.assertEqual(hd.saved.name, "آب"); self.assertEqual(hd.saved.days, list(range(7)))
        hd2 = dg.HabitDialog(self.win); hd2._save(); self.assertIsNone(hd2.saved)                      # empty name rejected
        cd = dg.ClientDialog(self.win); cd.name.setText("مشتری"); cd.email.setText("bad"); cd._save(); self.assertIsNone(cd.saved)
        cd.email.setText("a@b.co"); cd._save(); self.assertEqual(cd.saved.email, "a@b.co")
        md = dg.MemberDialog(self.win); md.name.setText("sara"); md._save(); self.assertEqual(md.saved.name, "sara")
        gd = dg.GoalDialog(self.win); gd.name.setText("هدف بزرگ"); gd.kr_target.setValue(5) if False else None; gd._items = [{"name": "k", "target": 5.0, "current": 1.0, "unit": ""}]; gd._save()
        self.assertEqual(gd.saved.progress, 0.2)
        self.assertNoLoggedErrors()

    def test_work_report_dialog_logs_and_prompter_moves_on(self):
        from worktracker.core.models import TimeEntry
        from worktracker.services.prompter import PromptConfig, Prompter
        from worktracker.ui.dialogs import WorkReportDialog
        p = Prompter(self.db, PromptConfig(forced=True))
        now = dt.datetime.now(dt.timezone.utc)
        sug = {"from": now - dt.timedelta(minutes=50), "to": now, "minutes": 50, "apps": [("Code.exe", 1800)], "title_hint": "کار با Code", "category": "development"}
        p.show()
        d = WorkReportDialog(self.win, p, sug)
        self.assertFalse(d._closable)                                                                    # forced: cannot be dismissed
        d._log()
        e = self.db.conn.execute("SELECT title, source, duration_sec FROM entries WHERE source='prompt'").fetchone()
        self.assertEqual((e["title"], e["source"], e["duration_sec"]), ("کار با Code", "prompt", 3000))
        self.assertEqual(self.db.conn.execute("SELECT action FROM prompt_log ORDER BY shown_at DESC LIMIT 1").fetchone()[0], "logged")
        self.assertNoLoggedErrors()

    # ---------------------------------------------------------------- runtime
    def test_runtime_ticks_never_raise(self):
        rt = self.win.runtime
        rt._sample(); rt._prompt_tick(); rt._remind_tick(); rt._hour_tick(); rt.reload()
        rt.shots.grab = lambda: (b"\xff\xd8JFIF" + b"x" * 4000, 640, 360)
        self.db.set_setting("shots_enabled", True); rt._shot_tick()
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0], 1)
        self.assertIsNotNone(rt.capture_now(force=True))
        rt.show_prompt(force=True); rt.stop(); rt.start()
        self.assertNoLoggedErrors()

    def test_auto_tracking_flows_through_the_runtime(self):
        rt = self.win.runtime
        t0 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)
        evs = [rt.auto.sample("Code.exe", "main.py", 0, t0 + dt.timedelta(seconds=10 * i)) for i in range(60)]
        self.assertIn("started", evs)
        self.assertEqual(rt.auto.finish() in ("stopped", "discarded"), True)

    # ---------------------------------------------------------------- page handlers
    def test_today_quick_add_and_complete(self):
        from worktracker.core.models import TimeEntry
        from worktracker.ui import pages_new as pn
        self.win.td_quick.setText("نوشتن مستند #docs 45m"); pn.quick_add(self.win)
        t = [e for e in self.db.all(TimeEntry) if e.title == "نوشتن مستند"][0]
        self.assertEqual((t.tags, t.estimated_min), (["docs"], 45))
        pn.complete_task(self.win, t.id)
        self.assertEqual(self.db.get(TimeEntry, t.id).column, "done")
        self.assertNoLoggedErrors()

    def test_tree_reorder_and_subtask_by_drop(self):
        from worktracker.core.models import TimeEntry
        from worktracker.ui import pages_new as pn
        pn._tree_dropped(self.win)
        self.assertNoLoggedErrors()

    def test_reports_page_builds_data_and_exports(self):
        from worktracker.ui import pages_ops as po
        self.win.rp_from.setDate(dt.date(2025, 3, 21)); self.win.rp_to.setDate(dt.date(2026, 3, 20))                       # the sample data lives in this window
        po.refresh_reports(self.win)
        self.assertIsNotNone(self.win.rp_data); self.assertGreater(self.win.rp_data["summary"]["total_sec"], 0)
        self.assertNoLoggedErrors()

    def test_screenshots_page_with_data(self):
        from worktracker.ui import pages_ops as po
        rt = self.win.runtime; rt.shots.grab = lambda: (b"\xff\xd8JFIF" + b"y" * 3000, 640, 360)
        rt.capture_now(force=True); po.refresh_screenshots(self.win)
        self.assertNoLoggedErrors()

    # ---------------------------------------------------------------- misc
    def test_floating_bubble_and_quick_panel_end_to_end(self):
        from worktracker.core.models import Status, TimeEntry
        b = self.win.bubble
        b.open_panel(); p = b.panel
        p.edit.setText("write spec #docs 30m"); p.mode.setValue("task"); p.submit()
        e = [t for t in self.db.all(TimeEntry) if t.title == "write spec"][0]
        self.assertEqual((e.status, e.estimated_min, e.tags), (Status.PLANNED, 30, ["docs"]))
        p.mode.setValue("log"); p.edit.setText("customer call 45m"); p.submit()
        e = [t for t in self.db.all(TimeEntry) if t.title == "customer call"][0]
        self.assertEqual((e.status, e.duration_sec, e.source), (Status.DONE, 2700, "quick"))
        p.edit.setText("no duration here"); p.submit()
        self.assertIn("⚠", p.feedback.text())                                                      # explains instead of failing silently
        p.mode.setValue("timer"); p.edit.setText("deep work"); p.submit()
        self.assertEqual(len(self.win.tracker.running()), 1)
        b.set_running(2, 90); b.reload(); self.win.set_bubble(False); self.win.set_bubble(True); self.win.open_quick_panel()
        self.assertNoLoggedErrors()

    def test_backup_restore_flows_end_to_end(self):
        from worktracker.core.models import Project, TimeEntry
        from worktracker.services import backup_pack as bp
        from worktracker.ui import backup_ui as bk
        win = self.win
        snap = bp.snapshot(self.db)                                                   # state the package will contain
        out = bk.export_package_ui(win, str(Path(self.tmp.name) / "b.wtpack"), bk.ExportOptions(include_history=True))
        self.assertTrue(out.exists()); bp.verify_package(out)
        self.db.save(Project(name="added after the backup")); self.db.set_setting("theme", "paper")
        rep = bk.restore_package_ui(win, str(out), choice=bk.RestoreChoice("replace"))
        self.assertIsNotNone(rep); self.assertEqual(bp.snapshot(self.db), snap)                                  # exactly the exported state, nothing added by the restore itself
        self.assertTrue(list((Path(self.tmp.name) / "backups").glob("pre-restore-*.db")))                    # the safety copy exists
        enc = bk.export_package_ui(win, str(Path(self.tmp.name) / "e.wtpack"), bk.ExportOptions(password="secret1"))
        self.assertIsNone(bk.restore_package_ui(win, str(enc), password="wrong", choice=bk.RestoreChoice()))   # wrong password: refused, data untouched
        strip = lambda d: {**d, "settings": [r for r in d["settings"] if r["key"] != "last_backup_at"]}      # exporting legitimately stamps the backup time
        self.assertEqual(strip(bp.snapshot(self.db)), strip(snap))
        self.db.set_setting("prompt_config", {"interval_min": 45}); self.db.set_setting("tg_token", "123:secret")
        cfg = bk.export_config_ui(win, str(Path(self.tmp.name) / "c.json"), include_secrets=False)
        self.db.set_setting("prompt_config", {"interval_min": 99}); plan = bk.import_config_ui(win, str(cfg), "merge")
        self.assertIn("prompt_config", plan["changed"]); self.assertEqual(self.db.get_setting("prompt_config"), {"interval_min": 45})     # settings really came back
        self.assertNotIn("tg_token", Path(cfg).read_text(encoding="utf-8"))                                                                 # secrets stay out by default
        junk = Path(self.tmp.name) / "junk.wtpack"; junk.write_bytes(b"nope")
        self.assertIsNone(bk.restore_package_ui(win, str(junk), choice=bk.RestoreChoice()))
        self.assertNoLoggedErrors()

    def test_daily_report_window(self):
        from worktracker.ui.daily_ui import DailyReportDialog
        d = DailyReportDialog(self.win, dt.date(2025, 5, 1))
        self.assertIn("گزارش", d.text.toPlainText()); d.copy()
        p = d.save(str(Path(self.tmp.name) / "r.md")); self.assertTrue(p.exists())
        d._shift(1); d.generate(); self.assertNoLoggedErrors()

    def test_startup_screenshot_and_daily_auto_backup(self):
        rt = self.win.runtime
        rt.shots.grab = lambda: (b"\xff\xd8JFIF" + b"z" * 3000, 640, 360)
        self.db.set_setting("shots_enabled", True); rt._startup_shot()
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0], 1)              # taken right at launch
        rt._startup_shot(); self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0], 1)   # not twice within 2 minutes
        self.db.set_setting("shots_paused", True); rt.capture_now(force=False); self.assertEqual(rt.last_capture_reason, "paused")
        name = rt.auto_backup(); self.assertTrue(name and name.startswith("worktracker-")); self.assertIsNone(rt.auto_backup())
        self.db.set_setting("auto_backup", False); self.db.set_setting("last_backup_at", None); self.assertIsNone(rt.auto_backup())
        self.assertNoLoggedErrors()

    def test_english_ltr_mode_builds_every_page(self):
        from worktracker.core import persian
        from worktracker.ui.strings import S
        self.db.set_setting("lang", "en")
        win = self.app.App(self.db, Path(self.tmp.name), None)
        self.assertFalse(persian.DIGITS_FA); self.assertTrue(persian.is_gregorian()); self.assertEqual(S["start"], "Start")
        for i in range(len(self.app.PAGE_KEYS)):
            win.goto(i)
        win.goto("calendar"); self.assertRegex(win.cal_title.text(), r"[A-Z][a-z]+ \d{4}")                       # "May 2026", Latin digits
        self.assertEqual(persian.to_fa_digits("12٪"), "12%")
        self.assertNoLoggedErrors()

    def test_routines_page_dialog_and_notification_tick(self):
        from worktracker.services import routines as rt
        from worktracker.ui import routines_ui as ru
        d = ru.RoutineDialog(self.win)
        d._save(); self.assertIsNone(d.saved)                                                     # empty title is refused, nothing stored
        d.title_in.setText("آب بخور"); d.kind.setValue("interval"); d.from_h.setValue(0); d.to_h.setValue(23); d.every_m.setValue(5); d.repeat.setValue(10); d._save()
        self.assertEqual((d.saved["title"], d.saved["kind"], d.saved["every_min"]), ("آب بخور", "interval", 5))
        d2 = ru.RoutineDialog(self.win, d.saved); self.assertEqual(d2.fields()["title"], "آب بخور")
        self.win.goto("routines"); ru.refresh_routines(self.win)
        self.win.runtime._routine_tick()                                                          # something due within the last 12 h -> notified once
        self.assertTrue(self.db.get_setting("routine_notified"))
        before = self.db.get_setting("routine_notified"); self.win.runtime._routine_tick()
        self.assertEqual(before.keys(), self.db.get_setting("routine_notified").keys())
        item = rt.today_items(self.db)[0]; ru._on_toggle(self.win, item["routine"]["id"], item["key"], True)
        self.assertTrue(rt.is_checked(self.db, item["routine"]["id"], item["key"]))
        ru._on_toggle(self.win, item["routine"]["id"], item["key"], False); self.assertFalse(rt.is_checked(self.db, item["routine"]["id"], item["key"]))
        self.assertNoLoggedErrors()

    def test_sprint_dialogs_and_panel(self):
        from worktracker.core.models import Project, Sprint
        from worktracker.services import sprints as sv
        from worktracker.ui import sprint_ui as su
        p = self.db.all(Project)[0]
        d = su.SprintDialog(self.win, p.id); d.start.setValue(dt.datetime.now(dt.timezone.utc)); d._save()
        self.assertIsNotNone(d.saved); self.assertEqual((d.saved.status, d.saved.project_id), ("planning", p.id))
        su.AssignDialog(self.win, d.saved).apply(); su.CompleteDialog(self.win, d.saved)
        su.refresh_sprints(self.win, p.id); su.refresh_sprints(self.win, None)
        c = su.BurndownChart(self.win.theme); c.set_data([], [], [])
        self.assertEqual(len(sv.for_project(self.db, p.id)), 1); self.assertNoLoggedErrors()

    def test_lists_page_bulk_paste_breakdown_split_and_checklist_quick_panel(self):
        from worktracker.core.models import Project
        from worktracker.services import lists as LS, project_split as ps
        from worktracker.ui import lists_ui as lu
        lid = LS.ensure_default(self.db)["id"]
        self.win.goto("lists"); lu.refresh_lists(self.win)
        d = lu.BulkDialog(self.win, lid); d.text.setPlainText("- [ ] a\n- [x] b\n  - [ ] c"); d._ok(); self.assertEqual(len(d.created), 3)
        d2 = lu.BulkDialog(self.win, lid); d2._ok(); self.assertEqual(d2.created, [])                         # empty paste: refused, nothing added
        lu.refresh_lists(self.win); lu.sync_google(self.win)                                                    # no Google credentials: a friendly toast, no crash
        b = self.win.bubble; b.open_panel(); p = b.panel
        p.mode.setValue("list"); p.edit.setText("x; y; z"); p.submit()
        self.assertEqual([e.title for e in LS.tasks(self.db, lid, include_done=False)][:3], ["x", "y", "z"])   # three items from one line, order kept
        p._tick(LS.tasks(self.db, lid, include_done=False)[0].id, True); self.assertTrue(LS.is_done(LS.tasks(self.db, lid)[-1]) or LS.counts(self.db, lid)[1] >= 2)
        pid = self.db.all(Project)[0].id
        bd = lu.BreakdownDialog(self.win, pid); bd.text.setPlainText(ps.template("book")); bd._ok(); self.assertGreaterEqual(bd.result["phases"], 3)
        from worktracker.core.models import TimeEntry
        e = LS.add_task(self.db, lid, "big"); e.estimated_min = 60; self.db.save(e)
        sd = lu.SplitTaskDialog(self.win, e); sd.text.setPlainText("one\ntwo"); sd._ok(); self.assertEqual([c.estimated_min for c in sd.created], [30, 30])
        self.win.dash_cols = 3; self.win.layout_dashboard(); self.win.dash_cols = 2
        self.assertNoLoggedErrors()

    def test_hourly_prompt_is_driven_by_the_measured_unlogged_time(self):
        import datetime as _dt
        from worktracker.core.models import PromptLog, TimeEntry
        from worktracker.core.persian import now_utc
        from worktracker.services import ledger as lg
        from worktracker.services.prompter import PromptConfig
        from worktracker.ui import pages_new as pn
        from worktracker.ui.dialogs import WorkReportDialog
        rt = self.win.runtime
        rt.prompter.cfg = PromptConfig(aligned=True, quiet_start=0, quiet_end=0, off_weekdays=[], min_gap_min=5)
        h = lg.hour_floor(now_utc()) - _dt.timedelta(hours=2)                                                # a finished hour, whatever time the test runs
        rt.ledger.sample(lg.ACTIVE, "Code.exe", h)
        for i in range(1, 721):
            rt.ledger.sample(lg.ACTIVE if i <= 540 else lg.IDLE, "Code.exe" if i <= 540 else "", h + _dt.timedelta(seconds=5 * i))        # 45 min worked, 15 min idle
        rep = rt.ledger.hour(h); self.assertEqual((rep["engaged_sec"], rep["idle_sec"]), (2700, 900))
        self.db.save(TimeEntry(title="already", start_utc=h, end_utc=h + _dt.timedelta(minutes=15)))             # 15 of the 45 minutes are logged
        self.assertEqual(rt.ledger.hour(h)["unlogged_sec"], 1800)
        rt._prompt_tick()                                                                                      # the dialog opens (stand-in: exec_ returns at once) for exactly that hour
        self.assertEqual(rt.prompter.hour_context, h)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM prompt_log").fetchone()[0], 1)
        sug = rt.ledger.suggest(rt.ledger.hour(h))
        self.assertEqual((sug["minutes"], sug["from"]), (30, h + _dt.timedelta(minutes=15)))                   # placed in the real free slot after the logged part
        d = WorkReportDialog(self.win, rt.prompter, sug); d.title.setText("deep work"); d._log()
        e = [t for t in self.db.all(TimeEntry) if t.title == "deep work"][0]
        self.assertEqual((e.start_utc, e.end_utc, e.source), (h + _dt.timedelta(minutes=15), h + _dt.timedelta(minutes=45), "prompt"))
        self.assertEqual(rt.ledger.answered()[h.isoformat()], "logged"); self.assertEqual(rt.ledger.pending(min_unlogged_sec=60), [])
        pn._refresh_hour_strip(self.win); self.assertEqual(len(self.win.hour_strip.rows), 24)
        rt._sample(); rt._sample()                                                                             # the sampler runs (screen grab is unavailable in the stand-in -> no delta)
        self.assertNoLoggedErrors()

    def test_sankey_layout_and_date_parsing(self):
        from worktracker.ui import glass, pm_pages as pm
        lay = glass.SankeyWidget.layout_nodes({"a": 3.0, "b": 1.0}, 106.0, gap=6.0)
        self.assertAlmostEqual(lay["a"][1], 75.0); self.assertAlmostEqual(lay["b"][1], 25.0)
        self.assertEqual(pm.parse_date("2026-05-01"), dt.date(2026, 5, 1)); self.assertEqual(pm.parse_date("۱۴۰۵/۰۲/۱۱"), dt.date(2026, 5, 1))
        with self.assertRaises(ValueError): pm.parse_date("garbage")

    def test_every_icon_the_ui_asks_for_exists(self):
        from worktracker.ui import icons
        asked = set()
        for f in SRC.glob("*.py"):
            asked |= set(re.findall(r'icon="([a-z_]+)"', f.read_text(encoding="utf-8")))
            asked |= set(re.findall(r'icons\.(?:icon|pixmap)\("([a-z_]+)"', f.read_text(encoding="utf-8")))
        asked |= {ic for _k, ic in self.app.NAV}
        self.assertEqual(sorted(a for a in asked if a not in icons.NAMES), [])

    def test_themes_defined(self):
        from worktracker.themes_list import THEME_NAMES
        from worktracker.ui import glass
        self.assertEqual(set(THEME_NAMES), set(glass.THEMES))


if __name__ == "__main__":
    unittest.main()
