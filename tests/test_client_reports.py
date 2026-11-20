import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from worktracker.core.crm import Store
from worktracker.core.database import Database
from worktracker.core.models import Client, Invoice, Project, Status, TimeEntry
from worktracker.core.persian import UTC
from worktracker.reports import builders as b, charts, locale_us as us, pdf, render, service
from worktracker.services import client_ops as ops, project_health as ph

NOW = dt.datetime(2026, 3, 12, 15, tzinfo=UTC)              # Thursday; the US week is Sun Mar 8 - Sat Mar 14


def D(m, d, h=12):
    return dt.datetime(2026, m, d, h, tzinfo=UTC)


def log(db, pid, title, start, hours, **kw):
    e = TimeEntry(title=title, start_utc=start, end_utc=start + dt.timedelta(hours=hours) if hours else None, project_id=pid, billable=kw.pop("billable", True), **kw)
    db.save(e)
    return e


class Seed(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.st = Store(self.db); self.tmp = tempfile.TemporaryDirectory(); self.dir = Path(self.tmp.name)
        self.c = Client(name="Acme", company="Acme Inc.", default_rate=100.0, currency="USD", email="ann@acme.test"); self.db.save(self.c)
        self.st.update("clients", self.c.id, timezone="America/New_York", contact_name="Ann", rounding_min=15, settings={"tax_percent": 8.25, "terms_days": 30})
        self.p = Project(name="Website", client_id=self.c.id, start=D(3, 1), deadline=D(3, 31), rate_per_hour=120.0, estimated_hours=40); self.db.save(self.p)
        self.db.set_setting("company_name", "barzanics"); self.db.set_setting("author_name", "Amirhossein Barzegar"); self.db.set_setting("company_email", "hello@barzanics.test")

    def tearDown(self):
        self.tmp.cleanup()


class PrivacyTests(Seed):
    def test_only_billable_or_flagged_entries_and_never_internal_notes(self):
        a = log(self.db, self.p.id, "Homepage design", D(3, 10, 15), 2.5, notes="SECRET internal note", description="SECRET description", status=Status.DONE)
        a.column, a.completed_at = "done", D(3, 10, 18); self.db.save(a)
        self.st.update("entries", a.id, client_note="Responsive layout delivered")
        log(self.db, self.p.id, "Internal admin", D(3, 10, 19), 1, billable=False, tags=["internal"], notes="SECRET admin")           # hidden even when flagged
        log(self.db, self.p.id, "Unflagged non-billable", D(3, 10, 20), 1, billable=False)
        flagged = log(self.db, self.p.id, "Flagged learning", D(3, 11, 15), 2, billable=False); self.st.update("entries", flagged.id, visible_to_client=1)
        d = b.build(self.db, self.p.id, "weekly", now=NOW)
        titles = {x["title"] for x in d["time"]["by_task"]}
        self.assertEqual(titles, {"Homepage design", "Flagged learning"}); self.assertEqual((d["time"]["billable_sec"], d["time"]["non_billable_sec"]), (9000, 7200))
        self.assertEqual(d["done"][0]["note"], "Responsive layout delivered")
        blob = json.dumps(d, default=str) + render.render_all(d, with_charts=False)["html"]
        self.assertNotIn("SECRET", blob); self.assertNotIn("Internal admin", blob); self.assertNotIn("Unflagged", blob)
        d2 = b.build(self.db, self.p.id, "weekly", now=NOW, options={"visibility": "flagged"}); self.assertEqual({x["title"] for x in d2["time"]["by_task"]}, {"Flagged learning"})

    def test_every_report_type_is_clean(self):
        log(self.db, self.p.id, "Secret sauce", D(3, 10, 15), 1, notes="SECRET", tags=["internal"]); ms = self.st.add("milestones", project_id=self.p.id, name="Beta", completed=0, description="d", acceptance_criteria="- Works\n- Fast")
        for kind in b.KINDS:
            d = b.build(self.db, self.p.id, kind, start=dt.date(2026, 3, 1), end=dt.date(2026, 3, 31), now=NOW, options={"milestone_id": ms["id"]})
            r = render.render_all(d)
            self.assertNotIn("SECRET", json.dumps(d, default=str) + r["html"] + r["email"] + r["md"], kind)


class TimeZoneAndRoundingTests(Seed):
    def test_us_formats_and_client_time_zone_decide_the_day(self):
        self.assertEqual((us.fmt_date(dt.date(2026, 3, 14)), us.fmt_range(dt.date(2026, 3, 8), dt.date(2026, 3, 14)), us.fmt_money(-1234.5), us.fmt_hm(3600 * 25 + 60)), ("Mar 14, 2026", "Mar 8–14, 2026", "-$1,234.50", "1501m" if False else "25h 01m"))
        log(self.db, self.p.id, "Late night", D(3, 11, 3) + dt.timedelta(minutes=30), 0.5)                      # 03:30 UTC on Mar 11 = 23:30 EDT on Mar 10
        d = b.build(self.db, self.p.id, "weekly", now=NOW); self.assertEqual([x["date"] for x in d["time"]["by_day"]], ["2026-03-10"])
        self.assertEqual((d["period"]["start"], d["period"]["end"], d["header"]["period_label"]), ("2026-03-08", "2026-03-14", "Mar 8–14, 2026"))
        self.st.update("clients", self.c.id, settings={"week_start": "mon"}); d = b.build(self.db, self.p.id, "weekly", now=NOW); self.assertEqual(d["period"]["start"], "2026-03-09")
        self.assertEqual(b.build(self.db, self.p.id, "daily", now=NOW)["period"]["days"], 1)

    def test_entry_crossing_local_midnight_is_split(self):
        log(self.db, self.p.id, "Overnight", D(3, 11, 3), 2)                                                      # 23:00 EDT Mar 10 -> 01:00 EDT Mar 11
        d = b.build(self.db, self.p.id, "weekly", now=NOW); self.assertEqual([(x["date"], x["billable"]) for x in d["time"]["by_day"]], [("2026-03-10", 3600), ("2026-03-11", 3600)])

    def test_rounding_up_to_the_client_increment(self):
        self.assertEqual([b.round_seconds(s, 15) for s in (1, 900, 901, 3000)], [900, 900, 1800, 3600]); self.assertEqual((b.round_seconds(100, 0), b.round_seconds(0, 15), b.round_seconds(400, 6, "nearest")), (100, 0, 360))
        self.assertEqual(us.add_business_days(dt.date(2026, 5, 22), 1), dt.date(2026, 5, 26))                    # Memorial Day weekend is skipped


class InvoiceTests(Seed):
    def test_invoice_lines_rounding_tax_terms_and_numbering(self):
        log(self.db, self.p.id, "Design", D(3, 3, 15), 50 / 60); log(self.db, self.p.id, "Design", D(3, 4, 15), 20 / 60); log(self.db, self.p.id, "Review", D(3, 5, 15), 1)
        log(self.db, self.p.id, "Free favour", D(3, 6, 15), 3, billable=False); log(self.db, self.p.id, "April work", D(4, 6, 15), 5)
        r = service.generate(self.db, self.dir, self.p.id, "invoice", dt.date(2026, 3, 1), dt.date(2026, 3, 31), NOW)
        i = r["payload"]["invoice"]
        self.assertEqual([(x["description"], x["hours"], x["amount"]) for x in i["items"]], [("Design", 1.5, 180.0), ("Review", 1.0, 120.0)])             # 50m->60m, 20m->30m
        self.assertEqual((i["subtotal"], i["tax"], i["total"], i["terms"], i["currency"]), (300.0, 24.75, 324.75, "Net 30", "USD")); self.assertEqual(i["due_date"], "2026-04-11")
        self.assertEqual((r["number"], i["number"]), ("INV-2026-0001", "INV-2026-0001")); self.assertEqual(service.generate(self.db, self.dir, self.p.id, "invoice", dt.date(2026, 3, 1), dt.date(2026, 3, 31), NOW)["number"], "INV-2026-0002")
        self.assertIn("Total due", render.render_all(r["payload"], with_charts=False)["html"])
        inv = service.create_invoice_record(self.db, r["id"]); self.assertEqual((inv.number, round(inv.total, 2)), ("INV-2026-0001", 324.75)); self.assertEqual(service.create_invoice_record(self.db, r["id"]).id, inv.id)
        with self.assertRaises(service.ReportStateError): service.create_invoice_record(self.db, service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW)["id"])

    def test_default_invoice_period_is_the_previous_month(self):
        d = b.build(self.db, self.p.id, "invoice", now=D(4, 2)); self.assertEqual((d["period"]["start"], d["period"]["end"]), ("2026-03-01", "2026-03-31"))


