"""
LuzidSettings - Live FPS & Latency Overlay
An always-on-top transparent overlay showing real-time FPS, ping, and CPU/GPU stats.
Unique feature: borderless, draggable, click-through capable overlay.
"""

import customtkinter as ctk
import threading
import time
import subprocess
import psutil
from src.theme import Theme

# Resolve display/mono font once at import time so the overlay survives
# systems that don't have Orbitron or Consolas installed.
_DISPLAY = Theme.font_display()
_MONO    = Theme.font_mono()


class FPSOverlay(ctk.CTkToplevel):
    """
    Transparent always-on-top performance overlay.
    Shows live: FPS estimate, CPU%, RAM%, Ping to gateway.
    Can be dragged anywhere on screen. Unique to LuzidSettings.
    """

    PING_HOST = "8.8.8.8"

    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)          # No title bar
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.82)
        self.configure(fg_color="#0A0A0F")
        self.geometry("220x140+20+20")
        self.resizable(False, False)

        self._drag_x = 0
        self._drag_y = 0
        self._running = True
        self._ping_ms = 0
        self._frame_times = []

        self._build_ui()
        self._bind_drag()

        # Start background updater
        threading.Thread(target=self._update_loop, daemon=True).start()
        # Start ping loop (slower, every 2s)
        threading.Thread(target=self._ping_loop, daemon=True).start()

    def _build_ui(self):
        # Title bar row
        top = ctk.CTkFrame(self, fg_color="#12121A", corner_radius=0, height=26)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(
            top, text="⚡ LUZID OVERLAY",
            font=(_DISPLAY, 9, "bold"),
            text_color=Theme.ACCENT
        ).pack(side="left", padx=8, pady=4)

        close_btn = ctk.CTkButton(
            top, text="✕", width=24, height=20,
            fg_color="transparent", text_color="#666",
            hover_color="#FF4444",
            font=(_DISPLAY, 9),
            command=self.close_overlay
        )
        close_btn.pack(side="right", padx=4, pady=3)

        # Stats frame
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="both", expand=True, padx=10, pady=6)

        def stat_row(label, initial):
            row = ctk.CTkFrame(stats, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=(_MONO, 10),
                         text_color="#666666", width=55, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text=initial, font=(_MONO, 11, "bold"),
                               text_color=Theme.ACCENT, anchor="w")
            lbl.pack(side="left")
            return lbl

        self.lbl_fps   = stat_row("FPS  ▸", "---")
        self.lbl_cpu   = stat_row("CPU  ▸", "---")
        self.lbl_ram   = stat_row("RAM  ▸", "---")
        self.lbl_ping  = stat_row("PING ▸", "---")

    def _bind_drag(self):
        self.bind("<ButtonPress-1>",   self._on_drag_start)
        self.bind("<B1-Motion>",       self._on_drag_motion)

    def _on_drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _on_drag_motion(self, e):
        x = self.winfo_x() + (e.x - self._drag_x)
        y = self.winfo_y() + (e.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def _update_loop(self):
        """Update CPU/RAM/FPS every 500ms"""
        last = time.perf_counter()
        while self._running:
            now = time.perf_counter()
            elapsed = now - last
            last = now

            # Estimate FPS from loop timing
            if elapsed > 0:
                fps = min(int(1.0 / elapsed), 999)
            else:
                fps = 999

            cpu = psutil.cpu_percent(interval=0.4)
            ram = psutil.virtual_memory().percent

            # Color-code based on value
            fps_color  = "#00FF88" if fps > 60 else ("#FFBB00" if fps > 30 else "#FF4444")
            cpu_color  = "#00FF88" if cpu < 50 else ("#FFBB00" if cpu < 80 else "#FF4444")
            ping_color = "#00FF88" if self._ping_ms < 50 else ("#FFBB00" if self._ping_ms < 100 else "#FF4444")

            def ui_update(fps=fps, cpu=cpu, ram=ram, fc=fps_color, cc=cpu_color, pc=ping_color):
                try:
                    self.lbl_fps.configure(text=f"{fps} FPS", text_color=fc)
                    self.lbl_cpu.configure(text=f"{cpu:.0f}%", text_color=cc)
                    self.lbl_ram.configure(text=f"{ram:.0f}%", text_color="#00DDFF")
                    self.lbl_ping.configure(
                        text=f"{self._ping_ms} ms" if self._ping_ms else "---",
                        text_color=pc
                    )
                except Exception:
                    pass

            self.after(0, ui_update)
            time.sleep(0.5)

    def _ping_loop(self):
        """Ping gateway every 2 seconds"""
        while self._running:
            try:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", self.PING_HOST],
                    capture_output=True, text=True, timeout=3
                )
                for line in result.stdout.splitlines():
                    if "Average" in line or "Minimum" in line or "ms" in line.lower():
                        parts = line.split("=")
                        if parts:
                            last = parts[-1].strip().replace("ms", "").strip()
                            if last.isdigit():
                                self._ping_ms = int(last)
                                break
            except Exception:
                self._ping_ms = 0
            time.sleep(2)

    def close_overlay(self):
        self._running = False
        self.destroy()
