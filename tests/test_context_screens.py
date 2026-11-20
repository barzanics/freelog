import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from worktracker.core.database import Database
from worktracker.core.models import Screenshot
from worktracker.core.persian import TEHRAN, UTC
from worktracker.services import context as cx, geometry as geo, screenshots as sh


def runner(stdout="", boom=False, calls=None):
    def run(cmd, **kw):
        if calls is not None: calls.append(cmd)
        if boom: raise OSError("not installed")
        return SimpleNamespace(stdout=stdout)
    return run


class ContextParsingTests(unittest.TestCase):
    def test_kinds(self):
        for app, kind in (("explorer.exe", "file_manager"), ("Finder", "file_manager"), ("dolphin", "file_manager"), ("chrome.exe", "browser"), ("msedge.exe", "browser"), ("firefox", "browser"),
                          ("Code.exe", "editor"), ("pycharm64.exe", "editor"), ("WindowsTerminal.exe", "terminal"), ("powershell.exe", "terminal"), ("figma.exe", "other"), ("", "other")):
            self.assertEqual(cx.kind_of(app), kind, app)

    def test_location_urls(self):
        self.assertEqual(cx.path_from_location_url("file:///C:/Users/Ann/My%20Docs/Site"), "C:\\Users\\Ann\\My Docs\\Site")
        self.assertEqual(cx.path_from_location_url("file://server/share/Clients/Acme"), "\\\\server\\share\\Clients\\Acme"); self.assertEqual(cx.path_from_location_url("file://localhost/D:/work"), "D:\\work")
        self.assertEqual(cx.path_from_location_url("file:///home/ann/Docs"), "/home/ann/Docs")
        for junk in ("", "shell:MyComputerFolder", "http://x/y", None): self.assertEqual(cx.path_from_location_url(junk), "")

    def test_explorer_active_tab_path(self):
        calls = []; out = json.dumps({"name": "Docs", "url": "file:///C:/Users/Ann/My%20Projects/Site%20v2"})
        r = cx.explorer_folder("Docs - File Explorer", runner(out, calls=calls), hwnd=4242); self.assertEqual(r, {"name": "Docs", "path": "C:\\Users\\Ann\\My Projects\\Site v2"})
        script = calls[0][-1]; self.assertIn("-eq 4242", script); self.assertIn("LocationName -eq 'Docs'", script)                      # the tab is matched by the title, the window by its handle
        self.assertIn("O''Neil", cx.explorer_script(1, "O'Neil"))                                                                       # quoting cannot be broken by a folder name
        self.assertIsNone(cx.explorer_folder("x", runner(boom=True), hwnd=1)); self.assertIsNone(cx.explorer_folder("x", runner(""), hwnd=1)); self.assertIsNone(cx.explorer_folder("x", runner("not json"), hwnd=1)); self.assertIsNone(cx.explorer_folder("x", runner(out), hwnd=0))

    def test_describe_every_kind(self):
        url = json.dumps({"name": "Invoices", "url": "file:///D:/Clients/Acme/Invoices"})
        self.assertEqual(cx.describe("explorer.exe", "Invoices - File Explorer", "win32", runner(url), hwnd=7)["text"], "File Explorer · D:\\Clients\\Acme\\Invoices")
        special = cx.describe("explorer.exe", "This PC - File Explorer", "win32", runner(json.dumps({"name": "This PC", "url": ""})), hwnd=7); self.assertEqual((special["path"], special["text"]), ("", "File Explorer · This PC"))
        self.assertEqual(cx.describe("explorer.exe", "Docs - File Explorer", "win32", runner(boom=True), hwnd=7)["text"], "File Explorer · Docs")                # PowerShell missing: falls back to the folder name
        d = cx.describe("dolphin", "/home/ann/Documents — Dolphin", "linux"); self.assertEqual((d["path"], d["text"]), ("/home/ann/Documents", "Dolphin · /home/ann/Documents"))
        self.assertEqual(cx.describe("Finder", "Desktop", "darwin", runner("/Users/ann/Desktop/\n"))["text"], "Finder · /Users/ann/Desktop/")
        self.assertEqual(cx.describe("chrome.exe", "Pricing - Acme Inc - Google Chrome", "win32")["text"], "Chrome · Tab: Pricing - Acme Inc"); self.assertEqual(cx.describe("msedge.exe", "Inbox - Microsoft Edge", "win32")["text"], "Edge · Tab: Inbox")
        self.assertEqual(cx.describe("Code.exe", "main.py - freelog - Visual Studio Code", "win32")["text"], "VS Code · main.py · freelog"); self.assertEqual(cx.describe("pycharm64.exe", "freelog – app.py", "win32")["detail"], "freelog · app.py")
        self.assertEqual(cx.describe("WindowsTerminal.exe", "C:\\work\\site", "win32")["text"], "Terminal · C:\\work\\site"); self.assertEqual(cx.describe("figma.exe", "Design", "win32")["text"], "")

    def test_text_is_sanitised_and_bounded(self):
        t = cx.describe("chrome.exe", "Evil\x00\x1b[31m tab\n" + "x" * 900 + " - Google Chrome", "win32")["text"]
        self.assertLessEqual(len(t), 300); self.assertFalse(any(ord(c) < 32 for c in t))


