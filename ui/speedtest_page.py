"""
SRK Boost - Speed Test Page v4.0
Pure socket-based speed test — zero external dependencies.
Speedtest.net-style animated gauge with live updating numbers.
"""

import logging
import time
import socket
import threading
import urllib.request
import urllib.error
import webbrowser
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QFont, QConicalGradient, QPainterPath
)

logger = logging.getLogger(__name__)

# ── Test servers (HTTP download endpoints, no auth needed) ────────────────────
TEST_SERVERS = [
    ("Cloudflare",    "speed.cloudflare.com", "/cdn-cgi/trace"),
    ("Fast.com CDN",  "api.fast.com",         "/netflix/speedtest"),
    ("Google",        "www.google.com",        "/"),
]

DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=25000000"   # 25 MB
UPLOAD_URL   = "https://speed.cloudflare.com/__up"


# ── Worker ────────────────────────────────────────────────────────────────────

class SpeedTestWorker(QObject):
    ping_done     = pyqtSignal(float)          # ms
    dl_progress   = pyqtSignal(float)          # current Mbps (live)
    dl_done       = pyqtSignal(float)          # final Mbps
    ul_progress   = pyqtSignal(float)
    ul_done       = pyqtSignal(float)
    status        = pyqtSignal(str)
    finished      = pyqtSignal()
    error         = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        try:
            # ── Ping ──────────────────────────────────────────────────────
            self.status.emit("📡 Ping ölçülüyor...")
            ping_ms = self._measure_ping("speed.cloudflare.com")
            if self._abort: return
            self.ping_done.emit(ping_ms)

            # ── Download ──────────────────────────────────────────────────
            self.status.emit("⬇ Download hızı ölçülüyor...")
            dl_mbps = self._measure_download()
            if self._abort: return
            self.dl_done.emit(dl_mbps)

            # ── Upload ────────────────────────────────────────────────────
            self.status.emit("⬆ Upload hızı ölçülüyor...")
            ul_mbps = self._measure_upload()
            if self._abort: return
            self.ul_done.emit(ul_mbps)

            q = "🟢 Mükemmel" if ping_ms < 30 else "🟡 İyi" if ping_ms < 60 else "🟠 Orta" if ping_ms < 120 else "🔴 Yüksek"
            self.status.emit(
                f"✅ Test tamamlandı!  {q}  •  "
                f"⬇ {dl_mbps:.1f} Mbps  ⬆ {ul_mbps:.1f} Mbps  📡 {ping_ms:.0f} ms"
            )
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def _measure_ping(self, host: str) -> float:
        samples = []
        for _ in range(4):
            try:
                t0 = time.perf_counter()
                req = urllib.request.Request(f"https://{host}/cdn-cgi/trace",
                                             headers={"User-Agent": "SRK-Boost/1.7"})
                urllib.request.urlopen(req, timeout=3)
                samples.append((time.perf_counter() - t0) * 1000)
            except Exception:
                pass
            time.sleep(0.1)
        return min(samples) if samples else 99.0

    def _measure_download(self) -> float:
        url = DOWNLOAD_URL
        total_bytes = 0
        t_start = time.perf_counter()
        last_report = t_start
        last_bytes = 0
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SRK-Boost/1.7"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                while not self._abort:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    now = time.perf_counter()
                    if now - last_report >= 0.3:
                        elapsed = now - last_report
                        chunk_mbps = (total_bytes - last_bytes) * 8 / elapsed / 1_000_000
                        self.dl_progress.emit(chunk_mbps)
                        last_report = now
                        last_bytes = total_bytes
                    if time.perf_counter() - t_start > 12:
                        break
        except Exception as e:
            logger.warning(f"Download error: {e}")
        elapsed = time.perf_counter() - t_start
        return total_bytes * 8 / elapsed / 1_000_000 if elapsed > 0 else 0.0

    def _measure_upload(self) -> float:
        data = b"0" * 10_000_000  # 10 MB
        total_sent = 0
        t_start = time.perf_counter()
        last_report = t_start
        last_sent = 0
        chunk_size = 65536
        try:
            req = urllib.request.Request(
                UPLOAD_URL, data=data,
                headers={
                    "User-Agent": "SRK-Boost/1.7",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(data)),
                },
                method="POST"
            )
            # Upload in chunks via a custom approach
            import io
            buf = io.BytesIO(data)
            while not self._abort:
                chunk = buf.read(chunk_size)
                if not chunk:
                    break
                total_sent += len(chunk)
                now = time.perf_counter()
                if now - last_report >= 0.3:
                    elapsed = now - last_report
                    mbps = (total_sent - last_sent) * 8 / elapsed / 1_000_000
                    self.ul_progress.emit(mbps)
                    last_report = now
                    last_sent = total_sent
                if time.perf_counter() - t_start > 10:
                    break
            # Send what we've buffered
            try:
                upload_req = urllib.request.Request(
                    UPLOAD_URL, data=data[:total_sent],
                    headers={"User-Agent": "SRK-Boost/1.7",
                             "Content-Type": "application/octet-stream"},
                    method="POST"
                )
                urllib.request.urlopen(upload_req, timeout=12)
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Upload error: {e}")
        elapsed = time.perf_counter() - t_start
        return total_sent * 8 / elapsed / 1_000_000 if elapsed > 0 else 0.0


