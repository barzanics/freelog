import datetime as dt
import unittest

from worktracker.core.crm import Store
from worktracker.core.database import Database
from worktracker.core.models import Client, Invoice, Project, Status, TimeEntry
from worktracker.core.persian import UTC
from worktracker.reports import locale_us as us
from worktracker.services import client_ops as ops, project_health as ph


def D(m, d, h=12, y=2026):
    return dt.datetime(y, m, d, h, tzinfo=UTC)


NOW = D(3, 16)                                                   # exactly half way through March


def task(db, pid, title, mins=60, done=False, **kw):
    e = TimeEntry(title=title, start_utc=D(3, 2), status=Status.PLANNED, project_id=pid, estimated_min=mins, **kw)
    if done:
        e.column, e.status, e.completed_at, e.progress = "done", Status.DONE, D(3, 10), 100
    db.save(e)
    return e


class Base(unittest.TestCase):
    def setUp(self):
        self.db = Database(); self.st = Store(self.db)
        self.c = Client(name="Acme", default_rate=100.0, currency="USD"); self.db.save(self.c)
        self.p = Project(name="Site", client_id=self.c.id, start=D(3, 1), deadline=D(3, 31), estimated_hours=20, budget=2000, rate_per_hour=100.0); self.db.save(self.p)

    def ms(self, name, weight=1.0, due=None, **kw):
        return self.st.add("milestones", project_id=self.p.id, name=name, weight=weight, due=due.isoformat() if due else None, completed=0, **kw)

    def ten(self, done):
        for i in range(10):
            task(self.db, self.p.id, f"t{i}", 60, done=i < done)


