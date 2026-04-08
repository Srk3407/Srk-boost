"""
SRK Boost - Dashboard Page
Real-time CPU/RAM gauges and performance graph.
Premium redesign: 120fps GPU-accelerated animations, gradient arcs, glow effects.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSlot
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPainterPath,
    QLinearGradient, QConicalGradient, QRadialGradient
)

import logging
from core.i18n import tr

logger = logging.getLogger(__name__)


class AnimatedGauge(QWidget):
    """
    High-quality animated circular gauge with:
    - Smooth 120fps animation via QTimer
    - GPU-accelerated QPainter with antialiasing
    - Gradient arc (green→yellow→red based on value)
    - Glow effect when value > 80%
    - Animated value transitions (easing)
    - Center text with value + unit
    - Label below
    """

    def __init__(self, label, unit="%", parent=None):
        super().__init__(parent)
        self._target = 0.0
        self._current = 0.0
        self._label = label
        self._unit = unit
        self.setMinimumSize(180, 190)

        # 120fps animation timer
        self._timer = QTimer()
        self._timer.setInterval(8)  # ~120fps
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def setValue(self, v):
        self._target = max(0, min(100, float(v)))

    def _animate(self):
        diff = self._target - self._current
        if abs(diff) > 0.1:
            self._current += diff * 0.12  # smooth easing
            self.update()

    def paintEvent(self, event):
        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2 - 8
        r = min(W, H - 30) // 2 - 14

        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )

        pct = self._current / 100.0

        # Dark radial background behind gauge
        grad = QRadialGradient(cx, cy, r + 14)
        grad.setColorAt(0.0, QColor(22, 22, 40))
        grad.setColorAt(1.0, QColor(10, 10, 20))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(cx - r - 14, cy - r - 14, (r + 14) * 2, (r + 14) * 2)

        # Background track
        track_pen = QPen(QColor("#1a1a2e"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, -270 * 16)

        # Color based on value: green→yellow→red
        if pct < 0.6:
            t = pct / 0.6
            red = int(0 + 255 * t)
            green = 200
            blue = 80
        else:
            t = (pct - 0.6) / 0.4
            red = 255
            green = int(200 - 200 * t)
            blue = int(80 - 80 * t)

        arc_color = QColor(red, green, blue)

        # Glow effect when high (> 80%)
        if pct > 0.8:
            for glow_w, glow_a in [(22, 15), (18, 25), (14, 35)]:
                glow_pen = QPen(
                    QColor(red, green, blue, glow_a), glow_w,
                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
                )
                painter.setPen(glow_pen)
                painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, int(-270 * 16 * pct))

        # Main arc
        arc_pen = QPen(arc_color, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, int(-270 * 16 * pct))

        # Inner highlight ring (subtle)
        inner_pen = QPen(QColor(red, green, blue, 30), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(inner_pen)
        painter.drawEllipse(cx - r + 16, cy - r + 16, (r - 16) * 2, (r - 16) * 2)

        # Value text
        painter.setPen(QColor("#ffffff"))
        val_str = f"{int(self._current)}"
        font = QFont("Segoe UI", max(10, r // 3))
        font.setBold(True)
        font.setWeight(QFont.Weight.Black)
        painter.setFont(font)
        painter.drawText(0, cy - r // 3, W, r // 2, Qt.AlignmentFlag.AlignCenter, val_str)

        # Unit
        painter.setPen(QColor("#5050a0"))
        font2 = QFont("Segoe UI", max(7, r // 6))
        font2.setBold(False)
        painter.setFont(font2)
        painter.drawText(0, cy + r // 8, W, r // 3, Qt.AlignmentFlag.AlignCenter, self._unit)

        # Label (colored to match arc)
        painter.setPen(arc_color if pct > 0.05 else QColor("#6060a0"))
        font3 = QFont("Segoe UI", max(8, r // 6))
        font3.setBold(True)
        painter.setFont(font3)
        painter.drawText(0, H - 28, W, 22, Qt.AlignmentFlag.AlignCenter, self._label)

        painter.end()


class AnimatedStatCard(QFrame):
    """Stat card with hover glow animation and left accent bar."""

    def __init__(self, title, value="—", color="#6c63ff", parent=None):
        super().__init__(parent)
        self._color = color
        self._glow = 0.0
        self._hover = False
        self.setFixedHeight(90)
        self.setObjectName("stat_card")

        # Hover animation timer
        self._htimer = QTimer()
        self._htimer.setInterval(16)
        self._htimer.timeout.connect(self._animate_hover)
        self._htimer.start()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 16, 12)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            "color: #5050a0; font-size: 10px; font-weight: 700; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"color: {color}; font-size: 19px; font-weight: 900; "
            "background: transparent; border: none;"
        )

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)

        self._update_style()

        # Left accent bar
        self._accent = QFrame(self)
        self._accent.setGeometry(0, 8, 3, 74)
        self._accent.setStyleSheet(f"background: {color}; border-radius: 2px;")

    def _animate_hover(self):
        target = 255.0 if self._hover else 0.0
        diff = target - self._glow
        if abs(diff) > 1.0:
            self._glow += diff * 0.15
            self._update_style()

    def _update_style(self):
        a = int(max(0, min(255, self._glow)))
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background: #111119;
                border: 1px solid rgba(108, 99, 255, {a});
                border-radius: 12px;
            }}
        """)

    def enterEvent(self, e):
        self._hover = True

    def leaveEvent(self, e):
        self._hover = False

    def update_value(self, v):
        self.value_lbl.setText(str(v))


