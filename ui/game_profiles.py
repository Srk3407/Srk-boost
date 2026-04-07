"""
SRK Boost - Game Profiles Page
Per-game tweak presets. Select a game → apply its optimized settings.
Create / edit / delete custom profiles.
"""

import json
import os
import logging
from typing import Dict, List, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QDialog, QLineEdit,
    QCheckBox, QGridLayout, QMessageBox, QSizePolicy,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.i18n import tr

logger = logging.getLogger(__name__)

PROFILES_FILE = os.path.join(os.path.expanduser("~"), ".srk_boost", "game_profiles.json")

# ── Built-in game presets ─────────────────────────────────────────────────────
DEFAULT_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "cs2",
        "name": "Counter-Strike 2",
        "icon": "🎯",
        "genre": "FPS · Competitive",
        "color": "#f59e0b",
        "description": "Maximum competitive edge. Low input lag, stable FPS, minimal stutters.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_mouse_acceleration",
            "disable_mpo",
            "set_timer_resolution",
            "disable_fullscreen_optimizations",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "set_cpu_responsiveness",
            "disable_network_throttling",
            "optimize_network_latency",
            "disable_cpu_core_parking",
        ],
        "builtin": True,
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "icon": "⚔️",
        "genre": "FPS · Tactical",
        "color": "#ef4444",
        "description": "Optimized for Riot anti-cheat compatibility + max performance.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_mouse_acceleration",
            "disable_mpo",
            "set_timer_resolution",
            "disable_fullscreen_optimizations",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "set_cpu_responsiveness",
            "disable_network_throttling",
            "disable_cpu_core_parking",
        ],
        "builtin": True,
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "icon": "🏗️",
        "genre": "Battle Royale",
        "color": "#8b5cf6",
        "description": "High FPS build-fights. Prioritizes GPU and CPU for rapid rendering.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_sysmain",
            "optimize_visual_effects",
            "set_gpu_max_performance",
            "disable_search_indexing",
            "disable_mpo",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "enable_hags",
            "set_cpu_responsiveness",
            "disable_cpu_core_parking",
        ],
        "builtin": True,
    },
    {
        "id": "gta5",
        "name": "GTA V / GTA Online",
        "icon": "🌆",
        "genre": "Open World",
        "color": "#10b981",
        "description": "Smooth open world. Reduces stutters and RAM pressure.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_sysmain",
            "disable_diagtrack",
            "optimize_visual_effects",
            "disable_search_indexing",
            "disable_network_throttling",
            "optimize_network_latency",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "clear_standby_memory",
            "disable_cpu_core_parking",
        ],
        "builtin": True,
    },
    {
        "id": "warzone",
        "name": "Call of Duty: Warzone",
        "icon": "🪖",
        "genre": "Battle Royale · FPS",
        "color": "#f97316",
        "description": "Large-map battle royale. Optimizes network + GPU for consistent frames.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_sysmain",
            "disable_mpo",
            "set_timer_resolution",
            "disable_network_throttling",
            "optimize_network_latency",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "set_cpu_responsiveness",
            "disable_cpu_core_parking",
            "disable_dpc_latency",
        ],
        "builtin": True,
    },
    {
        "id": "apex",
        "name": "Apex Legends",
        "icon": "🦾",
        "genre": "Battle Royale · FPS",
        "color": "#e11d48",
        "description": "Movement shooter. Prioritizes low input lag and stable frame timing.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_mouse_acceleration",
            "disable_mpo",
            "set_timer_resolution",
            "disable_fullscreen_optimizations",
            "set_win32_priority_separation",
            "set_gpu_priority",
            "set_cpu_responsiveness",
            "disable_cpu_core_parking",
        ],
        "builtin": True,
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "icon": "⛏️",
        "genre": "Sandbox",
        "color": "#84cc16",
        "description": "Java/Bedrock. Reduces JVM stutter by freeing RAM and background load.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
            "disable_sysmain",
            "disable_diagtrack",
            "disable_search_indexing",
            "clear_standby_memory",
            "set_win32_priority_separation",
            "set_cpu_responsiveness",
            "disable_dpc_latency",
        ],
        "builtin": True,
    },
    {
        "id": "custom",
        "name": "Custom Profile",
        "icon": "⚙️",
        "genre": "Custom",
        "color": "#6c63ff",
        "description": "Your own tweak combination. Edit to add or remove tweaks.",
        "tweaks": [
            "set_high_performance_power_plan",
            "disable_game_bar",
        ],
        "builtin": False,
    },
]

