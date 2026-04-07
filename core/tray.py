"""
SRK Boost - System Tray Manager
Runs in background, shows live stats, quick boost/restore from tray.
"""

import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

logger = logging.getLogger(__name__)


def _make_tray_icon(cpu: int = 0) -> QPixmap:
    """Generate a dynamic tray icon showing CPU usage."""
    size = 32
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#1a1430")))
    painter.drawEllipse(1, 1, size - 2, size - 2)

    # Arc fill based on CPU
    from PyQt6.QtGui import QPen
    from PyQt6.QtCore import Qt as QtCore

    if cpu < 50:
        arc_color = QColor("#6c63ff")
    elif cpu < 80:
        arc_color = QColor("#ffaa00")
    else:
        arc_color = QColor("#ff4444")

    pen = QPen(arc_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    span = int(-360 * 16 * cpu / 100)
    painter.drawArc(5, 5, size - 10, size - 10, 90 * 16, span)

    # Center text
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 7, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, str(cpu))

    painter.end()
    return pix


class TrayManager(QObject):
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu = 0
        self._ram = 0
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon(_make_tray_icon(0)))
        self._tray.setToolTip("SRK Boost — Click to open")
        self._build_menu()
        self._tray.activated.connect(self._on_activated)

        # Icon refresh timer
        self._icon_timer = QTimer(self)
        self._icon_timer.setInterval(2000)
        self._icon_timer.timeout.connect(self._refresh_icon)
        self._icon_timer.start()

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: #0e0c1e;
                border: 1px solid rgba(108,99,255,0.3);
                border-radius: 10px;
                padding: 5px;
                color: #e0e0ff;
                font-size: 13px;
            }
            QMenu::item { padding: 8px 20px; border-radius: 6px; }
            QMenu::item:selected { background: rgba(108,99,255,0.2); }
            QMenu::separator { height:1px; background: rgba(80,60,140,0.3); margin: 4px 10px; }
        """)

        # Stats header (non-clickable)
        self.stats_action = menu.addAction("CPU: —%  |  RAM: —%")
        self.stats_action.setEnabled(False)
        menu.addSeparator()

        open_action = menu.addAction("⚡  Open SRK Boost")
        open_action.triggered.connect(self.show_window_requested.emit)

        menu.addSeparator()

        boost_action = menu.addAction("🚀  Quick Boost (Safe Tweaks)")
        boost_action.triggered.connect(self._quick_boost)

        restore_action = menu.addAction("↩  Restore Last Point")
        restore_action.triggered.connect(self._quick_restore)

        menu.addSeparator()

        quit_action = menu.addAction("✕  Quit SRK Boost")
        quit_action.triggered.connect(self.quit_requested.emit)

        self._menu = menu
        self._tray.setContextMenu(menu)

    def update_stats(self, stats: dict):
        self._cpu = int(stats.get("cpu_percent", 0))
        self._ram = int(stats.get("ram_percent", 0))
        self.stats_action.setText(f"CPU: {self._cpu}%  |  RAM: {self._ram}%")
        self._tray.setToolTip(
            f"SRK Boost\nCPU: {self._cpu}%  RAM: {self._ram}%"
        )

    def _refresh_icon(self):
        self._tray.setIcon(QIcon(_make_tray_icon(self._cpu)))

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    def _quick_boost(self):
        """Apply safe tweaks in background thread."""
        import core.optimizer as opt

        safe_tweaks = [
            opt.set_high_performance_power_plan,
            opt.disable_game_bar,
            opt.disable_network_throttling,
            opt.set_win32_priority_separation,
            opt.set_gpu_priority,
            opt.set_cpu_responsiveness,
        ]
        ok_count = 0
        for fn in safe_tweaks:
            try:
                ok, _ = fn()
                if ok:
                    ok_count += 1
            except Exception:
                pass

        self._tray.showMessage(
            "SRK Boost",
            f"⚡ Quick Boost applied! ({ok_count} tweaks)",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _quick_restore(self):
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.restore_latest()
            self._tray.showMessage(
                "SRK Boost",
                "↩ Restored to last restore point.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        except Exception as e:
            self._tray.showMessage(
                "SRK Boost",
                f"Restore failed: {e}",
                QSystemTrayIcon.MessageIcon.Warning,
                3000,
            )

    def notify(self, title: str, message: str):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
