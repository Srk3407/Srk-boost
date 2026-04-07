"""
SRK Boost - Backup & Restore Page
Create and manage system restore points + app state backups
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os, json, subprocess, platform
from datetime import datetime
from core.i18n import tr

class CreateRestoreWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, label):
        super().__init__()
        self.label = label

    def run(self):
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            self.progress.emit("Creating app restore point...")
            rm.create_restore_point(self.label)

            # Also try Windows System Restore (requires admin)
            if platform.system() == "Windows":
                self.progress.emit("Creating Windows System Restore point...")
                try:
                    subprocess.run([
                        "powershell", "-Command",
                        f'Checkpoint-Computer -Description "SRK Boost: {self.label}" -RestorePointType MODIFY_SETTINGS'
                    ], timeout=30, capture_output=True, encoding="utf-8", errors="replace")
                    self.progress.emit("Windows System Restore point created!")
                except:
                    self.progress.emit("App restore point created (Windows SR skipped - needs admin)")

            self.finished.emit(True, f"Restore point '{self.label}' created successfully!")
        except Exception as e:
            self.finished.emit(False, str(e))


class BackupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()
        self._load_restore_points()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Backup & Restore")
        title.setStyleSheet("color: #e0e0ff; font-size: 22px; font-weight: 900;")
        layout.addWidget(title)

        subtitle = QLabel("Create restore points and restore your system to a previous state")
        subtitle.setStyleSheet("color: #6060a0; font-size: 13px;")
        layout.addWidget(subtitle)

        # Create backup card
        create_card = self._make_card()
        create_layout = QVBoxLayout(create_card)

        card_title = QLabel("Create New Restore Point")
        card_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        create_layout.addWidget(card_title)

        card_desc = QLabel("Save current system state before making changes. You can restore to this point if something goes wrong.")
        card_desc.setStyleSheet("color: #6060a0; font-size: 12px;")
        card_desc.setWordWrap(True)
        create_layout.addWidget(card_desc)

        btn_row = QHBoxLayout()

        self.quick_btn = QPushButton("Quick Backup")
        self.quick_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #8b5cf6);
                color: white; border: none; border-radius: 8px;
                padding: 10px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c73ff,stop:1 #9b6cf6); }
        """)
        self.quick_btn.clicked.connect(self._quick_backup)
        btn_row.addWidget(self.quick_btn)

        self.named_btn = QPushButton("Named Backup...")
        self.named_btn.setStyleSheet("""
            QPushButton {
                background: #1e1e2e; color: #e0e0ff;
                border: 1px solid #2a2a4a; border-radius: 8px;
                padding: 10px 24px; font-size: 13px;
            }
            QPushButton:hover { border-color: #6c63ff; }
        """)
        self.named_btn.clicked.connect(self._named_backup)
        btn_row.addWidget(self.named_btn)
        btn_row.addStretch()
        create_layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #1e1e2e; border-radius: 6px; height: 6px; border: none; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #00d4ff); border-radius: 6px; }
        """)
        create_layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        self.status_lbl.setVisible(False)
        create_layout.addWidget(self.status_lbl)

        layout.addWidget(create_card)

        # Restore points list
        list_card = self._make_card()
        list_layout = QVBoxLayout(list_card)

        list_header = QHBoxLayout()
        list_title = QLabel("Saved Restore Points")
        list_title.setStyleSheet("color: #e0e0ff; font-size: 15px; font-weight: bold;")
        list_header.addWidget(list_title)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background: #1e1e2e; color: #6060a0; border: 1px solid #2a2a4a; border-radius: 6px; padding: 6px 14px; font-size: 11px;")
        refresh_btn.clicked.connect(self._load_restore_points)
        list_header.addWidget(refresh_btn)
        list_layout.addLayout(list_header)

        self.restore_list = QListWidget()
        self.restore_list.setStyleSheet("""
            QListWidget { background: #0a0a0f; border: 1px solid #2a1a4a; border-radius: 8px; color: #e0e0ff; }
            QListWidget::item { padding: 10px 14px; border-bottom: 1px solid #1e1e2e; }
            QListWidget::item:selected { background: #2a1a4a; }
            QListWidget::item:hover { background: #1a1a2e; }
        """)
        self.restore_list.setMinimumHeight(200)
        list_layout.addWidget(self.restore_list)

        action_row = QHBoxLayout()

        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00c853,stop:1 #00a040);
                color: white; border: none; border-radius: 8px;
                padding: 10px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        self.restore_btn.clicked.connect(self._restore_selected)
        action_row.addWidget(self.restore_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #2a0a0a; color: #ff4444;
                border: 1px solid #ff4444; border-radius: 8px;
                padding: 10px 24px; font-size: 13px;
            }
            QPushButton:hover { background: #3a0a0a; }
        """)
        self.delete_btn.clicked.connect(self._delete_selected)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch()
        list_layout.addLayout(action_row)

        layout.addWidget(list_card)
        layout.addStretch()

    def _make_card(self):
        card = QFrame()
        card.setStyleSheet("background: #12121a; border: 1px solid #2a1a4a; border-radius: 14px; padding: 4px;")
        return card

    def _quick_backup(self):
        label = f"Manual Backup - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        self._create_backup(label)

    def _named_backup(self):
        text, ok = QInputDialog.getText(self, "Name Backup", "Enter a name for this restore point:")
        if ok and text.strip():
            self._create_backup(text.strip())

    def _create_backup(self, label):
        self.quick_btn.setEnabled(False)
        self.named_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setVisible(True)
        self.status_lbl.setText("Creating restore point...")
        self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")

        self._worker = CreateRestoreWorker(label)
        self._worker.progress.connect(lambda m: self.status_lbl.setText(m))
        self._worker.finished.connect(self._on_backup_done)
        self._worker.start()

    def _on_backup_done(self, success, msg):
        self.quick_btn.setEnabled(True)
        self.named_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if success:
            self.status_lbl.setText("✓ " + msg)
            self.status_lbl.setStyleSheet("color: #00ff88; font-size: 12px;")
            self._load_restore_points()
        else:
            self.status_lbl.setText("Error: " + msg)
            self.status_lbl.setStyleSheet("color: #ff4444; font-size: 12px;")

    def _load_restore_points(self):
        self.restore_list.clear()
        restore_dir = os.path.join(os.path.expanduser("~"), ".srk_boost", "restore_points")
        if not os.path.exists(restore_dir):
            self.restore_list.addItem("No restore points found. Create one above.")
            return

        files = sorted([f for f in os.listdir(restore_dir) if f.endswith(".json")], reverse=True)
        if not files:
            self.restore_list.addItem("No restore points found. Create one above.")
            return

        for f in files:
            path = os.path.join(restore_dir, f)
            try:
                with open(path) as fp:
                    data = json.load(fp)
                label = data.get("label", f)
                ts = data.get("timestamp", "")[:19].replace("T", " ")
                item = QListWidgetItem(f"  {ts}  —  {label}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.restore_list.addItem(item)
            except:
                item = QListWidgetItem(f"  {f}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.restore_list.addItem(item)

    def _restore_selected(self):
        item = self.restore_list.currentItem()
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(self, "Warning", "Please select a restore point.")
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Restore",
            f"Restore system to:\n{item.text().strip()}\n\nThis will revert FPS tweaks and optimizations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.restore import RestoreManager
                rm = RestoreManager()
                rm.restore_from_file(path)
                QMessageBox.information(self, "Success", "Restore completed successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Restore failed: {e}")

    def _delete_selected(self):
        item = self.restore_list.currentItem()
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this restore point?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(item.data(Qt.ItemDataRole.UserRole))
                self._load_restore_points()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