ALL_TWEAKS_META = [
    ("set_high_performance_power_plan", "High Performance Power Plan", "low"),
    ("disable_game_bar", "Disable Xbox Game Bar", "low"),
    ("disable_sysmain", "Disable SysMain (Superfetch)", "low"),
    ("disable_diagtrack", "Disable Telemetry (DiagTrack)", "low"),
    ("disable_mapbroker", "Disable MapsBroker", "low"),
    ("optimize_visual_effects", "Optimize Visual Effects", "low"),
    ("set_gpu_max_performance", "GPU Max Performance Mode", "medium"),
    ("disable_search_indexing", "Disable Search Indexing", "medium"),
    ("disable_network_throttling", "Disable Network Throttling", "low"),
    ("disable_mouse_acceleration", "Disable Mouse Acceleration", "low"),
    ("clear_standby_memory", "Clear Standby Memory", "low"),
    ("disable_cpu_core_parking", "Disable CPU Core Parking", "low"),
    ("disable_dpc_latency", "Reduce DPC Latency", "low"),
    ("optimize_network_latency", "Optimize Network Latency (TCP)", "low"),
    ("disable_mpo", "Disable MPO (Multi-Plane Overlay)", "medium"),
    ("set_timer_resolution", "Optimize Timer Resolution", "low"),
    ("disable_fullscreen_optimizations", "Disable Fullscreen Optimizations", "low"),
    ("set_win32_priority_separation", "Maximize CPU Foreground Priority", "low"),
    ("set_gpu_priority", "Set GPU Priority to Maximum", "low"),
    ("enable_hags", "Enable HAGS", "medium"),
    ("disable_windows_defender_gaming", "Pause Windows Defender", "medium"),
    ("set_cpu_responsiveness", "100% CPU for Games", "low"),
    ("disable_spectre_meltdown", "Disable CPU Security Mitigations", "high"),
]


def load_profiles() -> List[Dict]:
    """Load profiles from disk, merging with defaults."""
    try:
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved = {p["id"]: p for p in data}
            # Merge: defaults first, then saved custom ones on top
            merged = []
            for p in DEFAULT_PROFILES:
                if p["id"] in saved and not saved[p["id"]].get("builtin", True):
                    merged.append(saved[p["id"]])
                else:
                    merged.append(p)
            # Add any extra custom profiles
            default_ids = {p["id"] for p in DEFAULT_PROFILES}
            for pid, p in saved.items():
                if pid not in default_ids:
                    merged.append(p)
            return merged
    except Exception as e:
        logger.warning(f"Could not load profiles: {e}")
    return list(DEFAULT_PROFILES)


def save_profiles(profiles: List[Dict]):
    os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Could not save profiles: {e}")


# ── Profile Card ─────────────────────────────────────────────────────────────

