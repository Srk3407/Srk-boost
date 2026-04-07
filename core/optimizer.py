"""
SRK Boost - System Optimizer
Applies FPS/performance tweaks to Windows.
"""

import subprocess
import logging
import os
import sys
from typing import Callable, List, Tuple

logger = logging.getLogger(__name__)

# Each tweak: (display_name, function_name)
ALL_TWEAKS: List[Tuple[str, str]] = [
    ("Set Power Plan to High Performance", "set_high_performance_power_plan"),
    ("Disable Xbox Game Bar & Game DVR", "disable_game_bar"),
    ("Disable SysMain (Superfetch)", "disable_sysmain"),
    ("Disable DiagTrack (Telemetry)", "disable_diagtrack"),
    ("Disable MapsBroker Service", "disable_mapbroker"),
    ("Optimize Visual Effects for Performance", "optimize_visual_effects"),
    ("Disable GPU Hardware Scheduling (Legacy Mode)", "set_gpu_max_performance"),
    ("Disable Search Indexing", "disable_search_indexing"),
    ("Disable Network Throttling", "disable_network_throttling"),
    ("Disable Mouse Acceleration", "disable_mouse_acceleration"),
    ("Clear Standby Memory", "clear_standby_memory"),
    ("Disable CPU Core Parking", "disable_cpu_core_parking"),
    ("Reduce DPC Latency", "disable_dpc_latency"),
    ("Optimize Network Latency (TCP)", "optimize_network_latency"),
    ("Disable Multi-Plane Overlay (MPO)", "disable_mpo"),
    ("Optimize Windows Timer Resolution", "set_timer_resolution"),
    ("Disable Fullscreen Optimizations", "disable_fullscreen_optimizations"),
    ("Maximize CPU Foreground Priority", "set_win32_priority_separation"),
    ("Set GPU Priority to Maximum", "set_gpu_priority"),
    ("Enable Hardware Accelerated GPU Scheduling (HAGS)", "enable_hags"),
    ("Pause Windows Defender During Gaming", "disable_windows_defender_gaming"),
    ("Maximize CPU Responsiveness", "set_cpu_responsiveness"),
]


# ── Core helpers ──────────────────────────────────────────────────────────────

# Windows: suppress console window for subprocess calls
_CREATION_FLAGS = 0
if sys.platform == "win32":
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]


