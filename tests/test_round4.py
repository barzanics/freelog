import csv
import datetime as dt
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path

from worktracker.core.database import Database
from worktracker.core.models import ActivityEvent, Client, Invoice, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC, jalali_to_date, now_utc
from worktracker.integrations import http_api, importers
from worktracker.services import autostart, blueprints, maintenance, metrics, security, views


def L(h, m=0, day=2, month=5):
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class ModelFieldTests(unittest.TestCase):
    def test_project_new_fields_roundtrip(self):
        db = Database()
        p = Project(name="P", priority=2, start=L(9, day=1), deadline=L(9, day=20), team_members=["m1"], dependencies=["p0"], notes="n")
        db.save(p)
        q = db.get(Project, p.id)
        self.assertEqual((q.priority, q.team_members, q.dependencies, q.notes), (2, ["m1"], ["p0"], "n"))
        self.assertEqual(q.start, p.start)
        self.assertIsInstance(p.to_row()["team_members"], str)
        for bad in (dict(priority=9), dict(start=L(9, day=5), deadline=L(9, day=1))):
            with self.assertRaises(ValueError): Project(name="x", **bad)
        with self.assertRaises(ValueError): Project(name="x", id="a", dependencies=["a"])

    def test_entry_overdue_and_completed(self):
        e = TimeEntry(title="x", start_utc=L(9), due_utc=L(9, day=1), status=Status.PLANNED)
        self.assertTrue(e.is_overdue(L(9, day=3)))
        self.assertFalse(e.is_overdue(L(9, day=1) - dt.timedelta(hours=1)))
        e.status = Status.DONE; self.assertFalse(e.is_overdue(L(9, day=3)))
        self.assertFalse(TimeEntry(title="y", start_utc=L(9)).is_overdue())

    def test_private_notes_stay_encrypted(self):
        db = Database()
        e = TimeEntry(title="x", start_utc=L(9), notes_private=security.encrypt_text("pw", "سر"))
        db.save(e)
        raw = db.conn.execute("SELECT notes_private FROM entries").fetchone()[0]
        self.assertNotIn("سر", raw); self.assertEqual(security.decrypt_text("pw", raw), "سر")

    def test_completed_at_set_by_tracker_and_kanban(self):
        from worktracker.services.projects import ProjectService
        from worktracker.services.tracker import Tracker
        db = Database(); tr = Tracker(db)
        e = TimeEntry(title="k", start_utc=L(9), status=Status.PLANNED); db.save(e)
        ProjectService(db).move(e.id, "done"); self.assertIsNotNone(db.get(TimeEntry, e.id).completed_at)
        ProjectService(db).move(e.id, "review"); self.assertIsNone(db.get(TimeEntry, e.id).completed_at)

    def test_legacy_import_still_works_with_new_columns(self):
        # migration v4 columns must not break row inserts used by the importer
        db = Database(); self.assertEqual(db.version, 5)
        db.save(Project(name="a")); self.assertTrue(db.integrity_ok())


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def add(self, start, minutes, **kw):
        e = TimeEntry(title="t", start_utc=start, end_utc=start + dt.timedelta(minutes=minutes), **kw); self.db.save(e); return e

    def test_week_grid(self):
        self.add(L(9, day=2), 60); self.add(L(23, 30, day=3), 90)       # second crosses midnight
        g = views.week_grid(self.db, dt.date(2026, 5, 5))              # Tuesday -> week starts Sat May 2
        self.assertEqual([c["date"].day for c in g], [2, 3, 4, 5, 6, 7, 8])
        self.assertEqual([(b["start"], b["end"]) for b in g[0]["blocks"]], [("09:00", "10:00")])
        self.assertEqual([(b["start"], b["end"]) for b in g[1]["blocks"]], [("23:30", "00:00")])
        self.assertEqual([(b["start"], b["end"]) for b in g[2]["blocks"]], [("00:00", "01:00")])

    def test_month_calendar(self):
        self.add(L(9, day=2), 120)                                      # 1405/02/12
        jy = 1405
        cal = views.month_calendar(self.db, jy, 2)
        flat = [c for w in cal["weeks"] for c in w]
        self.assertTrue(all(len(w) == 7 for w in cal["weeks"]))
        self.assertEqual(len([c for c in flat if c]), 31)
        self.assertEqual(cal["total_sec"], 7200)
        self.assertIn((12, 7200), flat)
        # Esfand of a leap year has 30 days
        self.assertEqual(len([c for w in views.month_calendar(self.db, 1403, 12)["weeks"] for c in w if c]), 30)

    def test_timebox_adherence(self):
        self.add(L(9), 60, status=Status.PLANNED); self.add(L(11), 60, status=Status.PLANNED)
        self.add(L(9, 15), 30)                                          # worked 30 of the first hour
        r = views.timebox_adherence(self.db, dt.date(2026, 5, 2))
        self.assertEqual((r["planned_min"], r["worked_in_plan_min"], r["adherence_pct"]), (120.0, 30.0, 25.0))
        self.assertEqual(views.timebox_adherence(Database(), dt.date(2026, 5, 2))["adherence_pct"], 0.0)

    def test_breakdown(self):
        es = [TimeEntry(title="a", start_utc=L(9), end_utc=L(10), category="x"), TimeEntry(title="b", start_utc=L(9), end_utc=L(11), category="x")]
        self.assertEqual(views.breakdown_by_category(es), {"x": 10800})


