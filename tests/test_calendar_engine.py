import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import calendar_events as ce, calendar_geometry as cg, day_analysis as da
from worktracker.ui import strings


def T(h, m=0, day=17, month=11):
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class GeometryTests(unittest.TestCase):
    def test_snap_and_conversions(self):
        self.assertEqual([cg.snap(x) for x in (0, 7, 8, 22, 1450)], [0, 0, 15, 15, 1440]); self.assertEqual(cg.snap(100, 30, 60, 90), 90)
        self.assertEqual((cg.y_to_minutes(120, 60, 20), cg.minutes_to_y(90, 60, 20)), (100.0, 110.0))

    def test_overlapping_blocks_get_side_by_side_lanes(self):
        items = [{"id": "a", "start": 540, "end": 600}, {"id": "b", "start": 570, "end": 660}, {"id": "c", "start": 580, "end": 590}, {"id": "d", "start": 700, "end": 760}, {"id": "e", "start": 600, "end": 620}]
        r = {i["id"]: (i["lane"], i["lanes"]) for i in cg.layout_lanes(items)}
        self.assertEqual(r["a"][1], 3); self.assertEqual(len({r["a"][0], r["b"][0], r["c"][0]}), 3)              # a, b, c overlap each other: three lanes
        self.assertEqual(r["d"], (0, 1)); self.assertEqual(r["e"][0], r["a"][0])                                   # d is alone; e reuses the lane a freed
        self.assertEqual(cg.layout_lanes([]), [])

    def test_hit_zones_drag_range_move_and_resize(self):
        self.assertEqual([cg.hit_zone(y, 100, 200) for y in (100, 105, 150, 195, 200)], ["top", "top", "body", "bottom", "bottom"]); self.assertEqual(cg.hit_zone(101, 100, 110), "body")
        self.assertEqual(cg.drag_range(120, 180, 60), (120, 180)); self.assertEqual(cg.drag_range(180, 120, 60), (120, 180)); self.assertEqual(cg.drag_range(300, 301, 60), (300, 360))      # a click = 1 hour
        self.assertEqual(cg.drag_range(0, 2000, 60), (0, 1440))
        self.assertEqual(cg.move_resize("body", 540, 600, 40), (585, 645)); self.assertEqual(cg.move_resize("body", 1380, 1440, 120), (1380, 1440)); self.assertEqual(cg.move_resize("body", 0, 60, -50), (0, 60))
        self.assertEqual(cg.move_resize("top", 540, 600, 100), (585, 600)); self.assertEqual(cg.move_resize("bottom", 540, 600, -100), (540, 555)); self.assertEqual(cg.move_resize("bottom", 540, 600, 30), (540, 630))


class EventTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database()

    def tearDown(self):
        strings.set_language("fa")

    def test_validation_and_safe_links(self):
        for bad in ("javascript:alert(1)", "file:///etc/passwd", "ftp://x/y", "https://", "https://a b", "data:text/html,x", "https://" + "a" * 1100):
            with self.assertRaises(ce.EventError, msg=bad): ce.safe_link(bad)
        self.assertEqual((ce.safe_link(""), ce.safe_link(" https://meet.example/x?y=1 ")), ("", "https://meet.example/x?y=1"))
        for kw in (dict(title=" "), dict(title="x", kind="party"), dict(title="x", end=T(8)), dict(title="x", link="javascript:1"), dict(title="x", reminders=[-5]), dict(title="x", auto_open=True), dict(title="x", recurrence={"type": "yearly"})):
            with self.assertRaises(ce.EventError, msg=str(kw)): ce.add_event(self.db, kw.pop("title"), T(9), kw.pop("end", None), **kw)
        e = ce.add_event(self.db, "Call", T(9)); self.assertEqual((e["reminders"], e["end_utc"][:16]), ([1440, 120, 15, 0], T(10).isoformat()[:16]))

    def test_recurring_weekly_webinar_keeps_wall_clock_and_honours_until_count_exdates(self):
        e = ce.add_event(self.db, "Webinar", T(18, 0, 17), T(19, 0, 17), "webinar", link="https://zoom.example/j/1", recurrence={"type": "weekly", "weekdays": [1], "until": "2026-12-15"})
        occ = ce.occurrences(self.db, T(0, 0, 1, 11), T(0, 0, 31, 12)); self.assertEqual([o["start"].astimezone(TEHRAN).strftime("%m-%d %H:%M") for o in occ], ["11-17 18:00", "11-24 18:00", "12-01 18:00", "12-08 18:00", "12-15 18:00"])
        self.assertTrue(all(o["recurring"] and o["link"] for o in occ)); ce.skip_occurrence(self.db, e["id"], occ[1]["start"]); self.assertEqual(len(ce.occurrences(self.db, T(0, 0, 1, 11), T(0, 0, 31, 12))), 4)
        ce.add_event(self.db, "Standup", T(9), T(9, 15), recurrence={"type": "daily", "count": 3})
        self.assertEqual(len([o for o in ce.occurrences(self.db, T(0, 0, 17), T(0, 0, 30)) if o["title"] == "Standup"]), 3)                  # exactly three, then it stops
        ce.add_event(self.db, "Invoice day", T(10, 0, 30), T(11, 0, 30), recurrence={"type": "monthly"})
        self.assertEqual(len([o for o in ce.occurrences(self.db, T(0, 0, 1, 11), T(0, 0, 31, 12)) if o["title"] == "Invoice day"]), 2)           # Nov 30 and Dec 30
        ce.add_event(self.db, "Biweekly", T(9), recurrence={"type": "weekly", "weekdays": [1], "interval": 2})
        days = [o["start"].astimezone(TEHRAN).strftime("%m-%d") for o in ce.occurrences(self.db, T(0, 0, 17), T(0, 0, 2, 12)) if o["title"] == "Biweekly"]; self.assertEqual(days, ["11-17", "12-01"])

    def test_move_resize_single_or_series(self):
        one = ce.add_event(self.db, "Once", T(9), T(10)); u = ce.move_occurrence(self.db, one["id"], T(9), T(11), T(13)); self.assertEqual((u["start_utc"][:16], u["end_utc"][:16]), (T(11).isoformat()[:16], T(13).isoformat()[:16]))
        s = ce.add_event(self.db, "Weekly", T(9), T(10), recurrence={"type": "weekly", "weekdays": [1]})
        occ = ce.occurrences(self.db, T(0, 0, 17), T(0, 0, 25))[-1]                                                 # the 24th
        r = ce.move_occurrence(self.db, s["id"], occ["start"], T(14, 0, 24), T(15, 0, 24), "this"); self.assertEqual(r["recurrence"], {})                        # a one-off copy at the new time
        titles = [(o["start"].astimezone(TEHRAN).strftime("%d %H"), o["recurring"]) for o in ce.occurrences(self.db, T(0, 0, 17), T(0, 0, 26))]; self.assertEqual(titles, [("17 09", True), ("17 11", False), ("24 14", False)])                       # ("17 11" is the earlier "Once" event, moved to 11:00)
        ce.move_occurrence(self.db, s["id"], T(9), T(10), T(11), "all"); self.assertEqual(ce.get_event(self.db, s["id"])["start_utc"][:16], T(10).isoformat()[:16])
        with self.assertRaises(ce.EventError): ce.move_occurrence(self.db, one["id"], T(9), T(12), T(11))
        with self.assertRaises(KeyError): ce.get_event(self.db, "zz")

    def test_reminders_say_the_day_a_day_before_and_the_hour_two_hours_before(self):
        ce.add_event(self.db, "Client call", T(15, 0, 24), T(16, 0, 24), "meeting", link="https://meet.example/abc", reminders=[1440, 120, 0], auto_open=True)
        self.assertEqual(ce.due_reminders(self.db, T(14, 59, 22)), [])
        d = ce.due_reminders(self.db, T(15, 5, 23)); self.assertEqual([(x["kind"], x["minutes_before"]) for x in d], [("day", 1440)]); self.assertIn("فردا", d[0]["text"]); self.assertIn("15:00", d[0]["text"]); self.assertIn("Client call", d[0]["text"])
        ce.mark_fired(self.db, d); self.assertEqual(ce.due_reminders(self.db, T(16, 0, 23)), [])                                         # shown once
        h = ce.due_reminders(self.db, T(13, 1, 24)); self.assertEqual((h[0]["kind"], h[0]["minutes_before"]), ("hours", 120)); self.assertIn("2 ساعت", h[0]["text"]); self.assertIn("15:00", h[0]["text"]); self.assertFalse(h[0]["auto_open"])
        ce.mark_fired(self.db, h); s = ce.due_reminders(self.db, T(15, 0, 24)); self.assertEqual((s[0]["kind"], s[0]["auto_open"], s[0]["link"]), ("start", True, "https://meet.example/abc"))
        ce.mark_fired(self.db, s); self.assertEqual(ce.due_reminders(self.db, T(15, 2, 24)), []); self.assertEqual(ce.due_reminders(self.db, T(17, 0, 24)), [])                      # never after the event is over
        strings.set_language("en"); k, t = ce.reminder_text("Call", T(15, 0, 24), 120, T(13, 0, 24)); self.assertEqual((k, t), ("hours", "In 2 hours: Call — at 15:00"))
        self.assertTrue(ce.reminder_text("Call", T(15, 0, 24), 1440, T(15, 0, 23))[1].startswith("Tomorrow: Call")); self.assertEqual(ce.reminder_text("Call", T(15), 0)[1], "Starting now: Call")

    def test_a_reminder_missed_while_closed_still_appears_once_within_its_grace(self):
        ce.add_event(self.db, "Pitch", T(15, 0, 24), T(16, 0, 24), reminders=[1440, 15])
        self.assertEqual([x["minutes_before"] for x in ce.due_reminders(self.db, T(20, 0, 23))], [1440])                                  # 5 h late: the day reminder is still useful
        self.assertEqual(ce.due_reminders(self.db, T(2, 0, 24)), [])                                                                      # 12 h late: stale
        self.assertEqual([x["minutes_before"] for x in ce.due_reminders(self.db, T(14, 50, 24))], [15])

    def test_quick_text_becomes_an_event(self):
        now = T(12, 0, 17)                                                                                                                # Tuesday
        r = ce.parse_quick("Call with Acme next Tuesday 15:00 1h https://meet.example/x @Site remind 1d,2h", now)
        self.assertEqual((r["title"], r["start"], r["end"] - r["start"], r["link"], r["project"], r["reminders"], r["kind"]), ("Call with Acme", T(15, 0, 24), dt.timedelta(hours=1), "https://meet.example/x", "Site", [1440, 120], "meeting"))
        w = ce.parse_quick("Weekly webinar every Wed 18:00 https://zoom.example/j/1", now); self.assertEqual((w["recurrence"], w["kind"], w["start"]), ({"type": "weekly", "interval": 1, "weekdays": [2]}, "webinar", T(18, 0, 18)))
        self.assertEqual(ce.parse_quick("Dentist tomorrow 3pm 45m", now)["start"], T(15, 0, 18)); self.assertEqual(ce.parse_quick("lunch today 12:30", now)["start"], T(12, 30, 17))
        p = ce.parse_quick("جلسه با مشتری فردا ساعت 14:30 ۹۰ دقیقه", now); self.assertEqual((p["title"], p["start"], p["end"] - p["start"], p["kind"]), ("جلسه با مشتری", T(14, 30, 18), dt.timedelta(minutes=90), "meeting"))
        self.assertEqual(ce.parse_quick("report due 2026-12-01 09:00", now)["start"], T(9, 0, 1, 12)); self.assertEqual(ce.parse_quick("Gift 5 items", now)["title"], "Gift 5 items")        # a bare number is not a time
        for bad in ("   ", "tomorrow 15:00", "x 2026-13-45"):
            with self.assertRaises(ce.EventError, msg=bad): ce.parse_quick(bad, now)
        self.assertEqual(ce.parse_quick("Sync https://x.example/a.", now)["link"], "https://x.example/a")                                   # trailing punctuation is not part of the link

    def test_upcoming_lists_the_next_few(self):
        for i in range(4): ce.add_event(self.db, f"E{i}", T(9 + i, 0, 18))
        ce.add_event(self.db, "Past", T(9, 0, 10)); self.assertEqual([o["title"] for o in ce.upcoming(self.db, T(12, 0, 17), 3)], ["E0", "E1", "E2"])


class DayAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.a, self.b = Project(name="Alpha"), Project(name="Beta"); self.db.save(self.a); self.db.save(self.b)

    def log(self, title, s, e, project=None, **kw):
        kw.setdefault("billable", True)
        self.db.save(TimeEntry(title=title, start_utc=s, end_utc=e, project_id=project.id if project else None, **kw))

    def test_a_day_from_midnight_to_midnight(self):
        self.log("design", T(9), T(10, 30), self.a); self.log("code", T(11), T(12), self.b); self.log("code2", T(14), T(15, 30), self.b, billable=False); self.log("overnight", T(23, 0, 16), T(1, 0, 17), self.a)
        s = da.day_summary(self.db, dt.date(2026, 11, 17), now=T(23, 0))
        self.assertEqual((s["total_min"], [(p["project"], p["minutes"]) for p in s["by_project"]]), (300.0, [("Alpha", 150.0), ("Beta", 150.0)]))          # the overnight entry counts 1 h on the 17th (00:00-01:00) + 90 min of design for Alpha
        self.assertEqual((s["first"], s["last"], s["longest_focus_min"]), (T(0, 0, 17), T(15, 30), 90.0))
        self.assertEqual([(g["start"], g["end"], g["minutes"]) for g in s["gaps"]], [(T(1), T(9), 480.0), (T(10, 30), T(11), 30.0), (T(12), T(14), 120.0)]); self.assertEqual(s["unaccounted_min"], 630.0)
        self.assertEqual(s["hour_minutes"][0], 60.0); self.assertEqual((s["hour_minutes"][9], s["hour_minutes"][10], s["hour_minutes"][11]), (60.0, 30.0, 60.0)); self.assertEqual(s["billable_min"], 210.0)
        prev = da.day_summary(self.db, dt.date(2026, 11, 16), now=T(23, 0)); self.assertEqual(prev["total_min"], 60.0)

    def test_overlaps_are_not_double_counted_and_running_timers_count_until_now(self):
        self.log("a", T(9), T(11), self.a); self.log("b", T(10), T(12), self.b)
        s = da.day_summary(self.db, dt.date(2026, 11, 17), now=T(18)); self.assertEqual(s["total_min"], 180.0); self.assertEqual(sum(p["minutes"] for p in s["by_project"]), 240.0)       # the day is 3 h, per-project tallies keep their own 2 h each
        self.db.save(TimeEntry(title="running", start_utc=T(17), status=Status.RUNNING, project_id=self.a.id)); r = da.day_summary(self.db, dt.date(2026, 11, 17), now=T(17, 45)); self.assertEqual((r["total_min"], r["running"]), (225.0, True))

    def test_plan_versus_reality_and_events(self):
        self.db.save(TimeEntry(title="planned block", start_utc=T(9), end_utc=T(11), status=Status.PLANNED)); ce.add_event(self.db, "Client call", T(13), T(14))
        self.log("worked", T(9, 30), T(10, 30), self.a); self.log("on call", T(13, 15), T(13, 45), self.b)
        s = da.day_summary(self.db, dt.date(2026, 11, 17), now=T(20)); self.assertEqual((s["planned_min"], s["on_plan_min"], s["adherence_pct"], [e["title"] for e in s["events"]]), (180.0, 90.0, 50, ["Client call"]))
        self.assertIsNone(da.day_summary(self.db, dt.date(2026, 11, 20), now=T(20))["adherence_pct"])

    def test_range_aggregates(self):
        for d, h in ((17, 3), (18, 5), (20, 1)): self.log("w", T(9, 0, d), T(9 + h, 0, d), self.a if d != 20 else self.b)
        r = da.range_summary(self.db, dt.date(2026, 11, 16), dt.date(2026, 11, 22), now=T(23))
        self.assertEqual((r["total_min"], r["worked_days"], r["avg_per_worked_day_min"], r["best_day"]), (540.0, 3, 180.0, (dt.date(2026, 11, 18), 300.0))); self.assertEqual([(p["project"], p["pct"]) for p in r["by_project"]], [("Alpha", 88.9), ("Beta", 11.1)])
        self.assertEqual((r["weekday_minutes"][1], r["weekday_minutes"][2], r["weekday_minutes"][4]), (180.0, 300.0, 60.0)); self.assertEqual((r["peak_hour"], len(r["days"]), r["top_titles"][0]["minutes"]), (9, 7, 540.0))
        self.assertEqual(da.range_summary(Database(), dt.date(2026, 11, 16), dt.date(2026, 11, 16))["best_day"], None)