def _run(cmd: List[str], timeout: int = 10) -> Tuple[bool, str]:
    """Run a subprocess command without showing a console window."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            encoding="utf-8",
            errors="replace",
            creationflags=_CREATION_FLAGS,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError as e:
        return False, f"Command not found: {e}"
    except Exception as e:
        return False, str(e)


def _reg_add(key: str, name: str, value: str, reg_type: str = "REG_DWORD") -> Tuple[bool, str]:
    return _run(["reg", "add", key, "/v", name, "/t", reg_type, "/d", value, "/f"])


def _set_reg(key: str, name: str, value: str, reg_type: str = "REG_DWORD") -> Tuple[bool, str]:
    """Alias for _reg_add — used throughout for consistency."""
    return _reg_add(key, name, value, reg_type)


# ── Tweak functions ───────────────────────────────────────────────────────────

def set_high_performance_power_plan() -> Tuple[bool, str]:
    ok, out = _run(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
    if ok:
        return True, "Power plan set to High Performance"
    # Try listing and finding it
    ok2, out2 = _run(["powercfg", "/list"])
    if ok2:
        for line in out2.splitlines():
            if "High Performance" in line or "8c5e7fda" in line.lower():
                parts = line.split()
                for part in parts:
                    if len(part) == 36 and part.count("-") == 4:
                        ok3, _ = _run(["powercfg", "/setactive", part])
                        if ok3:
                            return True, "Power plan set to High Performance"
    return False, f"Could not set High Performance power plan: {out}"


def disable_game_bar() -> Tuple[bool, str]:
    key = r"HKCU\Software\Microsoft\GameBar"
    ok1, _ = _reg_add(key, "UseNexusForGameBarEnabled", "0")
    ok2, _ = _reg_add(key, "AllowAutoGameMode", "0")
    ok3, _ = _reg_add(r"HKCU\System\GameConfigStore", "GameDVR_Enabled", "0")
    ok4, _ = _reg_add(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR",
        "AllowGameDVR", "0"
    )
    all_ok = ok1 and ok2 and ok3 and ok4
    return all_ok, "Xbox Game Bar and Game DVR disabled" if all_ok else "Partial: some Game Bar tweaks applied"


def disable_sysmain() -> Tuple[bool, str]:
    _run(["sc", "stop", "SysMain"])
    ok, out = _run(["sc", "config", "SysMain", "start=", "disabled"])
    if ok:
        return True, "SysMain (Superfetch) stopped and disabled"
    return False, f"SysMain: {out}"


def disable_diagtrack() -> Tuple[bool, str]:
    _run(["sc", "stop", "DiagTrack"])
    ok, out = _run(["sc", "config", "DiagTrack", "start=", "disabled"])
    if ok:
        return True, "DiagTrack (Telemetry) disabled"
    return False, f"DiagTrack: {out}"


def disable_mapbroker() -> Tuple[bool, str]:
    _run(["sc", "stop", "MapsBroker"])
    ok, out = _run(["sc", "config", "MapsBroker", "start=", "disabled"])
    if ok:
        return True, "MapsBroker disabled"
    return False, f"MapsBroker: {out}"


def optimize_visual_effects() -> Tuple[bool, str]:
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    ok1, _ = _reg_add(key, "VisualFXSetting", "2")  # 2 = Best Performance
    ok2, _ = _reg_add(
        r"HKCU\Control Panel\Desktop", "UserPreferencesMask",
        "9012078010000000", "REG_BINARY"
    )
    ok3, _ = _reg_add(r"HKCU\Control Panel\Desktop", "FontSmoothing", "0", "REG_SZ")
    if ok1:
        return True, "Visual effects optimized for best performance"
    return False, "Could not optimize visual effects"


def set_gpu_max_performance() -> Tuple[bool, str]:
    """Try common GPU subkeys 0000-0003 to cover all GPU configs."""
    base = r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    any_ok = False
    for i in range(4):
        key = f"{base}\\{i:04d}"
        ok, _ = _reg_add(key, "PerfLevelSrc", "3322")
        if ok:
            any_ok = True
            _reg_add(key, "PowerMizerEnable", "1")
            _reg_add(key, "PowerMizerLevel", "1")
            _reg_add(key, "PowerMizerLevelAC", "1")
    # Also hint nvidia-smi if available
    _run(["nvidia-smi", "--auto-boost-default=0"])
    return True, "GPU set to max performance mode"


def disable_search_indexing() -> Tuple[bool, str]:
    _run(["sc", "stop", "WSearch"])
    ok, out = _run(["sc", "config", "WSearch", "start=", "disabled"])
    if ok:
        return True, "Windows Search Indexing disabled"
    return False, f"Search Indexing: {out}"


def disable_network_throttling() -> Tuple[bool, str]:
    key = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    ok, _ = _reg_add(key, "NetworkThrottlingIndex", "ffffffff")
    _reg_add(key, "SystemResponsiveness", "0")
    if ok:
        return True, "Network throttling disabled, system responsiveness maximized"
    return False, "Could not disable network throttling"


def disable_mouse_acceleration() -> Tuple[bool, str]:
    """Disable mouse acceleration for precise input."""
    ok1, _ = _set_reg(r"HKCU\Control Panel\Mouse", "MouseSpeed", "0", "REG_SZ")
    ok2, _ = _set_reg(r"HKCU\Control Panel\Mouse", "MouseThreshold1", "0", "REG_SZ")
    ok3, _ = _set_reg(r"HKCU\Control Panel\Mouse", "MouseThreshold2", "0", "REG_SZ")
    # Disable pointer precision (enhance pointer precision = acceleration)
    _set_reg(r"HKCU\Control Panel\Mouse", "MouseSensitivity", "10", "REG_SZ")
    if ok1 and ok2 and ok3:
        return True, "Mouse acceleration disabled"
    return False, "Could not disable mouse acceleration"


def restore_mouse_acceleration() -> Tuple[bool, str]:
    _set_reg(r"HKCU\Control Panel\Mouse", "MouseSpeed", "1", "REG_SZ")
    _set_reg(r"HKCU\Control Panel\Mouse", "MouseThreshold1", "6", "REG_SZ")
    _set_reg(r"HKCU\Control Panel\Mouse", "MouseThreshold2", "10", "REG_SZ")
    return True, "Mouse settings restored"


def clear_standby_memory() -> Tuple[bool, str]:
    """Clear standby memory list (requires EmptyStandbyList.exe)."""
    tool_path = os.path.join(os.path.dirname(sys.executable), "EmptyStandbyList.exe")
    if os.path.exists(tool_path):
        ok, out = _run([tool_path, "standbylist"])
        return ok, "Standby memory cleared" if ok else f"Standby clear failed: {out}"
    return False, "EmptyStandbyList.exe not found (optional tool)"


def disable_cpu_core_parking() -> Tuple[bool, str]:
    """Disable CPU Core Parking for lower input lag."""
    ok, _ = _run(["reg", "add",
        r"HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerSettings"
        r"\54533251-82be-4824-96c1-47b60b740d00"
        r"\0cc5b647-c1df-4637-891a-dec35c318583",
        "/v", "Attributes", "/t", "REG_DWORD", "/d", "0", "/f"])
    ok2, _ = _run(["powercfg", "/setacvalueindex", "scheme_current",
        "54533251-82be-4824-96c1-47b60b740d00",
        "0cc5b647-c1df-4637-891a-dec35c318583", "100"])
    _run(["powercfg", "/setactive", "scheme_current"])
    return True, "CPU Core Parking disabled"


def restore_cpu_core_parking() -> Tuple[bool, str]:
    """Re-enable CPU Core Parking."""
    _run(["powercfg", "/setacvalueindex", "scheme_current",
        "54533251-82be-4824-96c1-47b60b740d00",
        "0cc5b647-c1df-4637-891a-dec35c318583", "0"])
    _run(["powercfg", "/setactive", "scheme_current"])
    return True, "CPU Core Parking restored"


def disable_dpc_latency() -> Tuple[bool, str]:
    """Reduce DPC (Deferred Procedure Call) latency."""
    ok, _ = _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "DisablePagingExecutive", "1", "REG_DWORD"
    )
    return ok, "DPC Latency reduced"


def restore_dpc_latency() -> Tuple[bool, str]:
    _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "DisablePagingExecutive", "0", "REG_DWORD"
    )
    return True, "DPC Latency setting restored"


def optimize_network_latency() -> Tuple[bool, str]:
    """Optimize TCP/IP for lower gaming latency."""
    # Disable Nagle's algorithm (reduces TCP latency)
    _set_reg(r"HKLM\SOFTWARE\Microsoft\MSMQ\Parameters", "TCPNoDelay", "1", "REG_DWORD")
    # Set network throttling index to max
    _set_reg(
        r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "NetworkThrottlingIndex", "4294967295", "REG_DWORD"
    )
    # Disable auto-tuning (can cause latency spikes)
    _run(["netsh", "int", "tcp", "set", "global", "autotuninglevel=disabled"])
    _run(["netsh", "int", "tcp", "set", "global", "timestamps=enabled"])
    return True, "Network latency optimized"


def restore_network_latency() -> Tuple[bool, str]:
    _set_reg(
        r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "NetworkThrottlingIndex", "10", "REG_DWORD"
    )
    _run(["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"])
    return True, "Network settings restored"


def disable_mpo() -> Tuple[bool, str]:
    """Disable Multi-Plane Overlay (MPO) - fixes micro-stutter and input lag."""
    ok, out = _set_reg(
        r"HKLM\SOFTWARE\Microsoft\Windows\Dwm",
        "OverlayTestMode", "5", "REG_DWORD"
    )
    return ok, "MPO disabled (fixes micro-stutter)"


def restore_mpo() -> Tuple[bool, str]:
    _run(["reg", "delete", r"HKLM\SOFTWARE\Microsoft\Windows\Dwm",
          "/v", "OverlayTestMode", "/f"])
    return True, "MPO restored"


def set_timer_resolution() -> Tuple[bool, str]:
    """Set Windows timer to maximum resolution for lower latency."""
    _run(["bcdedit", "/set", "useplatformtick", "yes"])
    _run(["bcdedit", "/deletevalue", "useplatformclock"])
    return True, "Timer resolution optimized"


def restore_timer_resolution() -> Tuple[bool, str]:
    _run(["bcdedit", "/deletevalue", "useplatformtick"])
    return True, "Timer resolution restored"


def disable_fullscreen_optimizations() -> Tuple[bool, str]:
    """Disable fullscreen optimizations for lower latency."""
    ok, _ = _set_reg(
        r"HKCU\System\GameConfigStore",
        "GameDVR_FSEBehaviorMode", "2", "REG_DWORD"
    )
    _set_reg(
        r"HKCU\System\GameConfigStore",
        "GameDVR_HonorUserFSEBehaviorMode", "1", "REG_DWORD"
    )
    return ok, "Fullscreen optimizations disabled"


def restore_fullscreen_optimizations() -> Tuple[bool, str]:
    _set_reg(r"HKCU\System\GameConfigStore", "GameDVR_FSEBehaviorMode", "0", "REG_DWORD")
    _set_reg(r"HKCU\System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode", "0", "REG_DWORD")
    return True, "Fullscreen optimizations restored"


def set_win32_priority_separation() -> Tuple[bool, str]:
    """
    Win32PrioritySeparation = 38 (decimal) / 0x26 (hex).
    Gives foreground app (game) 3x more CPU time.
    Single most impactful registry tweak for gaming responsiveness.
    """
    ok, out = _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
        "Win32PrioritySeparation", "38", "REG_DWORD"
    )
    return ok, "CPU foreground priority maximized"


def restore_win32_priority_separation() -> Tuple[bool, str]:
    _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
        "Win32PrioritySeparation", "2", "REG_DWORD"
    )
    return True, "CPU priority separation restored"


def set_gpu_priority() -> Tuple[bool, str]:
    """
    GPU Priority 8 = highest. Reduces GPU queue latency = less input lag.
    Recommended by Blur Busters and competitive gaming communities.
    """
    base = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    _set_reg(base, "GPU Priority", "8", "REG_DWORD")
    _set_reg(base, "Priority", "6", "REG_DWORD")
    _set_reg(base, "Scheduling Category", "High", "REG_SZ")
    _set_reg(base, "SFIO Priority", "High", "REG_SZ")
    return True, "GPU priority set to maximum"


def restore_gpu_priority() -> Tuple[bool, str]:
    base = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    _set_reg(base, "GPU Priority", "1", "REG_DWORD")
    _set_reg(base, "Priority", "2", "REG_DWORD")
    _set_reg(base, "Scheduling Category", "Medium", "REG_SZ")
    _set_reg(base, "SFIO Priority", "Normal", "REG_SZ")
    return True, "GPU priority restored"


def enable_hags() -> Tuple[bool, str]:
    """
    Enable Hardware Accelerated GPU Scheduling (HAGS).
    Reduces CPU overhead, lowers input lag in supported games.
    Requires Windows 10 2004+ and recent GPU drivers.
    """
    ok, out = _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "HwSchMode", "2", "REG_DWORD"
    )
    return ok, "Hardware Accelerated GPU Scheduling enabled (restart required)"


def restore_hags() -> Tuple[bool, str]:
    _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "HwSchMode", "1", "REG_DWORD"
    )
    return True, "HAGS disabled"


def disable_windows_defender_gaming() -> Tuple[bool, str]:
    """
    Pause real-time scanning during gaming to prevent CPU spikes.
    Only disables real-time component, not full protection.
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Set-MpPreference -DisableRealtimeMonitoring $true"],
            capture_output=True, timeout=10, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            return True, "Windows Defender real-time scanning paused"
        return False, "Could not disable Defender (run as admin)"
    except Exception as e:
        return False, str(e)


