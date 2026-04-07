"""
SRK Boost - Benchmark Page
Before/After performance comparison. CPU + RAM stress test with score.
"""

import time
import math
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

logger = logging.getLogger(__name__)


def _run_cpu_benchmark(duration_sec: float = 3.0) -> float:
    """Pure Python CPU benchmark. Returns operations per second (normalized 0-100)."""
    ops = 0
    end_time = time.perf_counter() + duration_sec
    while time.perf_counter() < end_time:
        # Mixed workload: float math + integer ops
        x = 1.0
        for _ in range(500):
            x = math.sqrt(x * 1.0000001 + 0.5)
            x = math.sin(x) * math.cos(x)
        ops += 500
    score = min(100, ops / duration_sec / 50000 * 100)
    return round(score, 1)


def _run_memory_benchmark(size_mb: int = 64) -> float:
    """Memory bandwidth test. Returns score 0-100."""
    try:
        start = time.perf_counter()
        data = bytearray(size_mb * 1024 * 1024)
        for i in range(0, len(data), 4096):
            data[i] = (data[i] + 1) & 0xFF
        elapsed = time.perf_counter() - start
        # Faster = higher score. Target: 64MB in < 0.3s = 100
        score = min(100, max(0, (0.6 - elapsed) / 0.6 * 100))
        del data
        return round(score, 1)
    except Exception:
        return 50.0


class BenchmarkWorker(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict)

    def __init__(self, label: str = "run"):
        super().__init__()
        self.label = label

    def run(self):
        self.progress.emit(10, "Starting CPU benchmark...")
        cpu_score = _run_cpu_benchmark(3.0)
        self.progress.emit(60, "Running memory benchmark...")
        mem_score = _run_memory_benchmark(64)
        self.progress.emit(85, "Collecting system stats...")

        try:
            import psutil
            cpu_freq = psutil.cpu_freq()
            freq_mhz = cpu_freq.current if cpu_freq else 0
            ram = psutil.virtual_memory()
            ram_free_gb = ram.available / (1024 ** 3)
            cpu_cores = psutil.cpu_count(logical=False) or 1
            cpu_logical = psutil.cpu_count(logical=True) or 1
        except Exception:
            freq_mhz = 0
            ram_free_gb = 0
            cpu_cores = 1
            cpu_logical = 1

        # Composite score
        composite = round((cpu_score * 0.6 + mem_score * 0.4), 1)

        self.progress.emit(100, "Done!")
        self.result.emit({
            "label": self.label,
            "cpu_score": cpu_score,
            "mem_score": mem_score,
            "composite": composite,
            "freq_mhz": round(freq_mhz),
            "ram_free_gb": round(ram_free_gb, 1),
            "cpu_cores": cpu_cores,
            "cpu_logical": cpu_logical,
        })


