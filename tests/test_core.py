import datetime as dt
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worktracker.core.database import Database, import_legacy
from worktracker.core.models import (Client, Invoice, InvoiceStatus, Project, Status, TimeEntry)
from worktracker.core.persian import UTC, now_utc


def T(h, m=0, day=1):
    return dt.datetime(2026, 5, day, h, m, tzinfo=UTC)


class ModelTests(unittest.TestCase):
    def test_roundtrip_json_fields(self):
        e = TimeEntry(title="کار", start_utc=T(8), end_utc=T(9), tags=["a", "فارسی"], checklist=[{"t": "x", "done": True}],
                      extra={"k": [1, 2]}, billable=True)
        back = TimeEntry.from_row(e.to_row())
        self.assertEqual(back, e)
        self.assertIsInstance(e.to_row()["tags"], str)  # never a Python list in the DB row

    def test_validation(self):
        with self.assertRaises(ValueError):
            TimeEntry(title="x", start_utc=T(9), end_utc=T(8))
        with self.assertRaises(ValueError):
            TimeEntry(title="x", start_utc=T(9), energy=9)
        with self.assertRaises(ValueError):
            TimeEntry(title="x", start_utc=dt.datetime(2026, 1, 1)).to_row()  # naive rejected

    def test_variance(self):
        e = TimeEntry(title="x", start_utc=T(8), end_utc=T(10), estimated_min=60)
        self.assertEqual(e.variance_min, 60)
        self.assertIsNone(TimeEntry(title="x", start_utc=T(8)).variance_min)

    def test_invoice_math(self):
        inv = Invoice(client_id="c", items=[{"hours": 2, "rate": 100}, {"hours": 1.5, "rate": 200}],
                      tax_percent=10, discount=50)
        self.assertEqual(inv.subtotal, 500)
        self.assertEqual(inv.total, 495)
        inv.apply_payment(100)
        self.assertEqual((inv.status, inv.balance), (InvoiceStatus.PARTIAL, 395))
        inv.apply_payment(395)
        self.assertEqual((inv.status, inv.balance), (InvoiceStatus.PAID, 0))
        with self.assertRaises(ValueError):
            inv.apply_payment(0)

    def test_invoice_discount_over_subtotal(self):
        self.assertEqual(Invoice(client_id="c", items=[{"hours": 1, "rate": 10}], discount=99).total, 0)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_wal_and_version(self):
        self.assertEqual(self.db.conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.db.version, 5)
        self.db.migrate()  # idempotent
        self.assertEqual(self.db.version, 5)

    def test_crud_all_entities(self):
        c = Client(name="مشتری", tags=["vip"])
        p = Project(name="پروژه", client_id=c.id, tags=["x"])
        e = TimeEntry(title="t", start_utc=T(8), end_utc=T(9), project_id=p.id)
        i = Invoice(client_id=c.id, items=[{"hours": 1, "rate": 5}])
        for o in (c, p, e, i):
            self.db.save(o)
        self.assertEqual(self.db.get(Client, c.id).tags, ["vip"])
        self.assertEqual(self.db.get(Invoice, i.id).items, [{"hours": 1, "rate": 5}])
        p.name = "new"
        self.db.save(p)
        self.assertEqual(self.db.get(Project, p.id).name, "new")
        self.assertEqual(len(self.db.all(Project)), 1)
        self.assertTrue(self.db.delete(TimeEntry, e.id))
        self.assertFalse(self.db.delete(TimeEntry, e.id))

    def test_fk_behaviour(self):
        c = Client(name="c"); p = Project(name="p", client_id=c.id)
        e = TimeEntry(title="t", start_utc=T(8), end_utc=T(9), project_id=p.id)
        i = Invoice(client_id=c.id)
        for o in (c, p, e, i):
            self.db.save(o)
        self.db.delete(Project, p.id)
        self.assertIsNone(self.db.get(TimeEntry, e.id).project_id)       # SET NULL
        self.db.delete(Client, c.id)
        self.assertIsNone(self.db.get(Invoice, i.id))                      # CASCADE
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save(TimeEntry(title="x", start_utc=T(8), project_id="missing"))

    def test_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.db.transaction():
                self.db.save(Client(name="a"))
                raise RuntimeError
        # nested save committed inside; verify explicit raw rollback instead
        with self.assertRaises(RuntimeError):
            with self.db.transaction() as c:
                c.execute("INSERT INTO settings VALUES ('k','1')")
                raise RuntimeError
        self.assertIsNone(self.db.conn.execute("SELECT 1 FROM settings WHERE key='k'").fetchone())

    def test_search_escapes(self):
        self.db.save(TimeEntry(title="100% done", start_utc=T(8), end_utc=T(9)))
        self.db.save(TimeEntry(title="other", start_utc=T(9), end_utc=T(10)))
        self.assertEqual(len(self.db.search("%")), 1)
        self.assertEqual(len(self.db.search("_")), 0)
        self.assertEqual(len(self.db.search("OTHER")), 1)

    def test_settings(self):
        self.assertEqual(self.db.get_setting("x", 5), 5)
        self.db.set_setting("x", {"a": [1, "ب"]})
        self.assertEqual(self.db.get_setting("x"), {"a": [1, "ب"]})

    def test_backup_restore_identical(self):
        self.db.save(Project(name="p"))
        b = self.db.backup(Path(self.tmp.name) / "b" / "bk.db")
        self.db.save(Project(name="later"))
        restored = Database(b)
        self.assertEqual([p.name for p in restored.all(Project)], ["p"])
        self.assertTrue(restored.integrity_ok())
        restored.close()

    def test_rotate_backups(self):
        for _ in range(5):
            self.db.rotate_backups(Path(self.tmp.name) / "r", keep=3)
        self.assertEqual(len(list((Path(self.tmp.name) / "r").glob("*.db"))), 3)

    def test_audit(self):
        c = Client(name="a")
        self.db.save(c); self.db.save(c); self.db.delete(Client, c.id)
        acts = [r[0] for r in self.db.conn.execute("SELECT action FROM audit_log ORDER BY id")]
        self.assertEqual(acts, ["create", "update", "delete"])

    def test_bad_order_rejected(self):
        with self.assertRaises(ValueError):
            self.db.all(Project, "name; DROP TABLE projects")

    def test_10k_entries_query_fast(self):
        import time
        base = T(0)
        with self.db.transaction() as c:
            for n in range(10000):
                e = TimeEntry(title=f"t{n}", start_utc=base + dt.timedelta(minutes=n), end_utc=base + dt.timedelta(minutes=n + 1))
                row = e.to_row()
                c.execute(f"INSERT INTO entries ({','.join(chr(34)+k+chr(34) for k in row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
        t0 = time.perf_counter()
        rows = self.db.entries_between(base, base + dt.timedelta(days=3))
        self.assertLess(time.perf_counter() - t0, 0.5)
        self.assertEqual(len(rows), 4320)


class LegacyImportTests(unittest.TestCase):
    def make_legacy(self, path):
        c = sqlite3.connect(path)
        c.executescript("""
        CREATE TABLE projects (id TEXT PRIMARY KEY,name TEXT,description TEXT,color TEXT,icon TEXT,created_at TIMESTAMP,
            updated_at TIMESTAMP,deadline TIMESTAMP,budget REAL,status TEXT,metadata TEXT);
        CREATE TABLE tasks (id TEXT PRIMARY KEY,title TEXT,description TEXT,start_time TIMESTAMP,end_time TIMESTAMP,
            estimated_minutes INTEGER,actual_minutes INTEGER,category TEXT,project_id TEXT,priority INTEGER,status TEXT,
            notes TEXT,calendar_event_id TEXT);
        CREATE TABLE tags (id TEXT PRIMARY KEY,name TEXT);
        CREATE TABLE task_tags (task_id TEXT, tag_id TEXT);
        INSERT INTO projects VALUES ('p1','Alpha','d','#fff','x','2025-01-01 10:00:00','2025-01-01 10:00:00',NULL,100,'active',NULL);
        INSERT INTO tags VALUES ('g1','bug');
        INSERT INTO tasks VALUES ('t1','Fix','',  '2025-03-21 09:00:00','2025-03-21 10:30:00',60,90,'development','p1',9,'completed','n','ev1');
        INSERT INTO tasks VALUES ('t2','Plan','', '2025-03-22 09:00:00','2025-03-22 08:00:00',0,0,'x','ghost',3,'pending','',NULL);
        INSERT INTO tasks VALUES ('t3','Bad','', 'garbage',NULL,0,0,'x',NULL,3,'pending','',NULL);
        INSERT INTO task_tags VALUES ('t1','g1');
        """)
        c.commit(); c.close()

    def test_import(self):
        with tempfile.TemporaryDirectory() as d:
            legacy = Path(d) / "legacy.db"
            self.make_legacy(legacy)
            db = Database(Path(d) / "new.db")
            stats = import_legacy(db, legacy, backup_dir=Path(d) / "bk")
            self.assertEqual((stats["projects"], stats["entries"]), (1, 2))
            self.assertTrue((Path(d) / "bk" / "legacy-legacy.db").exists())
            t1 = db.get(TimeEntry, "t1")
            self.assertEqual(t1.tags, ["bug"])
            self.assertEqual(t1.duration_sec, 5400)
            self.assertEqual(t1.priority, 5)  # clamped
            self.assertEqual((t1.start_utc.hour, t1.start_utc.minute), (5, 30))  # Tehran -> UTC
            self.assertEqual(t1.status, Status.DONE)
            self.assertEqual(t1.extra["calendar_event_id"], "ev1")
            t2 = db.get(TimeEntry, "t2")
            self.assertIsNone(t2.project_id)            # dangling FK cleaned
            self.assertGreaterEqual(t2.end_utc, t2.start_utc)
            again = import_legacy(db, legacy)           # idempotent
            self.assertEqual((again["projects"], again["entries"]), (0, 0))
            db.close()


if __name__ == "__main__":
    unittest.main()