def restore_windows_defender_gaming() -> Tuple[bool, str]:
    try:
        subprocess.run(
            ["powershell", "-Command", "Set-MpPreference -DisableRealtimeMonitoring $false"],
            capture_output=True, timeout=10, encoding="utf-8", errors="replace"
        )
        return True, "Windows Defender real-time scanning restored"
    except Exception as e:
        return False, str(e)


def set_cpu_responsiveness() -> Tuple[bool, str]:
    """
    SystemResponsiveness = 0 gives 100% of multimedia resources to games.
    Default is 20 (20% reserved for background tasks).
    """
    ok, out = _set_reg(
        r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "SystemResponsiveness", "0", "REG_DWORD"
    )
    return ok, "CPU responsiveness maximized for gaming"


def restore_cpu_responsiveness() -> Tuple[bool, str]:
    _set_reg(
        r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "SystemResponsiveness", "20", "REG_DWORD"
    )
    return True, "CPU responsiveness restored"


def disable_spectre_meltdown() -> Tuple[bool, str]:
    """
    Disable Spectre/Meltdown mitigations — 5-15% CPU performance boost.
    ⚠️ RISK: Reduces security against side-channel attacks.
    Only for dedicated gaming PCs not used for sensitive work.
    """
    _run(["bcdedit", "/set", "disableerrorreporting", "yes"])
    ok, out = _run(["bcdedit", "/set", "spectre", "disable"])
    if not ok:
        # Alternative registry method
        _set_reg(
            r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "FeatureSettingsOverride", "3", "REG_DWORD"
        )
        _set_reg(
            r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "FeatureSettingsOverrideMask", "3", "REG_DWORD"
        )
    return True, "CPU security mitigations disabled (5-15% perf boost)"


