"""
SRK Boost - System Scanner Page
Displays detailed hardware information.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QScrollArea, QProgressBar,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QColor

from core.system_info import SystemInfo
from core.i18n import tr, get_language

logger = logging.getLogger(__name__)


class ScanWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            data = SystemInfo.get_all()
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class InfoRow(QWidget):
    def __init__(self, label: str, value: str = "—", color: str = "#e0e0ff", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        lbl.setFixedWidth(160)
        self.val = QLabel(value)
        self.val.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 500;")
        self.val.setWordWrap(True)
        layout.addWidget(lbl)
        layout.addWidget(self.val)
        layout.addStretch()

    def set_value(self, v: str):
        self.val.setText(v)


class HardwareCard(QFrame):
    def __init__(self, title: str, icon: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(4)
        self._rows: dict[str, InfoRow] = {}

        title_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("card_title")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        self._layout.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #1e1e2e; max-height: 1px; margin: 6px 0;")
        self._layout.addWidget(sep)

    def add_row(self, key: str, label: str, value: str = "—", color: str = "#e0e0ff") -> InfoRow:
        row = InfoRow(label, value, color)
        self._layout.addWidget(row)
        self._rows[key] = row
        return row

    def set_value(self, key: str, value: str):
        if key in self._rows:
            self._rows[key].set_value(value)


class StorageBar(QWidget):
    def __init__(self, drive: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        drive_lbl = QLabel(f"💾 {drive.get('mountpoint', '?')}  ({drive.get('type', 'Drive')})")
        drive_lbl.setStyleSheet("color: #e0e0ff; font-weight: 600; font-size: 13px;")
        size_lbl = QLabel(f"{drive.get('used_gb', 0):.1f} / {drive.get('total_gb', 0):.1f} GB")
        size_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        top.addWidget(drive_lbl)
        top.addStretch()
        top.addWidget(size_lbl)
        layout.addLayout(top)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(drive.get("percent", 0)))
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        if drive.get("percent", 0) > 85:
            bar.setObjectName("danger_bar")
        elif drive.get("percent", 0) > 65:
            bar.setProperty("style", "warning")
        layout.addWidget(bar)

        fs_lbl = QLabel(f"Free: {drive.get('free_gb', 0):.1f} GB   FS: {drive.get('fstype', 'NTFS')}")
        fs_lbl.setStyleSheet("color: #6060a0; font-size: 11px;")
        layout.addWidget(fs_lbl)


class ScannerPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
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
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Scan button bar
        action_bar = QHBoxLayout()
        self.scan_btn = QPushButton(tr("scan_hardware"))
        self.scan_btn.setObjectName("primary_btn")
        self.scan_btn.setMinimumHeight(42)
        self.scan_btn.clicked.connect(self._start_scan)
        self.status_lbl = QLabel(tr("scan_click_hint"))
        self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        action_bar.addWidget(self.scan_btn)
        action_bar.addSpacing(16)
        action_bar.addWidget(self.status_lbl)
        action_bar.addStretch()
        layout.addLayout(action_bar)

        # Cards grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # CPU card
        self.cpu_card = HardwareCard(tr("processor"), "")
        self.cpu_card.add_row("name", "Model", "—", "#6c63ff")
        self.cpu_card.add_row("cores", "Cores / Threads", "—")
        self.cpu_card.add_row("freq", "Base Frequency", "—")
        self.cpu_card.add_row("arch", "Architecture", "—")
        grid.addWidget(self.cpu_card, 0, 0)

        # GPU card
        self.gpu_card = HardwareCard(tr("graphics_card"), "")
        self.gpu_card.add_row("name", "Model", "—", "#00d4ff")
        self.gpu_card.add_row("vram", "VRAM", "—")
        self.gpu_card.add_row("driver", "Driver Version", "—")
        self.gpu_card.add_row("res", "Resolution", "—")
        grid.addWidget(self.gpu_card, 0, 1)

        # RAM card
        self.ram_card = HardwareCard(tr("memory_ram"), "")
        self.ram_card.add_row("total", "Total", "—", "#00ff88")
        self.ram_card.add_row("type", "Type", "—")
        self.ram_card.add_row("speed", "Speed", "—")
        self.ram_card.add_row("slots", "Sticks", "—")
        grid.addWidget(self.ram_card, 1, 0)

        # Motherboard card
        self.mb_card = HardwareCard(tr("motherboard"), "")
        self.mb_card.add_row("mfr", "Manufacturer", "—", "#ffaa00")
        self.mb_card.add_row("product", "Product", "—")
        self.mb_card.add_row("version", "Version", "—")
        grid.addWidget(self.mb_card, 1, 1)

        # OS card
        self.os_card = HardwareCard(tr("operating_system"), "")
        self.os_card.add_row("name", "OS", "—", "#6c63ff")
        self.os_card.add_row("version", "Version", "—")
        self.os_card.add_row("arch", "Architecture", "—")
        self.os_card.add_row("hostname", "Hostname", "—")
        grid.addWidget(self.os_card, 2, 0, 1, 2)

        layout.addLayout(grid)

        # Storage section
        self.storage_title = QLabel("💿 Storage Drives")
        self.storage_title.setObjectName("card_title")
        self.storage_title.setStyleSheet("color: #e0e0ff; font-size: 16px; font-weight: 600; margin-top: 8px;")
        layout.addWidget(self.storage_title)

        self.storage_container = QVBoxLayout()
        self.storage_container.setSpacing(10)
        layout.addLayout(self.storage_container)
        layout.addStretch()

    def _start_scan(self):
        if self._thread and self._thread.isRunning():
            return
        self.scan_btn.setEnabled(False)
        self.status_lbl.setText("🔍 Scanning hardware...")
        self._worker = ScanWorker()
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_scan_done)
        self._worker.error.connect(self._on_scan_error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(dict)
    def _on_scan_done(self, data: dict):
        self.scan_btn.setEnabled(True)
        self.status_lbl.setText("✅ Scan complete.")

        cpu = data.get("cpu", {})
        self.cpu_card.set_value("name", cpu.get("name", "Unknown"))
        self.cpu_card.set_value("cores", f"{cpu.get('cores', 0)} cores / {cpu.get('threads', 0)} threads")
        self.cpu_card.set_value("freq", f"{cpu.get('base_freq_mhz', 0)} MHz")
        self.cpu_card.set_value("arch", cpu.get("architecture", "x64"))

        gpus = data.get("gpus", [])
        if gpus:
            gpu = gpus[0]
            self.gpu_card.set_value("name", gpu.get("name", "Unknown"))
            vram = gpu.get("vram_gb", 0)
            self.gpu_card.set_value("vram", f"{vram} GB" if vram > 0 else "Unknown")
            self.gpu_card.set_value("driver", gpu.get("driver_version", "Unknown"))
            self.gpu_card.set_value("res", gpu.get("resolution", "Unknown"))

        ram = data.get("ram", {})
        self.ram_card.set_value("total", f"{ram.get('total_gb', 0)} GB")
        self.ram_card.set_value("type", ram.get("type", "Unknown"))
        self.ram_card.set_value("speed", ram.get("speed_mhz", "Unknown"))
        sticks = ram.get("slots", [])
        self.ram_card.set_value("slots", f"{len(sticks)} stick(s)" if sticks else "Unknown")

        mb = data.get("motherboard", {})
        self.mb_card.set_value("mfr", mb.get("manufacturer", "Unknown"))
        self.mb_card.set_value("product", mb.get("product", "Unknown"))
        self.mb_card.set_value("version", mb.get("version", "Unknown"))

        os_info = data.get("os", {})
        self.os_card.set_value("name", f"{os_info.get('name', '?')} {os_info.get('release', '')}")
        self.os_card.set_value("version", os_info.get("version", "Unknown"))
        self.os_card.set_value("arch", os_info.get("machine", "x64"))
        self.os_card.set_value("hostname", os_info.get("hostname", "Unknown"))

        # Storage drives
        # Clear existing
        while self.storage_container.count():
            item = self.storage_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for drive in data.get("storage", []):
            bar = StorageBar(drive)
            self.storage_container.addWidget(bar)

    @pyqtSlot(str)
    def _on_scan_error(self, msg: str):
        self.scan_btn.setEnabled(True)
        self.status_lbl.setText(f"❌ Scan error: {msg}")
