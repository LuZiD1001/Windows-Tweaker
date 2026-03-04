"""
LuzidSettings — Main Application Window
REDESIGN v4.0  |  Tactical-dark cyber interface
BUG FIX: self.tabs created BEFORE _build_nav so nav buttons can reference it.
NEW: Full Optimizer-16.7 feature set merged as toggles.
"""

import logging
import os
import queue
import subprocess
import threading
import time
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from src.theme import Theme
from src.engine import OptimizationEngine
from src.monitor import SystemMonitor
from src.profiles import ProfileManager, ProfileApplier
from src.fps_overlay import FPSOverlay
from src.process_scanner import ProcessScanner
from src.network_analyzer import NetworkAnalyzer
from src.game_detector import GameDetector
from src.registry_tweaker import RegistryTweaker, REGISTRY_TWEAKS
from src.benchmark import BenchmarkEngine
from src.startup_manager import StartupManager
from src.restore_points import RestorePointManager

logger = logging.getLogger("LuzidSettings.main")
_LOG_FILES = ("luzidmain.log", "luzidauth.log")

# ─── Feature registry ─────────────────────────────────────────────────────────
# Grouped toggles imported from optimizer-16.7 feature set.
# Each entry: (label, reg_key_or_cmd_tuple, description)
# Since we're Python-side, actions are lambda stubs that call engine or subprocess.
# Registry helpers are implemented in _apply_toggle / _revert_toggle.

_GENERAL_TWEAKS = [
    # (display_label, enable_fn_name, disable_fn_name, description)
    ("Enable Performance Tweaks",        "perf_enable",    "perf_disable",
     "Auto-end tasks, GPU priority, system responsiveness registry tweaks."),
    ("Disable Windows Defender",         "defender_off",   "defender_on",
     "Disables real-time protection. Use only in isolated environments."),
    ("Disable Telemetry Services",       "telem_svc_off",  "telem_svc_on",
     "Stops DiagTrack, diagsvc and dmwappushservice."),
    ("Disable Telemetry Tasks",          "telem_task_off", "telem_task_on",
     "Disables scheduled telemetry tasks in Task Scheduler."),
    ("Disable Network Throttling",       "netthrot_off",   "netthrot_on",
     "Removes artificial bandwidth limitations on network stack."),
    ("Disable HPET",                     "hpet_off",       "hpet_on",
     "Disables High Precision Event Timer — may reduce input latency."),
    ("Disable Error Reporting",          "errreport_off",  "errreport_on",
     "Prevents Windows Error Reporting from sending crash data."),
    ("Disable Superfetch / SysMain",     "superfetch_off", "superfetch_on",
     "Stops SysMain service — useful on SSDs."),
    ("Disable Print Spooler Service",    "print_off",      "print_on",
     "Stops the print spooler if no printer is attached."),
    ("Disable Fax Service",              "fax_off",        "fax_on",
     "Removes the legacy fax service from running."),
    ("Disable HomeGroup",                "hgroup_off",     "hgroup_on",
     "Disables HomeGroup networking services."),
    ("Disable SmartScreen",              "smartscreen_off","smartscreen_on",
     "Turns off SmartScreen URL filtering."),
    ("Disable System Restore",           "sysrestore_off", "sysrestore_on",
     "Disables automatic restore point creation."),
    ("Disable Sticky Keys Prompt",       "sticky_off",     "sticky_on",
     "Prevents Sticky Keys dialog on repeated Shift presses."),
    ("Disable Compatibility Assistant",  "compat_off",     "compat_on",
     "Turns off Program Compatibility Assistant."),
    ("Disable Media Player Sharing",     "mediashare_off", "mediashare_on",
     "Stops Windows Media Player network sharing service."),
    ("Disable Sensor Services",          "sensor_off",     "sensor_on",
     "Disables location, accelerometer and other sensor services."),
    ("Disable NTFS Timestamp",           "ntfstime_off",   "ntfstime_on",
     "Stops NTFS from updating last-access timestamps — disk perf boost."),
    ("Disable SMBv1 Protocol",           "smb1_off",       "smb1_on",
     "Removes the insecure SMBv1 protocol."),
    ("Disable SMBv2 Protocol",           "smb2_off",       "smb2_on",
     "Removes SMBv2 if not needed for file sharing."),
    ("Disable Hibernation",              "hibernate_off",  "hibernate_on",
     "Removes hiberfil.sys — frees disk space on desktops."),
    ("Enable Long Paths",                "longpath_on",    "longpath_off",
     "Allows file paths longer than 260 characters."),
    ("Enable UTC Time",                  "utc_on",         "utc_off",
     "Sets hardware clock to UTC — required for dual-boot Linux."),
    ("Remove Menus Delay",               "menudel_on",     "menudel_off",
     "Removes mouse-hover delay on context menus."),
    ("Show All Notification Icons",      "trayall_on",     "trayall_off",
     "Forces all system tray icons to always be visible."),
    ("Enable Detailed Login Screen",     "verblogin_on",   "verblogin_off",
     "Shows verbose status messages during logon/logoff."),
    ("Enable Classic Volume Mixer",      "oldmixer_on",    "oldmixer_off",
     "Restores the old-style per-app volume control panel."),
    ("Modern Standby — Disable",        "modstandby_off", "modstandby_on",
     "Forces S3 sleep instead of Modern Standby (S0ix)."),
]

_PRIVACY_TWEAKS = [
    ("Enhance Privacy",                  "privacy_on",     "privacy_off",
     "Disables activity history, advertising ID, feedback frequency."),
    ("Disable Cortana",                  "cortana_off",    "cortana_on",
     "Disables Cortana assistant and its background processes."),
    ("Disable Windows Ink",              "ink_off",        "ink_on",
     "Removes Windows Ink Workspace from taskbar."),
    ("Disable Spell Checking",           "spell_off",      "spell_on",
     "Turns off auto-correction and spell checking."),
    ("Disable Cloud Clipboard",          "cloudclip_off",  "cloudclip_on",
     "Stops clipboard history syncing to Microsoft cloud."),
    ("Disable NVIDIA Telemetry",         "nvtel_off",      "nvtel_on",
     "Kills NvTmRep, NvTmMon and container telemetry services."),
    ("Disable Google Chrome Telemetry",  "chrometel_off",  "chrometel_on",
     "Removes Chrome's crash reporting and telemetry registry keys."),
    ("Disable Mozilla Firefox Telemetry","fftel_off",      "fftel_on",
     "Disables Firefox telemetry and data reporting policies."),
    ("Disable Visual Studio Telemetry",  "vstel_off",      "vstel_on",
     "Kills VsHub and PerfWatson telemetry services for VS."),
    ("Disable Office 2016 Telemetry",    "officetel_off",  "officetel_on",
     "Stops Office telemetry scheduler and agent tasks."),
    ("Disable Edge Telemetry",           "edgetel_off",    "edgetel_on",
     "Removes Edge metrics collection registry entries."),
    ("Disable Edge Discover / Copilot",  "edgeai_off",     "edgeai_on",
     "Hides Edge Discover bar and disables Bing AI sidebar."),
    ("Disable CoPilot AI",               "copilot_off",    "copilot_on",
     "Removes Windows 11 CoPilot button and service."),
    ("Disable OneDrive",                 "onedrive_off",   "onedrive_on",
     "Prevents OneDrive from syncing and auto-starting."),
    ("Uninstall OneDrive",               "onedrive_uninstall", None,
     "Fully removes OneDrive from the system."),
    ("Disable Insider Service",          "insider_off",    "insider_on",
     "Stops Windows Insider hub and diagnostic services."),
    ("Disable My People",                "people_off",     "people_on",
     "Removes My People bar from taskbar."),
    ("Disable Start Menu Ads",           "ads_off",        "ads_on",
     "Removes suggested apps and ads from Start Menu."),
    ("Disable Search (Taskbar)",         "search_off",     "search_on",
     "Hides the search box/icon from the taskbar."),
]

_WIN11_TWEAKS = [
    ("Enable Gaming Mode",               "gamemode_on",    "gamemode_off",
     "Activates Windows Game Mode for automatic GPU/CPU prioritisation."),
    ("Disable Xbox Live",                "xbox_off",       "xbox_on",
     "Stops all Xbox-related background services."),
    ("Disable Game Bar",                 "gamebar_off",    "gamebar_on",
     "Removes Xbox Game Bar (Win+G overlay)."),
    ("Exclude Drivers from Updates",     "nodrivers_on",   "nodrivers_off",
     "Prevents Windows Update from installing driver updates."),
    ("Disable Automatic Updates",        "autoupdate_off", "autoupdate_on",
     "Stops Windows from downloading and installing updates automatically."),
    ("Disable Microsoft Store Updates",  "storeupdate_off","storeupdate_on",
     "Prevents Store apps from updating automatically."),
    ("Disable TPM 2.0 Check",            "tpm_off",        "tpm_on",
     "Bypasses TPM requirement for Windows 11 installation."),
    ("Enable Classic Right-Click Menu",  "classicctx_on",  "classicctx_off",
     "Restores the full right-click context menu in Windows 11."),
    ("Align Taskbar to Left",            "taskleft_on",    "taskleft_off",
     "Moves taskbar icons to the left side instead of centered."),
    ("Disable Widgets",                  "widgets_off",    "widgets_on",
     "Removes the Widgets button from taskbar."),
    ("Disable Chat (Teams)",             "chat_off",       "chat_on",
     "Removes the Teams/Chat icon from taskbar."),
    ("Disable Snap Assist",              "snap_off",       "snap_on",
     "Turns off Snap layout hover menu."),
    ("Disable Stickers",                 "stickers_off",   "stickers_on",
     "Removes desktop stickers feature."),
    ("Enable Compact Explorer Mode",     "compact_on",     "compact_off",
     "Reduces padding in File Explorer rows."),
    ("Restore Classic Photo Viewer",     "photoviewer_on", "photoviewer_off",
     "Restores Windows Photo Viewer as default image app."),
    ("Disable Virtualization Based Security","vbs_off",    "vbs_on",
     "Disables VBS/HVCI — significant gaming performance gain."),
    ("Remove Cast to Device",            "cast_off",       "cast_on",
     "Removes 'Cast to Device' from right-click context menu."),
    ("Restore Classic Windows Explorer", "oldexplorer_on", "oldexplorer_off",
     "Uses the Windows 10-style File Explorer ribbon."),
    ("Disable Modern Standby (S0ix)",    "modstandby_off", "modstandby_on",
     "Forces legacy S3 power state instead of S0ix."),
    ("News && Interests — Disable",     "newsint_off",    "newsint_on",
     "Removes News and Interests widget from taskbar."),
]

# Toggle state tracker (in-memory, resets on app restart — no registry read-back yet)
_toggle_states: dict = {}

# ─── Helper widgets ───────────────────────────────────────────────────────────