class ProgressAndHealthTests(Base):
    def test_weighted_progress_uses_milestone_weights_and_unphased_bucket(self):
        a, b = self.ms("Design", 1), self.ms("Build", 3)
        task(self.db, self.p.id, "A", 60, True, extra={"phase": a["id"]}); task(self.db, self.p.id, "B", 60, False, extra={"phase": a["id"]}); task(self.db, self.p.id, "C", 120, True, extra={"phase": b["id"]})
        r = ph.weighted_progress(self.db, self.p.id)
        self.assertEqual(r["pct"], 87.5); self.assertEqual([(m["name"], m["pct"]) for m in r["milestones"]], [("Design", 50.0), ("Build", 100.0)])
        task(self.db, self.p.id, "loose", 60, False)                                                  # a task in no milestone counts as one extra bucket of weight 1
        self.assertEqual(ph.weighted_progress(self.db, self.p.id)["pct"], 70.0)                       # (50*1 + 100*3 + 0*1) / 5
        self.st.update("milestones", a["id"], status="accepted"); self.assertEqual(ph.weighted_progress(self.db, self.p.id)["milestones"][0]["pct"], 100.0)

    def test_progress_without_milestones_is_estimate_weighted_and_subtasks_are_the_leaves(self):
        task(self.db, self.p.id, "done", 60, True); task(self.db, self.p.id, "open", 180)
        self.assertEqual(ph.weighted_progress(self.db, self.p.id)["pct"], 25.0)
        parent = task(self.db, self.p.id, "parent", 600)
        for i, d in enumerate((True, True, False)): task(self.db, self.p.id, f"s{i}", 60, d, parent_id=parent.id)
        r = ph.weighted_progress(self.db, self.p.id); self.assertEqual((r["tasks_total"], r["tasks_done"]), (2 + 3, 1 + 2))            # the parent itself is not counted, its sub-tasks are
        self.assertEqual(ph.weighted_progress(Database(), "none")["pct"], 0.0)

    def test_rag_thresholds_follow_the_spec(self):
        self.ten(4); h = ph.health(self.db, self.p.id, NOW)                                              # 40 % done, 50 % of the time gone -> 10 behind: still on track
        self.assertEqual((h["status"], h["planned_pct"], h["actual_pct"], h["gap_pts"]), ("on_track", 50.0, 40.0, 10.0)); self.assertIn("On schedule", h["reasons"][0]["text"])
        for k, expect in ((3, "at_risk"), (2, "off_track")):
            d = Database(); c = Client(name="x"); d.save(c); p = Project(name="p", client_id=c.id, start=D(3, 1), deadline=D(3, 31)); d.save(p)
            for i in range(10): task(d, p.id, f"t{i}", 60, i < k)
            self.assertEqual(ph.health(d, p.id, NOW)["status"], expect, k)
        self.assertEqual(ph.health(self.db, self.p.id, D(3, 1))["planned_pct"], 0.0)

    def test_overdue_milestones_budget_and_blockers_only_make_it_worse(self):
        self.ten(5)
        m1 = self.ms("Late 1", due=D(3, 10)); task(self.db, self.p.id, "m1 work", 60, True, extra={"phase": m1["id"]})                    # finished work but the milestone is not accepted yet
        self.assertEqual(ph.health(self.db, self.p.id, NOW)["status"], "at_risk")
        m2 = self.ms("Late 2", due=D(3, 12)); task(self.db, self.p.id, "m2 work", 60, True, extra={"phase": m2["id"]}); h = ph.health(self.db, self.p.id, NOW); self.assertEqual(h["status"], "off_track"); self.assertTrue(any(r["code"] == "milestone" for r in h["reasons"]))
        self.st.update("milestones", m1["id"], status="done")
        d = Database(); c = Client(name="x"); d.save(c); p = Project(name="p", client_id=c.id, start=D(3, 1), deadline=D(3, 31), estimated_hours=10); d.save(p)
        for i in range(10): task(d, p.id, f"t{i}", 60, i < 5)
        d.save(TimeEntry(title="work", start_utc=D(3, 2), end_utc=D(3, 2) + dt.timedelta(hours=11), billable=True, project_id=p.id))              # 110 % of the hour budget
        self.assertEqual(ph.health(d, p.id, NOW)["status"], "off_track")
        e = d.all(TimeEntry)[0]; ph.set_blocked(d, task(d, p.id, "blocked", 30).id, "waiting for logo", "client", now=D(3, 10))
        self.assertTrue(any(r["code"] == "blockers" for r in ph.health(d, p.id, NOW)["reasons"]))

    def test_complete_project_and_no_deadline(self):
        self.ten(10); h = ph.health(self.db, self.p.id, NOW); self.assertEqual((h["status"], h["reasons"][0]["code"]), ("on_track", "complete"))
        p2 = Project(name="open-ended", client_id=self.c.id); self.db.save(p2); task(self.db, p2.id, "a", 60, True); task(self.db, p2.id, "b", 60)
        h = ph.health(self.db, p2.id, NOW); self.assertEqual((h["status"], h["planned_pct"], h["reasons"][0]["text"]), ("on_track", None, "50% complete; no deadline set."))
        stored = ph.refresh_health(self.db, self.p.id, NOW); self.assertEqual(self.st.get("projects", self.p.id)["health"], stored["status"])

    def test_blockers_unblock_stale(self):
        t = task(self.db, self.p.id, "waiting"); ph.set_blocked(self.db, t.id, "need credentials", "client", now=D(3, 1))
        b = ph.blockers(self.db, self.p.id, 3, now=D(3, 10)); self.assertEqual((b[0]["days"], b[0]["aged"], b[0]["by"], b[0]["reason"]), (9, True, "client", "need credentials"))
        self.assertEqual(ph.blockers(self.db, self.p.id, 3, now=D(3, 2))[0]["aged"], False)
        ph.unblock(self.db, t.id); self.assertEqual(ph.blockers(self.db, self.p.id), []); self.assertNotIn("blocked_since", self.db.get(TimeEntry, t.id).extra)
        later = dt.datetime.now(UTC) + dt.timedelta(days=30); self.assertEqual([x.title for x in ph.stale_tasks(self.db, self.p.id, 14, later)], ["waiting"])
        with self.assertRaises(KeyError): ph.set_blocked(self.db, "zz")

    def test_scope_creep_against_the_baseline(self):
        self.assertFalse(ph.scope_creep(self.db, self.p.id)["has_baseline"])
        for i in range(3): task(self.db, self.p.id, f"base{i}", 60)
        base = ph.set_baseline(self.db, self.p.id); self.assertEqual(base["hours"], 3.0)
        self.assertEqual(ph.scope_creep(self.db, self.p.id)["added"], [])
        task(self.db, self.p.id, "extra request", 60); r = ph.scope_creep(self.db, self.p.id)
        self.assertEqual((len(r["added"]), r["added_hours"], r["pct"], r["flag"]), (1, 1.0, 33.3, True)); self.assertEqual(r["added"][0]["title"], "extra request")

    def test_budget_thresholds_fire_once(self):
        def log(h): self.db.save(TimeEntry(title="w", start_utc=D(3, 3), end_utc=D(3, 3) + dt.timedelta(hours=h), billable=True, project_id=self.p.id))
        log(10); self.assertEqual((ph.budget_status(self.db, self.p.id)["hours_pct"], ph.new_budget_alerts(self.db, self.p.id)), (50.0, []))
        log(5); self.assertEqual(ph.new_budget_alerts(self.db, self.p.id), [75]); self.assertEqual(ph.new_budget_alerts(self.db, self.p.id), [])
        log(3); self.assertEqual(ph.new_budget_alerts(self.db, self.p.id), [90]); log(3); self.assertEqual(ph.new_budget_alerts(self.db, self.p.id), [100])
        b = ph.budget_status(self.db, self.p.id); self.assertEqual((b["hours_used"], b["amount_used"], b["amount_pct"]), (21.0, 2100.0, 105.0))
        self.db.save(TimeEntry(title="free", start_utc=D(3, 4), end_utc=D(3, 5), billable=False, project_id=self.p.id)); self.assertEqual(ph.budget_status(self.db, self.p.id)["hours_used"], 21.0)

    def test_retainer_and_effective_rate(self):
        self.st.update("clients", self.c.id, retainer_hours=40)
        self.db.save(TimeEntry(title="m", start_utc=D(3, 3), end_utc=D(3, 3) + dt.timedelta(hours=30), project_id=self.p.id)); self.db.save(TimeEntry(title="apr", start_utc=D(4, 2), end_utc=D(4, 2, 20), project_id=self.p.id))
        r = ph.retainer_status(self.db, self.c.id, dt.date(2026, 3, 1)); self.assertEqual((r["used_hours"], r["remaining_hours"], r["pct"], r["over"]), (30.0, 10.0, 75.0, False))
        self.db.save(TimeEntry(title="more", start_utc=D(3, 20), end_utc=D(3, 20) + dt.timedelta(hours=15), project_id=self.p.id)); self.assertTrue(ph.retainer_status(self.db, self.c.id, dt.date(2026, 3, 1))["over"])
        inv = Invoice(client_id=self.c.id, items=[{"description": "work", "hours": 45, "rate": 100.0, "amount": 4500.0}], issued_at=D(3, 31)); self.db.save(inv)
        self.assertEqual(ph.effective_rate(self.db, self.c.id, dt.date(2026, 3, 1), dt.date(2026, 3, 31)), round(inv.total / 45, 2)); self.assertIsNone(ph.effective_rate(self.db, self.c.id, dt.date(2025, 1, 1), dt.date(2025, 1, 31)))

    def test_forecast_uses_velocity_in_business_days(self):
        for i in range(4): task(self.db, self.p.id, f"d{i}", 120, True, completed_at=None) if False else None
        for i in range(4):
            e = task(self.db, self.p.id, f"d{i}", 120, True); e.completed_at = NOW - dt.timedelta(days=5); self.db.save(e)                       # 8 h done in the last 4 weeks = 2 h/week
        task(self.db, self.p.id, "r1", 120); task(self.db, self.p.id, "r2", 120)                                                                # 4 h remaining -> 2 weeks -> 10 business days
        f = ph.forecast(self.db, self.p.id, NOW); self.assertEqual((f["remaining_hours"], f["velocity_hours_per_week"]), (4.0, 2.0)); self.assertEqual(f["projected_date"], us.add_business_days(NOW.date(), 10))
        self.assertEqual(f["late_days"], (f["projected_date"] - D(3, 31).date()).days)
        d = Database(); p = Project(name="n"); d.save(p); task(d, p.id, "x"); self.assertIsNone(ph.forecast(d, p.id, NOW)["projected_date"])

    def test_deadlines_on_holidays_and_weekends_are_flagged(self):
        task(self.db, self.p.id, "fireworks", due_utc=D(7, 3)); task(self.db, self.p.id, "saturday", due_utc=D(3, 14)); task(self.db, self.p.id, "wednesday", due_utc=D(3, 18)); task(self.db, self.p.id, "done", True, due_utc=D(7, 3)) if False else None
        self.ms("Launch", due=D(11, 26))
        w = {x["title"]: x["why"] for x in ph.holiday_warnings(self.db, self.p.id)}
        self.assertEqual(w, {"fireworks": "Independence Day", "saturday": "weekend", "Launch": "Thanksgiving"})