# ── Big animated gauge (speedtest.net style) ──────────────────────────────────

class BigGauge(QWidget):
    def __init__(self, label: str, unit: str, max_val: float, color: str, parent=None):
        super().__init__(parent)
        self._label  = label
        self._unit   = unit
        self._max    = max_val
        self._color  = QColor(color)
        self._value  = 0.0
        self._target = 0.0
        self._phase  = "idle"   # idle / testing / done
        self._anim   = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)
        self.setMinimumSize(280, 260)

    def setValue(self, v: float, final: bool = False):
        self._target = min(float(v), self._max)
        self._phase  = "done" if final else "testing"

    def reset(self):
        self._target = 0.0
        self._phase  = "idle"

    def _tick(self):
        diff = self._target - self._value
        if abs(diff) > 0.05:
            speed = 0.08 if self._phase == "testing" else 0.15
            self._value += diff * speed
            self.update()
        elif self._value != self._target:
            self._value = self._target
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2
        cy = int(h * 0.52)
        r  = min(w, h) // 2 - 22

        # Outer glow
        if self._phase != "idle" and self._value > 0:
            glow = QRadialGradient(cx, cy, r + 20)
            gc = QColor(self._color)
            gc.setAlpha(30)
            glow.setColorAt(0, gc)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - r - 20, cy - r - 20, (r + 20) * 2, (r + 20) * 2)

        # Track (dark arc 220° → from bottom-left to bottom-right)
        start_angle = 220
        span_angle  = -260
        pen_track = QPen(QColor(18, 16, 38), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(cx - r, cy - r, r * 2, r * 2,
                  start_angle * 16, span_angle * 16)

        # Value arc with gradient color
        pct = min(self._value / self._max, 1.0) if self._max > 0 else 0
        if pct > 0:
            arc_span = int(span_angle * pct)
            # Color: cyan → purple → red based on pct
            if pct < 0.4:
                arc_color = self._color
            elif pct < 0.75:
                arc_color = self._color.lighter(115)
            else:
                arc_color = self._color.lighter(135)
            pen_val = QPen(arc_color, 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen_val)
            p.drawArc(cx - r, cy - r, r * 2, r * 2,
                      start_angle * 16, arc_span)

            # Glowing dot at tip
            angle_deg = start_angle + (span_angle * pct)
            angle_rad = math.radians(angle_deg)
            tip_x = cx + r * math.cos(angle_rad)
            tip_y = cy - r * math.sin(angle_rad)
            p.setPen(Qt.PenStyle.NoPen)
            glow2 = QRadialGradient(tip_x, tip_y, 10)
            glow2.setColorAt(0, arc_color.lighter(150))
            glow2.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow2))
            p.drawEllipse(QPointF(tip_x, tip_y), 10, 10)
            p.setBrush(QBrush(arc_color))
            p.drawEllipse(QPointF(tip_x, tip_y), 5, 5)

        # Center value
        val_str = f"{self._value:.1f}" if self._value >= 0.1 else "—"
        p.setPen(QPen(QColor("#ffffff") if self._phase != "idle" else QColor(60, 55, 100)))
        font_val = QFont("Segoe UI", 36, QFont.Weight.Black)
        p.setFont(font_val)
        p.drawText(0, cy - 44, w, 54, Qt.AlignmentFlag.AlignCenter, val_str)

        # Unit
        p.setPen(QPen(QColor(90, 85, 150)))
        p.setFont(QFont("Segoe UI", 12))
        p.drawText(0, cy + 12, w, 22, Qt.AlignmentFlag.AlignCenter, self._unit)

        # Tick marks
        p.setPen(QPen(QColor(35, 30, 65), 2))
        for i in range(11):
            tick_pct = i / 10
            angle_deg = start_angle + span_angle * tick_pct
            angle_rad = math.radians(angle_deg)
            inner = r - 10
            outer_r = r + 2
            x1 = cx + inner * math.cos(angle_rad)
            y1 = cy - inner * math.sin(angle_rad)
            x2 = cx + outer_r * math.cos(angle_rad)
            y2 = cy - outer_r * math.sin(angle_rad)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Label
        p.setPen(QPen(self._color if self._phase != "idle" else QColor(50, 45, 90)))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(0, cy + 36, w, 20, Qt.AlignmentFlag.AlignCenter, self._label.upper())