class ContentTests(Seed):
    def test_weekly_sections_waiting_decisions_commitments_and_summary(self):
        done = log(self.db, self.p.id, "Logo", D(3, 9, 15), 2); done.column, done.status, done.completed_at = "done", Status.DONE, D(3, 9, 17); self.db.save(done)
        t = log(self.db, self.p.id, "Copy review", D(3, 10, 15), 0.5, status=Status.PLANNED, column="in_progress", billable=True); ph.set_blocked(self.db, t.id, "need approved copy", "client", NOW - dt.timedelta(days=5))
        dl = ops.add_deliverable(self.db, self.p.id, "Homepage mockup", "link", "https://figma.example/x", visible=True, delivered_at=D(3, 9))
        ops.add_promise(self.db, self.c.id, "Send staging link", D(3, 20), self.p.id, NOW); ops.log_meeting(self.db, self.c.id, "Weekly sync", 30, D(3, 10, 14), self.p.id, [{"text": "Send assets"}])
        ops.add_risk(self.db, self.p.id, "Content delays", 4, 4, "Weekly nudge", visible=True)
        d = b.build(self.db, self.p.id, "weekly", now=NOW)
        self.assertEqual([x["title"] for x in d["done"]], ["Logo"]); self.assertEqual([(w["title"], w["days"]) for w in d["waiting_on_client"]], [("Copy review", 5)])
        self.assertEqual((d["pending_approvals"], [x["kind"] for x in d["decisions"]]), (["Homepage mockup"], ["approval"])); self.assertEqual(d["commitments"][0]["text"], "Send staging link")
        self.assertEqual((d["meetings"][0]["summary"], d["meetings"][0]["actions"]), ("Weekly sync", ["Send assets"])); self.assertEqual(d["risks"][0]["level"], "high")
        self.assertIn("waiting on you", d["summary"]); self.assertRegex(d["summary"], r"^We logged 2\.0 hours this week"); self.assertNotIn("on schedule", d["summary"]); self.assertEqual(b.build(self.db, self.p.id, "weekly", now=NOW, options={"summary": "Custom text."})["summary"], "Custom text.")
        self.st.update("clients", self.c.id, settings={"tone": "i"}); self.assertTrue(b.build(self.db, self.p.id, "weekly", now=NOW)["summary"].startswith("I logged"))
        c = d["comparison"]; self.assertEqual([x["label"] for x in c], ["Hours", "Billable hours", "Tasks completed"])

    def test_milestone_report_requires_a_milestone_and_shows_sign_off(self):
        with self.assertRaises(b.ReportError): b.build(self.db, self.p.id, "milestone", now=NOW)
        ms = self.st.add("milestones", project_id=self.p.id, name="Beta", completed=0, due=D(3, 20).isoformat(), acceptance_criteria="- Works\n- Fast")
        t = log(self.db, self.p.id, "Beta build", D(3, 9, 15), 3, extra={"phase": ms["id"]}); ops.add_deliverable(self.db, self.p.id, "Beta APK", milestone_id=ms["id"], visible=True)
        d = b.build(self.db, self.p.id, "milestone", now=NOW, options={"milestone_id": ms["id"]}); m = d["milestone"]
        self.assertEqual((m["name"], m["criteria"], m["hours"], m["sign_off"], m["due_label"]), ("Beta", ["Works", "Fast"], 3.0, False, "Mar 20, 2026"))
        ops.decide_deliverable(self.db, m["id"] if False else self.st.rows("deliverables")[0]["id"], "approved"); self.assertTrue(b.build(self.db, self.p.id, "milestone", now=NOW, options={"milestone_id": ms["id"]})["milestone"]["sign_off"])
        other = Project(name="Other"); self.db.save(other)
        with self.assertRaises(b.ReportError): b.build(self.db, other.id, "milestone", now=NOW, options={"milestone_id": ms["id"]})

    def test_bad_arguments(self):
        with self.assertRaises(b.ReportError): b.build(self.db, self.p.id, "poem")
        with self.assertRaises(b.ReportError): b.build(self.db, self.p.id, "weekly", start=dt.date(2026, 3, 9), end=dt.date(2026, 3, 1))
        with self.assertRaises(KeyError): b.build(self.db, "nope", "weekly")
        d = b.build(Database() if False else self.db, self.p.id, "snapshot", now=NOW); self.assertEqual(d["header"]["type"], "snapshot")


