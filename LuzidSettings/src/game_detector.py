"""
LuzidSettings - Auto Game Detector
Automatically detects running games and applies the optimal
optimization profile without user interaction.
Monitors process list every 5 seconds for known game executables.
"""

import psutil
import threading
import time
from typing import Callable, Dict, Optional, Set


# Map of game exe -> profile key to auto-apply
GAME_PROFILES: Dict[str, tuple] = {
    # FPS Games
    "cs2.exe":              ("gaming", "Counter-Strike 2"),
    "csgo.exe":             ("gaming", "CS:GO"),
    "r5apex.exe":           ("gaming", "Apex Legends"),
    "valorant.exe":         ("gaming", "Valorant"),
    "overwatch.exe":        ("gaming", "Overwatch"),
    "overwatch 2.exe":      ("gaming", "Overwatch 2"),
    "cod.exe":              ("gaming", "Call of Duty"),
    "modernwarfare.exe":    ("gaming", "Modern Warfare"),
    "warzone.exe":          ("gaming", "Warzone"),
    "fortnite.exe":         ("gaming", "Fortnite"),

    # BR & Open World
    "pubg.exe":             ("gaming", "PUBG"),
    "eldenring.exe":        ("gaming", "Elden Ring"),
    "cyberpunk2077.exe":    ("gaming", "Cyberpunk 2077"),
    "witcher3.exe":         ("gaming", "The Witcher 3"),

    # FiveM / GTA
    "fivem.exe":            ("gaming", "FiveM"),
    "gta5.exe":             ("gaming", "GTA V"),
    "gtav.exe":             ("gaming", "GTA V"),

    # Streaming apps (apply streaming profile)
    "obs64.exe":            ("streaming", "OBS Studio"),
    "obs32.exe":            ("streaming", "OBS Studio"),
    "streamlabs obs.exe":   ("streaming", "Streamlabs OBS"),
    "xsplit.core.exe":      ("streaming", "XSplit"),

    # Competitive / MOBA
    "leagueoflegends.exe":  ("gaming", "League of Legends"),
    "dota2.exe":            ("gaming", "Dota 2"),
    "rocketleague.exe":     ("gaming", "Rocket League"),
}


class GameDetector:
    """
    Polls process list for known games.
    Auto-applies optimization profiles when a game launches or closes.
    Fires callbacks: on_game_detected(game_name, profile_key)
                     on_game_closed(game_name)
    """

    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval
        self._running = False
        self._active_games: Set[str] = set()
        self._callbacks: Dict[str, Callable] = {}
        self._thread: Optional[threading.Thread] = None
        self.enabled = True

    def on(self, event: str, cb: Callable):
        """Register event callback"""
        self._callbacks[event] = cb

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[GAME DETECTOR] Started")

    def stop(self):
        self._running = False
        print("[GAME DETECTOR] Stopped")

    def _poll_loop(self):
        while self._running:
            if self.enabled:
                self._check_processes()
            time.sleep(self.poll_interval)

    def _check_processes(self):
        try:
            running_exes = {
                p.name().lower()
                for p in psutil.process_iter(['name'])
                if p.info['name']
            }
        except Exception:
            return

        # Check for newly detected games
        for exe, (profile_key, game_name) in GAME_PROFILES.items():
            exe_lower = exe.lower()
            if exe_lower in running_exes and exe_lower not in self._active_games:
                self._active_games.add(exe_lower)
                print(f"[GAME DETECTOR] Detected: {game_name} → applying '{profile_key}'")
                if 'on_game_detected' in self._callbacks:
                    self._callbacks['on_game_detected'](game_name, profile_key)

            elif exe_lower not in running_exes and exe_lower in self._active_games:
                self._active_games.discard(exe_lower)
                print(f"[GAME DETECTOR] Closed: {game_name}")
                if 'on_game_closed' in self._callbacks:
                    self._callbacks['on_game_closed'](game_name)

    def get_active_games(self) -> list:
        """Get list of currently detected running games"""
        result = []
        for exe in self._active_games:
            for game_exe, (profile, name) in GAME_PROFILES.items():
                if game_exe.lower() == exe:
                    result.append({"exe": exe, "name": name, "profile": profile})
        return result

    @staticmethod
    def get_supported_games() -> Dict[str, tuple]:
        return GAME_PROFILES.copy()
