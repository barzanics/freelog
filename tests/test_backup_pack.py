import datetime as dt
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from worktracker import sample_data
from worktracker.core.database import Database
from worktracker.core.models import Client, Comment, Goal, Habit, Member, Milestone, Project, Rule, Sprint, Template, TimeEntry
from worktracker.core.persian import UTC, now_utc
from worktracker.services import backup_pack as bp, security
from worktracker.services.projects import ProjectService
from worktracker.services.team import Team


def make_db(path=None, seed=1, n=60) -> Database:
    db = Database(path or ":memory:")
    sample_data.generate(db, seed=seed, entries=n, invoices=5)
    ents = db.all(TimeEntry)
    ProjectService(db).add_dependency(ents[1].id, ents[0].id)
    m = Team(db).add_member("ali"); Team(db).comment(ents[0].id, m.id, "نظر با @ali فارسی")
    p = db.all(Project)[0]
    db.save(Milestone(project_id=p.id, name="نقطه عطف", deliverables=["الف", "ب"]))
    db.save(Sprint(project_id=p.id, name="S1", start=now_utc(), end=now_utc() + dt.timedelta(days=14)))
    db.save(Habit(name="آب", log=["2026-05-01"], days=[0, 1, 2])); db.save(Goal(name="هدف", key_results=[{"name": "k", "target": 5, "current": 1}]))
    db.save(Template(name="t", tags=["x"])); db.save(Rule(name="r", attr="priority", op=">=", value=1, action="add_tag", arg="z"))
    db.set_setting("theme", "nord"); db.set_setting("prompt_config", {"interval_min": 45, "forced": True}); db.set_setting("custom_categories", {"k": {"name": "دسته", "icon": "⭐"}})
    db.set_setting("tg_token", "123:secret"); db.set_setting("float_pos", [10, 20]); db.set_setting("fired_reminders", {"a": 1})
    return db


