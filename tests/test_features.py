import csv
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from worktracker import sample_data
from worktracker.core.database import Database
from worktracker.core.models import (Client, Habit, Invoice, InvoiceStatus, Project, Rule, Status, TimeEntry)
from worktracker.core.persian import TEHRAN, UTC, now_utc
from worktracker.integrations import git_reader, ical, importers, webhook
from worktracker.services import search, security
from worktracker.services.automation import Automation
from worktracker.services.billing import Billing, convert
from worktracker.services.habits import HabitService, update_key_result
from worktracker.services.smart import NaiveBayes, Smart
from worktracker.services.undo import UndoManager


def T(h, day=1, m=0):
    return dt.datetime(2026, 5, day, h, m, tzinfo=UTC)


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.b = Billing(self.db)
        self.c = Client(name="C", default_rate=100, currency="USD"); self.db.save(self.c)
        self.p1 = Project(name="P1", client_id=self.c.id, rate_per_hour=200); self.p2 = Project(name="P2", client_id=self.c.id)
        for p in (self.p1, self.p2): self.db.save(p)

    def entry(self, p, hours, billable=True, **kw):
        e = TimeEntry(title="w", start_utc=T(8), end_utc=T(8) + dt.timedelta(hours=hours), project_id=p.id, billable=billable, **kw)
        self.db.save(e); return e

    def test_rate_priority(self):
        e = self.entry(self.p1, 1, extra={"rate": 999})
        self.assertEqual(self.b.rate_for(e, self.p1, self.c), 999)
        e.extra = {}
        self.assertEqual(self.b.rate_for(e, self.p1, self.c), 200)
        self.assertEqual(self.b.rate_for(e, self.p2, self.c), 100)
        self.assertEqual(self.b.rate_for(e, None, None), 0)

    def test_invoice_from_time(self):
        e1, e2, e3 = self.entry(self.p1, 2), self.entry(self.p2, 1.5), self.entry(self.p1, 5, billable=False)
        inv = self.b.create_invoice(self.c.id, tax_percent=10)
        self.assertEqual(sorted((i["desc"], i["hours"], i["rate"]) for i in inv.items), [("P1", 2.0, 200), ("P2", 1.5, 100)])
        self.assertEqual(inv.subtotal, 550); self.assertEqual(inv.total, 605); self.assertTrue(inv.number.startswith("INV-"))
        self.assertEqual(self.db.get(TimeEntry, e1.id).invoice_id, inv.id)
        self.assertIsNone(self.db.get(TimeEntry, e3.id).invoice_id)
        with self.assertRaises(ValueError): self.b.create_invoice(self.c.id)       # nothing left: no double billing
        self.assertNotEqual(self.b.next_number(), inv.number)

    def test_void_releases_entries(self):
        e = self.entry(self.p1, 1); inv = self.b.create_invoice(self.c.id)
        self.b.void(inv.id)
        self.assertIsNone(self.db.get(TimeEntry, e.id).invoice_id); self.assertIsNone(self.db.get(Invoice, inv.id))
        inv2 = self.b.create_invoice(self.c.id); self.b.pay(inv2.id, 1)
        with self.assertRaises(ValueError): self.b.void(inv2.id)

    def test_atomic_failure_leaves_no_partial(self):
        self.entry(self.p1, 1)
        orig = self.db.save
        calls = {"n": 0}
        def flaky(obj):
            calls["n"] += 1
            if isinstance(obj, TimeEntry): raise RuntimeError("boom")
            orig(obj)
        self.db.save = flaky
        with self.assertRaises(RuntimeError): self.b.create_invoice(self.c.id)
        self.db.save = orig
        self.assertEqual(self.db.all(Invoice), [])
        self.assertEqual(len(self.b.unbilled(self.c.id)), 1)

    def test_payments(self):
        self.entry(self.p1, 1); inv = self.b.create_invoice(self.c.id)
        self.assertEqual(self.b.pay(inv.id, 50).status, InvoiceStatus.PARTIAL)
        with self.assertRaises(ValueError): self.b.pay(inv.id, 9999)
        self.assertEqual(self.b.pay(inv.id, 150).status, InvoiceStatus.PAID)
        self.assertEqual(self.b.outstanding("USD"), 0)

    def test_retainer_and_currency(self):
        inv = self.b.create_retainer(self.c.id, "Monthly", 10, 50)
        self.assertEqual(inv.total, 500)
        with self.assertRaises(ValueError): self.b.create_retainer(self.c.id, "x", 0, 1)
        self.assertEqual(convert(10, "USD", "IRR", self.b.rates), 6000000)
        self.assertEqual(convert(5, "USD", "USD", {}), 5)
        with self.assertRaises(ValueError): convert(1, "XXX", "IRR", self.b.rates)
        self.b.set_rate("USD", 1000)
        self.assertEqual(self.b.outstanding(), 500 * 1000)
        with self.assertRaises(ValueError): self.b.set_rate("USD", 0)

    def test_html_escapes_and_pdf(self):
        p = Project(name="<script>x</script>", client_id=self.c.id, rate_per_hour=1); self.db.save(p)
        self.entry(p, 1); inv = self.b.create_invoice(self.c.id)
        h = self.b.to_html(inv.id)
        self.assertNotIn("<script>", h); self.assertIn("&lt;script&gt;", h); self.assertIn('dir=\'rtl\'', h)
        with tempfile.TemporaryDirectory() as d:
            self.assertGreater(self.b.to_pdf(inv.id, Path(d) / "a.pdf").stat().st_size, 500)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(); p = Project(name="WebApp"); self.db.save(p)
        mk = lambda title, h, **kw: self.db.save(TimeEntry(title=title, start_utc=T(8), end_utc=T(8) + dt.timedelta(hours=h), **kw))
        mk("Fix login bug", 3, project_id=p.id, tags=["bug"], billable=True)
        mk("Write docs", 0.25, category="docs")
        mk("Login page design", 1, tags=["design"])

    def titles(self, q): return sorted(e.title for e in search.run(self.db, q))

    def test_operators(self):
        self.assertEqual(self.titles("tag:bug"), ["Fix login bug"])
        self.assertEqual(self.titles("project:web"), ["Fix login bug"])
        self.assertEqual(self.titles(">2h"), ["Fix login bug"])
        self.assertEqual(self.titles("<30m"), ["Write docs"])
        self.assertEqual(self.titles("billable:yes"), ["Fix login bug"])
        self.assertEqual(self.titles("category:docs"), ["Write docs"])
        self.assertEqual(self.titles("tag:bug project:web >2h login"), ["Fix login bug"])
        self.assertEqual(self.titles("tag:bug tag:design"), [])

    def test_fuzzy_and_dates(self):
        self.assertEqual(self.titles("logn"), ["Fix login bug", "Login page design"])
        self.assertEqual(self.titles("after:2026-06-01"), [])
        self.assertEqual(len(self.titles("after:2026-05-01 before:2026-05-02")), 3)
        self.assertEqual(len(self.titles("after:1405/02/01")), 3)

    def test_odd_input(self):
        self.assertEqual(len(self.titles("")), 3)
        search.run(self.db, 'unbalanced "quote')   # must not raise


