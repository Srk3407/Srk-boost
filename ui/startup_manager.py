"""
SRK Boost - Startup Manager  v2.0
Read/toggle/delete Windows startup registry entries — premium UI.
"""

import subprocess

# Windows: suppress console window
import sys as _sys, subprocess as _sp
_CREATE_NO_WINDOW = _sp.CREATE_NO_WINDOW if _sys.platform == "win32" else 0  # type: ignore

import logging
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QScrollArea,
    QHeaderView, QAbstractItemView, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QColor, QBrush

logger = logging.getLogger(__name__)

STARTUP_KEYS = [
    (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
    (r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
    (r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM (32)"),
]
APPROVED_KEY = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"


def _is_enabled(name: str) -> bool:
    try:
        r = subprocess.run(
            ["reg", "query", APPROVED_KEY, "/v", name],
            capture_output=True, creationflags=_CREATE_NO_WINDOW, text=True, timeout=5
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if name in line and "REG_BINARY" in line:
                    val = line.split()[-1] if line.split() else "02"
                    return not val.startswith("03")
        return True
    except Exception:
        return True


def get_startup_entries() -> List[Dict]:
    entries = []
    for reg_key, scope in STARTUP_KEYS:
        try:
            r = subprocess.run(["reg", "query", reg_key],
                               capture_output=True, creationflags=_CREATE_NO_WINDOW, text=True, timeout=10)
            if r.returncode != 0:
                continue
            for line in r.stdout.splitlines():
                line = line.strip()
                if not line or line == reg_key or "REG_" not in line:
                    continue
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    name, _, value = parts[0], parts[1], parts[2]
                    entries.append({
                        "name": name,
                        "command": value,
                        "scope": scope,
                        "reg_key": reg_key,
                        "enabled": _is_enabled(name),
                    })
        except Exception as e:
            logger.warning(f"Registry query failed {reg_key}: {e}")
    return entries


def set_startup_enabled(entry: Dict, enabled: bool) -> bool:
    try:
        val = "0200000000000000" if enabled else "0300000000000000"
        r = subprocess.run([
            "reg", "add", APPROVED_KEY,
            "/v", entry["name"],
            "/t", "REG_BINARY",
            "/d", val, "/f"
        ], capture_output=True, creationflags=_CREATE_NO_WINDOW, text=True, timeout=5)
        return r.returncode == 0
    except Exception as e:
        logger.error(f"set_startup_enabled: {e}")
        return False


def delete_startup_entry(entry: Dict) -> bool:
    try:
        r = subprocess.run([
            "reg", "delete", entry["reg_key"],
            "/v", entry["name"], "/f"
        ], capture_output=True, creationflags=_CREATE_NO_WINDOW, text=True, timeout=5)
        return r.returncode == 0
    except Exception as e:
        logger.error(f"delete_startup_entry: {e}")
        return False


class StartupWorker(QObject):
    finished = pyqtSignal(list)

    def run(self):
        self.finished.emit(get_startup_entries())


# ─────────────────────────────────────────────────────────────────────────────

class StartupManagerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: List[Dict] = []
        self._thread = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        c = QWidget()
        scroll.setWidget(c)
        layout = QVBoxLayout(c)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(3)
        t = QLabel("🚀  Başlangıç Yöneticisi")
        t.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 900; background: transparent;")
        s = QLabel("Control boot-time programs — disable unwanted entries to speed up startup")
        s.setStyleSheet("color: #3a3a6a; font-size: 12px; background: transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()

        self.load_btn = QPushButton("🔍  Load Entries")
        self.load_btn.setObjectName("primary_btn")
        self.load_btn.setFixedHeight(40)
        self.load_btn.clicked.connect(self._load)
        hdr.addWidget(self.load_btn)
        layout.addLayout(hdr)

        # ── Stat cards ────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.total_card   = self._stat_card("Total Entries",    "—",  "#6c63ff")
        self.enabled_card = self._stat_card("Enabled",          "—",  "#00e87a")
        self.disabled_card= self._stat_card("Disabled",         "—",  "#ff5555")
        self.hkcu_card    = self._stat_card("User (HKCU)",      "—",  "#00d4ff")
        for card in [self.total_card, self.enabled_card, self.disabled_card, self.hkcu_card]:
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        # ── Status ────────────────────────────────────────────────────────────
        self.status_lbl = QLabel("Click 'Load Entries' to read startup programs from the registry.")
        self.status_lbl.setStyleSheet("color: #4a4870; font-size: 12px; background: transparent;")
        layout.addWidget(self.status_lbl)

        # ── Table card ────────────────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setObjectName("card")
        tfl = QVBoxLayout(table_frame)
        tfl.setContentsMargins(0, 0, 0, 0)
        tfl.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(
            "background: rgba(108,99,255,0.06); "
            "border-bottom: 1px solid rgba(108,99,255,0.12); "
            "border-radius: 16px 16px 0 0;"
        )
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(20, 12, 20, 12)
        tb.setSpacing(10)

        section_lbl = QLabel("📋  STARTUP PROGRAMS")
        section_lbl.setStyleSheet(
            "color: rgba(108,99,255,0.6); font-size: 10px; font-weight: 900; "
            "letter-spacing: 2px; background: transparent;"
        )
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #3a3a6a; font-size: 11px; background: transparent;")
        tb.addWidget(section_lbl)
        tb.addStretch()
        tb.addWidget(self.count_lbl)

        self.enable_btn = QPushButton("▶  Enable Selected")
        self.enable_btn.setStyleSheet(
            "background: rgba(0,232,122,0.12); color: #00e87a; "
            "border: 1px solid rgba(0,232,122,0.35); border-radius: 8px; "
            "padding: 6px 14px; font-size: 12px; font-weight: 700;"
        )
        self.enable_btn.clicked.connect(lambda: self._set_enabled(True))
        tb.addWidget(self.enable_btn)

        self.disable_btn = QPushButton("⏸  Disable Selected")
        self.disable_btn.setStyleSheet(
            "background: rgba(108,99,255,0.1); color: #8b83ff; "
            "border: 1px solid rgba(108,99,255,0.3); border-radius: 8px; "
            "padding: 6px 14px; font-size: 12px; font-weight: 700;"
        )
        self.disable_btn.clicked.connect(lambda: self._set_enabled(False))
        tb.addWidget(self.disable_btn)

        self.delete_btn = QPushButton("🗑  Delete Selected")
        self.delete_btn.setStyleSheet(
            "background: rgba(239,68,68,0.12); color: #ff6060; "
            "border: 1px solid rgba(239,68,68,0.35); border-radius: 8px; "
            "padding: 6px 14px; font-size: 12px; font-weight: 700;"
        )
        self.delete_btn.clicked.connect(self._delete_selected)
        tb.addWidget(self.delete_btn)
        tfl.addWidget(toolbar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["", "#", "Name", "Command", "Scope"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 44)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 36)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 90)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(420)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background: transparent;
                border: none;
                alternate-background-color: rgba(108,99,255,0.03);
                selection-background-color: transparent;
            }
            QTableWidget::item {
                padding: 4px 10px;
                border-bottom: 1px solid rgba(30,24,50,0.8);
            }
            QTableWidget::item:selected { background: rgba(108,99,255,0.12); }
            QHeaderView::section {
                background: transparent;
                color: rgba(108,99,255,0.5);
                border: none;
                border-bottom: 1px solid rgba(108,99,255,0.1);
                padding: 8px;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1.5px;
            }
            QCheckBox { background: transparent; }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 2px solid rgba(108,99,255,0.4);
                background: rgba(10,9,20,0.8);
            }
            QCheckBox::indicator:checked {
                background: rgba(108,99,255,0.8);
                border: 2px solid #6c63ff;
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(108,99,255,0.8);
            }
        """)
        tfl.addWidget(self.table)
        layout.addWidget(table_frame)
        layout.addStretch()

    def _stat_card(self, label: str, value: str, color: str) -> QFrame:
        f = QFrame()
        f.setObjectName("card")
        vl = QVBoxLayout(f)
        vl.setContentsMargins(20, 14, 20, 14)
        vl.setSpacing(4)
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 900; background: transparent;")
        lb = QLabel(label)
        lb.setStyleSheet("color: rgba(160,150,220,0.45); font-size: 10px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
        vl.addWidget(v)
        vl.addWidget(lb)
        f._val = v
        return f

    def _update_stat(self, card, value: str):
        card._val.setText(value)

    def _load(self):
        if self._thread and self._thread.isRunning():
            return
        self.load_btn.setEnabled(False)
        self.status_lbl.setText("🔍 Reading registry startup entries...")
        self.table.setRowCount(0)

        self._worker = StartupWorker()
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(list)
    def _on_loaded(self, entries: List[Dict]):
        self._entries = entries
        self.load_btn.setEnabled(True)
        enabled_count = sum(1 for e in entries if e["enabled"])
        disabled_count = len(entries) - enabled_count
        hkcu_count = sum(1 for e in entries if e["scope"] == "HKCU")
        self._update_stat(self.total_card,    str(len(entries)))
        self._update_stat(self.enabled_card,  str(enabled_count))
        self._update_stat(self.disabled_card, str(disabled_count))
        self._update_stat(self.hkcu_card,     str(hkcu_count))
        self.status_lbl.setText(
            f"✅  Found {len(entries)} startup entries  •  "
            f"{enabled_count} enabled  •  {disabled_count} disabled"
        )
        self._populate(entries)

    def _populate(self, entries: List[Dict]):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.count_lbl.setText(f"{len(entries)} entries")

        for i, entry in enumerate(entries):
            row = self.table.rowCount()
            self.table.insertRow(row)
            enabled = entry.get("enabled", True)
            dim_color = "#4a4870" if not enabled else "#c0b8e8"

            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            # Number
            num = QTableWidgetItem(str(i + 1))
            num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setForeground(QBrush(QColor("#3a3a6a")))
            num.setData(Qt.ItemDataRole.UserRole, entry["name"])
            self.table.setItem(row, 1, num)

            # Name — with enabled/disabled badge
            badge = "🟢" if enabled else "🔴"
            name_item = QTableWidgetItem(f"{badge}  {entry['name']}")
            name_item.setForeground(QBrush(QColor(dim_color)))
            name_item.setData(Qt.ItemDataRole.UserRole, entry["name"])
            self.table.setItem(row, 2, name_item)

            # Command (truncate visually via tooltip)
            cmd_item = QTableWidgetItem(entry["command"])
            cmd_item.setForeground(QBrush(QColor("#4a4870" if not enabled else "#6060a0")))
            cmd_item.setToolTip(entry["command"])
            self.table.setItem(row, 3, cmd_item)

            # Scope
            scope_item = QTableWidgetItem(entry["scope"])
            scope_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            scope_color = "#00d4ff" if entry["scope"] == "HKCU" else "#f97316"
            scope_item.setForeground(QBrush(QColor(scope_color)))
            self.table.setItem(row, 4, scope_item)

        self.table.blockSignals(False)

    def _get_checkbox(self, row: int):
        w = self.table.cellWidget(row, 0)
        if w:
            for child in w.children():
                if isinstance(child, QCheckBox):
                    return child
        return None

    def _selected_entries(self) -> List[tuple]:
        result = []
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isChecked():
                item = self.table.item(row, 1)
                if item:
                    name = item.data(Qt.ItemDataRole.UserRole)
                    entry = next((e for e in self._entries if e["name"] == name), None)
                    if entry:
                        result.append((row, entry))
        return result

    def _set_enabled(self, enabled: bool):
        selected = self._selected_entries()
        if not selected:
            self.status_lbl.setText("⚠️  No entries selected.")
            return
        ok = 0
        for row, entry in selected:
            if set_startup_enabled(entry, enabled):
                entry["enabled"] = enabled
                badge = "🟢" if enabled else "🔴"
                dim_color = "#4a4870" if not enabled else "#c0b8e8"
                name_item = QTableWidgetItem(f"{badge}  {entry['name']}")
                name_item.setForeground(QBrush(QColor(dim_color)))
                name_item.setData(Qt.ItemDataRole.UserRole, entry["name"])
                self.table.setItem(row, 2, name_item)
                cmd_item = self.table.item(row, 3)
                if cmd_item:
                    cmd_item.setForeground(QBrush(QColor("#4a4870" if not enabled else "#6060a0")))
                ok += 1
        action = "enabled" if enabled else "disabled"
        self.status_lbl.setText(f"✅  {ok} entries {action}.")
        # refresh stats
        en = sum(1 for e in self._entries if e["enabled"])
        self._update_stat(self.enabled_card,  str(en))
        self._update_stat(self.disabled_card, str(len(self._entries) - en))

    def _delete_selected(self):
        selected = self._selected_entries()
        if not selected:
            self.status_lbl.setText("⚠️  No entries selected.")
            return
        deleted = 0
        for row, entry in sorted(selected, key=lambda x: x[0], reverse=True):
            if delete_startup_entry(entry):
                self.table.removeRow(row)
                self._entries.remove(entry)
                deleted += 1
        self.status_lbl.setText(f"🗑  Deleted {deleted} startup entries.")
        self._update_stat(self.total_card,    str(len(self._entries)))
        en = sum(1 for e in self._entries if e["enabled"])
        self._update_stat(self.enabled_card,  str(en))
        self._update_stat(self.disabled_card, str(len(self._entries) - en))
        self.count_lbl.setText(f"{len(self._entries)} entries")
