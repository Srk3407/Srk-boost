"""
SRK Boost - Cleaner Page
Scans and removes temp files and browser caches.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem, QProgressBar,
    QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QColor
from ui.confirm_dialog import ConfirmDialog

logger = logging.getLogger(__name__)


def _format_size(b: int) -> str:
    if b >= 1024 ** 3:
        return f"{b / (1024**3):.2f} GB"
    elif b >= 1024 ** 2:
        return f"{b / (1024**2):.2f} MB"
    elif b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"


def _scan_dir(path: str) -> Tuple[int, int]:
    """Returns (file_count, total_bytes) for a directory."""
    count, total = 0, 0
    try:
        for entry in Path(path).rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                    count += 1
                except Exception:
                    pass
    except Exception:
        pass
    return count, total


def _clean_dir(path: str) -> Tuple[int, int]:
    """Delete all files in a directory. Returns (deleted_count, freed_bytes)."""
    deleted, freed = 0, 0
    try:
        for entry in Path(path).iterdir():
            try:
                if entry.is_file():
                    size = entry.stat().st_size
                    entry.unlink()
                    deleted += 1
                    freed += size
                elif entry.is_dir():
                    size = sum(
                        f.stat().st_size
                        for f in entry.rglob("*") if f.is_file()
                    )
                    shutil.rmtree(entry, ignore_errors=True)
                    freed += size
                    deleted += 1
            except Exception:
                pass
    except Exception:
        pass
    return deleted, freed


def get_scan_targets() -> List[dict]:
    """Return list of scan target descriptors."""
    user = os.path.expanduser("~")
    appdata = os.getenv("APPDATA", os.path.join(user, "AppData", "Roaming"))
    local = os.getenv("LOCALAPPDATA", os.path.join(user, "AppData", "Local"))

    targets = [
        {
            "id": "user_temp",
            "label": "User Temp Files",
            "path": os.environ.get("TEMP", os.path.join(local, "Temp")),
            "icon": "🗑",
        },
        {
            "id": "win_temp",
            "label": "Windows Temp",
            "path": r"C:\Windows\Temp",
            "icon": "🪟",
        },
        {
            "id": "prefetch",
            "label": "Prefetch Cache",
            "path": r"C:\Windows\Prefetch",
            "icon": "⚡",
        },
        {
            "id": "chrome_cache",
            "label": "Chrome Cache",
            "path": os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache"),
            "icon": "🌐",
        },
        {
            "id": "edge_cache",
            "label": "Edge Cache",
            "path": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
            "icon": "🌊",
        },
        {
            "id": "firefox_cache",
            "label": "Firefox Cache",
            "path": os.path.join(local, "Mozilla", "Firefox", "Profiles"),
            "icon": "🦊",
        },
        {
            "id": "thumbnails",
            "label": "Thumbnail Cache",
            "path": os.path.join(local, "Microsoft", "Windows", "Explorer"),
            "icon": "🖼",
        },
        {
            "id": "recent",
            "label": "Recent Files List",
            "path": os.path.join(appdata, "Microsoft", "Windows", "Recent"),
            "icon": "📂",
        },
    ]
    return targets


class ScanWorker(QObject):
    item_scanned = pyqtSignal(str, int, int)  # id, count, bytes
    finished = pyqtSignal()

    def __init__(self, targets: List[dict]):
        super().__init__()
        self.targets = targets

    def run(self):
        for t in self.targets:
            count, size = _scan_dir(t["path"])
            self.item_scanned.emit(t["id"], count, size)
        self.finished.emit()


class CleanWorker(QObject):
    item_cleaned = pyqtSignal(str, int, int)  # id, deleted, freed
    finished = pyqtSignal(int, int)            # total_deleted, total_freed

    def __init__(self, targets: List[dict]):
        super().__init__()
        self.targets = targets

    def run(self):
        total_d, total_f = 0, 0
        for t in self.targets:
            d, f = _clean_dir(t["path"])
            self.item_cleaned.emit(t["id"], d, f)
            total_d += d
            total_f += f
        self.finished.emit(total_d, total_f)


class TargetRow(QWidget):
    def __init__(self, target: dict, parent=None):
        super().__init__(parent)
        self.target_id = target["id"]
        self._file_count = 0
        self._size_bytes = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.check = QCheckBox()
        self.check.setObjectName("toggle")
        self.check.setChecked(True)
        layout.addWidget(self.check)

        icon = QLabel(target["icon"])
        icon.setStyleSheet("font-size: 16px;")
        icon.setFixedWidth(22)
        layout.addWidget(icon)

        name = QLabel(target["label"])
        name.setStyleSheet("color: #e0e0ff; font-size: 13px; font-weight: bold;")
        name.setMinimumWidth(160)
        layout.addWidget(name)

        # Path label
        path_lbl = QLabel(target.get("path", ""))
        path_lbl.setStyleSheet("color: #404060; font-size: 10px;")
        path_lbl.setMinimumWidth(200)
        layout.addWidget(path_lbl)

        layout.addStretch()

        self.size_lbl = QLabel("—")
        self.size_lbl.setStyleSheet("color: #6060a0; font-size: 12px; min-width: 160px;")
        self.size_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.size_lbl)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 11px; min-width: 110px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_lbl)

        outer.addLayout(layout)

        # Progress bar per category
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #1e1e2e; border-radius: 2px; border: none; }
            QProgressBar::chunk { background: #6c63ff; border-radius: 2px; }
        """)
        outer.addWidget(self.progress_bar)

    def set_scanning(self):
        """Show scanning state."""
        self.size_lbl.setText("Scanning...")
        self.size_lbl.setStyleSheet("color: #6060a0; font-size: 12px; min-width: 160px;")
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(True)

    def set_scan_result(self, count: int, size_bytes: int):
        self._file_count = count
        self._size_bytes = size_bytes
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        if size_bytes > 0:
            self.size_lbl.setText(f"Found {count:,} files  •  {_format_size(size_bytes)}")
            self.size_lbl.setStyleSheet("color: #00ff88; font-size: 12px; font-weight: bold; min-width: 160px;")
            # Show relative progress fill (visual only — fill based on size)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(100, max(5, int(size_bytes / (1024 * 1024)))))
            self.progress_bar.setStyleSheet("""
                QProgressBar { background: #1e1e2e; border-radius: 2px; border: none; }
                QProgressBar::chunk { background: #ffaa00; border-radius: 2px; }
            """)
            self.progress_bar.setVisible(True)
        else:
            self.size_lbl.setText("Empty / Not found")
            self.size_lbl.setStyleSheet("color: #404060; font-size: 12px; min-width: 160px;")
            self.check.setChecked(False)

    def set_cleaned(self, freed: int):
        self.progress_bar.setVisible(False)
        self.status_lbl.setText(f"✓ {_format_size(freed)} freed")
        self.status_lbl.setStyleSheet("color: #00ff88; font-size: 11px; min-width: 110px;")
        self.size_lbl.setText("Cleaned")
        self.size_lbl.setStyleSheet("color: #404060; font-size: 12px; min-width: 160px;")

    @property
    def is_checked(self) -> bool:
        return self.check.isChecked()


class CleanerPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._targets = get_scan_targets()
        self._rows: dict[str, TargetRow] = {}
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
        layout.setSpacing(20)

        # ── Summary card ─────────────────────────────────────────────────────
        summary = QFrame()
        summary.setObjectName("card")
        sum_layout = QHBoxLayout(summary)
        sum_layout.setContentsMargins(20, 16, 20, 16)
        sum_layout.setSpacing(30)

        def _sum_stat(label, val, color):
            col = QVBoxLayout()
            col.setSpacing(4)
            v = QLabel(val)
            v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
            l = QLabel(label)
            l.setStyleSheet("color: #6060a0; font-size: 11px;")
            col.addWidget(v)
            col.addWidget(l)
            return col, v

        col1, self.total_size_lbl = _sum_stat("Junk Found", "—", "#ffaa00")
        col2, self.total_files_lbl = _sum_stat("Files Found", "—", "#6c63ff")
        col3, self.freed_lbl = _sum_stat("Space Freed", "—", "#00ff88")

        sum_layout.addLayout(col1)
        sum_layout.addLayout(col2)
        sum_layout.addLayout(col3)
        sum_layout.addStretch()

        # Scan + Clean buttons
        btn_col = QVBoxLayout()
        self.scan_btn = QPushButton("🔍  Scan")
        self.scan_btn.setObjectName("primary_btn")
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.clicked.connect(self._start_scan)

        self.clean_btn = QPushButton("🧹  Clean Selected")
        self.clean_btn.setObjectName("danger_btn")
        self.clean_btn.setMinimumHeight(40)
        self.clean_btn.setEnabled(False)
        self.clean_btn.clicked.connect(self._start_clean)

        btn_col.addWidget(self.scan_btn)
        btn_col.addWidget(self.clean_btn)
        sum_layout.addLayout(btn_col)
        layout.addWidget(summary)

        # ── Progress bar ─────────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, len(self._targets))
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("Press 'Scan' to find junk files.")
        self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        # ── Targets list card ────────────────────────────────────────────────
        list_card = QFrame()
        list_card.setObjectName("card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(16, 14, 16, 16)
        list_layout.setSpacing(4)

        list_title = QLabel("🗂 Scan Targets")
        list_title.setObjectName("card_title")
        list_layout.addWidget(list_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #1e1e2e; max-height: 1px; margin: 6px 0;")
        list_layout.addWidget(sep)

        for t in self._targets:
            row = TargetRow(t)
            self._rows[t["id"]] = row
            list_layout.addWidget(row)

        layout.addWidget(list_card)
        layout.addStretch()

    def _start_scan(self):
        if self._thread and self._thread.isRunning():
            return
        # Reset
        for row in self._rows.values():
            row.set_scanning()
            row.status_lbl.setText("")
        self.total_size_lbl.setText("—")
        self.total_files_lbl.setText("—")
        self.freed_lbl.setText("—")
        self.progress.setValue(0)
        self.scan_btn.setEnabled(False)
        self.clean_btn.setEnabled(False)
        self.status_lbl.setText("🔍 Scanning for junk files...")

        self._scan_results = {}
        self._worker = ScanWorker(self._targets)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.item_scanned.connect(self._on_item_scanned)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(str, int, int)
    def _on_item_scanned(self, tid: str, count: int, size: int):
        if tid in self._rows:
            self._rows[tid].set_scan_result(count, size)
        self._scan_results[tid] = (count, size)
        done = len(self._scan_results)
        self.progress.setValue(done)

    def _on_scan_finished(self):
        self.scan_btn.setEnabled(True)
        total_size = sum(v[1] for v in self._scan_results.values())
        total_files = sum(v[0] for v in self._scan_results.values())
        self.total_size_lbl.setText(_format_size(total_size))
        self.total_files_lbl.setText(f"{total_files:,}")
        if total_files > 0:
            self.status_lbl.setText(
                f"✅ Scan complete — Found {total_files:,} files ({_format_size(total_size)})"
            )
            self.status_lbl.setStyleSheet("color: #00ff88; font-size: 12px; font-weight: bold;")
        else:
            self.status_lbl.setText("✅ Scan complete — No junk files found.")
            self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        self.clean_btn.setEnabled(total_size > 0)

    def _start_clean(self):
        if self._thread and self._thread.isRunning():
            return
        selected = [t for t in self._targets if self._rows[t["id"]].is_checked]
        if not selected:
            return

        # Confirmation dialog
        action_labels = [f"Delete all files in: {t['label']}" for t in selected]
        dlg = ConfirmDialog(
            parent=self,
            title="Clean Junk Files?",
            description="The following locations will be permanently cleaned:",
            actions=action_labels,
            show_restore_note=False,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        self.clean_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status_lbl.setText("🧹 Cleaning junk files...")

        self._worker = CleanWorker(selected)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.item_cleaned.connect(self._on_item_cleaned)
        self._worker.finished.connect(self._on_clean_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(str, int, int)
    def _on_item_cleaned(self, tid: str, deleted: int, freed: int):
        if tid in self._rows:
            self._rows[tid].set_cleaned(freed)
        self.progress.setValue(self.progress.value() + 1)

    @pyqtSlot(int, int)
    def _on_clean_finished(self, deleted: int, freed: int):
        self.scan_btn.setEnabled(True)
        self.freed_lbl.setText(_format_size(freed))
        self.status_lbl.setText(
            f"✅ Cleaned {deleted} items and freed {_format_size(freed)}."
        )
