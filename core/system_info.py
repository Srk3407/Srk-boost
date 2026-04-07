"""
SRK Boost - System Information Module
Collects hardware and system information using psutil, platform, and subprocess.
"""

import platform
import subprocess
import logging
import os
import sys
from typing import Dict, Any, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
    _wmi_instance = None
except ImportError:
    WMI_AVAILABLE = False
    _wmi_instance = None

logger = logging.getLogger(__name__)


def get_wmi():
    """Get or create WMI instance (Windows only)."""
    global _wmi_instance
    if not WMI_AVAILABLE:
        return None
    if _wmi_instance is None:
        try:
            _wmi_instance = wmi.WMI()
        except Exception as e:
            logger.error(f"Failed to initialize WMI: {e}")
            return None
    return _wmi_instance


class SystemInfo:
    """Provides comprehensive system hardware information."""

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information."""
        info = {
            "name": "Unknown CPU",
            "cores": 0,
            "threads": 0,
            "base_freq_mhz": 0,
            "max_freq_mhz": 0,
            "architecture": platform.machine(),
        }

        # Try WMI first (Windows)
        if WMI_AVAILABLE:
            try:
                w = get_wmi()
                if w:
                    for cpu in w.Win32_Processor():
                        info["name"] = cpu.Name.strip()
                        info["cores"] = cpu.NumberOfCores or 0
                        info["threads"] = cpu.NumberOfLogicalProcessors or 0
                        info["base_freq_mhz"] = cpu.MaxClockSpeed or 0
                        break
            except Exception as e:
                logger.warning(f"WMI CPU info failed: {e}")

        # Fallback with psutil
        if PSUTIL_AVAILABLE:
            try:
                if info["cores"] == 0:
                    info["cores"] = psutil.cpu_count(logical=False) or 0
                if info["threads"] == 0:
                    info["threads"] = psutil.cpu_count(logical=True) or 0
                freq = psutil.cpu_freq()
                if freq:
                    info["max_freq_mhz"] = round(freq.max) if freq.max else round(freq.current)
                    if info["base_freq_mhz"] == 0:
                        info["base_freq_mhz"] = round(freq.current)
            except Exception as e:
                logger.warning(f"psutil CPU info failed: {e}")

        # Fallback name from platform
        if info["name"] == "Unknown CPU":
            info["name"] = platform.processor() or "Unknown CPU"

        return info

    @staticmethod
    def get_ram_info() -> Dict[str, Any]:
        """Get RAM information."""
        info = {
            "total_gb": 0,
            "available_gb": 0,
            "used_gb": 0,
            "percent": 0,
            "speed_mhz": "Unknown",
            "type": "Unknown",
            "slots": [],
        }

        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                info["total_gb"] = round(mem.total / (1024 ** 3), 1)
                info["available_gb"] = round(mem.available / (1024 ** 3), 1)
                info["used_gb"] = round(mem.used / (1024 ** 3), 1)
                info["percent"] = mem.percent
            except Exception as e:
                logger.warning(f"psutil RAM info failed: {e}")

        if WMI_AVAILABLE:
            try:
                w = get_wmi()
                if w:
                    for stick in w.Win32_PhysicalMemory():
                        speed = stick.Speed or 0
                        mem_type = stick.MemoryType or 0
                        type_map = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}
                        info["type"] = type_map.get(mem_type, "DDR4")
                        info["speed_mhz"] = f"{speed} MHz" if speed else "Unknown"
                        cap = int(stick.Capacity or 0)
                        info["slots"].append({
                            "capacity_gb": round(cap / (1024 ** 3), 1),
                            "speed": speed,
                            "type": info["type"],
                        })
            except Exception as e:
                logger.warning(f"WMI RAM info failed: {e}")

        return info

    @staticmethod
    def get_gpu_info() -> List[Dict[str, Any]]:
        """Get GPU information."""
        gpus = []

        if WMI_AVAILABLE:
            try:
                w = get_wmi()
                if w:
                    for gpu in w.Win32_VideoController():
                        vram = int(gpu.AdapterRAM or 0)
                        gpus.append({
                            "name": gpu.Name or "Unknown GPU",
                            "vram_gb": round(vram / (1024 ** 3), 1) if vram > 0 else 0,
                            "driver_version": gpu.DriverVersion or "Unknown",
                            "resolution": f"{gpu.CurrentHorizontalResolution or 0}x{gpu.CurrentVerticalResolution or 0}",
                            "refresh_rate": f"{gpu.CurrentRefreshRate or 0}Hz",
                        })
            except Exception as e:
                logger.warning(f"WMI GPU info failed: {e}")

        if not gpus:
            gpus.append({
                "name": "GPU Info Unavailable",
                "vram_gb": 0,
                "driver_version": "Unknown",
                "resolution": "Unknown",
                "refresh_rate": "Unknown",
            })

        return gpus

    @staticmethod
    def get_storage_info() -> List[Dict[str, Any]]:
        """Get storage/disk information."""
        drives = []

        if PSUTIL_AVAILABLE:
            try:
                for partition in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        drive_type = "Unknown"
                        if WMI_AVAILABLE:
                            try:
                                w = get_wmi()
                                if w:
                                    for disk in w.Win32_DiskDrive():
                                        media = (disk.MediaType or "").lower()
                                        if "solid" in media or "ssd" in media:
                                            drive_type = "SSD"
                                        elif "fixed" in media or "external" in media:
                                            drive_type = "HDD"
                                        else:
                                            drive_type = "HDD"
                                        break
                            except:
                                drive_type = "Drive"

                        drives.append({
                            "mountpoint": partition.mountpoint,
                            "device": partition.device,
                            "fstype": partition.fstype,
                            "total_gb": round(usage.total / (1024 ** 3), 1),
                            "used_gb": round(usage.used / (1024 ** 3), 1),
                            "free_gb": round(usage.free / (1024 ** 3), 1),
                            "percent": usage.percent,
                            "type": drive_type,
                        })
                    except PermissionError:
                        continue
            except Exception as e:
                logger.warning(f"Storage info failed: {e}")

        return drives

    @staticmethod
    def get_motherboard_info() -> Dict[str, Any]:
        """Get motherboard information."""
        info = {"manufacturer": "Unknown", "product": "Unknown", "version": "Unknown"}

        if WMI_AVAILABLE:
            try:
                w = get_wmi()
                if w:
                    for board in w.Win32_BaseBoard():
                        info["manufacturer"] = board.Manufacturer or "Unknown"
                        info["product"] = board.Product or "Unknown"
                        info["version"] = board.Version or "Unknown"
                        break
            except Exception as e:
                logger.warning(f"Motherboard info failed: {e}")

        return info

    @staticmethod
    def get_os_info() -> Dict[str, Any]:
        """Get OS information."""
        return {
            "name": platform.system(),
            "version": platform.version(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

    @staticmethod
    def get_network_info() -> List[Dict[str, Any]]:
        """Get network adapter information."""
        adapters = []
        if PSUTIL_AVAILABLE:
            try:
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                for name, addr_list in addrs.items():
                    stat = stats.get(name)
                    ipv4 = next((a.address for a in addr_list if a.family.name == "AF_INET"), "N/A")
                    adapters.append({
                        "name": name,
                        "ipv4": ipv4,
                        "speed_mbps": stat.speed if stat else 0,
                        "is_up": stat.isup if stat else False,
                    })
            except Exception as e:
                logger.warning(f"Network info failed: {e}")
        return adapters

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all system information at once."""
        return {
            "cpu": SystemInfo.get_cpu_info(),
            "ram": SystemInfo.get_ram_info(),
            "gpus": SystemInfo.get_gpu_info(),
            "storage": SystemInfo.get_storage_info(),
            "motherboard": SystemInfo.get_motherboard_info(),
            "os": SystemInfo.get_os_info(),
            "network": SystemInfo.get_network_info(),
        }
