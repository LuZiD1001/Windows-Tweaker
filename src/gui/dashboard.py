"""Dashboard component showing system metrics and health"""

import customtkinter as ctk
from typing import Optional, Callable
from datetime import datetime
import os

from src.theme import Theme
from src.monitor import SystemMonitor


class StatCard(ctk.CTkFrame):
    """Individual statistic card widget"""
    
    def __init__(self, parent, title: str, icon: str, **kwargs):
        super().__init__(
            parent,
            fg_color=Theme.CARD_BG,
            corner_radius=12,
            **kwargs
        )
        
        self.title = title
        self.icon = icon
        self.value = "0%"
        
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(
            title_frame,
            text=f"{icon} {title}",
            text_color=Theme.TEXT_H1,
            font=Theme.FONT_LABEL
        ).pack(side="left")
        
        # Value display
        self.value_label = ctk.CTkLabel(
            self,
            text=self.value,
            text_color=Theme.ACCENT,
            font=(Theme.font_display(), 28, "bold")
        )
        self.value_label.pack(pady=8)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self,
            fg_color=Theme.CARD_BORDER,
            progress_color=Theme.ACCENT
        )
        self.progress.pack(fill="x", padx=12, pady=(0, 12))
        self.progress.set(0)
    
    def update_value(self, value: float, color: str = None):
        """Update card value and progress"""
        self.value = f"{value:.1f}%"
        self.value_label.configure(text=self.value)
        self.progress.set(value / 100.0)
        
        if color:
            self.progress.configure(progress_color=color)


class HealthIndicator(ctk.CTkFrame):
    """System health indicator widget"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=Theme.CARD_BG,
            corner_radius=12,
            **kwargs
        )
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚕️ Health Status",
            text_color=Theme.TEXT_H1,
            font=Theme.FONT_MODULE
        )
        title.pack(pady=12)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self,
            text="EXCELLENT",
            text_color="#00FF88",
            font=(Theme.font_display(), 20, "bold")
        )
        self.status_label.pack(pady=8)
        
        # Status bar
        self.status_bar = ctk.CTkProgressBar(
            self,
            fg_color=Theme.CARD_BORDER,
            progress_color="#00FF88"
        )
        self.status_bar.pack(fill="x", padx=12, pady=(0, 12))
        self.status_bar.set(1.0)
    
    def update_status(self, status: str):
        """Update health status"""
        status_upper = status.upper()
        colors = {
            'excellent': '#00FF88',
            'good': '#00DDFF',
            'fair': '#FFBB00',
            'poor': '#FF4444'
        }
        color = colors.get(status, '#9A9A9A')
        
        self.status_label.configure(text=status_upper, text_color=color)
        self.status_bar.configure(progress_color=color)
        
        # Progress based on status
        progress = {
            'excellent': 1.0,
            'good': 0.75,
            'fair': 0.5,
            'poor': 0.25
        }.get(status, 0)
        self.status_bar.set(progress)


class Dashboard(ctk.CTkFrame):
    """Main dashboard showing system metrics"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.monitor = SystemMonitor()
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="📊 System Dashboard",
            text_color=Theme.TEXT_H1,
            font=Theme.FONT_HEADING
        )
        title.pack(pady=(0, 20))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="both", expand=False, pady=10)
        
        # Configure grid columns
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # CPU Card
        self.cpu_card = StatCard(stats_frame, "CPU Usage", "💻", height=130)
        self.cpu_card.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        
        # RAM Card
        self.ram_card = StatCard(stats_frame, "RAM Usage", "🧠", height=130)
        self.ram_card.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        
        # Disk Card
        self.disk_card = StatCard(stats_frame, "Disk Usage", "💾", height=130)
        self.disk_card.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        
        # Health Indicator
        self.health_card = HealthIndicator(stats_frame, height=130)
        self.health_card.grid(row=0, column=3, padx=8, pady=8, sticky="ew")
        
        # Process/System info frame
        info_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=12)
        info_frame.pack(fill="x", padx=0, pady=10)
        
        # Processes label
        self.processes_label = ctk.CTkLabel(
            info_frame,
            text="📈 Processes: 0 | Temp: 0°C",
            text_color=Theme.TEXT_P,
            font=Theme.FONT_BODY
        )
        self.processes_label.pack(pady=12)
        
        # Start monitoring
        self.monitor.start(callback=self._on_stats_update, interval=2.0)
    
    def _on_stats_update(self, stats: dict):
        """Handle stats update from monitor"""
        try:
            cpu = stats.get('cpu', 0)
            ram = stats.get('ram_percent', 0)
            disk = stats.get('disk', 0)
            temp = stats.get('temp', 0)
            processes = stats.get('processes', 0)
            
            # Determine colors based on thresholds
            cpu_color = self._get_color_for_value(cpu)
            ram_color = self._get_color_for_value(ram)
            disk_color = self._get_color_for_value(disk)
            
            # Update cards
            self.cpu_card.update_value(cpu, cpu_color)
            self.ram_card.update_value(ram, ram_color)
            self.disk_card.update_value(disk, disk_color)
            
            # Update health
            self.health_card.update_status(self.monitor.get_health_status())
            
            # Update process info
            temp_str = f"{temp:.0f}°C" if temp > 0 else "N/A"
            self.processes_label.configure(
                text=f"📈 Processes: {processes} | 🌡️ Temp: {temp_str}"
            )
        except Exception as e:
            print(f"[DASHBOARD] Error updating: {e}")
    
    def _get_color_for_value(self, value: float) -> str:
        """Get color based on percentage value"""
        if value < 30:
            return "#00FF88"  # Green
        elif value < 60:
            return "#00DDFF"  # Cyan
        elif value < 80:
            return "#FFBB00"  # Orange
        else:
            return "#FF4444"  # Red
    
    def cleanup(self):
        """Clean up monitor"""
        if self.monitor:
            self.monitor.stop()
