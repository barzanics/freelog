"""Fonts: loaded from the app's ``assets/fonts`` folder (same location as the v5 app), IRANSans first.

Drop IRANSans (.ttf/.otf) into ``assets/fonts`` next to the program (or next to this package). Pure helpers are Qt-free and unit-tested.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

PREFERRED = ["IRANSansX", "IRANSans", "IRANSans(FaNum)", "IRANSansWeb", "IRANSans FaNum", "IRANYekan", "Iran Sans", "Vazirmatn", "Vazir",
             "Shabnam", "Sahel", "Samim", "B Nazanin", "Tahoma", "Segoe UI", "Arial"]
EXTS = {".ttf", ".otf"}
_WEIGHT_WORDS = (("black", 900), ("heavy", 850), ("extrabold", 800), ("ultrabold", 800), ("bold", 700), ("demibold", 600), ("semibold", 600),
                 ("medium", 500), ("regular", 400), ("normal", 400), ("light", 300), ("thin", 200), ("ultralight", 200))


def norm(name: str) -> str:
    return re.sub(r"[\s_\-()]+", "", name).lower()


def candidate_dirs(base: Optional[Path] = None, extra: Iterable[Path] = ()) -> List[Path]:
    """Where to look, in order: env var, <base>/assets/fonts, <package>/../assets/fonts, <cwd>/assets/fonts, extras."""
    pkg = Path(__file__).resolve().parent.parent
    dirs: List[Path] = []
    if os.environ.get("WORKTRACKER_FONTS"):
        dirs.append(Path(os.environ["WORKTRACKER_FONTS"]))
    for b in (base, pkg, pkg.parent, Path.cwd()):
        if b:
            dirs.append(Path(b) / "assets" / "fonts")
    dirs.extend(Path(e) for e in extra)
    seen, out = set(), []
    for d in dirs:
        if str(d) not in seen:
            seen.add(str(d)); out.append(d)
    return out


def discover(dirs: Iterable[Path]) -> List[Path]:
    files: List[Path] = []
    for d in dirs:
        if d.is_dir():
            files += sorted(p for p in d.rglob("*") if p.suffix.lower() in EXTS)
    return files


def rank_family(name: str) -> int:
    n = norm(name)
    for i, pref in enumerate(PREFERRED):
        if n == norm(pref):
            return i
    for i, pref in enumerate(PREFERRED):               # e.g. "IRANSans Medium", "IRANSansWeb_Bold" -> its base family
        if n.startswith(norm(pref)):
            return i
    return 999


def pick_family(families: Iterable[str]) -> Optional[str]:
    fam = sorted(set(families), key=lambda f: (rank_family(f), len(f)))
    return fam[0] if fam and rank_family(fam[0]) < 999 else (fam[0] if fam else None)


def weight_of(text: str) -> int:
    n = norm(text)
    for word, w in _WEIGHT_WORDS:
        if word in n:
            return w
    return 400


def family_for_weight(families: Iterable[str], base: str, weight: int) -> str:
    """Pick the registered family that best represents ``weight`` for ``base`` (some IRANSans packs register 'IRANSans Bold' separately)."""
    nb = norm(base)
    cands = [f for f in families if norm(f).startswith(nb) and f != base]
    best, gap = base, 10 ** 6
    for f in cands:
        g = abs(weight_of(f) - weight)
        if weight_of(f) != 400 and g < gap and g <= 100:
            best, gap = f, g
    return best


@dataclass
class FontInfo:
    primary: str = "Tahoma"
    families: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    searched: List[str] = field(default_factory=list)
    found_iransans: bool = False

    def stack(self) -> str:
        """CSS/QSS font-family stack."""
        ordered = [self.primary] + [f for f in sorted(self.families, key=rank_family) if f != self.primary][:3]
        ordered += ["Vazirmatn", "Tahoma", "Segoe UI", "Arial", "sans-serif"]
        seen, out = set(), []
        for f in ordered:
            if f not in seen:
                seen.add(f); out.append(f"'{f}'" if f != "sans-serif" else f)
        return ", ".join(out)

    def family(self, weight: int = 400) -> str:
        return family_for_weight(self.families, self.primary, weight)

    def missing_message(self) -> str:
        return "" if self.found_iransans else ("فونت ایران‌سنس پیدا نشد؛ فایل‌های IRANSans را در پوشه‌ی assets/fonts کنار برنامه بگذارید. (جست‌وجو در: "
                                                + " | ".join(self.searched[:3]) + ")")


def load(base: Optional[Path] = None, extra: Iterable[Path] = ()) -> FontInfo:
    """Register every font file found and choose the primary family. Requires a running QApplication."""
    from PyQt5.QtGui import QFontDatabase
    dirs = candidate_dirs(base, extra)
    info = FontInfo(searched=[str(d) for d in dirs])
    for f in discover(dirs):
        fid = QFontDatabase.addApplicationFont(str(f))
        if fid != -1:
            info.files.append(f.name)
            info.families += [x for x in QFontDatabase.applicationFontFamilies(fid) if x not in info.families]
    info.found_iransans = any("iransans" in norm(f) or "iranyekan" in norm(f) for f in info.families)
    info.primary = pick_family(info.families or []) or pick_family(QFontDatabase().families()) or "Tahoma"
    if rank_family(info.primary) >= 999:
        for cand in PREFERRED:
            if cand in QFontDatabase().families():
                info.primary = cand
                break
    return info


def apply_app_font(app, info: FontInfo, size: int = 10) -> None:
    from PyQt5.QtGui import QFont
    f = QFont(info.primary, size)
    f.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(f)
