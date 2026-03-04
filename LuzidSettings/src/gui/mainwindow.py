"""Main application window for LuzidSettings"""

import customtkinter as ctk
from datetime import datetime
import os
from typing import Optional
from PIL import Image, ImageEnhance
import sys

from src.theme import Theme
from src.engine import OptimizationEngine
from src.security import get_resource_path
from src.utils import format_timestamp

# Logging to file
LOG_FILE = "luzidmain.log"

def log(msg: str):
    """Log message to file and stdout"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(full_msg + "\n")
    except:
        pass


class LuzidSettings(ctk.CTk):
    """Main application window for LuzidSettings"""

    def __init__(self):
        """Initialize the main application window"""
        try:
            log("[APP] Initializing LuzidSettings...")
            super().__init__()
            
            # Suppress TK internal errors
            import warnings
            warnings.filterwarnings("ignore")
            
            log("[APP] Creating optimization engine...")
            self.engine = OptimizationEngine()
            log("[APP] Engine initialized")
            
            log("[APP] Configuring window...")
            self.title(f"LuzidSettings Tweak - Premium Optimization")
            self.geometry(f"{Theme.WINDOW_WIDTH}x{Theme.WINDOW_HEIGHT}")
            self.configure(fg_color=Theme.BG_MAIN)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)
            
            log("[APP] Setting up sidebar...")
            self.setup_sidebar()
            log("[APP] Sidebar setup complete")
            
            log("[APP] Setting up main content...")
            self.setup_main_content()
            log("[APP] Main content setup complete")
            
            log("[APP] LuzidSettings initialized successfully - showing window...")
        
        except Exception as e:
            log(f"[APP INIT ERROR] {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def setup_sidebar(self):
        """Create and configure left sidebar"""
        try:
            log("[APP] Creating sidebar frame...")
            self.sidebar = ctk.CTkFrame(
                self,
                width=Theme.SIDEBAR_WIDTH,
                fg_color=Theme.SIDEBAR,
                corner_radius=0
            )
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            log("[APP] Sidebar frame created")
            
            # Logo Section
            log("[APP] Creating logo section...")
            self.create_logo_section()
            log("[APP] Logo section created")
            
            # Vault Section
            log("[APP] Creating vault section...")
            self.create_vault_section()
            log("[APP] Vault section created")
        
        except Exception as e:
            log(f"[APP ERROR] Error in setup_sidebar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_logo_section(self):
        """Create logo and branding section"""
        try:
            log("[APP] Creating logo section...")
            # Try to load logo image
            logo_path = get_resource_path("logo.png")
            log(f"[APP] Looking for logo at: {logo_path}")
            
            if os.path.exists(logo_path):
                try:
                    log("[APP] Loading logo image...")
                    img = Image.open(logo_path)
                    img = ImageEnhance.Brightness(img).enhance(3.5)
                    img = ImageEnhance.Contrast(img).enhance(1.2)
                    self.logo_img = ctk.CTkImage(img, size=(240, 320))
                    ctk.CTkLabel(
                        self.sidebar,
                        image=self.logo_img,
                        text=""
                    ).pack(pady=(60, 15))
                    log("[APP] Logo loaded successfully")
                except Exception as e:
                    log(f"[APP] Error loading logo image: {e}")
                    self.create_text_logo()
            else:
                log(f"[APP] Logo not found at {logo_path}, using text logo")
                self.create_text_logo()
        
        except Exception as e:
            log(f"[APP] Error in create_logo_section: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.create_text_logo()
            except:
                pass
    
    def create_text_logo(self):
        """Create text-based logo"""
        ctk.CTkLabel(
            self.sidebar,
            text="ZENITH",
            font=Theme.FONT_TITLE,
            text_color=Theme.ACCENT
        ).pack(pady=70)
        
        ctk.CTkLabel(
            self.sidebar,
            text="LUZIDSETTINGS",
            font=Theme.FONT_HEADING,
            text_color="#FFF"
        ).pack()
        
        ctk.CTkLabel(
            self.sidebar,
            text="CERTIFIED CUSTOMER BUILD",
            font=Theme.FONT_LABEL,
            text_color=Theme.ACCENT
        ).pack(pady=(0, 40))
    
    def create_vault_section(self):
        """Create stealth vault controls"""
        vault_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=Theme.BG_MAIN,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.CARD_BORDER
        )
        vault_frame.pack(padx=25, pady=20, fill="x")
        
        # Title
        ctk.CTkLabel(
            vault_frame,
            text="STEALTH VAULT",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_P
        ).pack(pady=(15, 5))
        
        # Path input
        self.vault_path_entry = ctk.CTkEntry(
            vault_frame,
            placeholder_text="Folder Path...",
            height=42,
            fg_color="#0D0D10",
            border_color=Theme.CARD_BORDER
        )
        self.vault_path_entry.pack(fill="x", padx=15, pady=5)
        
        # Ghost button
        ctk.CTkButton(
            vault_frame,
            text="GHOST FOLDER",
            fg_color=Theme.ACCENT,
            text_color="#000",
            font=(Theme.font_display(), 11, "bold"),
            command=self.execute_vault_lock
        ).pack(fill="x", padx=15, pady=5)
        
        # Reveal button
        ctk.CTkButton(
            vault_frame,
            text="REVEAL FOLDER",
            fg_color="transparent",
            border_width=1,
            border_color=Theme.ACCENT,
            text_color=Theme.ACCENT,
            command=self.execute_vault_unlock
        ).pack(fill="x", padx=15, pady=(5, 15))
    
    def setup_main_content(self):
        """Create main content area"""
        try:
            log("[APP] Creating main content...")
            scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll_frame.grid(row=0, column=1, sticky="nsew", padx=60, pady=50)
            log("[APP] Scroll frame created")
            
            # Header
            log("[APP] Adding headers...")
            ctk.CTkLabel(
                scroll_frame,
                text="System Optimization",
                font=Theme.FONT_HEADING,
                text_color="#FFF"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                scroll_frame,
                text="Professional grade tweaks for maximum gaming performance.",
                font=Theme.FONT_SUBTEXT,
                text_color=Theme.TEXT_P
            ).pack(anchor="w", pady=(0, 60))
            log("[APP] Headers added")
            
            # Optimization modules
            log("[APP] Creating module cards...")
            for i, module in enumerate(self.engine.modules):
                log(f"[APP]   Creating module {i+1}/{len(self.engine.modules)}: {module['title']}")
                self.create_module_card(
                    scroll_frame,
                    module["title"],
                    module["description"],
                    module["action"]
                )
            log("[APP] Module cards created")
            
            # Terminal section
            log("[APP] Creating terminal...")
            ctk.CTkLabel(
                scroll_frame,
                text="ENGINE TERMINAL",
                font=Theme.FONT_LABEL,
                text_color=Theme.ACCENT
            ).pack(anchor="w", pady=(45, 5))
            
            self.terminal = ctk.CTkTextbox(
                scroll_frame,
                height=280,
                fg_color="#0B0B0E",
                border_color=Theme.CARD_BORDER,
                border_width=1,
                font=Theme.FONT_TERMINAL,
                text_color="#E0E0E0"
            )
            self.terminal.pack(fill="x", pady=(0, 30))
            log("[APP] Terminal created")
            
            # Clear terminal button
            ctk.CTkButton(
                scroll_frame,
                text="CLEAR TERMINAL",
                fg_color=Theme.CARD_BORDER,
                text_color=Theme.TEXT_P,
                font=(Theme.font_display(), 11, "bold"),
                command=self.clear_terminal
            ).pack(anchor="w", pady=(0, 20))
            
            log("[APP] Main content setup complete")
        
        except Exception as e:
            log(f"[APP ERROR] Error in setup_main_content: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_module_card(self, parent, title: str, description: str, action):
        """Create optimization module card"""
        try:
            card = ctk.CTkFrame(
                parent,
                fg_color=Theme.CARD_BG,
                corner_radius=20,
                border_width=1,
                border_color=Theme.CARD_BORDER
            )
            card.pack(fill="x", pady=12)
            
            # Content area
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", padx=35, pady=30)
            
            ctk.CTkLabel(
                content,
                text=title,
                font=Theme.FONT_MODULE,
                text_color=Theme.ACCENT
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                content,
                text=description,
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_P
            ).pack(anchor="w")
            
            # Action button
            ctk.CTkButton(
                card,
                text="OPTIMIZE",
                fg_color=Theme.ACCENT,
                text_color="#000",
                font=(Theme.font_display(), 12, "bold"),
                width=150,
                height=48,
                corner_radius=12,
                command=lambda: self.log_output(action())
            ).pack(side="right", padx=40)
        
        except Exception as e:
            log(f"[APP ERROR] Error creating module card '{title}': {e}")
            import traceback
            traceback.print_exc()
    
    def execute_vault_lock(self):
        """Lock (hide) selected folder"""
        path = self.vault_path_entry.get().strip()
        result = self.engine.vault_folder(path, lock=True)
        self.log_output(result)
    
    def execute_vault_unlock(self):
        """Unlock (reveal) selected folder"""
        path = self.vault_path_entry.get().strip()
        result = self.engine.vault_folder(path, lock=False)
        self.log_output(result)
    
    def log_output(self, message: str):
        """
        Log message to terminal.
        
        Args:
            message: Message to log
        """
        timestamp = format_timestamp()
        self.terminal.insert("end", f"{timestamp} >> {message}\n")
        self.terminal.see("end")
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal.delete("1.0", "end")