class RenderTests(Seed):
    def setUp(self):
        super().setUp()
        for i in range(20): log(self.db, self.p.id, f"Task {i}", D(3, 9 + i % 4, 14) + dt.timedelta(hours=i % 5), 1)
        self.d = b.build(self.db, self.p.id, "weekly", now=NOW)

    def test_html_email_markdown_json_and_escaping(self):
        self.p.name = "Site <script>alert(1)</script>"; self.db.save(self.p)
        d = b.build(self.db, self.p.id, "weekly", now=NOW); r = render.render_all(d, "http://127.0.0.1:8765/r/tok", "http://127.0.0.1:8765/pixel/tok.gif")
        for needle in ("Weekly Progress Report", "Mar 8–14, 2026", "Progress", "Time breakdown", "barzanics", "&lt;script&gt;", "<svg"): self.assertIn(needle, r["html"])
        self.assertNotIn("<script>alert", r["html"]); self.assertNotIn("<script>alert", r["email"])
        self.assertIn("View the full report", r["email"]); self.assertIn("pixel/tok.gif", r["email"]); self.assertNotIn("pixel", render.render_all(d, "http://x/")["email"]); self.assertLess(len(r["email"]), 12000)
        self.assertTrue(r["md"].startswith("# Weekly Progress Report")); self.assertEqual(json.loads(r["json"])["header"]["type"], "weekly"); self.assertEqual(set(r["charts"]), {"burnup", "donut", "trend", "heatmap"})
        self.assertNotIn("http://", render.render_all(d, with_charts=False)["html"].replace("http://127.0.0.1", ""))                  # no external resources: the page is self-contained

    def test_charts_are_valid_images_and_degrade_gracefully(self):
        for name, c in render.render_all(self.d)["charts"].items(): self.assertTrue(c["svg"].startswith("<svg") and c["png"][:4] == b"\x89PNG", name)
        self.assertIsNone(charts.burndown([dt.date(2026, 3, 1)], [1], [1])); self.assertIsNone(charts.donut(["a"], [0])); self.assertEqual(charts.build_charts({}, ["donut", "trend"]), {})
        self.assertEqual(charts.build_charts({"donut": {"labels": ["a"], "values": "bad"}}, ["donut"]), {})                          # a broken series never raises

    def test_pdf_is_a_real_multipage_document(self):
        r = service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW)
        out = service.ensure_pdf(self.db, self.dir, r["id"]); raw = out.read_bytes()
        self.assertEqual(raw[:5], b"%PDF-"); self.assertGreaterEqual(raw.count(b"/Type /Page") - raw.count(b"/Type /Pages"), 2); self.assertEqual(service.ensure_pdf(self.db, self.dir, r["id"]), out)
        inv = service.generate(self.db, self.dir, self.p.id, "invoice", dt.date(2026, 3, 1), dt.date(2026, 3, 31), NOW); self.assertGreater(service.ensure_pdf(self.db, self.dir, inv["id"]).stat().st_size, 2000)
        self.assertEqual(pdf.render_pdf(self.d, render.render_all(self.d), self.dir / "x.pdf", prefer_weasyprint=False).read_bytes()[:5], b"%PDF-")