# ── Start button ──────────────────────────────────────────────────────────────

class StartButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover    = False
        self._pressed  = False
        self._phase    = "idle"   # idle / running / done
        self._pulse    = 0.0
        self._pulse_dir = 1
        self._timer    = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)
        self.setFixedSize(160, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_phase(self, phase: str):
        self._phase = phase
        self.update()

    def _tick(self):
        if self._phase == "running":
            self._pulse += 0.04 * self._pulse_dir
            if self._pulse > 1.0:
                self._pulse = 1.0; self._pulse_dir = -1
            elif self._pulse < 0.0:
                self._pulse = 0.0; self._pulse_dir = 1
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 8

        # Outer glow ring
        if self._phase == "running":
            alpha = int(40 + 60 * self._pulse)
            glow = QRadialGradient(cx, cy, r + 12)
            glow.setColorAt(0, QColor(108, 99, 255, alpha))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - r - 12, cy - r - 12, (r + 12) * 2, (r + 12) * 2)

        # Ring border
        ring_color = QColor("#6c63ff") if self._phase != "idle" else QColor(40, 36, 80)
        p.setPen(QPen(ring_color, 3))
        p.setBrush(QBrush(QColor(10, 8, 22)))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Inner gradient
        grad = QRadialGradient(cx, cy - 10, r - 8)
        if self._phase == "running":
            grad.setColorAt(0, QColor(50, 45, 100))
            grad.setColorAt(1, QColor(15, 12, 35))
        elif self._phase == "done":
            grad.setColorAt(0, QColor(0, 80, 50))
            grad.setColorAt(1, QColor(0, 30, 20))
        else:
            grad.setColorAt(0, QColor(30, 26, 65))
            grad.setColorAt(1, QColor(10, 8, 22))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(cx - r + 3, cy - r + 3, (r - 3) * 2, (r - 3) * 2)

        # Text
        if self._phase == "idle":
            text, color, size = "GO", "#6c63ff", 28
        elif self._phase == "running":
            text, color, size = "■", "#ff6060", 22
        else:
            text, color, size = "✓", "#00e87a", 26

        p.setPen(QPen(QColor(color)))
        p.setFont(QFont("Segoe UI", size, QFont.Weight.Black))
        p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, text)

        # "BAŞLAT" label below
        p.setPen(QPen(QColor(60, 55, 100)))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        label = "BAŞLAT" if self._phase == "idle" else "DURDUR" if self._phase == "running" else "TEKRAR"
        p.drawText(0, h - 18, w, 16, Qt.AlignmentFlag.AlignCenter, label)

    def mousePressEvent(self, e):
        self._pressed = True
        self.update()

    def mouseReleaseEvent(self, e):
        if self._pressed:
            self._pressed = False
            self.clicked.emit()
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()


# ── Main Page ─────────────────────────────────────────────────────────────────

class SpeedTestPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker  = None
        self._thread  = None
        self._running = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: #080716;")
        scroll.setWidget(container)
        vl = QVBoxLayout(container)
        vl.setContentsMargins(32, 28, 32, 32)
        vl.setSpacing(24)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(2)
        t = QLabel("🌐  İnternet Hız Testi")
        t.setStyleSheet("color:#ffffff;font-size:22px;font-weight:900;background:transparent;")
        s = QLabel("Download  •  Upload  •  Ping  —  Anlık canlı ölçüm")
        s.setStyleSheet("color:#2a2850;font-size:11px;background:transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()
        web_btn = QPushButton("🌐  speedtest.net")
        web_btn.setStyleSheet(
            "background:rgba(108,99,255,0.08);color:#4a45a0;"
            "border:1px solid rgba(108,99,255,0.2);border-radius:10px;"
            "font-size:11px;font-weight:700;padding:8px 16px;"
        )
        web_btn.clicked.connect(lambda: webbrowser.open("https://www.speedtest.net"))
        hdr.addWidget(web_btn)
        vl.addLayout(hdr)

        # ── Gauges + Start button ─────────────────────────────────────────
        gauges_frame = QFrame()
        gauges_frame.setStyleSheet(
            "background: rgba(108,99,255,0.04);"
            "border: 1px solid rgba(108,99,255,0.1);"
            "border-radius: 24px;"
        )
        gfl = QVBoxLayout(gauges_frame)
        gfl.setContentsMargins(24, 24, 24, 24)
        gfl.setSpacing(16)

        # Gauges row
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(12)
        gauges_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._dl_gauge   = BigGauge("⬇  Download", "Mbps", 1000, "#00d4ff")
        self._start_btn  = StartButton()
        self._ul_gauge   = BigGauge("⬆  Upload",   "Mbps", 1000, "#00e87a")

        gauges_row.addWidget(self._dl_gauge, 2)
        gauges_row.addWidget(self._start_btn, 0, Qt.AlignmentFlag.AlignCenter)
        gauges_row.addWidget(self._ul_gauge, 2)
        gfl.addLayout(gauges_row)

        # Ping + stat cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._ping_card  = self._stat("📡  Ping",     "—",      "#f97316")
        self._dl_card    = self._stat("⬇  Download",  "—",      "#00d4ff")
        self._ul_card    = self._stat("⬆  Upload",    "—",      "#00e87a")
        self._isp_card   = self._stat("🌍  Sunucu",   "Cloudflare", "#a78bff")
        for c in [self._ping_card, self._dl_card, self._ul_card, self._isp_card]:
            stats_row.addWidget(c)
        gfl.addLayout(stats_row)

        # Status
        self._status_lbl = QLabel("GO butonuna bas — hız testi başlasın")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            "color:#3a3570;font-size:12px;font-weight:600;background:transparent;"
        )
        gfl.addWidget(self._status_lbl)

        vl.addWidget(gauges_frame)
        vl.addStretch()

        self._start_btn.clicked.connect(self._toggle)

    def _stat(self, label, value, color):
        f = QFrame()
        f.setStyleSheet(
            "QFrame{background:rgba(108,99,255,0.05);"
            "border:1px solid rgba(108,99,255,0.1);border-radius:14px;}"
        )
        vl = QVBoxLayout(f)
        vl.setContentsMargins(16, 10, 16, 10)
        vl.setSpacing(2)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color};font-size:18px;font-weight:900;background:transparent;")
        lb = QLabel(label)
        lb.setStyleSheet("color:rgba(100,90,160,0.5);font-size:9px;font-weight:700;letter-spacing:0.5px;background:transparent;")
        vl.addWidget(v)
        vl.addWidget(lb)
        f._val = v
        return f

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._running = True
        self._start_btn.set_phase("running")
        self._dl_gauge.reset()
        self._ul_gauge.reset()
        self._ping_card._val.setText("—")
        self._dl_card._val.setText("—")
        self._ul_card._val.setText("—")
        self._status_lbl.setText("🌍 Bağlanıyor...")
        self._status_lbl.setStyleSheet(
            "color:#6c63ff;font-size:12px;font-weight:600;background:transparent;"
        )

        self._thread = QThread()
        self._worker = SpeedTestWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.ping_done.connect(self._on_ping)
        self._worker.dl_progress.connect(lambda v: self._dl_gauge.setValue(v))
        self._worker.dl_done.connect(self._on_dl_done)
        self._worker.ul_progress.connect(lambda v: self._ul_gauge.setValue(v))
        self._worker.ul_done.connect(self._on_ul_done)
        self._worker.status.connect(self._status_lbl.setText)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _stop(self):
        if self._worker:
            self._worker.abort()

    def _on_ping(self, ms: float):
        q = "🟢" if ms < 30 else "🟡" if ms < 60 else "🟠" if ms < 120 else "🔴"
        self._ping_card._val.setText(f"{q} {ms:.0f} ms")

    def _on_dl_done(self, mbps: float):
        self._dl_gauge.setValue(mbps, final=True)
        self._dl_card._val.setText(f"{mbps:.1f} Mbps")

    def _on_ul_done(self, mbps: float):
        self._ul_gauge.setValue(mbps, final=True)
        self._ul_card._val.setText(f"{mbps:.1f} Mbps")

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"❌ {msg}")
        self._status_lbl.setStyleSheet(
            "color:#ff6060;font-size:12px;font-weight:600;background:transparent;"
        )

    def _on_finished(self):
        self._running = False
        self._start_btn.set_phase("done")

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)
