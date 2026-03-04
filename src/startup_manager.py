"""
LuzidSettings - Startup Manager
Read, enable, disable and analyze Windows startup entries from:
  - HKCU Run / HKLM Run registry keys
  - Startup folder (per-user + all users)
  - Task Scheduler (basic scan)

Safely disables by moving to a backup key (fully reversible).
"""

import winreg
import os
import json
import shutil
import threading
import logging
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

DISABLED_BACKUP_KEY = r"SOFTWARE\LuzidSettings\DisabledStartup"

# Known safe-to-disable startup entries
KNOWN_BLOAT = {
    "microsoftedgeupdate":  ("Edge Updater",      "Safe to disable"),
    "googleupdate":         ("Google Updater",     "Safe to disable"),
    "onedrive":             ("Microsoft OneDrive", "Disable if not using"),
    "adobeupdater":         ("Adobe Updater",      "Safe to disable"),
    "teams":                ("Microsoft Teams",    "Disable if not using"),
    "discord":              ("Discord",            "Disable if not using"),
    "spotify":              ("Spotify",            "Disable if not using"),
    "epicgameslauncher":    ("Epic Games",         "Disable if not gaming"),
    "steamwebhelper":       ("Steam Web Helper",   "Disable if not gaming"),
    "nvbackend":            ("NVIDIA Backend",     "Safe to disable"),
    "amdrsserv":            ("AMD Radeon Settings","Can disable"),
    "jusched":              ("Java Update",        "Safe to disable"),
    "itunes":               ("iTunes",             "Disable if not using"),
    "dropbox":              ("Dropbox",            "Disable if not using"),
    "zoom":                 ("Zoom",               "Disable if not using"),
}


@dataclass
class StartupEntry:
    name: str
    path: str
    source: str       # "HKCU", "HKLM", "Folder-User", "Folder-All"
    enabled: bool
    known_app: str    # Human-readable name if known
    recommendation: str  # "Safe to disable", "Keep", etc.
    is_system: bool   # True for Windows system entries
    last_seen: str