if __name__ == "__main__":
    unittest.main()


class CalendarOpsTests(unittest.TestCase):
    def setUp(self):
        from worktracker.services import calendar_ops as co
        self.co = co; self.db = Database(); self.p = Project(name="Site", color="#112233"); self.db.save(self.p)

    def test_listing_shows_events_and_planned_blocks_but_not_time_logs(self):
        ce.add_event(self.db, "Client call", T(10, 0, 18), T(11, 0, 18), "meeting"); self.co.create_item(self.db, "task", "Write brief", T(14, 0, 18), T(15, 30, 18), project_id=self.p.id)
        self.db.save(TimeEntry(title="worked", start_utc=T(9, 0, 18), end_utc=T(10, 0, 18)))                                     # a finished time log: it belongs to the actual lane
        self.db.save(TimeEntry(title="auto", start_utc=T(16, 0, 18), end_utc=T(17, 0, 18), status=Status.PLANNED, source="auto"))
        items = self.co.items_for_range(self.db, T(0, 0, 18), T(0, 0, 19)); self.assertEqual([(i["source"], i["title"]) for i in items], [("event", "Client call"), ("entry", "Write brief")])
        self.assertEqual(items[1]["project_id"], self.p.id); self.assertEqual(items[1]["end"] - items[1]["start"], dt.timedelta(minutes=90))

    def test_create_move_resize_delete_and_duplicate(self):
        t = self.co.create_item(self.db, "task", "Block", T(9), T(10)); e = self.co.create_item(self.db, "meeting", "Call", T(11), T(12), link="https://m.example/x")
        items = {i["title"]: i for i in self.co.items_for_range(self.db, T(0), T(0, 0, 18))}
        self.co.move_item(self.db, items["Block"], T(13), T(14, 30)); b = self.db.get(TimeEntry, t["id"]); self.assertEqual((b.start_utc, b.end_utc, b.estimated_min), (T(13), T(14, 30), 90))           # resized to 90 min
        self.co.move_item(self.db, items["Call"], T(15), T(16)); self.assertEqual(ce.get_event(self.db, e["id"])["start_utc"][:16], T(15).isoformat()[:16])
        d = self.co.duplicate_item(self.db, {**items["Call"], "start": T(15), "end": T(16)}); self.assertNotEqual(d["id"], e["id"]); self.assertEqual(len(self.co.items_for_range(self.db, T(0), T(0, 0, 19))), 3)
        for bad in (lambda: self.co.move_item(self.db, items["Block"], T(10), T(9)), lambda: self.co.create_item(self.db, "event", "x", T(10), T(10))):
            with self.assertRaises(self.co.CalendarError): bad()
        logged = TimeEntry(title="log", start_utc=T(8), end_utc=T(9)); self.db.save(logged)
        with self.assertRaises(self.co.CalendarError): self.co.move_item(self.db, {"source": "entry", "id": logged.id, "start": T(8), "end": T(9)}, T(10), T(11))                                         # logged time is history
        self.co.delete_item(self.db, items["Block"]); self.co.delete_item(self.db, {**items["Call"], "occ_start": T(15)}, "all"); self.assertEqual([i["title"] for i in self.co.items_for_range(self.db, T(0), T(0, 0, 19))], ["Call"])

    def test_recurring_event_delete_this_or_all(self):
        s = ce.add_event(self.db, "Weekly", T(9, 0, 17), T(10, 0, 17), recurrence={"type": "weekly", "weekdays": [1]})
        occ = [i for i in self.co.items_for_range(self.db, T(0, 0, 17), T(0, 0, 26))]; self.assertEqual(len(occ), 2)
        self.co.delete_item(self.db, occ[1]); self.assertEqual(len(self.co.items_for_range(self.db, T(0, 0, 17), T(0, 0, 26))), 1)
        self.co.delete_item(self.db, occ[0], "all"); self.assertEqual(self.co.items_for_range(self.db, T(0, 0, 17), T(0, 0, 26)), [])

    def test_project_colours_are_stable(self):
        q = Project(name="No colour", color=""); self.db.save(q); pal = ["#aa0000", "#00aa00", "#0000aa"]
        c1, c2 = self.co.project_colors(self.db, pal), self.co.project_colors(self.db, pal); self.assertEqual((c1, c1[self.p.id]), (c2, "#112233")); self.assertIn(c1[q.id], pal)


if __name__ == "__main__":
    unittest.main()
