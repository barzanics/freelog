import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import catchup as cu, routines as rt
from worktracker.ui import strings

NOW = dt.datetime(2026, 5, 3, 6, 0, tzinfo=UTC)                  # Sunday 09:30 Tehran; Friday (weekday 4) is the day off
TODAY = dt.date(2026, 5, 3)


def T(day, h=9, month=5):
    return dt.datetime(2026, month, day, h, tzinfo=TEHRAN).astimezone(UTC)


def add(db, title, due=None, prio=3, mins=60, **kw):
    e = TimeEntry(title=title, start_utc=kw.pop("start", T(1)), status=Status.PLANNED, due_utc=due, priority=prio, estimated_min=mins, **kw)
    db.save(e)
    return e


class CatchupTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.p = Project(name="Site"); self.db.save(self.p)

    def tearDown(self):
        strings.set_language("fa")

    def test_scan_finds_overdue_missed_blocks_and_postponed_but_not_the_rest(self):
        add(self.db, "late", due=T(1), project_id=self.p.id); add(self.db, "due today", due=T(3)); add(self.db, "future", due=T(9)); add(self.db, "no due")
        add(self.db, "missed block", start=T(2, 10), end_utc=T(2, 11)); add(self.db, "pushed", extra={"postponed": 1}); add(self.db, "auto log", due=T(1), source="auto")
        d = add(self.db, "done late", due=T(1)); d.column, d.status = "done", Status.DONE; self.db.save(d)
        sc = cu.scan(self.db, NOW)
        self.assertEqual({i["title"] for i in sc["items"]}, {"late", "missed block", "pushed"}); self.assertEqual(sc["counts"], {"overdue": 1, "missed_blocks": 1, "postponed": 1, "chronic": 0, "missed_routines": 0, "total": 3})
        late = next(i for i in sc["items"] if i["title"] == "late"); self.assertEqual((late["days_overdue"], late["project"], late["kind"]), (2, "Site", "overdue"))

    def test_ranking_prefers_priority_lateness_and_repeated_postponement(self):
        add(self.db, "low", due=T(2), prio=5); add(self.db, "urgent", due=T(2), prio=1); add(self.db, "ancient", due=T(20, month=4), prio=3); add(self.db, "chronic", due=T(2), prio=3, extra={"postponed": 3})
        order = [i["title"] for i in cu.scan(self.db, NOW)["items"]]; self.assertEqual(order[0], "urgent"); self.assertEqual(order[-1], "low"); self.assertLess(order.index("chronic"), order.index("low"))
        s = cu.score({"priority": 1, "important": True, "days_overdue": 20, "postponed": 9, "est_min": 10}); self.assertEqual(s, 50 + 15 + 30 + 40 + 12)           # every term is capped

    def test_recommendations(self):
        r = lambda **k: cu.recommend({"postponed": 0, "est_min": 60, "priority": 3, "days_overdue": 1, **k})
        self.assertEqual([r(), r(est_min=10), r(priority=1), r(days_overdue=9), r(postponed=3, est_min=20), r(postponed=3, est_min=240), r(postponed=4, priority=5), r(postponed=4, priority=2, est_min=60)],
                         ["schedule", "now", "today", "today", "now", "split", "drop", "today"])        # a high-priority task pushed 4 times is not dropped: it goes to today

    def test_plan_respects_capacity_skips_the_day_off_and_orders_quick_wins_first(self):
        for i, m in enumerate((120, 120, 120, 120, 120)): add(self.db, f"big{i}", due=T(1), prio=2, mins=m)
        add(self.db, "quick", due=T(2), prio=4, mins=10); add(self.db, "dropme", due=T(1), prio=5, extra={"postponed": 4}); add(self.db, "huge", due=T(1), mins=300, extra={"postponed": 3})
        p = cu.plan(self.db, NOW, capacity_min=300, days=2)
        self.assertEqual([d["date"] for d in p["days"]], [TODAY, dt.date(2026, 5, 4)]); self.assertEqual(p["days"][0]["items"][0]["title"], "quick")                      # the 10-minute win is first
        self.assertTrue(all(d["minutes"] <= d["capacity"] for d in p["days"])); self.assertEqual([i["title"] for i in p["decide"]], ["dropme"]); self.assertEqual([i["title"] for i in p["split"]], ["huge"])
        self.assertEqual([len(d["items"]) for d in p["days"]], [3, 2]); self.assertEqual(len(p["later"]), 1); self.assertFalse(p["summary"]["fits"])
        first = p["days"][0]["items"][0]; self.assertEqual((first["slot_start"], first["slot_end"] - first["slot_start"]), (T(3, 9), dt.timedelta(minutes=10)))
        sat = cu.plan(self.db, dt.datetime(2026, 5, 7, 6, tzinfo=UTC), capacity_min=300, days=3)                                                                  # Thursday: Friday is skipped
        self.assertEqual([d["date"].weekday() for d in sat["days"]], [3, 5, 6])

    def test_already_scheduled_work_reduces_the_capacity(self):
        add(self.db, "meeting", start=T(3, 10), end_utc=T(3, 13), due=None)                                   # 3 h block today
        add(self.db, "late", due=T(1), mins=120); p = cu.plan(self.db, NOW, capacity_min=300, days=1)
        self.assertEqual(p["days"][0]["capacity"], 120); self.assertEqual(len(p["days"][0]["items"]), 1)
        slot = p["days"][0]["items"][0]["slot_start"]; self.assertGreaterEqual(slot, T(3, 12))                  # placed after the existing block's time budget, not on top of 09:00

    def test_apply_plan_writes_slots_and_remembers_the_original(self):
        e = add(self.db, "late", due=T(1), mins=45); p = cu.plan(self.db, NOW, capacity_min=300, days=1); self.assertEqual(cu.apply_plan(self.db, p, NOW), 1)
        g = self.db.get(TimeEntry, e.id); self.assertEqual((g.start_utc, g.end_utc), (T(3, 9), T(3, 9) + dt.timedelta(minutes=45))); self.assertEqual(g.extra["rescheduled_from"], T(1).isoformat()); self.assertEqual(g.extra["postpone_log"][-1]["by"], "plan")
        self.assertNotIn("postponed", g.extra)                                                                  # fixing a slip is not another postponement
        self.assertEqual(cu.scan(self.db, NOW + dt.timedelta(hours=1))["counts"]["missed_blocks"], 0)

    def test_postpone_counts_logs_and_warns_from_the_third_time(self):
        e = add(self.db, "report", due=T(3, 17), start=T(3, 9), end_utc=T(3, 10), mins=60)
        r1 = cu.postpone(self.db, e.id, "tomorrow", "client call ran long", NOW); self.assertEqual((r1["count"], r1["chronic"], r1["date"]), (1, False, dt.date(2026, 5, 4)))
        g = self.db.get(TimeEntry, e.id); self.assertEqual((g.start_utc, g.end_utc, g.due_utc), (T(4, 9), T(4, 10), T(4, 17)))
        cu.postpone(self.db, e.id, "next_week", now=NOW); r3 = cu.postpone(self.db, e.id, dt.date(2026, 6, 1), now=NOW)
        self.assertEqual((r3["count"], r3["chronic"]), (3, True)); self.assertTrue(r3["advice"]); self.assertEqual(len(self.db.get(TimeEntry, e.id).extra["postpone_log"]), 3)
        fri = cu.postpone(self.db, add(self.db, "x").id, "in_3_days", now=dt.datetime(2026, 5, 6, 6, tzinfo=UTC)); self.assertEqual(fri["date"], dt.date(2026, 5, 9))      # Wednesday + 3 = Saturday, a working day here (only Friday is off)
        with self.assertRaises(ValueError): cu.postpone(self.db, e.id, "someday")
        with self.assertRaises(KeyError): cu.postpone(self.db, "zz")

    def test_drop_complete_and_stats(self):
        a, b, c = add(self.db, "a", extra={"postponed": 3, "postpone_log": [{"at": NOW.isoformat(), "from": "x", "to": "y"}]}), add(self.db, "b", extra={"postponed": 1, "postpone_log": [{"at": NOW.isoformat()}]}), add(self.db, "late", due=T(1))
        cu.complete(self.db, b.id, NOW); cu.drop(self.db, c.id, "not needed", NOW)
        self.assertEqual((self.db.get(TimeEntry, b.id).column, self.db.get(TimeEntry, c.id).column, self.db.get(TimeEntry, c.id).extra["dropped_reason"]), ("done", "cancelled", "not needed"))
        s = cu.stats(self.db, NOW); self.assertEqual((s["pushes"], s["postponed_tasks"], s["finished_pct"], s["chronic"]), (2, 2, 50, ["a"]))

    def test_missed_routines_can_be_ticked_late_or_skipped(self):
        r = rt.add(self.db, title="journal", kind="daily", time="21:00"); rt.add(self.db, title="water", kind="hourly", from_hour=9, to_hour=12)       # hourly ones are ephemeral
        m = rt.missed(self.db, NOW); self.assertEqual([(x["routine"]["title"], x["key"], x["days_late"]) for x in m], [("journal", "d:2026-05-01", 2), ("journal", "d:2026-05-02", 1)])
        rt.check(self.db, r["id"], "d:2026-05-01", NOW); rt.skip(self.db, r["id"], "d:2026-05-02", NOW); self.assertEqual(rt.missed(self.db, NOW), [])
        self.assertTrue(rt.is_skipped(self.db, r["id"], "d:2026-05-02")); self.assertFalse(rt.is_checked(self.db, r["id"], "d:2026-05-02"))
        with self.assertRaises(KeyError): rt.skip(self.db, "zz", "k")
        rt.uncheck(self.db, r["id"], "d:2026-05-01"); self.assertEqual(cu.scan(self.db, NOW)["counts"]["missed_routines"], 1)

    def test_morning_briefing_shows_once_a_day_and_summarises(self):
        self.assertFalse(cu.morning_briefing(self.db, NOW)["has_work"]); add(self.db, "late", due=T(1), mins=15); add(self.db, "chronic", due=T(2), extra={"postponed": 3})
        b = cu.morning_briefing(self.db, NOW); self.assertTrue(b["has_work"]); self.assertEqual(b["title"], "برنامه‌ی جبران امروز"); self.assertTrue(any("late" in l for l in b["lines"])); self.assertTrue(any("۲ بار" in l for l in b["lines"]))
        self.assertTrue(cu.should_show_briefing(self.db, NOW)); cu.mark_briefing_shown(self.db, NOW); self.assertFalse(cu.should_show_briefing(self.db, NOW)); self.assertTrue(cu.should_show_briefing(self.db, NOW + dt.timedelta(days=1)))
        self.db.set_setting("catchup_briefing", False); self.assertFalse(cu.should_show_briefing(self.db, NOW + dt.timedelta(days=1)))
        strings.set_language("en"); self.assertEqual(cu.morning_briefing(self.db, NOW)["title"], "Today's recovery plan")


if __name__ == "__main__":
    unittest.main()