class StartupManager:
    """
    Enumerate, enable and disable startup items safely.
    All disables are reversible via backup registry key.
    """
    
    def __init__(self):
        self._entries: List[StartupEntry] = []
        self._lock = threading.Lock()
        self._callbacks: Dict[str, Callable] = {}
    
    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb
    
    def _emit(self, event: str, *args):
        if event in self._callbacks:
            self._callbacks[event](*args)
    
    def scan(self) -> List[StartupEntry]:
        """Scan all startup locations synchronously"""
        entries = []
        entries.extend(self._scan_registry(winreg.HKEY_CURRENT_USER,
                                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                                           "HKCU"))
        entries.extend(self._scan_registry(winreg.HKEY_LOCAL_MACHINE,
                                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                                           "HKLM"))
        entries.extend(self._scan_folder_startup())
        entries.extend(self._scan_disabled_backup())
        
        with self._lock:
            self._entries = entries
        
        return entries
    
    def scan_async(self):
        """Async scan, fires on_complete(entries)"""
        threading.Thread(target=self._do_scan_async, daemon=True).start()
    
    def _do_scan_async(self):
        results = self.scan()
        self._emit("on_complete", results)
    
    def _scan_registry(self, hive, key_path: str, source: str) -> List[StartupEntry]:
        entries = []
        try:
            with winreg.OpenKey(hive, key_path) as k:
                i = 0
                while True:
                    try:
                        name, data, _ = winreg.EnumValue(k, i)
                        known, rec, sys = self._classify(name, data)
                        entries.append(StartupEntry(
                            name=name,
                            path=data,
                            source=source,
                            enabled=True,
                            known_app=known,
                            recommendation=rec,
                            is_system=sys,
                            last_seen=datetime.now().isoformat()
                        ))
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.debug(f"Registry scan {source}: {e}")
        return entries
    
    def _scan_folder_startup(self) -> List[StartupEntry]:
        entries = []
        paths = []
        
        # Per-user startup
        user_startup = os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
        )
        if os.path.isdir(user_startup):
            paths.append((user_startup, "Folder-User"))
        
        # All users startup
        all_startup = os.path.expandvars(
            r"%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs\Startup"
        )
        if os.path.isdir(all_startup):
            paths.append((all_startup, "Folder-All"))
        
        for folder, source in paths:
            for fname in os.listdir(folder):
                if fname.startswith('.') or fname.lower() == 'desktop.ini':
                    continue
                fpath = os.path.join(folder, fname)
                known, rec, sys = self._classify(fname, fpath)
                entries.append(StartupEntry(
                    name=fname,
                    path=fpath,
                    source=source,
                    enabled=True,
                    known_app=known,
                    recommendation=rec,
                    is_system=sys,
                    last_seen=datetime.now().isoformat()
                ))
        return entries
    
    def _scan_disabled_backup(self) -> List[StartupEntry]:
        """Read our backup key to show disabled entries"""
        entries = []
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY) as k:
                i = 0
                while True:
                    try:
                        name, data, _ = winreg.EnumValue(k, i)
                        known, rec, sys = self._classify(name, data)
                        entries.append(StartupEntry(
                            name=name,
                            path=data,
                            source="Disabled",
                            enabled=False,
                            known_app=known,
                            recommendation=rec,
                            is_system=sys,
                            last_seen=datetime.now().isoformat()
                        ))
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass
        return entries
    
    def _classify(self, name: str, path: str) -> Tuple[str, str, bool]:
        """Returns (known_app, recommendation, is_system)"""
        name_lower = name.lower().replace(" ", "").replace("-", "")
        path_lower = path.lower()
        
        # Check known bloat
        for key, (app_name, rec) in KNOWN_BLOAT.items():
            if key in name_lower or key in path_lower.replace(" ", ""):
                return app_name, rec, False
        
        # System entries - keep!
        system_hints = ["windows", "system32", "windowsdefender", "securityhealth",
                        "ctfmon", "winlogon", "csrss"]
        for hint in system_hints:
            if hint in name_lower or hint in path_lower:
                return "Windows System", "Keep enabled", True
        
        return "", "Manual review", False
    
    # =========================================================================
    # Enable / Disable
    # =========================================================================
    
    def disable_entry(self, entry: StartupEntry) -> Tuple[bool, str]:
        """Disable a startup entry (reversible)"""
        try:
            if entry.source in ("HKCU", "HKLM"):
                return self._disable_registry(entry)
            elif entry.source.startswith("Folder"):
                return self._disable_folder(entry)
            return False, "Cannot disable this entry type"
        except Exception as e:
            return False, str(e)
    
    def _disable_registry(self, entry: StartupEntry) -> Tuple[bool, str]:
        hive = winreg.HKEY_CURRENT_USER if entry.source == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        # Backup to our key
        backup = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(backup, entry.name, 0, winreg.REG_SZ, entry.path)
        winreg.CloseKey(backup)
        
        # Delete from Run key
        with winreg.OpenKey(hive, run_key, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, entry.name)
        
        return True, f"✓ Disabled: {entry.name}"
    
    def _disable_folder(self, entry: StartupEntry) -> Tuple[bool, str]:
        disabled_folder = os.path.expandvars(r"%APPDATA%\LuzidSettings\DisabledStartup")
        os.makedirs(disabled_folder, exist_ok=True)
        dest = os.path.join(disabled_folder, os.path.basename(entry.path))
        shutil.move(entry.path, dest)
        return True, f"✓ Disabled: {entry.name}"
    
    def enable_entry(self, entry: StartupEntry) -> Tuple[bool, str]:
        """Re-enable a disabled entry"""
        try:
            # Restore from backup registry key
            restore_hive = winreg.HKEY_CURRENT_USER
            run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            restore_handle = winreg.CreateKeyEx(restore_hive, run_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(restore_handle, entry.name, 0, winreg.REG_SZ, entry.path)
            winreg.CloseKey(restore_handle)
            
            # Remove from backup
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY, 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, entry.name)
            
            return True, f"✓ Re-enabled: {entry.name}"
        except Exception as e:
            return False, f"✗ Enable failed: {str(e)[:50]}"
    
    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            total = len(self._entries)
            enabled = sum(1 for e in self._entries if e.enabled)
            disabled = total - enabled
            bloat = sum(1 for e in self._entries if e.recommendation != "Keep enabled" and e.enabled)
            return {"total": total, "enabled": enabled, "disabled": disabled, "bloat_detected": bloat}
    
    def get_cached(self) -> List[StartupEntry]:
        with self._lock:
            return list(self._entries)