class ScreenshotScheduleTests(unittest.TestCase):
    def test_context_is_stored_with_the_screenshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(); store = sh.ScreenshotStore(db, Path(tmp), lambda: (b"\xff\xd8JFIF" + b"q" * 2000, 100, 60))
            shot, why = store.capture_result("explorer.exe", "Invoices", context="File Explorer · D:\\Clients\\Acme\\Invoices"); self.assertEqual(why, "ok")
            self.assertEqual(db.get(Screenshot, shot.id).context, "File Explorer · D:\\Clients\\Acme\\Invoices"); self.assertEqual(store.capture("a", "b", force=True).context, "")

    def test_effective_interval_is_bounded_deterministic_and_optional(self):
        self.assertEqual(sh.effective_interval(60, 0, "x"), 60.0)
        vals = {sh.effective_interval(60, 25, f"seed{i}") for i in range(200)}
        self.assertTrue(all(45 <= v <= 75 for v in vals)); self.assertGreater(len(vals), 20); self.assertEqual(sh.effective_interval(60, 25, "same"), sh.effective_interval(60, 25, "same"))
        self.assertEqual(sh.effective_interval(60, 999, "x") <= 90, True); self.assertGreaterEqual(sh.effective_interval(1, 50, "x"), 1.0)

    def test_private_capture_window(self):
        at = lambda h, day=2: dt.datetime(2026, 5, day, h, tzinfo=TEHRAN)                          # Saturday May 2 2026 (weekday 5)
        self.assertTrue(sh.within_schedule(at(10), 9, 18)); self.assertFalse(sh.within_schedule(at(8), 9, 18)); self.assertFalse(sh.within_schedule(at(18), 9, 18)); self.assertTrue(sh.within_schedule(at(3), 0, 24))
        self.assertTrue(sh.within_schedule(at(23), 22, 6)); self.assertTrue(sh.within_schedule(at(2), 22, 6)); self.assertFalse(sh.within_schedule(at(12), 22, 6))      # a night shift wraps midnight
        self.assertFalse(sh.within_schedule(at(10), 9, 18, days_off=[5])); self.assertTrue(sh.within_schedule(at(10, 3), 9, 18, days_off=[5]))

    def test_bubble_glow_fits_inside_its_window(self):
        for orb in (56, 66, 78):
            for margin in (26, 30):
                half = orb / 2 + margin
                self.assertLess(geo.glow_radius(orb, margin), half); self.assertGreater(geo.glow_radius(orb, margin), orb / 2)        # larger than the orb, never reaching the square's edge


if __name__ == "__main__":
    unittest.main()
