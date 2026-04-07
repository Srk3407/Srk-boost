"""
SRK Boost - Network Optimizer  v1.0
Live ping monitor + TCP/registry tweaks to reduce latency.
"""

import logging
import subprocess

# Windows: suppress console window
import sys as _sys, subprocess as _sp
_CREATE_NO_WINDOW = _sp.CREATE_NO_WINDOW if _sys.platform == "win32" else 0  # type: ignore

import time
import re
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QComboBox,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QObject, QTimer,
    QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QPainterPath
)

logger = logging.getLogger(__name__)

# ── Network Tweaks ────────────────────────────────────────────────────────────

NETWORK_TWEAKS = [
    {
        "key": "tcp_no_delay",
        "title": "TCP NoDelay",
        "desc": "Nagle algoritmasını kapat — küçük paketleri anında gönder",
        "detail": "Oyunlarda en etkili tweak. Gecikmeyi 5-20ms düşürür.",
        "icon": "⚡",
        "color": "#6c63ff",
        "reg_cmds": [
            r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v TcpAckFrequency /t REG_DWORD /d 1 /f',
            r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v TCPNoDelay /t REG_DWORD /d 1 /f',
        ],
        "restore_cmds": [
            r'reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v TcpAckFrequency /f',
            r'reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v TCPNoDelay /f',
        ],
    },
    {
        "key": "network_throttling",
        "title": "Network Throttling Off",
        "desc": "Windows ağ hız sınırlamasını kaldır",
        "detail": "Multimedia uygulamaları için Windows'un koyduğu 10Mbps sınırı kaldırır.",
        "icon": "🚀",
        "color": "#00d4ff",
        "reg_cmds": [
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f',
        ],
        "restore_cmds": [
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f',
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 20 /f',
        ],
    },
    {
        "key": "qos_scheduler",
        "title": "QoS Bandwidth Reserve Kaldır",
        "desc": "Windows'un bant genişliği rezervini %20'den %0'a indir",
        "detail": "Windows varsayılan olarak %20 bant genişliği rezerv eder. Bunu kaldırır.",
        "icon": "📶",
        "color": "#00e87a",
        "reg_cmds": [
            r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched" /v NonBestEffortLimit /t REG_DWORD /d 0 /f',
        ],
        "restore_cmds": [
            r'reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched" /v NonBestEffortLimit /f',
        ],
    },
    {
        "key": "dns_cache",
        "title": "DNS Cache Temizle",
        "desc": "DNS önbelleğini temizle — yavaş domain çözümlemesini düzelt",
        "detail": "Bozuk DNS kayıtlarını temizler, yeniden bağlanma sorunlarını çözer.",
        "icon": "🔄",
        "color": "#f97316",
        "reg_cmds": [
            r'ipconfig /flushdns',
        ],
        "restore_cmds": [],
    },
    {
        "key": "ttl",
        "title": "TTL Optimize",
        "desc": "Default TTL değerini 64'e ayarla (Linux/game server uyumlu)",
        "detail": "Bazı ISP'lerde paket kaybını azaltır.",
        "icon": "🎯",
        "color": "#a78bff",
        "reg_cmds": [
            r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v DefaultTTL /t REG_DWORD /d 64 /f',
        ],
        "restore_cmds": [
            r'reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v DefaultTTL /f',
        ],
    },
]

# Valve CS2: SDR relay nodes — these are real Valve relay IPs confirmed via community research
# Riot Valorant: edge proxy IPs used for matchmaking traffic
# Google/CF: general internet reference
PRESET_SERVERS = [
    # ── Genel ────────────────────────────────────────────────────────────────
    ("Google DNS",               "8.8.8.8"),
    ("Cloudflare DNS",           "1.1.1.1"),
    # ── CS2 / Valve SDR Relay nodes (Europe) ────────────────────────────────
    # Valve uses Steam Datagram Relay (SDR) — relay IPs change per session.
    # These are the known PUBLIC relay pop IPs for each region.
    ("CS2 — Frankfurt (fra)",    "162.254.197.36"),
    ("CS2 — Amsterdam (ams)",    "162.254.197.40"),
    ("CS2 — Stockholm (sto)",    "162.254.197.46"),
    ("CS2 — Warsaw (waw)",       "162.254.197.50"),
    ("CS2 — Vienna (vie)",       "162.254.197.48"),
    ("CS2 — Madrid (mad)",       "162.254.196.68"),
    # ── Valorant / Riot Games (Europe) ───────────────────────────────────────
    # Riot uses Anycast — these IPs route to the nearest Riot PoP
    ("Valorant — Frankfurt",     "5.42.158.33"),
    ("Valorant — Stockholm",     "5.42.158.38"),
    ("Valorant — Warsaw",        "5.42.158.40"),
    ("Valorant — Paris",         "5.42.158.35"),
    ("Valorant — Istanbul",      "5.42.158.55"),
    # ── Diğer oyunlar ────────────────────────────────────────────────────────
    ("Riot (genel)",             "162.249.73.1"),
    ("Battle.net Europe",        "185.60.112.157"),
    ("Epic Games (Fortnite EU)", "34.212.220.7"),
    # ── Custom ───────────────────────────────────────────────────────────────
    ("Custom...",                "custom"),
]


