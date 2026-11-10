import datetime as dt
import json
import sqlite3
import tempfile
import unittest
import urllib.error
import urllib.request
import wave
from pathlib import Path

from worktracker.core import database as dbmod
from worktracker.core.database import Database
from worktracker.core.models import Member, Project, Status, Template, TimeEntry
from worktracker.core.persian import TEHRAN, UTC, now_utc
from worktracker.integrations import caldav, chat, http_api
from worktracker.integrations.google_calendar import GoogleCalendarPlugin, build_service
from worktracker.services import activity, extras, folder_sync, insights, quick, recurrence, sound
from worktracker.services.hotkey import parse_hotkey
from worktracker.services.reminders import Reminders
from worktracker.services.team import Team
from worktracker.services.tracker import Tracker, TrackerSettings


def T(h, m=0, day=1):
    return dt.datetime(2026, 5, day, h, m, tzinfo=UTC)


def L(h, m=0, day=1):   # Tehran local -> UTC
    return dt.datetime(2026, 5, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class Clock:
    def __init__(self, t=None):
        self.t = t or dt.datetime(2026, 5, 2, 9, tzinfo=UTC)
    def __call__(self):
        return self.t
    def adv(self, **kw):
        self.t += dt.timedelta(**kw)


class DbRound3(unittest.TestCase):
    def test_history_and_time_travel(self):
        db = Database()
        e = TimeEntry(title="v1", start_utc=T(8), end_utc=T(9)); db.save(e)
        mid = now_utc(); import time; time.sleep(0.01)
        e.title = "v2"; db.save(e)
        gone = TimeEntry(title="gone", start_utc=T(10), end_utc=T(11)); db.save(gone)
        before_delete = now_utc(); time.sleep(0.01)
        db.delete(TimeEntry, gone.id)
        h = db.history(TimeEntry, e.id)
        self.assertEqual([x["action"] for x in h], ["create", "update"])
        self.assertEqual([x["row"]["title"] for x in h], ["v1", "v2"])
        self.assertEqual([x.title for x in db.entries_as_of(mid)], ["v1"])
        self.assertEqual(sorted(x.title for x in db.entries_as_of(before_delete)), ["gone", "v2"])
        self.assertEqual([x.title for x in db.entries_as_of(now_utc())], ["v2"])
        self.assertEqual(db.prune_audit(365), 0)
        self.assertGreater(db.prune_audit(0), 0); self.assertEqual(db.history(TimeEntry, e.id), [])

    def test_touch_false_keeps_updated_at(self):
        db = Database(); e = TimeEntry(title="x", start_utc=T(8)); stamp = e.updated_at - dt.timedelta(days=5); e.updated_at = stamp
        db.save(e, touch=False)
        self.assertEqual(db.get(TimeEntry, e.id).updated_at, stamp)

    def test_upgrade_from_v2_preserves_data(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "old.db"
            c = sqlite3.connect(path)
            for m in dbmod.MIGRATIONS[:2]:
                c.executescript(m)
            c.execute("PRAGMA user_version=2")
            c.execute("INSERT INTO projects (id,name,created_at,updated_at) VALUES ('p','Old','2026-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00')")
            c.commit(); c.close()
            db = Database(path)
            self.assertEqual(db.version, 5)
            self.assertEqual(db.get(Project, "p").name, "Old")
            self.assertTrue(db.integrity_ok()); db.close()

    def test_multi_timer(self):
        db, clk = Database(), Clock()
        tr = Tracker(db, TrackerSettings(), clk)
        a = tr.start("meeting"); b = tr.start("docs", exclusive=False)
        self.assertEqual(len(tr.running()), 2)
        clk.adv(minutes=30)
        self.assertEqual(tr.stop(entry_id=a.id).duration_sec, 1800)
        self.assertEqual([r.id for r in tr.running()], [b.id])
        self.assertIsNone(tr.stop(entry_id=a.id))        # already stopped
        tr.start("third")                                  # exclusive stops the rest
        self.assertEqual(len(tr.running()), 1)


class TeamTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.t = Team(self.db)
        self.a, self.b = self.t.add_member("ali"), self.t.add_member("sara")
        self.e = TimeEntry(title="task", start_utc=T(8), end_utc=T(10)); self.db.save(self.e)

    def test_members_validation(self):
        with self.assertRaises(ValueError): self.t.add_member("two words")
        with self.assertRaises(ValueError): self.t.add_member("ALI")
        with self.assertRaises(ValueError): self.t.add_member("  ")

    def test_assign_and_workload(self):
        self.t.assign(self.e.id, self.a.id)
        self.assertEqual([x.id for x in self.t.tasks_of(self.a.id)], [self.e.id])
        self.assertEqual(self.t.workload_hours(), {"ali": 2.0})
        self.t.assign(self.e.id, None); self.assertEqual(self.t.tasks_of(self.a.id), [])
        with self.assertRaises(KeyError): self.t.assign(self.e.id, "nobody")

    def test_threads_and_mentions(self):
        c1 = self.t.comment(self.e.id, self.a.id, "hey @sara please review @ali @ghost")
        c2 = self.t.comment(self.e.id, self.b.id, "on it", parent_id=c1.id)
        self.t.comment(self.e.id, self.a.id, "thanks", parent_id=c2.id)
        self.t.comment(self.e.id, self.b.id, "another top-level")
        self.assertEqual([(x["comment"].text[:5], x["depth"]) for x in self.t.thread(self.e.id)],
                         [("hey @", 0), ("on it", 1), ("thank", 2), ("anoth", 0)])
        self.assertEqual(c1.mentions, sorted([self.a.id, self.b.id]))
        self.assertEqual(len(self.t.unread(self.b.id)), 1)       # sara notified
        self.assertEqual(len(self.t.unread(self.a.id)), 0)       # no self-notification
        self.assertEqual(self.t.mark_read(self.b.id), 1); self.assertEqual(self.t.unread(self.b.id), [])

    def test_comment_validation(self):
        with self.assertRaises(ValueError): self.t.comment(self.e.id, self.a.id, "  ")
        with self.assertRaises(KeyError): self.t.comment("nope", self.a.id, "x")
        other = TimeEntry(title="o", start_utc=T(8)); self.db.save(other)
        c = self.t.comment(other.id, self.a.id, "x")
        with self.assertRaises(ValueError): self.t.comment(self.e.id, self.a.id, "y", parent_id=c.id)

    def test_cascade_delete_comments(self):
        self.t.comment(self.e.id, self.a.id, "x"); self.db.delete(TimeEntry, self.e.id)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0], 0)


