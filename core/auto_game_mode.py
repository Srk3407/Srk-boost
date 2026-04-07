"""
SRK Boost - Auto Game Mode
Watches for game processes. When a game starts → auto-apply tweaks.
When game exits → auto-restore.
"""

import os
import json
import logging
from typing import Set, Optional, Dict

from PyQt6.QtCore import QThread, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".srk_boost", "settings.json")

# Known game executables
KNOWN_GAMES: Dict[str, str] = {
    # FPS
    "cs2.exe": "Counter-Strike 2",
    "csgo.exe": "CS:GO",
    "valorant.exe": "Valorant",
    "VALORANT-Win64-Shipping.exe": "Valorant",
    "r5apex.exe": "Apex Legends",
    "cod.exe": "Call of Duty",
    "ModernWarfare.exe": "Warzone",
    "cod_live_ship.exe": "Warzone 2",
    "Overwatch.exe": "Overwatch 2",
    # Battle Royale
    "FortniteClient-Win64-Shipping.exe": "Fortnite",
    "PUBG.exe": "PUBG",
    "RustClient.exe": "Rust",
    # Open World / AAA
    "GTA5.exe": "GTA V",
    "RDR2.exe": "Red Dead 2",
    "Cyberpunk2077.exe": "Cyberpunk 2077",
    "witcher3.exe": "The Witcher 3",
    "ELDENring.exe": "Elden Ring",
    # Strategy / Other
    "LeagueOfLegends.exe": "League of Legends",
    "dota2.exe": "Dota 2",
    "minecraft.exe": "Minecraft",
    "javaw.exe": "Minecraft (Java)",
    "steam.exe": None,  # Don't trigger on Steam itself
}

# Tweaks to auto-apply when a game is detected
AUTO_TWEAKS = [
    "set_high_performance_power_plan",
    "disable_game_bar",
    "set_win32_priority_separation",
    "set_gpu_priority",
    "set_cpu_responsiveness",
    "disable_network_throttling",
    "disable_cpu_core_parking",
]


class AutoGameModeWatcher(QThread):
    """
    Polls running processes every 5 seconds.
    Emits game_started / game_stopped signals.
    """
    game_started  = pyqtSignal(str)   # game name
    game_stopped  = pyqtSignal(str)   # game name
    status_update = pyqtSignal(str)   # log message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._active_games: Set[str] = set()
        self._enabled = self._load_enabled()
        self._tweaks_applied = False

    def _load_enabled(self) -> bool:
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE) as f:
                    return json.load(f).get("auto_game_mode", False)
        except Exception:
            pass
        return False

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        try:
            data = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE) as f:
                    data = json.load(f)
            data["auto_game_mode"] = enabled
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save auto_game_mode setting: {e}")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def run(self):
        self._running = True
        self.status_update.emit("Auto Game Mode watcher started.")
        while self._running:
            if self._enabled:
                self._poll()
            self.msleep(5000)  # check every 5 seconds
        self.status_update.emit("Auto Game Mode watcher stopped.")

    def stop(self):
        self._running = False

    def _poll(self):
        try:
            import psutil
        except ImportError:
            return

        try:
            running_exes: Set[str] = set()
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name and name in KNOWN_GAMES and KNOWN_GAMES[name] is not None:
                        running_exes.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # New games started
            for exe in running_exes - self._active_games:
                game_name = KNOWN_GAMES.get(exe, exe)
                self._active_games.add(exe)
                self.game_started.emit(game_name)
                logger.info(f"Game detected: {game_name}")
                if not self._tweaks_applied:
                    self._apply_tweaks()

            # Games stopped
            for exe in self._active_games - running_exes:
                game_name = KNOWN_GAMES.get(exe, exe)
                self._active_games.discard(exe)
                self.game_stopped.emit(game_name)
                logger.info(f"Game exited: {game_name}")
                if not self._active_games and self._tweaks_applied:
                    self._restore_tweaks()

        except Exception as e:
            logger.error(f"Auto game mode poll error: {e}")

    def _apply_tweaks(self):
        try:
            import core.optimizer as opt
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.create_restore_point("auto_game_mode_pre")
            for func_name in AUTO_TWEAKS:
                fn = getattr(opt, func_name, None)
                if fn:
                    try:
                        fn()
                    except Exception:
                        pass
            self._tweaks_applied = True
            self.status_update.emit("⚡ Auto-boosted for gaming!")
            logger.info("Auto Game Mode: tweaks applied")
        except Exception as e:
            logger.error(f"Auto Game Mode apply error: {e}")

    def _restore_tweaks(self):
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.restore_latest()
            self._tweaks_applied = False
            self.status_update.emit("↩ Auto-restored after gaming session.")
            logger.info("Auto Game Mode: tweaks restored")
        except Exception as e:
            logger.error(f"Auto Game Mode restore error: {e}")
