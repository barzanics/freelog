import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Status, TimeEntry
from worktracker.core.persian import UTC, now_utc
from worktracker.integrations.google_tasks import GoogleTasksSync
from worktracker.services import lists as L
from worktracker.ui import strings


class ListTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.a = L.ensure_default(self.db)["id"]; self.b = L.add_list(self.db, "Work")["id"]

    def titles(self, lid, done=True):
        return [e.title for e in L.tasks(self.db, lid, include_done=done)]

    def test_lists_crud_and_rules(self):
        self.assertEqual(L.ensure_default(self.db)["id"], "default"); self.assertEqual([l["name"] for l in L.lists(self.db)], ["کارهای من", "Work"])
        for bad in ("", "  ", "x" * 61, "work"):
            with self.assertRaises(L.ListError): L.add_list(self.db, bad)
        L.rename_list(self.db, self.b, "Office")
        with self.assertRaises(L.ListError): L.rename_list(self.db, self.b, "کارهای من")
        with self.assertRaises(KeyError): L.rename_list(self.db, "zz", "x")
        c = L.add_list(self.db, "C"); L.reorder_lists(self.db, [c["id"], self.a]); self.assertEqual([l["name"] for l in L.lists(self.db)], ["C", "کارهای من", "Office"])

    def test_new_tasks_go_on_top_and_validate(self):
        for t in ("one", "two", "three"): L.add_task(self.db, self.a, t)
        self.assertEqual(self.titles(self.a), ["three", "two", "one"])
        with self.assertRaises(L.ListError): L.add_task(self.db, self.a, " ")
        with self.assertRaises(L.ListError): L.add_task(self.db, "nope", "x")
        e = L.add_task(self.db, self.a, "with due", due=dt.date(2026, 5, 2), notes=" n ", starred=True)
        self.assertEqual((e.description, e.important, e.extra["list"], e.source), ("n", True, self.a, "list")); self.assertEqual(e.due_utc.astimezone().date() if False else e.due_utc.date(), dt.date(2026, 5, 1) if e.due_utc.hour < 20 else e.due_utc.date())

    def test_tick_moves_task_down_and_untick_restores(self):
        x = L.add_task(self.db, self.a, "x"); y = L.add_task(self.db, self.a, "y")
        self.assertTrue(L.toggle(self.db, x.id)); self.assertEqual(self.titles(self.a), ["y", "x"]); self.assertEqual(L.counts(self.db, self.a), (1, 1))
        e = self.db.get(TimeEntry, x.id); self.assertEqual((e.column, e.status, e.progress), ("done", Status.DONE, 100)); self.assertIsNotNone(e.completed_at)
        self.assertFalse(L.toggle(self.db, x.id)); e = self.db.get(TimeEntry, x.id); self.assertEqual((e.column, e.status, e.completed_at), ("backlog", Status.PLANNED, None))
        with self.assertRaises(KeyError): L.toggle(self.db, "zz")

    def test_reorder_inside_a_list(self):
        t = [L.add_task(self.db, self.a, n) for n in "abcd"]                                  # order: d c b a
        L.reorder(self.db, self.a, [t[0].id, t[2].id])                                         # a, c first; the others keep their relative order
        self.assertEqual(self.titles(self.a), ["a", "c", "d", "b"]); L.reorder(self.db, self.a, ["ghost"] + [x.id for x in t])
        self.assertEqual(self.titles(self.a), ["a", "b", "c", "d"])

    def test_drag_between_lists_at_a_position_with_subtasks(self):
        a1, a2 = L.add_task(self.db, self.a, "a1"), L.add_task(self.db, self.a, "a2")
        b1 = L.add_task(self.db, self.b, "b1"); b2 = L.add_task(self.db, self.b, "b2")        # b2 b1
        sub = L.add_task(self.db, self.a, "child", parent_id=a1.id)
        L.move(self.db, a1.id, self.b, 1)
        self.assertEqual(self.titles(self.b), ["b2", "a1", "b1"]); self.assertEqual(self.titles(self.a), ["a2"])
        self.assertEqual(self.db.get(TimeEntry, sub.id).extra["list"], self.b)                 # the sub-task travelled with its parent
        L.move(self.db, a2.id, self.b, 99); self.assertEqual(self.titles(self.b)[-1], "a2")   # index beyond the end -> last
        L.move(self.db, sub.id, self.a, 0); self.assertIsNone(self.db.get(TimeEntry, sub.id).parent_id); self.assertEqual(self.titles(self.a), ["child"])
        with self.assertRaises(L.ListError): L.move(self.db, a1.id, "nope")
        ranks = [e.rank for e in L.tasks(self.db, self.b, include_done=False)]; self.assertEqual(ranks, sorted(ranks))

    def test_indent_outdent_star_sort_clear(self):
        t = [L.add_task(self.db, self.a, n) for n in "abc"]                                    # c b a
        self.assertFalse(L.indent(self.db, t[2].id))                                           # top task cannot be indented
        self.assertTrue(L.indent(self.db, t[1].id)); self.assertEqual(self.db.get(TimeEntry, t[1].id).parent_id, t[2].id); self.assertEqual(self.titles(self.a), ["c", "a"])
        self.assertFalse(L.indent(self.db, t[1].id)); self.assertTrue(L.outdent(self.db, t[1].id)); self.assertFalse(L.outdent(self.db, t[1].id))
        self.assertTrue(L.star(self.db, t[0].id)); self.assertFalse(L.star(self.db, t[0].id))
        for n, d in zip(t, (dt.date(2026, 6, 1), None, dt.date(2026, 5, 1))): L.update_task(self.db, n.id, due=d)
        L.sort_by_due(self.db, self.a); self.assertEqual(self.titles(self.a), ["c", "a", "b"])
        L.toggle(self.db, t[0].id); self.assertEqual(L.clear_completed(self.db, self.a), 1); self.assertEqual(L.counts(self.db, self.a), (2, 0))
        with self.assertRaises(L.ListError): L.update_task(self.db, t[1].id, title="  ")
        L.update_task(self.db, t[1].id, title="B2", notes="note", due=None); e = self.db.get(TimeEntry, t[1].id); self.assertEqual((e.title, e.description, e.due_utc), ("B2", "note", None))

    def test_delete_list_moves_or_deletes_tasks(self):
        L.add_task(self.db, self.b, "x"); L.add_task(self.db, self.b, "y")
        self.assertEqual(L.delete_list(self.db, self.b, move_to=self.a), 2); self.assertEqual(len(self.titles(self.a)), 2)
        d = L.add_list(self.db, "D"); L.add_task(self.db, d["id"], "gone"); self.assertEqual(L.delete_list(self.db, d["id"]), 1)
        self.assertIsNone(self.db.conn.execute("SELECT 1 FROM entries WHERE title='gone'").fetchone())
        with self.assertRaises(L.ListError): L.delete_list(self.db, self.a, move_to=self.a)
        self.assertEqual(len(L.lists(self.db)), 1)
        with self.assertRaises(L.ListError): L.delete_list(self.db, L.lists(self.db)[0]["id"])                     # the last list stays


