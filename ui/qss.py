"""One global stylesheet. Every input/list/scrollbar/menu/checkbox is glass, nothing falls back to the white system palette.

Key rules that fixed the "white box behind forms": QScrollArea hands its viewport *and* the hosted widget an auto-filled white palette background, so
those are forced transparent here; dialogs and stacked pages are transparent too. Arrow and check images are rendered once to PNG (see icons.export_pngs).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .glass import Theme

EMOJI_FONTS = "'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Twemoji Mozilla'"


def _u(asset_dir: Optional[Path], name: str) -> str:
    return f'url("{(asset_dir / name).as_posix()}")' if asset_dir else "none"


def build_qss(theme: Theme, font_stack: str = "'IRANSans', 'Vazirmatn', Tahoma, sans-serif", asset_dir: Optional[Path] = None) -> str:
    dark = theme.dark
    txt, mut = theme.text().name(), theme.text(True).name()
    a0, a1 = theme.accents[0], theme.accents[1]
    fill = "rgba(255,255,255,0.07)" if dark else "rgba(255,255,255,0.72)"
    fill_f = "rgba(255,255,255,0.12)" if dark else "rgba(255,255,255,0.95)"
    fill_l = "rgba(255,255,255,0.04)" if dark else "rgba(255,255,255,0.55)"
    line = "rgba(255,255,255,0.18)" if dark else "rgba(40,40,90,0.20)"
    pop = str(theme.t["bg"]) if dark else "#FFFFFF"
    hov = "rgba(255,255,255,0.08)" if dark else "rgba(60,60,140,0.08)"
    stack = f"{font_stack}, {EMOJI_FONTS}, sans-serif" if "sans-serif" not in font_stack else font_stack.replace("sans-serif", f"{EMOJI_FONTS}, sans-serif")
    down, up, check = _u(asset_dir, "chevron_down.png"), _u(asset_dir, "chevron_up.png"), _u(asset_dir, "check.png")
    return f"""
* {{ font-family: {stack}; outline: 0; }}
QWidget {{ color: {txt}; }}
QDialog, QStackedWidget, QStackedWidget > QWidget, QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget, QAbstractScrollArea {{ background: transparent; border: none; }}
QLabel {{ background: transparent; color: {txt}; }}
QLabel[muted="true"] {{ color: {mut}; }}
QLabel[accent="true"] {{ color: {a1}; font-weight: bold; }}
QLabel[danger="true"] {{ color: #FF6B81; font-weight: bold; }}
QToolTip {{ background: {pop}; color: {txt}; border: 1px solid {line}; border-radius: 10px; padding: 6px 10px; }}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTimeEdit, QDateEdit {{
    background: {fill}; color: {txt}; border: 1px solid {line}; border-radius: 12px; padding: 7px 12px; min-height: 22px; selection-background-color: {a0}; selection-color: #FFFFFF; }}
QTextEdit, QPlainTextEdit {{ padding: 8px 12px; }}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QTimeEdit:hover {{ border: 1px solid {mut}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTimeEdit:focus {{ background: {fill_f}; border: 1px solid {a1}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {mut}; background: {fill_l}; }}
QComboBox::drop-down {{ border: none; width: 30px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: {down}; width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{ background: {pop}; color: {txt}; border: 1px solid {line}; border-radius: 12px; padding: 6px; selection-background-color: {a0}; selection-color: #FFFFFF; outline: 0; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 22px; border: none; background: transparent; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; border: none; background: transparent; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: {up}; width: 10px; height: 10px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: {down}; width: 10px; height: 10px; }}
QTimeEdit::up-button, QTimeEdit::down-button {{ width: 0px; border: none; }}
QListWidget, QTreeWidget, QTableView, QListView {{ background: {fill_l}; border: 1px solid {line}; border-radius: 14px; color: {txt}; padding: 4px; }}
QListWidget::item, QTreeWidget::item, QListView::item {{ padding: 8px 10px; border-radius: 10px; margin: 2px 1px; }}
QListWidget::item:hover, QTreeWidget::item:hover, QListView::item:hover {{ background: {hov}; }}
QListWidget::item:selected, QTreeWidget::item:selected, QListView::item:selected {{ background: {a0}; color: #FFFFFF; }}
QListWidget::indicator, QTreeWidget::indicator, QListView::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {line}; background: {fill}; }}
QListWidget::indicator:checked, QTreeWidget::indicator:checked, QListView::indicator:checked {{ background: {a0}; border: 1px solid {a1}; image: {check}; }}
QHeaderView::section {{ background: transparent; color: {mut}; border: none; padding: 7px; }}
QTableView {{ gridline-color: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: {line}; border-radius: 4px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {a1}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 3px; }}
QScrollBar::handle:horizontal {{ background: {line}; border-radius: 4px; min-width: 36px; }}
QScrollBar::handle:horizontal:hover {{ background: {a1}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QProgressBar {{ background: {fill}; border: none; border-radius: 8px; text-align: center; min-height: 16px; max-height: 16px; color: {txt}; }}
QProgressBar::chunk {{ border-radius: 8px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {a0}, stop:1 {a1}); }}
QSlider::groove:horizontal {{ height: 6px; background: {fill_f}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {a0}, stop:1 {a1}); border-radius: 3px; }}
QSlider::handle:horizontal {{ background: #FFFFFF; width: 18px; height: 18px; margin: -7px 0; border-radius: 9px; border: 2px solid {a1}; }}
QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 7px; border: 1px solid {line}; background: {fill}; }}
QCheckBox::indicator:hover {{ border: 1px solid {a1}; }}
QCheckBox::indicator:checked {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {a0}, stop:1 {a1}); border: 1px solid {a1}; image: {check}; }}
QMenu {{ background: {pop}; color: {txt}; border: 1px solid {line}; border-radius: 14px; padding: 6px; }}
QMenu::item {{ padding: 8px 22px; border-radius: 9px; }}
QMenu::item:selected {{ background: {a0}; color: #FFFFFF; }}
QMenu::separator {{ height: 1px; background: {line}; margin: 5px 10px; }}
QPushButton[chip="true"] {{ background: {fill}; border: 1px solid {line}; border-radius: 15px; padding: 6px 14px; min-height: 18px; color: {txt}; }}
QPushButton[chip="true"]:hover {{ background: {hov}; border: 1px solid {a1}; }}
QPushButton[chip="true"]:checked {{ background: {a0}; border: 1px solid {a1}; color: #FFFFFF; }}
QPushButton[ghost="true"] {{ background: transparent; border: none; color: {mut}; padding: 5px 9px; border-radius: 10px; }}
QPushButton[ghost="true"]:hover {{ background: {hov}; color: {txt}; }}
QFrame[card="true"] {{ background: {fill_l}; border: 1px solid {line}; border-radius: 16px; }}
QTextBrowser {{ background: transparent; border: none; color: {txt}; }}
"""