class ScoreRing(QWidget):
    """Animated circular score display."""

    def __init__(self, title: str, color: str = "#6c63ff", parent=None):
        super().__init__(parent)
        self._title = title
        self._color = color
        self._score = 0.0
        self._displayed = 0.0
        self.setFixedSize(160, 175)

        from PyQt6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def set_score(self, v: float):
        self._score = max(0, min(100, v))

    def _animate(self):
        diff = self._score - self._displayed
        if abs(diff) > 0.3:
            self._displayed += diff * 0.1
            self.update()

    def paintEvent(self, event):
        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2 - 10
        r = min(W, H) // 2 - 16

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pct = self._displayed / 100.0

        # Track
        track_pen = QPen(QColor("#1e1e2e"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, -270 * 16)

        # Arc
        c = QColor(self._color)
        arc_pen = QPen(c, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, int(-270 * 16 * pct))

        # Score text
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 22, QFont.Weight.Black)
        painter.setFont(font)
        painter.drawText(0, cy - r // 2, W, r, Qt.AlignmentFlag.AlignCenter, f"{int(self._displayed)}")

        # /100
        painter.setPen(QColor("#3a3a6a"))
        font2 = QFont("Segoe UI", 9)
        painter.setFont(font2)
        painter.drawText(0, cy + r // 4, W, r // 2, Qt.AlignmentFlag.AlignCenter, "/100")

        # Title
        painter.setPen(QColor(self._color))
        font3 = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font3)
        painter.drawText(0, H - 24, W, 20, Qt.AlignmentFlag.AlignCenter, self._title)

        painter.end()


class ComparisonBar(QFrame):
    """Shows before/after score with a visual bar."""

    def __init__(self, label: str, before: float, after: float, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel(label)
        title.setStyleSheet(
            "color: rgba(180,170,255,0.7); font-size: 10px; font-weight: 700; "
            "letter-spacing: 1.5px; background: transparent;"
        )
        layout.addWidget(title)

        row = QHBoxLayout()

        before_lbl = QLabel(f"{before:.0f}")
        before_lbl.setStyleSheet(
            "color: #6060a0; font-size: 26px; font-weight: 900; background: transparent;"
        )
        before_lbl.setFixedWidth(60)
        row.addWidget(before_lbl)

        bar_col = QVBoxLayout()
        bar_col.setSpacing(4)

        before_bar = QProgressBar()
        before_bar.setRange(0, 100)
        before_bar.setValue(int(before))
        before_bar.setFixedHeight(8)
        before_bar.setStyleSheet("""
            QProgressBar { background: #1e1e2e; border: none; border-radius: 4px; }
            QProgressBar::chunk { background: #3a3a6a; border-radius: 4px; }
        """)
        bar_col.addWidget(before_bar)

        after_bar = QProgressBar()
        after_bar.setRange(0, 100)
        after_bar.setValue(int(after))
        after_bar.setFixedHeight(8)
        after_bar.setStyleSheet(f"""
            QProgressBar {{ background: #1e1e2e; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}
        """)
        bar_col.addWidget(after_bar)

        row.addLayout(bar_col, 1)

        after_lbl = QLabel(f"{after:.0f}")
        after_lbl.setStyleSheet(
            f"color: {color}; font-size: 26px; font-weight: 900; background: transparent;"
        )
        after_lbl.setFixedWidth(60)
        after_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(after_lbl)

        layout.addLayout(row)

        # Delta
        delta = after - before
        delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        delta_color = "#00e87a" if delta > 0 else "#ff5555" if delta < 0 else "#6060a0"
        delta_lbl = QLabel(f"{delta_str} points  {'▲ Improved' if delta > 0 else '▼ Reduced' if delta < 0 else '— No change'}")
        delta_lbl.setStyleSheet(
            f"color: {delta_color}; font-size: 11px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(delta_lbl)


class BenchmarkPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._before: dict = {}
        self._after: dict = {}
        self._worker = None
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

        # Header
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(3)
        t = QLabel("📊  Benchmark")
        t.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 900; background: transparent;")
        s = QLabel("Compare performance before and after optimization")
        s.setStyleSheet("color: #3a3a6a; font-size: 12px; background: transparent;")
        left.addWidget(t)
        left.addWidget(s)
        hdr.addLayout(left)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Info card
        info = QFrame()
        info.setObjectName("card")
        info_l = QHBoxLayout(info)
        info_l.setContentsMargins(20, 16, 20, 16)
        info_lbl = QLabel(
            "📌  <b>How to use:</b>  Run <b>Before</b> benchmark first → apply tweaks → run <b>After</b> benchmark → compare."
        )
        info_lbl.setStyleSheet("color: #8080c0; font-size: 12px; background: transparent;")
        info_lbl.setWordWrap(True)
        info_l.addWidget(info_lbl)
        layout.addWidget(info)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.before_btn = QPushButton("▶  Run BEFORE Benchmark")
        self.before_btn.setObjectName("secondary_btn")
        self.before_btn.setFixedHeight(42)
        self.before_btn.clicked.connect(lambda: self._start_bench("before"))

        self.after_btn = QPushButton("▶  Run AFTER Benchmark")
        self.after_btn.setObjectName("primary_btn")
        self.after_btn.setFixedHeight(42)
        self.after_btn.setEnabled(False)
        self.after_btn.clicked.connect(lambda: self._start_bench("after"))

        btn_row.addWidget(self.before_btn)
        btn_row.addWidget(self.after_btn)
        layout.addLayout(btn_row)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #6c63ff; font-size: 12px; background: transparent;")
        self.status_lbl.setVisible(False)
        layout.addWidget(self.status_lbl)

        # Score rings
        scores_frame = QFrame()
        scores_frame.setObjectName("card")
        scores_layout = QHBoxLayout(scores_frame)
        scores_layout.setContentsMargins(30, 24, 30, 24)
        scores_layout.setSpacing(0)

        self.cpu_ring_before = ScoreRing("CPU BEFORE", "#6060a0")
        self.cpu_ring_after  = ScoreRing("CPU AFTER",  "#6c63ff")
        self.mem_ring_before = ScoreRing("MEM BEFORE", "#6060a0")
        self.mem_ring_after  = ScoreRing("MEM AFTER",  "#00d4ff")
        self.comp_ring_before = ScoreRing("TOTAL BEFORE", "#6060a0")
        self.comp_ring_after  = ScoreRing("TOTAL AFTER",  "#00e87a")

        for ring in [
            self.cpu_ring_before, self.cpu_ring_after,
            self.mem_ring_before, self.mem_ring_after,
            self.comp_ring_before, self.comp_ring_after,
        ]:
            scores_layout.addWidget(ring)
            scores_layout.addStretch(1)

        layout.addWidget(scores_frame)

        # Comparison bars (hidden until both runs done)
        self.comparison_frame = QFrame()
        self.comparison_frame.setVisible(False)
        self.comparison_layout = QVBoxLayout(self.comparison_frame)
        self.comparison_layout.setContentsMargins(0, 0, 0, 0)
        self.comparison_layout.setSpacing(12)

        comp_title = QLabel("📈  Before vs After Comparison")
        comp_title.setStyleSheet(
            "color: #e0e0ff; font-size: 16px; font-weight: 800; background: transparent;"
        )
        self.comparison_layout.addWidget(comp_title)

        self.comparison_cards_layout = QVBoxLayout()
        self.comparison_layout.addLayout(self.comparison_cards_layout)

        layout.addWidget(self.comparison_frame)
        layout.addStretch()

    def _start_bench(self, label: str):
        if self._worker and self._worker.isRunning():
            return

        self.before_btn.setEnabled(False)
        self.after_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setVisible(True)
        self.status_lbl.setText("Benchmarking... please wait")

        self._worker = BenchmarkWorker(label)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.start()

    def _on_progress(self, v: int, msg: str):
        self.progress_bar.setValue(v)
        self.status_lbl.setText(msg)

    def _on_result(self, data: dict):
        label = data["label"]

        if label == "before":
            self._before = data
            self.cpu_ring_before.set_score(data["cpu_score"])
            self.mem_ring_before.set_score(data["mem_score"])
            self.comp_ring_before.set_score(data["composite"])
            self.status_lbl.setText(
                f"✅ Before benchmark done — Score: {data['composite']}/100"
            )
            self.status_lbl.setStyleSheet(
                "color: #00e87a; font-size: 12px; background: transparent;"
            )
            self.after_btn.setEnabled(True)
        else:
            self._after = data
            self.cpu_ring_after.set_score(data["cpu_score"])
            self.mem_ring_after.set_score(data["mem_score"])
            self.comp_ring_after.set_score(data["composite"])
            self.status_lbl.setText(
                f"✅ After benchmark done — Score: {data['composite']}/100"
            )
            self.status_lbl.setStyleSheet(
                "color: #00e87a; font-size: 12px; background: transparent;"
            )
            self._show_comparison()

        self.before_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def _show_comparison(self):
        # Clear old cards
        while self.comparison_cards_layout.count():
            item = self.comparison_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._before or not self._after:
            return

        b, a = self._before, self._after

        self.comparison_cards_layout.addWidget(
            ComparisonBar("CPU SCORE", b["cpu_score"], a["cpu_score"], "#6c63ff")
        )
        self.comparison_cards_layout.addWidget(
            ComparisonBar("MEMORY SCORE", b["mem_score"], a["mem_score"], "#00d4ff")
        )
        self.comparison_cards_layout.addWidget(
            ComparisonBar("COMPOSITE SCORE", b["composite"], a["composite"], "#00e87a")
        )

        self.comparison_frame.setVisible(True)