class SmartTests(unittest.TestCase):
    def test_naive_bayes(self):
        db = Database(); s = Smart(db)
        for t in ["fix login bug", "fix crash bug", "debug api error"]: s.learn(t, "development")
        for t in ["weekly team meeting", "client meeting call", "standup meeting"]: s.learn(t, "meeting")
        self.assertEqual(s.suggest_category("another bug in login"), "development")
        self.assertEqual(s.suggest_category("meeting with client"), "meeting")
        self.assertIsNone(s.suggest_category("zzz qqq"))
        self.assertEqual(Smart(db).suggest_category("login bug"), "development")        # persisted
        self.assertIsNone(NaiveBayes().predict("x"))

    def test_persian_tokens_and_tags_and_dupes(self):
        db = Database(); s = Smart(db)
        db.save(TimeEntry(title="رفع باگ ورود", start_utc=T(8), end_utc=T(9), tags=["باگ"]))
        db.save(TimeEntry(title="رفع باگ ورود کاربر", start_utc=T(10), end_utc=T(12)))
        self.assertEqual(s.suggest_tags("باگ ورود"), ["باگ"])
        self.assertEqual(len(s.similar("رفع باگ ورود")), 1)
        self.assertEqual(len(s.similar("رفع باگ ورود", threshold=0.75)), 2)
        self.assertEqual(s.similar("چیز دیگر"), [])
        est = s.estimate("رفع باگ ورود"); self.assertEqual(est["samples"], 2); self.assertEqual(est["avg_min"], 90.0)

    def test_anomaly_and_summary(self):
        s = Smart(Database())
        self.assertEqual(s.anomalies({dt.date(2026, 1, 1): 14 * 3600, dt.date(2026, 1, 2): 3600}), [dt.date(2026, 1, 1)])
        self.assertIn("ثبت نشده", s.daily_summary([], {}))
        txt = s.daily_summary([TimeEntry(title="کار", start_utc=T(8), end_utc=T(10))], {})
        self.assertIn("کار", txt); self.assertIn("۲ ساعت", txt)


