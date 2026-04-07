"""
SRK Boost - Game Mode Page  v2.0
Running processes table — kill background apps to free RAM before gaming.
"""

import logging
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QScrollArea,
    QHeaderView, QAbstractItemView, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot, QTimer
from PyQt6.QtGui import QColor, QBrush, QFont
from ui.confirm_dialog import ConfirmDialog
from core.i18n import tr

logger = logging.getLogger(__name__)

SAFE_PROCESSES = {
    'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
    'services.exe', 'lsass.exe', 'svchost.exe', 'explorer.exe',
    'python.exe', 'pythonw.exe', 'python3.exe', 'main.py',
    'dwm.exe', 'registry', 'idle',
}

PROCESS_DESC = {
    "chrome.exe": "Google Chrome Browser",
    "firefox.exe": "Mozilla Firefox Browser",
    "msedge.exe": "Microsoft Edge Browser",
    "brave.exe": "Brave Browser",
    "discord.exe": "Discord Chat App",
    "steam.exe": "Steam Game Platform",
    "steamwebhelper.exe": "Steam Web Helper",
    "spotify.exe": "Spotify Music Player",
    "slack.exe": "Slack Team Chat",
    "teams.exe": "Microsoft Teams",
    "zoom.exe": "Zoom Video Calls",
    "telegram.exe": "Telegram Messenger",
    "whatsapp.exe": "WhatsApp Desktop",
    "code.exe": "Visual Studio Code",
    "vlc.exe": "VLC Media Player",
    "obs64.exe": "OBS Studio",
    "onedrive.exe": "Microsoft OneDrive",
    "dropbox.exe": "Dropbox Sync",
    "googledrivefs.exe": "Google Drive Sync",
    "explorer.exe": "Windows File Explorer",
    "lghub.exe": "Logitech G HUB",
    "corsairhid.exe": "Corsair iCUE",
    "msiafterburner.exe": "MSI Afterburner",
    "razer synapse 3.exe": "Razer Synapse",
    "epicgameslauncher.exe": "Epic Games Launcher",
    "battle.net.exe": "Battle.net Launcher",
    "robloxplayerbeta.exe": "Roblox Client",
    "origin.exe": "EA Origin Launcher",
    "upc.exe": "Ubisoft Connect",
    "msmpeng.exe": "Windows Defender",
    "avastui.exe": "Avast Antivirus",
    "avgui.exe": "AVG Antivirus",
    "ccleaner.exe": "CCleaner",
    "hwinfo64.exe": "HWiNFO Monitor",
    "cpuz.exe": "CPU-Z Info",
    "taskmgr.exe": "Task Manager",
    "audiodg.exe": "Windows Audio",
    "ctfmon.exe": "Language/Input Method",
    "searchindexer.exe": "Windows Search Indexer",
    "spoolsv.exe": "Print Spooler",
    "wuauclt.exe": "Windows Update",
    "runtimebroker.exe": "Runtime Broker",
    "sihost.exe": "Shell Infrastructure Host",
}


def get_processes() -> List[Dict]:
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = p.info
                name = info["name"] or "Unknown"
                mem_mb = round(info["memory_info"].rss / (1024 ** 2), 1) if info["memory_info"] else 0
                if mem_mb < 1.0:
                    continue
                is_safe = name.lower() in SAFE_PROCESSES
                desc = PROCESS_DESC.get(name.lower(), "")
                if not desc and is_safe:
                    desc = "🔒 Protected  •  System Process"
                procs.append({
                    "pid": info["pid"],
                    "name": name,
                    "cpu": info.get("cpu_percent") or 0.0,
                    "mem_mb": mem_mb,
                    "killable": not is_safe,
                    "is_safe": is_safe,
                    "description": desc,
                })
            except Exception:
                pass
        procs.sort(key=lambda x: x["mem_mb"], reverse=True)
        return procs[:200]
    except Exception as e:
        logger.error(f"get_processes: {e}")
        return []


def kill_process(pid: int) -> bool:
    try:
        import psutil
        proc = psutil.Process(pid)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()  # force if terminate didn't work
        return True
    except psutil.NoSuchProcess:
        return True  # already gone — count as success
    except Exception as e:
        logger.warning(f"kill {pid}: {e}")
        return False


class KillWorker(QObject):
    finished = pyqtSignal(list, int)

    def __init__(self, pids):
        super().__init__()
        self.pids = pids

    def run(self):
        killed, fails = [], 0
        for pid in self.pids:
            if kill_process(pid):
                killed.append(pid)
            else:
                fails += 1
        self.finished.emit(killed, fails)


class LoadWorker(QObject):
    finished = pyqtSignal(list)

    def run(self):
        self.finished.emit(get_processes())


# ─────────────────────────────────────────────────────────────────────────────

class GameModePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes: List[Dict] = []
        self._load_thread = None
        self._kill_thread = None
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
        t = QLabel("⚡  Game Mode")
        t.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 900; background: transparent;")
        s = QLabel("Kill background apps to free RAM and CPU before gaming")
        s.setStyleSheet("color: #3a3a6a; font-size: 12px; background: transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()

        self.load_btn = QPushButton("🔄  Load Processes")
        self.load_btn.setObjectName("primary_btn")
        self.load_btn.setFixedHeight(40)
        self.load_btn.clicked.connect(self._load)
        hdr.addWidget(self.load_btn)
        layout.addLayout(hdr)

        # ── Stat cards ────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.total_card  = self._stat_card("Total Processes", "—",  "#6c63ff")
        self.sel_card    = self._stat_card("Selected",        "0",  "#00d4ff")
        self.killed_card = self._stat_card("Processes Killed","0",  "#00e87a")
        self.ram_card    = self._stat_card("Est. RAM Freed",  "~0 MB", "#f97316")
        for card in [self.total_card, self.sel_card, self.killed_card, self.ram_card]:
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        # ── Status label ──────────────────────────────────────────────────────
        self.status_lbl = QLabel("Click 'Load Processes' to list running applications.")
        self.status_lbl.setStyleSheet("color: #4a4870; font-size: 12px; background: transparent;")
        layout.addWidget(self.status_lbl)

        # ── Table card ────────────────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setObjectName("card")
        tfl = QVBoxLayout(table_frame)
        tfl.setContentsMargins(0, 0, 0, 0)
        tfl.setSpacing(0)

        # Table toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(
            "background: rgba(108,99,255,0.06); "
            "border-bottom: 1px solid rgba(108,99,255,0.12); "
            "border-radius: 16px 16px 0 0;"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 12, 20, 12)
        tb_layout.setSpacing(10)

        section_lbl = QLabel("🔴  RUNNING PROCESSES")
        section_lbl.setStyleSheet(
            "color: rgba(108,99,255,0.6); font-size: 10px; font-weight: 900; "
            "letter-spacing: 2px; background: transparent;"
        )
        tb_layout.addWidget(section_lbl)
        tb_layout.addStretch()

        self.sel_all_btn = QPushButton("☑  Tümünü Seç")
        self.sel_all_btn.setStyleSheet(
            "background: rgba(108,99,255,0.12); color: #8b83ff; "
            "border: 1px solid rgba(108,99,255,0.35); border-radius: 8px; "
            "padding: 6px 14px; font-size: 12px; font-weight: 700;"
        )
        self.sel_all_btn.clicked.connect(self._select_all)
        tb_layout.addWidget(self.sel_all_btn)

        self.desel_btn = QPushButton("☐  Seçimi Kaldır")
        self.desel_btn.setStyleSheet(
            "background: rgba(60,55,100,0.08); color: #5050a0; "
            "border: 1px solid rgba(60,55,100,0.25); border-radius: 8px; "
            "padding: 6px 14px; font-size: 12px; font-weight: 700;"
        )
        self.desel_btn.clicked.connect(self._deselect_all)
        tb_layout.addWidget(self.desel_btn)

        self.kill_btn = QPushButton("⚡  Seçilenleri Kapat")
        self.kill_btn.setStyleSheet(
            "background: rgba(239,68,68,0.15); color: #ff6060; "
            "border: 1px solid rgba(239,68,68,0.4); border-radius: 8px; "
            "padding: 6px 18px; font-size: 12px; font-weight: 700;"
        )
        self.kill_btn.clicked.connect(self._kill_selected)
        tb_layout.addWidget(self.kill_btn)

        tfl.addWidget(toolbar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["", "#", "İşlem", "CPU %", "RAM (MB)"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 44)  # checkbox
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 36)  # number
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 70)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 90)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(460)
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
                padding: 4px 8px;
                border-bottom: 1px solid rgba(30,24,50,0.8);
                color: #c0b8e8;
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
                image: none;
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(108,99,255,0.8);
            }
        """)
        self.table.cellChanged.connect(self._on_cell_changed)
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

    def _update_stat(self, card: QFrame, value: str):
        card._val.setText(value)

    def _load(self):
        if self._load_thread and self._load_thread.isRunning():
            return
        self.load_btn.setEnabled(False)
        self.status_lbl.setText("🔍 Loading processes...")
        self.table.setRowCount(0)

        self._lworker = LoadWorker()
        self._load_thread = QThread()
        self._lworker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._lworker.run)
        self._lworker.finished.connect(self._on_loaded)
        self._lworker.finished.connect(self._load_thread.quit)
        self._load_thread.start()

    @pyqtSlot(list)
    def _on_loaded(self, procs: List[Dict]):
        self._processes = procs
        self.load_btn.setEnabled(True)
        self.status_lbl.setText(f"✅  Loaded {len(procs)} processes.")
        self._update_stat(self.total_card, str(len(procs)))
        self._update_stat(self.killed_card, "0")
        self._update_stat(self.ram_card, "~0 MB")
        self._populate(procs)

    def _populate(self, procs: List[Dict]):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for i, p in enumerate(procs):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox col
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setEnabled(p["killable"])
            chk.stateChanged.connect(self._update_selection_count)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            # Number
            num = QTableWidgetItem(str(i + 1))
            num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setForeground(QBrush(QColor("#3a3a6a")))
            self.table.setItem(row, 1, num)

            # Name + description
            name = p["name"]
            desc = p.get("description", "")
            is_safe = p.get("is_safe", False)

            name_item = QTableWidgetItem(name)
            if is_safe:
                name_item.setForeground(QBrush(QColor("#ff6060")))
            else:
                name_item.setForeground(QBrush(QColor("#e0e0ff")))

            if desc:
                name_item.setText(f"{name}   —   {desc}" if not is_safe else name)
                if is_safe:
                    name_item.setToolTip(f"🔒 Protected — {desc or 'System Process'}")
                else:
                    name_item.setToolTip(desc)
            self.table.setItem(row, 2, name_item)

            # If safe, show description in separate col span via tooltip; mark red
            if is_safe:
                desc_item = QTableWidgetItem(f"🔒 Protected  •  {desc}" if desc else "🔒 Protected")
                desc_item.setForeground(QBrush(QColor("#ff4040")))
            else:
                desc_item = QTableWidgetItem(desc)
                desc_item.setForeground(QBrush(QColor("#6060a0")))
            # Overwrite col 2 with combined
            combined = QTableWidgetItem()
            if is_safe:
                combined.setText(f"🔒  {name}")
                combined.setForeground(QBrush(QColor("#ff5555")))
            else:
                combined.setText(name)
                combined.setForeground(QBrush(QColor("#e0e0ff")))
            if desc:
                combined.setToolTip(desc)
            self.table.setItem(row, 2, combined)

            # CPU
            cpu_val = p.get("cpu", 0.0)
            cpu_item = QTableWidgetItem(f"{cpu_val:.1f}%")
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_item.setForeground(QBrush(QColor("#ffaa00" if cpu_val > 10 else "#6060a0")))
            self.table.setItem(row, 3, cpu_item)

            # RAM
            mem = p.get("mem_mb", 0)
            ram_item = QTableWidgetItem(f"{mem:.0f} MB")
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if mem > 500:
                ram_item.setForeground(QBrush(QColor("#ff5555")))
            elif mem > 200:
                ram_item.setForeground(QBrush(QColor("#ffaa00")))
            else:
                ram_item.setForeground(QBrush(QColor("#6060a0")))
            self.table.setItem(row, 4, ram_item)

            # Store pid in row
            self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, p["pid"])

        self.table.blockSignals(False)
        self._update_selection_count()

    def _get_checkbox(self, row: int):
        w = self.table.cellWidget(row, 0)
        if w:
            for child in w.children():
                if isinstance(child, QCheckBox):
                    return child
        return None

    def _select_all(self):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isEnabled():
                chk.setChecked(True)
        self.table.blockSignals(False)
        self._update_selection_count()

    def _deselect_all(self):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk:
                chk.setChecked(False)
        self.table.blockSignals(False)
        self._update_selection_count()

    def _on_cell_changed(self):
        self._update_selection_count()

    def _update_selection_count(self):
        count = 0
        ram_total = 0.0
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isChecked():
                count += 1
                if self.table.item(row, 4):
                    try:
                        ram_total += float(self.table.item(row, 4).text().replace(" MB", ""))
                    except Exception:
                        pass
        self._update_stat(self.sel_card, str(count))
        self._update_stat(self.ram_card, f"~{ram_total:.0f} MB")

    def _kill_selected(self):
        pids = []
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isChecked():
                num_item = self.table.item(row, 1)
                if num_item:
                    pid = num_item.data(Qt.ItemDataRole.UserRole)
                    if pid:
                        pids.append(pid)
        if not pids:
            self.status_lbl.setText("⚠️  No processes selected.")
            return

        dialog = ConfirmDialog(
            f"Kill {len(pids)} process(es)? This cannot be undone.",
            self
        )
        if dialog.exec() != 1:
            return

        self.kill_btn.setEnabled(False)
        self.status_lbl.setText(f"⚡ Killing {len(pids)} processes...")

        self._kworker = KillWorker(pids)
        self._kill_thread = QThread()
        self._kworker.moveToThread(self._kill_thread)
        self._kill_thread.started.connect(self._kworker.run)
        self._kworker.finished.connect(self._on_killed)
        self._kworker.finished.connect(self._kill_thread.quit)
        self._kill_thread.start()

    @pyqtSlot(list, int)
    def _on_killed(self, killed: list, fails: int):
        self.kill_btn.setEnabled(True)
        self._update_stat(self.killed_card, str(len(killed)))
        self.status_lbl.setText(
            f"✅  Killed {len(killed)} process(es)." +
            (f"  ⚠️ {fails} failed." if fails else "")
        )
        QTimer.singleShot(800, self._load)
