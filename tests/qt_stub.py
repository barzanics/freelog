"""Minimal permissive PyQt5 stand-in so UI *code paths* execute without Qt (catches NameError/AttributeError/typos in our code).
It does NOT validate real Qt API usage; real-Qt smoke tests (test_ui_smoke.py) do that when PyQt5 is installed."""
import sys
import types


class _Meta(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return 1                    # enum-like constants (Qt.AlignCenter, ...)

    def __or__(cls, other):
        return 1


class Dummy(metaclass=_Meta):
    def __init__(self, *a, **k):
        self._v = {}

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Method(self, name)

    def __bool__(self):
        return True

    def __or__(self, o):
        return 1

    def __ror__(self, o):
        return 1

    # arithmetic on geometry values is irrelevant here; behave like numbers
    def __sub__(self, o): return 0
    def __rsub__(self, o): return 0
    def __add__(self, o): return 0
    def __radd__(self, o): return 0
    def __mul__(self, o): return 0
    def __floordiv__(self, o): return 0
    def __truediv__(self, o): return 0
    def __int__(self): return 0
    def __float__(self): return 0.0


class _Method:
    def __init__(self, owner, name):
        self.owner, self.name = owner, name

    def __call__(self, *a, **k):
        if self.name in ("text", "currentText", "toPlainText"):
            return self.owner._v.get("text", "")
        if self.name in ("setText", "setPlainText", "setEditText") and a:
            self.owner._v["text"] = a[0]
            return None
        if self.name == "setValue" and a:
            self.owner._v["value"] = a[0]
            return None
        if self.name == "value":
            return self.owner._v.get("value", 0)
        if self.name.endswith("Count"):
            return 0
        if self.name in ("findChildren", "children"):
            return []
        if self.name in ("currentData", "currentItem", "currentIndex", "findData", "count"):
            return None if self.name in ("currentData", "currentItem") else 0
        if self.name in ("connect", "emit", "setStyleSheet"):
            return None
        if self.name in ("width", "height"):
            return 800
        if self.name in ("isVisible", "isActiveWindow", "isMinimized", "isActive"):
            return False
        if self.name == "rect" or self.name == "size":
            return Dummy()
        return Dummy()

    def __getattr__(self, n):
        return Dummy()

    def connect(self, *a, **k):
        return None


class QTimeStub:
    def __init__(self, h=0, m=0, *a): self.h, self.m = h, m
    def hour(self): return self.h
    def minute(self): return self.m


class TimeEditStub(Dummy):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self._t = QTimeStub(0, 0)
    def time(self): return self._t
    def setTime(self, t): self._t = t


class ClipStub:
    def __init__(self): self.t = ""
    def setText(self, t): self.t = t
    def text(self): return self.t


_CLIP = ClipStub()


class DialogStub(Dummy):
    """QDialog: exec_ returns Accepted immediately (nothing is shown in tests)."""
    def exec_(self): return 1
    def done(self, r): self._result = r
    def accept(self): self.done(1)
    def reject(self): self.done(0)
    def showEvent(self, e): return None
    def keyPressEvent(self, e): return None
    def mousePressEvent(self, e): return None
    def closeEvent(self, e): return None


class StackedStub(Dummy):
    """QStackedWidget that really tracks its pages (the app asserts page order)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages, self._cur = [], 0

    def addWidget(self, w):
        self._pages.append(w); return len(self._pages) - 1

    def insertWidget(self, i, w):
        self._pages.insert(i, w); return i

    def removeWidget(self, w):
        if w in self._pages:
            self._pages.remove(w)

    def count(self): return len(self._pages)
    def widget(self, i): return self._pages[i] if 0 <= i < len(self._pages) else None
    def currentIndex(self): return self._cur
    def setCurrentIndex(self, i): self._cur = i


class Signal:
    def __init__(self, *a): pass
    def __get__(self, obj, typ=None): return Dummy()


def install():
    names = {"QtMultimedia": [], "QtCore": ["QAbstractTableModel", "QModelIndex", "Qt", "QTimer", "QVariant", "QEasingCurve", "QPointF", "QPropertyAnimation", "QRectF", "QUrl"],
             "QtGui": ["QBrush", "QColor", "QFont", "QLinearGradient", "QPainter", "QPainterPath", "QPen", "QRadialGradient", "QKeySequence", "QPixmap", "QIcon"],
             "QtWidgets": ["QAbstractItemView", "QCheckBox", "QComboBox", "QDialog", "QDoubleSpinBox", "QFileDialog", "QGridLayout", "QHBoxLayout",
                           "QHeaderView", "QLabel", "QLineEdit", "QListWidget", "QMainWindow", "QMessageBox", "QShortcut", "QSpinBox", "QStackedWidget",
                           "QSystemTrayIcon", "QTableView", "QVBoxLayout", "QWidget", "QFrame", "QPushButton", "QInputDialog", "QColorDialog",
                           "QScrollArea", "QApplication", "QListWidgetItem", "QPlainTextEdit"]}
    pkg = types.ModuleType("PyQt5"); pkg.__path__ = []
    sys.modules["PyQt5"] = pkg
    for mod, cls in names.items():
        m = types.ModuleType("PyQt5." + mod)
        for c in cls:
            setattr(m, c, type(c, (Dummy,), {}))
        if mod == "QtCore":
            m.pyqtSignal = Signal
            m.pyqtProperty = lambda t, g=None, s=None: property(g, s)
            m.Qt = type("Qt", (Dummy,), {})
        def _lazy(name, _m=m):
            if name.startswith("__"):
                raise AttributeError(name)
            cls_ = type(name, (Dummy,), {})
            setattr(_m, name, cls_)
            return cls_
        m.__dict__["__getattr__"] = _lazy                   # any Qt class a module imports is fabricated on demand
        setattr(pkg, mod, m)
        sys.modules["PyQt5." + mod] = m
    sys.modules["PyQt5.QtWidgets"].QStackedWidget = StackedStub
    sys.modules["PyQt5.QtWidgets"].QDialog = DialogStub
    sys.modules["PyQt5.QtWidgets"].QTimeEdit = TimeEditStub
    sys.modules["PyQt5.QtCore"].QTime = QTimeStub
    _qa = sys.modules["PyQt5.QtWidgets"].QApplication
    _qa.instance = staticmethod(lambda: None)
    _qa.alert = staticmethod(lambda *a, **k: None)
    _qa.clipboard = staticmethod(lambda: _CLIP)
    _qa.quit = staticmethod(lambda: None)
    sys.modules["PyQt5.QtCore"].QTimer.singleShot = staticmethod(lambda *a, **k: None)
    sys.modules["PyQt5.QtWidgets"].QSystemTrayIcon.isSystemTrayAvailable = staticmethod(lambda: False)
    sys.modules["PyQt5.QtWidgets"].QMessageBox = type("QMessageBox", (Dummy,), {"warning": staticmethod(lambda *a, **k: None), "information": staticmethod(lambda *a, **k: None)})