class MetricsTests(unittest.TestCase):
    def test_funnel(self):
        db = Database()
        db.save(TimeEntry(title="plan", start_utc=L(9), status=Status.PLANNED))
        db.save(TimeEntry(title="doing", start_utc=L(9), status=Status.PLANNED, column="in_progress"))
        db.save(TimeEntry(title="done", start_utc=L(9), end_utc=L(10)))
        sub = TimeEntry(title="sub", start_utc=L(9), status=Status.PLANNED, parent_id=None); db.save(sub)
        self.assertEqual(metrics.funnel(db), {"planned": 4, "started": 2, "completed": 1})

    def test_cohorts(self):
        db = Database()
        a, b = Client(name="a"), Client(name="b"); db.save(a); db.save(b)
        pa = Project(name="pa", client_id=a.id); db.save(pa)
        db.save(TimeEntry(title="x", start_utc=L(9), end_utc=L(11), project_id=pa.id))
        for _ in range(2): db.save(Invoice(client_id=a.id, items=[{"hours": 1, "rate": 10}]))
        db.save(Invoice(client_id=b.id, items=[{"hours": 1, "rate": 5}]))
        c = metrics.client_cohorts(db)
        self.assertEqual((c["repeat"]["clients"], c["repeat"]["hours"], c["repeat"]["billed"]), (1, 2.0, 20.0))
        self.assertEqual((c["first_time"]["clients"], c["first_time"]["billed"]), (1, 5.0))

    def test_kpis_and_dashboards(self):
        db = Database()
        db.save(TimeEntry(title="x", start_utc=L(9), end_utc=L(11), billable=True)); db.save(TimeEntry(title="y", start_utc=L(12), end_utc=L(14)))
        metrics.define_kpi(db, "billable ratio", "billable_hours / total_hours * 100"); metrics.define_kpi(db, "broken", "1 / (total_hours - 4)")
        with self.assertRaises(ValueError): metrics.define_kpi(db, "const", "1 / 0")
        with self.assertRaises(ValueError): metrics.define_kpi(db, "bad", "nope + 1")
        with self.assertRaises(ValueError): metrics.define_kpi(db, "evil", "__import__('os')")
        k = metrics.evaluate_kpis(db, 1405)
        self.assertEqual(k["billable ratio"], 50.0); self.assertNotEqual(k["broken"], k["broken"])   # NaN
        metrics.save_dashboard(db, "focus", ["timer", "pomodoro", "timer"])
        self.assertEqual(metrics.get_dashboard(db, "focus"), ["timer", "pomodoro"])
        self.assertEqual(metrics.get_dashboard(db, "unknown"), list(metrics.WIDGETS))
        with self.assertRaises(ValueError): metrics.save_dashboard(db, "x", ["nope"])
        with self.assertRaises(ValueError): metrics.save_dashboard(db, " ", ["hero"])


class MaintenanceTests(unittest.TestCase):
    def test_compress_audit_keeps_history_and_time_travel(self):
        db = Database(); e = TimeEntry(title="old", start_utc=L(9), end_utc=L(10)); db.save(e)
        db.conn.execute("UPDATE audit_log SET at=?", ((now_utc() - dt.timedelta(days=200)).isoformat(),)); db.conn.commit()
        before = db.conn.execute("SELECT LENGTH(detail) FROM audit_log").fetchone()[0]
        self.assertEqual(maintenance.compress_old_audit(db), 1)
        self.assertEqual(maintenance.compress_old_audit(db), 0)                          # idempotent
        d = db.conn.execute("SELECT detail FROM audit_log").fetchone()[0]
        self.assertTrue(d.startswith("gz:")); self.assertLess(len(d), before)
        self.assertEqual(db.history(TimeEntry, e.id)[0]["row"]["title"], "old")
        self.assertEqual([x.title for x in db.entries_as_of(now_utc())], ["old"])
        maintenance.vacuum(db)
        self.assertEqual(maintenance.unpack("plain"), "plain")