def rewrite(src: Path, dst: Path, edits: dict, fix_checksums: bool = True) -> None:
    """Copy a package replacing/deleting files; keeps the manifest consistent unless asked not to."""
    zin = zipfile.ZipFile(src); files = {n: zin.read(n) for n in zin.namelist()}; zin.close()
    m = json.loads(files["manifest.json"])
    for name, data in edits.items():
        if data is None:
            files.pop(name, None); m["files"].pop(name, None)
        else:
            files[name] = data
            if fix_checksums and name != "manifest.json":
                m["files"][name] = {"sha256": bp._sha(data), "bytes": len(data)}
                if name.startswith("data/"):
                    m["tables"][name[5:-6]] = sum(1 for l in data.split(b"\n") if l.strip())
    if "manifest.json" not in edits:
        files["manifest.json"] = json.dumps(m).encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.t = Path(self.tmp.name); self.src = make_db()
        self.pack = bp.export_package(self.src, self.t / "full.wtpack")

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip_is_exact_for_every_table_and_setting(self):
        dst = Database()
        rep = bp.restore_package(dst, self.pack)
        a, b = bp.snapshot(self.src), bp.snapshot(dst)
        self.assertEqual(set(a), set(b))
        for t in a:
            key = "key" if t == "settings" else "id"
            self.assertEqual(sorted(a[t], key=lambda r: str(r[key])), sorted(b[t], key=lambda r: str(r[key])), f"table {t} differs")
        self.assertEqual(rep.total_rows, sum(rep.manifest['tables'].values())); self.assertGreater(rep.total_rows, 80); self.assertTrue(dst.integrity_ok())
        self.assertEqual(dst.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)                   # enforcement is switched back on
        e = dst.all(TimeEntry)[0]; self.assertIsInstance(e.tags, list); self.assertEqual(dst.get_setting("custom_categories")["k"]["name"], "دسته")

    def test_manifest_is_complete_and_checksummed(self):
        m = bp.verify_package(self.pack)
        self.assertEqual((m["format"], m["schema_version"]), (bp.FORMAT, self.src.version)); self.assertEqual(m["tables"]["entries"], 60)
        self.assertIn("data/entries.jsonl", m["files"]); self.assertIn("settings.json", m["files"]); self.assertNotIn("audit_log", m["tables"])
        self.assertFalse(list(self.t.glob("*.tmp")))                                                  # atomic write left nothing behind

    def test_replace_overwrites_and_makes_a_safety_backup(self):
        dst = make_db(self.t / "live.db", seed=9, n=15)
        before = bp.snapshot(dst)
        rep = bp.restore_package(dst, self.pack, mode="replace", backup_dir=self.t / "bk")
        self.assertEqual(len(dst.all(TimeEntry)), 60); self.assertEqual(bp.snapshot(dst)["entries"], bp.snapshot(self.src)["entries"])
        old = Database(rep.safety_backup)
        self.assertEqual(len(old.all(TimeEntry)), 15); self.assertEqual(bp.snapshot(old)["entries"], before["entries"]); old.close(); dst.close()

    def test_merge_adds_updates_and_respects_conflict_policy(self):
        dst = Database(); bp.restore_package(dst, self.pack)
        extra = TimeEntry(title="only here", start_utc=now_utc()); dst.save(extra)                  # a row the package does not have
        e = self.src.all(TimeEntry)[0]
        mine = dst.get(TimeEntry, e.id); mine.title = "edited locally"; dst.save(mine)             # newer than the package
        bp.restore_package(dst, self.pack, mode="merge", conflict="newer")
        self.assertEqual(dst.get(TimeEntry, e.id).title, "edited locally"); self.assertIsNotNone(dst.get(TimeEntry, extra.id))      # local newer kept, extra kept
        rep = bp.restore_package(dst, self.pack, mode="merge", conflict="package")
        self.assertEqual(dst.get(TimeEntry, e.id).title, e.title); self.assertIsNotNone(dst.get(TimeEntry, extra.id)); self.assertGreater(rep.tables["entries"]["updated"], 0)
        dst.set_setting("theme", "paper"); bp.restore_package(dst, self.pack, mode="merge", conflict="keep")
        self.assertEqual(dst.get_setting("theme"), "paper")                                          # keep: existing settings win

    def test_tampering_and_garbage_are_detected(self):
        bad = self.t / "bad.wtpack"
        rewrite(self.pack, bad, {"data/entries.jsonl": b'{"id":"x"}'}, fix_checksums=False)
        with self.assertRaises(bp.VerificationError): bp.verify_package(bad)
        rewrite(self.pack, bad, {"data/entries.jsonl": None}, fix_checksums=False)
        with self.assertRaises(bp.VerificationError): bp.verify_package(bad)
        (self.t / "junk.wtpack").write_bytes(b"not a zip at all")
        with self.assertRaises(bp.PackageError): bp.verify_package(self.t / "junk.wtpack")
        with zipfile.ZipFile(self.t / "other.zip", "w") as z: z.writestr("manifest.json", json.dumps({"format": "something-else"}))
        with self.assertRaises(bp.PackageError): bp.verify_package(self.t / "other.zip")
        with zipfile.ZipFile(self.t / "nom.zip", "w") as z: z.writestr("x", "y")
        with self.assertRaises(bp.PackageError): bp.verify_package(self.t / "nom.zip")

    def test_refuses_packages_from_a_newer_version(self):
        z = zipfile.ZipFile(self.pack); m = json.loads(z.read("manifest.json")); z.close()
        m["schema_version"] = 999
        newer = self.t / "newer.wtpack"; rewrite(self.pack, newer, {"manifest.json": json.dumps(m).encode()})
        with self.assertRaises(bp.PackageError): bp.restore_package(Database(), newer)
        m["schema_version"], m["format_version"] = 1, 99
        rewrite(self.pack, newer, {"manifest.json": json.dumps(m).encode()})
        with self.assertRaises(bp.PackageError): bp.verify_package(newer)

    def test_broken_references_roll_everything_back(self):
        dst = make_db(seed=5, n=10); before = bp.snapshot(dst)
        broken = self.t / "broken.wtpack"
        row = json.dumps({"id": "d1", "task_id": "ghost", "depends_on": "ghost2", "kind": "finish_to_start", "lag_days": 0})
        rewrite(self.pack, broken, {"data/dependencies.jsonl": row.encode()})
        with self.assertRaises(bp.RestoreError): bp.restore_package(dst, broken, mode="replace")
        self.assertEqual(bp.snapshot(dst), before)                                                     # nothing changed: all or nothing
        self.assertEqual(dst.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1); self.assertTrue(dst.integrity_ok())

    def test_old_and_future_column_sets(self):
        z = zipfile.ZipFile(self.pack); rows = [json.loads(l) for l in z.read("data/entries.jsonl").decode().splitlines()]; z.close()
        for r in rows:
            r.pop("rank", None); r.pop("source", None); r["column_from_the_future"] = 1                  # an older and a newer app at once
        p2 = self.t / "cols.wtpack"; rewrite(self.pack, p2, {"data/entries.jsonl": "\n".join(json.dumps(r) for r in rows).encode()})
        dst = Database(); rep = bp.restore_package(dst, p2)
        self.assertEqual(len(dst.all(TimeEntry)), 60); self.assertEqual((dst.all(TimeEntry)[0].rank, dst.all(TimeEntry)[0].source), (0.0, "manual"))   # defaults filled in
        self.assertTrue(any("column_from_the_future" in w for w in rep.warnings))

    def test_encryption(self):
        enc = bp.export_package(self.src, self.t / "enc.wtpack", password="pw پسورد")
        self.assertNotEqual(enc.read_bytes()[:2], b"PK")
        with self.assertRaises(bp.PackageError): bp.verify_package(enc)
        with self.assertRaises(security.DecryptError): bp.verify_package(enc, "wrong")
        dst = Database(); bp.restore_package(dst, enc, password="pw پسورد")
        self.assertEqual(bp.snapshot(dst)["entries"], bp.snapshot(self.src)["entries"])

    def test_history_and_screenshot_archives(self):
        shots = self.t / "shots"; shots.mkdir(); (shots / "2026-05-02.zip").write_bytes(b"PK\x05\x06" + b"\0" * 18)
        full = bp.export_package(self.src, self.t / "h.wtpack", include_history=True, screenshots_dir=shots)
        m = bp.verify_package(full); self.assertIn("audit_log", m["tables"]); self.assertEqual(m["screenshot_archives"], 1)
        dst = Database(); out = self.t / "restored_shots"
        rep = bp.restore_package(dst, full, screenshots_dir=out)
        self.assertEqual(rep.screenshots_copied, 1); self.assertTrue((out / "2026-05-02.zip").exists()); self.assertGreater(len(bp.snapshot(dst, True)["audit_log"]), 0)
        self.assertEqual(bp.restore_package(Database(), full, screenshots_dir=out).screenshots_copied, 0)       # already there: not copied again

    def test_larger_dataset_is_fast_and_exact(self):
        import time
        big = Database()
        with big.transaction() as c:
            for i in range(5000):
                e = TimeEntry(title=f"t{i}", start_utc=now_utc(), end_utc=now_utc()); r = e.to_row()
                c.execute(f"INSERT INTO entries ({','.join(chr(34) + k + chr(34) for k in r)}) VALUES ({','.join('?' * len(r))})", tuple(r.values()))
        t0 = time.perf_counter(); p = bp.export_package(big, self.t / "big.wtpack"); dst = Database(); bp.restore_package(dst, p)
        self.assertLess(time.perf_counter() - t0, 15); self.assertEqual(len(dst.all(TimeEntry)), 5000)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError): bp.restore_package(Database(), self.pack, mode="nope")
        with self.assertRaises(ValueError): bp.restore_package(Database(), self.pack, conflict="nope")


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.t = Path(self.tmp.name); self.db = make_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_leaves_out_machine_state_and_secrets(self):
        f = bp.export_config(self.db, self.t / "cfg.json"); doc = json.loads(f.read_text(encoding="utf-8"))
        s = doc["settings"]
        self.assertEqual(s["theme"], "nord"); self.assertEqual(s["prompt_config"]["interval_min"], 45); self.assertEqual(s["custom_categories"]["k"]["name"], "دسته")
        for k in ("float_pos", "fired_reminders", "tg_token", "invoice_seq"):
            self.assertNotIn(k, s)
        self.assertFalse(doc["includes_secrets"])
        s2 = json.loads(bp.export_config(self.db, self.t / "c2.json", include_secrets=True).read_text(encoding="utf-8"))["settings"]
        self.assertEqual(s2["tg_token"], "123:secret"); self.assertNotIn("float_pos", s2)

    def test_import_roundtrip_diff_and_modes(self):
        f = bp.export_config(self.db, self.t / "cfg.json")
        other = Database(); other.set_setting("theme", "paper"); other.set_setting("local_only", 1); other.set_setting("float_pos", [1, 2])
        plan = bp.diff_config(other, f)
        self.assertIn("theme", plan["changed"]); self.assertIn("prompt_config", plan["new"]); self.assertNotIn("local_only", plan["new"])
        bp.import_config(other, f, "merge")
        self.assertEqual(other.get_setting("theme"), "nord"); self.assertEqual(other.get_setting("local_only"), 1); self.assertEqual(other.get_setting("float_pos"), [1, 2])
        self.assertEqual(other.get_setting("prompt_config"), {"interval_min": 45, "forced": True})
        bp.import_config(other, f, "replace")
        self.assertIsNone(other.get_setting("local_only")); self.assertEqual(other.get_setting("float_pos"), [1, 2])               # machine state survives a replace
        again = bp.diff_config(other, f); self.assertEqual((again["new"], again["changed"]), ([], []))

    def test_invalid_and_hostile_files(self):
        for name, content in (("a.json", "{not json"), ("b.json", "[]"), ("c.json", json.dumps({"format": "x", "settings": {}})), ("d.json", json.dumps({"format": bp.CONFIG_FORMAT, "settings": []})),
                              ("e.json", json.dumps({"format": bp.CONFIG_FORMAT, "format_version": 99, "settings": {}}))):
            (self.t / name).write_text(content, encoding="utf-8")
            with self.assertRaises(bp.PackageError, msg=name): bp.import_config(Database(), self.t / name)
        with self.assertRaises(bp.PackageError): bp.import_config(Database(), self.t / "missing.json")
        evil = {"format": bp.CONFIG_FORMAT, "format_version": 1, "settings": {"ok_key": 1, "bad key!": 2, "../../x": 3, "fired_reminders": {"a": 1}, "huge": "x" * 600000}}
        (self.t / "evil.json").write_text(json.dumps(evil), encoding="utf-8")
        db = Database(); plan = bp.import_config(db, self.t / "evil.json")
        self.assertEqual(plan["new"], ["ok_key"]); self.assertEqual(sorted(plan["ignored"]), ["../../x", "bad key!", "fired_reminders", "huge"]); self.assertIsNone(db.get_setting("fired_reminders"))
        with self.assertRaises(ValueError): bp.import_config(db, self.t / "evil.json", "nope")

    def test_package_and_config_agree_on_user_settings(self):
        pack = bp.export_package(self.db, self.t / "p.wtpack"); dst = Database(); bp.restore_package(dst, pack)
        self.assertEqual(dst.get_setting("float_pos"), [10, 20])                                       # a full backup keeps *everything*, including machine state
        self.assertEqual(dst.get_setting("tg_token"), "123:secret")


if __name__ == "__main__":
    unittest.main()