# ---------------------------------------------------------------- a faithful in-memory Google Tasks API
class Req:
    def __init__(self, fn): self.fn = fn
    def execute(self): return self.fn()


class FakeTasks:
    def __init__(self, page=100):
        self.tl, self.tk, self.n, self.t, self.page, self.fail_patch = {}, {}, 0, 0, page, set()
    def stamp(self):
        self.t += 1; return (dt.datetime(2030, 1, 1, tzinfo=UTC) + dt.timedelta(seconds=self.t)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    def _id(self, p): self.n += 1; return f"{p}{self.n}"
    def tasklists(self):
        f = self
        class TL:
            def list(s, maxResults=100, pageToken=None): return Req(lambda: {"items": list(f.tl.values())})
            def insert(s, body): 
                def run():
                    i = f._id("L"); f.tl[i] = {"id": i, "title": body["title"]}; f.tk[i] = {}; return f.tl[i]
                return Req(run)
        return TL()
    def tasks(self):
        f = self
        class T:
            def list(s, tasklist, showCompleted=True, showHidden=True, maxResults=100, pageToken=None):
                def run():
                    items = list(f.tk[tasklist].values()); start = int(pageToken or 0); chunk = items[start:start + f.page]
                    return {"items": chunk, **({"nextPageToken": str(start + f.page)} if start + f.page < len(items) else {})}
                return Req(run)
            def insert(s, tasklist, body, parent=None):
                def run():
                    i = f._id("T"); t = {"id": i, "updated": f.stamp(), "position": f"{f.n:08d}", **body}
                    if parent: t["parent"] = parent
                    f.tk[tasklist][i] = t; return t
                return Req(run)
            def patch(s, tasklist, task, body):
                def run():
                    if task in f.fail_patch: raise RuntimeError("500 boom")
                    if task not in f.tk[tasklist]: raise RuntimeError("404 not found")
                    t = f.tk[tasklist][task]; t.update({k: v for k, v in body.items() if v is not None}); t["updated"] = f.stamp()
                    if body.get("status") == "needsAction": t.pop("completed", None)
                    return t
                return Req(run)
            def delete(s, tasklist, task):
                def run():
                    if task not in f.tk.get(tasklist, {}): raise RuntimeError("404 not found")
                    del f.tk[tasklist][task]
                return Req(run)
        return T()
    # test helpers
    def add_list(self, title): i = self._id("L"); self.tl[i] = {"id": i, "title": title}; self.tk[i] = {}; return i
    def add_task(self, lid, title, **kw): i = self._id("T"); self.tk[lid][i] = {"id": i, "title": title, "updated": self.stamp(), "status": "needsAction", "position": f"{self.n:08d}", **kw}; return i
    def edit(self, lid, tid, **kw): self.tk[lid][tid].update(kw); self.tk[lid][tid]["updated"] = self.stamp()


class GTasksTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa"); self.db = Database(); self.api = FakeTasks(); self.sync = GoogleTasksSync(self.db, self.api, clock=lambda: dt.datetime(2030, 6, 1, tzinfo=UTC))
        self.a = L.ensure_default(self.db)["id"]

    def remote_titles(self, lid): return sorted(t["title"] for t in self.api.tk[lid].values())

    def test_first_sync_pushes_lists_and_tasks_and_second_is_a_no_op(self):
        t1 = L.add_task(self.db, self.a, "write", due=dt.date(2026, 5, 2), notes="details"); t2 = L.add_task(self.db, self.a, "done one"); L.toggle(self.db, t2.id)
        rep = self.sync.sync()
        self.assertEqual((rep.lists_created_remote, rep.pushed_new, rep.errors), (1, 2, []))
        gl = L.lists(self.db)[0]["gid"]; remote = {t["title"]: t for t in self.api.tk[gl].values()}
        self.assertEqual((remote["write"]["notes"], remote["write"]["due"], remote["write"]["status"], remote["done one"]["status"]), ("details", "2026-05-02T00:00:00.000Z", "needsAction", "completed"))
        again = self.sync.sync(); self.assertEqual(again.changes, 0)                                  # idempotent: nothing is re-sent or re-created
        self.assertEqual(len(self.api.tk[gl]), 2); self.assertIsNotNone(self.db.get_setting("gtasks_last_sync"))

    def test_remote_changes_are_pulled_including_new_lists_and_hierarchy(self):
        lid = self.api.add_list("Shopping"); p = self.api.add_task(lid, "groceries", notes="n", due="2026-05-03T00:00:00.000Z"); self.api.add_task(lid, "milk", parent=p); self.api.add_task(lid, "paid", status="completed")
        rep = self.sync.sync()
        self.assertEqual((rep.lists_created_local, rep.pulled_new), (1, 3))
        loc = next(l for l in L.lists(self.db) if l["name"] == "Shopping"); ts = {e.title: e for e in L._all_in(self.db, loc["id"], with_children=True)}
        self.assertEqual((ts["groceries"].description, ts["milk"].parent_id, L.is_done(ts["paid"])), ("n", ts["groceries"].id, True)); self.assertEqual(ts["groceries"].due_utc.date().isoformat() in ("2026-05-02", "2026-05-03"), True)
        self.assertEqual(self.sync.sync().changes, 0)

    def test_same_named_lists_are_linked_not_duplicated(self):
        rl = self.api.add_list("کارهای من"); self.api.add_task(rl, "remote task")
        self.sync.sync(); self.assertEqual(len(L.lists(self.db)), 1); self.assertEqual(L.lists(self.db)[0]["gid"], rl); self.assertEqual(len(self.api.tl), 1)
        self.assertEqual([e.title for e in L.tasks(self.db, self.a)], ["remote task"])

    def test_edits_flow_both_ways_and_newer_wins_a_conflict(self):
        t = L.add_task(self.db, self.a, "orig"); self.sync.sync(); gl = L.lists(self.db)[0]["gid"]; gid = self.db.get(TimeEntry, t.id).extra["gid"]
        L.update_task(self.db, t.id, title="local edit"); rep = self.sync.sync()                      # local -> remote
        self.assertEqual((rep.pushed_updated, self.api.tk[gl][gid]["title"]), (1, "local edit"))
        self.api.edit(gl, gid, title="remote edit"); rep = self.sync.sync()                           # remote -> local
        self.assertEqual((rep.pulled_updated, self.db.get(TimeEntry, t.id).title), (1, "remote edit")); self.assertEqual(self.sync.sync().changes, 0)
        e = self.db.get(TimeEntry, t.id); e.title = "both A"; e.updated_at = dt.datetime(2029, 1, 1, tzinfo=UTC); self.db.save(e, touch=False); self.api.edit(gl, gid, title="both B")      # remote stamp (2030) is newer
        self.sync.sync(); self.assertEqual(self.db.get(TimeEntry, t.id).title, "both B")
        e = self.db.get(TimeEntry, t.id); e.title = "both C"; e.updated_at = dt.datetime(2031, 1, 1, tzinfo=UTC); self.db.save(e, touch=False); self.api.edit(gl, gid, title="both D")        # local is newer
        self.sync.sync(); self.assertEqual((self.db.get(TimeEntry, t.id).title, self.api.tk[gl][gid]["title"]), ("both C", "both C"))

    def test_completion_syncs_both_ways(self):
        t = L.add_task(self.db, self.a, "tick me"); self.sync.sync(); gl = L.lists(self.db)[0]["gid"]; gid = self.db.get(TimeEntry, t.id).extra["gid"]
        L.toggle(self.db, t.id); self.sync.sync(); self.assertEqual(self.api.tk[gl][gid]["status"], "completed")
        L.toggle(self.db, t.id); self.sync.sync(); self.assertEqual(self.api.tk[gl][gid]["status"], "needsAction"); self.assertNotIn("completed", self.api.tk[gl][gid])
        self.api.edit(gl, gid, status="completed"); self.sync.sync(); self.assertTrue(L.is_done(self.db.get(TimeEntry, t.id)))

    def test_deletions_both_ways_and_404_is_harmless(self):
        x, y = L.add_task(self.db, self.a, "x"), L.add_task(self.db, self.a, "y"); self.sync.sync(); gl = L.lists(self.db)[0]["gid"]
        gx, gy = (self.db.get(TimeEntry, i).extra["gid"] for i in (x.id, y.id))
        L.delete_task(self.db, x.id); rep = self.sync.sync(); self.assertEqual((rep.deleted_remote, gx in self.api.tk[gl]), (1, False)); self.assertEqual(self.db.get_setting("gtasks_deleted"), [])
        del self.api.tk[gl][gy]; rep = self.sync.sync()                                                # removed on Google -> hidden here
        self.assertEqual(rep.hidden_local, 1); self.assertEqual(L.tasks(self.db, self.a), []); self.assertEqual(self.sync.sync().changes, 0)
        z = L.add_task(self.db, self.a, "z"); self.sync.sync(); gz = self.db.get(TimeEntry, z.id).extra["gid"]; del self.api.tk[gl][gz]; L.delete_task(self.db, z.id)
        self.assertEqual(self.sync.sync().errors, []); self.assertEqual(self.db.get_setting("gtasks_deleted"), [])        # already gone remotely: tombstone cleared, no error

    def test_one_failing_task_does_not_stop_the_others(self):
        a, b = L.add_task(self.db, self.a, "a"), L.add_task(self.db, self.a, "b"); self.sync.sync(); gl = L.lists(self.db)[0]["gid"]
        L.update_task(self.db, a.id, title="a2"); L.update_task(self.db, b.id, title="b2"); self.api.fail_patch.add(self.db.get(TimeEntry, a.id).extra["gid"])
        rep = self.sync.sync(); self.assertEqual((rep.pushed_updated, len(rep.errors)), (1, 1)); self.assertIn("b2", self.remote_titles(gl))
        self.assertIsNone(self.db.get_setting("gtasks_last_sync", None) if False else None)
        self.api.fail_patch.clear(); self.assertEqual(self.sync.sync().pushed_updated, 1); self.assertIn("a2", self.remote_titles(gl))        # retried next time

    def test_pagination_and_unavailable(self):
        lid = self.api.add_list("Big")
        for i in range(25): self.api.add_task(lid, f"t{i}")
        self.api.page = 10; self.assertEqual(self.sync.sync().pulled_new, 25)
        with self.assertRaises(RuntimeError): GoogleTasksSync(self.db, None).sync()
        self.assertFalse(GoogleTasksSync(self.db, None).available)
        from worktracker.integrations.google_tasks import build_tasks_service
        import tempfile; self.assertIsNone(build_tasks_service(tempfile.gettempdir() + "/definitely-no-credentials-here"))


if __name__ == "__main__":
    unittest.main()
