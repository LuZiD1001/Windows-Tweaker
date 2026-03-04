"""
LuzidSettings - System Benchmark Engine
Fast synthetic benchmarks for CPU, RAM, Disk and Network.
Scores are stored historically so users can compare before/after tweaks.
"""

import time
import os
import json
import math
import socket
import struct
import threading
import hashlib
import tempfile
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

SCORES_FILE = "luzid_benchmark_scores.json"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run"""
    timestamp: str
    cpu_score: float       # Higher = better (Mhash/s)
    ram_score: float       # MB/s sequential read
    disk_score: float      # MB/s write speed
    network_latency: float # ms ping to 8.8.8.8
    overall_score: int     # Weighted composite
    profile_applied: str   # Which profile was active


class BenchmarkEngine:
    """
    Fast but meaningful synthetic benchmarks.
    CPU: Multi-threaded SHA256 hashing
    RAM: Sequential array allocation+write
    Disk: Temp file write/read speed
    Network: Raw socket ping latency
    """
    
    THREAD_COUNT = 4  # Use 4 threads for CPU bench
    
    def __init__(self):
        self._running = False
        self._callbacks: Dict[str, Callable] = {}
        self._history: List[BenchmarkResult] = []
        self._load_history()
    
    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb
    
    def _emit(self, event: str, *args):
        if event in self._callbacks:
            self._callbacks[event](*args)
    
    # =========================================================================
    # CPU Benchmark - Multi-threaded SHA256
    # =========================================================================
    
    def _cpu_worker(self, duration: float, result_box: list):
        """Hash as many times as possible in `duration` seconds"""
        count = 0
        data = os.urandom(1024)
        deadline = time.perf_counter() + duration
        while time.perf_counter() < deadline:
            hashlib.sha256(data).digest()
            count += 1
        result_box.append(count)
    
    def benchmark_cpu(self, duration: float = 2.0) -> float:
        """Returns Mhash/s"""
        threads = []
        results = []
        for _ in range(self.THREAD_COUNT):
            t = threading.Thread(target=self._cpu_worker, args=(duration, results))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        total_hashes = sum(results)
        mhash_per_sec = (total_hashes / duration) / 1_000_000
        return round(mhash_per_sec, 2)
    
    # =========================================================================
    # RAM Benchmark - Sequential write speed
    # =========================================================================
    
    def benchmark_ram(self, size_mb: int = 256) -> float:
        """Returns MB/s write speed"""
        try:
            chunk = bytes(1024 * 1024)  # 1 MB chunk
            buf = []
            
            start = time.perf_counter()
            for _ in range(size_mb):
                buf.append(bytearray(chunk))
            elapsed = time.perf_counter() - start
            
            del buf  # Free memory
            
            if elapsed > 0:
                return round(size_mb / elapsed, 1)
            return 0.0
        except MemoryError:
            return 0.0
    
    # =========================================================================
    # Disk Benchmark - Sequential write to temp file
    # =========================================================================
    
    def benchmark_disk(self, size_mb: int = 64) -> float:
        """Returns MB/s write speed"""
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="luzid_bench_")
            chunk = os.urandom(1024 * 1024)  # 1 MB random data
            
            start = time.perf_counter()
            with os.fdopen(tmp_fd, 'wb') as f:
                for _ in range(size_mb):
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
            elapsed = time.perf_counter() - start
            
            if elapsed > 0:
                return round(size_mb / elapsed, 1)
            return 0.0
        except Exception as e:
            logger.warning(f"Disk bench error: {e}")
            return 0.0
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    
    # =========================================================================
    # Network Benchmark - ICMP ping latency
    # =========================================================================
    
    def benchmark_network(self, host: str = "8.8.8.8", count: int = 10) -> float:
        """Returns average latency in ms (uses raw TCP connect as fallback)"""
        latencies = []
        
        # Try TCP connect method (works without admin)
        for _ in range(count):
            try:
                start = time.perf_counter()
                sock = socket.create_connection((host, 53), timeout=2)
                sock.close()
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
                time.sleep(0.05)
            except Exception:
                pass
        
        if latencies:
            # Return average, dropping highest outlier
            latencies.sort()
            trimmed = latencies[:-1] if len(latencies) > 3 else latencies
            return round(sum(trimmed) / len(trimmed), 2)
        return 999.0
    
    # =========================================================================
    # Full Benchmark Suite
    # =========================================================================
    
    def run_full_async(self, profile: str = "none", progress_cb: Optional[Callable] = None):
        """Run full benchmark suite asynchronously"""
        if self._running:
            return
        self._running = True
        threading.Thread(
            target=self._run_full,
            args=(profile, progress_cb),
            daemon=True
        ).start()
    
    def _run_full(self, profile: str, progress_cb: Optional[Callable]):
        try:
            results = {}
            
            if progress_cb:
                progress_cb("🔥 CPU Benchmark (multi-thread SHA256)…", 0.1)
            cpu = self.benchmark_cpu(2.0)
            results['cpu'] = cpu
            
            if progress_cb:
                progress_cb(f"✓ CPU: {cpu} Mhash/s  |  💾 RAM Benchmark…", 0.35)
            ram = self.benchmark_ram(128)
            results['ram'] = ram
            
            if progress_cb:
                progress_cb(f"✓ RAM: {ram} MB/s  |  💿 Disk Benchmark…", 0.6)
            disk = self.benchmark_disk(32)
            results['disk'] = disk
            
            if progress_cb:
                progress_cb(f"✓ Disk: {disk} MB/s  |  🌐 Network Latency…", 0.8)
            net = self.benchmark_network()
            results['net'] = net
            
            # Composite score (weighted)
            # CPU: 40%, RAM: 25%, Disk: 20%, Net: 15%
            cpu_norm  = min(cpu / 50.0,  1.0)   # 50 Mhash/s = perfect CPU
            ram_norm  = min(ram / 10000.0, 1.0) # 10 GB/s = perfect RAM
            disk_norm = min(disk / 500.0,  1.0) # 500 MB/s = perfect disk (NVMe)
            net_norm  = max(0, 1.0 - (net / 200.0))  # 0ms ideal, 200ms = 0
            
            overall = int(
                (cpu_norm * 40 + ram_norm * 25 + disk_norm * 20 + net_norm * 15) * 10000 / 100
            )
            # Cap at 9999
            overall = min(overall, 9999)
            
            result = BenchmarkResult(
                timestamp=datetime.now().isoformat(),
                cpu_score=cpu,
                ram_score=ram,
                disk_score=disk,
                network_latency=net,
                overall_score=overall,
                profile_applied=profile
            )
            
            self._history.append(result)
            self._save_history()
            
            if progress_cb:
                progress_cb(f"✅ Complete! Score: {overall}/9999", 1.0)
            
            self._emit("on_complete", result)
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            if progress_cb:
                progress_cb(f"⚠ Error: {e}", 1.0)
        finally:
            self._running = False
    
    # =========================================================================
    # History
    # =========================================================================
    
    def get_history(self) -> List[BenchmarkResult]:
        return list(self._history)
    
    def get_best(self) -> Optional[BenchmarkResult]:
        if not self._history:
            return None
        return max(self._history, key=lambda r: r.overall_score)
    
    def get_last(self) -> Optional[BenchmarkResult]:
        return self._history[-1] if self._history else None
    
    def _save_history(self):
        try:
            data = []
            for r in self._history[-20:]:  # Keep last 20
                data.append({
                    "timestamp": r.timestamp,
                    "cpu_score": r.cpu_score,
                    "ram_score": r.ram_score,
                    "disk_score": r.disk_score,
                    "network_latency": r.network_latency,
                    "overall_score": r.overall_score,
                    "profile_applied": r.profile_applied,
                })
            with open(SCORES_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Save history failed: {e}")
    
    def _load_history(self):
        try:
            if os.path.exists(SCORES_FILE):
                with open(SCORES_FILE) as f:
                    data = json.load(f)
                for item in data:
                    self._history.append(BenchmarkResult(**item))
        except Exception:
            pass
    
    def clear_history(self):
        self._history.clear()
        try:
            os.unlink(SCORES_FILE)
        except Exception:
            pass
    
    @staticmethod
    def score_grade(score: int) -> str:
        """Letter grade for a score"""
        if score >= 8000: return "S+"
        if score >= 6500: return "S"
        if score >= 5000: return "A"
        if score >= 3500: return "B"
        if score >= 2000: return "C"
        return "D"
    
    @staticmethod
    def score_color(score: int) -> str:
        if score >= 8000: return "#FFD700"
        if score >= 6500: return "#00FF88"
        if score >= 5000: return "#00DDFF"
        if score >= 3500: return "#A43BFF"
        if score >= 2000: return "#FFBB00"
        return "#FF4444"
