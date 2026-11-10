import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import HourLog, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import ledger as lg
from worktracker.services.autotrack import AutoConfig, AutoTracker
from worktracker.services.prompter import PromptConfig, Prompter


def L(h, m=0, s=0, day=2):
    return dt.datetime(2026, 5, day, h, m, s, tzinfo=TEHRAN).astimezone(UTC)


def run(led, start, minutes, state, app="Code.exe", step=5):
    """Feed one sample every ``step`` seconds for ``minutes`` minutes; returns the time after the last sample."""
    t = start
    for _ in range(int(minutes * 60 / step)):
        t += dt.timedelta(seconds=step)
        led.sample(state, app, t)
    return t


class LedgerMeasuringTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.led = lg.Ledger(self.db)

    def test_an_hour_is_split_into_engaged_and_idle_exactly(self):
        self.led.sample("active", "Code.exe", L(9))                                   # the first sample only sets the clock
        t = run(self.led, L(9), 40, lg.ACTIVE, "Code.exe"); t = run(self.led, t, 10, lg.IDLE, ""); t = run(self.led, t, 10, lg.ACTIVE, "chrome.exe")
        r = self.led.hour(lg.hour_floor(L(9, 30)))
        self.assertEqual((r["engaged_sec"], r["idle_sec"]), (50 * 60, 10 * 60)); self.assertEqual(r["apps"], [("Code.exe", 2400), ("chrome.exe", 600)])

    def test_intervals_straddling_the_hour_are_split_at_the_boundary(self):
        self.led.sample("active", "x", L(9, 59, 30)); self.led.sample("active", "x", L(10, 0, 30))
        self.assertEqual(self.led.hour(lg.hour_floor(L(9)))["engaged_sec"], 30); self.assertEqual(self.led.hour(lg.hour_floor(L(10)))["engaged_sec"], 30)

    def test_sleep_and_lock_gaps_count_as_nothing(self):
        self.led.sample("active", "x", L(9)); self.led.sample("active", "x", L(9, 0, 5)); self.led.sample("active", "x", L(11, 0, 0))     # laptop slept for 2 h
        self.led.sample("active", "x", L(11, 0, 5))
        self.assertEqual((self.led.hour(lg.hour_floor(L(9)))["engaged_sec"], self.led.hour(lg.hour_floor(L(10)))["engaged_sec"], self.led.hour(lg.hour_floor(L(11)))["engaged_sec"]), (5, 0, 5))
        self.led.sample("active", "x", L(11, 0, 1))                                                                                       # a clock that goes backwards adds nothing
        self.assertEqual(self.led.hour(lg.hour_floor(L(11)))["engaged_sec"], 5)

    def test_persistence_survives_a_restart_and_never_duplicates_rows(self):
        self.led.sample("active", "Code.exe", L(9)); run(self.led, L(9), 10, lg.ACTIVE); self.assertEqual(self.led.flush(), 1); self.assertEqual(self.led.flush(), 0)
        led2 = lg.Ledger(self.db); led2.sample("active", "Code.exe", L(9, 10)); run(led2, L(9, 10), 5, lg.ACTIVE); led2.flush()
        rows = self.db.conn.execute("SELECT * FROM hour_log").fetchall(); self.assertEqual(len(rows), 1)
        hl = HourLog.from_row(rows[0]); self.assertEqual((hl.engaged_sec, hl.apps["Code.exe"]), (900, 900)); self.assertIn("Code", hl.summary)

    def test_autotrack_flush_does_not_double_count_when_the_ledger_owns_the_numbers(self):
        self.led.sample("active", "Code.exe", L(9)); run(self.led, L(9), 20, lg.ACTIVE); self.led.flush()
        at = AutoTracker(self.db, AutoConfig(start_after=60), clock=lambda: L(9, 30)); at.write_hour_numbers = False
        for i in range(30): at.sample("Code.exe", "main.py", 0, L(9) + dt.timedelta(seconds=10 * i))
        at.clock = lambda: L(10, 5); at.sample("Code.exe", "main.py", 0, L(10, 5)); self.assertEqual(len(self.db.conn.execute("SELECT * FROM hour_log").fetchall()), 1)
        self.assertEqual(HourLog.from_row(self.db.conn.execute("SELECT * FROM hour_log").fetchone()).engaged_sec, 1200)


class LedgerUnloggedTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.led = lg.Ledger(self.db, clock=lambda: L(10, 5)); self.led.sample("active", "Code.exe", L(9))
        t = run(self.led, L(9), 50, lg.ACTIVE); run(self.led, t, 10, lg.IDLE, "")                                  # 09:00-10:00: 50 min worked

    def entry(self, a, b, **kw):
        self.db.save(TimeEntry(title="e", start_utc=a, end_utc=b, **kw))

    def test_unlogged_is_engaged_minus_the_union_of_entries(self):
        h = lg.hour_floor(L(9))
        self.assertEqual(self.led.hour(h, L(10, 5))["unlogged_sec"], 3000)
        self.entry(L(9, 0), L(9, 20)); self.entry(L(9, 10), L(9, 30))                                              # overlapping entries: union 30 min, not 40
        r = self.led.hour(h, L(10, 5)); self.assertEqual((r["logged_sec"], r["unlogged_sec"]), (1800, 1200))
        self.db.save(TimeEntry(title="planned", start_utc=L(9, 30), end_utc=L(10), status=Status.PLANNED)); self.assertEqual(self.led.hour(h, L(10, 5))["logged_sec"], 1800)   # plans are not work
        self.entry(L(8, 30), L(9, 10)); self.assertEqual(self.led.hour(h, L(10, 5))["logged_sec"], 1800)             # an entry from the previous hour only counts its part inside this one

    def test_a_running_timer_counts_until_now(self):
        self.db.save(TimeEntry(title="run", start_utc=L(9, 40), status=Status.RUNNING)); h = lg.hour_floor(L(9))
        self.assertEqual(self.led.hour(h, L(9, 50))["logged_sec"], 600); self.assertEqual(self.led.hour(h, L(10, 30))["logged_sec"], 1200)

    def test_pending_waits_for_the_grace_period_skips_answered_and_small_gaps(self):
        h = lg.hour_floor(L(9))
        self.assertEqual(self.led.pending(L(10, 1)), [])                                                           # the hour just ended: wait so its last minutes are measured
        p = self.led.pending(L(10, 3)); self.assertEqual([x["hour_start"] for x in p], [h]); self.assertEqual(p[0]["unlogged_sec"], 3000)
        self.entry(L(9, 0), L(9, 48)); self.assertEqual(self.led.pending(L(10, 3), min_unlogged_sec=300), [])      # only 2 min unlogged: do not nag
        self.assertEqual(len(self.led.pending(L(10, 3), min_unlogged_sec=60)), 1)
        self.led.mark_answered(h, "away"); self.assertEqual(self.led.pending(L(10, 3), min_unlogged_sec=60), [])
        self.assertEqual(self.led.pending(L(23, 0, day=9)), [])                                                    # outside the look-back window

    def test_free_slots_and_the_prefilled_suggestion(self):
        self.entry(L(9, 0), L(9, 20)); self.entry(L(9, 45), L(9, 50))
        slots = self.led.free_slots(lg.hour_floor(L(9)), L(10, 5)); self.assertEqual([(a, b) for a, b in slots], [(L(9, 20), L(9, 45)), (L(9, 50), L(10, 0))])      # longest first
        s = self.led.suggest(self.led.hour(lg.hour_floor(L(9)), L(10, 5)), L(10, 5))
        self.assertEqual((s["from"], s["minutes"], s["to"]), (L(9, 20), 25, L(9, 45)))                             # 30 unlogged min, but the biggest slot only holds 25
        self.assertEqual((s["engaged_min"], s["logged_min"], s["apps"][0][0], s["category"]), (50, 25, "Code.exe", "development")); self.assertIn("Code", s["title_hint"])

    def test_prompter_answer_marks_the_hour_so_it_is_not_asked_again(self):
        p = Prompter(self.db, PromptConfig(), clock=lambda: L(10, 5)); h = lg.hour_floor(L(9)); p.hour_context = h; p.show(); p.answer("logged")
        self.assertEqual(self.led.answered()[h.isoformat()], "logged"); self.assertEqual(self.led.pending(L(10, 5), min_unlogged_sec=60), []); self.assertIsNone(p.hour_context)
        p2 = Prompter(self.db, PromptConfig(), clock=lambda: L(10, 5)); p2.hour_context = lg.hour_floor(L(8)); p2.show(); p2.snooze(); self.assertNotIn(lg.hour_floor(L(8)).isoformat(), self.led.answered())   # snooze is not an answer


if __name__ == "__main__":
    unittest.main()
