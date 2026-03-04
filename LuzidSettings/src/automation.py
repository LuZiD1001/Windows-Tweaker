"""Task scheduling and automation for LuzidSettings"""

from typing import Callable, Dict, List
from datetime import datetime, time
import threading
import json
import os
from dataclasses import dataclass, asdict

# Optional: try importing schedule, but don't fail if not available
try:
    import schedule
except ImportError:
    schedule = None


@dataclass
class ScheduledTask:
    """Represents a scheduled optimization task"""
    name: str
    description: str
    enabled: bool
    frequency: str  # 'daily', 'weekly', 'hourly', 'on_startup'
    time: str  # HH:MM format for daily/weekly
    profiles: List[str]  # Profile keys to apply
    day_of_week: int = None  # 0-6 for weekly (Monday-Sunday)


class TaskScheduler:
    """Manage scheduled optimization tasks"""
    
    CONFIG_FILE = "task_schedule.json"
    
    def __init__(self):
        """Initialize scheduler"""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.is_running = False
        self.scheduler_thread = None
        self.callbacks: Dict[str, Callable] = {}
        self._stop_event = threading.Event()
        self.load_tasks()
    
    def add_callback(self, event_type: str, callback: Callable):
        """Register callback for events"""
        self.callbacks[event_type] = callback
    
    def add_task(self, task: ScheduledTask) -> bool:
        """Add a new task"""
        if task.name in self.tasks:
            return False
        
        self.tasks[task.name] = task
        self.save_tasks()
        return True
    
    def remove_task(self, name: str) -> bool:
        """Remove a task"""
        if name in self.tasks:
            del self.tasks[name]
            self.save_tasks()
            return True
        return False
    
    def update_task(self, name: str, task: ScheduledTask) -> bool:
        """Update a task"""
        if name not in self.tasks:
            return False
        
        self.tasks[name] = task
        self.save_tasks()
        return True
    
    def get_task(self, name: str) -> ScheduledTask:
        """Get task by name"""
        return self.tasks.get(name)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def enable_task(self, name: str) -> bool:
        """Enable a task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            self.save_tasks()
            return True
        return False
    
    def disable_task(self, name: str) -> bool:
        """Disable a task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            self.save_tasks()
            return True
        return False
    
    def save_tasks(self):
        """Save tasks to file"""
        try:
            data = {name: asdict(task) for name, task in self.tasks.items()}
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SCHEDULER] Error saving tasks: {e}")
    
    def load_tasks(self):
        """Load tasks from file"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.tasks = {
                        name: ScheduledTask(**task_data)
                        for name, task_data in data.items()
                    }
        except Exception as e:
            print(f"[SCHEDULER] Error loading tasks: {e}")
    
    def start(self):
        """Start scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("[SCHEDULER] Started")
    
    def stop(self):
        """Stop scheduler"""
        self.is_running = False
        self._stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self._stop_event.clear()
        print("[SCHEDULER] Stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop (stub for real implementation)"""
        while self.is_running:
            try:
                for task in self.tasks.values():
                    if task.enabled:
                        # Check if task should run (simplified)
                        if self._should_run_task(task):
                            self._trigger_task(task)
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")
            
            self._stop_event.wait(60)  # Check every minute
    
    def _should_run_task(self, task: ScheduledTask) -> bool:
        """Check if task should run now (stub)"""
        # This would be properly implemented with schedule library
        return False
    
    def _trigger_task(self, task: ScheduledTask):
        """Execute a task"""
        try:
            if 'on_task_trigger' in self.callbacks:
                self.callbacks['on_task_trigger'](task)
            print(f"[SCHEDULER] Task '{task.name}' triggered")
        except Exception as e:
            print(f"[SCHEDULER] Error triggering task: {e}")


class AutoOptimizer:
    """Automatic optimization manager"""
    
    def __init__(self, engine, profile_applier):
        """
        Initialize auto optimizer.
        
        Args:
            engine: OptimizationEngine instance
            profile_applier: ProfileApplier instance
        """
        self.engine = engine
        self.profile_applier = profile_applier
        self.scheduler = TaskScheduler()
        
        # Register scheduler callback
        self.scheduler.add_callback('on_task_trigger', self._on_task_trigger)
    
    def create_default_tasks(self):
        """Create default automation tasks"""
        tasks = [
            ScheduledTask(
                name='Daily Morning Boost',
                description='Run memory cleanup every morning at 8:00 AM',
                enabled=False,
                frequency='daily',
                time='08:00',
                profiles=['balanced']
            ),
            ScheduledTask(
                name='Hourly Cache Clear',
                description='Clear system cache every hour',
                enabled=False,
                frequency='hourly',
                time='00:00',
                profiles=['balanced']
            ),
            ScheduledTask(
                name='Weekly Deep Optimize',
                description='Run full optimization every Sunday at midnight',
                enabled=False,
                frequency='weekly',
                time='00:00',
                day_of_week=6,
                profiles=['ultra']
            ),
        ]
        
        for task in tasks:
            self.scheduler.add_task(task)
    
    def start_automation(self):
        """Start the automation scheduler"""
        self.scheduler.start()
    
    def stop_automation(self):
        """Stop the automation scheduler"""
        self.scheduler.stop()
    
    def _on_task_trigger(self, task: ScheduledTask):
        """Handle task trigger"""
        for profile in task.profiles:
            self.profile_applier.apply_profile(profile)
