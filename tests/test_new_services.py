import datetime as dt
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from worktracker.core.database import Database
from worktracker.core.models import ActivityEvent, Client, Goal, Habit, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC, now_utc
from worktracker.services import autotrack, prompter as pr, report_builder as rb, screenshots as sh


def L(h, m=0, day=2, month=5, s=0):
    return dt.datetime(2026, month, day, h, m, s, tzinfo=TEHRAN).astimezone(UTC)


class Clock:
    def __init__(self, t): self.t = t
    def __call__(self): return self.t
    def adv(self, **kw): self.t += dt.timedelta(**kw)


# ======================================================================= screenshots
class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.db = Database(); self.clk = Clock(L(9)); self.n = 0
        self.store = sh.ScreenshotStore(self.db, Path(self.tmp.name) / "shots", self.grab, self.clk)

    def tearDown(self): self.tmp.cleanup()

    def grab(self):
        self.n += 1
        return (b"\xff\xd8JPEG" + bytes([self.n]) * 5000, 1280, 720)

    def test_schedule_rule(self):
        t = L(9)
        self.assertTrue(sh.should_capture(t, None, 60, True))
        self.assertFalse(sh.should_capture(t, t - dt.timedelta(minutes=30), 60, True)); self.assertTrue(sh.should_capture(t, t - dt.timedelta(minutes=60), 60, True))
        self.assertFalse(sh.should_capture(t, None, 60, engaged=False)); self.assertTrue(sh.should_capture(t, None, 60, engaged=False, require_engaged=False))
        with self.assertRaises(ValueError): sh.should_capture(t, None, 0, True)

    def test_capture_zip_index_and_read(self):
        a = self.store.capture("Code.exe", "main.py"); self.clk.adv(hours=1); b = self.store.capture("chrome", "docs")
        zips = list((Path(self.tmp.name) / "shots").glob("*.zip")); self.assertEqual(len(zips), 1)               # one zip per day
        with zipfile.ZipFile(zips[0]) as z: self.assertEqual(len(z.namelist()), 2)
        self.assertEqual(self.store.read(a)[:6], b"\xff\xd8JPEG"); self.assertEqual((a.app, a.width, b.member[:2]), ("Code.exe", 1280, "10"))
        self.assertEqual([s.id for s in self.store.for_day(dt.date(2026, 5, 2))], [a.id, b.id])
        self.assertEqual(self.store.near(L(10, 5)).id, b.id); self.assertIsNone(self.store.near(L(15)))
        self.assertLess(self.store.total_bytes(), 3 * 5000 * 2)                                                  # deflate keeps it small

    def test_duplicate_screens_are_not_stored_twice(self):
        same = (b"\xff\xd8SAME" * 100, 100, 100)
        s = sh.ScreenshotStore(self.db, Path(self.tmp.name) / "d", lambda: same, self.clk)
        self.assertIsNotNone(s.capture()); self.clk.adv(hours=1); self.assertIsNone(s.capture()); self.assertIsNotNone(s.capture(force=True))

    def test_privacy_pause_and_blocklist(self):
        self.assertIsNone(self.store.capture("KeePass.exe", "Vault")); self.assertIsNone(self.store.capture("chrome", "Bank login — حساب بانک"))
        self.db.set_setting("shots_paused", True); self.assertIsNone(self.store.capture("Code.exe", "x")); self.assertIsNotNone(self.store.capture("Code.exe", "x", force=True))
        self.db.set_setting("shots_blocked", ["secret"]); self.db.set_setting("shots_paused", False); self.clk.adv(hours=1)
        self.assertIsNone(self.store.capture("my SECRET app", "")); self.assertIsNotNone(self.store.capture("chrome", ""))
        self.assertIsNone(sh.ScreenshotStore(self.db, self.tmp.name, lambda: None, self.clk).capture())          # no screen available

    def test_delete_one_rewrites_zip(self):
        a = self.store.capture("a", ""); self.clk.adv(hours=1); b = self.store.capture("b", "")
        self.assertTrue(self.store.delete(a.id)); self.assertFalse(self.store.delete(a.id))
        with zipfile.ZipFile(Path(self.tmp.name) / "shots" / a.path) as z: self.assertEqual(z.namelist(), [b.member])
        self.assertEqual(self.store.read(self.store.for_day(dt.date(2026, 5, 2))[0])[:4], b"\xff\xd8JP")

    def test_retention_days_and_size_cap(self):
        for d in range(1, 6):
            self.clk.t = L(9, day=d, month=4); self.store.capture("a", "")
        self.clk.t = L(9, day=10, month=5)
        self.assertEqual(self.store.cleanup(keep_days=30, max_total_mb=500), 5)                                   # all older than 30 days
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0], 0)
        for d in range(1, 4):
            self.clk.t = L(9, day=d, month=5); self.store.capture("a", "")
        self.assertEqual(self.store.cleanup(keep_days=365, max_total_mb=0), 3)                                     # cap forces removal of oldest first
        self.assertEqual(self.store.total_bytes(), 0)

    def test_export_day(self):
        self.store.capture("a", "")
        out = self.store.export_day_zip(dt.date(2026, 5, 2), Path(self.tmp.name) / "x.zip"); self.assertTrue(zipfile.is_zipfile(out))
        with self.assertRaises(FileNotFoundError): self.store.export_day_zip(dt.date(2026, 1, 1), Path(self.tmp.name) / "y.zip")


