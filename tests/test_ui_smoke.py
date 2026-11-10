"""UI smoke tests. Skipped automatically when PyQt5 is not installed (headless CI uses QT_QPA_PLATFORM=offscreen)."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QPushButton
    HAVE_QT = True
except ImportError:  # pragma: no cover
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PyQt5 not installed")
class UiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from worktracker.core.database import Database
        from worktracker.ui.main_window import MainWindow
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")
        self.win = MainWindow(self.db, Path(self.tmp.name))

    def tearDown(self):
        self.win.close(); self.db.close(); self.tmp.cleanup()

    def test_pages_and_pointer_cursors(self):
        for i in range(6):
            self.win.goto(i)
        for b in self.win.findChildren(QPushButton):
            self.assertEqual(b.cursor().shape(), Qt.PointingHandCursor)

    def test_timer_flow(self):
        self.win.t_title.setText("test")
        self.win.toggle_timer()
        self.assertIsNotNone(self.win.tracker.current)
        self.win.toggle_timer()
        self.assertIsNone(self.win.tracker.current)

    def test_empty_title_does_not_start(self):
        from unittest import mock
        with mock.patch("worktracker.ui.main_window.QMessageBox.warning"):
            self.win.toggle_timer()
        self.assertIsNone(self.win.tracker.current)


if __name__ == "__main__":
    unittest.main()