class ExtrasTests(unittest.TestCase):
    def test_template_batch_filters(self):
        db = Database()
        t = Template(name="Standup", title="Daily standup", category="meeting", tags=["team"], estimated_min=15); db.save(t)
        e = extras.from_template(db, t.id)
        self.assertEqual((e.title, e.status, e.estimated_min, e.tags), ("Daily standup", Status.PLANNED, 15, ["team"]))
        with self.assertRaises(KeyError): extras.from_template(db, "x")
        ids = [TimeEntry(title=f"t{i}", start_utc=T(8 + i), end_utc=T(9 + i)) for i in range(3)]
        for x in ids: db.save(x)
        self.assertEqual(extras.batch_update(db, [x.id for x in ids] + ["missing"], add_tags=["a"], category="dev", billable=True), 3)
        self.assertTrue(all(db.get(TimeEntry, x.id).tags == ["a"] and db.get(TimeEntry, x.id).billable for x in ids))
        f = extras.save_filter(db, "billable dev", "billable:yes category:dev")
        self.assertEqual(len(extras.run_filter(db, f.id)), 3)
        with self.assertRaises(ValueError): extras.save_filter(db, " ", "x")
        self.assertEqual(extras.batch_delete(db, [ids[0].id, "zzz"]), 1)

    def test_custom_fields(self):
        db = Database(); e = TimeEntry(title="x", start_utc=T(8), end_utc=T(10), extra={"rate": 50}); db.save(e)
        extras.define_field(db, "complexity", "number"); extras.define_field(db, "kind", "select", ["a", "b"]); extras.define_field(db, "due", "date")
        with self.assertRaises(ValueError): extras.define_field(db, "kind", "text")
        with self.assertRaises(ValueError): extras.define_field(db, "z", "weird")
        extras.set_field(db, e.id, "complexity", "3")
        with self.assertRaises(ValueError): extras.set_field(db, e.id, "kind", "c")
        with self.assertRaises(ValueError): extras.set_field(db, e.id, "due", "not-a-date")
        with self.assertRaises(KeyError): extras.set_field(db, e.id, "ghost", 1)
        self.assertEqual(db.get(TimeEntry, e.id).extra["fields"], {"complexity": 3.0})
        self.assertEqual(extras.entry_formula(db, e.id, "hours * rate * complexity"), 2 * 50 * 3)

    def test_formula_safety(self):
        f = extras.evaluate_formula
        self.assertEqual(f("2 + 3 * 4", {}), 14); self.assertEqual(f("-x + max(1, 2)", {"x": 5}), -3); self.assertEqual(f("round(10/4)", {}), 2)
        for bad in ["__import__('os').system('x')", "x.__class__", "2**100", "1/0", "unknown + 1", "[1]", "(1,2)", "lambda: 1", "'a'*3", "True+1", "1+", "a" * 300]:
            with self.assertRaises(ValueError, msg=bad): f(bad, {"x": 1})

    def test_quick_capture(self):
        c = quick.parse("fix login #bug #urgent @WebApp 1h30m")
        self.assertEqual((c.title, c.tags, c.project, c.minutes), ("fix login", ["bug", "urgent"], "WebApp", 90))
        self.assertEqual(quick.parse("write 45m report").minutes, 45)
        self.assertEqual(quick.parse("plan 1.5h").minutes, 90)
        self.assertEqual(quick.parse("sync 1h30 x").minutes, 90); self.assertEqual(quick.parse("a 2h 15m b").minutes, 135)
        self.assertEqual(quick.parse("buy 3 apples").title, "buy 3 apples")
        self.assertEqual(quick.parse("call 3rd team").title, "call 3rd team")      # not a duration
        with self.assertRaises(ValueError): quick.parse("#only 5m")

    def test_recurrence(self):
        s = dt.datetime(2026, 1, 31, 9, tzinfo=UTC)
        m = recurrence.occurrences(s, "monthly", dt.datetime(2026, 4, 30, 23, tzinfo=UTC))
        self.assertEqual([(x.month, x.day) for x in m], [(2, 28), (3, 31), (4, 30)])
        self.assertEqual(len(recurrence.occurrences(s, "weekly", s + dt.timedelta(days=22))), 3)
        self.assertEqual(len(recurrence.occurrences(s, "every:3", s + dt.timedelta(days=10))), 3)
        for bad in ("hourly", "every:0"):
            with self.assertRaises(ValueError): recurrence.occurrences(s, bad, s)
        db = Database(); e = TimeEntry(title="r", start_utc=T(9), end_utc=T(10), status=Status.PLANNED); db.save(e)
        made = recurrence.expand(db, e.id, "daily", T(9, day=4))
        self.assertEqual(len(made), 3); self.assertEqual(made[0].end_utc - made[0].start_utc, dt.timedelta(hours=1))
        self.assertEqual(recurrence.expand(db, e.id, "daily", T(9, day=4)), [])         # idempotent
        self.assertEqual(len(recurrence.expand(db, e.id, "daily", T(9, day=5))), 1)