class PerformanceChart(QWidget):
    """High-quality real-time line chart with filled gradient areas."""

    MAX_POINTS = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cpu_history = [0.0] * self.MAX_POINTS
        self.ram_history = [0.0] * self.MAX_POINTS
        self.setMinimumHeight(280)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def update_data(self, cpu_history: list, ram_history: list):
        self.cpu_history = list(cpu_history)[-self.MAX_POINTS:]
        while len(self.cpu_history) < self.MAX_POINTS:
            self.cpu_history.insert(0, 0.0)
        self.ram_history = list(ram_history)[-self.MAX_POINTS:]
        while len(self.ram_history) < self.MAX_POINTS:
            self.ram_history.insert(0, 0.0)
        self.update()

    def _make_points(self, history, pad_l, pad_r, pad_t, pad_b, W, H):
        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b
        pts = []
        for i, v in enumerate(history):
            x = pad_l + int(i * chart_w / (self.MAX_POINTS - 1))
            y = pad_t + int(chart_h * (1.0 - v / 100.0))
            pts.append((x, y))
        return pts

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing
        )

        W = self.width()
        H = self.height()
        pad_l, pad_r, pad_t, pad_b = 44, 20, 20, 36

        # Background
        painter.fillRect(self.rect(), QColor("#0c0c14"))

        # Grid lines (horizontal)
        grid_labels = ["100%", "75%", "50%", "25%", "0%"]
        for i in range(5):
            y = pad_t + i * (H - pad_t - pad_b) // 4
            # Grid line
            grid_pen = QPen(QColor("#1c1c2c"), 1, Qt.PenStyle.DashLine)
            painter.setPen(grid_pen)
            painter.drawLine(pad_l, y, W - pad_r, y)
            # Label
            painter.setPen(QColor("#3a3a6a"))
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(2, y - 7, 40, 14, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, grid_labels[i])

        # Vertical grid lines (time marks)
        for i in range(0, self.MAX_POINTS, 10):
            x = pad_l + int(i * (W - pad_l - pad_r) / (self.MAX_POINTS - 1))
            grid_pen2 = QPen(QColor("#161626"), 1, Qt.PenStyle.DotLine)
            painter.setPen(grid_pen2)
            painter.drawLine(x, pad_t, x, H - pad_b)

        def draw_series(history, line_color_hex, fill_color_hex):
            pts = self._make_points(history, pad_l, pad_r, pad_t, pad_b, W, H)
            if len(pts) < 2:
                return

            # Build path for the line
            path = QPainterPath()
            path.moveTo(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                # Smooth curve using cubic bezier
                x0, y0 = pts[i - 1]
                x1, y1 = pts[i]
                cx0 = x0 + (x1 - x0) * 0.5
                path.cubicTo(cx0, y0, cx0, y1, x1, y1)

            # Fill area under line with gradient
            fill_path = QPainterPath(path)
            fill_path.lineTo(pts[-1][0], H - pad_b)
            fill_path.lineTo(pts[0][0], H - pad_b)
            fill_path.closeSubpath()

            fill_grad = QLinearGradient(0, pad_t, 0, H - pad_b)
            fill_c = QColor(fill_color_hex)
            fill_c.setAlpha(70)
            fill_grad.setColorAt(0.0, fill_c)
            fill_c2 = QColor(fill_color_hex)
            fill_c2.setAlpha(0)
            fill_grad.setColorAt(1.0, fill_c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill_grad))
            painter.drawPath(fill_path)

            # Glow line (thicker, translucent)
            glow_pen = QPen(QColor(fill_color_hex), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            glow_c = QColor(fill_color_hex)
            glow_c.setAlpha(35)
            glow_pen.setColor(glow_c)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            # Main line
            line_pen = QPen(QColor(line_color_hex), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(line_pen)
            painter.drawPath(path)

            # Dot at latest value
            lx, ly = pts[-1]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(line_color_hex)))
            painter.drawEllipse(lx - 4, ly - 4, 8, 8)

        draw_series(self.cpu_history, "#6c63ff", "#6c63ff")
        draw_series(self.ram_history, "#00d4ff", "#00d4ff")

        # Bottom axis line
        axis_pen = QPen(QColor("#1e1e30"), 1)
        painter.setPen(axis_pen)
        painter.drawLine(pad_l, H - pad_b, W - pad_r, H - pad_b)

        # Legend
        legend_y = H - 22
        for label, color in [("CPU %", "#6c63ff"), ("RAM %", "#00d4ff")]:
            x_off = pad_l if label == "CPU %" else pad_l + 80
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x_off, legend_y, 16, 4, 2, 2)
            painter.setPen(QColor("#8080c0"))
            font2 = QFont("Segoe UI", 9)
            painter.setFont(font2)
            painter.drawText(x_off + 20, legend_y - 4, 60, 14, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

        painter.end()


class HealthScoreCard(QFrame):
    """Animated health score card with color-pulsing border."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._score = 0
        self._color = "#00ff88"
        self._pulse = 0.0
        self._pulse_dir = 1.0

        self._pulse_timer = QTimer()
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._do_pulse)
        self._pulse_timer.start()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(28)

        # Left side description
        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        title = QLabel("System Health Score")
        title.setStyleSheet("color: #e0e0ff; font-size: 16px; font-weight: 800; background: transparent; border: none;")

        desc = QLabel(
            "Overall performance rating based on CPU, RAM, and disk utilization.\n"
            "Higher is better — keep it above 70 for smooth operation."
        )
        desc.setStyleSheet("color: #4a4a7a; font-size: 12px; background: transparent; border: none;")
        desc.setWordWrap(True)

        left_col.addWidget(title)
        left_col.addWidget(desc)
        left_col.addStretch()

        # Right side: big score
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.score_lbl = QLabel("—")
        self.score_lbl.setStyleSheet(
            "color: #00ff88; font-size: 60px; font-weight: 900; min-width: 100px; "
            "background: transparent; border: none;"
        )
        self.score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rating_lbl = QLabel("Calculating...")
        self.rating_lbl.setStyleSheet(
            "color: #4a4a7a; font-size: 13px; font-weight: 600; "
            "background: transparent; border: none;"
        )
        self.rating_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_col.addWidget(self.score_lbl)
        right_col.addWidget(self.rating_lbl)

        layout.addLayout(left_col, 1)
        layout.addLayout(right_col)

    def _do_pulse(self):
        self._pulse += self._pulse_dir * 3.5
        if self._pulse >= 255:
            self._pulse = 255
            self._pulse_dir = -1.0
        elif self._pulse <= 80:
            self._pulse = 80
            self._pulse_dir = 1.0
        a = int(self._pulse)
        c = QColor(self._color)
        c.setAlpha(a)
        self.setStyleSheet(f"""
            QFrame#card {{
                background: #12121a;
                border: 1px solid rgba({c.red()}, {c.green()}, {c.blue()}, {a});
                border-radius: 12px;
            }}
        """)

    def update_score(self, score, color, rating):
        self._score = score
        self._color = color
        self.score_lbl.setText(str(score))
        self.score_lbl.setStyleSheet(
            f"color: {color}; font-size: 60px; font-weight: 900; min-width: 100px; "
            "background: transparent; border: none;"
        )
        self.rating_lbl.setText(rating)
        self.rating_lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700; "
            "background: transparent; border: none;"
        )


class DashboardPage(QWidget):
    """Main dashboard with animated gauges and live performance chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(22)

        # ── Dashboard Header ─────────────────────────────────────────────────
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        dash_title = QLabel("System Performance")
        dash_title.setStyleSheet(
            "color: #e0e0ff; font-size: 26px; font-weight: 900; "
            "letter-spacing: 0.5px; background: transparent;"
        )
        dash_sub = QLabel("Live metrics — updates every second")
        dash_sub.setStyleSheet("color: #3a3a6a; font-size: 12px; background: transparent;")
        title_col.addWidget(dash_title)
        title_col.addWidget(dash_sub)

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(
            "color: #4a4a7a; font-size: 13px; font-weight: 600; background: transparent;"
        )
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._update_clock()

        self._clock_timer = QTimer()
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()

        header_layout.addLayout(title_col)
        header_layout.addStretch()
        header_layout.addWidget(self._clock_lbl)
        layout.addWidget(header_widget)

        # ── Gauges row ───────────────────────────────────────────────────────
        gauges_card = QFrame()
        gauges_card.setObjectName("card")
        gauges_layout = QHBoxLayout(gauges_card)
        gauges_layout.setContentsMargins(24, 22, 24, 20)
        gauges_layout.setSpacing(0)

        self.cpu_gauge = AnimatedGauge(tr("cpu_usage"), "%")
        self.ram_gauge = AnimatedGauge(tr("ram_usage"), "%")
        self.temp_gauge = AnimatedGauge(tr("temperature"), "°C")
        self.disk_gauge = AnimatedGauge("Disk I/O", "MB/s")

        self.cpu_gauge.setMinimumSize(220, 230)
        self.ram_gauge.setMinimumSize(220, 230)
        self.temp_gauge.setMinimumSize(220, 230)
        self.disk_gauge.setMinimumSize(220, 230)

        gauges_layout.addStretch(1)
        for g in (self.cpu_gauge, self.ram_gauge, self.temp_gauge, self.disk_gauge):
            gauges_layout.addWidget(g)
            gauges_layout.addStretch(1)

        layout.addWidget(gauges_card)

        # ── Stat cards (3-column grid, 8 stats) ─────────────────────────────
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        stats_grid.setColumnStretch(0, 1)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(2, 1)

        self.stat_cpu_freq = AnimatedStatCard("CPU FREQUENCY", "— MHz", "#6c63ff")
        self.stat_ram_used = AnimatedStatCard("RAM USED", "— GB", "#00d4ff")
        self.stat_ram_free = AnimatedStatCard("RAM FREE", "— GB", "#00ff88")
        self.stat_cpu_temp = AnimatedStatCard("CPU TEMP", "—°C", "#ffaa00")
        self.stat_gpu_clock = AnimatedStatCard("GPU CLOCK", "— MHz", "#00d4ff")
        self.stat_gpu_temp = AnimatedStatCard("GPU TEMP", "—°C", "#ff6b6b")
        self.stat_disk_r = AnimatedStatCard("DISK READ", "— MB/s", "#a78bff")
        self.stat_disk_w = AnimatedStatCard("DISK WRITE", "— MB/s", "#ff6b6b")
        self.stat_net_in = AnimatedStatCard("NET DOWNLOAD", "— Mbps", "#00d4ff")
        self.stat_net_out = AnimatedStatCard("NET UPLOAD", "— Mbps", "#6c63ff")

        cards = [
            self.stat_cpu_freq, self.stat_cpu_temp, self.stat_gpu_clock,
            self.stat_gpu_temp, self.stat_ram_used, self.stat_ram_free,
            self.stat_disk_r, self.stat_disk_w,
            self.stat_net_in, self.stat_net_out,
        ]
        positions = [
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0), (2, 1), (2, 2),
            (3, 0),
        ]
        for card, (row, col) in zip(cards, positions):
            stats_grid.addWidget(card, row, col)

        layout.addLayout(stats_grid)

        # ── Performance chart ─────────────────────────────────────────────────
        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_card_layout = QVBoxLayout(chart_card)
        chart_card_layout.setContentsMargins(20, 16, 20, 16)
        chart_card_layout.setSpacing(10)

        chart_header = QHBoxLayout()
        chart_title = QLabel("⚡ Performance History")
        chart_title.setStyleSheet(
            "color: #e0e0ff; font-size: 14px; font-weight: 700; background: transparent;"
        )
        chart_sub = QLabel("Last 60 seconds")
        chart_sub.setStyleSheet(
            "color: #3a3a6a; font-size: 11px; background: transparent;"
        )
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_header.addWidget(chart_sub)
        chart_card_layout.addLayout(chart_header)

        self.perf_chart = PerformanceChart()
        self.perf_chart.setMinimumHeight(280)
        chart_card_layout.addWidget(self.perf_chart)

        layout.addWidget(chart_card)

        # ── System Health Score ───────────────────────────────────────────────
        self.health_card = HealthScoreCard()
        layout.addWidget(self.health_card)

        layout.addStretch()

    def _update_clock(self):
        dt = QDateTime.currentDateTime()
        self._clock_lbl.setText(dt.toString("dddd, MMMM d  •  hh:mm:ss"))

    @pyqtSlot(dict)
    def update_stats(self, stats: dict):
        """Called by the monitor thread with fresh stats."""
        cpu = stats.get("cpu_percent", 0)
        ram = stats.get("ram_percent", 0)
        temp = stats.get("cpu_temp_c")
        disk_r = stats.get("disk_read_mbps", 0)

        self.cpu_gauge.setValue(cpu)
        self.ram_gauge.setValue(ram)

        if temp is not None:
            self.temp_gauge.setValue(min(temp, 100))
            self.stat_cpu_temp.update_value(f"{temp:.0f}°C")
        else:
            self.temp_gauge.setValue(0)
            self.stat_cpu_temp.update_value("— (Sıcaklık için LibreHardwareMonitor kur)")

        # GPU clock
        gpu_clock = stats.get("gpu_clock_mhz")
        if gpu_clock is not None:
            self.stat_gpu_clock.update_value(f"{gpu_clock} MHz")
        else:
            self.stat_gpu_clock.update_value("N/A")

        # GPU temp
        gpu_temp = stats.get("gpu_temp_c")
        if gpu_temp is not None:
            self.stat_gpu_temp.update_value(f"{gpu_temp:.0f}°C")
        else:
            self.stat_gpu_temp.update_value("N/A")

        # Normalize disk read: 0-200MB/s → 0-100%
        disk_pct = min(disk_r / 2, 100)
        self.disk_gauge.setValue(disk_pct)

        self.stat_cpu_freq.update_value(f"{stats.get('cpu_freq_mhz', 0)} MHz")
        self.stat_ram_used.update_value(f"{stats.get('ram_used_gb', 0):.1f} GB")
        ram_total = stats.get("ram_total_gb", 0)
        ram_used = stats.get("ram_used_gb", 0)
        self.stat_ram_free.update_value(f"{ram_total - ram_used:.1f} GB")
        self.stat_disk_r.update_value(f"{stats.get('disk_read_mbps', 0):.1f} MB/s")
        self.stat_disk_w.update_value(f"{stats.get('disk_write_mbps', 0):.1f} MB/s")
        self.stat_net_in.update_value(f"{stats.get('net_recv_mbps', 0):.2f} Mbps")
        self.stat_net_out.update_value(f"{stats.get('net_sent_mbps', 0):.2f} Mbps")

        cpu_hist = stats.get("cpu_history", [])
        ram_hist = stats.get("ram_history", [])
        if cpu_hist:
            self.perf_chart.update_data(cpu_hist, ram_hist)

        # Health score
        score = max(0, int(100 - (cpu * 0.4) - (ram * 0.4) - (disk_pct * 0.2)))
        if score >= 80:
            color, rating = "#00ff88", "✦ Excellent"
        elif score >= 60:
            color, rating = "#ffaa00", "▲ Good"
        elif score >= 40:
            color, rating = "#ff8800", "▼ Fair"
        else:
            color, rating = "#ff4444", "✖ Poor"
        self.health_card.update_score(score, color, rating)
