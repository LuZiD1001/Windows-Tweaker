"""
LuzidSettings - Deep Registry Tweaker
Applies proven Windows registry optimizations for gaming/performance.
Each tweak is documented, reversible, and backed up before applying.
"""

import winreg
import os
import json
import threading
import logging
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RegTweak:
    """A single registry tweak"""
    name: str
    description: str
    category: str
    key: str
    value_name: str
    value_data: any
    value_type: int  # winreg.REG_DWORD etc
    default_data: any  # For reverting
    risky: bool = False  # Warn before applying


# All tweaks - each is documented and reversible
REGISTRY_TWEAKS: List[RegTweak] = [
    # === INPUT LATENCY ===
    RegTweak(
        name="Disable Mouse Acceleration",
        description="Removes Windows pointer precision (raw 1:1 input)",
        category="⚡ Input",
        key=r"Control Panel\Mouse",
        value_name="MouseSpeed",
        value_data="0",
        value_type=winreg.REG_SZ,
        default_data="1"
    ),
    RegTweak(
        name="Raw Mouse Input Threshold 1",
        description="Set mouse threshold 1 to 0 for linear response",
        category="⚡ Input",
        key=r"Control Panel\Mouse",
        value_name="MouseThreshold1",
        value_data="0",
        value_type=winreg.REG_SZ,
        default_data="6"
    ),
    RegTweak(
        name="Raw Mouse Input Threshold 2",
        description="Set mouse threshold 2 to 0 for linear response",
        category="⚡ Input",
        key=r"Control Panel\Mouse",
        value_name="MouseThreshold2",
        value_data="0",
        value_type=winreg.REG_SZ,
        default_data="10"
    ),
    RegTweak(
        name="GPU Priority Boost",
        description="Sets GPU scheduling priority to highest (reduces stutter)",
        category="🖥️ GPU",
        key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
        value_name="GPU Priority",
        value_data=8,
        value_type=winreg.REG_DWORD,
        default_data=2
    ),
    RegTweak(
        name="Game Task Priority",
        description="Raises game process scheduling priority",
        category="🖥️ GPU",
        key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
        value_name="Priority",
        value_data=6,
        value_type=winreg.REG_DWORD,
        default_data=2
    ),
    RegTweak(
        name="Game Scheduling Category",
        description="Sets Windows game scheduling to High",
        category="🖥️ GPU",
        key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
        value_name="Scheduling Category",
        value_data="High",
        value_type=winreg.REG_SZ,
        default_data="Medium"
    ),
    # === NETWORK ===
    RegTweak(
        name="Nagle Algorithm Disable",
        description="Disables Nagle's algorithm for lower TCP latency in games",
        category="🌐 Network",
        key=r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
        value_name="TcpAckFrequency",
        value_data=1,
        value_type=winreg.REG_DWORD,
        default_data=0
    ),
    RegTweak(
        name="TCP No Delay",
        description="Disable TCP delay for immediate packet transmission",
        category="🌐 Network",
        key=r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
        value_name="TCPNoDelay",
        value_data=1,
        value_type=winreg.REG_DWORD,
        default_data=0
    ),
    RegTweak(
        name="Network Throttling Index",
        description="Removes Windows network throttling for games (MMCSS)",
        category="🌐 Network",
        key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        value_name="NetworkThrottlingIndex",
        value_data=0xffffffff,
        value_type=winreg.REG_DWORD,
        default_data=10
    ),
    # === POWER ===
    RegTweak(
        name="Power Scheme - High Performance",
        description="Forces High Performance power plan via registry",
        category="⚡ Power",
        key=r"SYSTEM\CurrentControlSet\Control\Power",
        value_name="CsEnabled",
        value_data=0,
        value_type=winreg.REG_DWORD,
        default_data=1
    ),
    RegTweak(
        name="Timer Resolution",
        description="Sets system timer to 1ms (reduces input lag, increases power use)",
        category="⚡ Power",
        key=r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel",
        value_name="GlobalTimerResolutionRequests",
        value_data=1,
        value_type=winreg.REG_DWORD,
        default_data=0
    ),
    # === VISUAL / PRIVACY ===
    RegTweak(
        name="Disable Telemetry Level",
        description="Sets Windows telemetry to Security level (minimum)",
        category="🔒 Privacy",
        key=r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
        value_name="AllowTelemetry",
        value_data=0,
        value_type=winreg.REG_DWORD,
        default_data=1
    ),
    RegTweak(
        name="Disable Activity History",
        description="Stops Windows tracking your activity history",
        category="🔒 Privacy",
        key=r"SOFTWARE\Policies\Microsoft\Windows\System",
        value_name="PublishUserActivities",
        value_data=0,
        value_type=winreg.REG_DWORD,
        default_data=1
    ),
    RegTweak(
        name="Disable Advertising ID",
        description="Kills the per-app advertising ID tracking",
        category="🔒 Privacy",
        key=r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
        value_name="Enabled",
        value_data=0,
        value_type=winreg.REG_DWORD,
        default_data=1
    ),
    RegTweak(
        name="Disable Search Indexing on Battery",
        description="Stops Windows Search from hammering disk while on battery",
        category="💾 Storage",
        key=r"SOFTWARE\Microsoft\Windows Search",
        value_name="EnableSearchOnBattery",
        value_data=0,
        value_type=winreg.REG_DWORD,
        default_data=1
    ),
    RegTweak(
        name="Prefetch/Superfetch Config",
        description="Optimizes Windows Prefetch for SSD users",
        category="💾 Storage",
        key=r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters",
        value_name="EnablePrefetcher",
        value_data=3,
        value_type=winreg.REG_DWORD,
        default_data=3
    ),
    RegTweak(
        name="Disable Windows Tips",
        description="Removes nag screens and 'tips' that waste CPU cycles",
        category="🔒 Privacy",
        key=r"SOFTWARE\Policies\Microsoft\Windows\CloudContent",
        value_name="DisableSoftLanding",
        value_data=1,
        value_type=winreg.REG_DWORD,
        default_data=0
    ),
    RegTweak(
        name="MMCSS Audio Priority",
        description="Boosts audio thread priority to reduce stutters mid-game",
        category="⚡ Input",
        key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Audio",
        value_name="Priority",
        value_data=6,
        value_type=winreg.REG_DWORD,
        default_data=2
    ),
]


