"""Toast notifications and UI feedback system — REDESIGN v4.0"""

import customtkinter as ctk
from src.theme import Theme
from typing import Literal
import threading


class Toast(ctk.CTkToplevel):
    """Sleek corner toast notification."""

    _COLORS = {
        "info":    Theme.INFO,
        "success": Theme.SUCCESS,
        "warning": Theme.WARNING,
        "error":   Theme.ERROR,
    }
    _ICONS = {
        "info": "◆", "success": "✓", "warning": "!", "error": "✕",
    }

    def __init__(self, parent, message: str,
                 toast_type: Literal["info", "success", "warning", "error"] = "info",
                 duration: int = 3000):
        super().__init__(parent)
        color = self._COLORS.get(toast_type, Theme.ACCENT)
        icon  = self._ICONS.get(toast_type, "◆")

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(fg_color=Theme.CARD_BG2)

        # Left-accent bar + content
        outer = ctk.CTkFrame(self, fg_color=Theme.CARD_BG2, corner_radius=Theme.RADIUS,
                             border_width=1, border_color=Theme.CARD_BORDER2)
        outer.pack(padx=0, pady=0)

        bar = ctk.CTkFrame(outer, width=4, fg_color=color, corner_radius=0)
        bar.pack(side="left", fill="y")

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(side="left", padx=14, pady=12)

        ctk.CTkLabel(inner, text=f"{icon}  {message}",
                     font=Theme.FONT_BODY, text_color=Theme.TEXT_H1,
                     wraplength=300).pack(anchor="w")

        # Position bottom-right
        self.update_idletasks()
        try:
            px = parent.winfo_x() + parent.winfo_width()  - self.winfo_reqwidth() - 20
            py = parent.winfo_y() + parent.winfo_height() - self.winfo_reqheight() - 20
            self.geometry(f"+{px}+{py}")
        except Exception:
            self.geometry("+50+50")

        # Fade in
        self._fade_in()
        self.after(duration, self._fade_out)

    def _fade_in(self, alpha: float = 0.0):
        alpha = min(alpha + 0.1, 0.95)
        self.attributes("-alpha", alpha)
        if alpha < 0.95:
            self.after(20, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha: float = 0.95):
        alpha = max(alpha - 0.1, 0.0)
        self.attributes("-alpha", alpha)
        if alpha > 0:
            self.after(25, lambda: self._fade_out(alpha))
        else:
            try:
                self.destroy()
            except Exception:
                pass


class LoadingSpinner(ctk.CTkFrame):
    """Braille-dot spinning animation."""

    _FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._active = False
        self._idx = 0
        self._lbl = ctk.CTkLabel(self, text=self._FRAMES[0],
                                  text_color=Theme.ACCENT,
                                  font=(Theme.font_display(), 22))
        self._lbl.pack()

    def start(self):
        self._active = True
        self._tick()

    def stop(self):
        self._active = False

    def _tick(self):
        if not self._active:
            return
        self._lbl.configure(text=self._FRAMES[self._idx % len(self._FRAMES)])
        self._idx += 1
        self.after(90, self._tick)


class ProgressOverlay(ctk.CTkToplevel):
    """Modal progress overlay — minimal and crisp."""

    def __init__(self, parent, title: str = "Processing…"):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.97)
        self.configure(fg_color=Theme.BG_MAIN)
        self.geometry("640x260")
        self.overrideredirect(True)

        wrap = ctk.CTkFrame(self, fg_color=Theme.CARD_BG2,
                            corner_radius=Theme.RADIUS_LG,
                            border_width=1, border_color=Theme.CARD_BORDER2)
        wrap.pack(expand=True, fill="both", padx=2, pady=2)

        ctk.CTkLabel(wrap, text=title,
                     font=Theme.FONT_HEADING, text_color=Theme.ACCENT).pack(pady=(24, 8))

        self.spinner = LoadingSpinner(wrap)
        self.spinner.pack(pady=8)
        self.spinner.start()

        self.status_label = ctk.CTkLabel(wrap, text="Please wait…",
                                          font=Theme.FONT_BODY, text_color=Theme.TEXT_P)
        self.status_label.pack(pady=(8, 0))

        self.progress_bar = ctk.CTkProgressBar(wrap,
                                                fg_color=Theme.CARD_BORDER,
                                                progress_color=Theme.ACCENT,
                                                height=3)
        self.progress_bar.pack(fill="x", padx=28, pady=(20, 24))
        self.progress_bar.set(0)

    def update_status(self, message: str):
        self.status_label.configure(text=message)

    def update_progress(self, value: float):
        self.progress_bar.set(max(0.0, min(1.0, value)))

    def close_overlay(self):
        self.spinner.stop()
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(parent_window, message: str,
               toast_type: Literal["info", "success", "warning", "error"] = "info",
               duration: int = 3000):
    """Show a toast notification from any thread."""
    try:
        parent_window.after(0, lambda: Toast(parent_window, message, toast_type, duration))
    except Exception:
        pass


def confirm_dialog(parent_window, title: str, message: str) -> bool:
    """Blocking confirmation dialog. Returns True if user confirmed."""
    dialog = ctk.CTkToplevel(parent_window)
    dialog.title(title)
    dialog.geometry("420x200")
    dialog.attributes("-topmost", True)
    dialog.configure(fg_color=Theme.BG_MAIN)

    result = {"ok": False}

    ctk.CTkLabel(dialog, text=message,
                 font=Theme.FONT_BODY, text_color=Theme.TEXT_H1,
                 wraplength=380).pack(pady=32, padx=24)

    btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_row.pack(pady=8)

    def _yes():
        result["ok"] = True
        dialog.destroy()

    ctk.CTkButton(btn_row, text="CONFIRM",
                  fg_color=Theme.ACCENT, text_color="#000000",
                  font=Theme.FONT_LABEL_BOLD, width=120, height=38,
                  corner_radius=Theme.RADIUS, command=_yes).pack(side="left", padx=8)

    ctk.CTkButton(btn_row, text="CANCEL",
                  fg_color=Theme.CARD_BG2, text_color=Theme.TEXT_P,
                  border_width=1, border_color=Theme.CARD_BORDER2,
                  font=Theme.FONT_LABEL_BOLD, width=120, height=38,
                  corner_radius=Theme.RADIUS, command=dialog.destroy).pack(side="left", padx=8)

    dialog.wait_window()
    return result["ok"]