class ProfileCard(QFrame):
    apply_requested = pyqtSignal(dict)   # profile dict
    edit_requested  = pyqtSignal(dict)
    delete_requested = pyqtSignal(str)   # profile id

    def __init__(self, profile: dict, parent=None):
        super().__init__(parent)
        self.profile = profile
        self._build(profile)

    def _build(self, p: dict):
        color = p.get("color", "#6c63ff")
        self.setObjectName("profileCard")
        self.setStyleSheet(f"""
            QFrame#profileCard {{
                background: rgba(12, 10, 22, 0.95);
                border: 1px solid rgba(108,99,255,0.15);
                border-radius: 16px;
            }}
            QFrame#profileCard:hover {{
                border: 1px solid {color};
                background: rgba(18, 14, 32, 0.98);
            }}
        """)
        self.setFixedHeight(175)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)

        # Top row: icon + name + genre
        top = QHBoxLayout()
        top.setSpacing(12)

        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {color}44, stop:1 {color}22);"
            f"border: 1px solid {color}55; border-radius: 12px;"
        )
        icon_lbl = QLabel(p.get("icon", "🎮"))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent; border: none;")
        icon_inner = QVBoxLayout(icon_frame)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.addWidget(icon_lbl)
        top.addWidget(icon_frame)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_lbl = QLabel(p.get("name", "Profile"))
        name_lbl.setStyleSheet(
            f"color: #ffffff; font-size: 15px; font-weight: 800; "
            "background: transparent; border: none;"
        )
        genre_lbl = QLabel(p.get("genre", ""))
        genre_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            "letter-spacing: 0.5px; background: transparent; border: none;"
        )
        name_col.addWidget(name_lbl)
        name_col.addWidget(genre_lbl)
        top.addLayout(name_col)
        top.addStretch()

        # Tweak count badge
        tweak_count = len(p.get("tweaks", []))
        count_lbl = QLabel(f"{tweak_count} tweaks")
        count_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            f"background: {color}22; border: 1px solid {color}44; "
            "border-radius: 8px; padding: 3px 10px;"
        )
        top.addWidget(count_lbl)
        layout.addLayout(top)

        # Description
        desc_lbl = QLabel(p.get("description", ""))
        desc_lbl.setStyleSheet(
            "color: #5a5880; font-size: 11px; background: transparent; border: none;"
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Tweaks list (first 4 shown)
        tweaks = p.get("tweaks", [])
        if tweaks:
            TWEAK_DISPLAY = {
                "set_high_performance_power_plan": "⚡ High Performance Power",
                "disable_game_bar": "🎮 Disable Game Bar",
                "disable_sysmain": "💾 Disable Superfetch",
                "disable_diagtrack": "📡 Disable Telemetry",
                "disable_mouse_acceleration": "🖱 No Mouse Accel",
                "disable_mpo": "🖥 Disable MPO",
                "set_timer_resolution": "⏱ Timer Resolution",
                "disable_fullscreen_optimizations": "🪟 Disable FSO",
                "set_win32_priority_separation": "🧠 CPU Foreground Priority",
                "set_gpu_priority": "🎯 GPU Priority Max",
                "set_cpu_responsiveness": "💯 100% CPU for Games",
                "enable_hags": "⚙ Enable HAGS",
                "disable_network_throttling": "🌐 No Net Throttling",
                "optimize_network_latency": "📶 TCP Latency Opt",
                "disable_cpu_core_parking": "🔓 No Core Parking",
                "disable_dpc_latency": "📉 Reduce DPC Latency",
                "disable_search_indexing": "🔍 No Search Index",
                "clear_standby_memory": "🧹 Clear RAM",
                "disable_windows_defender_gaming": "🛡 Pause Defender",
                "set_gpu_max_performance": "🖥 GPU Max Mode",
                "optimize_visual_effects": "✨ Optimize Visuals",
                "disable_mapbroker": "🗺 Disable Maps",
            }
            tweak_row = QHBoxLayout()
            tweak_row.setSpacing(4)
            show = tweaks[:4]
            for t in show:
                label = TWEAK_DISPLAY.get(t, t.replace('_', ' ').title())
                t_lbl = QLabel(label)
                t_lbl.setStyleSheet(
                    f"color: {color}; font-size: 9px; background: {color}18; "
                    f"border: 1px solid {color}30; border-radius: 4px; padding: 2px 5px;"
                )
                tweak_row.addWidget(t_lbl)
            if len(tweaks) > 4:
                more_lbl = QLabel(f"+{len(tweaks)-4} more")
                more_lbl.setStyleSheet(
                    "color: #4a4870; font-size: 9px; background: transparent; border: none;"
                )
                tweak_row.addWidget(more_lbl)
            tweak_row.addStretch()
            layout.addLayout(tweak_row)
        else:
            layout.addStretch()

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        apply_btn = QPushButton("▶  Apply Profile")
        apply_btn.setFixedHeight(34)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {color}, stop:1 {color}cc);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {color}ee, stop:1 {color});
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.profile))
        btn_row.addWidget(apply_btn, 1)

        # Rich tooltip with all tweaks
        TWEAK_DISPLAY = {
            "set_high_performance_power_plan": "⚡ High Performance Power Plan",
            "disable_game_bar": "🎮 Disable Xbox Game Bar",
            "disable_sysmain": "💾 Disable SysMain (Superfetch)",
            "disable_diagtrack": "📡 Disable Telemetry",
            "disable_mapbroker": "🗺 Disable MapsBroker",
            "optimize_visual_effects": "✨ Optimize Visual Effects",
            "set_gpu_max_performance": "🖥 GPU Max Performance",
            "disable_search_indexing": "🔍 Disable Search Indexing",
            "disable_network_throttling": "🌐 Disable Network Throttling",
            "disable_mouse_acceleration": "🖱 No Mouse Acceleration",
            "clear_standby_memory": "🧹 Clear Standby Memory",
            "disable_cpu_core_parking": "🔓 Disable CPU Core Parking",
            "disable_dpc_latency": "📉 Reduce DPC Latency",
            "optimize_network_latency": "📶 Optimize Network Latency",
            "disable_mpo": "🖥 Disable MPO (fixes stutter)",
            "set_timer_resolution": "⏱ Optimize Timer Resolution",
            "disable_fullscreen_optimizations": "🪟 Disable Fullscreen Optim.",
            "set_win32_priority_separation": "🧠 CPU Foreground Priority",
            "set_gpu_priority": "🎯 GPU Priority Maximum",
            "enable_hags": "⚙ Hardware GPU Scheduling",
            "disable_windows_defender_gaming": "🛡 Pause Windows Defender",
            "set_cpu_responsiveness": "💯 100% CPU for Games",
            "disable_spectre_meltdown": "⚠ Disable CPU Mitigations",
        }
        tweaks = p.get("tweaks", [])
        tip_lines = [f"<b>{p.get('name','')}</b> — {p.get('genre','')}",
                     f"<i>{p.get('description','')}</i>", ""]
        for t in tweaks:
            tip_lines.append(TWEAK_DISPLAY.get(t, t.replace('_',' ').title()))
        self.setToolTip("\n".join(tip_lines))

        if not p.get("builtin", True):
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(34, 34)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(108,99,255,0.12);
                    color: #8b83ff;
                    border: 1px solid rgba(108,99,255,0.3);
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover { background: rgba(108,99,255,0.22); }
            """)
            edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.profile))
            btn_row.addWidget(edit_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(34, 34)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,68,68,0.1);
                    color: #ff5555;
                    border: 1px solid rgba(255,68,68,0.25);
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover { background: rgba(255,68,68,0.2); }
            """)
            del_btn.clicked.connect(lambda: self.delete_requested.emit(self.profile["id"]))
            btn_row.addWidget(del_btn)

        layout.addLayout(btn_row)