class OpsBase(Base):
    def setUp(self):
        super().setUp(); self.rep = self.st.add("client_reports", project_id=self.p.id, type="weekly")


class ClientScoreTests(OpsBase):
    def test_a_happy_active_client_scores_high_and_each_problem_lowers_it(self):
        ops.touch_contact(self.db, self.c.id, NOW); self.ten(6); ops.add_feedback(self.db, self.rep["id"], 5, "great", NOW)
        s = ops.health_score(self.db, self.c.id, NOW); self.assertEqual((s["grade"], s["alert"], s["components"]["responsiveness"]), ("A", False, 100)); self.assertGreaterEqual(s["score"], 85)
        late = ops.health_score(self.db, self.c.id, NOW + dt.timedelta(days=20)); self.assertLess(late["score"], s["score"]); self.assertTrue(any("No contact for 20 days" in r for r in late["reasons"]))
        self.db.save(Invoice(client_id=self.c.id, items=[{"description": "x", "hours": 1, "rate": 100.0, "amount": 100.0}], issued_at=D(1, 1))); bad = ops.health_score(self.db, self.c.id, NOW)
        self.assertEqual(bad["components"]["payments"], 70); self.assertTrue(any("overdue" in r for r in bad["reasons"]))
        t = task(self.db, self.p.id, "w"); ph.set_blocked(self.db, t.id, "logo", "client", now=D(3, 1)); self.assertEqual(ops.health_score(self.db, self.c.id, NOW)["components"]["blockers"], 75)

    def test_unhappy_silent_client_raises_the_alert(self):
        ops.add_feedback(self.db, self.rep["id"], 1, "slow", D(1, 1)); self.ten(1)
        s = ops.health_score(self.db, self.c.id, D(3, 16)); self.assertTrue(s["alert"]); self.assertLess(s["score"], 60); self.assertEqual(s["components"]["satisfaction"], 0)
        self.assertEqual(ops.health_score(self.db, Client(name="none").id if False else self.c.id, NOW)["grade"] in "ABCDF", True)
        with self.assertRaises(KeyError): ops.health_score(self.db, "nope")

    def test_silence_alerts_use_each_clients_own_limit_and_ignore_inactive_ones(self):
        ops.touch_contact(self.db, self.c.id, D(3, 1))
        a = ops.silence_alerts(self.db, NOW); self.assertEqual([(x["name"], x["days"], x["limit"], x["never"]) for x in a], [("Acme", 15, 7, False)])
        self.assertEqual(ops.silence_alerts(self.db, D(3, 5)), [])
        self.st.update("clients", self.c.id, settings={"silence_days": 30, "last_contact_at": D(3, 1).isoformat()}); self.assertEqual(ops.silence_alerts(self.db, NOW), [])
        self.st.update("projects", self.p.id, status="completed"); self.assertEqual(ops.silence_alerts(self.db, D(6, 1)), [])
        c2 = Client(name="NeverTalked"); self.db.save(c2); self.db.save(Project(name="p2", client_id=c2.id)); self.assertTrue(ops.silence_alerts(self.db, dt.datetime.now(UTC) + dt.timedelta(days=9))[0]["never"])

    def test_feedback_rules(self):
        for bad in (0, 6): 
            with self.assertRaises(ops.OpsError): ops.add_feedback(self.db, self.rep["id"], bad)
        with self.assertRaises(KeyError): ops.add_feedback(self.db, "nope", 5)
        ops.add_feedback(self.db, self.rep["id"], 4, " ok ", NOW); ops.add_feedback(self.db, self.rep["id"], 5, "", NOW)
        self.assertEqual(ops.average_rating(self.db, self.c.id, 180, NOW), 4.5); self.assertEqual(ops.last_contact(self.db, self.c.id), NOW); self.assertIsNone(ops.average_rating(self.db, self.c.id, 1, NOW + dt.timedelta(days=5)))


