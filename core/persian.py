"""Jalali (Persian) calendar, Persian digits and Tehran-time helpers.

Pure stdlib. The Jalali algorithm follows the well-known 33-year-cycle
``jalaali`` implementation and is verified by round-trip tests.
"""
from __future__ import annotations

import datetime as dt
from typing import Tuple

try:  # zoneinfo needs tzdata on Windows; fall back to fixed +03:30 (no DST since 2022)
    from zoneinfo import ZoneInfo
    TEHRAN: dt.tzinfo = ZoneInfo("Asia/Tehran")
except Exception:  # pragma: no cover - environment dependent
    TEHRAN = dt.timezone(dt.timedelta(hours=3, minutes=30), "Asia/Tehran")

UTC = dt.timezone.utc

_BREAKS = (-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
           1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178)

MONTHS_FA = ("فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
             "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند")
WEEKDAYS_FA = ("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")  # Mon..Sun

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _div(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


# ---- locale (set once by the UI): English mode shows Latin digits and the Gregorian calendar; Persian mode shows Persian digits and Jalali
DIGITS_FA = True
CALENDAR = "jalali"          # "jalali" | "gregorian"
MONTHS_EN = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
WEEKDAYS_EN = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")   # Monday = 0, like datetime.weekday()
DEFAULT_DATE_FMT = "{y}/{m:02d}/{d:02d}"


def set_locale(lang: str, calendar: str = "") -> None:
    """lang 'fa' -> Persian digits + Jalali; 'en' -> Latin digits + Gregorian. ``calendar`` may override the calendar."""
    global DIGITS_FA, CALENDAR
    DIGITS_FA = lang == "fa"
    CALENDAR = calendar or ("jalali" if lang == "fa" else "gregorian")


def is_gregorian() -> bool:
    return CALENDAR == "gregorian"


def month_name(m: int) -> str:
    """Name of month ``m`` (1-12) in the active calendar."""
    return (MONTHS_EN if is_gregorian() else MONTHS_FA)[(m - 1) % 12]


_EN_PUNCT = str.maketrans({"٪": "%", "،": ",", "؛": ";", "؟": "?", "…": "…"})
WEEKDAYS_FA_SHORT = ("د", "س", "چ", "پ", "ج", "ش", "ی")                 # Mon..Sun
WEEKDAYS_EN_SHORT = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def tr(fa: str, en: str) -> str:
    """Pick the text for the active language (use for one-off strings that are not worth a key in the strings table)."""
    return fa if DIGITS_FA else en


def to_fa_digits(text: object) -> str:
    """Persian digits in Persian mode; in English mode Latin digits and Latin punctuation (so ``٪`` becomes ``%``)."""
    return str(text).translate(_FA_DIGITS) if DIGITS_FA else str(text).translate(_EN_PUNCT)


def weekday_names(short: bool = False, first: str = "auto") -> tuple:
    """Weekday names in the active language. ``first``: 'auto' (Saturday for Jalali, Monday for Gregorian), 'mon' or 'sat'."""
    names = (WEEKDAYS_EN_SHORT if short else WEEKDAYS_EN) if is_gregorian() else (WEEKDAYS_FA_SHORT if short else WEEKDAYS_FA)   # Monday-first
    if not DIGITS_FA and not is_gregorian():
        names = WEEKDAYS_EN_SHORT if short else WEEKDAYS_EN
    start_sat = first == "sat" or (first == "auto" and not is_gregorian())
    return tuple(names[(i - 2) % 7] for i in range(7)) if start_sat else tuple(names)


def to_en_digits(text: object) -> str:
    """Convert Persian/Arabic digits to Latin digits."""
    return str(text).translate(_EN_DIGITS)


def _jal_cal(jy: int) -> Tuple[int, int, int]:
    if jy < _BREAKS[0] or jy >= _BREAKS[-1]:
        raise ValueError(f"Jalali year out of range: {jy}")
    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    jump = 0
    for jm in _BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(jump % 33, 4)
        jp = jm
    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(n % 33 + 3, 4)
    if jump % 33 == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = ((n + 1) % 33 - 1) % 4
    if leap == -1:
        leap = 4
    return leap, gy, march


def is_jalali_leap(jy: int) -> bool:
    """Return True if Jalali year ``jy`` has 366 days."""
    return _jal_cal(jy)[0] == 0


def jalali_month_length(jy: int, jm: int) -> int:
    """Number of days in a Jalali month."""
    if not 1 <= jm <= 12:
        raise ValueError("month must be 1..12")
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap(jy) else 29


def _g2d(gy: int, gm: int, gd: int) -> int:
    d = (_div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
         + _div(153 * ((gm + 9) % 12) + 2, 5) + gd - 34840408)
    return d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752


def _d2g(jdn: int) -> Tuple[int, int, int]:
    j = 4 * jdn + 139361631
    j += _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(j % 1461, 4) * 5 + 308
    gd = _div(i % 153, 5) + 1
    gm = (_div(i, 153) % 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def _j2d(jy: int, jm: int, jd: int) -> int:
    _, gy, march = _jal_cal(jy)
    return _g2d(gy, 3, march) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2j(jdn: int) -> Tuple[int, int, int]:
    gy = _d2g(jdn)[0]
    jy = gy - 621
    leap, _, march = _jal_cal(jy)
    k = jdn - _g2d(gy, 3, march)
    if k >= 0:
        if k <= 185:
            return jy, 1 + _div(k, 31), k % 31 + 1
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return jy, 7 + _div(k, 30), k % 30 + 1


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
    """Convert a Gregorian date to (jy, jm, jd)."""
    return _d2j(_g2d(gy, gm, gd))


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
    """Convert a Jalali date to (gy, gm, gd). Validates the day range."""
    if not 1 <= jm <= 12 or not 1 <= jd <= jalali_month_length(jy, jm):
        raise ValueError(f"invalid Jalali date {jy}-{jm}-{jd}")
    return _d2g(_j2d(jy, jm, jd))


def date_to_jalali(d: dt.date) -> Tuple[int, int, int]:
    """Convert a ``datetime.date`` to a Jalali tuple."""
    return gregorian_to_jalali(d.year, d.month, d.day)


def jalali_to_date(jy: int, jm: int, jd: int) -> dt.date:
    """Convert a Jalali tuple to ``datetime.date``."""
    return dt.date(*jalali_to_gregorian(jy, jm, jd))


def format_jalali(d: dt.date, fmt: str = "{y}/{m:02d}/{d:02d}", fa_digits: bool = True) -> str:
    """Format a date. Fields: y, m, d, month_name, weekday."""
    if is_gregorian():
        out = ("{y}-{m:02d}-{d:02d}" if fmt == DEFAULT_DATE_FMT else fmt).format(y=d.year, m=d.month, d=d.day, month_name=MONTHS_EN[d.month - 1], weekday=WEEKDAYS_EN[d.weekday()])
        return out
    jy, jm, jd = date_to_jalali(d)
    out = fmt.format(y=jy, m=jm, d=jd, month_name=MONTHS_FA[jm - 1],
                     weekday=WEEKDAYS_FA[d.weekday()])
    return to_fa_digits(out) if fa_digits else out


def parse_jalali(text: str) -> dt.date:
    """Parse ``YYYY/MM/DD`` (Persian or Latin digits, ``/`` or ``-``)."""
    parts = to_en_digits(text).strip().replace("-", "/").split("/")
    if len(parts) != 3:
        raise ValueError(f"bad Jalali date: {text!r}")
    return jalali_to_date(*(int(p) for p in parts))


def now_utc() -> dt.datetime:
    """Timezone-aware current UTC time."""
    return dt.datetime.now(UTC)


def to_utc(value: dt.datetime, assume: dt.tzinfo = TEHRAN) -> dt.datetime:
    """Return an aware UTC datetime; naive values are assumed to be in ``assume``."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=assume)
    return value.astimezone(UTC)


def to_tehran(value: dt.datetime) -> dt.datetime:
    """Convert an aware (or UTC-assumed naive) datetime to Tehran time."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(TEHRAN)


def jalali_year_bounds(jy: int) -> Tuple[dt.datetime, dt.datetime]:
    """UTC [start, end) bounds of Jalali year ``jy`` (Tehran midnight to midnight)."""
    start = dt.datetime.combine(jalali_to_date(jy, 1, 1), dt.time(), tzinfo=TEHRAN)
    end = dt.datetime.combine(jalali_to_date(jy + 1, 1, 1), dt.time(), tzinfo=TEHRAN)
    return start.astimezone(UTC), end.astimezone(UTC)


def format_duration(seconds: int, fa_digits: bool = False) -> str:
    """``3725`` -> ``1:02`` (h:mm). Negative values clamp to zero."""
    seconds = max(0, int(seconds))
    text = f"{seconds // 3600}:{(seconds % 3600) // 60:02d}"
    return to_fa_digits(text) if fa_digits else text