def restore_spectre_meltdown() -> Tuple[bool, str]:
    _run(["bcdedit", "/deletevalue", "spectre"])
    _run(["reg", "delete",
        r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "/v", "FeatureSettingsOverride", "/f"])
    _run(["reg", "delete",
        r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "/v", "FeatureSettingsOverrideMask", "/f"])
    return True, "CPU security mitigations restored"


# ── Restore-only functions ────────────────────────────────────────────────────

def restore_power_plan() -> Tuple[bool, str]:
    """Restore balanced power plan."""
    ok, out = _run(["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"])
    return ok, "Power plan restored to Balanced" if ok else f"Could not restore power plan: {out}"


def restore_game_bar() -> Tuple[bool, str]:
    """Re-enable Xbox Game Bar."""
    ok1, _ = _set_reg(r"HKCU\Software\Microsoft\GameBar", "AllowAutoGameMode", "1")
    ok2, _ = _set_reg(r"HKCU\Software\Microsoft\GameBar", "UseNexusForGameBarEnabled", "1")
    ok3, _ = _set_reg(r"HKCU\System\GameConfigStore", "GameDVR_Enabled", "1")
    all_ok = ok1 and ok2 and ok3
    return all_ok, "Xbox Game Bar re-enabled" if all_ok else "Partial: some Game Bar settings restored"


