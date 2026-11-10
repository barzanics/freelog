import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import routines as rt, sprints as sp
from worktracker.ui import strings


def L(h, m=0, day=2, month=5):
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class RoutineTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database()

    def tearDown(self):
        strings.set_language("fa")

    def test_validation(self):
        bad = [dict(title=""), dict(title="x", kind="never"), dict(title="x", kind="daily", time="25:00"), dict(title="x", kind="weekly", weekdays=[]), dict(title="x", kind="weekly", weekdays=[9]),
               dict(title="x", kind="monthly", day=32), dict(title="x", kind="hourly", every_hours=0), dict(title="x", kind="hourly", from_hour=18, to_hour=9),
               dict(title="x", kind="interval", every_min=1), dict(title="x", repeat_min=-5)]
        for b in bad:
            with self.assertRaises(rt.RoutineError, msg=str(b)): rt.add(self.db, **b)
        self.assertEqual(rt.all_routines(self.db), [])

    def test_daily_check_uncheck_and_persistence(self):
        r = rt.add(self.db, title="water", kind="daily", time="10:00")
        items = rt.today_items(self.db, L(9)); self.assertEqual([(i["key"], i["checked"], i["overdue"], i["upcoming"]) for i in items], [("d:2026-05-02", False, False, True)])
        self.assertTrue(rt.today_items(self.db, L(11))[0]["overdue"])
        self.assertTrue(rt.toggle(self.db, r["id"], "d:2026-05-02", L(11))); self.assertTrue(rt.today_items(self.db, L(12))[0]["checked"])
        self.assertFalse(rt.toggle(self.db, r["id"], "d:2026-05-02")); self.assertFalse(rt.today_items(self.db, L(12))[0]["checked"])
        with self.assertRaises(KeyError): rt.check(self.db, "nope", "d:x")

    def test_weekly_only_on_chosen_weekdays(self):
        rt.add(self.db, title="review", kind="weekly", weekdays=[5], time="17:00")                          # Saturday
        self.assertEqual(len(rt.today_items(self.db, L(9, day=2))), 1)                                       # 2026-05-02 is a Saturday
        self.assertEqual(rt.today_items(self.db, L(9, day=3)), [])

    def test_monthly_jalali_clamps_day_31_and_gregorian_clamps_february(self):
        rt.add(self.db, title="invoice", kind="monthly", day=31, time="09:00")
        it = rt.this_month_items(self.db, L(9, day=2))[0]                                                    # Ordibehesht has 31 days
        self.assertEqual(it["key"], "m:2026-05-21")
        it = rt.this_month_items(self.db, L(9, day=2, month=10))[0]                                          # Mehr has 30 days -> 30th (2026-10-22)
        self.assertEqual(it["key"], "m:2026-10-22")
        strings.set_language("en")
        it = rt.this_month_items(self.db, L(9, month=2, day=10))[0]; self.assertEqual(it["key"], "m:2026-02-28")   # Gregorian February clamps to 28
        self.assertEqual(rt.this_month_items(self.db, L(9, day=2))[0]["key"], "m:2026-05-31")

    def test_hourly_window_and_interval(self):
        rt.add(self.db, title="stretch", kind="hourly", every_hours=2, from_hour=9, to_hour=17)
        keys = [i["key"] for i in rt.today_items(self.db, L(8))]; self.assertEqual(keys, [f"h:2026-05-02-{h:02d}" for h in (9, 11, 13, 15, 17)])
        rt.add(self.db, title="eyes", kind="interval", every_min=20, from_hour=9, to_hour=10)
        self.assertEqual(len([i for i in rt.today_items(self.db, L(8)) if i["routine"]["title"] == "eyes"]), 4)   # 09:00 09:20 09:40 10:00
        self.assertEqual(rt.today_items(self.db, L(8))[0]["due"].hour, 9)

    def test_notifications_fire_once_then_repeat_and_stop_when_checked(self):
        r = rt.add(self.db, title="call mom", kind="daily", time="10:00", repeat_min=30)
        self.assertEqual(rt.due_notifications(self.db, L(9, 59)), [])
        d = rt.due_notifications(self.db, L(10, 1)); self.assertEqual([x["key"] for x in d], ["d:2026-05-02"]); rt.mark_notified(self.db, d, L(10, 1))
        self.assertEqual(rt.due_notifications(self.db, L(10, 20)), [])                                       # not again yet
        d2 = rt.due_notifications(self.db, L(10, 35)); self.assertEqual(len(d2), 1); rt.mark_notified(self.db, d2, L(10, 35))
        rt.check(self.db, r["id"], "d:2026-05-02", L(10, 40)); self.assertEqual(rt.due_notifications(self.db, L(11, 30)), [])
        q = rt.add(self.db, title="quiet", kind="daily", time="08:00", notify=False); self.assertEqual([x["routine"]["title"] for x in rt.due_notifications(self.db, L(9))], [])
        rt.update(self.db, q["id"], active=False); rt.add(self.db, title="once", kind="daily", time="08:00")
        d = rt.due_notifications(self.db, L(9)); rt.mark_notified(self.db, d, L(9)); self.assertEqual(rt.due_notifications(self.db, L(9, 30)), [])   # no repeat_min -> only once

    def test_streak_and_completion(self):
        r = rt.add(self.db, title="journal", kind="daily", time="21:00")
        for day in (28, 29, 30, 1):                                                                           # 4 days in a row (Apr 28..30 + May 1)
            rt.check(self.db, r["id"], f"d:2026-0{4 if day > 5 else 5}-{day:02d}", L(22))
        now = L(12, day=2)                                                                                    # today's 21:00 is not due yet: it must not break the streak
        self.assertEqual(rt.streak(self.db, r["id"], now), 4)
        rt.uncheck(self.db, r["id"], "d:2026-04-30"); self.assertEqual(rt.streak(self.db, r["id"], now), 1)
        self.assertGreater(rt.completion(self.db, r["id"], 10, now), 0); self.assertEqual(rt.completion(self.db, rt.add(self.db, title="n", kind="weekly", weekdays=[2])["id"], 1, now), 0.0)

    def test_update_delete_clean_up_history(self):
        r = rt.add(self.db, title="a", kind="daily", time="09:00"); rt.check(self.db, r["id"], "d:2026-05-02")
        u = rt.update(self.db, r["id"], title="b", time="10:30"); self.assertEqual((u["title"], u["time"], u["created"]), ("b", "10:30", r["created"]))
        with self.assertRaises(KeyError): rt.update(self.db, "zz", title="x")
        self.assertTrue(rt.delete(self.db, r["id"])); self.assertFalse(rt.delete(self.db, r["id"])); self.assertEqual(self.db.get_setting("routine_checks"), {})


class SprintTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.p = Project(name="P"); self.db.save(self.p)
        self.t = [TimeEntry(title=f"t{i}", start_utc=L(9), status=Status.PLANNED, project_id=self.p.id, estimated_min=m) for i, m in enumerate((120, 60, 180, 60))]
        for e in self.t:
            self.db.save(e)

    def make(self, **kw):
        return sp.create(self.db, self.p.id, kw.pop("name", "S1"), kw.pop("start", dt.date(2026, 5, 2)), kw.pop("days", 10), **kw)

    def test_validation_and_lifecycle(self):
        for bad in (dict(name=" "), dict(days=0), dict(days=99), dict(capacity_hours=-1)):
            with self.assertRaises(sp.SprintError): self.make(**bad)
        s = self.make(capacity_hours=6)
        with self.assertRaises(sp.SprintError): sp.start(self.db, s.id)                                       # empty
        self.assertEqual(sp.assign(self.db, s.id, [e.id for e in self.t[:3]] + ["ghost"]), 3)
        st = sp.stats(self.db, s.id); self.assertEqual((st["tasks"], st["committed_hours"], st["over_capacity"], st["capacity_pct"]), (3, 6.0, False, 100.0))
        sp.assign(self.db, s.id, [self.t[3].id]); self.assertTrue(sp.stats(self.db, s.id)["over_capacity"])
        self.assertEqual(sp.start(self.db, s.id).status, "active")
        with self.assertRaises(sp.SprintError): sp.start(self.db, s.id)
        s2 = self.make(name="S2", start=dt.date(2026, 5, 12)); sp.assign(self.db, s2.id, [])
        with self.assertRaises(sp.SprintError): sp.complete(self.db, s2.id)                                   # planning cannot be completed

    def test_only_one_active_sprint_per_project(self):
        a, b = self.make(), self.make(name="S2")
        sp.assign(self.db, a.id, [self.t[0].id]); sp.assign(self.db, b.id, [self.t[1].id]); sp.start(self.db, a.id)
        with self.assertRaises(sp.SprintError): sp.start(self.db, b.id)

    def test_complete_carry_over_modes(self):
        for mode in ("backlog", "next", "keep"):
            db = Database(); p = Project(name="P"); db.save(p)
            es = [TimeEntry(title=f"t{i}", start_utc=L(9), status=Status.PLANNED, project_id=p.id, estimated_min=60) for i in range(3)]
            for e in es: db.save(e)
            a = sp.create(db, p.id, "A", dt.date(2026, 5, 2), 7); b = sp.create(db, p.id, "B", dt.date(2026, 5, 9), 7)
            sp.assign(db, a.id, [e.id for e in es]); sp.start(db, a.id)
            done = db.get(TimeEntry, es[0].id); done.column, done.status, done.completed_at = "done", Status.DONE, L(15); db.save(done)
            if mode == "next":
                with self.assertRaises(sp.SprintError): sp.complete(db, a.id, "next", a.id)
                with self.assertRaises(sp.SprintError): sp.complete(db, a.id, "next", None)
            r = sp.complete(db, a.id, mode, b.id if mode == "next" else None)
            self.assertEqual((r["done_tasks"], r["carried"], r["velocity_hours"], r["status"]), (1, 0 if mode == "keep" else 2, 1.0, "completed"))
            left = [db.get(TimeEntry, e.id) for e in es[1:]]
            if mode == "backlog": self.assertTrue(all(e.sprint_id is None and e.column == "backlog" for e in left))
            if mode == "next": self.assertTrue(all(e.sprint_id == b.id for e in left))
            if mode == "keep": self.assertTrue(all(e.sprint_id == a.id for e in left))
            with self.assertRaises(sp.SprintError): sp.assign(db, a.id, [es[1].id])                           # completed sprints are closed

    def test_burndown_ideal_and_actual(self):
        s = self.make(days=4)                                                                                 # May 2 .. May 6
        sp.assign(self.db, s.id, [e.id for e in self.t[:2]])                                                  # 2h + 1h = 3h
        e = self.db.get(TimeEntry, self.t[0].id); e.column, e.status, e.completed_at = "done", Status.DONE, L(14, day=3); self.db.save(e)     # 2h finished on day 2
        b = sp.burndown(self.db, s.id, today=dt.date(2026, 5, 4))
        self.assertEqual((len(b["days"]), b["total_hours"]), (5, 3.0)); self.assertEqual(b["ideal"], [3.0, 2.25, 1.5, 0.75, 0.0])
        self.assertEqual(b["actual"], [3.0, 1.0, 1.0, None, None])

    def test_velocity_and_forecast(self):
        self.assertEqual((sp.average_velocity(self.db, self.p.id), sp.sprints_needed(self.db, self.p.id)), (0.0, None))
        s = self.make(days=5); sp.assign(self.db, s.id, [self.t[0].id, self.t[1].id]); sp.start(self.db, s.id)
        e = self.db.get(TimeEntry, self.t[0].id); e.column, e.status, e.completed_at = "done", Status.DONE, L(12, day=3); self.db.save(e)
        sp.complete(self.db, s.id, "backlog")
        self.assertEqual(sp.velocity_history(self.db, self.p.id), [{"sprint": "S1", "completed_hours": 2.0, "committed_hours": 3.0}])
        self.assertEqual(sp.average_velocity(self.db, self.p.id), 2.0)
        self.assertEqual(sp.stats(self.db, s.id)["committed_hours"], 3.0)                                      # snapshot survives the carry-over
        self.assertEqual(sp.sprints_needed(self.db, self.p.id), 2.5)                                          # t1(1h)+t2(3h)+t3(1h)=5h backlog / 2h per sprint
        self.assertEqual([x.name for x in sp.for_project(self.db, self.p.id)], ["S1"])


if __name__ == "__main__":
    unittest.main()
