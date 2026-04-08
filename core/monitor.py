"""
SRK Boost - Real-time System Monitor
Provides live CPU, RAM, and temperature monitoring via a QThread worker.
"""

import logging
import time
from collections import deque
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, QObject

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

logger = logging.getLogger(__name__)

HISTORY_LEN = 60  # seconds of history


class MonitorWorker(QObject):
    """Background worker that emits system stats every second."""

    stats_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self.interval_ms = interval_ms
        self._running = False
        self.cpu_history = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self.ram_history = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self._wmi = None

    def _get_wmi(self):
        if not WMI_AVAILABLE:
            return None
        if self._wmi is None:
            try:
                self._wmi = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            except Exception:
                try:
                    self._wmi = wmi.WMI()
                except Exception as e:
                    logger.warning(f"WMI monitor init failed: {e}")
        return self._wmi

    def start_monitoring(self):
        """Main loop — runs in a QThread."""
        self._running = True
        # Prime psutil CPU measurement
        if PSUTIL_AVAILABLE:
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass

        while self._running:
            try:
                stats = self._collect()
                self.cpu_history.append(stats.get("cpu_percent", 0))
                self.ram_history.append(stats.get("ram_percent", 0))
                stats["cpu_history"] = list(self.cpu_history)
                stats["ram_history"] = list(self.ram_history)
                self.stats_updated.emit(stats)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                self.error_occurred.emit(str(e))
            time.sleep(self.interval_ms / 1000)

    def stop(self):
        self._running = False

    def _collect(self) -> dict:
        stats = {
            "cpu_percent": 0.0,
            "cpu_freq_mhz": 0,
            "cpu_temp_c": None,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "gpu_percent": None,
            "gpu_temp_c": None,
            "gpu_clock_mhz": None,
            "disk_read_mbps": 0.0,
            "disk_write_mbps": 0.0,
            "net_sent_mbps": 0.0,
            "net_recv_mbps": 0.0,
        }

        if not PSUTIL_AVAILABLE:
            return stats

        try:
            stats["cpu_percent"] = psutil.cpu_percent(interval=None)
        except Exception:
            pass

        try:
            freq = psutil.cpu_freq()
            if freq:
                stats["cpu_freq_mhz"] = round(freq.current)
        except Exception:
            pass

        try:
            mem = psutil.virtual_memory()
            stats["ram_percent"] = mem.percent
            stats["ram_used_gb"] = round(mem.used / (1024 ** 3), 1)
            stats["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        except Exception:
            pass

        # CPU Temperature — WMI (Windows) önce, psutil fallback
        try:
            wmi_obj = self._get_wmi()
            if wmi_obj:
                # OpenHardwareMonitor namespace dene
                try:
                    ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                    for sensor in ohm.Sensor():
                        if sensor.SensorType == "Temperature" and "CPU" in (sensor.Name or ""):
                            stats["cpu_temp_c"] = round(float(sensor.Value), 1)
                            break
                except Exception:
                    pass
                # OHM çalışmadıysa MSAcpi_ThermalZoneTemperature dene
                if stats["cpu_temp_c"] is None:
                    try:
                        w2 = wmi.WMI(namespace="root\\wmi")
                        for t in w2.MSAcpi_ThermalZoneTemperature():
                            kelvin = t.CurrentTemperature
                            stats["cpu_temp_c"] = round(kelvin / 10.0 - 273.15, 1)
                            break
                    except Exception:
                        pass
        except Exception:
            pass
        # psutil fallback (Linux/Mac)
        if stats["cpu_temp_c"] is None:
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                        if key in temps and temps[key]:
                            stats["cpu_temp_c"] = round(temps[key][0].current, 1)
                            break
            except Exception:
                pass

        # GPU clock + temperature via WMI / OpenHardwareMonitor
        try:
            wmi_obj = self._get_wmi()
            if wmi_obj:
                # OpenHardwareMonitor GPU verileri
                try:
                    ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                    gpu_clock = None
                    gpu_temp = None
                    gpu_load = None
                    for sensor in ohm.Sensor():
                        stype = sensor.SensorType or ""
                        sname = sensor.Name or ""
                        sparent = sensor.Parent or ""
                        # GPU kontrolü
                        if any(k in sparent.lower() for k in ("gpu", "nvidia", "amd", "radeon", "geforce")):
                            if stype == "Clock" and "GPU Core" in sname and gpu_clock is None:
                                gpu_clock = round(float(sensor.Value))
                            elif stype == "Temperature" and gpu_temp is None:
                                gpu_temp = round(float(sensor.Value), 1)
                            elif stype == "Load" and "GPU Core" in sname and gpu_load is None:
                                gpu_load = round(float(sensor.Value), 1)
                    if gpu_clock is not None:
                        stats["gpu_clock_mhz"] = gpu_clock
                    if gpu_temp is not None:
                        stats["gpu_temp_c"] = gpu_temp
                    if gpu_load is not None:
                        stats["gpu_percent"] = gpu_load
                except Exception:
                    pass
        except Exception:
            pass

        # Disk I/O (delta)
        try:
            if not hasattr(self, "_last_disk_io"):
                self._last_disk_io = psutil.disk_io_counters()
                self._last_disk_time = time.time()
            else:
                now_io = psutil.disk_io_counters()
                now_time = time.time()
                dt = max(now_time - self._last_disk_time, 0.001)
                stats["disk_read_mbps"] = round(
                    (now_io.read_bytes - self._last_disk_io.read_bytes) / dt / (1024 ** 2), 2
                )
                stats["disk_write_mbps"] = round(
                    (now_io.write_bytes - self._last_disk_io.write_bytes) / dt / (1024 ** 2), 2
                )
                self._last_disk_io = now_io
                self._last_disk_time = now_time
        except Exception:
            pass

        # Network I/O (delta)
        try:
            if not hasattr(self, "_last_net_io"):
                self._last_net_io = psutil.net_io_counters()
                self._last_net_time = time.time()
            else:
                now_net = psutil.net_io_counters()
                now_time = time.time()
                dt = max(now_time - self._last_net_time, 0.001)
                stats["net_sent_mbps"] = round(
                    (now_net.bytes_sent - self._last_net_io.bytes_sent) / dt / (1024 ** 2), 3
                )
                stats["net_recv_mbps"] = round(
                    (now_net.bytes_recv - self._last_net_io.bytes_recv) / dt / (1024 ** 2), 3
                )
                self._last_net_io = now_net
                self._last_net_time = now_time
        except Exception:
            pass

        return stats


class SystemMonitor:
    """High-level monitor that manages the background QThread."""

    def __init__(self, interval_ms: int = 1000):
        self.worker = MonitorWorker(interval_ms)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start_monitoring)

    def start(self):
        if not self.thread.isRunning():
            self.thread.start()

    def stop(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait(3000)

    @property
    def stats_updated(self):
        return self.worker.stats_updated
