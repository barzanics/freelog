"""Benchmark core performance: python -m worktracker.tools.bench"""
import datetime as dt
import tempfile
import time
from pathlib import Path

from worktracker.core.database import Database
from worktracker.core.models import TimeEntry
from worktracker.core.persian import UTC
from worktracker.services.analytics import Analytics


def main(n: int = 100_000) -> None:
    with tempfile.TemporaryDirectory() as d:
        db = Database(Path(d) / "b.db")
        base = dt.datetime(2026, 3, 21, 4, tzinfo=UTC)
        t = time.perf_counter()
        with db.transaction() as c:
            for i in range(n):
                e = TimeEntry(title=f"task {i}", start_utc=base + dt.timedelta(minutes=5 * i), end_utc=base + dt.timedelta(minutes=5 * i + 4), category="dev")
                r = e.to_row()
                c.execute(f"INSERT INTO entries ({','.join(chr(34) + k + chr(34) for k in r)}) VALUES ({','.join('?' * len(r))})", tuple(r.values()))
        print(f"insert {n}: {time.perf_counter() - t:.2f}s")
        t = time.perf_counter(); rows = db.entries_between(base, base + dt.timedelta(days=2))
        print(f"day-range query ({len(rows)} rows): {(time.perf_counter() - t) * 1000:.1f} ms")
        t = time.perf_counter(); db.search("task 99999")
        print(f"search over {n}: {(time.perf_counter() - t) * 1000:.1f} ms")
        t = time.perf_counter(); s = Analytics(db).year_summary(1405)
        print(f"year summary ({s.total_hours:.0f} h): {(time.perf_counter() - t) * 1000:.0f} ms")
        db.close()


if __name__ == "__main__":
    main()