class AutomationTests(unittest.TestCase):
    def test_rules(self):
        db, calls = Database(), []
        au = Automation(db, webhook=lambda u, p: calls.append((u, p["rule"])))
        au.add(Rule(name="long", attr="duration_sec", op=">", value=4 * 3600, action="add_tag", arg="long-task"))
        au.add(Rule(name="docs", attr="title", op="contains", value="doc", action="set_category", arg="docs"))
        au.add(Rule(name="hook", attr="tags", op="contains", value="long-task", action="webhook", arg="http://x"))
        e = TimeEntry(title="Write DOCS", start_utc=T(8), end_utc=T(14))
        fired = au.apply(e)
        self.assertEqual(fired, ["long", "docs", "hook"])
        self.assertIn("long-task", e.tags); self.assertEqual(e.category, "docs")
        self.assertEqual(db.get(TimeEntry, e.id).tags, ["long-task"])
        self.assertEqual(calls, [("http://x", "hook")])     # tag was added earlier in the same pass
        short = TimeEntry(title="x", start_utc=T(8), end_utc=T(9))
        self.assertEqual(au.apply(short), [])

    def test_validation_and_failing_webhook(self):
        db = Database()
        au = Automation(db, webhook=lambda u, p: 1 / 0)
        with self.assertRaises(ValueError): au.add(Rule(name="bad", attr="nope"))
        with self.assertRaises(ValueError): au.add(Rule(name="bad", op="~"))
        au.add(Rule(name="h", attr="priority", op=">=", value=1, action="webhook", arg="http://x"))
        self.assertEqual(au.apply(TimeEntry(title="x", start_utc=T(8))), ["h"])   # no exception
        db.all(Rule)[0].enabled = False


class HabitTests(unittest.TestCase):
    def test_habits_and_goals(self):
        from worktracker.core.models import Goal
        db = Database(); hs = HabitService(db)
        h = Habit(name="read", target_per_week=4); db.save(h)
        today = dt.date(2026, 5, 5)  # Tuesday; Persian week starts Saturday (May 2)
        for i in range(3):
            hs.check_in(h.id, today - dt.timedelta(days=i))
        hs.check_in(h.id, today)                                    # idempotent
        self.assertEqual(len(db.get(Habit, h.id).log), 3)
        self.assertEqual(hs.streak(h.id, today), (3, 3))
        self.assertAlmostEqual(hs.week_completion(h.id, today), 0.75)
        hs.undo_check_in(h.id, today); self.assertEqual(hs.streak(h.id, today)[1], 2)
        with self.assertRaises(ValueError): hs.check_in(h.id, dt.date(2999, 1, 1))
        with self.assertRaises(KeyError): hs.check_in("zz")
        g = Goal(name="g", key_results=[{"name": "k", "target": 10, "current": 0}]); db.save(g)
        self.assertEqual(update_key_result(db, g.id, 0, 5).progress, 0.5)
        with self.assertRaises(IndexError): update_key_result(db, g.id, 3, 1)


class SecurityTests(unittest.TestCase):
    def test_roundtrip_wrong_password_tamper(self):
        blob = security.encrypt_bytes("pw", b"secret data")
        self.assertEqual(security.decrypt_bytes("pw", blob), b"secret data")
        self.assertNotEqual(blob, security.encrypt_bytes("pw", b"secret data"))      # random salt/nonce
        with self.assertRaises(security.DecryptError): security.decrypt_bytes("bad", blob)
        t = bytearray(blob); t[-1] ^= 1
        with self.assertRaises(security.DecryptError): security.decrypt_bytes("pw", bytes(t))
        with self.assertRaises(security.DecryptError): security.decrypt_bytes("pw", b"junk")
        with self.assertRaises(ValueError): security.encrypt_bytes("", b"x")
        self.assertEqual(security.decrypt_text("pw", security.encrypt_text("pw", "یادداشت خصوصی")), "یادداشت خصوصی")

    def test_encrypted_backup_restore(self):
        with tempfile.TemporaryDirectory() as d:
            db = Database(Path(d) / "a.db"); db.save(Project(name="مهم"))
            f = security.encrypted_backup(db, Path(d) / "b.wtbackup", "pw")
            self.assertNotIn(b"SQLite format", f.read_bytes()[:20])
            db2 = security.restore_backup(f, Path(d) / "r.db", "pw")
            self.assertEqual([p.name for p in db2.all(Project)], ["مهم"])
            with self.assertRaises(FileExistsError): security.restore_backup(f, Path(d) / "r.db", "pw")
            with self.assertRaises(security.DecryptError): security.restore_backup(f, Path(d) / "r2.db", "no")
            self.assertFalse((Path(d) / "r2.db").exists())
            db.close(); db2.close()


