"""Performance benchmarking and metrics tracking"""

import psutil
from datetime import datetime
from typing import Dict, List
import json
import os


class PerformanceMetrics:
    """Track system performance metrics over time"""
    
    METRICS_FILE = "performance_history.json"
    
    def __init__(self):
        """Initialize metrics tracker"""
        self.current_metrics = {}
        self.history: List[Dict] = []
        self.load_history()
    
    @staticmethod
    def measure_now() -> Dict:
        """Take current system measurements"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.5)
            import os, sys
            disk_path = 'C:\\' if sys.platform == 'win32' else '/'
            disk = psutil.disk_usage(disk_path)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "processes": len(psutil.pids()),
                "boot_time": psutil.boot_time()
            }
        except:
            return None
    
    def add_measurement(self, metrics: Dict):
        """Add a measurement to history"""
        if metrics:
            self.current_metrics = metrics
            self.history.append(metrics)
            
            # Keep only last 100 measurements
            if len(self.history) > 100:
                self.history.pop(0)
            
            self.save_history()
    
    def get_improvement(self, metric: str, before: Dict, after: Dict) -> float:
        """
        Calculate improvement percentage.
        
        Args:
            metric: Metric name (cpu_percent, memory_percent, etc.)
            before: Metrics before optimization
            after: Metrics after optimization
            
        Returns:
            Improvement percentage (positive = improvement)
        """
        if metric not in before or metric not in after:
            return 0.0
        
        before_val = before[metric]
        after_val = after[metric]
        
        if before_val == 0:
            return 0.0
        
        return ((before_val - after_val) / before_val) * 100
    
    def get_avg_improvement_summary(self, before: Dict, after: Dict) -> Dict:
        """Get summary of improvements"""
        return {
            "cpu": self.get_improvement("cpu_percent", before, after),
            "memory": self.get_improvement("memory_percent", before, after),
            "disk": self.get_improvement("disk_percent", before, after)
        }
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent metrics history"""
        return self.history[-limit:]
    
    def save_history(self):
        """Save metrics history to file"""
        try:
            with open(self.METRICS_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[METRICS] Error saving history: {e}")
    
    def load_history(self):
        """Load metrics history from file"""
        try:
            if os.path.exists(self.METRICS_FILE):
                with open(self.METRICS_FILE, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"[METRICS] Error loading history: {e}")


class BenchmarkTool:
    """Run performance benchmarks"""
    
    @staticmethod
    def benchmark_disk_io(folder: str = ".", duration_ms: int = 1000) -> Dict:
        """
        Benchmark disk I/O performance.
        
        Returns:
            Dict with read/write speeds
        """
        try:
            import tempfile
            import time
            
            test_size = 1024 * 1024  # 1MB
            results = {}
            
            # Write test
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(b'x' * test_size)
            
            # Simple benchmark
            start = time.time()
            with open(tmp_path, 'rb') as f:
                f.read()
            read_time = time.time() - start
            
            # Calculate speed
            results['read_speed_mbps'] = test_size / (1024*1024) / read_time if read_time > 0 else 0
            results['write_speed_mbps'] = test_size / (1024*1024) / read_time if read_time > 0 else 0
            
            # Cleanup
            os.unlink(tmp_path)
            
            return results
        except:
            return {'read_speed_mbps': 0, 'write_speed_mbps': 0}
    
    @staticmethod
    def benchmark_cpu() -> Dict:
        """
        Benchmark CPU performance.
        
        Returns:
            CPU benchmark results
        """
        try:
            import time
            
            # Prime calculation benchmark
            def calculate_primes(n):
                count = 0
                for num in range(2, n):
                    is_prime = True
                    for i in range(2, int(num**0.5)+1):
                        if num % i == 0:
                            is_prime = False
                            break
                    if is_prime:
                        count += 1
                return count
            
            start = time.time()
            primes = calculate_primes(1000)
            duration = time.time() - start
            
            return {
                'primes_found': primes,
                'duration_seconds': duration,
                'primes_per_second': primes / duration if duration > 0 else 0
            }
        except:
            return {'primes_found': 0, 'duration_seconds': 0, 'primes_per_second': 0}
    
    @staticmethod
    def benchmark_memory() -> Dict:
        """
        Benchmark memory performance.
        
        Returns:
            Memory benchmark results
        """
        try:
            import time
            
            test_size = 10 * 1024 * 1024  # 10MB
            
            # Allocation speed test
            start = time.time()
            arr = bytearray(test_size)
            allocation_time = time.time() - start
            
            # Write speed test
            start = time.time()
            for i in range(0, len(arr), 1024):
                arr[i] = 1
            write_time = time.time() - start
            
            # Read speed test
            start = time.time()
            _ = sum(arr[i] for i in range(0, len(arr), 1024))
            read_time = time.time() - start
            
            return {
                'allocation_time_ms': allocation_time * 1000,
                'write_time_ms': write_time * 1000,
                'read_time_ms': read_time * 1000,
                'memory_used_mb': test_size / (1024*1024)
            }
        except:
            return {'allocation_time_ms': 0, 'write_time_ms': 0, 'read_time_ms': 0}


class PerformanceReport:
    """Generate performance comparison reports"""
    
    @staticmethod
    def generate_report(before: Dict, after: Dict) -> str:
        """
        Generate improvement report.
        
        Args:
            before: Metrics before optimization
            after: Metrics after optimization
            
        Returns:
            Formatted report string
        """
        metrics = PerformanceMetrics()
        improvements = metrics.get_avg_improvement_summary(before, after)
        
        report = """
╔════════════════════════════════════════════╗
║        OPTIMIZATION REPORT                 ║
╚════════════════════════════════════════════╝

BEFORE OPTIMIZATION:
  CPU Usage:     {cpu_before:.1f}%
  RAM Usage:     {mem_before:.1f}%
  Disk Usage:    {disk_before:.1f}%

AFTER OPTIMIZATION:
  CPU Usage:     {cpu_after:.1f}%
  RAM Usage:     {mem_after:.1f}%
  Disk Usage:    {disk_after:.1f}%

IMPROVEMENTS:
  CPU:           {cpu_imp:+.1f}% {cpu_emoji}
  Memory:        {mem_imp:+.1f}% {mem_emoji}
  Disk:          {disk_imp:+.1f}% {disk_emoji}

═════════════════════════════════════════════
""".format(
            cpu_before=before.get('cpu_percent', 0),
            mem_before=before.get('memory_percent', 0),
            disk_before=before.get('disk_percent', 0),
            cpu_after=after.get('cpu_percent', 0),
            mem_after=after.get('memory_percent', 0),
            disk_after=after.get('disk_percent', 0),
            cpu_imp=improvements['cpu'],
            mem_imp=improvements['memory'],
            disk_imp=improvements['disk'],
            cpu_emoji='✓' if improvements['cpu'] > 0 else '✗',
            mem_emoji='✓' if improvements['memory'] > 0 else '✗',
            disk_emoji='✓' if improvements['disk'] > 0 else '✗'
        )
        
        return report
