import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import calendar_events as ce, checkin as ck, ledger as lg
from worktracker.ui import strings


def T(h, m=0, day=4, month=5):                                   # Monday May 4 2026, Tehran time (Friday is the day off)
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


def measure(db, hour_h, minutes, app="Code.exe", day=4):
    led = lg.Ledger(db); start = T(hour_h, 0, day); led.sample("active", app, start)
    for i in range(1, minutes * 12 + 1): led.sample("active", app, start + dt.timedelta(seconds=5 * i))
    led.flush()


class CheckinTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.p = Project(name="Site"); self.db.save(self.p)

    def tearDown(self):
        strings.set_language("fa")

    def test_due_only_at_work_hours_when_present_unanswered_and_not_snoozed(self):
        now = T(14, 1); h = lg.hour_floor(now)
        self.assertEqual(ck.due(self.db, now), h); self.assertIsNone(ck.due(self.db, now, engaged_recently=False))                                                # you are away: do not interrupt
        self.assertIsNone(ck.due(self.db, T(14, 1, 8)))                                                                                                                # Friday May 8: day off
        self.db.set_setting("prompt_config", {"quiet_start": 13, "quiet_end": 15}); self.assertIsNone(ck.due(self.db, now)); self.db.set_setting("prompt_config", {})
        ck.set_config(self.db, enabled=False); self.assertIsNone(ck.due(self.db, now)); ck.set_config(self.db, enabled=True)
        self.assertTrue(ck.snooze(self.db, h, now)); self.assertIsNone(ck.due(self.db, T(14, 5))); self.assertEqual(ck.due(self.db, T(14, 12)), h)                         # back after 10 minutes
        self.assertEqual(ck.snoozes_left(self.db, h), 1); self.assertTrue(ck.snooze(self.db, h, T(14, 12))); self.assertFalse(ck.snooze(self.db, h, T(14, 25)))        # the third snooze is refused: forced
        with self.assertRaises(ck.CheckinError): ck.set_config(self.db, mode="sometimes")
        with self.assertRaises(ck.CheckinError): ck.set_config(self.db, bogus=1)

    def test_both_halves_are_required_and_everything_is_applied_atomically(self):
        measure(self.db, 13, 50); now = T(14, 1); h = lg.hour_floor(now)
        with self.assertRaises(ck.CheckinError): ck.submit(self.db, h, new_plans=[{"title": "x"}], now=now)                                       # 50 unlogged minutes: say what you did
        with self.assertRaises(ck.CheckinError): ck.submit(self.db, h, logged={"title": "coding", "minutes": 50}, now=now)                       # ... and plan the next hour
        before = len(self.db.all(TimeEntry))
        r = ck.submit(self.db, h, logged={"title": "Homepage coding", "minutes": 50, "project_id": self.p.id}, new_plans=[{"title": "Write proposal", "minutes": 30, "project_id": self.p.id}, {"title": "Reply to emails"}], now=now)
        self.assertEqual((r["logged"], r["planned"]), (1, 2)); self.assertEqual(len(self.db.all(TimeEntry)), before + 3)
        plans = sorted((e for e in self.db.all(TimeEntry) if e.source == "checkin"), key=lambda e: e.start_utc)
        self.assertEqual([(e.title, e.start_utc, e.end_utc) for e in plans], [("Write proposal", T(14), T(14, 30)), ("Reply to emails", T(14, 30), T(14, 50))])      # back-to-back, default 20 min
        self.assertIsNone(ck.due(self.db, T(14, 40))); self.assertEqual(ck.due(self.db, T(15, 1)), lg.hour_floor(T(15, 1)))                                          # answered; the next hour asks again
        self.assertEqual(lg.Ledger(self.db).answered()[lg.hour_floor(T(13)).isoformat()], "logged")

    def test_a_free_hour_away_and_modes(self):
        measure(self.db, 13, 40); h = lg.hour_floor(T(14, 1))
        r = ck.submit(self.db, h, away=True, free_hour=True, now=T(14, 1)); self.assertEqual((r["away"], r["planned"], r["logged"]), (True, 0, 0)); self.assertEqual(lg.Ledger(self.db).answered()[lg.hour_floor(T(13)).isoformat()], "away")
        db = Database(); ck.set_config(db, mode="future"); measure(db, 13, 50)
        self.assertEqual(ck.submit(db, lg.hour_floor(T(14, 1)), new_plans=[{"title": "Plan only"}], now=T(14, 1))["planned"], 1)                      # 'future' mode never asks about the past
        db2 = Database(); ck.set_config(db2, mode="past"); measure(db2, 13, 50); self.assertEqual(ck.submit(db2, lg.hour_floor(T(14, 1)), logged={"title": "did it", "minutes": 50}, now=T(14, 1))["logged"], 1)

    def test_last_hours_plan_can_be_ticked_done_or_carried_over(self):
        h13 = lg.hour_floor(T(13, 1)); ck.submit(self.db, h13, free_hour=True, new_plans=[{"title": "Draft contract", "minutes": 30}, {"title": "Call vendor", "minutes": 20}], now=T(13, 1))
        pr = ck.past_report(self.db, lg.hour_floor(T(14, 1)), T(14, 1)); self.assertEqual([e.title for e in pr["planned"]], ["Draft contract", "Call vendor"]); self.assertTrue(pr["needs_answer"])
        done, carry = pr["planned"][0].id, pr["planned"][1].id
        r = ck.submit(self.db, lg.hour_floor(T(14, 1)), done_ids=[done], carry_ids=[carry], free_hour=True, now=T(14, 1)); self.assertEqual((r["done"], r["carried"]), (1, 1))
        a, b = self.db.get(TimeEntry, done), self.db.get(TimeEntry, carry); self.assertEqual((a.status, a.column), (Status.DONE, "done")); self.assertEqual((b.start_utc, b.extra["postponed"]), (T(14), 1))      # the unfinished one moves into this hour
        s = ck.stats(self.db, T(15)); self.assertEqual((s["answered"], s["planned_blocks"], s["kept"], s["follow_through_pct"]), (2, 2, 1, 50))

    def test_candidates_mix_slipped_work_events_and_the_last_task(self):
        late = TimeEntry(title="Late invoice", start_utc=T(9, 0, 1), status=Status.PLANNED, due_utc=T(9, 0, 1), estimated_min=45, project_id=self.p.id); self.db.save(late)
        self.db.save(TimeEntry(title="Due today", start_utc=T(8), status=Status.PLANNED, due_utc=T(17), estimated_min=90)); self.db.save(TimeEntry(title="Previous work", start_utc=T(11), end_utc=T(12)))
        ce.add_event(self.db, "Client call", T(15, 0), T(16, 0), "meeting")
        c = ck.next_hour_candidates(self.db, lg.hour_floor(T(14, 1)), T(14, 1))
        self.assertEqual([(x["title"], x["why"]) for x in c["candidates"]], [("Late invoice", "عقب‌افتاده"), ("Due today", "موعد امروز"), ("Previous work", "ادامه‌ی کار قبلی")]); self.assertEqual(c["candidates"][1]["minutes"], 60)
        self.assertEqual([e["title"] for e in c["events"]], ["Client call"])
        r = ck.submit(self.db, lg.hour_floor(T(14, 1)), picked=[{"id": late.id, "minutes": 45}, {"id": None, "title": "Previous work", "minutes": 30}], now=T(14, 1)); self.assertEqual(r["planned"], 2)
        g = self.db.get(TimeEntry, late.id); self.assertEqual((g.start_utc, g.end_utc, g.extra["checkin"]), (T(14), T(14, 45), lg.hour_floor(T(14, 1)).isoformat()))

    def test_break_is_suggested_after_a_long_run_and_streak_counts(self):
        for hh in (11, 12, 13): measure(self.db, hh, 55)
        self.assertEqual(ck.needs_break(self.db, lg.hour_floor(T(14, 1)), T(14, 1)), 180); measure(self.db, 10, 55); self.assertEqual(ck.needs_break(self.db, lg.hour_floor(T(14, 1)), T(14, 1)), 240)
        self.assertEqual(ck.needs_break(self.db, lg.hour_floor(T(11, 1)), T(11, 1)), 0); r = ck.submit(self.db, lg.hour_floor(T(14, 1)), free_hour=True, add_break=True, away=True, now=T(14, 1)); self.assertEqual(r["planned"], 1)
        self.assertTrue(any(e.extra.get("break") for e in self.db.all(TimeEntry)))
        for hh in (15, 16, 17): ck.submit(self.db, lg.hour_floor(T(hh, 1)), free_hour=True, away=True, now=T(hh, 1))
        self.assertEqual(ck.streak(self.db), 4); ck.submit(self.db, lg.hour_floor(T(23, 1)), free_hour=True, away=True, now=T(23, 1)); self.assertEqual(ck.streak(self.db), 1)       # a 6-hour hole breaks it


if __name__ == "__main__":
    unittest.main()
