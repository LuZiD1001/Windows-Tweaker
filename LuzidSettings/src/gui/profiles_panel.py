"""Quick access profiles panel for one-click optimization"""

import customtkinter as ctk
from typing import Callable, Optional
import threading

from src.theme import Theme
from src.profiles import ProfileManager, ProfileApplier


class ProfileButton(ctk.CTkButton):
    """Custom profile button with enhanced styling"""
    
    def __init__(self, parent, profile, callback: Callable, **kwargs):
        self.profile_key = profile[0]
        self.profile = profile[1]
        
        super().__init__(
            parent,
            text=f"{self.profile.icon} {self.profile.name}\n{self.profile.description}",
            command=lambda: callback(self.profile_key),
            fg_color=Theme.CARD_BG,
            hover_color=Theme.ACCENT,
            text_color=Theme.TEXT_H1,
            font=Theme.FONT_MODULE,
            height=80,
            corner_radius=12,
            **kwargs
        )


class ProfilesPanel(ctk.CTkFrame):
    """Panel showing optimization profiles for quick access"""
    
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.engine = engine
        self.profile_applier = ProfileApplier(engine)
        self.applying = False
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚡ Quick Profiles",
            text_color=Theme.TEXT_H1,
            font=Theme.FONT_HEADING
        )
        title.pack(pady=(0, 15))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="One-click optimization profiles tailored for your needs",
            text_color=Theme.TEXT_P,
            font=Theme.FONT_BODY
        )
        subtitle.pack(pady=(0, 20))
        
        # Profiles grid
        self.profiles_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.profiles_frame.pack(fill="both", expand=True)
        
        # Configure grid for 2 columns
        self.profiles_frame.grid_columnconfigure(0, weight=1)
        self.profiles_frame.grid_columnconfigure(1, weight=1)
        
        # Create profile buttons
        profiles = ProfileManager.get_profile_list()
        for idx, profile in enumerate(profiles):
            btn = ProfileButton(
                self.profiles_frame,
                profile,
                self._on_profile_selected
            )
            row = idx // 2
            col = idx % 2
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        # Progress bar (hidden by default)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.progress_frame.pack(fill="x", padx=0, pady=(20, 0))
        self.progress_frame.pack_forget()
        
        progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Applying profile...",
            text_color=Theme.ACCENT,
            font=Theme.FONT_LABEL
        )
        progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=Theme.CARD_BORDER,
            progress_color=Theme.ACCENT
        )
        self.progress_bar.pack(fill="x", padx=0, pady=(0, 10))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            text_color=Theme.TEXT_P,
            font=Theme.FONT_BODY
        )
        self.progress_label.pack(pady=(0, 10))
        
        # Set progress callback
        self.profile_applier.set_progress_callback(self._on_progress)
    
    def _on_profile_selected(self, profile_key: str):
        """Handle profile button click"""
        if self.applying:
            return
        
        self.applying = True
        
        # Show progress
        self.progress_frame.pack(fill="x", padx=0, pady=(20, 0))
        
        # Apply in background thread
        thread = threading.Thread(
            target=self._apply_profile,
            args=(profile_key,),
            daemon=True
        )
        thread.start()
    
    def _apply_profile(self, profile_key: str):
        """Apply profile in background"""
        try:
            self.profile_applier.apply_profile(profile_key)
        except Exception as e:
            print(f"[ERROR] Profile application failed: {e}")
        finally:
            self.applying = False
    
    def _on_progress(self, message: str, progress: float):
        """Handle progress update"""
        try:
            self.progress_label.configure(text=message)
            self.progress_bar.set(progress)
            
            if progress >= 1.0:
                self.after(1000, lambda: self.progress_frame.pack_forget())
        except:
            pass
