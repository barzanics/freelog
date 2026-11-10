import datetime as dt
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from worktracker.core import recovery
from worktracker.core.database import Database
from worktracker.core.models import Client, Goal, Invoice, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC, now_utc
from worktracker.integrations import chat
from worktracker.services import bulk, recurring, reports, smart2
from worktracker.services.tracker import Tracker, TrackerSettings

ROOT = str(Path(__file__).resolve().parents[2])


def L(h, m=0, day=2, month=5):
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.c = Client(name="C", default_rate=100); self.db.save(self.c)
        self.p = Project(name="Alpha|X", client_id=self.c.id, rate_per_hour=50); self.db.save(self.p)
        self.db.save(TimeEntry(title="a|b", start_utc=L(9), end_utc=L(11), project_id=self.p.id))

    def test_markdown_and_html_escape(self):
        md = reports.year_markdown(self.db, 1405)
        self.assertIn("۲", md); self.assertIn("پروژه", md)
        h = reports.to_html("# <script>x</script>\n- **bold** item\n| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertNotIn("<script>", h); self.assertIn("<b>bold</b>", h); self.assertIn("<table>", h); self.assertIn("<th>a</th>", h); self.assertIn("dir='rtl'", h)
        mm = reports.month_markdown(self.db, 1405, 2)
        self.assertIn("a/b", mm)                                           # pipe in a title can't break the table
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(reports.save(md, Path(d) / "r.md").read_text(encoding="utf-8").startswith("# گزارش"))

    def test_client_report(self):
        inv = Invoice(client_id=self.c.id, items=[{"hours": 2, "rate": 50}], paid=40); self.db.save(inv)
        r = reports.client_report(self.db, self.c.id)
        self.assertEqual((r["total_hours"], r["billed"], r["paid"], r["outstanding"], r["invoices"]), (2.0, 100.0, 40.0, 60.0, 1))
        self.assertEqual(r["projects"][0]["value"], 100.0)
        with self.assertRaises(KeyError): reports.client_report(self.db, "x")


class RecurringBulkTests(unittest.TestCase):
    def test_retainers_once_per_month(self):
        db = Database(); c = Client(name="c"); db.save(c)
        recurring.define(db, c.id, "Retainer", 10, 100, day_of_month=5)
        self.assertEqual(recurring.run_due(db, dt.date(2026, 4, 24)), [])           # 1405/02/04: day 5 not reached yet
        d = recurring.run_due(db, dt.date(2026, 5, 20)); self.assertEqual(len(d), 1)
        self.assertEqual(recurring.run_due(db, dt.date(2026, 5, 21)), [])           # idempotent in same month
        self.assertEqual(len(recurring.run_due(db, dt.date(2026, 6, 28))), 1)       # next Jalali month
        self.assertEqual(d[0].total, 1000)
        for bad in (dict(hours=0), dict(day_of_month=31), dict(description=" ")):
            with self.assertRaises(ValueError): recurring.define(db, c.id, **{**dict(description="x", hours=1, rate=1), **bad})
        with self.assertRaises(KeyError): recurring.define(db, "zz", "x", 1, 1)

    def test_bulk(self):
        db = Database(); p = Project(name="Web"); db.save(p)
        txt = "// comment\n2026-05-01 09:00-10:30 write docs #docs @web\n۱۴۰۵/۰۲/۱۲ 23:00-01:00 night work\n\n"
        r = bulk.bulk_add(db, txt)
        self.assertEqual((r["added"], r["errors"]), (2, []))
        es = db.all(TimeEntry, "start_utc")
        self.assertEqual((es[0].duration_sec, es[0].tags, es[0].project_id), (5400, ["docs"], p.id))
        self.assertEqual(es[1].duration_sec, 7200)                                   # crosses midnight
        r2 = bulk.bulk_add(db, "2026-05-01 09:00-10:00 ok\nnot a line\n2026-05-01 10:00-11:00 #only")
        self.assertEqual(r2["added"], 0); self.assertEqual([n for n, _ in r2["errors"]], [2, 3])
        self.assertEqual(len(db.all(TimeEntry)), 2)                                  # all-or-nothing

    def test_resume_last(self):
        db = Database(); t = [now_utc()]; tr = Tracker(db, TrackerSettings(), lambda: t[0])
        self.assertIsNone(tr.resume_last())
        tr.start("deep work", tags=["x"], billable=True); t[0] += dt.timedelta(minutes=10); tr.stop()
        r = tr.resume_last(); self.assertEqual((r.title, r.tags, r.billable, r.status), ("deep work", ["x"], True, Status.RUNNING))


class Smart2Tests(unittest.TestCase):
    def test_title_suggestions(self):
        db = Database()
        for t in ["Fix login validation bug", "Fix login validation bug", "Fix payment bug", "Write docs"]:
            db.save(TimeEntry(title=t, start_utc=L(9), end_utc=L(10)))
        self.assertEqual(smart2.suggest_titles(db, "fix bug")[0], "Fix login validation bug")
        self.assertEqual(smart2.suggest_titles(db, "fi"), []); self.assertEqual(smart2.suggest_titles(db, "zzzz"), [])

    def test_mood_energy_smart_feed(self):
        self.assertEqual(smart2.typing_mood([100, 110, 90, 105, 95, 100, 98, 102, 99, 101]), "flow")
        self.assertEqual(smart2.typing_mood([50, 900, 80, 1500, 60, 700, 90, 2000, 70, 800]), "stressed")
        self.assertEqual(smart2.typing_mood([400, 500, 450, 480, 420, 460, 440, 470, 430, 490]), "calm")
        self.assertEqual(smart2.typing_mood([1, 2]), "unknown"); self.assertEqual(smart2.typing_mood([100] * 10, backspaces=5), "stressed")
        db = Database()
        for h, e in [(9, 5), (9, 4), (14, 2), (20, 0)]:
            db.save(TimeEntry(title="x", start_utc=L(h), end_utc=L(h + 1), energy=e))
        self.assertEqual(smart2.energy_by_hour(db), {9: 4.5, 14: 2.0}); self.assertEqual(smart2.peak_energy_hours(db, 1), [9])
        ok = Goal(name="Ship version one", key_results=[{"name": "k", "target": 5, "current": 0}], deadline=L(9))
        self.assertEqual(smart2.validate_smart(ok), [])
        bad = Goal(name="x", key_results=[{"name": "k", "target": 0}] * 6)
        self.assertEqual(len(smart2.validate_smart(bad)), 4)
        sw = smart2.same_week_last_year(db, dt.date(2026, 5, 5)); self.assertIn("change_pct", sw)
        db.save(Project(name="P")); feed = smart2.activity_feed(db, 3)
        self.assertEqual(feed[0]["action"], "create"); self.assertEqual(feed[0]["label"], "P")

    def test_telegram_polling(self):
        db, calls = Database(), []
        updates = {"result": [{"update_id": 7, "message": {"chat": {"id": 1}, "text": "/log 30m call"}},
                              {"update_id": 8, "message": {"chat": {"id": 99}, "text": "/log 30m hack"}}]}
        class R:
            def __init__(s, body): s.body, s.status = body, 200
            def read(s): return s.body
            def __enter__(s): return s
            def __exit__(s, *a): return False
        def opener(req, timeout):
            url = req.full_url if hasattr(req, "full_url") else req
            calls.append(url)
            return R(json.dumps(updates).encode() if "getUpdates" in url else b"{}")
        tok = "123456:" + "A" * 30
        off = chat.poll_once(db, tok, [1], 0, opener)
        self.assertEqual(off, 9); self.assertEqual([e.title for e in db.all(TimeEntry)], ["call"])      # stranger ignored
        self.assertTrue(any("sendMessage" in c for c in calls))
        self.assertEqual(chat.poll_once(db, "bad", [1], 5, opener), 5)
        def boom(req, timeout): raise OSError("offline")
        self.assertEqual(chat.poll_once(db, tok, [1], 5, boom), 5)


class ReliabilityTests(unittest.TestCase):
    def test_two_threads_writing(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "c.db"; Database(path).close(); errors = []
            def worker(tag):
                try:
                    db = Database(path)
                    for i in range(150): db.save(TimeEntry(title=f"{tag}{i}", start_utc=now_utc(), end_utc=now_utc()))
                    db.close()
                except Exception as exc:       # noqa: BLE001
                    errors.append(exc)
            ts = [threading.Thread(target=worker, args=(c,)) for c in "ab"]
            [t.start() for t in ts]; [t.join(30) for t in ts]
            db = Database(path)
            self.assertEqual(errors, []); self.assertEqual(len(db.all(TimeEntry)), 300); self.assertTrue(db.integrity_ok()); db.close()

    def test_kill_mid_write_keeps_database_intact(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "k.db"
            db = Database(path); db.save(Project(name="committed")); db.close()
            code = ("import os,sys; sys.path.insert(0, sys.argv[2]);"
                    "from worktracker.core.database import Database; from worktracker.core.models import Project;"
                    "db=Database(sys.argv[1]); db.conn.execute('BEGIN'); "
                    "[db.conn.execute(\"INSERT INTO projects (id,name,created_at,updated_at) VALUES (?,?,'x','x')\",(f'u{i}','uncommitted')) for i in range(500)];"
                    "os._exit(9)")
            r = subprocess.run([sys.executable, "-c", code, str(path), ROOT], capture_output=True, timeout=60)
            self.assertEqual(r.returncode, 9)
            db = Database(path)
            self.assertTrue(db.integrity_ok()); self.assertEqual([p.name for p in db.all(Project)], ["committed"]); db.close()

    def test_corrupt_database_recovers_from_backup(self):
        with tempfile.TemporaryDirectory() as d:
            path, bk = Path(d) / "m.db", Path(d) / "bk"
            db = Database(path); db.save(Project(name="precious")); db.rotate_backups(bk); db.close()
            for ext in ("-wal", "-shm"): Path(str(path) + ext).unlink(missing_ok=True)
            path.write_bytes(b"this is not a database" * 100)
            self.assertFalse(recovery.is_healthy(path))
            used = recovery.recover(path, bk); self.assertIsNotNone(used)
            db = Database(path); self.assertEqual([p.name for p in db.all(Project)], ["precious"]); db.close()
            self.assertTrue(path.with_suffix(".corrupt").exists())
            self.assertIsNone(recovery.recover(path, bk))                             # healthy -> untouched
            path.write_bytes(b"junk" * 100)
            with self.assertRaises(RuntimeError): recovery.recover(path, Path(d) / "empty")

    def test_works_with_network_blocked(self):
        def deny(*a, **k): raise OSError("network disabled for test")
        with mock.patch.object(socket.socket, "connect", deny), mock.patch.object(socket, "create_connection", deny), \
             mock.patch.object(socket, "getaddrinfo", deny):
            from worktracker.integrations.google_calendar import GoogleCalendarPlugin, build_service
            from worktracker.integrations.webhook import post_json
            from worktracker.services import activity, analytics, billing, exporter, insights
            with tempfile.TemporaryDirectory() as d:
                db = Database(Path(d) / "o.db")
                self.assertIsNone(build_service(d))                                    # no credentials -> no network, no error
                self.assertFalse(GoogleCalendarPlugin(db, None).available)
                tr = Tracker(db); tr.start("offline"); time.sleep(0.01); tr.stop()
                db.save(TimeEntry(title="x", start_utc=L(9), end_utc=L(10)))
                analytics.Analytics(db).year_summary(1405); insights.year_in_review(db, 1405); exporter.export_json(db, Path(d) / "a.json")
                self.assertFalse(post_json("http://example.invalid/x", {}))            # fails quietly
                activity.foreground_window()
                self.assertEqual(chat.poll_once(db, "1:" + "x" * 25, [1], 3), 3)

    def test_cold_start_core_under_800ms(self):
        code = ("import sys,time; t=time.perf_counter(); sys.path.insert(0, sys.argv[1]);"
                "from worktracker.core.database import Database; from worktracker.services.analytics import Analytics; db=Database(); Analytics(db).year_summary(1405);"
                "print(time.perf_counter()-t)")
        r = subprocess.run([sys.executable, "-c", code, ROOT], capture_output=True, text=True, timeout=60)
        self.assertLess(float(r.stdout.strip()), 0.8)

    def test_no_network_calls_in_ui_startup_source(self):
        # static guard: nothing in the UI package may import a network library
        for f in (Path(ROOT) / "worktracker" / "ui").glob("*.py"):
            src = f.read_text(encoding="utf-8")
            for banned in ("import requests", "import urllib", "import socket", "http.client"):
                self.assertNotIn(banned, src, f"{f.name} must not use {banned}")


class EisenhowerTests(unittest.TestCase):
    def test_drag_targets(self):
        from worktracker.services import planner
        db, now = Database(), dt.datetime(2026, 5, 2, 9, tzinfo=UTC)
        e = TimeEntry(title="t", start_utc=now, status=Status.PLANNED); db.save(e)
        self.assertEqual(planner.eisenhower(db.get(TimeEntry, e.id), now), "eliminate")
        for q in ("do", "delegate", "schedule", "eliminate", "do"):
            planner.set_quadrant(db, e.id, q, now)
            self.assertEqual(planner.eisenhower(db.get(TimeEntry, e.id), now), q, q)
        with self.assertRaises(ValueError): planner.set_quadrant(db, e.id, "x", now)
        with self.assertRaises(KeyError): planner.set_quadrant(db, "zz", "do", now)
        g = planner.quadrants(db, now); self.assertEqual([len(g[k]) for k in ("do", "schedule", "delegate", "eliminate")], [1, 0, 0, 0])
        db.save(TimeEntry(title="done", start_utc=now, end_utc=now + dt.timedelta(hours=1)))   # finished tasks are not listed
        self.assertEqual(sum(len(v) for v in planner.quadrants(db, now).values()), 1)


if __name__ == "__main__":
    unittest.main()
