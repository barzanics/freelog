import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import (Dependency, Goal, Milestone, Project, ProjectStatus, Sprint, Status, TimeEntry)
from worktracker.core.persian import TEHRAN, UTC, now_utc
from worktracker.services.planner import Planner, WorkingHours, eisenhower, free_slots, merge
from worktracker.services.pomodoro import IDLE, LONG, SHORT, WORK, Pomodoro, PomodoroConfig
from worktracker.services.projects import ProjectService


class Clock:
    def __init__(self):
        self.t = dt.datetime(2026, 5, 2, 9, 0, tzinfo=UTC)
    def __call__(self):
        return self.t
    def adv(self, **kw):
        self.t += dt.timedelta(**kw)


class PomodoroTests(unittest.TestCase):
    def setUp(self):
        self.db, self.clk = Database(), Clock()
        self.pm = Pomodoro(self.db, PomodoroConfig(work_min=25, short_min=5, long_min=15, cycles_before_long=2, auto_start_next=True), self.clk)

    def test_full_cycle(self):
        self.pm.start(); self.assertEqual(self.pm.phase, WORK)
        self.clk.adv(minutes=24, seconds=59); self.assertIsNone(self.pm.tick())
        self.clk.adv(seconds=1); self.assertEqual(self.pm.tick(), SHORT)
        self.clk.adv(minutes=5); self.assertEqual(self.pm.tick(), WORK)
        self.clk.adv(minutes=25); self.assertEqual(self.pm.tick(), LONG)   # 2nd work -> long
        self.assertEqual((self.pm.total_completed, self.pm.completed_work), (2, 0))
        self.clk.adv(minutes=15); self.assertEqual(self.pm.tick(), WORK)

    def test_pause_resume(self):
        self.pm.start(); self.clk.adv(minutes=10); self.pm.pause()
        self.clk.adv(hours=3)
        self.assertEqual(self.pm.remaining(), 15 * 60)
        self.assertIsNone(self.pm.tick())
        self.pm.resume(); self.clk.adv(minutes=15)
        self.assertEqual(self.pm.tick(), SHORT)

    def test_invalid_transitions(self):
        with self.assertRaises(RuntimeError): self.pm.pause()
        with self.assertRaises(RuntimeError): self.pm.resume()
        with self.assertRaises(RuntimeError): self.pm.skip()
        self.pm.start()
        with self.assertRaises(RuntimeError): self.pm.start()
        with self.assertRaises(ValueError): PomodoroConfig(work_min=0)

    def test_skip_work_does_not_count(self):
        self.pm.start(); self.clk.adv(minutes=3)
        self.assertEqual(self.pm.skip(), SHORT)
        self.assertEqual(self.pm.total_completed, 0)

    def test_manual_mode_goes_idle(self):
        pm = Pomodoro(self.db, PomodoroConfig(auto_start_next=False), self.clk)
        pm.start(); self.clk.adv(minutes=25)
        self.assertEqual(pm.tick(), SHORT); self.assertEqual(pm.phase, IDLE)

    def test_persist_and_restore_after_restart(self):
        self.pm.start(); self.clk.adv(minutes=10)
        pm2 = Pomodoro(self.db, clock=self.clk)
        self.assertTrue(pm2.restore())
        self.assertEqual((pm2.phase, pm2.remaining()), (WORK, 15 * 60))
        self.clk.adv(minutes=20)           # app was closed while the phase ended
        self.assertEqual(pm2.tick(), SHORT)

    def test_fill_level(self):
        self.pm.start(); self.assertEqual(self.pm.fill_level(), 1.0)
        self.clk.adv(minutes=5); self.assertAlmostEqual(self.pm.fill_level(), 0.8)
        self.pm.reset(); self.assertEqual(self.pm.fill_level(), 0.0)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.ps = ProjectService(self.db)
        self.p = Project(name="P", estimated_hours=10, budget=1000, rate_per_hour=100); self.db.save(self.p)

    def task(self, title, **kw):
        kw.setdefault("status", Status.PLANNED)
        e = TimeEntry(title=title, start_utc=now_utc(), project_id=self.p.id, **kw); self.db.save(e); return e

    def test_kanban_and_blocking(self):
        a, b = self.task("a", estimated_min=480), self.task("b", estimated_min=480)
        self.ps.add_dependency(b.id, a.id)
        with self.assertRaises(ValueError): self.ps.move(b.id, "in_progress")
        self.ps.move(a.id, "in_progress"); self.ps.move(a.id, "done")
        self.assertEqual(self.db.get(TimeEntry, a.id).status, Status.DONE)
        self.ps.move(b.id, "in_progress")
        self.assertEqual([t.title for t in self.ps.board()["in_progress"]], ["b"])
        with self.assertRaises(ValueError): self.ps.move(b.id, "nope")
        with self.assertRaises(KeyError): self.ps.move("zzz", "done")

    def test_cycle_rejected(self):
        a, b, c = self.task("a"), self.task("b"), self.task("c")
        self.ps.add_dependency(b.id, a.id); self.ps.add_dependency(c.id, b.id)
        with self.assertRaises(ValueError): self.ps.add_dependency(a.id, c.id)
        with self.assertRaises(ValueError): Dependency(task_id=a.id, depends_on=a.id)
        with self.assertRaises(ValueError): Dependency(task_id="x", depends_on="y", kind="weird")

    def test_gantt(self):
        a, b, c = self.task("a", estimated_min=960), self.task("b", estimated_min=480), self.task("c", estimated_min=480)
        self.ps.add_dependency(b.id, a.id)
        self.ps.add_dependency(c.id, a.id, lag_days=2)
        g = self.ps.gantt(self.p.id, dt.date(2026, 1, 1))
        self.assertEqual(g[a.id], (dt.date(2026, 1, 1), dt.date(2026, 1, 2)))
        self.assertEqual(g[b.id][0], dt.date(2026, 1, 3))
        self.assertEqual(g[c.id][0], dt.date(2026, 1, 5))

    def test_subtasks(self):
        t = self.task("t")
        s1, s2 = self.ps.add_subtask(t.id, "s1"), self.ps.add_subtask(t.id, "s2")
        self.assertEqual(self.ps.progress(t.id), 0.0)
        self.ps.move(s1.id, "done")
        self.assertEqual(self.ps.progress(t.id), 0.5)
        with self.assertRaises(ValueError): self.ps.add_subtask(s1.id, "deep")

    def test_milestones(self):
        m1, m2 = Milestone(project_id=self.p.id, name="m1"), Milestone(project_id=self.p.id, name="m2")
        self.db.save(m1); self.db.save(m2)
        self.ps.complete_milestone(m1.id)
        self.assertEqual(self.ps.milestone_progress(self.p.id), (1, 2))

    clk0 = dt.datetime(2026, 1, 1, tzinfo=UTC)

    def test_sprint_and_velocity(self):
        s = Sprint(project_id=self.p.id, name="S1", start=now_utc(), end=now_utc() + dt.timedelta(days=14), capacity_hours=5, status="completed")
        self.db.save(s)
        self.task("x", sprint_id=s.id, estimated_min=240)
        self.task("y", sprint_id=s.id, estimated_min=120, status=Status.DONE)
        st = self.ps.sprint_stats(s.id)
        self.assertEqual((st["committed_hours"], st["completed_hours"], st["over_capacity"], st["burn_pct"]), (6.0, 2.0, 1.0, 33.3))
        self.assertEqual(self.ps.velocity(self.p.id), 2.0)
        with self.assertRaises(ValueError): Sprint(project_id="p", name="x", start=self.clk0, end=self.clk0)

    def test_health(self):
        self.assertEqual(self.ps.health(self.p.id), "on_track")
        s = now_utc() - dt.timedelta(hours=11)
        self.db.save(TimeEntry(title="big", start_utc=s, end_utc=s + dt.timedelta(hours=11), project_id=self.p.id))
        self.assertEqual(self.ps.health(self.p.id), "off_track")        # hours>est (2) + budget>1.0 (2)
        self.p.status = ProjectStatus.COMPLETED; self.db.save(self.p)
        self.assertEqual(self.ps.health(self.p.id), "on_track")

    def test_health_overdue_without_milestones(self):
        self.p.deadline = now_utc() - dt.timedelta(days=1); self.db.save(self.p)
        self.assertEqual(self.ps.health(self.p.id), "off_track")


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.pl = Planner(self.db, WorkingHours(dt.time(9), dt.time(17), (4,)))
        self.sat = dt.date(2026, 5, 2)  # Saturday

    def at(self, h, m=0, day=None):
        return dt.datetime.combine(day or self.sat, dt.time(h, m), tzinfo=TEHRAN)

    def test_merge_and_free(self):
        self.assertEqual(merge([(1, 3), (2, 5), (7, 8)]), [(1, 5), (7, 8)])
        w = (self.at(9), self.at(17))
        fs = free_slots(w, [(self.at(10), self.at(11)), (self.at(10, 30), self.at(12)), (self.at(8), self.at(9, 30))])
        self.assertEqual(fs, [(self.at(9, 30), self.at(10)), (self.at(12), self.at(17))])
        self.assertEqual(free_slots(w, []), [w])

    def test_off_day(self):
        self.assertIsNone(self.pl.day_window(dt.date(2026, 5, 1)))  # Friday
        self.assertEqual(self.pl.day_free(dt.date(2026, 5, 1)), [])

    def test_time_block_overlap(self):
        a = TimeEntry(title="a", start_utc=now_utc(), status=Status.PLANNED, estimated_min=60)
        b = TimeEntry(title="b", start_utc=now_utc(), status=Status.PLANNED, estimated_min=60)
        self.db.save(a); self.db.save(b)
        self.pl.time_block(a.id, self.at(10))
        with self.assertRaises(ValueError): self.pl.time_block(b.id, self.at(10, 30))
        self.pl.time_block(b.id, self.at(11))
        self.pl.time_block(a.id, self.at(9, 30))        # moving a into free space is fine
        with self.assertRaises(ValueError): self.pl.time_block(a.id, self.at(10, 15))   # but not onto b
        self.assertEqual(len(self.pl.day_free(self.sat)), 3)

    def test_auto_schedule_priority_deadline_and_skip_friday(self):
        now = self.at(8, day=dt.date(2026, 4, 30))
        t1 = TimeEntry(title="low", start_utc=now_utc(), estimated_min=240, priority=5, status=Status.PLANNED)
        t2 = TimeEntry(title="due", start_utc=now_utc(), estimated_min=240, priority=5, status=Status.PLANNED, due_utc=now_utc() + dt.timedelta(days=1))
        t3 = TimeEntry(title="huge", start_utc=now_utc(), estimated_min=60 * 20, priority=1, status=Status.PLANNED)
        res = self.pl.auto_schedule([t1, t2, t3], dt.date(2026, 4, 30), now=now)   # starts Thursday
        self.assertEqual(res[t2.id], self.at(9, day=dt.date(2026, 4, 30)))
        self.assertGreater(res[t1.id], res[t2.id])
        self.assertIsNone(res[t3.id])                                               # cannot fit any single day
        for v in res.values():
            if v: self.assertNotEqual(v.weekday(), 4)

    def test_buffers_respected(self):
        a = TimeEntry(title="m", start_utc=self.at(9).astimezone(UTC), end_utc=self.at(10).astimezone(UTC), status=Status.PLANNED)
        self.db.save(a)
        t = TimeEntry(title="t", start_utc=now_utc(), estimated_min=30, status=Status.PLANNED)
        res = self.pl.auto_schedule([t], self.sat, buffer_min=15)
        self.assertEqual(res[t.id], self.at(10, 15))

    def test_estimate_learning(self):
        for _ in range(3):
            s = now_utc()
            self.db.save(TimeEntry(title="x", start_utc=s, end_utc=s + dt.timedelta(minutes=120), estimated_min=60, category="dev"))
        self.assertEqual(self.pl.estimate_accuracy(), {"dev": 2.0})
        self.assertEqual(self.pl.suggest_estimate("dev", 30), 60)
        self.assertEqual(self.pl.suggest_estimate("unknown", 30), 30)

    def test_eisenhower(self):
        now = now_utc()
        mk = lambda due, imp: TimeEntry(title="x", start_utc=now, due_utc=due, important=imp)
        soon, later = now + dt.timedelta(hours=5), now + dt.timedelta(days=30)
        self.assertEqual([eisenhower(mk(soon, True), now), eisenhower(mk(later, True), now), eisenhower(mk(soon, False), now),
                          eisenhower(mk(None, False), now)], ["do", "schedule", "delegate", "eliminate"])

    def test_goal_progress(self):
        g = Goal(name="g", key_results=[{"name": "a", "target": 10, "current": 5}, {"name": "b", "target": 4, "current": 9}, {"name": "c", "target": 0, "current": 1}])
        self.assertAlmostEqual(g.progress, (0.5 + 1 + 0) / 3)
        self.assertEqual(Goal(name="e").progress, 0.0)


if __name__ == "__main__":
    unittest.main()
