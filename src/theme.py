"""
Theme and styling configuration for LuzidSettings — REDESIGN v4.0
Aesthetic: Tactical-dark cyber with neon-teal accent. Sharp and focused.
"""

import sys
import tkinter.font as tkfont


def _resolve_font(preferred: str, fallbacks: list) -> str:
    try:
        available = set(tkfont.families())
        for name in [preferred] + fallbacks:
            if name in available:
                return name
    except Exception:
        pass
    return "Segoe UI" if sys.platform == "win32" else "TkDefaultFont"


_DISPLAY = _resolve_font("Rajdhani", ["Orbitron", "Segoe UI Semibold", "Ubuntu Condensed", "Segoe UI"])
_MONO    = _resolve_font("Cascadia Code", ["Consolas", "JetBrains Mono", "Fira Mono", "DejaVu Sans Mono", "Courier New"])
_BODY    = _resolve_font("Segoe UI", ["SF Pro Text", "Ubuntu", "Helvetica Neue", "Arial"])


class Theme:
    """Central design token store — LuzidSettings REDESIGN v4.0"""

    # ── Palette ───────────────────────────────────────────────────────────────
    ACCENT       = "#00F5C4"   # Neon teal — primary interactive
    ACCENT_DIM   = "#00BFA5"   # Dimmed for hover/pressed
    ACCENT_GLOW  = "#00F5C420" # Transparent glow fills

    BG_MAIN      = "#07080B"   # Near-void background
    BG_DEEP      = "#0A0C10"
    SIDEBAR      = "#0D0F14"
    CARD_BG      = "#111318"
    CARD_BG2     = "#161A22"
    CARD_BORDER  = "#1E2430"
    CARD_BORDER2 = "#2A3444"

    SUCCESS      = "#00E676"
    ERROR        = "#FF3D5A"
    WARNING      = "#FFB300"
    INFO         = "#40C4FF"

    TEXT_H1      = "#E8EAF0"
    TEXT_H2      = "#B0B8C8"
    TEXT_P       = "#6A7890"
    TEXT_DIM     = "#3A4455"

    # ── Typography ────────────────────────────────────────────────────────────
    FONT_HERO       = (_DISPLAY, 44, "bold")
    FONT_HEADING    = (_DISPLAY, 22, "bold")
    FONT_SUBHEADING = (_DISPLAY, 16, "bold")
    FONT_MODULE     = (_DISPLAY, 14, "bold")
    FONT_LABEL      = (_DISPLAY, 11)
    FONT_LABEL_BOLD = (_DISPLAY, 11, "bold")
    FONT_BODY       = (_BODY,    13)
    FONT_BODY_SM    = (_BODY,    11)
    FONT_TERMINAL   = (_MONO,    12)
    FONT_MONO_LG    = (_MONO,    20, "bold")
    FONT_MONO_MD    = (_MONO,    14)

    # ── Legacy aliases (compatibility) ────────────────────────────────────────
    FONT_TITLE      = FONT_HERO
    FONT_SUBTEXT    = FONT_BODY
    FONT_MONO       = FONT_MONO_MD

    # ── Layout ────────────────────────────────────────────────────────────────
    SIDEBAR_WIDTH = 200
    WINDOW_WIDTH  = 1540
    WINDOW_HEIGHT = 960
    CORNER_RADIUS = 10
    RADIUS        = 10
    RADIUS_LG     = 14
    RADIUS_SM     = 6

    @classmethod
    def font_display(cls) -> str:
        return _DISPLAY

    @classmethod
    def font_mono(cls) -> str:
        return _MONO

    @classmethod
    def font_body(cls) -> str:
        return _BODY