class AutostartTests(unittest.TestCase):
    def test_linux_and_mac_create_parents(self):
        with tempfile.TemporaryDirectory() as d:
            f = autostart.enable(d, "linux", "run-me")
            self.assertTrue(f.exists()); self.assertIn("Exec=run-me", f.read_text()); self.assertTrue(autostart.is_enabled(d, "linux"))
            self.assertTrue(autostart.disable(d, "linux")); self.assertFalse(autostart.is_enabled(d, "linux")); self.assertFalse(autostart.disable(d, "linux"))
            m = autostart.enable(d, "darwin", "a & b")
            self.assertIn("a &amp; b", m.read_text()); self.assertTrue(m.parent.name == "LaunchAgents")


class BlueprintTests(unittest.TestCase):
    def test_blueprint_and_summary(self):
        db = Database()
        blueprints.save_blueprint(db, "web", [{"title": "design", "estimated_min": 240}, {"title": "build", "estimated_min": 480, "depends_on": [0]},
                                              {"title": "launch", "depends_on": [0, 1]}], defaults={"rate_per_hour": 100, "estimated_hours": 20})
        p = blueprints.create_from_blueprint(db, "web", "Site X")
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM entries WHERE project_id=?", (p.id,)).fetchone()[0], 3)
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0], 3)
        db.save(TimeEntry(title="work", start_utc=L(9), end_utc=L(11), project_id=p.id))
        s = blueprints.project_summary(db, p.id)
        self.assertEqual((s["actual_hours"], s["spent"], s["tasks"], s["health"]), (2.0, 200.0, 4, "on_track"))
        with self.assertRaises(KeyError): blueprints.create_from_blueprint(db, "nope", "x")
        for bad in ([], [{"title": ""}], [{"title": "a", "depends_on": [0]}], [{"title": "a"}, {"title": "b", "depends_on": [5]}]):
            with self.assertRaises(ValueError): blueprints.save_blueprint(db, "bad", bad)

    def test_blueprint_atomic_on_failure(self):
        db = Database()
        blueprints.save_blueprint(db, "ok", [{"title": "a"}])
        db.set_setting("blueprints", {"ok": {"tasks": [{"title": "a"}, {"title": "b", "depends_on": [1]}], "defaults": {}}})   # corrupted: self-dependency
        with self.assertRaises(Exception): blueprints.create_from_blueprint(db, "ok", "P")
        self.assertEqual(db.all(Project), [])


class ImportTests(unittest.TestCase):
    def test_rescuetime(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "rt.csv"
            with f.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh); w.writerow(["Date", "Time Spent (seconds)", "Activity", "Category", "Productivity"])
                w.writerows([["2026-05-01", "600", "Visual Studio Code", "Editing", 2], ["2026-05-01", "300", "chrome.exe", "Browsing", 0],
                             ["2026-05-01", "0", "zero", "x", 0], ["bad", "10", "x", "y", 0], ["2026-05-02", "60", "", "y", 0]])
            db = Database(); st = importers.import_rescuetime(db, f)
            self.assertEqual(st, {"events": 2, "skipped": 3})
            ev = db.all(ActivityEvent) if False else [ActivityEvent.from_row(r) for r in db.conn.execute("SELECT * FROM activity_events ORDER BY start_utc")]
            self.assertEqual((ev[0].seconds, ev[0].category, ev[1].start_utc), (600, "development", ev[0].end_utc))


class WebActivityApiTests(unittest.TestCase):
    def test_domain_and_endpoint(self):
        self.assertEqual(http_api.domain_of("https://www.Example.com/path?q=1"), "example.com")
        self.assertEqual(http_api.domain_of("github.com/x"), "github.com"); self.assertEqual(http_api.domain_of("ftp://x.com"), ""); self.assertEqual(http_api.domain_of(""), "")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "a.db"; Database(path).close(); tok = "k" * 20
            srv, _ = http_api.start_server(path, tok, 0); base = f"http://127.0.0.1:{srv.server_address[1]}"
            def post(body):
                req = urllib.request.Request(base + "/v1/activity", data=json.dumps(body).encode(), method="POST", headers={"Authorization": "Bearer " + tok})
                try:
                    with urllib.request.urlopen(req, timeout=5) as r: return r.status
                except urllib.error.HTTPError as e: return e.code
            try:
                self.assertEqual(post({"url": "https://news.ycombinator.com/x", "seconds": 90}), 200); self.assertEqual(post({"url": "", "seconds": 5}), 400)
            finally:
                srv.shutdown(); srv.server_close()
            db = Database(path)
            row = db.conn.execute("SELECT app, category FROM activity_events").fetchone(); db.close()
            self.assertEqual(tuple(row), ("web:news.ycombinator.com", "browsing"))


if __name__ == "__main__":
    unittest.main()