# ── Profile Edit Dialog ───────────────────────────────────────────────────────

class ProfileEditDialog(QDialog):
    def __init__(self, profile: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Profile" if profile else "New Profile")
        self.setMinimumSize(600, 600)
        self.setStyleSheet("""
            QDialog {
                background: #0e0c1e;
                border: 1px solid rgba(108,99,255,0.3);
                border-radius: 16px;
            }
        """)
        self._profile = profile or {
            "id": f"custom_{int(__import__('time').time())}",
            "name": "My Profile",
            "icon": "🎮",
            "genre": "Custom",
            "color": "#6c63ff",
            "description": "",
            "tweaks": [],
            "builtin": False,
        }
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Profile Settings")
        title.setStyleSheet(
            "color: #e0e0ff; font-size: 18px; font-weight: 800; background: transparent;"
        )
        layout.addWidget(title)

        # Name
        layout.addWidget(self._field_label("Profile Name"))
        self.name_edit = QLineEdit(self._profile.get("name", ""))
        self.name_edit.setPlaceholderText("e.g. My FPS Game")
        layout.addWidget(self.name_edit)

        # Icon + Genre row
        row = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self._field_label("Icon (emoji)"))
        self.icon_edit = QLineEdit(self._profile.get("icon", "🎮"))
        self.icon_edit.setFixedWidth(80)
        col1.addWidget(self.icon_edit)
        row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.addWidget(self._field_label("Genre"))
        self.genre_edit = QLineEdit(self._profile.get("genre", ""))
        self.genre_edit.setPlaceholderText("e.g. FPS · Competitive")
        col2.addWidget(self.genre_edit)
        row.addLayout(col2, 1)
        layout.addLayout(row)

        # Description
        layout.addWidget(self._field_label("Description"))
        self.desc_edit = QLineEdit(self._profile.get("description", ""))
        self.desc_edit.setPlaceholderText("Short description of this profile...")
        layout.addWidget(self.desc_edit)

        # Tweaks
        layout.addWidget(self._field_label("Select Tweaks"))
        tweaks_scroll = QScrollArea()
        tweaks_scroll.setWidgetResizable(True)
        tweaks_scroll.setMaximumHeight(260)
        tweaks_scroll.setStyleSheet(
            "QScrollArea { border: 1px solid rgba(108,99,255,0.2); border-radius: 10px; }"
        )

        tweaks_widget = QWidget()
        tweaks_layout = QVBoxLayout(tweaks_widget)
        tweaks_layout.setContentsMargins(12, 10, 12, 10)
        tweaks_layout.setSpacing(6)

        active_tweaks = set(self._profile.get("tweaks", []))
        self._checkboxes: Dict[str, QCheckBox] = {}

        RISK_COLORS = {"low": "#00e87a", "medium": "#ffaa00", "high": "#ff5555"}

        for func_name, display_name, risk in ALL_TWEAKS_META:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(4, 2, 4, 2)
            row_l.setSpacing(10)

            cb = QCheckBox()
            cb.setChecked(func_name in active_tweaks)
            self._checkboxes[func_name] = cb
            row_l.addWidget(cb)

            lbl = QLabel(display_name)
            lbl.setStyleSheet("color: #c0b8ff; font-size: 12px; background: transparent;")
            row_l.addWidget(lbl)
            row_l.addStretch()

            risk_lbl = QLabel(risk.upper())
            c = RISK_COLORS.get(risk, "#6c63ff")
            risk_lbl.setStyleSheet(
                f"color: {c}; font-size: 9px; font-weight: 700; "
                f"background: {c}22; border: 1px solid {c}44; "
                "border-radius: 4px; padding: 2px 7px;"
            )
            row_l.addWidget(risk_lbl)
            tweaks_layout.addWidget(row_w)

        tweaks_scroll.setWidget(tweaks_widget)
        layout.addWidget(tweaks_scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary_btn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾  Save Profile")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: rgba(108,99,255,0.7); font-size: 10px; font-weight: 700; "
            "letter-spacing: 1px; background: transparent;"
        )
        return lbl

    def get_profile(self) -> dict:
        selected_tweaks = [fn for fn, cb in self._checkboxes.items() if cb.isChecked()]
        return {
            **self._profile,
            "name": self.name_edit.text().strip() or self._profile["name"],
            "icon": self.icon_edit.text().strip() or "🎮",
            "genre": self.genre_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "tweaks": selected_tweaks,
            "builtin": False,
        }


