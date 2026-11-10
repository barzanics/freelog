import csv
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from worktracker.core.database import Database
from worktracker.core.models import Client, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC, jalali_to_date, now_utc
from worktracker.services import exporter
from worktracker.services.analytics import Analytics, split_by_local_day, streaks
from worktracker.services.tracker import MAX_SESSION_SEC, Tracker, TrackerSettings, round_seconds


class Clock:
    def __init__(self):
        self.t = now_utc()

    def __call__(self):
        return self.t

    def adv(self, **kw):
        self.t += dt.timedelta(**kw)


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.clk = Clock()
        self.tr = Tracker(self.db, TrackerSettings(), self.clk)

    def test_start_stop(self):
        self.tr.start("کار")
        self.clk.adv(minutes=30)
        self.assertEqual(self.tr.elapsed(), 1800)
        e = self.tr.stop()
        self.assertEqual((e.duration_sec, e.status), (1800, Status.DONE))
        self.assertIsNone(self.tr.current)

    def test_only_one_running(self):
        self.tr.start("a"); self.clk.adv(minutes=5)
        self.tr.start("b")
        running = self.db.conn.execute("SELECT COUNT(*) FROM entries WHERE status='running'").fetchone()[0]
        self.assertEqual(running, 1)
        self.assertEqual(len(self.db.entries_between(self.clk.t - dt.timedelta(days=1), self.clk.t + dt.timedelta(days=1))), 1)

    def test_min_duration_discards(self):
        self.tr.start("x"); self.clk.adv(seconds=30)
        self.assertIsNone(self.tr.stop())
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0], 0)

    def test_idle_trim(self):
        self.tr.start("x"); self.clk.adv(minutes=40)
        self.assertEqual(self.tr.stop(idle_seconds=600).duration_sec, 30 * 60)

    def test_idle_larger_than_session(self):
        self.tr.start("x"); self.clk.adv(minutes=2)
        self.assertIsNone(self.tr.stop(idle_seconds=99999))

    def test_rounding(self):
        self.assertEqual(round_seconds(61, 15), 900)
        self.assertEqual(round_seconds(900, 15), 900)
        self.assertEqual(round_seconds(901, 15), 1800)
        self.assertEqual(round_seconds(0, 15), 0)
        self.assertEqual(round_seconds(100, 0), 100)
        self.tr.settings.round_to_min = 15
        self.tr.start("x"); self.clk.adv(minutes=20)
        self.assertEqual(self.tr.stop().duration_sec, 1800)

    def test_auto_split_after_4h(self):
        self.tr.start("long"); self.clk.adv(hours=9)
        last = self.tr.stop()
        rows = self.db.all(TimeEntry, "start_utc")
        self.assertEqual(sum(r.duration_sec for r in rows), 9 * 3600)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r.duration_sec <= MAX_SESSION_SEC for r in rows))
        self.assertEqual(rows[-1].id, last.id)
        for a, b in zip(rows, rows[1:]):
            self.assertEqual(a.end_utc, b.start_utc)

    def test_empty_title_and_stop_without_timer(self):
        with self.assertRaises(ValueError):
            self.tr.start("   ")
        self.assertIsNone(self.tr.stop())

    def test_manual(self):
        s = self.clk.t - dt.timedelta(hours=3)
        e = self.tr.add_manual("m", s, s + dt.timedelta(hours=1), billable=True)
        self.assertEqual(e.duration_sec, 3600)
        with self.assertRaises(ValueError):
            self.tr.add_manual("m", s, s)

    def test_crash_recovery(self):
        self.tr.start("x")
        e = self.tr.recover_after_crash()
        self.assertIsNone(e)  # < min duration => dropped
        self.assertIsNone(self.tr.current)


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.an = Analytics(self.db)
        self.p = Project(name="Alpha"); self.db.save(self.p)

    def add(self, day, h, m, dur_min, **kw):
        local = dt.datetime.combine(day, dt.time(h, m), tzinfo=TEHRAN)
        s = local.astimezone(UTC)
        self.db.save(TimeEntry(title="t", start_utc=s, end_utc=s + dt.timedelta(minutes=dur_min), **kw))

    def test_midnight_split(self):
        s = dt.datetime(2026, 5, 1, 23, 0, tzinfo=TEHRAN).astimezone(UTC)
        e = TimeEntry(title="x", start_utc=s, end_utc=s + dt.timedelta(hours=2))
        parts = split_by_local_day(e)
        self.assertEqual([(d.day, sec) for d, sec, _ in parts], [(1, 3600), (2, 3600)])

    def test_year_summary(self):
        d1 = jalali_to_date(1405, 1, 1); d2 = jalali_to_date(1405, 1, 2)
        self.add(d1, 9, 0, 120, project_id=self.p.id, category="dev", tags=["a"], billable=True)
        self.add(d1, 14, 0, 60, category="dev")
        self.add(d2, 10, 0, 30, project_id=self.p.id, category="ops")
        s = self.an.year_summary(1405, today=d2)
        self.assertEqual(s.total_sec, 210 * 60)
        self.assertEqual(s.total_hours, 3.5)
        self.assertEqual(s.billable_sec, 7200)
        self.assertEqual(s.days_worked, 2)
        self.assertEqual(s.by_project, {"Alpha": 9000, "—": 3600})
        self.assertEqual(s.by_category["dev"], 10800)
        self.assertEqual(s.by_tag, {"a": 7200})
        self.assertEqual(s.by_month[0], 210 * 60)
        self.assertEqual((s.by_hour[9], s.by_hour[10], s.by_hour[14], sum(s.by_hour)), (3600, 3600 + 1800, 3600, 210 * 60))
        self.assertEqual((s.longest_streak, s.current_streak), (2, 2))
        self.assertEqual(s.avg_hours_per_worked_day, 1.75)

    def test_year_boundary_exclusion(self):
        self.add(jalali_to_date(1404, 12, 29), 10, 0, 60)   # last day of 1404
        self.add(jalali_to_date(1405, 1, 1), 10, 0, 60)
        self.assertEqual(self.an.year_summary(1405).total_sec, 3600)
        self.assertEqual(self.an.year_summary(1404).total_sec, 3600)

    def test_year_boundary_midnight_straddle(self):
        last = jalali_to_date(1404, 12, 29)
        self.add(last, 23, 0, 120)  # 1h in 1404, 1h in 1405
        self.assertEqual(self.an.year_summary(1404).total_sec, 3600)
        self.assertEqual(self.an.year_summary(1405).total_sec, 3600)

    def test_year_summary_performance_10k(self):
        import time
        base = dt.datetime(2026, 4, 1, 5, tzinfo=UTC)
        with self.db.transaction() as c:
            for i in range(10000):
                e = TimeEntry(title="t", start_utc=base + dt.timedelta(minutes=30 * i), end_utc=base + dt.timedelta(minutes=30 * i + 20))
                r = e.to_row()
                c.execute(f"INSERT INTO entries ({','.join(chr(34) + k + chr(34) for k in r)}) VALUES ({','.join('?' * len(r))})", tuple(r.values()))
        t0 = time.perf_counter()
        s = self.an.year_summary(1405)
        self.assertLess(time.perf_counter() - t0, 0.5)
        self.assertEqual(s.total_sec, 10000 * 20 * 60)

    def test_entries_with_fractional_seconds_crossing_an_hour_do_not_hang(self):
        """Regression: start 10:15:30.5 + 1 h used to loop forever (distance to the hour rounded down to 0)."""
        import signal
        from worktracker.services.analytics import spread_hours
        buckets = [0] * 24
        start = dt.datetime(2026, 5, 2, 10, 15, 30, 500000, tzinfo=TEHRAN)
        signal.alarm(5)
        try:
            spread_hours(buckets, start, 3600)
            self.assertEqual((sum(buckets), buckets[10], buckets[11]), (3600, 2670, 930))
            spread_hours([0] * 24, dt.datetime(2026, 5, 2, 10, 59, 59, 999999, tzinfo=TEHRAN), 7200)
            e = TimeEntry(title="real timer", start_utc=start.astimezone(UTC), end_utc=start.astimezone(UTC) + dt.timedelta(minutes=95, microseconds=123456))
            self.db.save(e)
            s = self.an.year_summary(1405)
            self.assertEqual(sum(s.by_hour), s.total_sec); self.assertGreater(s.total_sec, 5000)
        finally:
            signal.alarm(0)

    def test_empty_year(self):
        s = self.an.year_summary(1405)
        self.assertEqual((s.total_sec, s.days_worked, s.avg_hours_per_worked_day, s.longest_streak), (0, 0, 0.0, 0))

    def test_streaks(self):
        d = dt.date(2026, 1, 1)
        days = [d, d + dt.timedelta(1), d + dt.timedelta(2), d + dt.timedelta(5)]
        self.assertEqual(streaks(days, today=d + dt.timedelta(5)), (3, 1))
        self.assertEqual(streaks(days, today=d + dt.timedelta(6)), (3, 1))  # yesterday counts
        self.assertEqual(streaks(days, today=d + dt.timedelta(9)), (3, 0))
        self.assertEqual(streaks([]), (0, 0))

    def test_heatmap_levels(self):
        d = dt.date(2026, 1, 1)
        daily = {d + dt.timedelta(i): v for i, v in enumerate([0, 10, 20, 30, 40, 1000])}
        lv = Analytics.heatmap_levels(daily)
        self.assertNotIn(d, lv)
        self.assertEqual(lv[d + dt.timedelta(5)], 4)
        self.assertTrue(all(1 <= v <= 4 for v in lv.values()))
        self.assertEqual(Analytics.heatmap_levels({}), {})

    def test_productivity_bounds(self):
        f = Analytics.productivity_score
        self.assertEqual(f(0, 0, 30), 0 + round(100 * 0.2))  # only focus credit
        self.assertEqual(f(6 * 3600 * 30, 30, 30), 100)
        self.assertEqual(f(10**9, 30, 30), 100)
        self.assertEqual(f(0, 0, 0), 0)
        self.assertLess(f(3600, 5, 30, interruptions_per_day=10), f(3600, 5, 30))

    def test_forecast(self):
        d = jalali_to_date(1405, 1, 10)
        self.add(jalali_to_date(1405, 1, 1), 9, 0, 600)
        self.assertEqual(self.an.forecast_year_total_hours(1405, d), round(10 / 10 * 365, 1))

    def test_budget_status(self):
        p = Project(name="B", estimated_hours=10, budget=1000, rate_per_hour=50); self.db.save(p)
        self.add(dt.date(2026, 5, 1), 9, 0, 300, project_id=p.id)
        st = self.an.project_budget_status(p.id)
        self.assertEqual((st["hours"], st["hours_pct"], st["cost"], st["budget_pct"]), (5.0, 50.0, 250.0, 25.0))
        with self.assertRaises(KeyError):
            self.an.project_budget_status("nope")


