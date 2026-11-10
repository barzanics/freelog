"""Offline "AI": Naive Bayes categorizer, tag suggestions, duplicate/anomaly detection, estimates, summaries."""
from __future__ import annotations

import difflib
import math
import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

from ..core.database import Database
from ..core.models import TimeEntry
from ..core.persian import to_fa_digits, to_tehran

_TOKEN = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


def tokens(text: str) -> List[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1]


class NaiveBayes:
    """Multinomial NB with Laplace smoothing; serialisable to plain JSON."""

    def __init__(self) -> None:
        self.class_docs: Counter = Counter()
        self.word_counts: Dict[str, Counter] = defaultdict(Counter)
        self.vocab: set = set()

    def train(self, text: str, label: str) -> None:
        toks = tokens(text)
        if not toks:
            return
        self.class_docs[label] += 1
        for t in toks:
            self.word_counts[label][t] += 1
            self.vocab.add(t)

    def predict(self, text: str) -> Optional[Tuple[str, float]]:
        toks = [t for t in tokens(text) if t in self.vocab]
        if not toks or not self.class_docs:
            return None
        total_docs, v = sum(self.class_docs.values()), len(self.vocab)
        logs: Dict[str, float] = {}
        for c, n in self.class_docs.items():
            tot = sum(self.word_counts[c].values())
            logs[c] = math.log(n / total_docs) + sum(math.log((self.word_counts[c][t] + 1) / (tot + v)) for t in toks)
        m = max(logs.values())
        exp = {c: math.exp(x - m) for c, x in logs.items()}
        z = sum(exp.values())
        best = max(exp, key=exp.get)  # type: ignore[arg-type]
        return best, exp[best] / z

    def to_dict(self) -> dict:
        return {"docs": dict(self.class_docs), "words": {c: dict(w) for c, w in self.word_counts.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "NaiveBayes":
        nb = cls()
        nb.class_docs = Counter(d.get("docs", {}))
        for c, w in d.get("words", {}).items():
            nb.word_counts[c] = Counter(w)
            nb.vocab.update(w)
        return nb


class Smart:
    KEY = "nb_category"

    def __init__(self, db: Database) -> None:
        self.db = db
        self.nb = NaiveBayes.from_dict(db.get_setting(self.KEY, {}))

    def learn(self, title: str, category: str) -> None:
        """Call whenever the user sets or corrects a category."""
        self.nb.train(title, category)
        self.db.set_setting(self.KEY, self.nb.to_dict())

    def suggest_category(self, title: str, min_conf: float = 0.6) -> Optional[str]:
        r = self.nb.predict(title)
        return r[0] if r and r[1] >= min_conf else None

    def suggest_tags(self, title: str, top: int = 3) -> List[str]:
        """Tags most often used with the words of ``title`` in past entries."""
        words = set(tokens(title))
        score: Counter = Counter()
        for r in self.db.conn.execute("SELECT title, tags FROM entries WHERE tags!='[]' ORDER BY start_utc DESC LIMIT 2000"):
            import json
            overlap = len(words & set(tokens(r[0])))
            if overlap:
                for t in json.loads(r[1]):
                    score[t] += overlap
        return [t for t, _ in score.most_common(top)]

    def similar(self, title: str, threshold: float = 0.85, limit: int = 5) -> List[TimeEntry]:
        """Existing entries whose titles closely match (duplicate warning)."""
        t = title.lower().strip()
        found = []
        for e in self.db.all(TimeEntry, "start_utc DESC")[:2000]:
            r = difflib.SequenceMatcher(None, t, e.title.lower().strip()).ratio()
            if r >= threshold:
                found.append((r, e))
        return [e for _, e in sorted(found, key=lambda x: -x[0])[:limit]]

    def estimate(self, title: str, threshold: float = 0.6) -> Optional[Dict[str, float]]:
        """Average minutes of similar finished tasks."""
        t = title.lower()
        mins = [e.duration_sec / 60 for e in self.db.all(TimeEntry) if e.duration_sec > 0 and
                difflib.SequenceMatcher(None, t, e.title.lower()).ratio() >= threshold]
        return {"avg_min": round(mean(mins), 1), "samples": len(mins)} if mins else None

    def anomalies(self, daily_sec: Dict, max_hours: float = 12.0) -> List:
        """Days whose total exceeds ``max_hours`` (probably a forgotten running timer)."""
        return sorted(d for d, s in daily_sec.items() if s > max_hours * 3600)

    def daily_summary(self, entries: Iterable[TimeEntry], names: Dict[str, str]) -> str:
        """Template-based Persian summary (no LLM)."""
        es = [e for e in entries if e.duration_sec > 0]
        if not es:
            return "امروز کاری ثبت نشده است."
        total = sum(e.duration_sec for e in es)
        per: Counter = Counter()
        for e in es:
            per[names.get(e.project_id or "", "بدون پروژه")] += e.duration_sec
        top, top_sec = per.most_common(1)[0]
        longest = max(es, key=lambda e: e.duration_sec)
        return to_fa_digits(f"مجموع {total // 3600} ساعت و {total % 3600 // 60} دقیقه در {len(es)} ثبت. "
                            f"بیشترین زمان: «{top}» ({top_sec // 60} دقیقه). "
                            f"طولانی‌ترین کار: «{longest.title}» ({longest.duration_sec // 60} دقیقه).")