class SyncAndMiscTests(unittest.TestCase):
    def test_reminders(self):
        db, clk = Database(), Clock(); r = Reminders(db, clk)
        self.assertEqual(r.due(True), [])                    # first call arms the counters
        clk.adv(minutes=21); self.assertEqual(r.due(True), ["eyes"])
        self.assertEqual(r.due(True), [])                    # not again immediately
        clk.adv(minutes=30); self.assertEqual(set(r.due(True, focus_mode=True)), set())
        self.assertEqual(set(r.due(True)), {"eyes", "posture"})
        clk.adv(hours=5); self.assertEqual(r.due(False), [])
        r.set_interval("water", 5); self.assertEqual(r.intervals()["water"], 5)
        with self.assertRaises(ValueError): r.set_interval("nap", 5)
        with self.assertRaises(ValueError): r.set_interval("eyes", 0)

    def test_folder_sync(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Database(), Database()
            e = TimeEntry(title="from A", start_utc=T(8), end_utc=T(9)); a.save(e)
            self.assertEqual(folder_sync.sync(a, d, "A").pulled, 0)
            rep = folder_sync.sync(b, d, "B"); self.assertEqual(rep.pulled, 1)
            self.assertEqual(b.get(TimeEntry, e.id).title, "from A")
            self.assertEqual(b.get(TimeEntry, e.id).updated_at, a.get(TimeEntry, e.id).updated_at)
            be = b.get(TimeEntry, e.id); be.title = "edited on B"; b.save(be); folder_sync.push(b, d, "B")
            self.assertEqual(folder_sync.sync(a, d, "A").pulled, 1)
            self.assertEqual(a.get(TimeEntry, e.id).title, "edited on B")
            ae = a.get(TimeEntry, e.id); ae.title = "newer on A"; a.save(ae)
            rep = folder_sync.pull(a, d, "A"); self.assertEqual(rep.pulled, 0)       # stale remote does not overwrite
            (Path(d) / "worktracker-C.json").write_text("{broken", encoding="utf-8")
            self.assertEqual(len(folder_sync.pull(a, d, "A").conflicts), 1)
            self.assertFalse(list(Path(d).glob(".*.tmp")))

    def test_sound(self):
        for k in sound.KINDS:
            s = sound.generate_samples(k, 0.5, 8000)
            self.assertEqual(len(s), 4000); self.assertTrue(all(-32768 <= x <= 32767 for x in s)); self.assertGreater(max(map(abs, s)), 100)
        self.assertEqual(sound.generate_samples("pink", 0.2, 8000), sound.generate_samples("pink", 0.2, 8000))   # deterministic
        with self.assertRaises(ValueError): sound.generate_samples("thunder")
        with tempfile.TemporaryDirectory() as d:
            p = sound.write_wav("rain", Path(d) / "r.wav", 0.5, 8000)
            with wave.open(str(p)) as w: self.assertEqual((w.getnchannels(), w.getframerate(), w.getnframes()), (1, 8000, 4000))

    def test_hotkey_parse(self):
        self.assertEqual(parse_hotkey("Ctrl+Shift+Space"), (0x2 | 0x4, 0x20))
        self.assertEqual(parse_hotkey("alt+f9"), (0x1, 0x6F + 9)); self.assertEqual(parse_hotkey("Win+k"), (0x8, ord("K")))
        for bad in ("space", "Ctrl+", "Hyper+x", "Ctrl+f99", "Ctrl+??"):
            with self.assertRaises(ValueError, msg=bad): parse_hotkey(bad)

    def test_languages(self):
        from worktracker.ui import strings
        from worktracker.ui.strings_en import EN
        self.assertEqual(set(strings.S), set(EN))
        fa = strings.S["start"]
        strings.set_language("en"); self.assertEqual(strings.S["start"], "Start")
        strings.set_language("fa"); self.assertEqual(strings.S["start"], fa)
        with self.assertRaises(ValueError): strings.set_language("xx")


class InsightTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.p = Project(name="P"); self.db.save(self.p)

    def add(self, start, minutes, **kw):
        e = TimeEntry(title="t", start_utc=start, end_utc=start + dt.timedelta(minutes=minutes), **kw); self.db.save(e); return e

    def test_moving_average(self):
        self.assertEqual(insights.moving_average([2, 4, 6, 8], 2), [2.0, 3.0, 5.0, 7.0])
        self.assertEqual(insights.moving_average([], 3), [])
        with self.assertRaises(ValueError): insights.moving_average([1], 0)

    def test_comparisons(self):
        sat = dt.date(2026, 5, 2)           # Saturday
        self.add(L(9, day=2), 120); self.add(L(9, day=3), 60); self.add(L(9, day=25 - 18 + 0), 60) if False else None
        self.add(dt.datetime(2026, 4, 25, 9, tzinfo=TEHRAN).astimezone(UTC), 60)   # previous Saturday
        r = insights.week_over_week(self.db, dt.date(2026, 5, 3))
        self.assertEqual((r["a_hours"], r["b_hours"], r["change_pct"]), (3.0, 1.0, 200.0))
        self.assertEqual(insights.compare_periods(self.db, (dt.date(2030, 1, 1), dt.date(2030, 1, 2)), (dt.date(2031, 1, 1), dt.date(2031, 1, 2)))["change_pct"], 0.0)

    def test_year_over_year(self):
        self.add(L(9, day=2), 120)
        r = insights.year_over_year(self.db, 1405)
        self.assertEqual((r["a_hours"], r["b_hours"]), (2.0, 0.0))

    def test_flow_and_switches(self):
        es = [self.add(T(8), 40, category="a"), self.add(T(8, 43), 30, category="a"), self.add(T(11), 20, category="b"),
              self.add(T(11, 25), 50, category="b", project_id=self.p.id)]
        flows = insights.flow_sessions(es)
        self.assertEqual([f[1] - f[0] for f in flows], [dt.timedelta(minutes=75), dt.timedelta(minutes=73)])   # longest first
        self.assertEqual(len(insights.flow_sessions(es, max_gap_min=1, min_minutes=10)), 4)
        self.assertEqual(len(insights.flow_sessions(es, max_gap_min=1)), 1)                                      # only the 50-min block
        self.assertEqual(insights.context_switches(es), 1)          # only the last pair is adjacent with a changed project
        self.assertEqual(insights.context_switches([]), 0); self.assertEqual(insights.switch_cost_minutes(4), 30)

    def test_early_start_effect(self):
        self.add(L(7, day=2), 480); self.add(L(7, day=3), 420); self.add(L(11, day=4), 120)
        r = insights.early_start_effect(self.db, dt.date(2026, 5, 1), dt.date(2026, 5, 10))
        self.assertEqual((r["early_avg"], r["late_avg"], r["difference_pct"]), (7.5, 2.0, 275.0))
        self.assertIsNone(insights.early_start_effect(Database(), dt.date(2026, 5, 1), dt.date(2026, 5, 2)))

    def test_sankey_and_year_review_and_weekly(self):
        self.add(L(9, day=2), 120, project_id=self.p.id, category="dev"); self.add(L(9, day=3), 60, category="ops")
        sk = insights.sankey(self.db, 1405)
        self.assertEqual(sorted(sk["nodes"]), ["P", "dev", "ops", "—"])
        self.assertEqual(sk["links"][0], {"source": "P", "target": "dev", "hours": 2.0})
        yr = insights.year_in_review(self.db, 1405)
        self.assertEqual((yr["total_hours"], yr["top_project"], yr["top_category"], yr["days_worked"]), (3.0, "P", "dev", 2))
        self.assertEqual(insights.year_in_review(Database(), 1405), {"year": 1405, "empty": True})
        self.assertIn("ساعت", insights.weekly_review(self.db, dt.date(2026, 5, 3)))
        self.assertIn("ثبت نشده", insights.weekly_review(Database(), dt.date(2026, 5, 3)))


class ActivityTests(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(activity.classify("Code.exe", "main.py"), "development"); self.assertEqual(activity.classify("zoom.exe"), "communication")
        self.assertEqual(activity.classify("weird"), "other")

    def test_recorder_merges_and_idle(self):
        db, clk = Database(), Clock(); cur = {"w": ("Code.exe", "a.py")}; idle = {"s": 0}
        rec = activity.ActivityRecorder(db, lambda: cur["w"], clk, lambda: idle["s"], idle_limit=120)
        for _ in range(4): rec.sample(); clk.adv(seconds=10)
        cur["w"] = ("chrome.exe", "docs"); rec.sample(); clk.adv(seconds=30); rec.sample()
        idle["s"] = 500; self.assertIsNone(rec.sample())               # idle: flushes, records nothing
        idle["s"] = 0; cur["w"] = None; self.assertIsNone(rec.sample())    # no window
        rows = db.conn.execute("SELECT app, category FROM activity_events ORDER BY start_utc").fetchall()
        self.assertEqual([tuple(r) for r in rows], [("Code.exe", "development"), ("chrome.exe", "browsing")])
        usage = activity.app_usage(db, T(0), T(23, day=30))
        self.assertEqual(dict(usage), {"Code.exe": 30, "chrome.exe": 30})
        self.assertEqual(sum(activity.category_usage(db, clk.t - dt.timedelta(days=1), clk.t + dt.timedelta(days=1)).values()), sum(s for _, s in usage))
        sug = activity.suggest_task(db, clk.t - dt.timedelta(days=1))
        self.assertIn(sug["app"], ("Code.exe", "chrome.exe"))
        self.assertIsNone(activity.suggest_task(Database(), T(0)))

    def test_foreground_window_never_raises(self):
        r = activity.foreground_window()
        self.assertTrue(r is None or (isinstance(r, tuple) and len(r) == 2))


class FakeGoogle:
    def __init__(self, items=None, fail=False):
        self.store, self.items, self.fail, self.n = {}, items or [], fail, 0
    def events(self): return self
    def _ex(self, fn):
        class R:
            def execute(s): return fn()
        return R()
    def insert(self, calendarId, body):
        if self.fail: raise RuntimeError("quota")
        self.n += 1; eid = f"ev{self.n}"; self.store[eid] = body; return self._ex(lambda: {"id": eid})
    def update(self, calendarId, eventId, body): self.store[eventId] = body; return self._ex(lambda: {})
    def delete(self, calendarId, eventId): self.store.pop(eventId); return self._ex(lambda: {})
    def list(self, **kw): return self._ex(lambda: {"items": self.items})


class IntegrationRound3(unittest.TestCase):
    def test_google_optional(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(build_service(d))                          # no credentials.json -> None, no exception
        p = GoogleCalendarPlugin(Database(), None)
        self.assertFalse(p.available)
        self.assertEqual((p.push().pushed, p.pull(T(0), T(23)).pulled), (0, 0))
        self.assertFalse(p.delete_remote("x"))

    def test_google_push_pull(self):
        db, svc = Database(), FakeGoogle(items=[
            {"id": "g1", "summary": "Remote meeting", "start": {"dateTime": "2026-05-01T09:00:00Z"}, "end": {"dateTime": "2026-05-01T10:00:00Z"}},
            {"id": "g2", "summary": "All day", "start": {"date": "2026-05-01"}, "end": {"date": "2026-05-02"}},
            {"id": "g3", "summary": "ours", "start": {"dateTime": "2026-05-01T09:00:00Z"}, "end": {"dateTime": "2026-05-01T10:00:00Z"},
             "extendedProperties": {"private": {"wt_id": "x"}}}])
        pl = GoogleCalendarPlugin(db, svc)
        local = TimeEntry(title="local", start_utc=T(8), end_utc=T(9)); db.save(local)
        running = TimeEntry(title="run", start_utc=T(8), status=Status.RUNNING); db.save(running)
        self.assertEqual(pl.pull(T(0), T(23)).pulled, 1)                 # only g1
        self.assertEqual(pl.pull(T(0), T(23)).pulled, 0)                 # idempotent
        self.assertEqual(pl.push().pushed, 1)                            # local only (not running, not google-sourced)
        self.assertEqual(db.get(TimeEntry, local.id).extra["calendar_event_id"], "ev1")
        local = db.get(TimeEntry, local.id); local.title = "renamed"; db.save(local)
        self.assertEqual(pl.push([local.id]).pushed, 1); self.assertEqual(svc.store["ev1"]["summary"], "renamed"); self.assertEqual(svc.n, 1)
        self.assertTrue(pl.delete_remote(local.id)); self.assertNotIn("ev1", svc.store)

    def test_google_failure_is_contained(self):
        db = Database(); db.save(TimeEntry(title="x", start_utc=T(8), end_utc=T(9)))
        r = GoogleCalendarPlugin(db, FakeGoogle(fail=True)).push()
        self.assertEqual((r.pushed, len(r.errors)), (0, 1))

    def test_caldav(self):
        seen = []
        class R:
            status = 201
            def __enter__(s): return s
            def __exit__(s, *a): return False
        def opener(req, timeout): seen.append((req.get_method(), req.full_url, req.get_header("Authorization"))); return R()
        e = TimeEntry(title="x", start_utc=T(8), end_utc=T(9))
        self.assertTrue(caldav.put_event("https://cal.example/dav/", "u", "p", e, opener))
        self.assertTrue(caldav.delete_event("https://cal.example/dav", "u", "p", e, opener))
        self.assertEqual(seen[0][:2], ("PUT", f"https://cal.example/dav/{e.id}.ics")); self.assertTrue(seen[0][2].startswith("Basic "))
        self.assertFalse(caldav.put_event("ftp://x", "u", "p", e, opener)); self.assertFalse(caldav.put_event("https://x", "u", "p", TimeEntry(title="r", start_utc=T(8)), opener))
        def boom(req, timeout): raise OSError("offline")
        self.assertFalse(caldav.put_event("https://x.y", "u", "p", e, boom))

    def test_telegram_commands(self):
        db, clk = Database(), Clock(); up = lambda text, chat_id=1: {"message": {"chat": {"id": chat_id}, "text": text}}
        h = lambda text, cid=1: chat.handle_update(db, up(text, cid), [1], clk)
        self.assertEqual(h("/start deploy #ops"), "▶ deploy"); clk.adv(minutes=20)
        self.assertIn("running: deploy", h("/status")); self.assertIn("■ deploy 0:20", h("/stop"))
        self.assertEqual(h("/log 1h30 write docs"), "✓ write docs 90 min")
        self.assertEqual([e.duration_sec for e in db.all(TimeEntry) if e.title == "write docs"], [5400])
        self.assertIn("usage", h("/log write docs")); self.assertTrue(h("/start").startswith("commands")); self.assertEqual(h("/status"), "idle")
        self.assertEqual(h("/start hacked", cid=999), "")                # stranger ignored
        self.assertEqual(len(db.all(TimeEntry)), 2)
        self.assertEqual(chat.handle_update(db, {}, [1]), "")

    def test_telegram_slack_send(self):
        calls = []
        class R:
            status = 200
            def __enter__(s): return s
            def __exit__(s, *a): return False
        op = lambda req, timeout: (calls.append(req.full_url), R())[1]
        tok = "123456:" + "A" * 30
        self.assertTrue(chat.telegram_send(tok, 1, "hi", op)); self.assertIn("api.telegram.org/bot" + tok, calls[0])
        self.assertFalse(chat.telegram_send("bad token", 1, "hi", op)); self.assertTrue(chat.slack_send("https://hooks.slack.test/x", "hi", op))
        self.assertIn("1:00", chat.daily_digest(Database(), [TimeEntry(title="x", start_utc=T(8), end_utc=T(9))]))

    def test_http_api(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "api.db"; Database(path).close()
            with self.assertRaises(ValueError): http_api.start_server(path, "short")
            with self.assertRaises(ValueError): http_api.start_server(":memory:", "x" * 20)
            tok = "t" * 24; srv, th = http_api.start_server(path, tok, port=0); base = f"http://127.0.0.1:{srv.server_address[1]}"
            def call(method, p, body=None, token=tok):
                req = urllib.request.Request(base + p, data=json.dumps(body).encode() if body is not None else None, method=method)
                if token: req.add_header("Authorization", "Bearer " + token)
                try:
                    with urllib.request.urlopen(req, timeout=5) as r: return r.status, json.loads(r.read())
                except urllib.error.HTTPError as e: return e.code, json.loads(e.read())
            try:
                self.assertEqual(call("GET", "/v1/status", token=None)[0], 401); self.assertEqual(call("GET", "/v1/status", token="wrong" * 5)[0], 401)
                self.assertEqual(call("GET", "/v1/status")[1]["running"], False)
                self.assertEqual(call("POST", "/v1/timer/start", {"title": ""})[0], 400)
                self.assertEqual(call("POST", "/v1/timer/start", {"title": "ide work"})[0], 200)
                self.assertEqual(call("GET", "/v1/status")[1]["title"], "ide work")
                self.assertEqual(call("POST", "/v1/timer/stop")[0], 200)
                self.assertEqual(call("GET", "/v1/entries?limit=5")[0], 200); self.assertEqual(call("GET", "/v1/nope")[0], 404)
                self.assertEqual(srv.server_address[0], "127.0.0.1")
            finally:
                srv.shutdown(); srv.server_close()


if __name__ == "__main__":
    unittest.main()