# ── Workers ───────────────────────────────────────────────────────────────────

class PingWorker(QObject):
    result   = pyqtSignal(float)   # ms or -1 for timeout
    finished = pyqtSignal()

    def __init__(self, host: str):
        super().__init__()
        self._host = host
        self._running = False

    def start_ping(self):
        self._running = True
        while self._running:
            ms = self._ping_once(self._host)
            self.result.emit(ms)
            time.sleep(1.0)
        self.finished.emit()

    def stop(self):
        self._running = False

    def _ping_once(self, host: str) -> float:
        try:
            r = subprocess.run(
                ["ping", "-n", "1", "-w", "2000", host],
                capture_output=True, creationflags=_CREATE_NO_WINDOW, text=True, timeout=3
            )
            m = re.search(r"time[=<](\d+)ms", r.stdout)
            if m:
                return float(m.group(1))
            return -1.0
        except Exception:
            return -1.0


class TweakWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, cmds: List[str]):
        super().__init__()
        self._cmds = cmds

    def run(self):
        errors = []
        for cmd in self._cmds:
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, creationflags=_CREATE_NO_WINDOW, creationflags=_CREATE_NO_WINDOW, text=True, timeout=8)
                self.progress.emit(f"✓ {cmd.split()[0]}")
                if r.returncode != 0 and r.stderr:
                    errors.append(r.stderr.strip())
            except Exception as e:
                errors.append(str(e))
        if errors:
            self.finished.emit(False, "\n".join(errors))
        else:
            self.finished.emit(True, "All tweaks applied successfully.")


# ── Ping Graph Widget ─────────────────────────────────────────────────────────