class ServiceTests(Seed):
    def setUp(self):
        super().setUp(); log(self.db, self.p.id, "Work", D(3, 10, 15), 2)

    def test_lifecycle_files_status_and_numbering(self):
        r1 = service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW); r2 = service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW)
        self.assertEqual((r1["number"], r2["number"], r1["status"]), ("WR-20260312-01", "WR-20260312-02", "draft"))
        for ext in (".html", ".md", ".json"): self.assertTrue((self.dir / "client_reports" / self.p.id / f"{r1['number']}{ext}").exists())
        u = service.update_summary(self.db, self.dir, r1["id"], "  Hand-written summary.  "); self.assertEqual(u["summary"], "Hand-written summary.")
        self.assertIn("Hand-written summary.", Path(r1["html_path"]).read_text(encoding="utf-8")); self.assertEqual(service.approve(self.db, r1["id"])["status"], "approved")
        pdf_path = service.ensure_pdf(self.db, self.dir, r1["id"]); service.update_summary(self.db, self.dir, r1["id"], "Edited again."); self.assertFalse(pdf_path.exists())     # stale PDF removed
        self.assertEqual(service.get(self.db, r1["id"])["status"], "draft")
        Store(self.db).update("client_reports", r1["id"], status="sent")
        for call in (lambda: service.update_summary(self.db, self.dir, r1["id"], "x"), lambda: service.approve(self.db, r1["id"])):
            with self.assertRaises(service.ReportStateError): call()
        self.assertEqual([r["number"] for r in service.list_reports(self.db, self.p.id)], ["WR-20260312-02", "WR-20260312-01"]); self.assertEqual(len(service.list_reports(self.db, status="sent")), 1)
        with self.assertRaises(KeyError): service.get(self.db, "nope")

    def test_diff_against_the_previous_report(self):
        first = service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW - dt.timedelta(days=7)); self.assertFalse(service.diff(self.db, first["id"])["has_previous"])
        log(self.db, self.p.id, "More work", D(3, 11, 15), 3); t = log(self.db, self.p.id, "Waiting", D(3, 11, 16), 0.5, status=Status.PLANNED, column="in_progress"); ph.set_blocked(self.db, t.id, "asset", "client", NOW)
        second = service.generate(self.db, self.dir, self.p.id, "weekly", now=NOW); d = service.diff(self.db, second["id"])
        self.assertTrue(d["has_previous"]); self.assertTrue(any(l.startswith("Hours logged: 5.0 h") for l in d["lines"])); self.assertIn("Newly waiting on the client: Waiting", d["lines"])


if __name__ == "__main__":
    unittest.main()
