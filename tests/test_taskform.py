import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import task_reminders as tr, taskform as tf, views
from worktracker.services.taskform import TaskValues


def L(h, m=0, day=2, month=5):
    return dt.datetime(2026, month, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


NOW = L(9)


class ValidationTests(unittest.TestCase):
    def test_valid_minimal(self):
        self.assertEqual(tf.validate(TaskValues(title="x")), {})

    def test_every_rule(self):
        cases = {"title": TaskValues(title="  "), "priority": TaskValues(title="a", priority=9), "column": TaskValues(title="a", column="zzz"),
                 "end": TaskValues(title="a", start=L(10), end=L(9)), "start": TaskValues(title="a", end=L(9)), "due": TaskValues(title="a", start=L(10), due=L(8)),
                 "estimated_min": TaskValues(title="a", estimated_min=-5), "energy": TaskValues(title="a", energy=7), "progress": TaskValues(title="a", progress=101),
                 "rate": TaskValues(title="a", rate=-1), "start_timer_now": TaskValues(title="a", column="done", start_timer_now=True),
                 "recurrence": TaskValues(title="a", recurrence={"type": "weekly", "interval": 0}, start=L(9)), "reminders": TaskValues(title="a", reminders=[-1]),
                 "checklist": TaskValues(title="a", checklist=[{"text": " "}])}
        for field, v in cases.items():
            self.assertIn(field, tf.validate(v), field)
        self.assertIn("title", tf.validate(TaskValues(title="x" * 201)))
        self.assertIn("recurrence", tf.validate(TaskValues(title="a", recurrence={"type": "weekly"})))              # needs a start time
        self.assertNotIn("due", tf.validate(TaskValues(title="a", start=L(10), due=L(8), column="done")))           # finished tasks may be overdue

    def test_time_helpers(self):
        self.assertEqual(tf.end_from_minutes(L(9), 90), L(10, 30)); self.assertEqual(tf.minutes_between(L(9), L(10, 30)), 90); self.assertEqual(tf.minutes_between(L(10), L(9)), 0)
        self.assertEqual(tf.minutes_between(None, L(9)), 0)
        n = L(9, 13)
        self.assertEqual(tf.quick_time("now", n).minute, 10); self.assertEqual(tf.quick_time("in30", n).minute, 40); self.assertEqual(tf.quick_time("in60", n).hour, 10)
        self.assertEqual(tf.quick_time("tonight", n).hour, 20); self.assertEqual(tf.quick_time("tonight", L(21)).hour, 22); t = tf.quick_time("tomorrow", n); self.assertEqual((t.day, t.hour), (3, 9))
        with self.assertRaises(ValueError): tf.quick_time("zzz")


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.p = Project(name="P"); self.db.save(self.p)

    def test_create_with_everything(self):
        other = TimeEntry(title="dep", start_utc=NOW, status=Status.PLANNED); self.db.save(other)
        v = TaskValues(title=" Build form ", description="long text", project_id=self.p.id, category="backend_development", subcategory="Laravel", priority=1, tags=["b", "a", "a", " "],
                       start=L(10), end=L(11, 30), due=L(18), estimated_min=60, energy=4, location="office", billable=True, rate=250000.0, color="#FF3D71", icon="🔥",
                       checklist=[{"text": " step 1 ", "done": True}], subtasks=["sub A", "sub B", " "], depends_on=[other.id], reminders=[10, 5, 10], notes="n",
                       attachments=["/tmp/a.pdf"], important=True, column="in_progress")
        e = tf.apply(self.db, v, now=NOW)
        g = self.db.get(TimeEntry, e.id)
        self.assertEqual((g.title, g.tags, g.priority, g.subcategory, g.reminders, g.extra["rate"]), ("Build form", ["a", "b"], 1, "Laravel", [5, 10], 250000.0))
        self.assertEqual((g.status, g.column, g.duration_sec, g.progress), (Status.PLANNED, "in_progress", 0, 0)); self.assertEqual(g.checklist, [{"text": "step 1", "done": True}])
        self.assertEqual(g.attachments, ["/tmp/a.pdf"]); self.assertTrue(g.important and g.billable)
        subs = [x.title for x in self.db.all(TimeEntry) if x.parent_id == e.id]; self.assertEqual(sorted(subs), ["sub A", "sub B"])
        self.assertEqual(self.db.conn.execute("SELECT depends_on FROM dependencies WHERE task_id=?", (e.id,)).fetchone()[0], other.id)

    def test_done_logs_time_and_progress(self):
        e = tf.apply(self.db, TaskValues(title="x", start=L(9), end=L(10, 30), column="done"), now=NOW)
        self.assertEqual((e.status, e.duration_sec, e.progress), (Status.DONE, 5400, 100)); self.assertIsNotNone(e.completed_at)
        e2 = tf.apply(self.db, tf.from_entry(self.db, e).__class__(**{**tf.from_entry(self.db, e).__dict__, "column": "review"}), entry=self.db.get(TimeEntry, e.id), now=NOW)
        self.assertEqual((e2.status, e2.completed_at), (Status.PLANNED, None))                                                       # re-opening clears completion

    def test_edit_roundtrip_and_dependency_replacement(self):
        a = TimeEntry(title="a", start_utc=NOW, status=Status.PLANNED); b = TimeEntry(title="b", start_utc=NOW, status=Status.PLANNED); c = TimeEntry(title="c", start_utc=NOW, status=Status.PLANNED)
        for x in (a, b, c): self.db.save(x)
        e = tf.apply(self.db, TaskValues(title="t", depends_on=[a.id, b.id]), now=NOW)
        v = tf.from_entry(self.db, self.db.get(TimeEntry, e.id)); self.assertEqual(sorted(v.depends_on), sorted([a.id, b.id]))
        v.depends_on = [c.id, b.id]; v.title = "t2"; tf.apply(self.db, v, entry=self.db.get(TimeEntry, e.id), now=NOW)
        self.assertEqual(sorted(r[0] for r in self.db.conn.execute("SELECT depends_on FROM dependencies WHERE task_id=?", (e.id,))), sorted([b.id, c.id]))
        self.assertEqual(len(self.db.all(TimeEntry)), 4)                                                                                # edit did not duplicate

    def test_cycle_rolls_back_everything(self):
        a = tf.apply(self.db, TaskValues(title="a"), now=NOW); b = tf.apply(self.db, TaskValues(title="b", depends_on=[a.id]), now=NOW)
        before = len(self.db.all(TimeEntry))
        with self.assertRaises(ValueError): tf.apply(self.db, TaskValues(title="a changed", depends_on=[b.id], subtasks=["s"]), entry=self.db.get(TimeEntry, a.id), now=NOW)
        self.assertEqual(len(self.db.all(TimeEntry)), before); self.assertEqual(self.db.get(TimeEntry, a.id).title, "a")               # atomic: no half-saved task / subtask

    def test_invalid_is_rejected_before_writing(self):
        with self.assertRaises(ValueError): tf.apply(self.db, TaskValues(title=""))
        self.assertEqual(self.db.all(TimeEntry), [])

    def test_recurrence_creates_copies_once(self):
        v = TaskValues(title="standup", start=L(9), end=L(9, 15), recurrence={"type": "daily", "interval": 1, "until": L(9, day=6).isoformat()})
        e = tf.apply(self.db, v, now=NOW)
        copies = [x for x in self.db.all(TimeEntry) if x.extra.get("recurs_from") == e.id]
        self.assertEqual(len(copies), 4); self.assertTrue(all(c.recurrence == {} for c in copies)); self.assertEqual(copies[0].end_utc - copies[0].start_utc, dt.timedelta(minutes=15))
        tf.apply(self.db, tf.from_entry(self.db, e), entry=self.db.get(TimeEntry, e.id), now=NOW)                                       # editing never re-expands
        self.assertEqual(len([x for x in self.db.all(TimeEntry) if x.extra.get("recurs_from") == e.id]), 4)
        w = tf.apply(self.db, TaskValues(title="biweekly", start=L(9), end=L(10), recurrence={"type": "weekly", "interval": 2, "until": L(9, day=30).isoformat()}), now=NOW)
        starts = sorted(x.start_utc for x in self.db.all(TimeEntry) if x.extra.get("recurs_from") == w.id); self.assertEqual((starts[1] - starts[0]).days, 14)

    def test_start_timer_now_stops_other_timers(self):
        old = tf.apply(self.db, TaskValues(title="old", start_timer_now=True), now=L(8)); self.assertEqual(self.db.get(TimeEntry, old.id).status, Status.RUNNING)
        new = tf.apply(self.db, TaskValues(title="new", start_timer_now=True), now=L(9))
        self.assertEqual([r.id for r in self.db.running_entries()], [new.id]); self.assertEqual(self.db.get(TimeEntry, old.id).status, Status.DONE)
        self.assertEqual(self.db.get(TimeEntry, new.id).column, "in_progress")
        again = tf.apply(self.db, tf.from_entry(self.db, self.db.get(TimeEntry, new.id)), entry=self.db.get(TimeEntry, new.id), now=L(9, 30))
        self.assertEqual(again.status, Status.RUNNING)                                                                                   # editing a running task keeps it running


class ReminderAndGridTests(unittest.TestCase):
    def test_reminders_fire_once_and_survive_restart(self):
        db = Database(); e = TimeEntry(title="call", start_utc=L(10), status=Status.PLANNED, reminders=[30, 5]); db.save(e)
        self.assertEqual(tr.due(db, L(9, 20)), [])
        d = tr.due(db, L(9, 31)); self.assertEqual([(x.title, off) for x, off in d], [("call", 30)])
        tr.mark_fired(db, d, L(9, 31)); self.assertEqual(tr.due(db, L(9, 40)), [])
        d2 = tr.due(db, L(9, 56)); self.assertEqual([off for _, off in d2], [5]); self.assertEqual(tr.due(Database(), L(9, 56)), [])
        e.start_utc = L(11); db.save(e); self.assertEqual(tr.due(db, L(10, 40))[0][1], 30)                                               # rescheduling re-arms
        e.column = "done"; db.save(e); self.assertEqual(tr.due(db, L(10, 40)), [])

    def test_overdue(self):
        db = Database(); db.save(TimeEntry(title="late", start_utc=L(9), due_utc=L(9, day=1), status=Status.PLANNED)); db.save(TimeEntry(title="ok", start_utc=L(9), due_utc=L(9, day=20), status=Status.PLANNED))
        self.assertEqual([e.title for e in tr.overdue(db, L(9))], ["late"])

    def test_jalali_grid(self):
        g = views.jalali_grid(1405, 2)                                                           # Ordibehesht 1405 starts on Tuesday (Apr 21 2026)
        self.assertTrue(all(len(w) == 7 for w in g)); flat = [c for w in g for c in w if c]
        self.assertEqual(flat, list(range(1, 32))); self.assertEqual(g[0].index(1), 3)           # Sat, Sun, Mon blank -> Tuesday is index 3
        self.assertEqual(len([c for w in views.jalali_grid(1403, 12) for c in w if c]), 30)
        self.assertEqual(views.shift_month(1405, 12, 1), (1406, 1)); self.assertEqual(views.shift_month(1405, 1, -1), (1404, 12)); self.assertEqual(views.shift_month(1405, 6, 25), (1407, 7))


if __name__ == "__main__":
    unittest.main()


class EditKeepsChildrenRegression(unittest.TestCase):
    """INSERT OR REPLACE used to delete the old row first, firing ON DELETE CASCADE/SET NULL on every child row. Never again."""

    def test_editing_a_task_keeps_dependencies_and_comments(self):
        from worktracker.core.models import Member
        from worktracker.services.team import Team
        db = Database(); a = TimeEntry(title="a", start_utc=NOW); b = TimeEntry(title="b", start_utc=NOW); db.save(a); db.save(b)
        from worktracker.services.projects import ProjectService
        ProjectService(db).add_dependency(b.id, a.id); m = Team(db).add_member("ali"); Team(db).comment(a.id, m.id, "hello")
        a.title = "a edited"; db.save(a); a.priority = 1; db.save(a)
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0], 1)
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0], 1)

    def test_editing_a_project_keeps_its_tasks(self):
        db = Database(); p = Project(name="P"); db.save(p); e = TimeEntry(title="t", start_utc=NOW, project_id=p.id); db.save(e)
        p.name = "P2"; db.save(p)
        self.assertEqual(db.get(TimeEntry, e.id).project_id, p.id)

    def test_editing_a_client_keeps_invoices_and_projects(self):
        from worktracker.core.models import Client, Invoice
        db = Database(); c = Client(name="C"); db.save(c); db.save(Invoice(client_id=c.id, items=[{"hours": 1, "rate": 5}])); p = Project(name="P", client_id=c.id); db.save(p)
        c.email = "x@y.z"; db.save(c)
        self.assertEqual(len(db.all(__import__("worktracker.core.models", fromlist=["Invoice"]).Invoice)), 1); self.assertEqual(db.get(Project, p.id).client_id, c.id)

    def test_upsert_creates_then_updates_and_audits(self):
        db = Database(); e = TimeEntry(title="x", start_utc=NOW); db.save(e); e.title = "y"; db.save(e)
        self.assertEqual(db.get(TimeEntry, e.id).title, "y"); self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0], 1)
        self.assertEqual([h["action"] for h in db.history(TimeEntry, e.id)], ["create", "update"])