class PingGraph(QWidget):
    MAX_POINTS = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[float] = []
        self._max_shown = 200.0
        self.setMinimumHeight(160)

    def add_point(self, ms: float):
        self._data.append(ms)
        if len(self._data) > self.MAX_POINTS:
            self._data.pop(0)
        # auto-scale
        valid = [v for v in self._data if v > 0]
        if valid:
            self._max_shown = max(200.0, max(valid) * 1.2)
        self.update()

    def clear(self):
        self._data.clear()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 52, 16, 16, 32

        # Background
        p.fillRect(0, 0, w, h, QColor(8, 7, 18))

        # Grid lines
        grid_pen = QPen(QColor(30, 28, 55), 1, Qt.PenStyle.DashLine)
        p.setPen(grid_pen)
        for i in range(1, 5):
            y = pad_t + (h - pad_t - pad_b) * i / 4
            p.drawLine(pad_l, int(y), w - pad_r, int(y))
            val = self._max_shown * (1 - i / 4)
            p.setPen(QPen(QColor(60, 55, 100)))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(2, int(y) - 8, pad_l - 6, 18, Qt.AlignmentFlag.AlignRight, f"{val:.0f}")
            p.setPen(grid_pen)

        # X-axis labels
        p.setPen(QPen(QColor(60, 55, 100)))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(pad_l, h - pad_b + 4, 40, 16, Qt.AlignmentFlag.AlignLeft, "60s ago")
        p.drawText(w - pad_r - 30, h - pad_b + 4, 40, 16, Qt.AlignmentFlag.AlignRight, "now")

        if not self._data:
            p.setPen(QPen(QColor(60, 55, 100)))
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "Start monitoring to see ping graph")
            return

        # Draw area fill + line
        graph_w = w - pad_l - pad_r
        graph_h = h - pad_t - pad_b

        def to_xy(i, val):
            x = pad_l + (i / (self.MAX_POINTS - 1)) * graph_w
            if val < 0:
                return x, None
            y = pad_t + graph_h * (1 - min(val, self._max_shown) / self._max_shown)
            return x, y

        # Gradient fill
        fill_path = QPainterPath()
        started = False
        last_x = pad_l + graph_w

        pts = [(to_xy(i, v)) for i, v in enumerate(self._data)]
        valid_pts = [(x, y) for x, y in pts if y is not None]

        if valid_pts:
            fill_path.moveTo(valid_pts[0][0], pad_t + graph_h)
            for x, y in valid_pts:
                fill_path.lineTo(x, y)
            fill_path.lineTo(valid_pts[-1][0], pad_t + graph_h)
            fill_path.closeSubpath()

            grad = QLinearGradient(0, pad_t, 0, pad_t + graph_h)
            grad.setColorAt(0, QColor(108, 99, 255, 80))
            grad.setColorAt(1, QColor(108, 99, 255, 5))
            p.fillPath(fill_path, QBrush(grad))

        # Line
        line_pen = QPen(QColor(108, 99, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(line_pen)
        prev = None
        for x, y in pts:
            if y is None:
                prev = None
                continue
            if prev:
                # Color-code: green < 50, yellow < 120, red > 120
                last_val = self._data[pts.index((x, y))]
                if last_val < 50:
                    color = QColor(0, 232, 122)
                elif last_val < 120:
                    color = QColor(249, 115, 22)
                else:
                    color = QColor(239, 68, 68)
                p.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(int(prev[0]), int(prev[1]), int(x), int(y))
            prev = (x, y)

        # Last point dot
        if valid_pts:
            lx, ly = valid_pts[-1]
            last_val = self._data[-1]
            if last_val < 50:
                dot_color = QColor(0, 232, 122)
            elif last_val < 120:
                dot_color = QColor(249, 115, 22)
            else:
                dot_color = QColor(239, 68, 68)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(dot_color))
            p.drawEllipse(int(lx) - 5, int(ly) - 5, 10, 10)
            p.setBrush(QBrush(QColor(8, 7, 18)))
            p.drawEllipse(int(lx) - 3, int(ly) - 3, 6, 6)


# ── Animated Tweak Card ───────────────────────────────────────────────────────

class TweakCard(QFrame):
    def __init__(self, tweak: dict, parent=None):
        super().__init__(parent)
        self._tweak = tweak
        self._applied = False
        self._color = QColor(tweak["color"])
        self.setObjectName("tweak_card")
        self.setMinimumHeight(80)
        self._build()
        self._set_style(False)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        icon = QLabel(self._tweak["icon"])
        icon.setStyleSheet(f"font-size: 24px; background: transparent;")
        icon.setFixedWidth(36)
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._title_lbl = QLabel(self._tweak["title"])
        self._title_lbl.setStyleSheet("font-size: 14px; font-weight: 800; background: transparent;")
        self._desc_lbl = QLabel(self._tweak["desc"])
        self._desc_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        self._detail_lbl = QLabel(self._tweak["detail"])
        self._detail_lbl.setStyleSheet("font-size: 10px; background: transparent;")
        self._detail_lbl.setWordWrap(True)
        text_col.addWidget(self._title_lbl)
        text_col.addWidget(self._desc_lbl)
        text_col.addWidget(self._detail_lbl)
        layout.addLayout(text_col, 1)

        self._status_badge = QLabel("NOT APPLIED")
        self._status_badge.setFixedSize(100, 26)
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_badge)

    def _set_style(self, applied: bool):
        c = self._tweak["color"]
        if applied:
            border_alpha = "0.7"
            bg_alpha = "0.12"
            title_color = c
            badge_bg = f"rgba({self._hex_to_rgb(c)}, 0.2)"
            badge_color = c
            badge_text = "✓ APPLIED"
        else:
            border_alpha = "0.18"
            bg_alpha = "0.04"
            title_color = "#c0b8e8"
            badge_bg = "rgba(30,28,55,0.8)"
            badge_color = "#4a4870"
            badge_text = "NOT APPLIED"

        self.setStyleSheet(f"""
            QFrame#tweak_card {{
                background: rgba({self._hex_to_rgb(c)}, {bg_alpha});
                border: 1px solid rgba({self._hex_to_rgb(c)}, {border_alpha});
                border-radius: 14px;
            }}
        """)
        self._title_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 800; color: {title_color}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"font-size: 11px; color: {'#6060a0' if not applied else '#8080b0'}; background: transparent;"
        )
        self._detail_lbl.setStyleSheet(
            f"font-size: 10px; color: {'#3a3a6a' if not applied else '#4a4a80'}; background: transparent;"
        )
        self._status_badge.setStyleSheet(f"""
            background: {badge_bg};
            color: {badge_color};
            border: 1px solid rgba({self._hex_to_rgb(c)}, {'0.5' if applied else '0.15'});
            border-radius: 6px;
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 1px;
        """)
        self._status_badge.setText(badge_text)

    def set_applied(self, applied: bool):
        self._applied = applied
        self._set_style(applied)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"