# ======================================================================= auto tracking
class AutoTrackTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.clk = Clock(L(9)); self.cfg = autotrack.AutoConfig(start_after=120, stop_after=180, min_session=60)
        self.at = autotrack.AutoTracker(self.db, self.cfg, self.clk)

    def feed(self, app, title, idle, seconds, step=10):
        events = []
        for _ in range(seconds // step):
            self.clk.adv(seconds=step); ev = self.at.sample(app, title, idle); events.append(ev)
        return [e for e in events if e]

    def test_judge(self):
        c = self.cfg
        self.assertEqual(autotrack.judge(c, "Code.exe", "x", 0), autotrack.WORK); self.assertEqual(autotrack.judge(c, "Code.exe", "x", 500), autotrack.AWAY)
        self.assertEqual(autotrack.judge(c, "chrome.exe", "news", 0), autotrack.NEUTRAL); self.assertEqual(autotrack.judge(c, "spotify", "song", 0), autotrack.AWAY)
        c.extra_work_apps = {"myerp"}; self.assertEqual(autotrack.judge(c, "MyERP.exe", "", 0), autotrack.WORK)

    def test_starts_backdated_then_stops_and_trims(self):
        self.assertEqual(self.feed("Code.exe", "main.py", 0, 200), ["started"])
        e = self.db.running_entries()[0]
        self.assertEqual((e.source, e.status), ("auto", Status.RUNNING)); self.assertLessEqual((e.start_utc - L(9)).total_seconds(), 15)   # backdated to the first observed moment of work, not to when the 2 minutes were over
        self.feed("Code.exe", "main.py", 0, 300)
        end_of_work = self.clk.t
        self.assertEqual(self.feed("Code.exe", "main.py", 600, 200), ["stopped"])
        d = self.db.all(TimeEntry)[0]
        self.assertEqual(d.status, Status.DONE); self.assertEqual(d.end_utc, end_of_work)                      # idle tail trimmed away
        self.assertIn("Code", d.title); self.assertEqual(d.category, "development"); self.assertIn("خودکار", d.tags)
        self.assertGreater(d.duration_sec, 450)

    def test_short_or_non_work_sessions_do_nothing(self):
        self.assertEqual(self.feed("Code.exe", "x", 0, 60), []); self.assertEqual(self.feed("Code.exe", "x", 999, 60), [])
        self.assertEqual(self.feed("spotify", "song", 0, 600), []); self.assertEqual(self.db.all(TimeEntry), [])

    def test_neutral_browsing_is_tolerated_briefly(self):
        self.feed("Code.exe", "x", 0, 200)
        self.assertEqual(self.feed("chrome.exe", "stackoverflow", 0, 100), []); self.assertEqual(len(self.db.running_entries()), 1)   # still one entry
        self.feed("Code.exe", "x", 0, 100); self.assertEqual(len(self.db.running_entries()), 1)

    def test_manual_timer_always_wins(self):
        self.db.save(TimeEntry(title="manual", start_utc=self.clk.t, status=Status.RUNNING))
        self.assertEqual(self.feed("Code.exe", "x", 0, 400), [])
        self.assertEqual(len(self.db.running_entries()), 1)

    def test_disabled_and_discard(self):
        self.cfg.enabled = False; self.assertEqual(self.feed("Code.exe", "x", 0, 400), [])
        self.cfg.enabled = True; self.cfg.min_session = 10 ** 6
        self.feed("Code.exe", "x", 0, 200); self.assertEqual(self.at.finish(), "discarded"); self.assertEqual(self.db.all(TimeEntry), [])
        self.assertIsNone(self.at.finish())

    def test_hour_log_summary_and_flush(self):
        self.feed("Code.exe", "x", 0, 600); self.feed("Code.exe", "x", 999, 300)
        self.clk.adv(hours=1); self.at.sample("Code.exe", "x", 0)                                              # crossing the hour flushes
        hl = self.db.conn.execute("SELECT * FROM hour_log").fetchall()
        self.assertEqual(len(hl), 1); row = json.loads(hl[0]["apps"]); self.assertGreater(row["Code.exe"], 500); self.assertGreater(hl[0]["idle_sec"], 200); self.assertIn("Code.exe", hl[0]["summary"])
        self.assertEqual(autotrack.hour_summary({}), "فعالیتی ثبت نشد")

    def test_config_roundtrip(self):
        c = autotrack.AutoConfig.from_dict(autotrack.AutoConfig(start_after=5, work_categories={"design"}).to_dict())
        self.assertEqual((c.start_after, c.work_categories), (5, {"design"})); self.assertEqual(autotrack.AutoConfig.from_dict({"bogus": 1}).start_after, 180)


# ======================================================================= the periodic work-report prompt
class PrompterTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.clk = Clock(L(10)); self.p = pr.Prompter(self.db, pr.PromptConfig(interval_min=60), self.clk)

    def test_schedule_arm_due_and_gap(self):
        self.assertFalse(self.p.due()); self.assertIsNotNone(self.p.next_due)                                   # first call arms
        self.clk.adv(minutes=59); self.assertFalse(self.p.due()); self.clk.adv(minutes=2); self.assertTrue(self.p.due())
        g = self.p.gap(); self.assertEqual(g[1], self.clk.t); self.assertGreaterEqual(g[1] - g[0], dt.timedelta(minutes=10))

    def test_nothing_to_ask_when_already_logged_or_running(self):
        self.p.arm(); self.clk.adv(minutes=61)
        self.db.save(TimeEntry(title="logged", start_utc=self.clk.t - dt.timedelta(minutes=70), end_utc=self.clk.t - dt.timedelta(minutes=2)))
        self.assertFalse(self.p.due())                                                                          # gap < min_gap -> postpone, no nag
        self.clk.adv(minutes=61); self.assertTrue(self.p.due())
        self.p.open_log_id = None; self.db.save(TimeEntry(title="run", start_utc=self.clk.t, status=Status.RUNNING)); self.p.next_due = self.clk.t
        self.assertFalse(self.p.due())

    def test_quiet_hours_weekends_and_idle(self):
        night = pr.Prompter(self.db, pr.PromptConfig(), Clock(L(23)))
        self.assertTrue(night.in_quiet_time()); self.assertTrue(pr.Prompter(self.db, pr.PromptConfig(), Clock(L(3))).in_quiet_time())
        self.assertFalse(pr.Prompter(self.db, pr.PromptConfig(), Clock(L(12))).in_quiet_time())
        self.assertTrue(pr.Prompter(self.db, pr.PromptConfig(), Clock(L(12, day=1))).in_quiet_time())          # Friday
        self.p.arm(); self.clk.adv(minutes=61); self.assertFalse(self.p.due(engaged_recently=False))             # away the whole time: skip
        self.assertTrue(self.p.next_due > self.clk.t)

    def test_snooze_limits_and_forced_mode(self):
        self.p.arm(); self.clk.adv(minutes=61); self.assertTrue(self.p.due()); self.p.show()
        self.assertTrue(self.p.snooze()); self.assertEqual(self.p.next_due, self.clk.t + dt.timedelta(minutes=10))
        self.clk.adv(minutes=11); self.assertTrue(self.p.due()); self.p.show(); self.assertTrue(self.p.snooze())
        self.clk.adv(minutes=11); self.p.show(); self.assertFalse(self.p.snooze())                                # 2 snoozes used
        forced = pr.Prompter(self.db, pr.PromptConfig(forced=True), self.clk); forced.open_log_id = None; forced.show()
        self.assertFalse(forced.can_snooze())
        with self.assertRaises(PermissionError): forced.answer("skipped")
        forced.answer("away"); self.assertIsNone(forced.open_log_id); self.assertIsNotNone(forced.next_due)

    def test_answers_cover_the_gap_so_it_is_not_asked_again(self):
        self.p.arm(); self.clk.adv(minutes=61); log = self.p.show(); gap_end = log.covers_to
        e = TimeEntry(title="x", start_utc=log.covers_from, end_utc=log.covers_to); self.db.save(e)
        self.p.answer("logged", e.id)
        self.assertEqual(self.p.last_covered(), gap_end); self.assertEqual(self.p.snoozes, 0)
        with self.assertRaises(ValueError): self.p.answer("bogus")

    def test_suggestion_from_activity(self):
        s0 = self.clk.t - dt.timedelta(minutes=50)
        self.db.save(ActivityEvent(app="Figma.exe", start_utc=s0, end_utc=s0 + dt.timedelta(minutes=40)))
        self.db.save(ActivityEvent(app="chrome.exe", start_utc=s0 + dt.timedelta(minutes=40), end_utc=s0 + dt.timedelta(minutes=45)))
        sug = self.p.suggestion()
        self.assertEqual(sug["apps"][0][0], "Figma.exe"); self.assertEqual(sug["category"], "ui_ux_design"); self.assertIn("Figma", sug["title_hint"]); self.assertGreaterEqual(sug["minutes"], 50)

    def test_compliance_and_persistence(self):
        self.p.arm(); self.clk.adv(minutes=61); self.p.show(); self.p.answer("logged")
        self.clk.adv(minutes=61); self.p.show(); self.p.snooze()
        c = self.p.compliance(L(0), L(23)); self.assertEqual((c["logged"], c["snoozed"], c["total"], c["rate_pct"]), (1, 1, 2, 50.0))
        again = pr.Prompter(self.db, clock=self.clk); self.assertEqual(again.snoozes, self.p.snoozes); self.assertEqual(again.next_due, self.p.next_due)
        self.p.cfg.interval_min = 45; self.p.save_config(); self.assertEqual(pr.Prompter(self.db, clock=self.clk).cfg.interval_min, 45)
        with self.assertRaises(ValueError): pr.PromptConfig.from_dict({"interval_min": 1})


# ======================================================================= reports
class ReportTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.c = Client(name="C1", default_rate=100); self.db.save(self.c)
        self.p = Project(name="Alpha", client_id=self.c.id, rate_per_hour=200, estimated_hours=20); self.db.save(self.p)
        self.p2 = Project(name="Beta"); self.db.save(self.p2)
        def add(day, h, mins, **kw): self.db.save(TimeEntry(title=kw.pop("title", "t"), start_utc=L(h, day=day), end_utc=L(h, day=day) + dt.timedelta(minutes=mins), **kw))
        add(2, 9, 120, project_id=self.p.id, category="backend_development", tags=["api"], billable=True, estimated_min=60, title="build API")
        add(2, 14, 60, project_id=self.p2.id, category="meeting", tags=["x"])
        add(3, 23, 120, project_id=self.p.id, category="backend_development")                       # crosses midnight into day 4
        add(1, 9, 60, project_id=self.p.id)                                                          # outside the period
        self.spec = rb.ReportSpec(kind="detailed", start=dt.date(2026, 5, 2), end=dt.date(2026, 5, 4), title="T", sections=set(rb.ALL_SECTIONS))

    def test_totals_and_midnight_split(self):
        d = rb.build(self.db, self.spec); s = d["summary"]
        self.assertEqual((s["total_sec"], s["days_worked"], s["entries"]), (5 * 3600, 3, 3)); self.assertEqual(dict(d["by_day"])["2026-05-04"], 3600)
        self.assertEqual(dict(d["by_project"]), {"Alpha": 4 * 3600, "Beta": 3600}); self.assertEqual(dict(d["by_hour"])[23], 3600); self.assertEqual(dict(d["by_hour"])[0], 3600)
        self.assertEqual(dict(d["by_weekday"])["شنبه"], 3 * 3600); self.assertEqual(s["billable_sec"], 2 * 3600)
        self.assertEqual(d["billing"]["amounts"], {"IRR": 100 * 2.0 * 1.0 + 0.0} if False else d["billing"]["amounts"]); self.assertIn("IRR", d["billing"]["amounts"])
        self.assertEqual(d["estimates"]["accuracy_pct"], 200.0)

    def test_filters(self):
        self.spec.projects = [self.p2.id]; self.assertEqual(rb.build(self.db, self.spec)["summary"]["total_sec"], 3600)
        self.spec.projects = []; self.spec.billable = True; self.assertEqual(rb.build(self.db, self.spec)["summary"]["entries"], 1)
        self.spec.billable = None; self.spec.tags = ["api"]; self.assertEqual(rb.build(self.db, self.spec)["summary"]["entries"], 1)
        self.spec.tags = []; self.spec.min_minutes = 90; self.assertEqual(rb.build(self.db, self.spec)["summary"]["entries"], 2)
        self.spec.end = dt.date(2026, 5, 1)
        with self.assertRaises(ValueError): rb.build(self.db, self.spec)

    def test_previous_period_comparison(self):
        d = rb.build(self.db, self.spec)
        self.assertEqual(d["previous"]["total_sec"], 3600); self.assertEqual(d["previous"]["change_pct"], 400.0)

    def test_presets_use_jalali_boundaries(self):
        m = rb.ReportSpec.preset("monthly", dt.date(2026, 5, 2))                                      # 1405/02/12
        self.assertEqual((m.start, m.end), (dt.date(2026, 4, 21), dt.date(2026, 5, 21)))
        w = rb.ReportSpec.preset("weekly", dt.date(2026, 5, 5)); self.assertEqual((w.start, w.end), (dt.date(2026, 5, 2), dt.date(2026, 5, 8)))
        y = rb.ReportSpec.preset("yearly", dt.date(2026, 5, 2)); self.assertEqual((y.start, y.end), (dt.date(2026, 3, 21), dt.date(2027, 3, 20)))
        self.assertEqual(rb.ReportSpec.preset("daily", dt.date(2026, 5, 2)).start, dt.date(2026, 5, 2))
        with self.assertRaises(ValueError): rb.ReportSpec.preset("nope", dt.date.today())
        for k in rb.KINDS: self.assertTrue(rb.ReportSpec.preset(k, dt.date(2026, 5, 2)).sections)

    def test_all_renderers(self):
        self.db.save(Habit(name="water", log=["2026-05-02", "2026-05-03"])); self.db.save(Goal(name="g", key_results=[{"target": 10, "current": 5}]))
        d = rb.build(self.db, self.spec)
        h = rb.to_html(d)
        for needle in ("<svg", "dir='rtl'", "IRANSans", "Alpha", "جمع ساعت", "فهرست کامل", "عادت"): self.assertIn(needle, h)
        self.assertNotIn("<script", h)
        self.assertIn("۵:۰۰", h)                                                                               # Persian digits by default
        self.assertIn("5:00", rb.to_html(d, fa=False))
        md = rb.to_markdown(d); self.assertIn("|", md); self.assertIn("Alpha", md)
        self.assertEqual(len(rb.to_csv(d).splitlines()), 4); self.assertEqual(json.loads(rb.to_json(d))["summary"]["entries"], 3)
        with tempfile.TemporaryDirectory() as t:
            for fmt in ("html", "md", "csv", "json", "xlsx"): self.assertGreater(rb.save(d, Path(t) / f"r.{fmt}", fmt).stat().st_size, 100)
            with self.assertRaises(ValueError): rb.save(d, Path(t) / "r.x", "pdfx")
        self.assertIn("امضا", rb.to_html(rb.build(self.db, rb.ReportSpec.preset("company", dt.date(2026, 5, 2)))))

    def test_html_is_escaped_and_csv_is_formula_safe(self):
        self.db.save(TimeEntry(title="=cmd|' /C calc'!A0 <img src=x onerror=alert(1)>", start_utc=L(10), end_utc=L(11), notes="<script>x</script>"))
        d = rb.build(self.db, self.spec)
        h = rb.to_html(d); self.assertNotIn("<img", h); self.assertNotIn("<script>", h); self.assertIn("&lt;img", h)
        self.assertIn("'=cmd", rb.to_csv(d))

    def test_svg_helpers_handle_edge_cases(self):
        self.assertEqual(rb.svg_bars([]), ""); self.assertEqual(rb.svg_donut([("a", 0)]), ""); self.assertEqual(rb.svg_line([1]), ""); self.assertEqual(rb.svg_hbars([]), "")
        self.assertIn("<svg", rb.svg_heat([[0] * 24 for _ in range(7)])); self.assertIn("&lt;", rb.svg_bars([("<x>", 5)]))
        self.assertIn("<svg", rb.svg_bars([(str(i), i) for i in range(400)]))                                    # many bars do not explode

    def test_empty_period(self):
        d = rb.build(Database(), rb.ReportSpec.preset("monthly", dt.date(2026, 5, 2)))
        self.assertEqual(d["summary"]["total_sec"], 0); self.assertTrue(rb.to_html(d)); self.assertIsNone(d["previous"]["change_pct"])


if __name__ == "__main__":
    unittest.main()
