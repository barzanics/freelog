"""Additional screens: planner, analytics, habits, team + mini timer, quick capture, year review.

Each ``build_*`` receives the MainWindow (for theme/db/helpers) and appends one page to ``win.pages``.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)

from ..core.models import Habit, Member, Project, Status, TimeEntry
from ..core.persian import (MONTHS_FA, WEEKDAYS_FA, date_to_jalali, format_duration, format_jalali, jalali_year_bounds, now_utc,
                            to_fa_digits, to_tehran)
from ..services import activity, insights, quick
from ..services.analytics import Analytics
from ..services.habits import HabitService
from ..services.planner import Planner
from ..services.team import Team
from . import pm_pages as pm
from .glass import BarChart, GlassButton
from .strings import S

log = logging.getLogger("worktracker.ui.extra")
WEEKDAY_SHORT = ("د", "س", "چ", "پ", "ج", "ش", "ی")   # Mon..Sun


def _page(win) -> tuple:
    page = QWidget()
    page.setStyleSheet(win._field_style())
    return page, QVBoxLayout(page)


def _item(text: str, uid: Optional[str] = None):
    from PyQt5.QtWidgets import QListWidgetItem
    it = QListWidgetItem(text)
    if uid is not None:
        it.setData(Qt.UserRole, uid)
    return it


# ---------------------------------------------------------------- planner
def build_planner(win) -> None:
    page, lay = _page(win)
    win.pl_date = win.label("", 14, True)
    btn = GlassButton(S["auto_schedule"], win.theme, primary=True)
    btn.clicked.connect(lambda _c=False: planner_auto(win))
    top = QHBoxLayout(); top.addWidget(win.pl_date, 1); top.addWidget(btn); lay.addLayout(top)
    row = QHBoxLayout()
    for attr, title in (("pl_free", S["free_slots"]), ("pl_tasks", S["planner"])):
        card = win.card(); cl = QVBoxLayout(card); cl.addWidget(win.label(title, 11, True))
        lw = QListWidget(); setattr(win, attr, lw); cl.addWidget(lw); row.addWidget(card, 1)
    lay.addLayout(row, 1)
    win.pages.addWidget(page)


def refresh_planner(win) -> None:
    today = to_tehran(now_utc()).date()
    win.pl_date.setText(to_fa_digits(format_jalali(today, "{weekday} {d} {month_name} {y}", fa_digits=False)))
    pl = Planner(win.db)
    win.pl_free.clear()
    for s, e in pl.day_free(today):
        win.pl_free.addItem(to_fa_digits(f"{s:%H:%M} – {e:%H:%M}"))
    win.pl_tasks.clear()
    for e in win.db.all(TimeEntry, "start_utc"):
        if e.status != Status.PLANNED or e.parent_id:
            continue
        when = to_tehran(e.start_utc).strftime("%m/%d %H:%M") if e.end_utc else "—"
        win.pl_tasks.addItem(_item(to_fa_digits(f"{when}   {e.title}   ({e.estimated_min or 30}m)"), e.id))


def planner_auto(win) -> None:
    try:
        pl = Planner(win.db)
        today = to_tehran(now_utc()).date()
        todo = [e for e in win.db.all(TimeEntry) if e.status == Status.PLANNED and e.end_utc is None and not e.parent_id]
        placed = pl.auto_schedule(todo, today, now=to_tehran(now_utc()))
        for tid, start in placed.items():
            if start is not None:
                pl.time_block(tid, start)
        refresh_planner(win)
    except Exception as exc:  # noqa: BLE001 - UI boundary
        log.exception("auto schedule failed")
        QMessageBox.warning(win, S["error"], str(exc))


# ---------------------------------------------------------------- analytics
def build_analytics(win) -> None:
    page, lay = _page(win)
    top = QHBoxLayout()
    review = GlassButton(S["year_review"], win.theme, primary=True)
    review.clicked.connect(lambda _c=False: show_year_review(win))
    top.addStretch(); top.addWidget(review); lay.addLayout(top)
    card = win.card(); cl = QVBoxLayout(card); cl.setContentsMargins(20, 14, 20, 14)
    win.an_weekday = BarChart(win.theme, WEEKDAY_SHORT); cl.addWidget(win.an_weekday)
    win.an_text = win.label("", 11); win.an_text.setWordWrap(True); cl.addWidget(win.an_text, 1)
    lay.addWidget(card, 1)
    pm.build_sankey(win, lay)
    win.pages.addWidget(page)


def refresh_analytics(win) -> None:
    db = win.db
    today = to_tehran(now_utc()).date()
    jy = date_to_jalali(today)[0]
    s = Analytics(db).year_summary(jy, today)
    win.an_weekday.set_values([x / 3600 for x in s.by_weekday])
    pm.refresh_sankey(win, jy)
    start, _ = jalali_year_bounds(jy)
    days = max(1, (today - to_tehran(start).date()).days + 1)
    lines: List[str] = [f"امتیاز بهره‌وری: {Analytics.productivity_score(s.total_sec, s.days_worked, days)} از ۱۰۰"]
    w = insights.week_over_week(db, today)
    lines.append(f"این هفته {w['a_hours']} ساعت (هفته قبل: {w['b_hours']}، تغییر {w['change_pct']}٪)")
    y = insights.year_over_year(db, jy)
    lines.append(f"امسال {y['a_hours']} ساعت — سال قبل {y['b_hours']} ساعت")
    peaks = insights.peak_hours(s)
    if peaks:
        lines.append("ساعت‌های اوج کار: " + "، ".join(f"{h}:۰۰" for h in peaks))
    eff = insights.early_start_effect(db, to_tehran(start).date(), today + dt.timedelta(days=1))
    if eff:
        lines.append(f"روزهایی که قبل از ۹ شروع کرده‌اید {eff['difference_pct']}٪ تفاوت در ساعت کار داشتند")
    todays = db.entries_between(dt.datetime.combine(today, dt.time(), tzinfo=to_tehran(now_utc()).tzinfo),
                                dt.datetime.combine(today + dt.timedelta(days=1), dt.time(), tzinfo=to_tehran(now_utc()).tzinfo))
    sw = insights.context_switches(todays)
    lines.append(f"تعویض زمینه امروز: {sw} (هزینهٔ تقریبی {insights.switch_cost_minutes(sw):.0f} دقیقه)")
    lines.append(insights.weekly_review(db, today))
    sk = insights.sankey(db, jy)["links"][:6]
    if sk:
        lines.append("جریان زمان: " + " | ".join(f"{l['source']}→{l['target']} {l['hours']}h" for l in sk))
    week_ago = now_utc() - dt.timedelta(days=7)
    usage = activity.app_usage(db, week_ago, now_utc())[:5]
    if usage:
        lines.append("برنامه‌های پرکاربرد: " + "، ".join(f"{a} ({sec // 60}m)" for a, sec in usage))
    win.an_text.setText(to_fa_digits("\n\n".join(lines)))


def show_year_review(win) -> None:
    jy = date_to_jalali(to_tehran(now_utc()).date())[0]
    r = insights.year_in_review(win.db, jy)
    if r.get("empty"):
        QMessageBox.information(win, S["year_review"], "هنوز داده‌ای برای امسال ثبت نشده است.")
        return
    wd = ("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")[int(r["favorite_weekday"])]  # type: ignore[arg-type]
    text = (f"🎉 سال {jy}\n\n⏱ {r['total_hours']} ساعت کار در {r['days_worked']} روز\n🔥 طولانی‌ترین رشته: {r['longest_streak']} روز\n"
            f"🏆 پروژهٔ اول: {r['top_project']} ({r['top_project_hours']} ساعت)\n📅 پرکارترین روز: {r['busiest_day']} ({r['busiest_day_hours']} ساعت)\n"
            f"🗓 روز محبوب: {wd}\n🌸 بهترین ماه: {r['best_month']}")
    QMessageBox.information(win, S["year_review"], to_fa_digits(text))


# ---------------------------------------------------------------- habits
def build_habits(win) -> None:
    page, lay = _page(win)
    card = win.card(); cl = QHBoxLayout(card); cl.setContentsMargins(18, 14, 18, 14)
    win.h_name = QLineEdit(placeholderText=S["add_habit"])
    add = GlassButton(S["add_habit"], win.theme, primary=True); add.clicked.connect(lambda _c=False: add_habit(win))
    check = GlassButton(S["check_in"], win.theme); check.clicked.connect(lambda _c=False: check_in(win))
    for w in (win.h_name, add, check):
        cl.addWidget(w)
    win.h_list = QListWidget(); win.h_list.setCursor(Qt.PointingHandCursor)
    lay.addWidget(card); lay.addWidget(win.h_list, 1)
    win.pages.addWidget(page)


def add_habit(win) -> None:
    name = win.h_name.text().strip()
    if not name:
        QMessageBox.warning(win, S["error"], S["need_title"]); return
    win.db.save(Habit(name=name)); win.h_name.clear(); refresh_habits(win)


def check_in(win) -> None:
    it = win.h_list.currentItem()
    if it:
        HabitService(win.db).check_in(it.data(Qt.UserRole)); refresh_habits(win)


def refresh_habits(win) -> None:
    hs = HabitService(win.db)
    win.h_list.clear()
    for h in win.db.all(Habit):
        longest, cur = hs.streak(h.id)
        win.h_list.addItem(_item(to_fa_digits(f"{h.name}  —  🔥 {cur}  (بیشترین {longest})  —  هفته: {int(hs.week_completion(h.id) * 100)}٪"), h.id))


# ---------------------------------------------------------------- team
def build_team(win) -> None:
    page, lay = _page(win)
    card = win.card(); cl = QHBoxLayout(card); cl.setContentsMargins(18, 14, 18, 14)
    win.m_name = QLineEdit(placeholderText=S["member"])
    add = GlassButton(S["add_member"], win.theme, primary=True); add.clicked.connect(lambda _c=False: add_member(win))
    cl.addWidget(win.m_name); cl.addWidget(add)
    assign = win.card(); al = QHBoxLayout(assign); al.setContentsMargins(18, 14, 18, 14)
    win.m_task, win.m_member = QComboBox(), QComboBox()
    ab = GlassButton(S["assign"], win.theme); ab.clicked.connect(lambda _c=False: assign_task(win))
    for w in (win.m_task, win.m_member, ab):
        al.addWidget(w)
    cm = win.card(); cml = QHBoxLayout(cm); cml.setContentsMargins(18, 14, 18, 14)
    win.m_comment = QLineEdit(placeholderText=S["comment"]); win.m_comment.returnPressed.connect(lambda: post_comment(win))
    cb = GlassButton(S["comment"], win.theme); cb.clicked.connect(lambda _c=False: post_comment(win))
    cml.addWidget(win.m_comment); cml.addWidget(cb)
    win.m_list, win.m_thread = QListWidget(), QListWidget()
    row = QHBoxLayout(); row.addWidget(win.m_list, 1); row.addWidget(win.m_thread, 2)
    for w in (card, assign, cm):
        lay.addWidget(w)
    lay.addLayout(row, 1)
    win.m_task.currentIndexChanged.connect(lambda _i=0: refresh_thread(win))
    win.pages.addWidget(page)


def add_member(win) -> None:
    try:
        Team(win.db).add_member(win.m_name.text()); win.m_name.clear(); refresh_team(win)
    except ValueError as exc:
        QMessageBox.warning(win, S["error"], str(exc))


def assign_task(win) -> None:
    tid, mid = win.m_task.currentData(), win.m_member.currentData()
    if tid:
        Team(win.db).assign(tid, mid); refresh_team(win)


def post_comment(win) -> None:
    tid, mid, text = win.m_task.currentData(), win.m_member.currentData(), win.m_comment.text()
    if not (tid and mid and text.strip()):
        return
    try:
        Team(win.db).comment(tid, mid, text); win.m_comment.clear(); refresh_thread(win)
    except ValueError as exc:
        QMessageBox.warning(win, S["error"], str(exc))


def refresh_thread(win) -> None:
    win.m_thread.clear()
    tid = win.m_task.currentData()
    if not tid:
        return
    names = {m.id: m.name for m in win.db.all(Member)}
    for node in Team(win.db).thread(tid):
        c = node["comment"]
        win.m_thread.addItem("    " * node["depth"] + f"{names.get(c.author_id, '?')}: {c.text}")


def refresh_team(win) -> None:
    team = Team(win.db)
    members = win.db.all(Member)
    win.m_member.clear()
    for m in members:
        win.m_member.addItem(m.name, m.id)
    win.m_task.clear()
    for e in win.db.all(TimeEntry, "start_utc DESC")[:200]:
        if not e.parent_id:
            win.m_task.addItem(e.title, e.id)
    load = team.workload_hours()
    win.m_list.clear()
    for m in members:
        win.m_list.addItem(to_fa_digits(f"{m.name} — {load.get(m.name, 0)}h — {len(team.tasks_of(m.id))} کار — 🔔 {len(team.unread(m.id))}"))
    refresh_thread(win)


# ---------------------------------------------------------------- mini timer + quick capture
class MiniTimer(QWidget):
    """Frameless always-on-top floating timer (drag to move)."""

    def __init__(self, on_stop) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._drag = None
        self.setStyleSheet("QWidget{background:rgba(20,20,35,215);border:1px solid rgba(255,255,255,70);border-radius:16px;}"
                           "QLabel{color:white;font-size:11pt;border:none;background:transparent;}"
                           "QPushButton{color:white;background:rgba(255,255,255,40);border:none;border-radius:10px;padding:4px 10px;}")
        lay = QHBoxLayout(self); lay.setContentsMargins(14, 8, 14, 8)
        self.title, self.clock = QLabel("—"), QLabel("0:00:00")
        self.btn = QPushButton("■"); self.btn.setCursor(Qt.PointingHandCursor); self.btn.clicked.connect(on_stop)
        for w in (self.title, self.clock, self.btn):
            lay.addWidget(w)

    def set_state(self, title: str, seconds: int) -> None:
        self.title.setText(title[:24] or "—")
        self.clock.setText(to_fa_digits(f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"))

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._drag = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._drag = None


def quick_capture(win) -> None:
    """Prompt for "title #tag @project 45m"; with a duration it logs a finished entry, otherwise it starts a timer."""
    text, ok = QInputDialog.getText(win, S["quick"], S["quick_hint"])
    if not ok or not text.strip():
        return
    try:
        cap = quick.parse(text)
        pid = None
        if cap.project:
            pid = next((p.id for p in win.db.all(Project) if p.name.lower() == cap.project.lower()), None)
        if cap.minutes:
            end = now_utc()
            win.tracker.add_manual(cap.title, end - dt.timedelta(minutes=cap.minutes), end, tags=cap.tags, project_id=pid)
        else:
            win.tracker.start(cap.title, project_id=pid, tags=cap.tags)
            win.clock.start(); win.idle_timer.start(); win.reminder_timer.start()
        win.refresh_all()
    except ValueError as exc:
        QMessageBox.warning(win, S["error"], str(exc))