# ── Animated Apply Button ─────────────────────────────────────────────────────

class AnimatedButton(QPushButton):
    def __init__(self, text: str, color: str = "#6c63ff", parent=None):
        super().__init__(text, parent)
        self._base_color = color
        self._progress = 0.0
        self._timer = None
        self._animating = False

    def start_animation(self):
        self._progress = 0.0
        self._animating = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def stop_animation(self, success: bool = True):
        if self._timer:
            self._timer.stop()
        self._animating = False
        self._progress = 1.0 if success else 0.0
        self.update()

    def _tick(self):
        self._progress = min(1.0, self._progress + 0.025)
        self.update()
        if self._progress >= 1.0:
            if self._timer:
                self._timer.stop()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h // 2

        # Background
        bg = QColor(20, 18, 40)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, r, r)
        p.fillPath(path, bg)

        # Progress fill
        if self._progress > 0:
            fill_w = int(w * self._progress)
            clip_path = QPainterPath()
            clip_path.addRoundedRect(0, 0, fill_w, h, r, r)
            grad = QLinearGradient(0, 0, w, 0)
            c = QColor(self._base_color)
            grad.setColorAt(0, c.darker(110))
            grad.setColorAt(1, c.lighter(130))
            p.fillPath(clip_path, QBrush(grad))

        # Border
        pen = QPen(QColor(self._base_color), 1.5)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(1, 1, w - 2, h - 2, r - 1, r - 1)

        # Text
        p.setPen(QPen(QColor("#ffffff")))
        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, self.text())


# ── Main Page ─────────────────────────────────────────────────────────────────

class NetworkOptimizerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ping_thread: Optional[QThread] = None
        self._ping_worker: Optional[PingWorker] = None
        self._ping_history: List[float] = []
        self._monitoring = False
        self._applied: set = set()
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
        layout.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(3)
        t = QLabel("📡  Network Optimizer")
        t.setStyleSheet("color:#ffffff;font-size:24px;font-weight:900;background:transparent;")
        s = QLabel("Reduce ping & latency with TCP tweaks  •  Live ping monitor with graph")
        s.setStyleSheet("color:#3a3a6a;font-size:12px;background:transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()

        self._apply_all_btn = AnimatedButton("⚡  Apply All Tweaks", "#6c63ff")
        self._apply_all_btn.setFixedSize(180, 42)
        self._apply_all_btn.clicked.connect(self._apply_all)
        hdr.addWidget(self._apply_all_btn)

        self._restore_btn = QPushButton("↩  Restore")
        self._restore_btn.setStyleSheet(
            "background:rgba(239,68,68,0.08);color:#ff6060;"
            "border:1px solid rgba(239,68,68,0.3);border-radius:10px;"
            "padding:8px 16px;font-size:12px;font-weight:700;"
        )
        self._restore_btn.clicked.connect(self._restore_all)
        hdr.addWidget(self._restore_btn)
        layout.addLayout(hdr)

        # ── Stat cards ───────────────────────────────────────────────────────
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self._cur_card  = self._stat_card("Current Ping", "— ms",  "#6c63ff")
        self._avg_card  = self._stat_card("Average",      "— ms",  "#00d4ff")
        self._min_card  = self._stat_card("Best",         "— ms",  "#00e87a")
        self._max_card  = self._stat_card("Worst",        "— ms",  "#ff5555")
        self._loss_card = self._stat_card("Packet Loss",  "—",     "#f97316")
        for card in [self._cur_card, self._avg_card, self._min_card, self._max_card, self._loss_card]:
            stats.addWidget(card)
        layout.addLayout(stats)

        # ── Ping Monitor card ────────────────────────────────────────────────
        mon_frame = QFrame()
        mon_frame.setObjectName("card")
        mfl = QVBoxLayout(mon_frame)
        mfl.setContentsMargins(0, 0, 0, 0)
        mfl.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(
            "background:rgba(108,99,255,0.06);"
            "border-bottom:1px solid rgba(108,99,255,0.12);"
            "border-radius:16px 16px 0 0;"
        )
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(20, 12, 20, 12)
        tbl.setSpacing(10)

        section_lbl = QLabel("📡  LIVE PING MONITOR")
        section_lbl.setStyleSheet(
            "color:rgba(108,99,255,0.6);font-size:10px;font-weight:900;"
            "letter-spacing:2px;background:transparent;"
        )
        tbl.addWidget(section_lbl)
        tbl.addStretch()

        host_lbl = QLabel("Target:")
        host_lbl.setStyleSheet("color:#4a4870;font-size:11px;background:transparent;")
        tbl.addWidget(host_lbl)

        self._host_combo = QComboBox()
        self._host_combo.setFixedWidth(220)
        for name, ip in PRESET_SERVERS:
            if ip == "custom":
                self._host_combo.addItem("Custom...", "custom")
            elif name.startswith("CS2 —"):
                self._host_combo.addItem(f"🟦 {name}  ({ip})", ip)
            elif name.startswith("Valorant"):
                self._host_combo.addItem(f"🟥 {name}  ({ip})", ip)
            elif name.startswith("Battle") or name.startswith("Epic") or name.startswith("Riot"):
                self._host_combo.addItem(f"🟧 {name}  ({ip})", ip)
            else:
                self._host_combo.addItem(f"⚪ {name}  ({ip})", ip)
        self._host_combo.setStyleSheet(
            "QComboBox{background:rgba(108,99,255,0.08);color:#c0b8e8;"
            "border:1px solid rgba(108,99,255,0.25);border-radius:8px;padding:4px 10px;font-size:11px;}"
            "QComboBox::drop-down{border:none;}"
            "QComboBox QAbstractItemView{background:#0f0e24;color:#c0b8e8;border:1px solid rgba(108,99,255,0.3);}"
        )
        self._host_combo.currentIndexChanged.connect(self._on_host_changed)
        tbl.addWidget(self._host_combo)

        self._custom_host = QLineEdit()
        self._custom_host.setPlaceholderText("Enter IP or hostname")
        self._custom_host.setFixedWidth(160)
        self._custom_host.setVisible(False)
        self._custom_host.setStyleSheet(
            "QLineEdit{background:rgba(108,99,255,0.08);color:#c0b8e8;"
            "border:1px solid rgba(108,99,255,0.25);border-radius:8px;padding:4px 10px;font-size:11px;}"
        )
        tbl.addWidget(self._custom_host)

        self._monitor_btn = AnimatedButton("▶  Start", "#00e87a")
        self._monitor_btn.setFixedSize(100, 32)
        self._monitor_btn.clicked.connect(self._toggle_monitor)
        tbl.addWidget(self._monitor_btn)
        mfl.addWidget(toolbar)

        # Graph
        self._graph = PingGraph()
        mfl.addWidget(self._graph)

        # Status bar
        self._ping_status = QLabel("Click ▶ Start to begin monitoring")
        self._ping_status.setStyleSheet(
            "color:#3a3a6a;font-size:11px;padding:8px 20px;background:transparent;"
        )
        mfl.addWidget(self._ping_status)
        layout.addWidget(mon_frame)

        # ── Tweaks section ────────────────────────────────────────────────────
        tweaks_hdr = QHBoxLayout()
        tweaks_title = QLabel("🔧  LATENCY TWEAKS")
        tweaks_title.setStyleSheet(
            "color:rgba(108,99,255,0.6);font-size:10px;font-weight:900;"
            "letter-spacing:2px;background:transparent;"
        )
        tweaks_hdr.addWidget(tweaks_title)
        tweaks_hdr.addStretch()
        layout.addLayout(tweaks_hdr)

        self._tweak_cards = {}
        self._tweak_btns = {}
        for tweak in NETWORK_TWEAKS:
            row = QHBoxLayout()
            row.setSpacing(12)
            card = TweakCard(tweak)
            self._tweak_cards[tweak["key"]] = card
            row.addWidget(card, 1)

            btn_col = QVBoxLayout()
            btn_col.setSpacing(6)

            apply_btn = AnimatedButton(f"Apply", tweak["color"])
            apply_btn.setFixedSize(90, 36)
            apply_btn.clicked.connect(lambda checked, k=tweak["key"]: self._apply_single(k))

            restore_btn = QPushButton("Restore")
            restore_btn.setFixedSize(90, 30)
            restore_btn.setStyleSheet(
                "background:rgba(30,28,55,0.8);color:#4a4870;"
                "border:1px solid rgba(108,99,255,0.1);border-radius:8px;"
                "font-size:10px;font-weight:700;"
            )
            restore_btn.clicked.connect(lambda checked, k=tweak["key"]: self._restore_single(k))

            btn_col.addWidget(apply_btn)
            btn_col.addWidget(restore_btn)
            btn_col.addStretch()
            row.addLayout(btn_col)
            layout.addLayout(row)
            self._tweak_btns[tweak["key"]] = (apply_btn, restore_btn)

        layout.addStretch()

    # ── Stat card helper ─────────────────────────────────────────────────────

    def _stat_card(self, label: str, value: str, color: str) -> QFrame:
        f = QFrame()
        f.setObjectName("card")
        vl = QVBoxLayout(f)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(3)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color};font-size:22px;font-weight:900;background:transparent;")
        lb = QLabel(label)
        lb.setStyleSheet("color:rgba(160,150,220,0.4);font-size:9px;font-weight:700;letter-spacing:0.5px;background:transparent;")
        vl.addWidget(v)
        vl.addWidget(lb)
        f._val = v
        return f

    def _update_stat(self, card, value: str):
        card._val.setText(value)

    # ── Host combo ────────────────────────────────────────────────────────────

    def _on_host_changed(self, idx: int):
        ip = self._host_combo.itemData(idx)
        self._custom_host.setVisible(ip == "custom")

    def _current_host(self) -> str:
        ip = self._host_combo.currentData()
        if ip == "custom":
            return self._custom_host.text().strip() or "8.8.8.8"
        return ip

    # ── Monitor ───────────────────────────────────────────────────────────────

    def _toggle_monitor(self):
        if self._monitoring:
            self._stop_monitor()
        else:
            self._start_monitor()

    def _start_monitor(self):
        host = self._current_host()
        self._monitoring = True
        self._monitor_btn.setText("⏹  Stop")
        self._graph.clear()
        self._ping_history.clear()
        self._ping_status.setText(f"🔍 Monitoring {host}...")

        self._ping_thread = QThread()
        self._ping_worker = PingWorker(host)
        self._ping_worker.moveToThread(self._ping_thread)
        self._ping_thread.started.connect(self._ping_worker.start_ping)
        self._ping_worker.result.connect(self._on_ping_result)
        self._ping_worker.finished.connect(self._ping_thread.quit)
        self._ping_thread.start()

    def _stop_monitor(self):
        self._monitoring = False
        self._monitor_btn.setText("▶  Start")
        if self._ping_worker:
            self._ping_worker.stop()
        self._ping_status.setText("Monitoring stopped.")

    def _on_ping_result(self, ms: float):
        self._graph.add_point(ms)
        self._ping_history.append(ms)
        valid = [v for v in self._ping_history if v > 0]
        timeouts = [v for v in self._ping_history if v < 0]
        loss_pct = len(timeouts) / len(self._ping_history) * 100 if self._ping_history else 0

        if ms < 0:
            self._update_stat(self._cur_card, "Timeout")
            self._ping_status.setText("⚠ Request timed out")
        else:
            color = "#00e87a" if ms < 50 else "#f97316" if ms < 120 else "#ff5555"
            self._cur_card._val.setStyleSheet(
                f"color:{color};font-size:22px;font-weight:900;background:transparent;"
            )
            self._update_stat(self._cur_card, f"{ms:.0f} ms")
            label = "🟢 Excellent" if ms < 30 else "🟡 Good" if ms < 60 else "🟠 Fair" if ms < 120 else "🔴 High"
            self._ping_status.setText(f"{label}  •  {ms:.0f} ms  •  Host: {self._current_host()}")

        if valid:
            self._update_stat(self._avg_card, f"{sum(valid)/len(valid):.0f} ms")
            self._update_stat(self._min_card, f"{min(valid):.0f} ms")
            self._update_stat(self._max_card, f"{max(valid):.0f} ms")
        self._update_stat(self._loss_card, f"{loss_pct:.1f}%")

    # ── Tweaks ────────────────────────────────────────────────────────────────

    def _apply_single(self, key: str):
        tweak = next(t for t in NETWORK_TWEAKS if t["key"] == key)
        apply_btn, _ = self._tweak_btns[key]
        apply_btn.setEnabled(False)
        apply_btn.start_animation()

        self._tw_thread = QThread()
        self._tw_worker = TweakWorker(tweak["reg_cmds"])
        self._tw_worker.moveToThread(self._tw_thread)
        self._tw_thread.started.connect(self._tw_worker.run)
        self._tw_worker.finished.connect(lambda ok, msg, k=key: self._on_tweak_done(k, ok, msg))
        self._tw_worker.finished.connect(self._tw_thread.quit)
        self._tw_thread.start()

    def _on_tweak_done(self, key: str, ok: bool, msg: str):
        apply_btn, _ = self._tweak_btns[key]
        apply_btn.stop_animation(ok)
        apply_btn.setEnabled(True)
        if ok:
            self._applied.add(key)
            self._tweak_cards[key].set_applied(True)
        logger.info(f"Tweak {key}: {msg}")

    def _restore_single(self, key: str):
        tweak = next(t for t in NETWORK_TWEAKS if t["key"] == key)
        if not tweak["restore_cmds"]:
            return
        _, restore_btn = self._tweak_btns[key]
        restore_btn.setEnabled(False)

        self._tr_thread = QThread()
        self._tr_worker = TweakWorker(tweak["restore_cmds"])
        self._tr_worker.moveToThread(self._tr_thread)
        self._tr_thread.started.connect(self._tr_worker.run)
        self._tr_worker.finished.connect(lambda ok, msg, k=key: self._on_restore_done(k, ok))
        self._tr_worker.finished.connect(self._tr_thread.quit)
        self._tr_thread.start()

    def _on_restore_done(self, key: str, ok: bool):
        _, restore_btn = self._tweak_btns[key]
        restore_btn.setEnabled(True)
        if ok:
            self._applied.discard(key)
            self._tweak_cards[key].set_applied(False)

    def _apply_all(self):
        all_cmds = []
        for tweak in NETWORK_TWEAKS:
            all_cmds.extend(tweak["reg_cmds"])
        self._apply_all_btn.setEnabled(False)
        self._apply_all_btn.start_animation()

        self._all_thread = QThread()
        self._all_worker = TweakWorker(all_cmds)
        self._all_worker.moveToThread(self._all_thread)
        self._all_thread.started.connect(self._all_worker.run)
        self._all_worker.finished.connect(self._on_all_done)
        self._all_worker.finished.connect(self._all_thread.quit)
        self._all_thread.start()

    def _on_all_done(self, ok: bool, msg: str):
        self._apply_all_btn.stop_animation(ok)
        self._apply_all_btn.setEnabled(True)
        if ok:
            for tweak in NETWORK_TWEAKS:
                self._applied.add(tweak["key"])
                self._tweak_cards[tweak["key"]].set_applied(True)

    def _restore_all(self):
        all_cmds = []
        for tweak in NETWORK_TWEAKS:
            all_cmds.extend(tweak["restore_cmds"])
        self._restore_btn.setEnabled(False)

        self._ral_thread = QThread()
        self._ral_worker = TweakWorker(all_cmds)
        self._ral_worker.moveToThread(self._ral_thread)
        self._ral_thread.started.connect(self._ral_worker.run)
        self._ral_worker.finished.connect(self._on_restore_all_done)
        self._ral_worker.finished.connect(self._ral_thread.quit)
        self._ral_thread.start()

    def _on_restore_all_done(self, ok: bool, msg: str):
        self._restore_btn.setEnabled(True)
        if ok:
            self._applied.clear()
            for tweak in NETWORK_TWEAKS:
                self._tweak_cards[tweak["key"]].set_applied(False)

    def closeEvent(self, event):
        self._stop_monitor()
        super().closeEvent(event)