def restore_sysmain() -> Tuple[bool, str]:
    """Re-enable SysMain (Superfetch) service."""
    _run(["sc", "config", "SysMain", "start=", "auto"])
    ok, _ = _run(["sc", "start", "SysMain"])
    return True, "SysMain re-enabled and started" if ok else "SysMain configured (may already be running)"


def restore_diagtrack() -> Tuple[bool, str]:
    """Re-enable DiagTrack (Telemetry) service."""
    _run(["sc", "config", "DiagTrack", "start=", "auto"])
    _run(["sc", "start", "DiagTrack"])
    return True, "DiagTrack re-enabled and started"


def restore_mapbroker() -> Tuple[bool, str]:
    """Re-enable MapsBroker service."""
    _run(["sc", "config", "MapsBroker", "start=", "auto"])
    _run(["sc", "start", "MapsBroker"])
    return True, "MapsBroker re-enabled and started"


def restore_visual_effects() -> Tuple[bool, str]:
    """Restore visual effects to default (Let Windows decide)."""
    ok, _ = _set_reg(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
        "VisualFXSetting", "0"
    )
    return ok, "Visual effects restored to default" if ok else "Could not restore visual effects"


def restore_gpu_mode() -> Tuple[bool, str]:
    """Restore GPU hardware scheduling to default."""
    ok, _ = _set_reg(
        r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "HwSchMode", "1"
    )
    return ok, "GPU scheduling restored to default" if ok else "Could not restore GPU mode"


def restore_search_indexing() -> Tuple[bool, str]:
    """Re-enable Windows Search indexing service."""
    _run(["sc", "config", "WSearch", "start=", "auto"])
    _run(["sc", "start", "WSearch"])
    return True, "Windows Search Indexing re-enabled"


