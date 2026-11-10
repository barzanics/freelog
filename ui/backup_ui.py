"""Backup / restore dialogs and flows (Settings > Data). Every flow can be driven with explicit arguments so it is testable without file pickers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLabel, QLineEdit, QMessageBox

from ..core.persian import now_utc, to_fa_digits, to_tehran, tr
from ..services import backup_pack as bp
from ..services import security
from .dialogs import PopDialog
from .forms import Section, Segmented
from .glass import GlassButton, LiquidSwitch
from .strings import S

log = logging.getLogger("worktracker.backup_ui")


@dataclass
class ExportOptions:
    include_history: bool = False
    include_screenshots: bool = False
    password: Optional[str] = None


@dataclass
class RestoreChoice:
    mode: str = "replace"
    conflict: str = "newer"
    include_settings: bool = True
    include_screenshots: bool = True


class ExportOptionsDialog(PopDialog):
    def __init__(self, win) -> None:
        super().__init__(win, S["bk_export_title"], "download", 560)
        self.history, self.shots, self.enc = LiquidSwitch(win.theme), LiquidSwitch(win.theme), LiquidSwitch(win.theme)
        self.pw, self.pw2 = QLineEdit(), QLineEdit()
        for w in (self.pw, self.pw2):
            w.setEchoMode(QLineEdit.Password)
        sec = Section(S["bk_what"])
        for sw, label in ((self.history, S["bk_history"]), (self.shots, S["bk_shots"]), (self.enc, S["bk_encrypt"])):
            from .pages_ops import _row
            sec.add("", _row(label, sw))
        sec.pair(S["password"], self.pw, S["bk_repeat"], self.pw2)
        self.body.addWidget(sec)
        self.body.addWidget(win.label(S["bk_export_note"], 9, muted=True))
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["bk_export_go"], self.theme, primary=True, icon="download"); ok.clicked.connect(self._ok)
        self.buttons(cancel, ok)

    def _ok(self) -> None:
        if self.enc.isChecked():
            if len(self.pw.text()) < 6:
                self.show_error(S["bk_pw_short"]); return
            if self.pw.text() != self.pw2.text():
                self.show_error(S["bk_pw_mismatch"]); return
        self.accept()

    def options(self) -> ExportOptions:
        return ExportOptions(self.history.isChecked(), self.shots.isChecked(), self.pw.text() if self.enc.isChecked() else None)


class RestoreDialog(PopDialog):
    def __init__(self, win, manifest: Dict[str, Any]) -> None:
        super().__init__(win, S["bk_restore_title"], "upload", 600)
        tables = manifest.get("tables", {})
        rows = sum(tables.values())
        when = manifest.get("created_at", "")[:16].replace("T", " ")
        info = [f"{S['bk_created']}: {when}", f"{S['bk_version']}: {manifest.get('app_version', '?')}  (schema {manifest.get('schema_version', '?')})",
                f"{S['bk_rows']}: {rows}   ·   {S['bk_tasks']}: {tables.get('entries', 0)}   ·   {S['projects']}: {tables.get('projects', 0)}   ·   {S['bk_invoices']}: {tables.get('invoices', 0)}",
                f"{S['bk_settings_n']}: {manifest.get('settings_keys', 0)}   ·   {S['bk_shot_archives']}: {manifest.get('screenshot_archives', 0)}"]
        lab = QLabel(to_fa_digits("\n".join(info))); lab.setWordWrap(True); lab.setTextInteractionFlags(Qt.TextSelectableByMouse); self.body.addWidget(lab)
        self.mode = Segmented([(S["bk_replace"], "replace"), (S["bk_merge"], "merge")], wrap=False); self.mode.changed.connect(self._mode)
        self.conflict = Segmented([(S["bk_newer"], "newer"), (S["bk_package"], "package"), (S["bk_keep"], "keep")], wrap=False)
        self.settings_sw, self.shots_sw = LiquidSwitch(win.theme, True), LiquidSwitch(win.theme, True)
        sec = Section(S["bk_how"]); sec.add(S["bk_mode"], self.mode); self.cf_cell = sec.add(S["bk_conflict"], self.conflict)
        from .pages_ops import _row
        sec.add("", _row(S["bk_with_settings"], self.settings_sw)); sec.add("", _row(S["bk_with_shots"], self.shots_sw))
        self.body.addWidget(sec)
        self.warn = QLabel(); self.warn.setWordWrap(True); self.body.addWidget(self.warn)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        self.go = GlassButton(S["bk_restore_go"], self.theme, danger=True, icon="upload"); self.go.clicked.connect(self.accept)
        self.buttons(cancel, self.go)
        self._mode("replace")

    def _mode(self, mode) -> None:
        replace = mode == "replace"
        self.conflict.setEnabled(not replace)
        self.warn.setText(("⚠ " + S["bk_warn_replace"]) if replace else S["bk_note_merge"])
        self.warn.setProperty("danger", replace); self.warn.setProperty("muted", not replace)

    def choice(self) -> RestoreChoice:
        return RestoreChoice(self.mode.value(), self.conflict.value(), self.settings_sw.isChecked(), self.shots_sw.isChecked())


class ConfigImportDialog(PopDialog):
    def __init__(self, win, plan: Dict[str, list]) -> None:
        super().__init__(win, S["bk_cfg_title"], "upload", 560)
        txt = [f"{S['bk_cfg_new']}: {len(plan['new'])}", f"{S['bk_cfg_changed']}: {len(plan['changed'])}", f"{S['bk_cfg_same']}: {len(plan['same'])}", f"{S['bk_cfg_ignored']}: {len(plan['ignored'])}"]
        if plan["changed"]:
            txt.append("\n" + S["bk_cfg_will_change"] + ": " + "، ".join(plan["changed"][:14]) + (" …" if len(plan["changed"]) > 14 else ""))
        lab = QLabel(to_fa_digits("\n".join(txt))); lab.setWordWrap(True); self.body.addWidget(lab)
        self.mode = Segmented([(S["bk_cfg_merge"], "merge"), (S["bk_cfg_replace"], "replace")], wrap=False); self.body.addWidget(self.mode)
        cancel = GlassButton(S["cancel"], self.theme); cancel.clicked.connect(self.reject)
        ok = GlassButton(S["bk_cfg_apply"], self.theme, primary=True, icon="check"); ok.clicked.connect(self.accept); self.buttons(cancel, ok)


# ======================================================================== flows
def _warn(win, text: str) -> None:
    QMessageBox.warning(win, S["error"], text)


def export_package_ui(win, path: Optional[str] = None, options: Optional[ExportOptions] = None) -> Optional[Path]:
    """Ask for options + a file name, write a verified package. Returns the path (or None if cancelled)."""
    if options is None:
        dlg = ExportOptionsDialog(win)
        if not dlg.exec_():
            return None
        options = dlg.options()
    if path is None:
        path, _ = QFileDialog.getSaveFileName(win, S["bk_export_title"], f"worktracker-{to_tehran(now_utc()):%Y%m%d}.wtpack", "WorkTracker (*.wtpack)")
        if not path:
            return None
    try:
        out = bp.export_package(win.db, path, include_history=options.include_history,
                                screenshots_dir=(win.data_dir / "screenshots") if options.include_screenshots else None, password=options.password)
        bp.verify_package(out, options.password, win.db.version)                       # read it back: never trust a backup you have not verified
    except Exception as exc:  # noqa: BLE001 - UI boundary
        log.exception("export failed"); _warn(win, f"{S['bk_failed']}: {exc}"); return None
    win.db.set_setting("last_backup_at", now_utc().isoformat())
    win.toast(to_fa_digits(f"{S['bk_done']} · {out.stat().st_size / 1048576:.1f} MB"))
    if win.theme.fx is not None:
        win.theme.fx.play("success")
    return Path(out)


def restore_package_ui(win, path: Optional[str] = None, password: Optional[str] = None, choice: Optional[RestoreChoice] = None) -> Optional[bp.RestoreReport]:
    """Pick a package, verify it, show what is inside, restore atomically (safety backup first). Returns the report (or None)."""
    if path is None:
        path, _ = QFileDialog.getOpenFileName(win, S["bk_restore_title"], "", "WorkTracker (*.wtpack *.zip);;All (*)")
        if not path:
            return None
    try:
        if Path(path).read_bytes()[:4] == security.MAGIC and password is None:
            password, ok = QInputDialog.getText(win, S["password"], S["bk_enter_pw"], QLineEdit.Password)
            if not ok:
                return None
        manifest = bp.verify_package(path, password, win.db.version)
    except security.DecryptError:
        _warn(win, S["bk_wrong_pw"]); return None
    except bp.PackageError as exc:
        _warn(win, f"{S['bk_invalid']}: {exc}"); return None
    if choice is None:
        dlg = RestoreDialog(win, manifest)
        if not dlg.exec_():
            return None
        choice = dlg.choice()
    try:
        rep = bp.restore_package(win.db, path, choice.mode, password, backup_dir=win.data_dir / "backups",
                                 screenshots_dir=(win.data_dir / "screenshots") if choice.include_screenshots else None,
                                 include_settings=choice.include_settings, conflict=choice.conflict)
    except (bp.RestoreError, bp.PackageError) as exc:
        log.exception("restore failed"); _warn(win, f"{S['bk_restore_failed']}: {exc}"); return None
    win.after_restore()
    win.toast(to_fa_digits(f"{S['bk_restored']} · {rep.total_rows} {S['rows']}"))
    return rep


def export_config_ui(win, path: Optional[str] = None, include_secrets: Optional[bool] = None) -> Optional[Path]:
    if include_secrets is None:
        include_secrets = QMessageBox.question(win, S["bk_cfg_export"], S["bk_cfg_secrets"]) == QMessageBox.Yes
    if path is None:
        path, _ = QFileDialog.getSaveFileName(win, S["bk_cfg_export"], "worktracker-settings.json", "JSON (*.json)")
        if not path:
            return None
    try:
        out = bp.export_config(win.db, path, include_secrets)
    except Exception as exc:  # noqa: BLE001
        log.exception("config export failed"); _warn(win, f"{S['bk_failed']}: {exc}"); return None
    win.toast(S["saved"])
    return Path(out)


def import_config_ui(win, path: Optional[str] = None, mode: Optional[str] = None) -> Optional[Dict[str, list]]:
    if path is None:
        path, _ = QFileDialog.getOpenFileName(win, S["bk_cfg_import"], "", "JSON (*.json)")
        if not path:
            return None
    try:
        plan = bp.diff_config(win.db, path)
        if mode is None:
            dlg = ConfigImportDialog(win, plan)
            if not dlg.exec_():
                return None
            mode = dlg.mode.value()
        plan = bp.import_config(win.db, path, mode)
    except bp.PackageError as exc:
        _warn(win, f"{S['bk_invalid']}: {exc}"); return None
    win.after_restore()
    win.toast(to_fa_digits(f"{S['saved']} · {len(plan['new']) + len(plan['changed'])}"))
    return plan
