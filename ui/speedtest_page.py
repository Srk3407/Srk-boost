"""
SRK Boost - Speed Test Page  v3.0
Pure Python speedtest — no PyQtWebEngine needed.
Uses speedtest-cli library with animated gauges.
"""

import logging
import webbrowser
import threading
import time
import socket
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QLinearGradient

logger = logging.getLogger(__name__)


# ── Animated Speed Gauge ──────────────────────────────────────────────────────

class SpeedGauge(QWidget):
    def __init__(self, label, unit, max_val, color, parent=None):
        super().__init__(parent)
        self._label = label
        self._unit = unit
        self._max = max_val
        self._color = QColor(color)
        self._value = 0.0
        self._target = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(16)
        self.setFixedSize(200, 170)

    def setValue(self, v):
        self._target = min(float(v), self._max)

    def _tick(self):
        diff = self._target - self._value
        if abs(diff) > 0.1:
            self._value += diff * 0.12
            self.update()
        elif self._value != self._target:
            self._value = self._target
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 8
        r = min(w, h) // 2 - 20

        # Background circle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(12, 10, 25)))
        p.drawEllipse(cx - r - 8, cy - r - 8, (r + 8) * 2, (r + 8) * 2)

        # Track arc
        pen = QPen(QColor(25, 22, 48), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(cx - r, cy - r, r * 2, r * 2, 210 * 16, -240 * 16)

        # Value arc with gradient color
        pct = self._value / self._max if self._max else 0
        span = int(-240 * 16 * pct)
        if span:
            # Color shifts: green → orange → red
            if pct < 0.5:
                c = self._color
            elif pct < 0.8:
                c = self._color.lighter(110)
            else:
                c = self._color.lighter(130)
            pen2 = QPen(c, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen2)
            p.drawArc(cx - r, cy - r, r * 2, r * 2, 210 * 16, span)

        # Glow dot at tip
        if pct > 0:
            import math
            angle_deg = 210 - 240 * pct
            angle_rad = math.radians(angle_deg)
            tip_x = cx + r * math.cos(angle_rad)
            tip_y = cy - r * math.sin(angle_rad)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(self._color.lighter(150)))
            p.drawEllipse(int(tip_x) - 6, int(tip_y) - 6, 12, 12)

        # Value
        p.setPen(QPen(self._color))
        p.setFont(QFont("Segoe UI", 22, QFont.Weight.Black))
        p.drawText(0, cy - 22, w, 36, Qt.AlignmentFlag.AlignCenter,
                   f"{self._value:.1f}")

        # Unit
        p.setPen(QPen(QColor(80, 75, 130)))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(0, cy + 16, w, 20, Qt.AlignmentFlag.AlignCenter, self._unit)

        # Label
        p.setPen(QPen(QColor(60, 55, 100)))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(0, h - 22, w, 18, Qt.AlignmentFlag.AlignCenter, self._label.upper())


# ── Speedtest Worker ──────────────────────────────────────────────────────────

class SpeedTestWorker(QObject):
    progress = pyqtSignal(str, int)       # message, percent
    result   = pyqtSignal(float, float, float, str)  # dl, ul, ping, server_name
    error    = pyqtSignal(str)

    def run(self):
        try:
            import speedtest as _st
            self.progress.emit("🌍 Sunucu listesi alınıyor...", 10)
            st = _st.Speedtest(secure=True)

            self.progress.emit("📡 En yakın sunucu seçiliyor...", 20)
            st.get_best_server()
            server = st.results.server
            server_name = f"{server.get('name','?')}, {server.get('country','?')}"
            self.progress.emit(f"✅ Sunucu: {server_name}", 30)

            self.progress.emit("⬇ Download hızı ölçülüyor...", 40)
            dl = st.download(threads=4) / 1_000_000
            self.progress.emit(f"⬇ Download: {dl:.1f} Mbps", 65)

            self.progress.emit("⬆ Upload hızı ölçülüyor...", 70)
            ul = st.upload(threads=4) / 1_000_000
            self.progress.emit(f"⬆ Upload: {ul:.1f} Mbps", 90)

            ping = float(st.results.ping)
            self.progress.emit("✅ Test tamamlandı!", 100)
            self.result.emit(dl, ul, ping, server_name)

        except ImportError:
            self.error.emit(
                "speedtest-cli kurulu değil.\n"
                "Komut istemcisini aç ve şunu çalıştır:\n"
                "pip install speedtest-cli"
            )
        except Exception as e:
            self.error.emit(f"Hata: {str(e)}")


# ── Main Page ─────────────────────────────────────────────────────────────────

class SpeedTestPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._running = False
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

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

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(3)
        t = QLabel("🌐  İnternet Hız Testi")
        t.setStyleSheet("color:#ffffff;font-size:24px;font-weight:900;background:transparent;")
        s = QLabel("Download · Upload · Ping — speedtest-cli ile gerçek hız ölçümü")
        s.setStyleSheet("color:#3a3a6a;font-size:12px;background:transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()
        layout.addLayout(hdr)

        # ── Stat cards ────────────────────────────────────────────────────────
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self._dl_card   = self._stat_card("⬇ Download",  "— Mbps", "#00d4ff")
        self._ul_card   = self._stat_card("⬆ Upload",    "— Mbps", "#00e87a")
        self._ping_card = self._stat_card("📡 Ping",     "— ms",   "#f97316")
        self._isp_card  = self._stat_card("🌍 Sunucu",   "—",      "#a78bff")
        for c in [self._dl_card, self._ul_card, self._ping_card, self._isp_card]:
            stats.addWidget(c)
        layout.addLayout(stats)

        # ── Gauges card ───────────────────────────────────────────────────────
        gauges_frame = QFrame()
        gauges_frame.setObjectName("card")
        gfl = QVBoxLayout(gauges_frame)
        gfl.setContentsMargins(20, 16, 20, 16)
        gfl.setSpacing(12)

        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(20)
        gauges_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dl_gauge   = SpeedGauge("⬇ Download", "Mbps", 1000, "#00d4ff")
        self._ul_gauge   = SpeedGauge("⬆ Upload",   "Mbps", 1000, "#00e87a")
        self._ping_gauge = SpeedGauge("📡 Ping",     "ms",   200,  "#f97316")
        for g in [self._dl_gauge, self._ul_gauge, self._ping_gauge]:
            gauges_row.addWidget(g)
        gfl.addLayout(gauges_row)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setStyleSheet("""
            QProgressBar {
                background: rgba(108,99,255,0.08);
                border: 1px solid rgba(108,99,255,0.15);
                border-radius: 6px; height: 8px; text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6c63ff, stop:1 #00d4ff);
                border-radius: 6px;
            }
        """)
        self._progress.setVisible(False)
        gfl.addWidget(self._progress)

        # Status
        self._status_lbl = QLabel("▶ Başlamak için 'Hız Testini Başlat' butonuna tıklayın")
        self._status_lbl.setStyleSheet(
            "color:#6c63ff;font-size:12px;font-weight:600;background:transparent;"
        )
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gfl.addWidget(self._status_lbl)

        layout.addWidget(gauges_frame)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._start_btn = QPushButton("▶   Hız Testini Başlat")
        self._start_btn.setObjectName("boost_btn")
        self._start_btn.setFixedHeight(52)
        self._start_btn.clicked.connect(self._start_test)
        btn_row.addWidget(self._start_btn, 2)

        web_btn = QPushButton("🌐  speedtest.net")
        web_btn.setStyleSheet(
            "background:rgba(108,99,255,0.08);color:#6c63ff;"
            "border:1px solid rgba(108,99,255,0.25);border-radius:12px;"
            "font-size:13px;font-weight:700;padding:12px 20px;"
        )
        web_btn.clicked.connect(lambda: webbrowser.open("https://www.speedtest.net"))
        btn_row.addWidget(web_btn, 1)
        layout.addLayout(btn_row)

        # ── Install hint ──────────────────────────────────────────────────────
        hint = QFrame()
        hint.setObjectName("card")
        hint.setStyleSheet(
            "QFrame#card{background:rgba(249,115,22,0.05);"
            "border:1px solid rgba(249,115,22,0.15);border-radius:14px;}"
        )
        hl = QHBoxLayout(hint)
        hl.setContentsMargins(16, 12, 16, 12)
        icon_l = QLabel("💡")
        icon_l.setStyleSheet("font-size:18px;background:transparent;")
        msg = QLabel(
            "speedtest-cli gereklidir.  Kurulu değilse:\n"
            "Komut İstemi'ni açın → pip install speedtest-cli"
        )
        msg.setStyleSheet("color:#6060a0;font-size:11px;background:transparent;")
        hl.addWidget(icon_l)
        hl.addWidget(msg, 1)
        layout.addWidget(hint)

        layout.addStretch()

    def _stat_card(self, label, value, color):
        f = QFrame()
        f.setObjectName("card")
        vl = QVBoxLayout(f)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(3)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color};font-size:20px;font-weight:900;background:transparent;")
        lb = QLabel(label)
        lb.setStyleSheet("color:rgba(160,150,220,0.4);font-size:9px;font-weight:700;letter-spacing:0.5px;background:transparent;")
        vl.addWidget(v)
        vl.addWidget(lb)
        f._val = v
        return f

    def _start_test(self):
        if self._running:
            return
        self._running = True
        self._start_btn.setEnabled(False)
        self._start_btn.setText("⏳  Test çalışıyor...")
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._dl_gauge.setValue(0)
        self._ul_gauge.setValue(0)
        self._ping_gauge.setValue(0)
        self._dl_card._val.setText("— Mbps")
        self._ul_card._val.setText("— Mbps")
        self._ping_card._val.setText("— ms")
        self._isp_card._val.setText("—")

        self._thread = QThread()
        self._worker = SpeedTestWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.result.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._on_thread_done)
        self._thread.start()

    def _on_progress(self, msg, pct):
        self._status_lbl.setText(msg)
        self._progress.setValue(pct)

    def _on_result(self, dl, ul, ping, server):
        self._dl_gauge.setValue(dl)
        self._ul_gauge.setValue(ul)
        self._ping_gauge.setValue(ping)
        self._dl_card._val.setText(f"{dl:.1f} Mbps")
        self._ul_card._val.setText(f"{ul:.1f} Mbps")
        self._ping_card._val.setText(f"{ping:.0f} ms")
        self._isp_card._val.setText(server[:22] if len(server) > 22 else server)
        q = "🟢 Mükemmel" if ping < 30 else "🟡 İyi" if ping < 60 else "🟠 Orta" if ping < 100 else "🔴 Yüksek"
        self._status_lbl.setText(f"✅ Test tamamlandı!  {q}  •  {dl:.1f} ↓  {ul:.1f} ↑  {ping:.0f}ms ping")

    def _on_error(self, msg):
        self._status_lbl.setText(f"❌ {msg}")

    def _on_thread_done(self):
        self._running = False
        self._start_btn.setEnabled(True)
        self._start_btn.setText("🔄  Tekrar Test Et")
        self._progress.setVisible(False)