def restore_network_throttling() -> Tuple[bool, str]:
    """Restore network throttling to default."""
    key = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    _set_reg(key, "NetworkThrottlingIndex", "10", "REG_DWORD")
    _set_reg(key, "SystemResponsiveness", "20", "REG_DWORD")
    return True, "Network throttling restored to default"


# ── Function maps ─────────────────────────────────────────────────────────────

TWEAK_FUNCTIONS = {
    "set_high_performance_power_plan": set_high_performance_power_plan,
    "disable_game_bar": disable_game_bar,
    "disable_sysmain": disable_sysmain,
    "disable_diagtrack": disable_diagtrack,
    "disable_mapbroker": disable_mapbroker,
    "optimize_visual_effects": optimize_visual_effects,
    "set_gpu_max_performance": set_gpu_max_performance,
    "disable_search_indexing": disable_search_indexing,
    "disable_network_throttling": disable_network_throttling,
    "disable_mouse_acceleration": disable_mouse_acceleration,
    "clear_standby_memory": clear_standby_memory,
    # Input lag tweaks
    "disable_cpu_core_parking": disable_cpu_core_parking,
    "disable_dpc_latency": disable_dpc_latency,
    "optimize_network_latency": optimize_network_latency,
    "disable_mpo": disable_mpo,
    "set_timer_resolution": set_timer_resolution,
    "disable_fullscreen_optimizations": disable_fullscreen_optimizations,
    # In-game performance tweaks
    "set_win32_priority_separation": set_win32_priority_separation,
    "set_gpu_priority": set_gpu_priority,
    "enable_hags": enable_hags,
    "disable_windows_defender_gaming": disable_windows_defender_gaming,
    "set_cpu_responsiveness": set_cpu_responsiveness,
    "disable_spectre_meltdown": disable_spectre_meltdown,
}

RESTORE_FUNCTIONS = {
    "restore_power_plan": restore_power_plan,
    "restore_game_bar": restore_game_bar,
    "restore_sysmain": restore_sysmain,
    "restore_diagtrack": restore_diagtrack,
    "restore_mapbroker": restore_mapbroker,
    "restore_visual_effects": restore_visual_effects,
    "restore_gpu_mode": restore_gpu_mode,
    "restore_search_indexing": restore_search_indexing,
    "restore_network_throttling": restore_network_throttling,
    # Input lag restore functions
    "restore_cpu_core_parking": restore_cpu_core_parking,
    "restore_dpc_latency": restore_dpc_latency,
    "restore_network_latency": restore_network_latency,
    "restore_mouse_acceleration": restore_mouse_acceleration,
    "restore_mpo": restore_mpo,
    "restore_timer_resolution": restore_timer_resolution,
    "restore_fullscreen_optimizations": restore_fullscreen_optimizations,
    # In-game performance restore functions
    "restore_win32_priority_separation": restore_win32_priority_separation,
    "restore_gpu_priority": restore_gpu_priority,
    "restore_hags": restore_hags,
    "restore_windows_defender_gaming": restore_windows_defender_gaming,
    "restore_cpu_responsiveness": restore_cpu_responsiveness,
    "restore_spectre_meltdown": restore_spectre_meltdown,
}


# ── Public API ────────────────────────────────────────────────────────────────

def run_tweak(func_name: str) -> Tuple[bool, str]:
    """Run a single tweak by function name."""
    fn = TWEAK_FUNCTIONS.get(func_name)
    if fn is None:
        return False, f"Unknown tweak: {func_name}"
    try:
        return fn()
    except Exception as e:
        logger.error(f"Tweak '{func_name}' crashed: {e}")
        return False, str(e)


def run_all_tweaks(progress_callback: Callable[[int, str, bool], None] = None) -> List[dict]:
    """Run all tweaks sequentially, calling progress_callback(index, name, success)."""
    results = []
    for i, (display_name, func_name) in enumerate(ALL_TWEAKS):
        logger.info(f"Running tweak: {display_name}")
        ok, msg = run_tweak(func_name)
        results.append({"name": display_name, "func": func_name, "success": ok, "message": msg})
        if progress_callback:
            progress_callback(i, display_name, ok)
    return results
