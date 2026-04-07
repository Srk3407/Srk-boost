"""
SRK Boost - Settings Page
Language switcher, restore points, startup, notifications, auto-clean, about.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import os
import sys
import json
import logging
from core.i18n import tr, set_language, get_language

logger = logging.getLogger(__name__)

RESTORE_DIR = os.path.join(os.path.expanduser("~"), ".srk_boost", "restore_points")
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".srk_boost", "settings.json")
SRK_BOOST_DIR = os.path.join(os.path.expanduser("~"), ".srk_boost")

_DEFAULT_SETTINGS = {
    "start_with_windows": False,
    "notify_on_scan_complete": True,
    "auto_clean_on_startup": False,
    "language": "en",
}


def _load_settings() -> dict:
    """Load settings from file, filling missing keys with defaults."""
    settings = dict(_DEFAULT_SETTINGS)
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            settings.update(saved)
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
    return settings


def _save_settings(settings: dict):
    """Save settings to JSON file."""
    try:
        os.makedirs(SRK_BOOST_DIR, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save settings: {e}")


def _set_startup_registry(enable: bool):
    """Add or remove SRK Boost from Windows startup registry."""
    try:
        import subprocess
        key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SRKBoost"
        if enable:
            # Use the current executable path
            exe_path = sys.executable
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                exe_path = f'"{sys.executable}" "{main_py}"'
            subprocess.run(
                ["reg", "add", key, "/v", app_name, "/t", "REG_SZ", "/d", exe_path, "/f"],
                capture_output=True, timeout=5
            )
        else:
            subprocess.run(
                ["reg", "delete", key, "/v", app_name, "/f"],
                capture_output=True, timeout=5
            )
    except Exception as e:
        logger.warning(f"Startup registry change failed: {e}")


class SettingsPage(QWidget):
    language_changed = pyqtSignal()
    restore_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = _load_settings()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        title = QLabel(tr("settings_title"))
        title.setStyleSheet("color: #e0e0ff; font-size: 22px; font-weight: 900;")
        main_layout.addWidget(title)

        # ── Language section ──────────────────────────────────────────────────
        lang_card = self._make_card()
        lang_layout = QVBoxLayout(lang_card)
        lang_layout.setSpacing(12)

        lang_title = QLabel(tr("language"))
        lang_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        lang_layout.addWidget(lang_title)

        lang_desc = QLabel("Select the application language / Uygulama dilini seçin")
        lang_desc.setStyleSheet("color: #6060a0; font-size: 12px;")
        lang_layout.addWidget(lang_desc)

        btn_row = QHBoxLayout()
        self.btn_en = QPushButton("English")
        self.btn_tr = QPushButton("Türkçe")

        for btn, lang in [(self.btn_en, "en"), (self.btn_tr, "tr")]:
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda checked, l=lang: self._set_lang(l))
            btn_row.addWidget(btn)

        btn_row.addStretch()
        lang_layout.addLayout(btn_row)
        self._update_lang_buttons()
        main_layout.addWidget(lang_card)

        # ── Startup section ───────────────────────────────────────────────────
        startup_card = self._make_card()
        startup_layout = QVBoxLayout(startup_card)
        startup_layout.setSpacing(12)

        startup_title = QLabel("⚡ Startup")
        startup_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        startup_layout.addWidget(startup_title)

        self.startup_toggle = self._make_toggle(
            "Start with Windows",
            "Automatically launch SRK Boost when Windows starts",
            self._settings.get("start_with_windows", False),
            self._on_startup_toggled
        )
        startup_layout.addWidget(self.startup_toggle)
        main_layout.addWidget(startup_card)

        # ── Notifications section ─────────────────────────────────────────────
        notif_card = self._make_card()
        notif_layout = QVBoxLayout(notif_card)
        notif_layout.setSpacing(12)

        notif_title = QLabel("🔔 Notifications")
        notif_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        notif_layout.addWidget(notif_title)

        self.notif_toggle = self._make_toggle(
            "Show notifications when scan completes",
            "Display a notification popup after cleaner scan finishes",
            self._settings.get("notify_on_scan_complete", True),
            lambda state: self._save_setting("notify_on_scan_complete", state)
        )
        notif_layout.addWidget(self.notif_toggle)
        main_layout.addWidget(notif_card)

        # ── Auto Clean section ────────────────────────────────────────────────
        autoclean_card = self._make_card()
        autoclean_layout = QVBoxLayout(autoclean_card)
        autoclean_layout.setSpacing(12)

        autoclean_title = QLabel("🧹 Auto Clean")
        autoclean_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        autoclean_layout.addWidget(autoclean_title)

        self.autoclean_toggle = self._make_toggle(
            "Auto-clean temp files on startup",
            "Automatically remove temp files when SRK Boost launches",
            self._settings.get("auto_clean_on_startup", False),
            lambda state: self._save_setting("auto_clean_on_startup", state)
        )
        autoclean_layout.addWidget(self.autoclean_toggle)
        main_layout.addWidget(autoclean_card)

        # ── Restore Points section ────────────────────────────────────────────
        restore_card = self._make_card()
        restore_layout = QVBoxLayout(restore_card)
        restore_layout.setSpacing(12)

        r_header = QHBoxLayout()
        r_title = QLabel(tr("restore_points"))
        r_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        r_header.addWidget(r_title)
        r_header.addStretch()
        self.restore_count_lbl = QLabel("")
        self.restore_count_lbl.setStyleSheet("color: #6c63ff; font-size: 12px; padding: 2px 10px; border: 1px solid #6c63ff; border-radius: 10px;")
        r_header.addWidget(self.restore_count_lbl)
        restore_layout.addLayout(r_header)

        self.restore_list = QListWidget()
        self.restore_list.setStyleSheet("""
            QListWidget { background: #0a0a0f; border: 1px solid #2a1a4a; border-radius: 8px; color: #e0e0ff; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #1e1e2e; }
            QListWidget::item:selected { background: #2a1a4a; }
        """)
        self.restore_list.setMaximumHeight(180)
        restore_layout.addWidget(self.restore_list)

        r_btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setStyleSheet("background: #1e1e2e; color: #6060a0; border: 1px solid #2a2a3e; border-radius: 6px; padding: 8px 16px;")
        refresh_btn.clicked.connect(self._load_restore_points)
        r_btn_row.addWidget(refresh_btn)

        restore_btn = QPushButton("Restore Selected")
        restore_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #8b5cf6); color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c73ff,stop:1 #9b6cf6); }
        """)
        restore_btn.clicked.connect(self._restore_selected)
        r_btn_row.addWidget(restore_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("background: #2a0a0a; color: #ff4444; border: 1px solid #ff4444; border-radius: 6px; padding: 8px 16px;")
        delete_btn.clicked.connect(self._delete_selected)
        r_btn_row.addWidget(delete_btn)
        r_btn_row.addStretch()

        restore_layout.addLayout(r_btn_row)
        main_layout.addWidget(restore_card)

        # ── About section ─────────────────────────────────────────────────────
        about_card = self._make_card()
        about_layout = QVBoxLayout(about_card)

        about_title = QLabel(tr("about"))
        about_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        about_layout.addWidget(about_title)

        about_text = QLabel(
            "<b style='color:#6c63ff; font-size:20px;'>SRK Boost</b> <span style='color:#6060a0'>v1.0</span><br>"
            "<span style='color:#6060a0'>Professional PC Optimization Suite</span><br><br>"
            "<span style='color:#e0e0ff'>System Requirements:</span><br>"
            "<span style='color:#6060a0'>Windows 10/11 · Python 3.10+ · Admin privileges recommended</span>"
        )
        about_text.setTextFormat(Qt.TextFormat.RichText)
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        main_layout.addWidget(about_card)

        main_layout.addStretch()
        self._load_restore_points()

    def _make_toggle(self, label: str, desc: str, checked: bool, callback) -> QWidget:
        """Create a toggle row with label and description."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        text_col = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #e0e0ff; font-size: 13px;")
        d = QLabel(desc)
        d.setStyleSheet("color: #6060a0; font-size: 11px;")
        text_col.addWidget(lbl)
        text_col.addWidget(d)
        layout.addLayout(text_col)
        layout.addStretch()

        toggle = QCheckBox()
        toggle.setChecked(checked)
        toggle.setStyleSheet("""
            QCheckBox::indicator {
                width: 40px; height: 20px;
                border-radius: 10px;
                border: 2px solid #3a3a5a;
                background: #1e1e2e;
            }
            QCheckBox::indicator:checked {
                background: #6c63ff;
                border: 2px solid #6c63ff;
            }
        """)
        toggle.stateChanged.connect(lambda state: callback(bool(state)))
        layout.addWidget(toggle)
        return widget

    def _save_setting(self, key: str, value):
        """Save a single setting value and persist to disk."""
        self._settings[key] = value
        _save_settings(self._settings)

    def _on_startup_toggled(self, enabled: bool):
        self._save_setting("start_with_windows", enabled)
        _set_startup_registry(enabled)

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #12121a;
                border: 1px solid #2a1a4a;
                border-radius: 12px;
                padding: 6px;
            }
        """)
        return card

    def _set_lang(self, lang: str):
        set_language(lang)
        self._update_lang_buttons()
        self.language_changed.emit()

    def _update_lang_buttons(self):
        current = get_language()
        active_style = """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #8b5cf6);
                color: white; border: none; border-radius: 8px; padding: 8px 24px; font-weight: bold;
            }
        """
        inactive_style = "background: #1e1e2e; color: #6060a0; border: 1px solid #2a2a3e; border-radius: 8px; padding: 8px 24px;"
        self.btn_en.setStyleSheet(active_style if current == "en" else inactive_style)
        self.btn_tr.setStyleSheet(active_style if current == "tr" else inactive_style)

    def _load_restore_points(self):
        self.restore_list.clear()
        if not os.path.exists(RESTORE_DIR):
            self.restore_count_lbl.setText("0 saved")
            return
        files = sorted(
            [f for f in os.listdir(RESTORE_DIR) if f.endswith(".json")],
            reverse=True
        )
        self.restore_count_lbl.setText(f"{len(files)} saved")
        for f in files:
            path = os.path.join(RESTORE_DIR, f)
            try:
                with open(path) as fp:
                    data = json.load(fp)
                label = data.get("label", f)
                ts = data.get("timestamp", "")
                item = QListWidgetItem(f"{ts[:19].replace('T',' ')}  —  {label}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.restore_list.addItem(item)
            except Exception:
                item = QListWidgetItem(f)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.restore_list.addItem(item)

    def _restore_selected(self):
        item = self.restore_list.currentItem()
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.restore_from_file(path)
            QMessageBox.information(self, tr("success"), "Restore point applied successfully!")
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def _delete_selected(self):
        item = self.restore_list.currentItem()
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        try:
            os.remove(path)
            self._load_restore_points()
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))
