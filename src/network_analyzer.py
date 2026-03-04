"""
LuzidSettings - Real-Time Network Analyzer
Monitors active network connections, detects suspicious outbound traffic,
shows per-process bandwidth usage, and identifies telemetry destinations.
"""

import psutil
import socket
import threading
import time
from typing import List, Dict, Callable
from dataclasses import dataclass, field


# Known telemetry/tracking IP ranges and hostnames (partial matches)
SUSPICIOUS_DESTINATIONS = [
    "telemetry", "analytics", "tracking", "stats.", "metrics.",
    "ocean.ac", "echo.ac", "detect.ac",
    "vortex.data.microsoft.com", "watson.telemetry.microsoft.com",
    "data.adobe.com", "ssl.google-analytics.com",
    "logs.roku.com", "ping.chartbeat.net",
]


@dataclass
class ConnectionInfo:
    pid: int
    process_name: str
    local_addr: str
    remote_addr: str
    remote_host: str
    status: str
    suspicious: bool
    suspicion_reason: str


class NetworkAnalyzer:
    """
    Analyze active network connections in real time.
    Flags connections to known telemetry/tracking hosts.
    Resolves hostnames asynchronously to avoid blocking.
    """

    def __init__(self):
        self._connections: List[ConnectionInfo] = []
        self._hostname_cache: Dict[str, str] = {}
        self._running = False
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()

    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb

    def start(self, interval: float = 3.0):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True).start()

    def stop(self):
        self._running = False

    def _monitor_loop(self, interval: float):
        while self._running:
            self._scan_connections()
            time.sleep(interval)

    def _scan_connections(self):
        results = []
        try:
            proc_map = {p.pid: p.name() for p in psutil.process_iter(['pid', 'name'])}
            conns = psutil.net_connections(kind='inet')

            for conn in conns:
                if not conn.raddr:
                    continue

                pid = conn.pid or 0
                proc_name = proc_map.get(pid, "unknown")
                local  = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}"
                status = conn.status or "NONE"

                # Resolve hostname (from cache or async)
                remote_host = self._resolve_host(conn.raddr.ip)

                # Check if suspicious
                suspicious = False
                reason = ""
                check_str = (remote_host + " " + conn.raddr.ip).lower()
                for pattern in SUSPICIOUS_DESTINATIONS:
                    if pattern in check_str:
                        suspicious = True
                        reason = f"Matches pattern: {pattern}"
                        break

                results.append(ConnectionInfo(
                    pid=pid,
                    process_name=proc_name,
                    local_addr=local,
                    remote_addr=remote,
                    remote_host=remote_host,
                    status=status,
                    suspicious=suspicious,
                    suspicion_reason=reason
                ))

        except Exception as e:
            print(f"[NETANALYZER] Error: {e}")

        with self._lock:
            self._connections = results

        if 'on_update' in self._callbacks:
            self._callbacks['on_update'](results)

    def _resolve_host(self, ip: str) -> str:
        """Resolve IP to hostname (cached, non-blocking)"""
        if ip in self._hostname_cache:
            return self._hostname_cache[ip]

        # Start async resolution
        def resolve():
            try:
                host = socket.gethostbyaddr(ip)[0]
            except Exception:
                host = ip
            self._hostname_cache[ip] = host

        threading.Thread(target=resolve, daemon=True).start()
        return ip  # Return IP now, hostname available next cycle

    def get_connections(self) -> List[ConnectionInfo]:
        with self._lock:
            return list(self._connections)

    def get_suspicious(self) -> List[ConnectionInfo]:
        with self._lock:
            return [c for c in self._connections if c.suspicious]

    @staticmethod
    def get_interface_stats() -> Dict[str, Dict]:
        """Get per-interface bytes sent/received"""
        try:
            stats = psutil.net_io_counters(pernic=True)
            return {
                iface: {
                    "bytes_sent": data.bytes_sent,
                    "bytes_recv": data.bytes_recv,
                    "packets_sent": data.packets_sent,
                    "packets_recv": data.packets_recv,
                    "errin": data.errin,
                    "errout": data.errout,
                }
                for iface, data in stats.items()
            }
        except Exception:
            return {}
