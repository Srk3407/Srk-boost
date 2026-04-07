"""
SRK Boost - Main Window
Handles the overall application layout: sidebar navigation + content stack.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget,
    QStatusBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QIcon

from core.monitor import SystemMonitor
from core.i18n import tr
from ui.dashboard import DashboardPage
from ui.fps_boost import FpsBoostPage
from ui.scanner import ScannerPage
from ui.cleaner import CleanerPage
from ui.game_mode import GameModePage
from ui.startup_manager import StartupManagerPage
from ui.driver_manager import DriverManagerPage
from ui.settings import SettingsPage
from ui.speedtest_page import SpeedTestPage
from ui.backup_page import BackupPage
from ui.game_profiles import GameProfilesPage
from ui.benchmark import BenchmarkPage as BenchmarkPageUI
from ui.network_optimizer import NetworkOptimizerPage
from core.tray import TrayManager
from core.auto_game_mode import AutoGameModeWatcher

logger = logging.getLogger(__name__)

# page_id, icon, tr_key, subtitle
NAV_ITEMS = [
    ("dashboard",      "⚡",  "dashboard",      "System overview and live stats"),
    ("fps_boost",      "🚀",  "fps_boost",      "One-click performance optimization"),
    ("game_profiles",  "🎮",  "game_profiles",  "Per-game tweak presets"),
    ("benchmark",      "📊",  "benchmark",      "Before/after performance comparison"),
    ("scanner",        "🔍",  "scanner",        "Detailed hardware information"),
    ("driver_manager", "🔧",  "drivers",        "Check and update device drivers"),
    ("cleaner",        "🧹",  "cleaner",        "Remove junk files and caches"),
    ("game_mode",      "🕹",  "game_mode",      "Kill background processes"),
    ("startup",        "🚦",  "startup",        "Control boot-time programs"),
    ("network",        "📡",  "network",        "Ping reducer & live monitor"),
    ("speedtest",      "🌐",  "speedtest",      "Internet speed test"),
    ("backup",         "💾",  "backup",         "Create and manage restore points"),
    ("settings",       "⚙",   "settings",      "Preferences and restore points"),
]


class SidebarNavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_btn")
        self._icon = icon
        self._label = label
        self._active = False
        self.setText(f"  {icon}  {label}")
        self.setCheckable(False)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        # Bold when active
        font = self.font()
        font.setBold(active)
        font.setWeight(QFont.Weight.Bold if active else QFont.Weight.Medium)
        self.setFont(font)
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_name") + " — PC Performance Optimizer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)

        self._current_page = "dashboard"
        self._nav_buttons: dict[str, SidebarNavButton] = {}
        self._monitor = SystemMonitor(interval_ms=1000)

        self._setup_ui()
        self._connect_monitor()
        self._navigate_to("dashboard")

        # Tray
        self._tray = TrayManager(self)
        self._tray.show_window_requested.connect(self._show_from_tray)
        self._tray.quit_requested.connect(self.close)
        self._tray.show()

        # Auto Game Mode watcher
        self._agm_watcher = AutoGameModeWatcher()
        self._agm_watcher.game_started.connect(self._on_game_started)
        self._agm_watcher.game_stopped.connect(self._on_game_stopped)
        self._agm_watcher.start()

        # RAM auto-clean timer (off by default; settings can enable)
        self._ram_clean_timer = QTimer(self)
        self._ram_clean_timer.setInterval(30 * 60 * 1000)  # 30 min default
        self._ram_clean_timer.timeout.connect(self._auto_clean_ram)

        # Start monitor after a short delay
        QTimer.singleShot(500, self._monitor.start)

    # ── UI Setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("content_area")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # Content
        self._content_stack = QStackedWidget()
        self._content_stack.setObjectName("content_area")
        root_layout.addWidget(self._content_stack)

        # Pages
        self._pages: dict[str, QWidget] = {}
        self._build_pages()

        # Status bar with colored stat labels
        self._status_bar = QStatusBar()
        self._status_bar.setObjectName("status_bar")
        self.setStatusBar(self._status_bar)

        self._sb_cpu_lbl = QLabel("CPU: —%")
        self._sb_cpu_lbl.setStyleSheet("color: #6c63ff; font-size: 11px; padding: 0 6px;")
        self._sb_ram_lbl = QLabel("RAM: —%")
        self._sb_ram_lbl.setStyleSheet("color: #00d4ff; font-size: 11px; padding: 0 6px;")
        self._sb_disk_lbl = QLabel("Disk: —")
        self._sb_disk_lbl.setStyleSheet("color: #00ff88; font-size: 11px; padding: 0 6px;")
        self._sb_net_lbl = QLabel("Net: ↓— ↑—")
        self._sb_net_lbl.setStyleSheet("color: #ffaa00; font-size: 11px; padding: 0 6px;")

        self._status_bar.addWidget(self._sb_cpu_lbl)
        self._status_bar.addWidget(self._make_sb_sep())
        self._status_bar.addWidget(self._sb_ram_lbl)
        self._status_bar.addWidget(self._make_sb_sep())
        self._status_bar.addWidget(self._sb_disk_lbl)
        self._status_bar.addWidget(self._make_sb_sep())
        self._status_bar.addWidget(self._sb_net_lbl)
        self._status_bar.showMessage("")

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(2)

        # ── Logo block ────────────────────────────────────────────────────────
        logo_frame = QFrame()
        logo_frame.setObjectName("sidebar_logo")
        logo_frame.setFixedHeight(100)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(18, 16, 18, 16)
        logo_layout.setSpacing(14)

        # Logo image
        import os, sys
        from PyQt6.QtGui import QPixmap
        # PyInstaller-safe path
        if hasattr(sys, '_MEIPASS'):
            _base = sys._MEIPASS
        else:
            _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(_base, "assets", "logo.png")
        icon_box = QLabel()
        icon_box.setFixedSize(52, 52)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                52, 52,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            icon_box.setPixmap(pix)
            icon_box.setStyleSheet(
                "border-radius: 14px; border: 2px solid rgba(108,99,255,0.4);"
                "background: #0a0914;"
            )
        else:
            icon_box.setText("⚡")
            icon_box.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6c63ff,stop:1 #00d4ff);"
                "border-radius: 14px; font-size: 24px;"
            )
        logo_layout.addWidget(icon_box)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        logo = QLabel("SRK Boost")
        logo.setObjectName("logo_label")
        logo.setStyleSheet(
            "font-size: 19px; font-weight: 900; letter-spacing: 1px;"
            "color: #c0b8ff;"
            "background: transparent; border: none;"
        )

        sub = QLabel("Performance Suite  v1.0")
        sub.setObjectName("logo_subtitle")
        sub.setStyleSheet(
            "font-size: 10px; color: #4a4a7a; background: transparent; "
            "border: none; letter-spacing: 0.5px;"
        )

        text_col.addWidget(logo)
        text_col.addWidget(sub)
        logo_layout.addLayout(text_col)
        logo_layout.addStretch()
        layout.addWidget(logo_frame)

        # ── Nav section label ─────────────────────────────────────────────────
        layout.addSpacing(6)
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            "color: #2e2e50; font-size: 9px; font-weight: 800; "
            "letter-spacing: 2.5px; padding: 0 20px;"
        )
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        # ── Nav buttons ────────────────────────────────────────────────────────
        main_pages = ["dashboard", "fps_boost", "scanner", "driver_manager", "cleaner"]
        tool_pages = ["game_mode", "startup", "speedtest", "backup", "settings"]

        for page_id, icon, tr_key, _ in NAV_ITEMS:
            if page_id == "game_mode":
                # Section separator + label before tools group
                sep_line = QFrame()
                sep_line.setFrameShape(QFrame.Shape.HLine)
                sep_line.setStyleSheet("background: #1a1a2a; max-height: 1px; margin: 4px 16px;")
                layout.addWidget(sep_line)
                tools_label = QLabel("TOOLS")
                tools_label.setStyleSheet(
                    "color: #2e2e50; font-size: 9px; font-weight: 800; "
                    "letter-spacing: 2.5px; padding: 4px 20px 0;"
                )
                layout.addWidget(tools_label)
                layout.addSpacing(2)

            btn = SidebarNavButton(icon, tr(tr_key))
            btn.clicked.connect(lambda checked, pid=page_id: self._navigate_to(pid))
            layout.addWidget(btn)
            self._nav_buttons[page_id] = btn
            btn._tr_key = tr_key

        layout.addStretch()

        # ── Bottom section ────────────────────────────────────────────────────
        sep_bottom = QFrame()
        sep_bottom.setFrameShape(QFrame.Shape.HLine)
        sep_bottom.setStyleSheet("background: #1a1a2a; max-height: 1px; margin: 4px 12px;")
        layout.addWidget(sep_bottom)

        # Live stats mini bar
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: transparent;")
        stats_vlayout = QVBoxLayout(stats_widget)
        stats_vlayout.setContentsMargins(16, 6, 16, 4)
        stats_vlayout.setSpacing(3)

        self._sidebar_cpu = QLabel("CPU  —%")
        self._sidebar_cpu.setStyleSheet(
            "color: #6c63ff; font-size: 11px; font-weight: 600; background: transparent;"
        )
        self._sidebar_ram = QLabel("RAM  —%")
        self._sidebar_ram.setStyleSheet(
            "color: #00d4ff; font-size: 11px; font-weight: 600; background: transparent;"
        )

        ver_lbl = QLabel("v1.0.0 — SRK Boost")
        ver_lbl.setStyleSheet(
            "color: #2a2a4a; font-size: 9px; background: transparent; "
            "letter-spacing: 0.5px; padding-top: 4px;"
        )

        stats_vlayout.addWidget(self._sidebar_cpu)
        stats_vlayout.addWidget(self._sidebar_ram)
        stats_vlayout.addWidget(ver_lbl)
        layout.addWidget(stats_widget)

        # Dil geçiş butonu
        from core.i18n import get_language
        self._lang_btn = QPushButton()
        self._lang_btn.setFixedHeight(34)
        self._lang_btn.setStyleSheet(
            "background: rgba(108,99,255,0.08); color: #6c63ff;"
            "border: 1px solid rgba(108,99,255,0.2); border-radius: 10px;"
            "font-size: 12px; font-weight: 700; margin: 0 14px 2px;"
        )
        self._lang_btn.setText("🇹🇷  Türkçe" if get_language() == "en" else "🇬🇧  English")
        self._lang_btn.clicked.connect(self._toggle_language)
        layout.addWidget(self._lang_btn)

        return sidebar

    def _build_pages(self):
        for page_id, _, tr_key, subtitle in NAV_ITEMS:
            wrapper = QWidget()
            wrapper.setObjectName("content_area")
            v = QVBoxLayout(wrapper)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(0)

            # Page header
            header = self._build_page_header(tr(tr_key), subtitle)
            v.addWidget(header)

            # Page content
            page_widget = self._create_page(page_id)
            v.addWidget(page_widget, 1)

            self._pages[page_id] = page_widget
            self._content_stack.addWidget(wrapper)

    def _build_page_header(self, title: str, subtitle: str) -> QFrame:
        header = QFrame()
        header.setStyleSheet("background: #0d0d15; border-bottom: 1px solid #1e1e2e;")
        header.setFixedHeight(72)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("page_title")
        s = QLabel(subtitle)
        s.setObjectName("page_subtitle")
        col.addWidget(t)
        col.addWidget(s)
        layout.addLayout(col)
        layout.addStretch()

        # Live CPU/RAM badges — store ALL headers to update them all
        cpu_lbl = QLabel("CPU: —%")
        cpu_lbl.setObjectName("badge_info")
        ram_lbl = QLabel("RAM: —%")
        ram_lbl.setObjectName("badge_info")
        layout.addWidget(cpu_lbl)
        layout.addWidget(ram_lbl)

        if not hasattr(self, '_header_cpu_labels'):
            self._header_cpu_labels = []
            self._header_ram_labels = []
        self._header_cpu_labels.append(cpu_lbl)
        self._header_ram_labels.append(ram_lbl)

        # Keep legacy refs pointing to latest (for backward compat)
        self._header_cpu = cpu_lbl
        self._header_ram = ram_lbl

        return header

    def _create_page(self, page_id: str) -> QWidget:
        if page_id == "dashboard":
            return DashboardPage()
        elif page_id == "fps_boost":
            return FpsBoostPage()
        elif page_id == "scanner":
            return ScannerPage()
        elif page_id == "driver_manager":
            return DriverManagerPage()
        elif page_id == "cleaner":
            return CleanerPage()
        elif page_id == "game_mode":
            return GameModePage()
        elif page_id == "startup":
            return StartupManagerPage()
        elif page_id == "network":
            return NetworkOptimizerPage()
        elif page_id == "speedtest":
            return SpeedTestPage()
        elif page_id == "game_profiles":
            return GameProfilesPage()
        elif page_id == "benchmark":
            return BenchmarkPageUI()
        elif page_id == "backup":
            return BackupPage()
        elif page_id == "settings":
            page = SettingsPage()
            page.restore_requested.connect(self._on_restore_requested)
            page.language_changed.connect(self._on_language_changed)
            return page
        return QWidget()



    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate_to(self, page_id: str):
        # Deactivate current
        if self._current_page in self._nav_buttons:
            self._nav_buttons[self._current_page].set_active(False)

        # Activate new
        self._current_page = page_id
        if page_id in self._nav_buttons:
            self._nav_buttons[page_id].set_active(True)

        # Find and show the wrapper in the stack
        for i in range(self._content_stack.count()):
            widget = self._content_stack.widget(i)
            if widget.property("page_id") == page_id:
                self._content_stack.setCurrentIndex(i)
                return

        # Match by order
        page_ids = [x[0] for x in NAV_ITEMS]
        if page_id in page_ids:
            idx = page_ids.index(page_id)
            self._content_stack.setCurrentIndex(idx)

    def _make_sb_sep(self) -> QLabel:
        sep = QLabel("•")
        sep.setStyleSheet("color: #3a2a5a; font-size: 11px;")
        return sep

    # ── Language ─────────────────────────────────────────────────────────────

    @pyqtSlot()
    def _toggle_language(self):
        from core.i18n import get_language, set_language
        new_lang = "tr" if get_language() == "en" else "en"
        set_language(new_lang)
        self._retranslate_ui()

    def _on_language_changed(self):
        self._retranslate_ui()

    def _retranslate_ui(self):
        """Update all translatable labels in the main window."""
        from core.i18n import get_language
        self.setWindowTitle(tr("app_name") + " — PC Performance Optimizer")
        # Lang button label
        if hasattr(self, '_lang_btn'):
            self._lang_btn.setText("🇹🇷  Türkçe" if get_language() == "en" else "🇬🇧  English")
        # Nav button labels
        for page_id, icon, tr_key, subtitle in NAV_ITEMS:
            btn = self._nav_buttons.get(page_id)
            if btn:
                btn.setText(f"  {icon}  {tr(tr_key)}")
        # Page header labels
        for i in range(self._content_stack.count()):
            wrapper = self._content_stack.widget(i)
            pid = wrapper.property("page_id")
            if not pid:
                continue
            item = next((x for x in NAV_ITEMS if x[0] == pid), None)
            if not item:
                continue
            _, icon, tr_key, subtitle = item
            sub_key = f"nav_sub_{pid}"
            localized_sub = tr(sub_key) if tr(sub_key) != sub_key else subtitle
            layout_w = wrapper.layout()
            if layout_w and layout_w.count() > 0:
                header = layout_w.itemAt(0).widget()
                if header:
                    for child in header.findChildren(QLabel):
                        obj = child.objectName()
                        if obj == "page_title":
                            child.setText(tr(tr_key))
                        elif obj == "page_subtitle":
                            child.setText(localized_sub)

    # ── Monitor Integration ───────────────────────────────────────────────────

    def _connect_monitor(self):
        self._monitor.stats_updated.connect(self._on_stats)

    @pyqtSlot(dict)
    def _on_stats(self, stats: dict):
        cpu = stats.get("cpu_percent", 0)
        ram = stats.get("ram_percent", 0)

        # Sidebar labels
        self._sidebar_cpu.setText(f"CPU  {cpu:.0f}%")
        self._sidebar_ram.setText(f"RAM  {ram:.0f}%")

        # Update ALL page header badges
        try:
            for lbl in getattr(self, '_header_cpu_labels', []):
                lbl.setText(f"CPU: {cpu:.0f}%")
            for lbl in getattr(self, '_header_ram_labels', []):
                lbl.setText(f"RAM: {ram:.0f}%")
        except RuntimeError:
            pass

        # Forward to dashboard
        try:
            dash = self._pages.get("dashboard")
            if dash:
                dash.update_stats(stats)
        except Exception:
            pass

        # Status bar
        try:
            disk_r = stats.get("disk_read_mbps", 0)
            disk_w = stats.get("disk_write_mbps", 0)
            net_d = stats.get("net_recv_mbps", 0)
            net_u = stats.get("net_sent_mbps", 0)
            self._sb_cpu_lbl.setText(f"CPU: {cpu:.1f}%")
            self._sb_ram_lbl.setText(f"RAM: {ram:.1f}%")
            self._sb_disk_lbl.setText(f"Disk R:{disk_r:.1f} W:{disk_w:.1f} MB/s")
            self._sb_net_lbl.setText(f"Net ↓{net_d:.2f} ↑{net_u:.2f} Mbps")
        except RuntimeError:
            pass

    @pyqtSlot(str)
    def _on_restore_requested(self, name: str):
        self._status_bar.showMessage(f"  ✅ Restored from '{name}'")

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_game_started(self, game_name: str):
        self._tray.notify("🎮 Game Detected", f"{game_name} started — boosting performance!")
        self._status_bar.showMessage(f"  🎮 Auto Game Mode: {game_name} detected")

    def _on_game_stopped(self, game_name: str):
        self._tray.notify("↩ Game Exited", f"{game_name} closed — settings restored.")
        self._status_bar.showMessage(f"  ↩ Auto Game Mode: {game_name} exited, restored")

    def _auto_clean_ram(self):
        try:
            from core.optimizer import clear_standby_memory
            ok, msg = clear_standby_memory()
            if ok:
                self._tray.notify("SRK Boost", "🧹 Standby memory cleaned automatically.")
        except Exception:
            pass

    def set_ram_auto_clean(self, enabled: bool, interval_min: int = 30):
        """Called from Settings page to toggle auto RAM clean."""
        if enabled:
            self._ram_clean_timer.setInterval(interval_min * 60 * 1000)
            self._ram_clean_timer.start()
        else:
            self._ram_clean_timer.stop()

    def set_auto_game_mode(self, enabled: bool):
        """Called from Settings page to toggle Auto Game Mode."""
        self._agm_watcher.set_enabled(enabled)

    def closeEvent(self, event):
        self._monitor.stop()
        self._agm_watcher.stop()
        self._agm_watcher.wait(2000)
        super().closeEvent(event)
