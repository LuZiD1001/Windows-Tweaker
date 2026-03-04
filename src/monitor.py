"""System monitoring and information utilities"""

import os
import psutil
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Real-time system monitoring"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize monitor with background thread"""
        if self._initialized:
            return
        
        self.running = False
        self.thread = None
        self.update_callback = None
        self.interval = 1.0
        self.current_stats = {
            'cpu': 0,
            'ram': 0,
            'disk': 0,
            'temp': 0,
            'processes': 0,
            'timestamp': datetime.now()
        }
        self._initialized = True
    
    def start(self, callback: Optional[Callable] = None, interval: float = 1.0):
        """Start background monitoring"""
        if self.running:
            return
        
        self.update_callback = callback
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Background monitor started")
    
    def stop(self):
        """Stop background monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Background monitor stopped")
    
    def _monitor_loop(self):
        """Main background monitoring loop"""
        while self.running:
            try:
                self._update_all_stats()
                if self.update_callback:
                    self.update_callback(self.current_stats)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            time.sleep(self.interval)
    
    def _update_all_stats(self):
        """Update all system statistics"""
        self.current_stats = {
            'cpu': self.get_cpu_usage(),
            'ram_percent': self.get_ram_usage()['percent'],
            'disk': self.get_disk_usage()['percent'],
            'temp': self._get_temperature(),
            'processes': self.get_process_count(),
            'timestamp': datetime.now()
        }
    
    def _get_temperature(self) -> float:
        """Get system temperature"""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except:
            pass
        return 0
    
    def get_health_status(self) -> str:
        """Get system health status"""
        cpu = self.current_stats.get('cpu', 0)
        ram = self.current_stats.get('ram_percent', 0)
        
        if cpu < 30 and ram < 40:
            return 'excellent'
        elif cpu < 60 and ram < 70:
            return 'good'
        elif cpu < 80 and ram < 85:
            return 'fair'
        else:
            return 'poor'
    
    def get_health_color(self) -> str:
        """Get color for current health status"""
        status = self.get_health_status()
        colors = {
            'excellent': '#00FF88',
            'good': '#00DDFF',
            'fair': '#FFBB00',
            'poor': '#FF4444'
        }
        return colors.get(status, '#9A9A9A')
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    @staticmethod
    def get_ram_usage() -> Dict[str, float]:
        """Get RAM usage statistics"""
        try:
            ram = psutil.virtual_memory()
            return {
                "used": ram.used / (1024**3),  # GB
                "total": ram.total / (1024**3),  # GB
                "percent": ram.percent
            }
        except:
            return {"used": 0, "total": 0, "percent": 0}
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage for C: drive"""
        try:
            disk = psutil.disk_usage('C:\\')
            return {
                "used": disk.used / (1024**3),  # GB
                "total": disk.total / (1024**3),  # GB
                "percent": disk.percent
            }
        except:
            return {"used": 0, "total": 0, "percent": 0}
    
    @staticmethod
    def get_gpu_info() -> str:
        """Get GPU information"""
        try:
            import subprocess
            result = subprocess.run(
                'wmic path win32_videocontroller get name',
                capture_output=True,
                text=True,
                timeout=2
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
        except:
            pass
        return "GPU Info Unavailable"
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get system information"""
        try:
            import platform
            import subprocess
            
            # Get Windows version
            version = platform.platform()
            
            # Get processor
            processor = platform.processor()
            
            # Get uptime using psutil boot time
            try:
                import time
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_hours = uptime_seconds / 3600
            except Exception:
                uptime_hours = 0
            
            return {
                "os": version,
                "processor": processor if processor else "Unknown",
                "uptime": f"{int(uptime_hours)}h",
                "cores": str(os.cpu_count() or 0)
            }
        except:
            return {
                "os": "Unknown",
                "processor": "Unknown",
                "uptime": "Unknown",
                "cores": "Unknown"
            }
    
    @staticmethod
    def get_process_count() -> int:
        """Get number of running processes"""
        try:
            return len(psutil.pids())
        except:
            return 0