class RelationshipTests(OpsBase):
    def test_promises_alert_once_suggest_a_notice_and_can_be_renegotiated(self):
        soon = ops.add_promise(self.db, self.c.id, "Homepage mockups", D(3, 17), self.p.id, NOW); late = ops.add_promise(self.db, self.c.id, "Logo options", D(3, 10), None, NOW)
        al = ops.promise_alerts(self.db, NOW); self.assertEqual([(a["text"], a["state"]) for a in al], [("Logo options", "overdue"), ("Homepage mockups", "due_soon")])
        self.assertIn("we are going to miss", al[0]["notice"]); self.assertIn("Mar 10, 2026", al[0]["notice"]); self.assertIn("Acme", al[0]["notice"])
        ops.mark_promise_notified(self.db, late["id"]); self.assertEqual([a["text"] for a in ops.promise_alerts(self.db, NOW)], ["Homepage mockups"])
        self.assertEqual(ops.mark_promise(self.db, soon["id"], "kept", NOW)["status"], "kept"); self.assertEqual(ops.promise_alerts(self.db, NOW), [])
        r = ops.mark_promise(self.db, late["id"], "renegotiated", NOW, new_due=D(3, 25)); self.assertEqual((r["status"], r["notified"], r["due"][:10]), ("open", 0, "2026-03-25"))
        with self.assertRaises(ops.OpsError): ops.mark_promise(self.db, late["id"], "bogus")
        with self.assertRaises(ops.OpsError): ops.add_promise(self.db, self.c.id, " ", D(3, 20))
        with self.assertRaises(KeyError): ops.add_promise(self.db, "zz", "x", D(3, 20))
        self.assertEqual([p["text"] for p in ops.promises(self.db, self.c.id, "open")], ["Logo options"])

    def test_onboarding_checklist(self):
        items = ops.ensure_onboarding(self.db, self.c.id); self.assertEqual(len(items), 9); self.assertEqual(len(ops.ensure_onboarding(self.db, self.c.id)), 9)
        self.assertTrue(ops.toggle_onboarding(self.db, items[0]["id"], NOW)); self.assertEqual(ops.onboarding_progress(self.db, self.c.id)["pct"], 11)
        self.assertFalse(ops.toggle_onboarding(self.db, items[0]["id"])); self.assertEqual(ops.onboarding_progress(self.db, self.c.id)["done"], 0)
        with self.assertRaises(KeyError): ops.toggle_onboarding(self.db, "zz")

    def test_meetings_count_as_contact_and_feed_the_report_window(self):
        m = ops.log_meeting(self.db, self.c.id, "Kickoff", 45, D(3, 3), self.p.id, [{"text": "Send brief", "owner": "client"}], ["Ann"]); self.assertEqual(m["action_items"][0]["text"], "Send brief")
        ops.log_meeting(self.db, self.c.id, "Monthly sync (client level)", 30, D(3, 12)); ops.log_meeting(self.db, self.c.id, "Out of window", 30, D(2, 1))
        self.assertEqual(ops.last_contact(self.db, self.c.id), D(3, 12))
        self.assertEqual([x["summary"] for x in ops.meetings_between(self.db, self.p.id, D(3, 1), D(3, 15))], ["Kickoff", "Monthly sync (client level)"])
        with self.assertRaises(ops.OpsError): ops.log_meeting(self.db, self.c.id, "x", 9999)
        with self.assertRaises(KeyError): ops.log_meeting(self.db, "zz", "x")

    def test_risk_register_scores_and_visibility(self):
        ops.add_risk(self.db, self.p.id, "Scope grows", 5, 4, "Weekly scope review", visible=True); ops.add_risk(self.db, self.p.id, "Holiday slip", 3, 3); ops.add_risk(self.db, self.p.id, "Typo", 1, 2)
        r = ops.risk_register(self.db, self.p.id); self.assertEqual([(x["title"], x["score"], x["level"]) for x in r], [("Scope grows", 20, "high"), ("Holiday slip", 9, "medium"), ("Typo", 2, "low")])
        self.assertEqual([x["title"] for x in ops.risk_register(self.db, self.p.id, only_visible=True)], ["Scope grows"])
        for bad in ((0, 3), (3, 6)):
            with self.assertRaises(ops.OpsError): ops.add_risk(self.db, self.p.id, "x", *bad)
        with self.assertRaises(ops.OpsError): ops.add_risk(self.db, self.p.id, " ", 3, 3)

    def test_deliverable_approval_flow_and_public_change_log(self):
        d = ops.add_deliverable(self.db, self.p.id, "Homepage design", "link", "https://figma.example/x", visible=True, delivered_at=D(3, 5)); hidden = ops.add_deliverable(self.db, self.p.id, "Internal notes", "note", visible=False)
        self.assertEqual([x["title"] for x in ops.pending_approvals(self.db, self.p.id)], ["Homepage design"])
        r = ops.decide_deliverable(self.db, d["id"], "changes_requested", "Make the logo bigger", D(3, 6)); self.assertEqual((r["status"], r["feedback"]), ("changes_requested", "Make the logo bigger"))
        self.assertEqual(ops.pending_approvals(self.db, self.p.id), []); ops.decide_deliverable(self.db, d["id"], "approved", "", D(3, 8))
        texts = [c["text"] for c in ops.public_changes(self.db, self.p.id)]; self.assertEqual(texts, ["Approved: Homepage design", "Changes requested: Homepage design", "Delivered: Homepage design"])      # the hidden deliverable never shows
        self.assertEqual(ops.last_contact(self.db, self.c.id), D(3, 8)); self.assertEqual(len(ops.public_changes(self.db, self.p.id, D(3, 7), D(3, 9))), 1)
        for bad in (lambda: ops.decide_deliverable(self.db, d["id"], "maybe"), lambda: ops.add_deliverable(self.db, self.p.id, " "), lambda: ops.add_deliverable(self.db, self.p.id, "x", "zip")):
            with self.assertRaises(ops.OpsError): bad()
        with self.assertRaises(KeyError): ops.decide_deliverable(self.db, "zz", "approved")

    def test_milestone_editing_and_completion(self):
        m = self.st.add("milestones", project_id=self.p.id, name="Beta", completed=0)
        r = ops.set_milestone(self.db, m["id"], weight=3, ord=2, acceptance_criteria="Passes QA", description="Beta build", deliverables=["APK", "Notes"]); self.assertEqual((r["weight"], r["ord"], r["acceptance_criteria"], r["deliverables"]), (3, 2, "Passes QA", ["APK", "Notes"]))
        for bad in (dict(weight=0), dict(color="red")):
            with self.assertRaises(ops.OpsError): ops.set_milestone(self.db, m["id"], **bad)
        done = ops.complete_milestone(self.db, m["id"], NOW); self.assertEqual((done["completed"], done["status"]), (1, "done")); self.assertEqual(ops.public_changes(self.db, self.p.id)[0]["text"], "Milestone completed: Beta")
        self.assertEqual(ph.weighted_progress(self.db, self.p.id)["milestones"][0]["pct"], 100.0)

    def test_upsell_only_when_it_is_a_good_moment(self):
        self.ten(9); ops.touch_contact(self.db, self.c.id, NOW); ops.add_feedback(self.db, self.rep["id"], 5, "", NOW)
        s = ops.upsell_suggestion(self.db, self.p.id, NOW); self.assertIsNotNone(s); self.assertIn("90%", s["reasons"][0])
        ops.add_feedback(self.db, self.rep["id"], 1, "", NOW); self.assertIsNone(ops.upsell_suggestion(self.db, self.p.id, NOW))                # average 3 < 4
        d = Database(); c = Client(name="c"); d.save(c); p = Project(name="p", client_id=c.id, start=D(3, 1), deadline=D(3, 31)); d.save(p)
        for i in range(10): task(d, p.id, f"t{i}", 60, i < 5)
        self.assertIsNone(ops.upsell_suggestion(d, p.id, NOW))                                                                                    # only 50 % done


if __name__ == "__main__":
    unittest.main()
