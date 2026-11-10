import datetime as dt
import unittest

from worktracker.core import persian as p


class PersianTests(unittest.TestCase):
    def test_nowruz_anchors(self):
        self.assertEqual(p.gregorian_to_jalali(2024, 3, 20), (1403, 1, 1))
        self.assertEqual(p.gregorian_to_jalali(2025, 3, 21), (1404, 1, 1))
        self.assertEqual(p.gregorian_to_jalali(2026, 3, 21), (1405, 1, 1))

    def test_leap_years(self):
        self.assertEqual([y for y in range(1395, 1410) if p.is_jalali_leap(y)], [1395, 1399, 1403, 1408])
        self.assertEqual(p.jalali_month_length(1403, 12), 30)
        self.assertEqual(p.jalali_month_length(1404, 12), 29)

    def test_roundtrip_110_years(self):
        d, end = dt.date(1990, 1, 1), dt.date(2100, 1, 1)
        while d < end:
            self.assertEqual(p.jalali_to_date(*p.date_to_jalali(d)), d)
            d += dt.timedelta(days=1)

    def test_year_length_and_boundaries(self):
        for jy in range(1400, 1501):
            a, b = p.jalali_to_date(jy, 1, 1), p.jalali_to_date(jy + 1, 1, 1)
            self.assertEqual((b - a).days, 366 if p.is_jalali_leap(jy) else 365)

    def test_invalid(self):
        for bad in [(1404, 13, 1), (1404, 12, 30), (1404, 7, 31), (1404, 1, 0)]:
            with self.assertRaises(ValueError):
                p.jalali_to_gregorian(*bad)

    def test_digits_and_parse(self):
        self.assertEqual(p.to_fa_digits("1404/07/16"), "۱۴۰۴/۰۷/۱۶")
        self.assertEqual(p.to_en_digits("۱۴۰۵"), "1405")
        self.assertEqual(p.parse_jalali("۱۴۰۵/۰۱/۰۱"), dt.date(2026, 3, 21))
        with self.assertRaises(ValueError):
            p.parse_jalali("nope")

    def test_utc_tehran(self):
        naive = dt.datetime(2026, 1, 1, 12, 0)
        self.assertEqual(p.to_utc(naive).hour, 8)  # +03:30
        self.assertEqual(p.to_utc(naive).minute, 30)
        self.assertEqual(p.to_tehran(p.to_utc(naive)).replace(tzinfo=None), naive)

    def test_year_bounds(self):
        s, e = p.jalali_year_bounds(1404)
        self.assertEqual(round((e - s).total_seconds() / 86400), 365)

    def test_duration(self):
        self.assertEqual(p.format_duration(3725), "1:02")
        self.assertEqual(p.format_duration(-5), "0:00")
        self.assertEqual(p.format_duration(86400), "24:00")


if __name__ == "__main__":
    unittest.main()