class UndoTests(unittest.TestCase):
    def test_undo_redo(self):
        db = Database(); u = UndoManager(db)
        p = Project(name="a"); u.save(p)
        p.name = "b"; u.save(p)
        u.undo(); self.assertEqual(db.get(Project, p.id).name, "a")
        u.undo(); self.assertIsNone(db.get(Project, p.id))
        self.assertFalse(u.undo())
        u.redo(); u.redo(); self.assertEqual(db.get(Project, p.id).name, "b")
        u.delete(p); self.assertIsNone(db.get(Project, p.id))
        u.undo(); self.assertEqual(db.get(Project, p.id).name, "b")
        u.undo(); u.save(Project(name="new")); self.assertFalse(u.can_redo)


class IntegrationTests(unittest.TestCase):
    def test_ics(self):
        e = TimeEntry(title="جلسه; مهم, فوری\nخط دوم " + "x" * 100, start_utc=T(8), end_utc=T(9), tags=["a,b"], notes="n")
        txt = ical.build_ics([e, TimeEntry(title="running", start_utc=T(8))])
        self.assertEqual(txt.count("BEGIN:VEVENT"), 1)
        self.assertIn("DTSTART:20260501T080000Z", txt)
        for line in txt.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 76)
        unfolded = txt.replace("\r\n ", "")
        self.assertIn("\\;", unfolded); self.assertIn("\\n", unfolded)

    def test_webhook(self):
        self.assertFalse(webhook.post_json("file:///etc/passwd", {}))
        self.assertFalse(webhook.post_json("notaurl", {}))
        class R:
            status = 204
            def __enter__(s): return s
            def __exit__(s, *a): return False
        self.assertTrue(webhook.post_json("http://x.test", {"a": now_utc()}, opener=lambda req, timeout: R()))
        def boom(req, timeout): raise OSError("offline")
        self.assertFalse(webhook.post_json("http://x.test", {}, opener=boom))   # offline = quiet failure

    def test_import_toggl_clockify(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.csv"
            with f.open("w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh)
                w.writerow(["Project", "Description", "Billable", "Start date", "Start time", "End date", "End time", "Tags"])
                w.writerow(["Alpha", "کار ۱", "Yes", "2026-05-01", "09:00:00", "2026-05-01", "10:30:00", "a, b"])
                w.writerow(["Alpha", "bad", "No", "garbage", "x", "x", "x", ""])
                w.writerow(["", "reversed", "No", "2026-05-01", "10:00:00", "2026-05-01", "09:00:00", ""])
            db = Database(); st = importers.import_toggl(db, f)
            self.assertEqual(st, {"entries": 1, "skipped": 2, "projects": 1})
            e = db.all(TimeEntry)[0]
            self.assertEqual((e.duration_sec, e.tags, e.billable, e.start_utc.hour, e.start_utc.minute), (5400, ["a", "b"], True, 5, 30))
            g = Path(d) / "c.csv"
            g.write_text("Project,Description,Billable,Start Date,Start Time,End Date,End Time,Tags\nAlpha,x,No,05/02/2026,09:00 AM,05/02/2026,10:00 AM,\n", encoding="utf-8")
            self.assertEqual(importers.import_clockify(db, g)["entries"], 1)
            self.assertEqual(len(db.all(Project)), 1)       # project re-used

    def test_git(self):
        out = "\n".join(f"{h}\x1f{int(t.timestamp())}\x1f{m}" for h, t, m in [
            ("a" * 40, T(8), "first"), ("b" * 40, T(9), "second"), ("c" * 40, T(20), "evening")])
        es = git_reader.commits_to_entries("/repo", runner=lambda r, s: out)
        self.assertEqual(len(es), 2)
        self.assertEqual((es[0].title, es[0].duration_sec), ("first (+1 commits)", 75 * 60))
        self.assertEqual(es[1].duration_sec, 15 * 60)
        self.assertEqual(git_reader.commits_to_entries("/r", runner=lambda r, s: ""), [])


class SampleDataTests(unittest.TestCase):
    def test_counts_and_determinism(self):
        a, b = Database(), Database()
        self.assertEqual(sample_data.generate(a, seed=3), {"clients": 5, "projects": 10, "entries": 500, "invoices": 20})
        sample_data.generate(b, seed=3)
        self.assertEqual([e.title for e in a.all(TimeEntry, "start_utc")][:20], [e.title for e in b.all(TimeEntry, "start_utc")][:20])
        self.assertEqual((len(a.all(Client)), len(a.all(Project)), len(a.all(TimeEntry)), len(a.all(Invoice))), (5, 10, 500, 20))
        from worktracker.services.analytics import Analytics
        self.assertGreater(Analytics(a).year_summary(1404).total_hours, 100)


if __name__ == "__main__":
    unittest.main()