class _Card(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color",      Theme.CARD_BG)
        kw.setdefault("corner_radius", Theme.RADIUS)
        kw.setdefault("border_width",  1)
        kw.setdefault("border_color",  Theme.CARD_BORDER)
        super().__init__(parent, **kw)


class _StatBadge(ctk.CTkFrame):
    def __init__(self, parent, label: str, initial: str = "—", color: str = Theme.TEXT_P):
        super().__init__(parent, fg_color=Theme.CARD_BG,
                         corner_radius=Theme.RADIUS_SM,
                         border_width=1, border_color=Theme.CARD_BORDER)
        ctk.CTkLabel(self, text=label, font=Theme.FONT_BODY_SM,
                     text_color=Theme.TEXT_DIM).pack(side="left", padx=(10, 4), pady=6)
        self._val = ctk.CTkLabel(self, text=initial, font=Theme.FONT_TERMINAL,
                                  text_color=color)
        self._val.pack(side="left", padx=(0, 10), pady=6)

    def set(self, value: str):
        self._val.configure(text=value)


class _MetricRow(ctk.CTkFrame):
    def __init__(self, parent, label: str, initial: str = "—",
                 color: str = Theme.ACCENT, even: bool = False):
        bg = Theme.CARD_BG2 if even else "transparent"
        super().__init__(parent, fg_color=bg, corner_radius=Theme.RADIUS_SM)
        self.pack(fill="x", padx=0, pady=1)
        ctk.CTkLabel(self, text=label, font=Theme.FONT_BODY,
                     text_color=Theme.TEXT_P, anchor="w",
                     width=220).pack(side="left", padx=14, pady=8)
        self._lbl = ctk.CTkLabel(self, text=initial, font=Theme.FONT_TERMINAL,
                                  text_color=color)
        self._lbl.pack(side="right", padx=14)

    def set(self, value: str, color: str = None):
        kw = {"text": value}
        if color:
            kw["text_color"] = color
        self._lbl.configure(**kw)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class LuzidSettings(ctk.CTk):
    """
    LuzidSettings — REDESIGN v4.0 + Optimizer-16.7 features merged.

    FIX: self.tabs is now created FIRST inside _build_body before _build_nav
         so NavButton lambdas can safely reference self.tabs.
    """

    _ALL_TABS = (
        "📊 DASHBOARD",
        "⚡ PROFILES",
        "⚙️ TWEAKS",
        "🛠️ GENERAL",
        "🔒 PRIVACY",
        "🪟 WIN 11",
        "📈 MONITOR",
        "🔧 SETTINGS",
        "📋 LOGS",
        "🔍 PROCESSES",
        "🌐 NETWORK",
        "🗂️ REGISTRY",
        "🏎️ BENCHMARK",
        "🚀 STARTUP",
        "🛡️ RESTORE",
    )

    def __init__(self) -> None:
        super().__init__()
        logger.info("Initialising LuzidSettings REDESIGN v4.0")

        import warnings; warnings.filterwarnings("ignore")
        ctk.set_appearance_mode("dark")

        # ── Services ──────────────────────────────────────────────────
        self.engine           = OptimizationEngine()
        self.monitor          = SystemMonitor()
        self.process_scanner  = ProcessScanner()
        self.network_analyzer = NetworkAnalyzer()
        self.game_detector    = GameDetector()
        self.reg_tweaker      = RegistryTweaker()
        self.benchmark_engine = BenchmarkEngine()
        self.startup_manager  = StartupManager()
        self.restore_manager  = RestorePointManager()
        self._overlay: Optional[FPSOverlay] = None

        # Thread-safe UI update queue — background threads put lambdas here
        # instead of calling self.after() directly (which causes RuntimeError)
        self._ui_queue: queue.Queue = queue.Queue()
        self.after(100, self._process_ui_queue)

        # ── Window ────────────────────────────────────────────────────
        self.title("LUZIDSETTINGS — PERFORMANCE SUITE v4.0")
        self.geometry(f"{Theme.WINDOW_WIDTH}x{Theme.WINDOW_HEIGHT}")
        self.minsize(1100, 720)
        self.configure(fg_color=Theme.BG_MAIN)

        self._build_ui()

        # ── Background services ───────────────────────────────────────
        self.game_detector.on("on_game_detected", self._on_game_detected)
        self.game_detector.on("on_game_closed",   self._on_game_closed)
        self.game_detector.start()
        self.network_analyzer.start(interval=4.0)

        self._monitor_active = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("Window ready")

    # =========================================================================
    # UI CONSTRUCTION — ORDER MATTERS
    # tabs must exist before nav buttons are created
    # =========================================================================

    def _build_ui(self) -> None:
        self._build_header()

        # 1-px separator
        ctk.CTkFrame(self, height=1, fg_color=Theme.CARD_BORDER,
                     corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ── STEP 1: create the tab widget FIRST ──
        content = ctk.CTkFrame(body, fg_color=Theme.BG_MAIN)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(
            content,
            fg_color=Theme.BG_MAIN,
            segmented_button_fg_color=Theme.SIDEBAR,
            segmented_button_selected_color=Theme.ACCENT,
            segmented_button_selected_hover_color=Theme.ACCENT_DIM,
            segmented_button_unselected_color=Theme.SIDEBAR,
            segmented_button_unselected_hover_color=Theme.CARD_BG2,
            text_color=Theme.TEXT_P,
            text_color_disabled=Theme.TEXT_DIM,
        )
        self.tabs.grid(row=0, column=0, sticky="nsew")

        for label in self._ALL_TABS:
            self.tabs.add(label)

        # ── STEP 2: nav can now safely reference self.tabs ──
        self._build_nav(body)

        # ── STEP 3: populate tab content ──
        self._build_dashboard_tab()
        self._build_profiles_tab()
        self._build_tweaks_tab()
        self._build_general_tab()
        self._build_privacy_tab()
        self._build_win11_tab()
        self._build_monitor_tab()
        self._build_settings_tab()
        self._build_logs_tab()
        self._build_processes_tab()
        self._build_network_tab()
        self._build_registry_tab()
        self._build_benchmark_tab()
        self._build_startup_tab()
        self._build_restore_tab()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=Theme.SIDEBAR, height=58, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left accent stripe + logo
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=20, fill="y")
        ctk.CTkFrame(left, width=3, fg_color=Theme.ACCENT,
                     corner_radius=0).pack(side="left", fill="y", padx=(0, 14))
        name_col = ctk.CTkFrame(left, fg_color="transparent")
        name_col.pack(side="left", fill="y", pady=12)
        ctk.CTkLabel(name_col, text="LUZIDSETTINGS",
                     font=Theme.FONT_HEADING, text_color=Theme.TEXT_H1).pack(anchor="w")
        ctk.CTkLabel(name_col, text="PERFORMANCE SUITE  v4.0",
                     font=Theme.FONT_BODY_SM, text_color=Theme.TEXT_P).pack(anchor="w")

        # Centre stat badges
        centre = ctk.CTkFrame(bar, fg_color="transparent")
        centre.place(relx=0.5, rely=0.5, anchor="center")
        self._badge_cpu  = _StatBadge(centre, "CPU",  "—", Theme.ACCENT)
        self._badge_cpu.pack(side="left", padx=4)
        self._badge_ram  = _StatBadge(centre, "RAM",  "—", Theme.INFO)
        self._badge_ram.pack(side="left", padx=4)
        self._badge_disk = _StatBadge(centre, "DISK", "—", Theme.TEXT_P)
        self._badge_disk.pack(side="left", padx=4)
        self._badge_procs= _StatBadge(centre, "PROCS","—", Theme.WARNING)
        self._badge_procs.pack(side="left", padx=4)

        # Right controls
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=18, fill="y")
        self._status_lbl = ctk.CTkLabel(right, text="● READY",
                                         font=Theme.FONT_LABEL, text_color=Theme.SUCCESS)
        self._status_lbl.pack(side="left", padx=(0, 14), pady=17)
        ctk.CTkButton(right, text="▲ FPS", width=72, height=30,
                      fg_color=Theme.CARD_BG2, hover_color=Theme.CARD_BORDER2,
                      text_color=Theme.SUCCESS, font=Theme.FONT_LABEL_BOLD,
                      corner_radius=Theme.RADIUS_SM,
                      command=self._toggle_overlay).pack(side="left", padx=3, pady=14)
        ctk.CTkButton(right, text="❓ GUIDE", width=96, height=30,
                      fg_color=Theme.CARD_BG2, hover_color=Theme.CARD_BORDER2,
                      text_color=Theme.INFO, font=Theme.FONT_LABEL_BOLD,
                      corner_radius=Theme.RADIUS_SM,
                      command=self._open_guided_flow).pack(side="left", padx=3, pady=14)
        ctk.CTkButton(right, text="⚡ FULL OPT", width=100, height=30,
                      fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_DIM,
                      text_color="#000000", font=Theme.FONT_LABEL_BOLD,
                      corner_radius=Theme.RADIUS_SM,
                      command=self._run_full_optimize).pack(side="left", padx=3, pady=14)
        ctk.CTkButton(right, text="—", width=34, height=30,
                      fg_color=Theme.CARD_BG, hover_color=Theme.CARD_BG2,
                      text_color=Theme.TEXT_P, font=Theme.FONT_LABEL_BOLD,
                      corner_radius=Theme.RADIUS_SM,
                      command=self.iconify).pack(side="left", padx=(3, 0), pady=14)

    # ── Nav ───────────────────────────────────────────────────────────────────
    # NOTE: called AFTER self.tabs is created

    def _build_nav(self, parent: ctk.CTkFrame) -> None:
        nav = ctk.CTkFrame(parent, width=Theme.SIDEBAR_WIDTH,
                           fg_color=Theme.SIDEBAR, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsew")
        nav.grid_propagate(False)

        # Logo mark
        mark = ctk.CTkFrame(nav, fg_color=Theme.ACCENT,
                             width=36, height=36, corner_radius=Theme.RADIUS_SM)
        mark.pack(pady=(20, 4), padx=20, anchor="w")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="LZ", font=(Theme.font_display(), 14, "bold"),
                     text_color="#000000").pack(expand=True)

        ctk.CTkLabel(nav, text="NAVIGATION",
                     font=Theme.FONT_LABEL, text_color=Theme.TEXT_DIM).pack(
            anchor="w", padx=20, pady=(14, 6))

        nav_items = [
            ("  Dashboard",  "📊 DASHBOARD"),
            ("  Profiles",   "⚡ PROFILES"),
            ("  Tweaks",     "⚙️ TWEAKS"),
            ("  General",    "🛠️ GENERAL"),
            ("  Privacy",    "🔒 PRIVACY"),
            ("  Win 11",     "🪟 WIN 11"),
            ("  Monitor",    "📈 MONITOR"),
            ("  Settings",   "🔧 SETTINGS"),
            ("  Logs",       "📋 LOGS"),
            ("  Processes",  "🔍 PROCESSES"),
            ("  Network",    "🌐 NETWORK"),
            ("  Registry",   "🗂️ REGISTRY"),
            ("  Benchmark",  "🏎️ BENCHMARK"),
            ("  Startup",    "🚀 STARTUP"),
            ("  Restore",    "🛡️ RESTORE"),
        ]
        for label, key in nav_items:
            ctk.CTkButton(nav, text=label, height=34,
                           corner_radius=Theme.RADIUS_SM,
                           fg_color="transparent", hover_color=Theme.CARD_BG2,
                           text_color=Theme.TEXT_P, font=Theme.FONT_LABEL,
                           anchor="w",
                           command=lambda k=key: self.tabs.set(k)
                           ).pack(fill="x", padx=12, pady=1)

        ctk.CTkFrame(nav, height=1, fg_color=Theme.CARD_BORDER).pack(
            fill="x", padx=12, pady=12)
        ctk.CTkLabel(nav, text="QUICK ACTIONS",
                     font=Theme.FONT_LABEL, text_color=Theme.TEXT_DIM).pack(
            anchor="w", padx=20, pady=(0, 6))

        ctk.CTkButton(nav, text="⚡  FULL OPTIMIZE", height=32,
                      corner_radius=Theme.RADIUS_SM,
                      fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_DIM,
                      text_color="#000000", font=Theme.FONT_LABEL_BOLD,
                      command=self._run_full_optimize).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(nav, text="🛡️  AC SHIELD", height=32,
                      corner_radius=Theme.RADIUS_SM,
                      fg_color=Theme.CARD_BG2, hover_color=Theme.CARD_BORDER2,
                      text_color=Theme.ACCENT, font=Theme.FONT_LABEL_BOLD,
                      command=lambda: self._run_tweak(self.engine.anti_ac)).pack(
            fill="x", padx=12, pady=2)
        ctk.CTkButton(nav, text="🧹  TRACE ERASE", height=32,
                      corner_radius=Theme.RADIUS_SM,
                      fg_color=Theme.CARD_BG2, hover_color=Theme.CARD_BORDER2,
                      text_color=Theme.WARNING, font=Theme.FONT_LABEL_BOLD,
                      command=lambda: self._run_tweak(self.engine.trace_wipe)).pack(
            fill="x", padx=12, pady=2)

    # =========================================================================
    # SHARED HELPERS
    # =========================================================================

    def _scroll(self, tab_label: str) -> ctk.CTkScrollableFrame:
        tab = self.tabs.tab(tab_label)
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                     scrollbar_button_color=Theme.CARD_BORDER2,
                                     scrollbar_button_hover_color=Theme.ACCENT)
        sf.pack(fill="both", expand=True)
        return sf

    def _section(self, parent, text: str, pady=(20, 8), padx=20) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(parent, text=text,
                            font=Theme.FONT_LABEL, text_color=Theme.ACCENT)
        lbl.pack(anchor="w", pady=pady, padx=padx)
        return lbl

    def _action_btn(self, parent, text: str, command,
                    side="right", accent=True, **kw) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            parent, text=text,
            width=kw.pop("width", 130), height=kw.pop("height", 34),
            fg_color=Theme.ACCENT if accent else Theme.CARD_BG2,
            hover_color=Theme.ACCENT_DIM if accent else Theme.CARD_BORDER2,
            text_color="#000000" if accent else Theme.ACCENT,
            font=Theme.FONT_LABEL_BOLD,
            corner_radius=Theme.RADIUS_SM,
            command=command, **kw,
        )
        btn.pack(side=side, padx=4)
        return btn

    def _info_row(self, parent, label: str, value_fn, even: bool = False):
        row = _MetricRow(parent, label, "…", Theme.TEXT_H2, even=even)
        def _load():
            try:   val = value_fn()
            except Exception: val = "N/A"
            # Schedule UI update on the main thread via after() called from main thread
            self._ui_queue.put(lambda r=row, v=val: r.set(str(v)))
        threading.Thread(target=_load, daemon=True).start()
        return row

    def _process_ui_queue(self) -> None:
        """Drain the thread-safe UI queue on the main thread."""
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(100, self._process_ui_queue)

    # =========================================================================
    # TOGGLE ENGINE  (Optimizer-16.7 features)
    # =========================================================================

    def _apply_toggle(self, fn_name: str) -> str:
        """Execute a toggle action by function-name key. Returns status string."""
        import winreg

        def _reg(hive_str, path, name, val, kind=None):
            hive = {"HKLM": winreg.HKEY_LOCAL_MACHINE,
                    "HKCU": winreg.HKEY_CURRENT_USER,
                    "HKCR": winreg.HKEY_CLASSES_ROOT}.get(hive_str, winreg.HKEY_LOCAL_MACHINE)
            k = winreg.CreateKeyEx(hive, path, access=winreg.KEY_SET_VALUE)
            if kind is None:
                kind = winreg.REG_DWORD if isinstance(val, int) else winreg.REG_SZ
            winreg.SetValueEx(k, name, 0, kind, val)
            winreg.CloseKey(k)

        def _svc(name, start=4):
            subprocess.run(f'sc config "{name}" start= disabled',
                            shell=True, capture_output=True)
            subprocess.run(f'sc stop "{name}"',
                            shell=True, capture_output=True)

        def _run(cmd):
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)

        try:
            if fn_name == "perf_enable":
                _reg("HKCU", r"Control Panel\Desktop", "AutoEndTasks", "1")
                _reg("HKCU", r"Control Panel\Desktop", "WaitToKillAppTimeout", "2000")
                _reg("HKCU", r"Control Panel\Desktop", "HungAppTimeout", "1000")
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", 1)
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority", 8)
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Priority", 6)
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Scheduling Category", "High", winreg.REG_SZ)
            elif fn_name == "perf_disable":
                _reg("HKCU", r"Control Panel\Desktop", "AutoEndTasks", "0")
            elif fn_name == "defender_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1)
            elif fn_name == "defender_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 0)
            elif fn_name in ("telem_svc_off", "telem_svc_on"):
                start = 4 if fn_name.endswith("off") else 2
                for svc in ("DiagTrack", "diagsvc", "dmwappushservice"):
                    subprocess.run(f'sc config "{svc}" start= {"disabled" if start==4 else "auto"}',
                                    shell=True, capture_output=True)
            elif fn_name in ("telem_task_off", "telem_task_on"):
                state = "disable" if fn_name.endswith("off") else "enable"
                tasks = [r"Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
                          r"Microsoft\Windows\Application Experience\ProgramDataUpdater",
                          r"Microsoft\Windows\Autochk\Proxy",
                          r"Microsoft\Windows\Customer Experience Improvement Program\Consolidator"]
                for t in tasks:
                    _run(f'schtasks /Change /TN "{t}" /{state}')
            elif fn_name == "netthrot_off":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", 0xffffffff)
            elif fn_name == "netthrot_on":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", 10)
            elif fn_name == "hpet_off":
                _run("bcdedit /deletevalue useplatformclock")
                _run("bcdedit /set disabledynamictick yes")
            elif fn_name == "hpet_on":
                _run("bcdedit /set useplatformclock true")
                _run("bcdedit /deletevalue disabledynamictick")
            elif fn_name == "errreport_off":
                _svc("WerSvc"); _svc("wercplsupport")
            elif fn_name == "errreport_on":
                subprocess.run('sc config "WerSvc" start= demand', shell=True, capture_output=True)
            elif fn_name == "superfetch_off":
                _svc("SysMain")
            elif fn_name == "superfetch_on":
                subprocess.run('sc config "SysMain" start= auto', shell=True, capture_output=True)
                subprocess.run('sc start "SysMain"', shell=True, capture_output=True)
            elif fn_name == "print_off":
                _svc("Spooler")
            elif fn_name == "print_on":
                subprocess.run('sc config "Spooler" start= auto', shell=True, capture_output=True)
            elif fn_name == "fax_off":
                _svc("Fax")
            elif fn_name == "fax_on":
                subprocess.run('sc config "Fax" start= demand', shell=True, capture_output=True)
            elif fn_name == "hgroup_off":
                _svc("HomeGroupListener"); _svc("HomeGroupProvider")
            elif fn_name == "hgroup_on":
                subprocess.run('sc config "HomeGroupListener" start= demand', shell=True, capture_output=True)
            elif fn_name == "smartscreen_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 0)
            elif fn_name == "smartscreen_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 1)
            elif fn_name == "sysrestore_off":
                _run('powershell "Disable-ComputerRestore -Drive C:\\"')
            elif fn_name == "sysrestore_on":
                _run('powershell "Enable-ComputerRestore -Drive C:\\"')
            elif fn_name == "sticky_off":
                _reg("HKCU", r"Control Panel\Accessibility\StickyKeys", "Flags", "506")
            elif fn_name == "sticky_on":
                _reg("HKCU", r"Control Panel\Accessibility\StickyKeys", "Flags", "510")
            elif fn_name == "compat_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisablePCA", 1)
            elif fn_name == "compat_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisablePCA", 0)
            elif fn_name == "mediashare_off":
                _svc("WMPNetworkSvc")
            elif fn_name == "sensor_off":
                for s in ("SensrSvc", "SensorDataService", "SensorService"):
                    _svc(s)
            elif fn_name == "ntfstime_off":
                _run("fsutil behavior set disablelastaccess 1")
            elif fn_name == "ntfstime_on":
                _run("fsutil behavior set disablelastaccess 0")
            elif fn_name == "smb1_off":
                _run("powershell Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart")
            elif fn_name == "smb1_on":
                _run("powershell Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart")
            elif fn_name == "smb2_off":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "SMB2", 0)
            elif fn_name == "smb2_on":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "SMB2", 1)
            elif fn_name == "hibernate_off":
                _run("powercfg /hibernate off")
            elif fn_name == "hibernate_on":
                _run("powercfg /hibernate on")
            elif fn_name == "longpath_on":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled", 1)
            elif fn_name == "longpath_off":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled", 0)
            elif fn_name == "utc_on":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation", "RealTimeIsUniversal", 1)
            elif fn_name == "utc_off":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation", "RealTimeIsUniversal", 0)
            elif fn_name == "menudel_on":
                _reg("HKCU", r"Control Panel\Desktop", "MenuShowDelay", "0")
            elif fn_name == "menudel_off":
                _reg("HKCU", r"Control Panel\Desktop", "MenuShowDelay", "400")
            elif fn_name == "trayall_on":
                _reg("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer", "EnableAutoTray", 0)
            elif fn_name == "trayall_off":
                _reg("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer", "EnableAutoTray", 1)
            elif fn_name == "verblogin_on":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "VerboseStatus", 1)
            elif fn_name == "verblogin_off":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "VerboseStatus", 0)
            elif fn_name == "oldmixer_on":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\MTCUVC", "EnableMtcUvc", 0)
            elif fn_name == "oldmixer_off":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\MTCUVC", "EnableMtcUvc", 1)
            elif fn_name == "modstandby_off":
                _run("powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0")
                _run("reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power /v PlatformAoAcOverride /t REG_DWORD /d 0 /f")
            elif fn_name == "modstandby_on":
                _run("reg delete HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power /v PlatformAoAcOverride /f")
            # PRIVACY
            elif fn_name == "privacy_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", 0)
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0)
                _reg("HKCU", r"SOFTWARE\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod", 0)
            elif fn_name == "cortana_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "CortanaEnabled", 0)
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", 0)
            elif fn_name == "cortana_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "CortanaEnabled", 1)
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", 1)
            elif fn_name == "ink_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\PenWorkspace", "PenWorkspaceButtonDesiredVisibility", 0)
            elif fn_name == "spell_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\TabletTip\1.7", "EnableSpellchecking", 0)
                _reg("HKCU", r"SOFTWARE\Microsoft\TabletTip\1.7", "EnableAutoCorrection", 0)
            elif fn_name == "cloudclip_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Clipboard", "EnableClipboardHistory", 0)
            elif fn_name == "cloudclip_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Clipboard", "EnableClipboardHistory", 1)
            elif fn_name == "nvtel_off":
                for s in ("NvTmRep_CrashReport1_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
                           "NvTmMon_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}"):
                    _svc(s)
            elif fn_name == "chrometel_off":
                _reg("HKLM", r"SOFTWARE\Policies\Google\Chrome", "MetricsReportingEnabled", 0)
            elif fn_name == "fftel_off":
                _reg("HKLM", r"SOFTWARE\Policies\Mozilla\Firefox", "DisableTelemetry", 1)
            elif fn_name == "vstel_off":
                for s in ("VSStandardCollectorService150", "PerfWatson2"):
                    _svc(s)
            elif fn_name == "officetel_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Office\16.0\Common", "QMEnable", 0)
            elif fn_name == "edgetel_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\MicrosoftEdge\Main", "AllowPrelaunch", 0)
            elif fn_name == "edgeai_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Edge", "HubsSidebarEnabled", 0)
            elif fn_name == "copilot_off":
                _reg("HKCU", r"SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1)
            elif fn_name == "copilot_on":
                _reg("HKCU", r"SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 0)
            elif fn_name == "onedrive_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", 1)
            elif fn_name == "onedrive_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", 0)
            elif fn_name == "onedrive_uninstall":
                _run(r'taskkill /f /im OneDrive.exe & %SystemRoot%\SysWOW64\OneDriveSetup.exe /uninstall')
            elif fn_name == "insider_off":
                _svc("wisvc")
            elif fn_name == "people_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", 0)
            elif fn_name == "people_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", 1)
            elif fn_name == "ads_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", 0)
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 0)
            elif fn_name == "ads_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", 1)
            elif fn_name == "search_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 0)
            elif fn_name == "search_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 1)
            # WIN 11
            elif fn_name == "gamemode_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\GameBar", "AutoGameModeEnabled", 1)
                _reg("HKCU", r"SOFTWARE\Microsoft\GameBar", "AllowAutoGameMode", 1)
            elif fn_name == "gamemode_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\GameBar", "AutoGameModeEnabled", 0)
            elif fn_name == "xbox_off":
                for s in ("XblAuthManager","XblGameSave","XboxNetApiSvc","XboxGipSvc"):
                    _svc(s)
            elif fn_name == "gamebar_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)
                _reg("HKCU", r"System\GameConfigStore", "GameDVR_Enabled", 0)
            elif fn_name == "gamebar_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 1)
                _reg("HKCU", r"System\GameConfigStore", "GameDVR_Enabled", 1)
            elif fn_name == "nodrivers_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", "ExcludeWUDriversInQualityUpdate", 1)
            elif fn_name == "nodrivers_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", "ExcludeWUDriversInQualityUpdate", 0)
            elif fn_name == "autoupdate_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoUpdate", 1)
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "AUOptions", 1)
            elif fn_name == "autoupdate_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoUpdate", 0)
            elif fn_name == "storeupdate_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\WindowsStore", "AutoDownload", 2)
            elif fn_name == "storeupdate_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\WindowsStore", "AutoDownload", 4)
            elif fn_name == "tpm_off":
                _reg("HKLM", r"SYSTEM\Setup\MoSetup", "AllowUpgradesWithUnsupportedTPMOrCPU", 1)
            elif fn_name == "tpm_on":
                _reg("HKLM", r"SYSTEM\Setup\MoSetup", "AllowUpgradesWithUnsupportedTPMOrCPU", 0)
            elif fn_name == "classicctx_on":
                _reg("HKCU", r"SOFTWARE\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32", "", "")
            elif fn_name == "classicctx_off":
                import winreg as wr
                try:
                    wr.DeleteKey(wr.HKEY_CURRENT_USER,
                                  r"SOFTWARE\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32")
                except Exception:
                    pass
            elif fn_name == "taskleft_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl", 0)
            elif fn_name == "taskleft_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl", 1)
            elif fn_name == "widgets_off":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests", 0)
            elif fn_name == "widgets_on":
                _reg("HKLM", r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests", 1)
            elif fn_name == "chat_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", 0)
            elif fn_name == "chat_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", 1)
            elif fn_name == "snap_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableSnapBar", 0)
            elif fn_name == "snap_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableSnapBar", 1)
            elif fn_name == "stickers_off":
                _reg("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "StickersEnabled", 0)
            elif fn_name == "compact_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "UseCompactMode", 1)
            elif fn_name == "compact_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "UseCompactMode", 0)
            elif fn_name == "photoviewer_on":
                _run(r'reg add "HKCU\SOFTWARE\Classes\.jpg\OpenWithProgids" /v PhotoViewer.FileAssoc.Tiff /t REG_NONE /f')
            elif fn_name == "vbs_off":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\DeviceGuard", "EnableVirtualizationBasedSecurity", 0)
            elif fn_name == "vbs_on":
                _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\DeviceGuard", "EnableVirtualizationBasedSecurity", 1)
            elif fn_name == "cast_off":
                _run(r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked" /v "{7AD84985-87B4-4a16-BE58-8B72A5B390F7}" /t REG_SZ /f')
            elif fn_name == "oldexplorer_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Internet Explorer\Main", "TabProcGrowth", "0")
            elif fn_name == "newsint_off":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 2)
            elif fn_name == "newsint_on":
                _reg("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 0)
            else:
                return f"⚠ Unknown action: {fn_name}"

            return f"✓ {fn_name} applied"
        except PermissionError:
            return "✗ Run as Administrator for this tweak"
        except Exception as exc:
            return f"✗ Error: {str(exc)[:80]}"

    def _build_toggle_tab(self, tab_label: str, toggle_list: list) -> None:
        """Generic builder for a tab full of toggle rows."""
        scroll = self._scroll(tab_label)

        # Status bar at top
        status_var = tk.StringVar(value="")
        status_lbl = ctk.CTkLabel(scroll, textvariable=status_var,
                                   font=Theme.FONT_BODY_SM, text_color=Theme.SUCCESS)
        status_lbl.pack(anchor="w", padx=20, pady=(0, 4))

        for i, (label, enable_fn, disable_fn, desc) in enumerate(toggle_list):
            key = enable_fn  # unique key for state tracking
            _toggle_states[key] = False
            self._toggle_row(scroll, label, enable_fn, disable_fn, desc,
                              status_var, status_lbl, even=(i % 2 == 0))

    def _toggle_row(self, parent, label: str, enable_fn: str,
                     disable_fn: Optional[str], desc: str,
                     status_var, status_lbl, even: bool = False) -> None:
        key = enable_fn
        bg = Theme.CARD_BG2 if even else Theme.CARD_BG

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=Theme.RADIUS_SM,
                            border_width=1, border_color=Theme.CARD_BORDER)
        row.pack(fill="x", padx=20, pady=3)

        # Icon area
        ico = ctk.CTkFrame(row, width=36, height=36, fg_color=Theme.CARD_BG,
                            corner_radius=Theme.RADIUS_SM)
        ico.pack(side="left", padx=(12, 10), pady=10)
        ico.pack_propagate(False)
        ico_lbl = ctk.CTkLabel(ico, text="●", font=(Theme.font_display(), 12),
                                text_color=Theme.TEXT_DIM)
        ico_lbl.pack(expand=True)

        # Text
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", fill="both", expand=True, pady=10)
        ctk.CTkLabel(txt, text=label, font=Theme.FONT_LABEL_BOLD,
                      text_color=Theme.TEXT_H1, anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text=desc, font=Theme.FONT_BODY_SM,
                      text_color=Theme.TEXT_P, wraplength=600, anchor="w").pack(anchor="w")

        # Toggle switch (CTkSwitch)
        sw = ctk.CTkSwitch(row, text="",
                            width=44, height=22,
                            fg_color=Theme.CARD_BORDER,
                            progress_color=Theme.ACCENT,
                            button_color=Theme.TEXT_H1,
                            button_hover_color=Theme.ACCENT)
        sw.pack(side="right", padx=16, pady=10)

        def _on_toggle():
            active = sw.get()
            _toggle_states[key] = bool(active)
            ico_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_DIM)

            fn = enable_fn if active else (disable_fn or enable_fn)
            if fn is None:
                return

            def _run():
                result = self._apply_toggle(fn)
                color = Theme.SUCCESS if result.startswith("✓") else Theme.ERROR
                self.after(0, lambda r=result, c=color: (
                    status_var.set(r),
                    status_lbl.configure(text_color=c)
                ))
            threading.Thread(target=_run, daemon=True).start()

        sw.configure(command=_on_toggle)

    # =========================================================================
    # DASHBOARD TAB
    # =========================================================================

    def _build_dashboard_tab(self) -> None:
        scroll = self._scroll("📊 DASHBOARD")
        self._section(scroll, "SYSTEM OVERVIEW")

        overview = _Card(scroll)
        overview.pack(fill="x", padx=20, pady=(0, 4))

        rows = [
            ("Processor",  lambda: self.monitor.get_system_info()["processor"]),
            ("Total RAM",  lambda: f"{self.monitor.get_ram_usage()['total']:.1f} GB"),
            ("Disk Total", lambda: f"{self.monitor.get_disk_usage()['total']:.1f} GB"),
            ("GPU",        lambda: self.monitor.get_gpu_info()),
            ("CPU Cores",  lambda: str(self.monitor.get_system_info()["cores"])),
            ("Uptime",     lambda: self.monitor.get_system_info()["uptime"]),
        ]
        for i, (label, fn) in enumerate(rows):
            self._info_row(overview, label, fn, even=(i % 2 == 0))

        self._section(scroll, "LIVE METRICS")
        live = _Card(scroll)
        live.pack(fill="x", padx=20, pady=(0, 20))
        self._dash_cpu   = _MetricRow(live, "CPU Usage",         "—", Theme.ACCENT,  even=False)
        self._dash_ram   = _MetricRow(live, "Memory Usage",      "—", Theme.INFO,    even=True)
        self._dash_disk  = _MetricRow(live, "Disk Usage",        "—", Theme.TEXT_H2, even=False)
        self._dash_procs = _MetricRow(live, "Running Processes", "—", Theme.WARNING, even=True)

    # ── Monitor loop ──────────────────────────────────────────────────────────

    def _monitor_loop(self) -> None:
        while self._monitor_active:
            try:
                cpu   = self.monitor.get_cpu_usage()
                ram   = self.monitor.get_ram_usage()
                disk  = self.monitor.get_disk_usage()
                procs = self.monitor.get_process_count()

                def _refresh(cpu=cpu, ram=ram, disk=disk, procs=procs):
                    try:
                        self._badge_cpu.set(f"{cpu:.0f}%")
                        self._badge_ram.set(f"{ram['percent']:.0f}%")
                        self._badge_disk.set(f"{disk['percent']:.0f}%")
                        self._badge_procs.set(str(procs))
                        self._dash_cpu.set(f"{cpu:.1f}%")
                        self._dash_ram.set(
                            f"{ram['used']:.1f} / {ram['total']:.1f} GB  ({ram['percent']:.0f}%)")
                        self._dash_disk.set(
                            f"{disk['used']:.1f} / {disk['total']:.1f} GB  ({disk['percent']:.0f}%)")
                        self._dash_procs.set(str(procs))
                        if hasattr(self, "_cpu_history"):
                            self._cpu_history.append(cpu)
                            self._cpu_history = self._cpu_history[-60:]
                            self._ram_history.append(ram["percent"])
                            self._ram_history = self._ram_history[-60:]
                            self._redraw_graphs()
                    except Exception:
                        pass
                self.after(0, _refresh)
            except Exception as exc:
                logger.debug("Monitor loop: %s", exc)
            time.sleep(2)

    # =========================================================================
    # PROFILES TAB
    # =========================================================================

    def _build_profiles_tab(self) -> None:
        scroll = self._scroll("⚡ PROFILES")
        self._section(scroll, "QUICK OPTIMISATION PROFILES")
        ctk.CTkLabel(scroll,
                      text="One-click presets — apply the right tweaks for every scenario",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(
            anchor="w", padx=20, pady=(0, 16))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", padx=20)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self.profile_applier = ProfileApplier(self.engine)
        for idx, (key, profile) in enumerate(ProfileManager.get_profile_list()):
            self._profile_card(grid, key, profile, idx)

        self._prof_prog_card = _Card(scroll)
        self._prof_prog_lbl  = ctk.CTkLabel(self._prof_prog_card, text="",
                                              font=Theme.FONT_SUBHEADING,
                                              text_color=Theme.ACCENT)
        self._prof_prog_lbl.pack(pady=(16, 4), padx=20)
        self._prof_prog_bar  = ctk.CTkProgressBar(self._prof_prog_card,
                                                   fg_color=Theme.CARD_BORDER,
                                                   progress_color=Theme.ACCENT, height=3)
        self._prof_prog_bar.pack(fill="x", padx=20, pady=4)
        self._prof_prog_bar.set(0)
        self._prof_status_lbl = ctk.CTkLabel(self._prof_prog_card, text="",
                                              font=Theme.FONT_BODY, text_color=Theme.TEXT_P)
        self._prof_status_lbl.pack(pady=(0, 16), padx=20)

    def _profile_card(self, parent, key: str, profile, idx: int) -> None:
        card = _Card(parent)
        card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="ew")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(inner, text=f"{profile.icon}  {profile.name}",
                      font=Theme.FONT_SUBHEADING, text_color=Theme.ACCENT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(inner, text=profile.description,
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P,
                      wraplength=240).pack(anchor="w", pady=(0, 6))
        mods = ", ".join(m.split(maxsplit=1)[-1] for m in profile.modules[:3])
        ctk.CTkLabel(inner, text=f"Modules: {mods}",
                      font=Theme.FONT_BODY_SM, text_color=Theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))
        ctk.CTkButton(inner, text=f"APPLY  {profile.name.upper()}",
                       height=36, corner_radius=Theme.RADIUS_SM,
                       fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_DIM,
                       text_color="#000000", font=Theme.FONT_LABEL_BOLD,
                       command=lambda k=key: self._apply_profile(k)).pack(fill="x")

    def _apply_profile(self, key: str) -> None:
        self._prof_prog_card.pack(fill="x", padx=20, pady=(16, 0))
        self._prof_prog_lbl.configure(text=f"Applying {key.upper()}…")
        self._prof_prog_bar.set(0)
        def _run():
            self.profile_applier.set_progress_callback(self._on_prof_progress)
            self.profile_applier.apply_profile(key)
        threading.Thread(target=_run, daemon=True).start()

    def _on_prof_progress(self, message: str, progress: float) -> None:
        def _u(m=message, v=progress):
            self._prof_status_lbl.configure(text=m)
            self._prof_prog_bar.set(v)
            if v >= 1.0:
                self.after(1800, self._prof_prog_card.pack_forget)
        self.after(0, _u)

    # =========================================================================
    # TWEAKS TAB
    # =========================================================================

    def _build_tweaks_tab(self) -> None:
        scroll = self._scroll("⚙️ TWEAKS")
        self._section(scroll, "SYSTEM OPTIMISATION TWEAKS")
        for icon, title, desc, action in (
            ("🛡️","Anti-Analysis Shield",
             "Block telemetry servers: Ocean.ac · Echo.ac · Detect.ac", self.engine.anti_ac),
            ("🌐","Network Zenith",
             "Flush DNS & ARP cache — optimise TCP/IP for gaming latency", self.engine.net_zenith),
            ("🚀","Memory Vacuum",
             "Purge standby list and clear RAM fragmentation", self.engine.ram_flush),
            ("⚡","Input Latency Fix",
             "Configure GPU scheduling priority and HPET timer resolution", self.engine.latency_fix),
            ("👻","Trace Eraser",
             "Delete temp files, prefetch cache, and recent-document trails", self.engine.trace_wipe),
        ):
            self._tweak_card(scroll, icon, title, desc, action)

    def _tweak_card(self, parent, icon, title, desc, action) -> None:
        card = _Card(parent)
        card.pack(fill="x", padx=20, pady=5)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=16)
        ico = ctk.CTkFrame(row, width=44, height=44, fg_color=Theme.CARD_BG2,
                            corner_radius=Theme.RADIUS_SM)
        ico.pack(side="left", padx=(0, 14))
        ico.pack_propagate(False)
        ctk.CTkLabel(ico, text=icon, font=(Theme.font_display(), 18)).pack(expand=True)
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(txt, text=title, font=Theme.FONT_SUBHEADING,
                      text_color=Theme.TEXT_H1).pack(anchor="w")
        ctk.CTkLabel(txt, text=desc, font=Theme.FONT_BODY,
                      text_color=Theme.TEXT_P).pack(anchor="w", pady=(3, 0))
        ctk.CTkButton(row, text="RUN", width=90, height=34,
                       corner_radius=Theme.RADIUS_SM,
                       fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_DIM,
                       text_color="#000000", font=Theme.FONT_LABEL_BOLD,
                       command=lambda a=action: self._run_tweak(a)).pack(side="right", padx=(14,0))

    def _run_tweak(self, fn) -> None:
        threading.Thread(target=fn, daemon=True).start()

    def _run_full_optimize(self) -> None:
        self._status_lbl.configure(text="● OPTIMISING…", text_color=Theme.WARNING)
        def _exec():
            for mod in self.engine.modules:
                try: mod["action"]()
                except Exception as exc: logger.warning("Module failed: %s", exc)
            self.after(0, lambda: self._status_lbl.configure(
                text="● READY", text_color=Theme.SUCCESS))
        threading.Thread(target=_exec, daemon=True).start()

    # =========================================================================
    # GENERAL TWEAKS TAB  (optimizer-16.7 general section)
    # =========================================================================

    def _build_general_tab(self) -> None:
        # Build scroll first, add description label inside the scroll frame (avoids pack/grid conflict)
        scroll = self._scroll("🛠️ GENERAL")
        ctk.CTkLabel(scroll, text="System-level performance & service toggles from Optimizer 16.7",
                     font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(
            anchor="w", padx=20, pady=(0, 8))

        # Status bar
        status_var = tk.StringVar(value="")
        status_lbl = ctk.CTkLabel(scroll, textvariable=status_var,
                                   font=Theme.FONT_BODY_SM, text_color=Theme.SUCCESS)
        status_lbl.pack(anchor="w", padx=20, pady=(0, 4))

        for i, (label, enable_fn, disable_fn, desc) in enumerate(_GENERAL_TWEAKS):
            _toggle_states[enable_fn] = False
            self._toggle_row(scroll, label, enable_fn, disable_fn, desc,
                              status_var, status_lbl, even=(i % 2 == 0))

    # =========================================================================
    # PRIVACY TAB  (optimizer-16.7 privacy section)
    # =========================================================================

    def _build_privacy_tab(self) -> None:
        self._build_toggle_tab("🔒 PRIVACY", _PRIVACY_TWEAKS)

    # =========================================================================
    # WIN 11 TAB  (optimizer-16.7 windows 11 section)
    # =========================================================================

    def _build_win11_tab(self) -> None:
        self._build_toggle_tab("🪟 WIN 11", _WIN11_TWEAKS)

    # =========================================================================
    # MONITOR TAB
    # =========================================================================

    def _build_monitor_tab(self) -> None:
        tab = self.tabs.tab("📈 MONITOR")
        self._section(tab, "LIVE SYSTEM MONITOR", pady=(16, 8), padx=20)

        graph_card = _Card(tab)
        graph_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        inner = ctk.CTkFrame(graph_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(inner, text="CPU USAGE  —  60s window",
                      font=Theme.FONT_LABEL, text_color=Theme.ACCENT).pack(anchor="w")
        self._cv_cpu = tk.Canvas(inner, height=160, bg=Theme.BG_MAIN, highlightthickness=0)
        self._cv_cpu.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(inner, text="MEMORY USAGE  —  60s window",
                      font=Theme.FONT_LABEL, text_color=Theme.INFO).pack(anchor="w")
        self._cv_ram = tk.Canvas(inner, height=100, bg=Theme.BG_MAIN, highlightthickness=0)
        self._cv_ram.pack(fill="x", pady=(4, 12))

        stat_row = ctk.CTkFrame(graph_card, fg_color="transparent")
        stat_row.pack(fill="x", padx=14, pady=(0, 12))
        self._mon_cpu  = _StatBadge(stat_row, "CPU",  "—", Theme.ACCENT)
        self._mon_cpu.pack(side="left", padx=4)
        self._mon_ram  = _StatBadge(stat_row, "RAM",  "—", Theme.INFO)
        self._mon_ram.pack(side="left", padx=4)
        self._mon_disk = _StatBadge(stat_row, "DISK", "—", Theme.TEXT_H2)
        self._mon_disk.pack(side="left", padx=4)
        self._mon_proc = _StatBadge(stat_row, "PROCS","—", Theme.WARNING)
        self._mon_proc.pack(side="left", padx=4)

        self._cpu_history: list = [0] * 60
        self._ram_history: list = [0] * 60

    def _redraw_graphs(self) -> None:
        try:
            self._draw_graph(self._cv_cpu, self._cpu_history, Theme.ACCENT)
            self._draw_graph(self._cv_ram, self._ram_history, Theme.INFO)
            self._mon_cpu.set(f"{self._cpu_history[-1]:.0f}%")
            self._mon_ram.set(f"{self._ram_history[-1]:.0f}%")
        except Exception:
            pass

    def _draw_graph(self, canvas: tk.Canvas, data: list, color: str) -> None:
        canvas.delete("all")
        w = canvas.winfo_width(); h = canvas.winfo_height()
        if w < 10 or h < 10:
            return
        n = len(data); step = w / max(n - 1, 1)
        pad_b = 5; pad_t = 8
        for pct in (25, 50, 75):
            y = h - (pct / 100) * (h - pad_t - pad_b) - pad_b
            canvas.create_line(0, y, w, y, fill=Theme.CARD_BORDER2, width=1, dash=(3, 6))
        pts = []
        for i, v in enumerate(data):
            pts.extend([i * step, h - (v / 100) * (h - pad_t - pad_b) - pad_b])
        if len(pts) >= 4:
            canvas.create_polygon(list(pts) + [pts[-2], h, pts[0], h],
                                   fill=color + "18", outline="")
            canvas.create_line(pts, fill=color, width=2, smooth=True)
        if data:
            canvas.create_text(w - 6, 6, text=f"{data[-1]:.0f}%",
                                fill=color, font=(Theme.font_mono(), 9, "bold"), anchor="ne")

    # =========================================================================
    # SETTINGS TAB
    # =========================================================================

    def _build_settings_tab(self) -> None:
        scroll = self._scroll("🔧 SETTINGS")
        self._section(scroll, "APPLICATION SETTINGS")
        ap = _Card(scroll)
        ap.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(ap, text="Appearance Theme",
                      font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_H1).pack(
            anchor="w", padx=16, pady=(14, 4))
        combo = ctk.CTkComboBox(ap, values=["Dark (Default)", "Light", "System"],
                                 fg_color=Theme.CARD_BG2, border_color=Theme.CARD_BORDER2,
                                 text_color=Theme.TEXT_H1, button_color=Theme.ACCENT,
                                 dropdown_fg_color=Theme.CARD_BG2)
        combo.set("Dark (Default)")
        combo.pack(fill="x", padx=16, pady=(0, 14))

        toggles = _Card(scroll)
        toggles.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(toggles, text="Behaviour",
                      font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_H1).pack(
            anchor="w", padx=16, pady=(14, 8))
        for label in ("Auto-start with Windows",
                       "Minimise to system tray on close",
                       "Write detailed log files",
                       "Auto-detect games and apply profiles"):
            ctk.CTkCheckBox(toggles, text=label, font=Theme.FONT_BODY,
                             text_color=Theme.TEXT_H2, fg_color=Theme.ACCENT,
                             checkmark_color="#000000",
                             hover_color=Theme.ACCENT_DIM).pack(
                anchor="w", padx=16, pady=6)
        ctk.CTkFrame(toggles, height=10, fg_color="transparent").pack()

    # =========================================================================
    # LOGS TAB
    # =========================================================================

    def _build_logs_tab(self) -> None:
        scroll = self._scroll("📋 LOGS")
        self._section(scroll, "APPLICATION LOGS")
        self._log_box = ctk.CTkTextbox(scroll, height=480,
                                        fg_color=Theme.CARD_BG,
                                        border_color=Theme.CARD_BORDER, border_width=1,
                                        corner_radius=Theme.RADIUS,
                                        font=Theme.FONT_TERMINAL, text_color=Theme.TEXT_H2)
        self._log_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=6)
        self._action_btn(btn_row, "🔄  REFRESH", self._refresh_logs, side="left")
        self._action_btn(btn_row, "🗑  CLEAR VIEW",
                          lambda: (self._log_box.delete("1.0", "end"),
                                   self._log_box.insert("1.0", "[display cleared]\n")),
                          side="left", accent=False)
        self._refresh_logs()

    def _refresh_logs(self) -> None:
        lines = []
        for fname in _LOG_FILES:
            if os.path.isfile(fname):
                try:
                    with open(fname, encoding="utf-8", errors="replace") as fh:
                        lines.extend(fh.readlines())
                except OSError:
                    pass
        self._log_box.delete("1.0", "end")
        for line in lines[-150:]:
            self._log_box.insert("end", line)
        self._log_box.see("end")

    # =========================================================================
    # PROCESS SCANNER TAB
    # =========================================================================

    def _build_processes_tab(self) -> None:
        tab = self.tabs.tab("🔍 PROCESSES")
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        self._section(hdr, "SMART PROCESS SCANNER", pady=(0, 0))
        self._scan_btn = self._action_btn(hdr, "🔄  SCAN NOW", self._start_scan)
        ctk.CTkLabel(tab, text="Flags telemetry agents, anti-cheat, CPU hogs and memory leaks",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(anchor="w", padx=20)
        self._scan_status = ctk.CTkLabel(tab, text="Press SCAN NOW to analyse",
                                          font=Theme.FONT_BODY_SM, text_color=Theme.TEXT_DIM)
        self._scan_status.pack(anchor="w", padx=20, pady=(2, 8))
        col_hdr = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG2, corner_radius=0)
        col_hdr.pack(fill="x", padx=20)
        for text, w in (("PROCESS", 180), ("CPU", 80), ("RAM", 90), ("FLAG", 200)):
            ctk.CTkLabel(col_hdr, text=text, font=Theme.FONT_LABEL,
                          text_color=Theme.TEXT_DIM, width=w, anchor="w").pack(
                side="left", padx=8, pady=5)
        self._proc_list = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                                   scrollbar_button_color=Theme.CARD_BORDER2)
        self._proc_list.pack(fill="both", expand=True, padx=20, pady=(1, 12))

    def _start_scan(self) -> None:
        self._scan_btn.configure(state="disabled", text="⏳  SCANNING…")
        self._scan_status.configure(text="Collecting process data…")
        for w in self._proc_list.winfo_children():
            w.destroy()
        self.process_scanner.on("on_complete", self._on_scan_done)
        self.process_scanner.scan_async()

    def _on_scan_done(self, results) -> None:
        def _u():
            self._scan_btn.configure(state="normal", text="🔄  SCAN NOW")
            flagged = sum(1 for r in results if r.flag)
            self._scan_status.configure(
                text=f"{len(results)} processes  ·  {flagged} flagged",
                text_color=Theme.ERROR if flagged else Theme.SUCCESS)
            ranked = sorted(results, key=lambda r: (r.flag == "", -r.cpu_percent))
            for i, proc in enumerate(ranked[:80]):
                self._proc_row(self._proc_list, proc, even=(i % 2 == 0))
        self.after(0, _u)

    _FLAG_COLORS = {
        "telemetry": Theme.ERROR, "anticheat": "#A855F7",
        "high_cpu": Theme.WARNING, "high_mem": Theme.INFO, "": Theme.TEXT_P,
    }

    def _proc_row(self, parent, proc, even: bool = False) -> None:
        color = self._FLAG_COLORS.get(proc.flag, Theme.TEXT_P)
        bg = "#1A100E" if proc.flag == "telemetry" else (
             "#0E0F1A" if proc.flag else (Theme.CARD_BG2 if even else "transparent"))
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=Theme.RADIUS_SM)
        row.pack(fill="x", pady=1)
        pfx = "⚠ " if proc.flag else "  "
        ctk.CTkLabel(row, text=f"{pfx}{proc.name}", font=Theme.FONT_TERMINAL,
                      text_color=color, width=180, anchor="w").pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(row, text=f"{proc.cpu_percent:.1f}%", font=Theme.FONT_TERMINAL,
                      text_color=Theme.TEXT_P, width=80).pack(side="left")
        ctk.CTkLabel(row, text=f"{proc.mem_mb:.0f} MB", font=Theme.FONT_TERMINAL,
                      text_color=Theme.TEXT_P, width=90).pack(side="left")
        if proc.flag_reason:
            ctk.CTkLabel(row, text=proc.flag_reason, font=Theme.FONT_BODY_SM,
                          text_color=color).pack(side="left", padx=6)
        if proc.pid and proc.pid > 4:
            ctk.CTkButton(row, text="KILL", width=56, height=22,
                           fg_color=Theme.ERROR, text_color="#FFFFFF",
                           hover_color="#AA0020", font=Theme.FONT_LABEL_BOLD,
                           corner_radius=Theme.RADIUS_SM,
                           command=lambda p=proc.pid, r=row: self._kill_proc(p, r)
                           ).pack(side="right", padx=8, pady=3)

    def _kill_proc(self, pid: int, row: ctk.CTkFrame) -> None:
        def _do():
            ok = self.process_scanner.kill_process(pid)
            def _ui():
                from src.gui.notifications import show_toast
                if ok: row.destroy(); show_toast(self, f"Process {pid} terminated", "success")
                else:  show_toast(self, f"Could not kill {pid} — run as Admin", "error")
            self.after(0, _ui)
        threading.Thread(target=_do, daemon=True).start()

    # =========================================================================
    # NETWORK TAB
    # =========================================================================

    def _build_network_tab(self) -> None:
        tab = self.tabs.tab("🌐 NETWORK")
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        self._section(hdr, "NETWORK ANALYSER", pady=(0, 0))
        self._action_btn(hdr, "🔄  REFRESH", self._refresh_network)
        ctk.CTkLabel(tab, text="Live connections — automatic telemetry & tracker detection",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(anchor="w", padx=20)
        self._net_status = ctk.CTkLabel(tab, text="● Monitoring…",
                                         font=Theme.FONT_LABEL, text_color=Theme.SUCCESS)
        self._net_status.pack(anchor="w", padx=20, pady=(4, 4))
        col_hdr = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG2, corner_radius=0)
        col_hdr.pack(fill="x", padx=20)
        for text, w in (("PROCESS", 150), ("REMOTE HOST", 210), ("ADDR", 160), ("STATUS", 110)):
            ctk.CTkLabel(col_hdr, text=text, font=Theme.FONT_LABEL,
                          text_color=Theme.TEXT_DIM, width=w, anchor="w").pack(
                side="left", padx=8, pady=5)
        self._net_list = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                                  scrollbar_button_color=Theme.CARD_BORDER2)
        self._net_list.pack(fill="both", expand=True, padx=20, pady=(1, 12))
        self.network_analyzer.on("on_update", self._on_net_update)

    def _on_net_update(self, connections) -> None:
        suspicious = sum(1 for c in connections if c.suspicious)
        def _u():
            try:
                self._net_status.configure(
                    text=f"● {len(connections)} connections  ·  {suspicious} suspicious",
                    text_color=Theme.ERROR if suspicious else Theme.SUCCESS)
            except Exception: pass
        self.after(0, _u)

    def _refresh_network(self) -> None:
        conns = self.network_analyzer.get_connections()
        for w in self._net_list.winfo_children():
            w.destroy()
        suspicious = sum(1 for c in conns if c.suspicious)
        self._net_status.configure(
            text=f"● {len(conns)} connections  ·  {suspicious} suspicious",
            text_color=Theme.ERROR if suspicious else Theme.SUCCESS)
        for i, conn in enumerate(sorted(conns,
                                         key=lambda c: (not c.suspicious, c.process_name))[:60]):
            self._net_row(self._net_list, conn, even=(i % 2 == 0))

    def _net_row(self, parent, conn, even: bool = False) -> None:
        color = Theme.ERROR if conn.suspicious else Theme.TEXT_P
        bg = "#1A0E0E" if conn.suspicious else (Theme.CARD_BG2 if even else "transparent")
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=Theme.RADIUS_SM)
        row.pack(fill="x", pady=1)
        pfx = "⚠ " if conn.suspicious else "  "
        ctk.CTkLabel(row, text=f"{pfx}{conn.process_name}", font=Theme.FONT_TERMINAL,
                      text_color=color, width=150, anchor="w").pack(side="left", padx=8, pady=3)
        host = (conn.remote_host[:26]+"…") if len(conn.remote_host)>28 else conn.remote_host
        ctk.CTkLabel(row, text=host, font=Theme.FONT_TERMINAL,
                      text_color=color if conn.suspicious else Theme.TEXT_H2,
                      width=210, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=conn.remote_addr, font=Theme.FONT_TERMINAL,
                      text_color=Theme.TEXT_P, width=160, anchor="w").pack(side="left")
        sc = Theme.SUCCESS if conn.status == "ESTABLISHED" else Theme.TEXT_P
        ctk.CTkLabel(row, text=conn.status, font=Theme.FONT_TERMINAL,
                      text_color=sc, width=110).pack(side="left")

    # =========================================================================
    # REGISTRY TAB
    # =========================================================================

    def _build_registry_tab(self) -> None:
        tab = self.tabs.tab("🗂️ REGISTRY")
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        self._section(hdr, "REGISTRY TWEAKER", pady=(0, 0))
        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right")
        self._action_btn(btn_frame, "✅ APPLY ALL",  self._reg_apply_all)
        self._action_btn(btn_frame, "↩ REVERT ALL", self._reg_revert_all, accent=False)
        ctk.CTkLabel(tab, text="Deep Windows registry tweaks — auto-backed up. All reversible.",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(anchor="w", padx=20)
        s = self.reg_tweaker.get_stats()
        self._reg_stats_lbl = ctk.CTkLabel(
            tab, text=f"{s['applied']} / {s['total']} active  ·  {s['backup_count']} backed up",
            font=Theme.FONT_LABEL, text_color=Theme.SUCCESS)
        self._reg_stats_lbl.pack(anchor="w", padx=20, pady=(2, 8))
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                         scrollbar_button_color=Theme.CARD_BORDER2)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self._reg_result_lbl = ctk.CTkLabel(scroll, text="", font=Theme.FONT_BODY,
                                              text_color=Theme.SUCCESS, wraplength=900)
        self._reg_result_lbl.pack(anchor="w", padx=4, pady=(0, 6))
        cats = self.reg_tweaker.get_tweaks_by_category()
        self._reg_btns: dict = {}
        for cat, tweaks in cats.items():
            cat_card = _Card(scroll, fg_color=Theme.CARD_BG2)
            cat_card.pack(fill="x", pady=5)
            ctk.CTkLabel(cat_card, text=cat, font=Theme.FONT_SUBHEADING,
                          text_color=Theme.ACCENT).pack(anchor="w", padx=16, pady=(12, 4))
            for tweak in tweaks:
                row = ctk.CTkFrame(cat_card, fg_color=Theme.CARD_BG,
                                    corner_radius=Theme.RADIUS_SM)
                row.pack(fill="x", padx=10, pady=3)
                col = ctk.CTkFrame(row, fg_color="transparent")
                col.pack(side="left", fill="both", expand=True, padx=14, pady=10)
                ctk.CTkLabel(col, text=tweak.name, font=Theme.FONT_LABEL_BOLD,
                              text_color=Theme.TEXT_H1).pack(anchor="w")
                ctk.CTkLabel(col, text=tweak.description, font=Theme.FONT_BODY_SM,
                              text_color=Theme.TEXT_P).pack(anchor="w")
                applied = self.reg_tweaker.is_applied(tweak.name)
                btn = ctk.CTkButton(row,
                                     text="APPLIED ✓" if applied else "APPLY",
                                     width=100, height=30,
                                     fg_color=Theme.SUCCESS if applied else Theme.ACCENT,
                                     text_color="#000000",
                                     hover_color=Theme.ACCENT_DIM,
                                     font=Theme.FONT_LABEL_BOLD,
                                     corner_radius=Theme.RADIUS_SM,
                                     command=lambda t=tweak: self._reg_toggle(t))
                btn.pack(side="right", padx=10, pady=8)
                self._reg_btns[tweak.name] = btn

    def _reg_toggle(self, tweak) -> None:
        def _run():
            if self.reg_tweaker.is_applied(tweak.name):
                ok, msg = self.reg_tweaker.revert_tweak(tweak)
            else:
                ok, msg = self.reg_tweaker.apply_tweak(tweak)
            self.after(0, lambda m=msg, t=tweak: self._reg_update_btn(t, m))
        threading.Thread(target=_run, daemon=True).start()

    def _reg_update_btn(self, tweak, msg: str) -> None:
        applied = self.reg_tweaker.is_applied(tweak.name)
        btn = self._reg_btns.get(tweak.name)
        if btn:
            btn.configure(text="APPLIED ✓" if applied else "APPLY",
                           fg_color=Theme.SUCCESS if applied else Theme.ACCENT)
        self._reg_result_lbl.configure(text=msg)
        s = self.reg_tweaker.get_stats()
        self._reg_stats_lbl.configure(
            text=f"{s['applied']} / {s['total']} active  ·  {s['backup_count']} backed up")

    def _reg_apply_all(self) -> None:
        def _run():
            self.reg_tweaker.apply_all(
                lambda msg, p: self.after(0, lambda m=msg: self._reg_result_lbl.configure(text=m)))
            self.after(0, self._reg_refresh_btns)
        threading.Thread(target=_run, daemon=True).start()

    def _reg_revert_all(self) -> None:
        def _run():
            self.reg_tweaker.revert_all(
                lambda msg, p: self.after(0, lambda m=msg: self._reg_result_lbl.configure(text=m)))
            self.after(0, self._reg_refresh_btns)
        threading.Thread(target=_run, daemon=True).start()

    def _reg_refresh_btns(self) -> None:
        for tweak in REGISTRY_TWEAKS:
            btn = self._reg_btns.get(tweak.name)
            if btn:
                applied = self.reg_tweaker.is_applied(tweak.name)
                btn.configure(text="APPLIED ✓" if applied else "APPLY",
                               fg_color=Theme.SUCCESS if applied else Theme.ACCENT)
        s = self.reg_tweaker.get_stats()
        self._reg_stats_lbl.configure(
            text=f"{s['applied']} / {s['total']} active  ·  {s['backup_count']} backed up")

    # =========================================================================
    # BENCHMARK TAB
    # =========================================================================

    def _build_benchmark_tab(self) -> None:
        tab = self.tabs.tab("🏎️ BENCHMARK")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                         scrollbar_button_color=Theme.CARD_BORDER2)
        scroll.pack(fill="both", expand=True)
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        self._section(hdr, "SYSTEM BENCHMARK", pady=(0, 0))
        self._bench_btn = self._action_btn(hdr, "🏎️  RUN BENCHMARK",
                                            self._run_benchmark, width=160)
        ctk.CTkLabel(scroll, text="CPU · RAM · Disk · Network — compare scores before & after tweaks",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(anchor="w", padx=20)
        self._bench_prog_lbl = ctk.CTkLabel(scroll, text="Press RUN to start",
                                              font=Theme.FONT_BODY_SM, text_color=Theme.TEXT_DIM)
        self._bench_prog_lbl.pack(anchor="w", padx=20, pady=(6, 2))
        self._bench_prog = ctk.CTkProgressBar(scroll, fg_color=Theme.CARD_BORDER,
                                               progress_color=Theme.ACCENT, height=3)
        self._bench_prog.pack(fill="x", padx=20, pady=(0, 14))
        self._bench_prog.set(0)
        score_row = ctk.CTkFrame(scroll, fg_color="transparent")
        score_row.pack(fill="x", padx=20, pady=(0, 14))
        score_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        def _sc(parent, label, col):
            card = _Card(parent)
            card.grid(row=0, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(card, text=label, font=Theme.FONT_LABEL,
                          text_color=Theme.TEXT_P).pack(pady=(12, 2))
            v = ctk.CTkLabel(card, text="—", font=Theme.FONT_MONO_LG,
                              text_color=Theme.ACCENT)
            v.pack(pady=(0, 12))
            return v

        self._bc_cpu  = _sc(score_row, "CPU", 0)
        self._bc_ram  = _sc(score_row, "RAM", 1)
        self._bc_disk = _sc(score_row, "DISK", 2)
        self._bc_net  = _sc(score_row, "NETWORK", 3)
        self._bc_tot  = _sc(score_row, "OVERALL", 4)
        self._section(scroll, "SCORE HISTORY", pady=(16, 8))
        self._bench_hist = _Card(scroll)
        self._bench_hist.pack(fill="x", padx=20, pady=(0, 20))
        self._bench_refresh_history()
        self.benchmark_engine.on("on_complete", self._on_bench_complete)

    def _run_benchmark(self) -> None:
        self._bench_btn.configure(state="disabled", text="⏳ RUNNING…")
        self._bench_prog.set(0)
        profile = (self.profile_applier.get_current_profile()
                   if hasattr(self, "profile_applier") else "none")
        self.benchmark_engine.run_full_async(profile=profile,
                                              progress_cb=self._bench_prog_cb)

    def _bench_prog_cb(self, msg: str, pct: float) -> None:
        self.after(0, lambda m=msg, v=pct: (
            self._bench_prog_lbl.configure(text=m),
            self._bench_prog.set(v),
        ))

    def _on_bench_complete(self, result) -> None:
        def _u():
            self._bench_btn.configure(state="normal", text="🏎️  RUN BENCHMARK")
            grade = self.benchmark_engine.score_grade(result.overall_score)
            color = self.benchmark_engine.score_color(result.overall_score)
            self._bc_cpu.configure(text=f"{result.cpu_score}\nMh/s")
            self._bc_ram.configure(text=f"{result.ram_score}\nMB/s")
            self._bc_disk.configure(text=f"{result.disk_score}\nMB/s")
            self._bc_net.configure(text=f"{result.network_latency}\nms")
            self._bc_tot.configure(text=f"{result.overall_score}\n{grade}", text_color=color)
            self._bench_refresh_history()
        self.after(0, _u)

    def _bench_refresh_history(self) -> None:
        for w in self._bench_hist.winfo_children():
            w.destroy()
        history = self.benchmark_engine.get_history()
        if not history:
            ctk.CTkLabel(self._bench_hist, text="No history yet — run your first benchmark",
                          font=Theme.FONT_BODY, text_color=Theme.TEXT_DIM).pack(pady=16)
            return
        col_hdr = ctk.CTkFrame(self._bench_hist, fg_color=Theme.CARD_BG2, corner_radius=0)
        col_hdr.pack(fill="x", padx=6, pady=(6, 2))
        for text, w in (("DATE",160),("CPU",90),("RAM",90),("DISK",90),
                         ("NET",90),("SCORE",90),("GRADE",70),("PROFILE",130)):
            ctk.CTkLabel(col_hdr, text=text, font=Theme.FONT_LABEL,
                          text_color=Theme.TEXT_DIM, width=w, anchor="w").pack(
                side="left", padx=6, pady=4)
        best = self.benchmark_engine.get_best()
        for i, r in enumerate(reversed(history[-10:])):
            is_best = best and r.overall_score == best.overall_score
            bg = "#101A14" if is_best else (Theme.CARD_BG2 if i%2==0 else "transparent")
            row = ctk.CTkFrame(self._bench_hist, fg_color=bg, corner_radius=Theme.RADIUS_SM)
            row.pack(fill="x", padx=6, pady=1)
            ts = r.timestamp[:16].replace("T", " ")
            color = self.benchmark_engine.score_color(r.overall_score)
            grade = self.benchmark_engine.score_grade(r.overall_score)
            pfx = "★ " if is_best else "  "
            for text, w in (
                (f"{pfx}{ts}",160),(f"{r.cpu_score}M",90),(f"{r.ram_score}M",90),
                (f"{r.disk_score}M",90),(f"{r.network_latency}ms",90),
                (str(r.overall_score),90),(grade,70),(r.profile_applied,130),
            ):
                tc = color if text.strip() in (str(r.overall_score), grade) else Theme.TEXT_P
                ctk.CTkLabel(row, text=text, font=Theme.FONT_TERMINAL,
                              text_color=tc, width=w, anchor="w").pack(
                    side="left", padx=6, pady=3)

    # =========================================================================
    # STARTUP TAB
    # =========================================================================

    def _build_startup_tab(self) -> None:
        tab = self.tabs.tab("🚀 STARTUP")
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        self._section(hdr, "STARTUP MANAGER", pady=(0, 0))
        self._startup_btn = self._action_btn(hdr, "🔄  SCAN", self._startup_scan, width=110)
        ctk.CTkLabel(tab, text="View and disable startup programs — all changes are reversible",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(anchor="w", padx=20)
        self._startup_stats = ctk.CTkLabel(tab, text="Press SCAN to load entries",
                                            font=Theme.FONT_LABEL, text_color=Theme.TEXT_DIM)
        self._startup_stats.pack(anchor="w", padx=20, pady=(2, 6))
        col_hdr = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG2, corner_radius=0)
        col_hdr.pack(fill="x", padx=20)
        for text, w in (("NAME",190),("PATH",290),("SOURCE",90),("APP",140),("TIP",160)):
            ctk.CTkLabel(col_hdr, text=text, font=Theme.FONT_LABEL,
                          text_color=Theme.TEXT_DIM, width=w, anchor="w").pack(
                side="left", padx=8, pady=5)
        self._startup_list = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                                     scrollbar_button_color=Theme.CARD_BORDER2)
        self._startup_list.pack(fill="both", expand=True, padx=20, pady=(1, 12))
        self.startup_manager.on("on_complete", self._on_startup_done)

    def _startup_scan(self) -> None:
        self._startup_btn.configure(state="disabled", text="⏳ SCANNING…")
        self._startup_stats.configure(text="Scanning startup entries…")
        for w in self._startup_list.winfo_children():
            w.destroy()
        self.startup_manager.scan_async()

    def _on_startup_done(self, entries) -> None:
        def _u():
            self._startup_btn.configure(state="normal", text="🔄  SCAN")
            s = self.startup_manager.get_stats()
            self._startup_stats.configure(
                text=f"{s['total']} entries  ·  {s['enabled']} enabled  ·  "
                     f"{s['disabled']} disabled  ·  ⚠ {s['bloat_detected']} bloat",
                text_color=Theme.WARNING if s["bloat_detected"]>0 else Theme.SUCCESS)
            for i, entry in enumerate(sorted(entries,
                    key=lambda e: (e.enabled, e.recommendation!="Keep enabled"), reverse=True)):
                self._startup_row(self._startup_list, entry, even=(i%2==0))
        self.after(0, _u)

    def _startup_row(self, parent, entry, even: bool = False) -> None:
        if entry.is_system or not entry.enabled: color = Theme.TEXT_DIM; bg = "transparent"
        elif entry.recommendation == "Keep enabled": color = Theme.SUCCESS; bg = "transparent"
        elif "Safe to disable" in entry.recommendation:
            color = Theme.WARNING; bg = "#191400" if not even else "#1F1A00"
        else: color = Theme.TEXT_P; bg = Theme.CARD_BG2 if even else "transparent"

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=Theme.RADIUS_SM)
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text=entry.name[:26], font=Theme.FONT_TERMINAL,
                      text_color=color, width=190, anchor="w").pack(side="left", padx=8, pady=3)
        path = (entry.path[:36]+"…") if len(entry.path)>38 else entry.path
        ctk.CTkLabel(row, text=path, font=Theme.FONT_BODY_SM,
                      text_color=Theme.TEXT_P, width=290, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=entry.source, font=Theme.FONT_TERMINAL,
                      text_color=Theme.ACCENT, width=90, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=entry.known_app or "—", font=Theme.FONT_TERMINAL,
                      text_color=color, width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=entry.recommendation, font=Theme.FONT_BODY_SM,
                      text_color=color, width=160, anchor="w").pack(side="left")
        if not entry.is_system:
            if entry.enabled:
                ctk.CTkButton(row, text="DISABLE", width=80, height=24,
                               fg_color=Theme.ERROR, text_color="#FFFFFF",
                               hover_color="#AA0020", font=Theme.FONT_LABEL_BOLD,
                               corner_radius=Theme.RADIUS_SM,
                               command=lambda e=entry, r=row: self._startup_disable(e, r)
                               ).pack(side="right", padx=8, pady=3)
            else:
                ctk.CTkButton(row, text="ENABLE", width=80, height=24,
                               fg_color=Theme.SUCCESS, text_color="#000000",
                               hover_color="#00B860", font=Theme.FONT_LABEL_BOLD,
                               corner_radius=Theme.RADIUS_SM,
                               command=lambda e=entry, r=row: self._startup_enable(e, r)
                               ).pack(side="right", padx=8, pady=3)

    def _startup_disable(self, entry, row) -> None:
        def _do():
            ok, msg = self.startup_manager.disable_entry(entry)
            def _ui():
                from src.gui.notifications import show_toast
                show_toast(self, msg, "success" if ok else "error")
                if ok: row.destroy()
            self.after(0, _ui)
        threading.Thread(target=_do, daemon=True).start()

    def _startup_enable(self, entry, row) -> None:
        def _do():
            ok, msg = self.startup_manager.enable_entry(entry)
            def _ui():
                from src.gui.notifications import show_toast
                show_toast(self, msg, "success" if ok else "error")
                if ok: row.destroy()
            self.after(0, _ui)
        threading.Thread(target=_do, daemon=True).start()

    # =========================================================================
    # RESTORE TAB
    # =========================================================================

    def _build_restore_tab(self) -> None:
        scroll = self._scroll("🛡️ RESTORE")
        self._section(scroll, "SYSTEM RESTORE POINTS")
        ctk.CTkLabel(scroll,
                      text="Create safety snapshots before applying tweaks. Fully reversible.",
                      font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(
            anchor="w", padx=20, pady=(0, 14))
        create_card = _Card(scroll)
        create_card.pack(fill="x", padx=20, pady=(0, 16))
        inner = ctk.CTkFrame(create_card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner, text="Create Restore Point",
                      font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_H1).pack(anchor="w", pady=(0,10))
        label_row = ctk.CTkFrame(inner, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(label_row, text="Label:", font=Theme.FONT_BODY,
                      text_color=Theme.TEXT_H2, width=60).pack(side="left")
        self._restore_entry = ctk.CTkEntry(label_row,
                                            placeholder_text="e.g. Before Registry Tweaks",
                                            fg_color=Theme.CARD_BG2,
                                            border_color=Theme.CARD_BORDER2,
                                            text_color=Theme.TEXT_H1, width=400)
        self._restore_entry.pack(side="left", padx=10)
        self._restore_btn = ctk.CTkButton(inner, text="🛡️  CREATE NOW",
                                           height=36, corner_radius=Theme.RADIUS_SM,
                                           fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_DIM,
                                           text_color="#000000", font=Theme.FONT_LABEL_BOLD,
                                           command=self._create_restore_point)
        self._restore_btn.pack(anchor="w", pady=(0, 8))
        self._restore_prog_lbl = ctk.CTkLabel(inner, text="",
                                               font=Theme.FONT_BODY, text_color=Theme.TEXT_P)
        self._restore_prog_lbl.pack(anchor="w")
        self._restore_prog = ctk.CTkProgressBar(inner, fg_color=Theme.CARD_BORDER,
                                                 progress_color=Theme.ACCENT, height=3)
        self._restore_prog.pack(fill="x", pady=(4, 0))
        self._restore_prog.set(0)
        self._section(scroll, "EXISTING RESTORE POINTS", pady=(20, 8))
        self._restore_list = _Card(scroll)
        self._restore_list.pack(fill="x", padx=20, pady=(0, 8))
        self._action_btn(scroll, "🔄  REFRESH LIST", self._refresh_restore_list,
                          side="left", accent=False, width=140)
        ctk.CTkFrame(scroll, height=8, fg_color="transparent").pack()
        ctk.CTkLabel(scroll,
                      text="💡  Windows Settings → System → Recovery → Open System Restore",
                      font=Theme.FONT_BODY_SM, text_color=Theme.TEXT_DIM).pack(
            anchor="w", padx=20, pady=(10, 20))
        self._refresh_restore_list()
        self.restore_manager.on("on_created", self._on_restore_created)

    def _create_restore_point(self) -> None:
        label = self._restore_entry.get().strip()
        self._restore_btn.configure(state="disabled", text="⏳ CREATING…")
        self._restore_prog.set(0)
        self.restore_manager.create_async(description=label or None,
                                           progress_cb=self._restore_prog_cb)

    def _restore_prog_cb(self, msg: str, pct: float) -> None:
        self.after(0, lambda m=msg, v=pct: (
            self._restore_prog_lbl.configure(text=m),
            self._restore_prog.set(v),
        ))

    def _on_restore_created(self, ok: bool, msg: str) -> None:
        def _u():
            self._restore_btn.configure(state="normal", text="🛡️  CREATE NOW")
            if ok:
                self._refresh_restore_list()
                from src.gui.notifications import show_toast
                show_toast(self, "✓ Restore point created!", "success")
        self.after(0, _u)

    def _refresh_restore_list(self) -> None:
        for w in self._restore_list.winfo_children():
            w.destroy()
        def _load():
            points = self.restore_manager.list_luzid_points()
            def _u():
                if not points:
                    ctk.CTkLabel(self._restore_list,
                                  text="No LuzidSettings restore points found yet.",
                                  font=Theme.FONT_BODY, text_color=Theme.TEXT_P).pack(pady=16)
                    return
                for i, p in enumerate(points[:10]):
                    bg = Theme.CARD_BG2 if i%2==0 else "transparent"
                    row = ctk.CTkFrame(self._restore_list, fg_color=bg,
                                       corner_radius=Theme.RADIUS_SM)
                    row.pack(fill="x", padx=8, pady=2)
                    ctk.CTkLabel(row, text=f"#{p.sequence_number}",
                                  font=Theme.FONT_MONO_MD, text_color=Theme.ACCENT,
                                  width=55).pack(side="left", padx=10, pady=8)
                    ctk.CTkLabel(row, text=p.description, font=Theme.FONT_LABEL_BOLD,
                                  text_color=Theme.TEXT_H1, width=380,
                                  anchor="w").pack(side="left")
                    ctk.CTkLabel(row, text=str(p.creation_time)[:16],
                                  font=Theme.FONT_TERMINAL,
                                  text_color=Theme.TEXT_P).pack(side="right", padx=14)
            self.after(0, _u)
        threading.Thread(target=_load, daemon=True).start()

    # =========================================================================
    # FPS OVERLAY
    # =========================================================================

    def _toggle_overlay(self) -> None:
        if self._overlay and self._overlay.winfo_exists():
            self._overlay.close_overlay(); self._overlay = None
        else:
            self._overlay = FPSOverlay(self)

    # =========================================================================
    # GUIDED FLOW
    # =========================================================================

    def _open_guided_flow(self) -> None:
        """Friendly guided workflow for first-time users."""
        # Re-focus existing window if it's already open
        if hasattr(self, "_guide_win") and self._guide_win.winfo_exists():
            self._guide_win.focus_force()
            return

        win = ctk.CTkToplevel(self)
        self._guide_win = win
        win.title("LuzidSettings — Geführter Modus")
        win.geometry("560x420")
        win.configure(fg_color=Theme.BG_DEEP)
        win.transient(self)
        win.grab_set()

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            container,
            text="Geführter Einstieg",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_H1,
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            container,
            text=(
                "Empfohlener Ablauf für neue Nutzer:\n"
                "1) Sicherungspunkt anlegen\n"
                "2) Profil wählen\n"
                "3) Optional: Volle Optimierung ausführen"
            ),
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_P,
            justify="left",
        ).pack(anchor="w", pady=(0, 18))

        steps = ctk.CTkFrame(container, fg_color="transparent")
        steps.pack(fill="both", expand=True)

        # Step 1 — Restore point
        card1 = _Card(steps)
        card1.pack(fill="x", pady=4)
        inner1 = ctk.CTkFrame(card1, fg_color="transparent")
        inner1.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            inner1,
            text="🛡️  Schritt 1 — Wiederherstellungspunkt",
            font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_H1,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner1,
            text="Lege einen Systemwiederherstellungspunkt an, bevor du starke Tweaks aktivierst.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_P,
            wraplength=480,
        ).pack(anchor="w", pady=(4, 6))

        def _goto_restore():
            self.tabs.set("🛡️ RESTORE")
            try:
                self._restore_entry.delete(0, "end")
                self._restore_entry.insert(0, "Vor LuzidSettings-Guided-Optimierung")
            except Exception:
                pass
            from src.gui.notifications import show_toast
            show_toast(self, "Wechsle zum Restore-Tab – hier kannst du sicher speichern.", "info")

        self._action_btn(inner1, "🛡️  RESTORE TAB ÖFFNEN", _goto_restore, side="right", accent=False)

        # Step 2 — Profile
        card2 = _Card(steps)
        card2.pack(fill="x", pady=4)
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            inner2,
            text="⚡  Schritt 2 — Profil wählen",
            font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_H1,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner2,
            text="Wähle ein Profil wie „Gaming“, „Balanced“ oder „Silent“, das zu deinem Use-Case passt.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_P,
            wraplength=480,
        ).pack(anchor="w", pady=(4, 6))

        def _goto_profiles():
            self.tabs.set("⚡ PROFILES")
            from src.gui.notifications import show_toast
            show_toast(self, "Wechsle zum Profile-Tab – klicke ein Profil zum Anwenden.", "info")

        self._action_btn(inner2, "⚡  PROFILE TAB ÖFFNEN", _goto_profiles, side="right", accent=False)

        # Step 3 — Full optimise (optional)
        card3 = _Card(steps)
        card3.pack(fill="x", pady=4)
        inner3 = ctk.CTkFrame(card3, fg_color="transparent")
        inner3.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            inner3,
            text="🚀  Schritt 3 — Volle Optimierung (optional)",
            font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_H1,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner3,
            text="Führt alle Module nacheinander aus. Empfohlen nach Restore-Punkt und Profilwahl.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_P,
            wraplength=480,
        ).pack(anchor="w", pady=(4, 6))

        def _run_and_close():
            self._run_full_optimize()
            from src.gui.notifications import show_toast
            show_toast(self, "Starte vollständige Optimierung – bitte nicht abbrechen.", "warning")
            win.destroy()

        self._action_btn(inner3, "🚀  VOLLE OPTIMIERUNG", _run_and_close, side="right", accent=True)

        # Footer
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(
            footer,
            text="Hinweis: Alle Tweaks sind reversibel, solange ein Restore-Punkt existiert.",
            font=Theme.FONT_BODY_SM,
            text_color=Theme.TEXT_DIM,
        ).pack(anchor="w")
        ctk.CTkButton(
            footer,
            text="Schließen",
            width=90,
            height=32,
            fg_color=Theme.CARD_BG2,
            hover_color=Theme.CARD_BORDER2,
            text_color=Theme.TEXT_P,
            font=Theme.FONT_LABEL,
            corner_radius=Theme.RADIUS_SM,
            command=win.destroy,
        ).pack(side="right", pady=(8, 0))

    # =========================================================================
    # GAME DETECTOR CALLBACKS
    # =========================================================================

    def _on_game_detected(self, game_name: str, profile_key: str) -> None:
        logger.info("Game detected: %s → %s", game_name, profile_key)
        def _apply():
            from src.gui.notifications import show_toast
            show_toast(self, f"🎮 {game_name}  →  {profile_key.upper()}", "success")
            self.profile_applier.apply_profile(profile_key)
        self.after(0, _apply)

    def _on_game_closed(self, game_name: str) -> None:
        logger.info("Game closed: %s", game_name)

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def _on_close(self) -> None:
        logger.info("Shutdown initiated")
        self._monitor_active = False
        for svc in (self.game_detector, self.network_analyzer):
            try: svc.stop()
            except Exception: pass
        if self._overlay:
            try: self._overlay.close_overlay()
            except Exception: pass
        self.destroy()
