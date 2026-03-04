"""Authentication window — license key verification against Supabase"""

import logging
import threading
from typing import Callable, Optional

import customtkinter as ctk

from src.theme import Theme
from src.security import get_hwid
from src.config.config import Config

logger = logging.getLogger("LuzidSettings.auth")

try:
    from supabase import create_client, Client as SupabaseClient
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False


class AuthWindow(ctk.CTk):
    """
    License-key verification screen shown before the main window.

    On success the *on_success* callback is invoked from the Tkinter
    main thread, then this window destroys itself.  In demo mode (no
    Supabase credentials) any non-empty key is accepted after a short
    artificial delay so the UI flow can still be tested end-to-end.
    """

    def __init__(self, on_success: Callable[[], None]) -> None:
        super().__init__()
        self._on_success = on_success
        self._supabase: Optional[SupabaseClient] = None
        self._demo_mode: bool = not (_SUPABASE_AVAILABLE and Config.is_valid())

        self._build_window()
        self._connect_supabase()
        self._build_ui()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        self.title("LuzidSettings — License Verification")
        self.geometry("480x660")
        self.configure(fg_color=Theme.BG_MAIN)
        self.resizable(False, False)
        self.attributes("-topmost", True)

    def _connect_supabase(self) -> None:
        if _SUPABASE_AVAILABLE and Config.is_valid():
            try:
                self._supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                logger.info("Supabase client initialised")
            except Exception as exc:
                logger.warning("Supabase init failed: %s", exc)
                self._supabase = None
                self._demo_mode = True

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Hero label ──
        ctk.CTkLabel(
            self,
            text="ZENITH",
            font=Theme.FONT_TITLE,
            text_color=Theme.ACCENT,
        ).pack(pady=(80, 6))

        ctk.CTkLabel(
            self,
            text="LICENSE VERIFICATION",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_P,
        ).pack()

        # ── Key input ──
        self._key_entry = ctk.CTkEntry(
            self,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            width=360,
            height=52,
            fg_color=Theme.SIDEBAR,
            border_color=Theme.ACCENT,
            justify="center",
            font=Theme.FONT_MONO,
        )
        self._key_entry.pack(pady=50)
        self._key_entry.bind("<Return>", lambda _e: self._begin_auth())

        # ── Activate button ──
        self._btn = ctk.CTkButton(
            self,
            text="ACTIVATE SYSTEM",
            fg_color=Theme.ACCENT,
            text_color="#000000",
            font=(*Theme.FONT_LABEL[:1], 14, "bold"),
            width=260,
            height=52,
            corner_radius=10,
            command=self._begin_auth,
        )
        self._btn.pack()

        # ── Status line ──
        self._status = ctk.CTkLabel(
            self,
            text="Ready for activation…",
            text_color=Theme.TEXT_P,
            font=Theme.FONT_BODY,
        )
        self._status.pack(pady=36)

        # ── Demo-mode notice ──
        if self._demo_mode:
            ctk.CTkLabel(
                self,
                text="⚠  DEMO MODE  —  Supabase not configured",
                text_color=Theme.WARNING,
                font=(*Theme.FONT_BODY[:1], 10),
            ).pack()

    # ── Auth flow ─────────────────────────────────────────────────────────────

    def _begin_auth(self) -> None:
        """Kick off authentication on a daemon thread."""
        self._btn.configure(state="disabled")
        threading.Thread(target=self._run_auth, daemon=True).start()

    def _run_auth(self) -> None:
        """Blocking auth logic — must never touch widgets directly."""
        key = self._key_entry.get().strip()

        if not key:
            self._ui(lambda: (
                self._status.configure(text="⚠  Please enter your license key",
                                       text_color=Theme.WARNING),
                self._btn.configure(state="normal"),
            ))
            return

        self._ui(lambda: self._status.configure(
            text="CONNECTING TO VERIFICATION SERVER…",
            text_color=Theme.ACCENT,
        ))

        # ── Demo / offline path ──────────────────────────────────────────────
        if self._demo_mode or self._supabase is None:
            logger.info("Demo mode — granting access without server check")
            self._ui(lambda: self._status.configure(
                text="⚠  DEMO MODE — Access granted",
                text_color=Theme.WARNING,
            ))
            self.after(1200, self._launch)
            return

        # ── Live Supabase check ──────────────────────────────────────────────
        try:
            hwid = get_hwid()
            logger.debug("Querying license table for key %s…", key[:4])
            res = (
                self._supabase
                .table(Config.LICENSE_TABLE)
                .select("*")
                .eq("key", key)
                .execute()
            )

            if not res.data:
                self._ui(lambda: (
                    self._status.configure(text="✗  Invalid license key",
                                           text_color=Theme.ERROR),
                    self._btn.configure(state="normal"),
                ))
                return

            record = res.data[0]
            stored_hwid = record.get("hwid")

            if not stored_hwid:
                # First activation on this machine — bind the key
                logger.info("First activation — registering HWID")
                self._supabase.table(Config.LICENSE_TABLE).update(
                    {"hwid": hwid}
                ).eq("key", key).execute()
                self.after(0, self._launch)

            elif stored_hwid == hwid:
                logger.info("HWID verified — granting access")
                self.after(0, self._launch)

            else:
                logger.warning("HWID mismatch for key %s", key[:4])
                self._ui(lambda: (
                    self._status.configure(
                        text="✗  Key already bound to another machine",
                        text_color=Theme.ERROR,
                    ),
                    self._btn.configure(state="normal"),
                ))

        except Exception as exc:
            msg = str(exc)[:60]
            logger.error("Auth error: %s", exc)
            self._ui(lambda: (
                self._status.configure(text=f"✗  {msg}", text_color=Theme.ERROR),
                self._btn.configure(state="normal"),
            ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ui(self, fn: Callable) -> None:
        """Schedule a callable on the Tkinter main thread (thread-safe)."""
        self.after(0, fn)

    def _launch(self) -> None:
        """Show success message, then hand off to the main app."""
        self._status.configure(text="✓  ACCESS GRANTED — INITIALISING…",
                               text_color=Theme.SUCCESS)
        logger.info("Authentication successful")
        self.after(500, self._handoff)

    def _handoff(self) -> None:
        """Call on_success and destroy this window."""
        try:
            self._on_success()
        except Exception as exc:
            logger.error("on_success raised: %s", exc)
        finally:
            self.after(400, self.destroy)
