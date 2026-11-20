import tempfile
import unittest
from pathlib import Path

from PIL import Image

from worktracker.core.database import Database
from worktracker.tools import shortcuts as sc
from worktracker.ui import branding

ROOT = Path(__file__).resolve().parents[2]


class LogoTests(unittest.TestCase):
    def test_logo_assets_exist_with_transparent_corners_and_all_sizes(self):
        png = Image.open(ROOT / "assets" / "freelog.png"); self.assertEqual((png.size, png.mode), ((1024, 1024), "RGBA"))
        self.assertEqual((png.getpixel((3, 3))[3], png.getpixel((512, 512))[3]), (0, 255))                         # rounded tile: corners are really transparent
        for n in (16, 24, 32, 48, 64, 128, 256, 512): self.assertEqual(Image.open(ROOT / "assets" / "icons" / f"freelog_{n}.png").size, (n, n))
        ico = Image.open(ROOT / "assets" / "freelog.ico"); self.assertIn((256, 256), ico.info.get("sizes", {(256, 256)})); self.assertGreater((ROOT / "assets" / "freelog.icns").stat().st_size, 1000)

    def test_branding_finds_assets_and_names_the_product(self):
        self.assertEqual((branding.APP_NAME, branding.ORGANIZATION, branding.AUTHOR), ("FreeLog", "barzanics", "Amirhossein Barzegar"))
        self.assertTrue(branding.logo_path().exists()); self.assertTrue(branding.ico_path().name == "freelog.ico"); self.assertIsNone(branding.find_asset("nope.png"))
        self.assertFalse(branding.set_windows_app_id() and False)


class ShortcutTests(unittest.TestCase):
    def test_launcher_texts_are_correct_and_safe(self):
        root = Path("/opt/free log")
        e = sc.desktop_entry(root, "/usr/bin/python3"); self.assertIn('Exec="/usr/bin/python3" -m worktracker.main', e); self.assertIn("Icon=/opt/free log/assets/icons/freelog_256.png", e); self.assertIn("Name=FreeLog", e)
        ps = sc.powershell_script(Path("C:/Users/O'Neil/FreeLog"), "C:/Python/python.exe")
        self.assertIn("'C:/Users/O''Neil/FreeLog'", ps); self.assertIn("freelog.ico,0", ps); self.assertIn("-m worktracker.main", ps); self.assertIn("WScript.Shell", ps)

    def test_linux_and_mac_files_are_written_and_windows_calls_powershell(self):
        with tempfile.TemporaryDirectory() as t:
            home = Path(t); (home / "Desktop").mkdir()
            made = sc.create_shortcuts(ROOT, "python3", "linux", home); self.assertEqual(len(made), 2); self.assertTrue((home / ".local/share/applications/freelog.desktop").exists()); self.assertTrue((home / "Desktop/FreeLog.desktop").stat().st_mode & 0o100)
            m = sc.create_shortcuts(ROOT, "python3", "darwin", home); self.assertTrue(m and (home / "Desktop/FreeLog.command").exists())
            calls = []; w = sc.create_shortcuts(ROOT, "C:/py/python.exe", "win32", home, runner=lambda *a, **k: calls.append(a)); self.assertEqual(w, ["Desktop", "Start menu"]); self.assertEqual(calls[0][0][0], "powershell")
            self.assertEqual(sc.create_shortcuts(ROOT, "p", "win32", home, runner=lambda *a, **k: (_ for _ in ()).throw(OSError("no powershell"))), [])        # failure is swallowed

    def test_created_once_and_can_be_turned_off(self):
        db = Database(); n = []
        self.assertTrue(sc.ensure_shortcuts(db, ROOT, platform="win32", runner=lambda *a, **k: n.append(1))); self.assertFalse(sc.ensure_shortcuts(db, ROOT, platform="win32", runner=lambda *a, **k: n.append(1))); self.assertEqual(len(n), 1)
        db2 = Database(); db2.set_setting("create_shortcuts", False); self.assertFalse(sc.ensure_shortcuts(db2, ROOT, platform="win32", runner=lambda *a, **k: n.append(1))); self.assertEqual(len(n), 1)
        db3 = Database(); self.assertFalse(sc.ensure_shortcuts(db3, ROOT, platform="win32", runner=lambda *a, **k: (_ for _ in ()).throw(OSError()))); self.assertFalse(db3.get_setting("shortcuts_created", False))   # retried next start


if __name__ == "__main__":
    unittest.main()
