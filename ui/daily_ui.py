"""The daily report window: pick a day, get the formal report, edit it, copy it, save it (txt / md / html) or send it (Slack / Telegram if configured)."""
from __future__ import annotations

import datetime as dt
import logging
import threading
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QWidget

from ..core.persian import format_duration, now_utc, to_fa_digits, to_tehran
from ..integrations import chat
from ..services import daily_report as dr
from .dialogs import PopDialog
from .forms import JalaliDateEdit, chip_button
from .glass import GlassButton
from .strings import S

log = logging.getLogger("worktracker.daily")


class DailyReportDialog(PopDialog):
    def __init__(self, win, day: Optional[dt.date] = None) -> None:
        super().__init__(win, S["dr_title"], "reports", 760)
        self.day = day or to_tehran(now_utc()).date()
        self.rep: Optional[dr.DailyReport] = None
        from .pages_new import arrow_icon
        row = QHBoxLayout(); row.setSpacing(8)
        prv = GlassButton("", self.theme, icon=arrow_icon(win, False)); prv.setFixedSize(40, 40); prv.clicked.connect(lambda: self._shift(-1))
        nxt = GlassButton("", self.theme, icon=arrow_icon(win, True)); nxt.setFixedSize(40, 40); nxt.clicked.connect(lambda: self._shift(1))
        self.picker = JalaliDateEdit(); self.picker.setDate(self.day); self.picker.changed.connect(self._picked)
        today = chip_button(S["today"]); today.clicked.connect(lambda: self._set(to_tehran(now_utc()).date()))
        for w in (prv, self.picker, nxt, today):
            row.addWidget(w)
        row.addStretch(); self.body.addLayout(row)
        self.info = QLabel(""); self.info.setProperty("muted", True); self.info.setWordWrap(True); self.body.addWidget(self.info)
        self.text = QPlainTextEdit(); self.text.setMinimumHeight(max(260, min(380, win.height() - 360))); self.body.addWidget(self.text, 1)
        regen = GlassButton(S["dr_regenerate"], self.theme, icon="refresh"); regen.clicked.connect(self.generate)
        cp = GlassButton(S["dr_copy"], self.theme, icon="copy"); cp.clicked.connect(self.copy)
        sv = GlassButton(S["dr_save"], self.theme, primary=True, icon="download"); sv.clicked.connect(self.save)
        self.footer.addWidget(regen); self.footer.addStretch(); self.footer.addWidget(cp)
        if win.db.get_setting("slack_url") or (win.db.get_setting("tg_token") and win.db.get_setting("tg_chat")):
            sd = GlassButton(S["dr_send"], self.theme, icon="upload"); sd.clicked.connect(self.send); self.footer.addWidget(sd)
        self.footer.addWidget(sv)
        self._pending: Optional[dict] = None
        self.generate()

    # ---- content -----------------------------------------------------------------------------
    def _set(self, d: dt.date) -> None:
        self.day = d; self.picker.setDate(d); self.generate()

    def _shift(self, n: int) -> None:
        self._set(self.day + dt.timedelta(days=n))

    def _picked(self) -> None:
        d = self.picker.date() if self.picker.isValid() else None
        if d and d != self.day:
            self.day = d; self.generate()

    def generate(self) -> None:
        self.rep = dr.build(self.db, self.day)
        self.text.setPlainText(dr.to_text(self.rep, str(self.db.get_setting("author_name", "") or "")))
        if self.rep.empty:
            self.info.setText(S["dr_nothing"])
        else:
            self.info.setText(to_fa_digits(f"{S['dr_total']}: {format_duration(self.rep.total_sec)}   ·   {len(self.rep.lines)} {S['dr_entries']}"))

    # ---- output ---------------------------------------------------------------------------------
    def copy(self) -> None:
        QApplication.clipboard().setText(self.text.toPlainText())
        self.win.toast(S["dr_copied"])
        if self.theme.fx is not None:
            self.theme.fx.play("success")

    def save(self, path: Optional[str] = None) -> Optional[Path]:
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, S["dr_save"], f"daily-report-{self.day}.txt", "Text (*.txt);;Markdown (*.md);;HTML (*.html)")
            if not path:
                return None
        assert self.rep is not None
        author = str(self.db.get_setting("author_name", "") or "")
        p = Path(path)
        content = {"md": lambda: dr.to_markdown(self.rep, author), "html": lambda: dr.to_html(self.rep, author)}.get(p.suffix.lower().lstrip("."), self.text.toPlainText)()
        p.write_text(content, encoding="utf-8")
        self.win.toast(S["saved"])
        return p

    def send(self) -> None:
        """Slack / Telegram in a worker thread (a slow network must never freeze the window); the result is polled on the GUI thread."""
        text, db = self.text.toPlainText(), self.db
        slack, tok, chat_id = db.get_setting("slack_url"), db.get_setting("tg_token"), db.get_setting("tg_chat")
        result = {"ok": None}

        def work() -> None:
            ok = False
            try:
                if slack:
                    ok = chat.slack_send(slack, text) or ok
                if tok and chat_id:
                    ok = chat.telegram_send(tok, int(chat_id), text) or ok
            except Exception:  # noqa: BLE001
                log.exception("send failed")
            result["ok"] = ok
        threading.Thread(target=work, daemon=True).start()
        timer = QTimer(self); timer.setInterval(300)

        def poll() -> None:
            if result["ok"] is not None:
                timer.stop(); self.win.toast(S["dr_sent"] if result["ok"] else S["dr_send_failed"])
        timer.timeout.connect(poll); timer.start(); self._poll = timer
