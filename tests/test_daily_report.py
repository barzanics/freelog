import datetime as dt
import unittest

from worktracker.core.database import Database
from worktracker.core.models import Habit, Project, Status, TimeEntry
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import daily_report as dr
from worktracker.ui import strings

DAY = dt.date(2026, 5, 2)


def L(h, m=0, day=2):
    return dt.datetime(2026, 5, day, h, m, tzinfo=TEHRAN).astimezone(UTC)


class DailyReportTests(unittest.TestCase):
    def setUp(self):
        strings.set_language("fa")
        self.db = Database(); self.p = Project(name="Alpha"); self.db.save(self.p)
        add = lambda title, a, b, **kw: self.db.save(TimeEntry(title=title, start_utc=a, end_utc=b, **kw))
        add("طراحی صفحه", L(9), L(10, 30), project_id=self.p.id, notes="نسخه‌ی اول")
        add("جلسه", L(11), L(12))
        add("late night", L(23, 30, day=1), L(1, 0), project_id=self.p.id)             # starts yesterday, crosses midnight into DAY
        add("other day", L(9, day=5), L(10, day=5))
        self.db.save(TimeEntry(title="در جریان", start_utc=L(8), status=Status.PLANNED, column="in_progress"))
        self.db.save(TimeEntry(title="مسدود", start_utc=L(8), status=Status.PLANNED, column="delayed", notes="منتظر API"))
        self.db.save(TimeEntry(title="فردا", start_utc=L(10, day=3), end_utc=L(11, day=3), status=Status.PLANNED))
        self.db.save(Habit(name="آب", log=[DAY.isoformat()]))

    def tearDown(self):
        strings.set_language("fa")

    def test_collects_the_right_day_and_splits_at_midnight(self):
        r = dr.build(self.db, DAY)
        self.assertEqual([l.title for l in r.lines], ["late night", "طراحی صفحه", "جلسه"])
        self.assertEqual((r.lines[0].start, r.lines[0].end, r.lines[0].minutes), ("00:00", "01:00", 60))                 # only the part inside this day
        self.assertEqual(r.total_sec, (60 + 90 + 60) * 60); self.assertEqual(r.by_project, {"Alpha": 150, "بدون پروژه": 60}); self.assertEqual(r.longest_min, 90)
        self.assertEqual((r.in_progress, r.tomorrow, r.habits_done), (["در جریان"], ["فردا"], ["آب"])); self.assertEqual(r.blockers, ["مسدود — منتظر API"])

    def test_persian_text_is_formal_and_complete(self):
        t = dr.to_text(dr.build(self.db, DAY), author="علی")
        for needle in ("گزارش کار روزانه", "تهیه‌کننده: علی", "۳:۳۰", "۰۹:۰۰–۱۰:۳۰", "طراحی صفحه [Alpha]", "نسخه‌ی اول", "به تفکیک پروژه:", "موانع و مشکلات:", "برنامه‌ی روز بعد:", "عادت‌های انجام‌شده:"):
            self.assertIn(needle, t)
        self.assertNotIn("3:30", t); self.assertIn("۱۴۰۵", t)

    def test_english_text_uses_latin_digits_and_gregorian_dates(self):
        strings.set_language("en")
        t = dr.to_text(dr.build(self.db, DAY))
        for needle in ("Daily work report", "Saturday 2 May 2026", "Total time: 3:30 h in 3 entries", "09:00–10:30", "Work completed:", "Plan for tomorrow:"):
            self.assertIn(needle, t)
        self.assertFalse(any(ch in t for ch in "۰۱۲۳۴۵۶۷۸۹"))
        self.assertIn("dir='ltr'", dr.to_html(dr.build(self.db, DAY)))

    def test_empty_day_and_formats(self):
        r = dr.build(self.db, dt.date(2026, 6, 1)); self.assertTrue(r.empty)
        self.assertIn("کاری ثبت نشده", dr.to_text(r))
        md = dr.to_markdown(dr.build(self.db, DAY)); self.assertTrue(md.startswith("# ")); self.assertIn("## ", md)
        h = dr.to_html(dr.build(self.db, DAY)); self.assertIn("dir='rtl'", h); self.assertNotIn("<script", h)
        self.db.save(TimeEntry(title="<script>x</script>", start_utc=L(15), end_utc=L(16)))
        self.assertNotIn("<script>", dr.to_html(dr.build(self.db, DAY)))


if __name__ == "__main__":
    unittest.main()