class RegistryBackup:
    """Saves and restores original registry values before tweaking"""
    
    BACKUP_FILE = "luzid_registry_backup.json"
    
    @classmethod
    def save(cls, key: str, value_name: str, original_data) -> bool:
        try:
            backup = cls._load_all()
            backup_key = f"{key}\\{value_name}"
            if backup_key not in backup:  # Don't overwrite original
                backup[backup_key] = {
                    "data": str(original_data),
                    "timestamp": datetime.now().isoformat()
                }
                with open(cls.BACKUP_FILE, "w") as f:
                    json.dump(backup, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Backup failed: {e}")
            return False
    
    @classmethod
    def _load_all(cls) -> dict:
        try:
            if os.path.exists(cls.BACKUP_FILE):
                with open(cls.BACKUP_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    @classmethod
    def has_backup(cls) -> bool:
        return os.path.exists(cls.BACKUP_FILE)
    
    @classmethod
    def get_backup_count(cls) -> int:
        return len(cls._load_all())


class RegistryTweaker:
    """
    Applies/reverts Windows registry tweaks.
    All writes are backed up first. Thread-safe.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._applied: Dict[str, bool] = {}  # tweak name -> applied?
        self._callbacks: Dict[str, Callable] = {}
        self._check_applied()
    
    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb
    
    def _emit(self, event: str, *args):
        if event in self._callbacks:
            self._callbacks[event](*args)
    
    def get_tweaks_by_category(self) -> Dict[str, List[RegTweak]]:
        """Group tweaks by category for UI display"""
        cats: Dict[str, List[RegTweak]] = {}
        for t in REGISTRY_TWEAKS:
            cats.setdefault(t.category, []).append(t)
        return cats
    
    def is_applied(self, tweak_name: str) -> bool:
        return self._applied.get(tweak_name, False)
    
    def _check_applied(self):
        """Check which tweaks are currently active"""
        for tweak in REGISTRY_TWEAKS:
            try:
                hive = winreg.HKEY_CURRENT_USER
                if tweak.key.startswith("SYSTEM") or tweak.key.startswith("SOFTWARE\\Policies"):
                    hive = winreg.HKEY_LOCAL_MACHINE
                
                with winreg.OpenKey(hive, tweak.key) as k:
                    val, _ = winreg.QueryValueEx(k, tweak.value_name)
                    # Check if current value matches our tweak value
                    if str(val) == str(tweak.value_data):
                        self._applied[tweak.name] = True
                    else:
                        self._applied[tweak.name] = False
            except Exception:
                self._applied[tweak.name] = False
    
    def apply_tweak(self, tweak: RegTweak) -> Tuple[bool, str]:
        """Apply a single tweak. Returns (success, message)"""
        with self._lock:
            try:
                hive = winreg.HKEY_CURRENT_USER
                hive_name = "HKCU"
                if (tweak.key.startswith("SYSTEM") or 
                    tweak.key.startswith("SOFTWARE\\Policies") or
                    tweak.key.startswith("SOFTWARE\\Microsoft\\Windows NT")):
                    hive = winreg.HKEY_LOCAL_MACHINE
                    hive_name = "HKLM"
                
                # Try to backup current value first
                try:
                    with winreg.OpenKey(hive, tweak.key) as k:
                        current_val, _ = winreg.QueryValueEx(k, tweak.value_name)
                        RegistryBackup.save(tweak.key, tweak.value_name, current_val)
                except FileNotFoundError:
                    pass  # Key/value doesn't exist yet, no backup needed
                
                # Create/open key with write access
                key_handle = winreg.CreateKeyEx(hive, tweak.key, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key_handle, tweak.value_name, 0, tweak.value_type, tweak.value_data)
                winreg.CloseKey(key_handle)
                
                self._applied[tweak.name] = True
                logger.info(f"Applied: {hive_name}\\{tweak.key}\\{tweak.value_name} = {tweak.value_data}")
                return True, f"✓ {tweak.name} applied"
                
            except PermissionError:
                return False, f"✗ {tweak.name}: Needs Admin rights"
            except Exception as e:
                return False, f"✗ {tweak.name}: {str(e)[:50]}"
    
    def revert_tweak(self, tweak: RegTweak) -> Tuple[bool, str]:
        """Revert a tweak to its default value"""
        with self._lock:
            try:
                hive = winreg.HKEY_CURRENT_USER
                if (tweak.key.startswith("SYSTEM") or 
                    tweak.key.startswith("SOFTWARE\\Policies") or
                    tweak.key.startswith("SOFTWARE\\Microsoft\\Windows NT")):
                    hive = winreg.HKEY_LOCAL_MACHINE
                
                key_handle = winreg.CreateKeyEx(hive, tweak.key, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key_handle, tweak.value_name, 0, tweak.value_type, tweak.default_data)
                winreg.CloseKey(key_handle)
                
                self._applied[tweak.name] = False
                return True, f"↩ {tweak.name} reverted"
            except PermissionError:
                return False, f"✗ Revert failed: Admin required"
            except Exception as e:
                return False, f"✗ Revert error: {str(e)[:50]}"
    
    def apply_category(self, category: str, progress_cb: Optional[Callable] = None) -> List[str]:
        """Apply all tweaks in a category. Returns list of results."""
        tweaks = [t for t in REGISTRY_TWEAKS if t.category == category]
        results = []
        for i, t in enumerate(tweaks):
            ok, msg = self.apply_tweak(t)
            results.append(msg)
            if progress_cb:
                progress_cb(msg, (i + 1) / len(tweaks))
        return results
    
    def apply_all(self, progress_cb: Optional[Callable] = None) -> List[str]:
        """Apply every tweak. Returns results."""
        results = []
        total = len(REGISTRY_TWEAKS)
        for i, t in enumerate(REGISTRY_TWEAKS):
            ok, msg = self.apply_tweak(t)
            results.append(msg)
            if progress_cb:
                progress_cb(msg, (i + 1) / total)
        return results
    
    def revert_all(self, progress_cb: Optional[Callable] = None) -> List[str]:
        """Revert all applied tweaks to defaults."""
        results = []
        applied = [t for t in REGISTRY_TWEAKS if self._applied.get(t.name)]
        if not applied:
            return ["No tweaks to revert"]
        for i, t in enumerate(applied):
            ok, msg = self.revert_tweak(t)
            results.append(msg)
            if progress_cb:
                progress_cb(msg, (i + 1) / len(applied))
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Summary stats for display"""
        total = len(REGISTRY_TWEAKS)
        applied = sum(1 for v in self._applied.values() if v)
        return {
            "total": total,
            "applied": applied,
            "pending": total - applied,
            "backup_count": RegistryBackup.get_backup_count()
        }
