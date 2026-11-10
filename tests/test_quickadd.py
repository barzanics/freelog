import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import geometry as geo, quick, quickadd


def L(h, m=0, day=2):
    return dt.datetime(2026, 5, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class ParseTests(unittest.TestCase):
    def test_everything_in_one_line(self):
        c = quick.parse("fix login #bug #urgent @WebApp 45m")
        self.assertEqual((c.title, c.tags, c.project, c.minutes, c.has_range), ("fix login", ["bug", "urgent"], "WebApp", 45, False))
        self.assertEqual(quick.parse("write docs 1h30").minutes, 90); self.assertEqual(quick.parse("x 2h 15m").minutes, 135); self.assertEqual(quick.parse("x 1.5h").minutes, 90)

    def test_time_ranges_and_persian_digits(self):
        c = quick.parse("standup 09:30-10:00 #team"); self.assertEqual((c.start_time, c.end_time, c.range_minutes(), c.tags), (dt.time(9, 30), dt.time(10, 0), 30, ["team"]))
        c = quick.parse("review ۹:۰۰-۱۱"); self.assertEqual((c.start_time, c.end_time, c.range_minutes()), (dt.time(9), dt.time(11), 120))
        self.assertEqual(quick.parse("night 23:00-01:00").range_minutes(), 120)                       # crosses midnight
        self.assertEqual(quick.parse("a #x،#y").tags, ["x", "y"])
        for bad in ("a 25:00-26:00", "a 9:99-10:00"):
            with self.assertRaises(ValueError): quick.parse(bad)
        with self.assertRaises(ValueError): quick.parse("#only 5m")
        self.assertEqual(quick.parse("buy 3 apples").title, "buy 3 apples")


class CreateTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.p = Project(name="WebApp"); self.db.save(self.p); self.now = L(14)

    def test_task_log_timer(self):
        r = quickadd.create(self.db, "write spec @web 30m", "task", now=self.now)
        self.assertEqual((r.kind, r.entry.project_id, r.entry.estimated_min, r.entry.status), ("task", self.p.id, 30, Status.PLANNED))
        r = quickadd.create(self.db, "call client #x 45m", "log", now=self.now)
        self.assertEqual((r.entry.status, r.entry.duration_sec, r.entry.end_utc, r.entry.source, r.entry.tags), (Status.DONE, 2700, self.now, "quick", ["x"]))
        r = quickadd.create(self.db, "deep work @web", "timer", now=self.now)
        self.assertEqual((r.kind, r.entry.status), ("timer", Status.RUNNING)); self.assertEqual(len(self.db.running_entries()), 1)

    def test_log_with_exact_range_and_yesterday_rule(self):
        r = quickadd.create(self.db, "standup 09:30-10:00", "log", now=self.now)
        self.assertEqual((r.entry.start_utc, r.entry.end_utc, r.minutes), (L(9, 30), L(10), 30))
        r = quickadd.create(self.db, "late call 21:00-23:00", "log", now=self.now)                      # at 14:00 that can only mean last night
        self.assertEqual((r.entry.start_utc, r.entry.end_utc), (L(21, day=1), L(23, day=1)))
        r = quickadd.create(self.db, "overnight 23:00-01:00", "log", now=L(8))
        self.assertEqual(r.minutes, 120)

    def test_explicit_chips_override_text_and_errors(self):
        r = quickadd.create(self.db, "x 10m @zzz", "log", project_id=self.p.id, minutes=60, now=self.now); self.assertEqual((r.minutes, r.entry.project_id), (60, self.p.id))
        with self.assertRaises(ValueError): quickadd.create(self.db, "no duration", "log", now=self.now)
        with self.assertRaises(ValueError): quickadd.create(self.db, "", "task")
        with self.assertRaises(ValueError): quickadd.create(self.db, "x", "bogus")
        with self.assertRaises(ValueError): quickadd.create(self.db, "huge 00:00-20:00", "log", now=L(23, day=3))

    def test_project_resolution(self):
        self.db.save(Project(name="Website Redesign")); self.db.save(Project(name="Mobile"))
        self.assertEqual(self.db.get(Project, quickadd.resolve_project(self.db, "mob")).name, "Mobile")
        self.assertEqual(self.db.get(Project, quickadd.resolve_project(self.db, "WEBAPP")).name, "WebApp")          # exact beats prefix
        self.assertIsNone(quickadd.resolve_project(self.db, "nothing")); self.assertIsNone(quickadd.resolve_project(self.db, None))


class GeometryTests(unittest.TestCase):
    SCREEN = (0, 0, 1920, 1080)

    def test_snap_to_nearest_edge_and_clamp(self):
        self.assertEqual(geo.snap_to_edge(300, 400, 88, 88, self.SCREEN), (6, 400)); self.assertEqual(geo.snap_to_edge(1500, 400, 88, 88, self.SCREEN), (1920 - 88 - 6, 400))
        self.assertEqual(geo.snap_to_edge(900, -50, 88, 88, self.SCREEN)[1], 6); self.assertEqual(geo.snap_to_edge(900, 5000, 88, 88, self.SCREEN)[1], 1080 - 88 - 6)
        self.assertEqual(geo.snap_to_edge(2000, 100, 88, 88, (1920, 0, 1920, 1080)), (1920 + 6, 100))                  # second monitor

    def test_keep_on_screen_after_monitor_change(self):
        self.assertEqual(geo.keep_on_screen(5000, 3000, 88, 88, self.SCREEN), (1920 - 88, 1080 - 88)); self.assertEqual(geo.keep_on_screen(10, 10, 88, 88, self.SCREEN), (10, 10))

    def test_panel_opens_on_the_roomy_side_and_stays_visible(self):
        x, y = geo.panel_position((6, 500, 88, 88), 420, 300, self.SCREEN); self.assertGreater(x, 94); self.assertEqual(y, 500 + 44 - 150)
        x, y = geo.panel_position((1826, 500, 88, 88), 420, 300, self.SCREEN); self.assertLess(x + 420, 1826)
        x, y = geo.panel_position((6, 5, 88, 88), 420, 300, self.SCREEN); self.assertGreaterEqual(y, 6)
        x, y = geo.panel_position((6, 500, 88, 88), 1800, 300, (0, 0, 1000, 800)); self.assertTrue(0 <= x and x + 1800 >= 0)       # panel wider than room: falls back above/below
        for bx in (0, 500, 1832):
            for by in (0, 500, 992):
                px, py = geo.panel_position((bx, by, 88, 88), 420, 300, self.SCREEN); self.assertTrue(0 <= px <= 1920 - 420 and 0 <= py <= 1080 - 300)


if __name__ == "__main__":
    unittest.main()
