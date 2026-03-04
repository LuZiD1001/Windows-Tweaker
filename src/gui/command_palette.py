"""Command palette for quick access to features"""

import customtkinter as ctk
from typing import Dict, Callable, List
from src.theme import Theme


class CommandPalette(ctk.CTkToplevel):
    """Quick command palette widget (like VS Code)"""
    
    def __init__(self, parent, commands: Dict[str, Callable]):
        """
        Initialize command palette.
        
        Args:
            parent: Parent window
            commands: Dict of command_name: callable
        """
        super().__init__(parent)
        self.title("Command Palette")
        self.geometry("600x400")
        self.configure(fg_color=Theme.BG_MAIN)
        
        self.commands = commands
        self.filtered_commands = list(commands.items())
        self.selected_index = 0
        
        # Search field
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search)
        
        search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text="Type command name...",
            font=Theme.FONT_BODY,
            fg_color=Theme.CARD_BG,
            border_width=1,
            border_color=Theme.ACCENT
        )
        search_entry.pack(fill="x", padx=15, pady=15)
        search_entry.focus()
        
        # Commands list
        self.listbox_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.CARD_BG,
            corner_radius=10
        )
        self.listbox_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Bind keys
        self.bind("<Up>", self._on_key_up)
        self.bind("<Down>", self._on_key_down)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self._refresh_commands()
    
    def _on_search(self, *args):
        """Filter commands on search"""
        query = self.search_var.get().lower()
        self.filtered_commands = [
            (name, cmd) for name, cmd in self.commands.items()
            if query in name.lower()
        ]
        self.selected_index = 0
        self._refresh_commands()
    
    def _refresh_commands(self):
        """Refresh command list display"""
        # Clear
        for widget in self.listbox_frame.winfo_children():
            widget.destroy()
        
        # Show filtered commands
        for idx, (name, _) in enumerate(self.filtered_commands):
            is_selected = (idx == self.selected_index)
            self._create_command_item(name, idx, is_selected)
    
    def _create_command_item(self, name: str, idx: int, selected: bool):
        """Create a command item"""
        btn = ctk.CTkButton(
            self.listbox_frame,
            text=name,
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT if selected else "transparent",
            text_color="#000" if selected else Theme.TEXT_H1,
            anchor="w",
            command=lambda: self._execute_command(idx)
        )
        btn.pack(fill="x", padx=10, pady=5)
    
    def _on_key_up(self, event):
        """Navigate up in list"""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._refresh_commands()
    
    def _on_key_down(self, event):
        """Navigate down in list"""
        if self.selected_index < len(self.filtered_commands) - 1:
            self.selected_index += 1
            self._refresh_commands()
    
    def _on_enter(self, event):
        """Execute selected command"""
        if self.filtered_commands:
            self._execute_command(self.selected_index)
    
    def _execute_command(self, idx: int):
        """Execute command at index"""
        if 0 <= idx < len(self.filtered_commands):
            _, cmd = self.filtered_commands[idx]
            self.destroy()
            cmd()


class QuickActionBar(ctk.CTkFrame):
    """Quick action bar with frequently used buttons"""
    
    def __init__(self, parent, commands: List[tuple], **kwargs):
        """
        Initialize quick action bar.
        
        Args:
            parent: Parent widget
            commands: List of (label, emoji, callback) tuples
        """
        super().__init__(parent, fg_color=Theme.CARD_BG, corner_radius=12, **kwargs)
        
        for label, emoji, callback in commands:
            btn = ctk.CTkButton(
                self,
                text=f"{emoji} {label}",
                font=Theme.FONT_LABEL,
                fg_color=Theme.ACCENT,
                text_color="#000",
                hover_color="#8A2BE2",
                height=36,
                command=callback
            )
            btn.pack(side="left", padx=8, pady=8)
