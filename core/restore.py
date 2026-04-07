"""
SRK Boost - Restore Point Manager
Saves and restores system settings before any optimization is applied.
"""

import json
import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Respect %USERPROFILE% on Windows, fall back to ~ on other platforms
_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))
RESTORE_DIR = os.path.join(_PROFILE, ".srk_boost", "restore_points")


def ensure_restore_dir() -> str:
    """Create restore directory if needed and return its path."""
    os.makedirs(RESTORE_DIR, exist_ok=True)
    return RESTORE_DIR


class RestorePoint:
    """Represents a single restore point snapshot."""

    def __init__(self, label: str = "", data: Optional[Dict] = None):
        now = datetime.now()
        self._ts_str = now.strftime('%Y%m%d_%H%M%S')
        # name is always restore_YYYYMMDD_HHMMSS  (the file-system key)
        self.name = f"restore_{self._ts_str}"
        # label is a human-readable description (e.g. "pre_fps_boost")
        self.label = label
        self.timestamp = now.isoformat()
        self.data = data or {}

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RestorePoint":
        rp = cls.__new__(cls)
        rp.name = d.get("name", "")
        rp.label = d.get("label", d.get("name", ""))
        # Reconstruct _ts_str from name if possible
        n = rp.name
        rp._ts_str = n[len("restore_"):] if n.startswith("restore_") else n
        rp.timestamp = d.get("timestamp", "")
        rp.data = d.get("data", {})
        return rp

    @property
    def filepath(self) -> str:
        """Always returns restore_YYYYMMDD_HHMMSS.json path."""
        return os.path.join(RESTORE_DIR, f"{self.name}.json")

    @property
    def display_name(self) -> str:
        return self.label or self.name