# ── Apply Worker ─────────────────────────────────────────────────────────────

from PyQt6.QtCore import QThread, pyqtSignal as Signal

class ProfileApplyWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str, int, int)   # ok, msg, applied, failed

    def __init__(self, profile: dict):
        super().__init__()
        self.profile = profile

    def run(self):
        tweaks = self.profile.get("tweaks", [])
        total = len(tweaks)
        if total == 0:
            self.finished.emit(False, "No tweaks in this profile.", 0, 0)
            return

        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.create_restore_point(f"Before profile: {self.profile['name']}")
            self.progress.emit(5, "Restore point created...")

            import core.optimizer as opt
            applied = 0
            failed = 0
            for i, func_name in enumerate(tweaks):
                pct = 5 + int((i / total) * 90)
                self.progress.emit(pct, f"Applying: {func_name}...")
                fn = getattr(opt, func_name, None)
                if fn:
                    try:
                        ok, _ = fn()
                        if ok:
                            applied += 1
                        else:
                            failed += 1
                    except Exception:
                        failed += 1

            self.progress.emit(100, "Done!")
            self.finished.emit(True, f"Profile applied!", applied, failed)
        except Exception as e:
            self.finished.emit(False, str(e), 0, 0)


# ── Main Page ─────────────────────────────────────────────────────────────────

class GameProfilesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._profiles = load_profiles()
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("🎮  Game Profiles")
        title.setStyleSheet(
            "color: #ffffff; font-size: 24px; font-weight: 900; background: transparent;"
        )
        sub = QLabel("One-click optimization presets for popular games")
        sub.setStyleSheet("color: #3a3a6a; font-size: 12px; background: transparent;")
        left.addWidget(title)
        left.addWidget(sub)
        header.addLayout(left)
        header.addStretch()

        new_btn = QPushButton("＋  New Profile")
        new_btn.setObjectName("primary_btn")
        new_btn.setFixedHeight(38)
        new_btn.clicked.connect(self._create_profile)
        header.addWidget(new_btn)
        layout.addLayout(header)

        # Status bar (hidden until boost runs)
        self.status_frame = QFrame()
        self.status_frame.setObjectName("card")
        self.status_frame.setVisible(False)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(20, 14, 20, 14)
        status_layout.setSpacing(8)

        self.status_lbl = QLabel("Applying profile...")
        self.status_lbl.setStyleSheet(
            "color: #e0e0ff; font-size: 13px; font-weight: 600; background: transparent;"
        )
        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        status_layout.addWidget(self.status_lbl)
        status_layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_frame)

        # Cards grid
        self.cards_frame = QWidget()
        self.cards_grid = QGridLayout(self.cards_frame)
        self.cards_grid.setSpacing(16)
        self.cards_grid.setColumnStretch(0, 1)
        self.cards_grid.setColumnStretch(1, 1)
        self.cards_grid.setColumnStretch(2, 1)
        layout.addWidget(self.cards_frame)

        self._rebuild_cards()

        layout.addStretch()

    def _rebuild_cards(self):
        # Clear existing
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, profile in enumerate(self._profiles):
            card = ProfileCard(profile)
            card.apply_requested.connect(self._apply_profile)
            card.edit_requested.connect(self._edit_profile)
            card.delete_requested.connect(self._delete_profile)
            row, col = divmod(i, 3)
            self.cards_grid.addWidget(card, row, col)

    def _apply_profile(self, profile: dict):
        if self._worker and self._worker.isRunning():
            return

        self.status_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText(f"Applying: {profile['name']}...")
        self.status_lbl.setStyleSheet(
            "color: #e0e0ff; font-size: 13px; font-weight: 600; background: transparent;"
        )

        self._worker = ProfileApplyWorker(profile)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, value: int, msg: str):
        self.progress_bar.setValue(value)
        self.status_lbl.setText(msg)

    def _on_finished(self, ok: bool, msg: str, applied: int, failed: int):
        if ok:
            self.status_lbl.setText(
                f"✅  Profile applied — {applied} tweaks succeeded, {failed} skipped"
            )
            self.status_lbl.setStyleSheet(
                "color: #00e87a; font-size: 13px; font-weight: 600; background: transparent;"
            )
        else:
            self.status_lbl.setText(f"❌  {msg}")
            self.status_lbl.setStyleSheet(
                "color: #ff5555; font-size: 13px; font-weight: 600; background: transparent;"
            )

    def _create_profile(self):
        dlg = ProfileEditDialog(parent=self)
        if dlg.exec():
            new_p = dlg.get_profile()
            self._profiles.append(new_p)
            save_profiles(self._profiles)
            self._rebuild_cards()

    def _edit_profile(self, profile: dict):
        dlg = ProfileEditDialog(profile=profile, parent=self)
        if dlg.exec():
            updated = dlg.get_profile()
            for i, p in enumerate(self._profiles):
                if p["id"] == updated["id"]:
                    self._profiles[i] = updated
                    break
            save_profiles(self._profiles)
            self._rebuild_cards()

    def _delete_profile(self, profile_id: str):
        self._profiles = [p for p in self._profiles if p["id"] != profile_id]
        save_profiles(self._profiles)
        self._rebuild_cards()
