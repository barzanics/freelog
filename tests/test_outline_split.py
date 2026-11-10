import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Milestone, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import lists as L, outline, project_split as ps
from worktracker.ui import strings


class OutlineTests(unittest.TestCase):
    def test_markdown_check_lists_bullets_numbers_and_nesting(self):
        r = outline.parse("- [ ] write #docs @web 45m\n- [x] done one\n  - [ ] child a\n  - [x] child b\n1. numbered\n* bullet\n• dot\n[ ] bare box")
        self.assertEqual([n.title for n in r], ["write", "done one", "numbered", "bullet", "dot", "bare box"])
        self.assertEqual((r[0].tags, r[0].project, r[0].minutes, r[0].done, r[1].done), (["docs"], "web", 45, False, True))
        self.assertEqual([(c.title, c.done) for c in r[1].children], [("child a", False), ("child b", True)])

    def test_headings_tabs_deep_nesting_flattened_and_junk(self):
        r = outline.parse("# Phase 1\n\t- task\n\t\t- sub\n\t\t\t- subsub\n# Phase 2\n- t2", max_depth=3)
        self.assertEqual([x.title for x in r], ["Phase 1", "Phase 2"]); self.assertTrue(r[0].heading)
        self.assertEqual([c.title for c in r[0].children], ["task"]); self.assertEqual([c.title for c in r[0].children[0].children], ["sub", "subsub"])      # level 4 flattened into level 3
        self.assertEqual([c.title for c in r[1].children], ["t2"])
        self.assertEqual(outline.parse("\n   \n#only_a_tag\n- [ ] \n"), [])                                                                                      # nothing usable
        self.assertEqual(len(outline.parse("\n".join(f"- t{i}" for i in range(900)), max_lines=500)), 500)

    def test_due_star_and_persian_input(self):
        r = outline.parse("!pay rent d:2026-05-03\n۱. تماس با مشتری #کار ۳۰m due:۱۴۰۵/۰۲/۱۳\n- bad date d:2026-13-45")
        self.assertEqual((r[0].starred, r[0].due), (True, dt.date(2026, 5, 3))); self.assertEqual((r[1].title, r[1].tags, r[1].minutes, r[1].due), ("تماس با مشتری", ["کار"], 30, dt.date(2026, 5, 3)))
        self.assertIsNone(r[2].due)


class BulkAddTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.a = L.ensure_default(self.db)["id"]; self.p = Project(name="WebApp"); self.db.save(self.p)

    def test_pasted_check_list_becomes_tasks_subtasks_done_and_keeps_order(self):
        L.add_task(self.db, self.a, "existing")
        made = L.bulk_add(self.db, self.a, "- [ ] first @web 30m #x\n- [x] second\n    - [ ] sub1\n    - [x] sub2\n- [ ] third")
        self.assertEqual(len(made), 5)
        self.assertEqual([e.title for e in L.tasks(self.db, self.a)], ["first", "third", "existing", "second"])                       # open ones in pasted order on top, done below
        first = next(e for e in made if e.title == "first"); self.assertEqual((first.project_id, first.estimated_min, first.tags), (self.p.id, 30, ["x"]))
        subs = L.children(self.db, next(e.id for e in made if e.title == "second")); self.assertEqual([(s.title, L.is_done(s)) for s in subs], [("sub1", False), ("sub2", True)])
        self.assertTrue(all(e.extra["list"] == self.a for e in made))
        with self.assertRaises(L.ListError): L.bulk_add(self.db, self.a, "  \n  ")
        with self.assertRaises(L.ListError): L.bulk_add(self.db, "nope", "- x")


class SplitTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.p = Project(name="Book"); self.db.save(self.p)
        self.text = "# Research\n- [x] Interview 3h\n- [ ] Outline 2h\n    - [ ] chapter list\n# Writing\n- [ ] Draft 20h\n"

    def test_preview_counts(self):
        self.assertEqual(ps.preview(self.text), {"mode": "phases", "phases": 2, "tasks": 3, "subtasks": 1, "estimate_hours": 25.0})
        self.assertEqual(ps.preview("- a\n- b\n  - c")["mode"], "tasks")
        for k in ps.TEMPLATES:
            for lang in ("fa", "en"):
                strings.set_language(lang); pv = ps.preview(ps.template(k)); self.assertGreater(pv["phases"], 1); self.assertGreater(pv["tasks"], 3)

    def test_apply_creates_phases_tasks_subtasks_atomically(self):
        r = ps.apply_outline(self.db, self.p.id, self.text, start=dt.date(2026, 5, 1), phase_days=10, now=dt.datetime(2026, 5, 1, tzinfo=UTC))
        self.assertEqual((r["phases"], r["tasks"], r["subtasks"], r["estimate_hours"]), (2, 3, 1, 25.0))
        ms = sorted((Milestone.from_row(x) for x in self.db.conn.execute("SELECT * FROM milestones")), key=lambda m: m.due)
        self.assertEqual([m.name for m in ms], ["Research", "Writing"]); self.assertEqual((ms[1].due - ms[0].due).days, 10)
        prog = ps.phase_progress(self.db, self.p.id); self.assertEqual([(x["name"], x["tasks"], x["done"], x["pct"], x["hours"]) for x in prog], [("Research", 2, 1, 50.0, 5.0), ("Writing", 1, 0, 0.0, 20.0)])
        sub = self.db.conn.execute("SELECT * FROM entries WHERE title='chapter list'").fetchone(); self.assertIsNotNone(TimeEntry.from_row(sub).parent_id)
        before = len(self.db.all(TimeEntry))
        with self.assertRaises(ps.SplitError): ps.apply_outline(self.db, "nope", self.text)
        with self.assertRaises(ps.SplitError): ps.apply_outline(self.db, self.p.id, "   ")
        with self.assertRaises(ps.SplitError): ps.apply_outline(self.db, self.p.id, self.text, phase_days=0)
        self.assertEqual(len(self.db.all(TimeEntry)), before)

    def test_flat_outline_makes_tasks_without_phases(self):
        r = ps.apply_outline(self.db, self.p.id, "- a 1h\n- b\n  - b1"); self.assertEqual((r["mode"], r["phases"], r["tasks"], r["subtasks"]), ("tasks", 0, 2, 1))
        self.assertEqual([x["name"] for x in ps.phase_progress(self.db, self.p.id)], ["بدون فاز"])

    def test_split_a_task_shares_the_estimate(self):
        t = TimeEntry(title="Big", start_utc=dt.datetime(2026, 5, 1, tzinfo=UTC), status=Status.PLANNED, project_id=self.p.id, estimated_min=100, priority=2, tags=["t"]); self.db.save(t)
        parts = ps.split_task(self.db, t.id, ["one", "two", "three"]); self.assertEqual([e.estimated_min for e in parts], [34, 33, 33])
        self.assertTrue(all(e.parent_id == t.id and e.priority == 2 and "t" in e.tags for e in parts))
        mixed = ps.split_task(self.db, t.id, ["fixed 60m", "rest"]); self.assertEqual([e.estimated_min for e in mixed], [60, 100])
        with self.assertRaises(ps.SplitError): ps.split_task(self.db, parts[0].id, ["x"])
        with self.assertRaises(ps.SplitError): ps.split_task(self.db, t.id, ["  ", ""])
        with self.assertRaises(ps.SplitError): ps.split_task(self.db, t.id, ["p"] * 51)
        with self.assertRaises(KeyError): ps.split_task(self.db, "nope", ["x"])

    def test_split_a_project_moves_tasks_with_their_subtasks(self):
        ps.apply_outline(self.db, self.p.id, self.text)
        ids = [r[0] for r in self.db.conn.execute("SELECT id FROM entries WHERE title IN ('Outline','Draft')")]
        new = ps.split_project(self.db, self.p.id, ids, "  Book 2 ")
        self.assertEqual(new.name, "Book 2")
        moved = {r[0] for r in self.db.conn.execute("SELECT title FROM entries WHERE project_id=?", (new.id,))}; self.assertEqual(moved, {"Outline", "chapter list", "Draft"})
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM entries WHERE project_id=?", (self.p.id,)).fetchone()[0], 1)
        self.assertTrue(all("phase" not in TimeEntry.from_row(r).extra for r in self.db.conn.execute("SELECT * FROM entries WHERE project_id=?", (new.id,))))
        with self.assertRaises(ps.SplitError): ps.split_project(self.db, self.p.id, ids, "x")                  # those tasks are not in the source project any more
        with self.assertRaises(ps.SplitError): ps.split_project(self.db, self.p.id, [], "x")
        with self.assertRaises(ps.SplitError): ps.split_project(self.db, self.p.id, ["z"], " ")


if __name__ == "__main__":
    unittest.main()