class ExporterTests(unittest.TestCase):
    def test_roundtrip_and_safety(self):
        with tempfile.TemporaryDirectory() as d:
            db = Database()
            c = Client(name="c"); p = Project(name="p", client_id=c.id)
            db.save(c); db.save(p)
            s = now_utc()
            db.save(TimeEntry(title="=cmd()", start_utc=s, end_utc=s + dt.timedelta(hours=1), project_id=p.id, tags=["x", "ی"], notes="@evil"))
            j = exporter.export_json(db, Path(d) / "a.json")
            json.loads(j.read_text(encoding="utf-8"))
            db2 = Database()
            self.assertEqual(exporter.import_json(db2, j), 3)
            self.assertEqual(db2.all(TimeEntry)[0].tags, ["x", "ی"])
            self.assertEqual(exporter.import_json(db2, j), 3)  # idempotent
            self.assertEqual(len(db2.all(TimeEntry)), 1)
            csvp = exporter.export_csv(db, Path(d) / "a.csv")
            with csvp.open(encoding="utf-8-sig") as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(rows[1][1], "'=cmd()")   # formula neutralised
            self.assertEqual(rows[1][9], "'@evil")
            self.assertEqual(rows[1][2], "p")
            x = exporter.export_xlsx(db, Path(d) / "a.xlsx")
            self.assertTrue(x.stat().st_size > 1000)


if __name__ == "__main__":
    unittest.main()
