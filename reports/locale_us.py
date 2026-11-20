"""US presentation rules for client-facing output: ``Mar 14, 2026`` dates, USD/EUR/GBP money, hours, Sunday-first weeks, US federal holidays, client time zones."""
from __future__ import annotations

import datetime as dt
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$", "AUD": "A$"}


def fmt_date(d: Optional[dt.date], long: bool = False) -> str:
    if d is None:
        return "—"
    if isinstance(d, dt.datetime):
        d = d.date()
    return f"{d.strftime('%A')}, {MONTHS[d.month - 1]} {d.day}, {d.year}" if long else f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_range(a: dt.date, b: dt.date) -> str:
    if a == b:
        return fmt_date(a)
    if a.year == b.year and a.month == b.month:
        return f"{MONTHS[a.month - 1]} {a.day}–{b.day}, {a.year}"
    if a.year == b.year:
        return f"{MONTHS[a.month - 1]} {a.day} – {MONTHS[b.month - 1]} {b.day}, {a.year}"
    return f"{fmt_date(a)} – {fmt_date(b)}"


def fmt_money(amount: float, currency: str = "USD") -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}{SYMBOLS.get(currency, currency + ' ')}{abs(amount):,.2f}"


def fmt_hours(seconds: float, decimals: int = 1) -> str:
    return f"{seconds / 3600:.{decimals}f} h"


def fmt_hm(seconds: float) -> str:
    m = int(round(seconds / 60))
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"


def fmt_pct(v: float) -> str:
    return f"{v:.0f}%"


def to_client_tz(t: dt.datetime, tz: str = "America/New_York") -> dt.datetime:
    try:
        return t.astimezone(ZoneInfo(tz))
    except Exception:  # noqa: BLE001 - an unknown zone name falls back to UTC rather than crashing a report
        return t.astimezone(dt.timezone.utc)


def _nth_weekday(y: int, m: int, weekday: int, n: int) -> dt.date:
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_weekday(y: int, m: int, weekday: int) -> dt.date:
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=1) if d.weekday() == 5 else (d + dt.timedelta(days=1) if d.weekday() == 6 else d)


def us_holidays(year: int) -> Dict[dt.date, str]:
    """US federal holidays (observed dates: Saturday -> Friday, Sunday -> Monday)."""
    fixed = {"New Year's Day": dt.date(year, 1, 1), "Juneteenth": dt.date(year, 6, 19), "Independence Day": dt.date(year, 7, 4), "Veterans Day": dt.date(year, 11, 11),
             "Christmas Day": dt.date(year, 12, 25)}
    out = {_observed(d): n for n, d in fixed.items()}
    out.update({_nth_weekday(year, 1, 0, 3): "Martin Luther King Jr. Day", _nth_weekday(year, 2, 0, 3): "Presidents' Day", _last_weekday(year, 5, 0): "Memorial Day",
                _nth_weekday(year, 9, 0, 1): "Labor Day", _nth_weekday(year, 10, 0, 2): "Columbus Day", _nth_weekday(year, 11, 3, 4): "Thanksgiving"})
    return out


def holiday_name(d: dt.date) -> Optional[str]:
    return us_holidays(d.year).get(d)


def is_business_day(d: dt.date) -> bool:
    return d.weekday() < 5 and holiday_name(d) is None


def next_business_day(d: dt.date) -> dt.date:
    d += dt.timedelta(days=1)
    while not is_business_day(d):
        d += dt.timedelta(days=1)
    return d


def add_business_days(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d = next_business_day(d)
        n -= 1
    return d


def week_bounds(d: dt.date, start: str = "sun") -> Tuple[dt.date, dt.date]:
    """The calendar week containing ``d``: Sunday–Saturday (US default) or Monday–Sunday."""
    offset = (d.weekday() + 1) % 7 if start == "sun" else d.weekday()
    a = d - dt.timedelta(days=offset)
    return a, a + dt.timedelta(days=6)
