"""
LuzidSettings - Smart Process Scanner & Killer
Scans running processes, flags suspicious/high-CPU hogs,
and lets users kill them with one click. Also detects known
anti-cheat / telemetry processes automatically.
"""

import psutil
import threading
from typing import List, Dict, Callable
from dataclasses import dataclass
from datetime import datetime


# Known telemetry / background bloat processes
KNOWN_TELEMETRY = {
    "compattelrunner.exe":  "Windows Telemetry",
    "wsappx.exe":           "Windows Store Telemetry",
    "svchost.exe":          "Service Host (check carefully)",
    "searchindexer.exe":    "Windows Search Indexer",
    "microsoftedgeupdate.exe": "Edge Auto-Updater",
    "GoogleUpdate.exe":     "Google Update Service",
    "aitstatic.exe":        "Application Impact Telemetry",
    "nvtray.exe":           "NVIDIA Tray (can disable)",
    "adobeupdatedaemon":    "Adobe Auto-Updater",
    "steam.exe":            "Steam Client (if not gaming)",
    "discordptb.exe":       "Discord PTB",
    "brave.exe":            "Brave Browser",
    "epic games launcher.exe": "Epic Games Launcher",
}

KNOWN_ANTICHEAT = {
    "EasyAntiCheat.exe":    "Easy Anti-Cheat",
    "BEService.exe":        "BattlEye Service",
    "vgc.exe":              "Vanguard (Valorant AC)",
    "mhyprot2.sys":         "miHoYo Protect 2",
    "faceit.exe":           "FACEIT Anti-Cheat",
    "ESEADriver2.sys":      "ESEA Anti-Cheat",
}


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    mem_mb: float
    status: str
    flag: str          # '', 'telemetry', 'anticheat', 'high_cpu', 'high_mem'
    flag_reason: str


class ProcessScanner:
    """
    Scan and analyze running processes.
    Flags high-CPU, high-memory, telemetry and anti-cheat processes.
    """

    CPU_THRESHOLD  = 5.0   # % - flag if above this
    MEM_THRESHOLD  = 200.0 # MB - flag if above this

    def __init__(self):
        self._cache: List[ProcessInfo] = []
        self._scanning = False
        self._callbacks: Dict[str, Callable] = {}

    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb

    def scan_async(self):
        """Start async scan - fires on_complete(results) when done"""
        if self._scanning:
            return
        self._scanning = True
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        results = []
        try:
            # Prime CPU measurement
            procs = list(psutil.process_iter(['pid', 'name', 'status']))
            # Let psutil gather CPU samples
            for p in procs:
                try:
                    p.cpu_percent(interval=None)
                except Exception:
                    pass
            threading.Event().wait(0.5)

            for p in procs:
                try:
                    name = p.info['name'] or "unknown"
                    pid = p.info['pid']
                    status = p.info['status']
                    cpu = p.cpu_percent(interval=None)
                    mem = p.memory_info().rss / (1024 * 1024)

                    flag = ''
                    reason = ''

                    name_lower = name.lower()
                    for key, label in KNOWN_TELEMETRY.items():
                        if key.lower() in name_lower:
                            flag = 'telemetry'
                            reason = label
                            break

                    if not flag:
                        for key, label in KNOWN_ANTICHEAT.items():
                            if key.lower() in name_lower:
                                flag = 'anticheat'
                                reason = label
                                break

                    if not flag and cpu > self.CPU_THRESHOLD:
                        flag = 'high_cpu'
                        reason = f"Using {cpu:.1f}% CPU"

                    if not flag and mem > self.MEM_THRESHOLD:
                        flag = 'high_mem'
                        reason = f"Using {mem:.0f} MB RAM"

                    results.append(ProcessInfo(
                        pid=pid, name=name,
                        cpu_percent=cpu, mem_mb=mem,
                        status=status, flag=flag, flag_reason=reason
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except Exception as e:
            print(f"[SCANNER] Error: {e}")
        finally:
            self._scanning = False
            self._cache = sorted(results, key=lambda x: x.cpu_percent, reverse=True)
            if 'on_complete' in self._callbacks:
                self._callbacks['on_complete'](self._cache)

    @staticmethod
    def kill_process(pid: int) -> bool:
        """Kill a process by PID. Returns True on success."""
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=3)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            try:
                psutil.Process(pid).kill()
                return True
            except Exception:
                return False

    def get_cached(self) -> List[ProcessInfo]:
        return self._cache