class RestoreManager:
    """Manages creation, listing, and restoration of restore points."""

    def __init__(self):
        ensure_restore_dir()

    # ── Public API ────────────────────────────────────────────────────────────

    def create_restore_point(self, label: str = "") -> RestorePoint:
        """
        Capture current system state and save to disk.
        The file is always named restore_YYYYMMDD_HHMMSS.json.
        Returns the created RestorePoint (including its filepath).
        """
        rp = RestorePoint(label=label)
        rp.data = self._capture_current_state()
        self._save(rp)
        logger.info(f"Restore point created: {rp.filepath}  (label={rp.label!r})")
        return rp

    def list_restore_points(self) -> List[RestorePoint]:
        """List all saved restore points, newest first."""
        points = []
        try:
            for fname in sorted(os.listdir(RESTORE_DIR), reverse=True):
                if fname.endswith(".json"):
                    fpath = os.path.join(RESTORE_DIR, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            d = json.load(f)
                        points.append(RestorePoint.from_dict(d))
                    except Exception as e:
                        logger.warning(f"Failed to load restore point {fname}: {e}")
        except Exception as e:
            logger.error(f"Failed to list restore points: {e}")
        return points

    def restore(self, rp: RestorePoint) -> bool:
        """Apply a restore point – re-enables services, restores registry & power plan."""
        try:
            data = rp.data
            self._apply_power_plan(data.get("power_plan_guid", ""))
            self._apply_services(data.get("services", {}))
            self._apply_visual_effects(data.get("visual_effects", ""))
            self._apply_registry_values(data.get("registry_values", []))
            logger.info(f"Restore point '{rp.display_name}' applied successfully.")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def restore_from_file(self, path: str) -> bool:
        """Restore from a specific restore point JSON file path."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rp = RestorePoint.from_dict(data)
            return self.restore(rp)
        except FileNotFoundError:
            raise FileNotFoundError(f"Restore point file not found: {path}")
        except Exception as e:
            logger.error(f"restore_from_file failed: {e}")
            raise

    def restore_latest(self) -> bool:
        """Restore from the most recent restore point."""
        restore_dir = self._get_restore_dir()
        files = sorted([f for f in os.listdir(restore_dir) if f.endswith('.json')], reverse=True)
        if not files:
            raise FileNotFoundError("No restore points found.")
        return self.restore_from_file(os.path.join(restore_dir, files[0]))

    def _get_restore_dir(self) -> str:
        """Return the restore directory path, creating it if needed."""
        ensure_restore_dir()
        return RESTORE_DIR

    def delete_restore_point(self, rp: RestorePoint) -> bool:
        """Delete a restore point file from disk."""
        try:
            if os.path.exists(rp.filepath):
                os.remove(rp.filepath)
                logger.info(f"Deleted restore point: {rp.name}")
                return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
        return False

    # ── State capture ─────────────────────────────────────────────────────────

    def _capture_current_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}

        # Power plan (Windows only – graceful on non-Windows)
        state["power_plan_guid"] = ""
        state["power_plan_name"] = "Unknown"
        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                # Output: "Power Scheme GUID: <guid>  (<name>)"
                # GUID is at index 3, name follows in parens
                state["power_plan_guid"] = parts[3] if len(parts) > 3 else ""
                state["power_plan_name"] = " ".join(parts[5:]).strip("()") if len(parts) > 5 else ""
        except Exception as e:
            logger.warning(f"Could not capture power plan: {e}")

        # Services state
        services_to_check = [
            "SysMain", "DiagTrack", "MapsBroker", "RetailDemo", "TabletInputService",
        ]
        services_state: Dict[str, str] = {}
        for svc in services_to_check:
            try:
                result = subprocess.run(
                    ["sc", "query", svc],
                    capture_output=True, text=True, timeout=5
                )
                services_state[svc] = "running" if "RUNNING" in result.stdout else "stopped"
            except Exception:
                services_state[svc] = "unknown"
        state["services"] = services_state

        # Visual effects registry setting
        state["visual_effects"] = self._get_registry_value(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            "VisualFXSetting"
        )

        # Registry snapshot (Game Bar + visual effects values)
        state["registry_values"] = self._capture_registry_snapshot()

        return state

    def _get_registry_value(self, key: str, name: str) -> str:
        try:
            result = subprocess.run(
                ["reg", "query", key, "/v", name],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if name in line:
                        return line.strip()
        except Exception:
            pass
        return ""

    def _capture_registry_snapshot(self) -> List[Dict]:
        snapshot: List[Dict] = []
        keys_to_capture = [
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                "VisualFXSetting",
            ),
            (r"HKCU\Software\Microsoft\GameBar", "UseNexusForGameBarEnabled"),
            (r"HKCU\Software\Microsoft\GameBar", "AllowAutoGameMode"),
        ]
        for key, name in keys_to_capture:
            try:
                result = subprocess.run(
                    ["reg", "query", key, "/v", name],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if name in line and "REG_" in line:
                            parts = line.split()
                            snapshot.append({
                                "key": key,
                                "name": name,
                                "type": parts[-2] if len(parts) >= 2 else "REG_DWORD",
                                "value": parts[-1] if parts else "0",
                            })
                            break
            except Exception:
                pass
        return snapshot

    # ── Restore helpers ────────────────────────────────────────────────────────

    def _apply_power_plan(self, guid: str):
        if not guid:
            return
        try:
            subprocess.run(["powercfg", "/setactive", guid], timeout=5, capture_output=True)
            logger.info(f"Power plan restored to GUID: {guid}")
        except Exception as e:
            logger.warning(f"Could not restore power plan: {e}")

    def _apply_services(self, services: Dict[str, str]):
        for svc, state in services.items():
            try:
                if state == "running":
                    subprocess.run(["sc", "start", svc], capture_output=True, encoding="utf-8", errors="replace", timeout=5)
                elif state == "stopped":
                    subprocess.run(["sc", "stop", svc], capture_output=True, encoding="utf-8", errors="replace", timeout=5)
            except Exception as e:
                logger.warning(f"Could not restore service {svc}: {e}")

    def _apply_visual_effects(self, value_line: str):
        if "VisualFXSetting" not in value_line:
            return
        try:
            parts = value_line.strip().split()
            val = parts[-1] if parts else "0"
            subprocess.run([
                "reg", "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                "/v", "VisualFXSetting", "/t", "REG_DWORD", "/d", val, "/f"
            ], capture_output=True, encoding="utf-8", errors="replace", timeout=5)
        except Exception as e:
            logger.warning(f"Could not restore visual effects: {e}")

    def _apply_registry_values(self, values: List[Dict]):
        for entry in values:
            try:
                subprocess.run([
                    "reg", "add", entry["key"],
                    "/v", entry["name"],
                    "/t", entry.get("type", "REG_DWORD"),
                    "/d", entry.get("value", "0"),
                    "/f"
                ], capture_output=True, encoding="utf-8", errors="replace", timeout=5)
            except Exception as e:
                logger.warning(f"Could not restore registry value {entry}: {e}")

    # ── Internal save ─────────────────────────────────────────────────────────

    def _save(self, rp: RestorePoint):
        ensure_restore_dir()
        path = rp.filepath
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rp.to_dict(), f, indent=2, ensure_ascii=False)
        if not os.path.exists(path):
            raise IOError(f"Restore point file was not created at: {path}")


# ── Standalone test ────────────────────────────────────────────────────────────

def test_restore_point_creation() -> bool:
    """
    Write a test restore point and verify the file exists on disk.
    Cleans up the test file afterwards.
    Returns True on success, False on failure.
    """
    try:
        rm = RestoreManager()
        rp = rm.create_restore_point(label="__test__")
        path = rp.filepath

        if not os.path.exists(path):
            logger.error(f"FAIL – restore point file not found at: {path}")
            return False

        # Validate the JSON content
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "name" in data, "Missing 'name' field"
        assert "timestamp" in data, "Missing 'timestamp' field"
        assert data["name"].startswith("restore_"), f"Unexpected name: {data['name']}"

        # Clean up
        os.remove(path)
        logger.info(f"PASS – restore point created and verified: {path}")
        return True

    except Exception as e:
        logger.error(f"FAIL – restore point test raised exception: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ok = test_restore_point_creation()
    print("Restore point test:", "PASSED ✅" if ok else "FAILED ❌")
    print(f"Restore directory : {RESTORE_DIR}")
