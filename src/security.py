"""Security and hardware-identification utilities for LuzidSettings"""

import hashlib
import os
import subprocess
import sys
import uuid


def get_hwid() -> str:
    """
    Generate a stable hardware fingerprint for this machine.

    Combines three sources of machine-specific data that are individually
    spoofable but collectively very stable:

    * MAC address via ``uuid.getnode()``
    * Current OS username
    * Windows System UUID from WMI (falls back to ``"unknown"`` gracefully
      on non-Windows or if WMI is unavailable)

    The three components are joined, UTF-8 encoded and run through SHA-256
    so the raw values are never stored anywhere.

    Returns:
        64-character lowercase hex digest.

    Raises:
        RuntimeError: If even the fallback components cannot be read.
    """
    try:
        mac  = str(uuid.getnode())
        user = _current_username()
        uuid_str = _wmi_system_uuid()
        raw = f"{mac}:{user}:{uuid_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception as exc:
        raise RuntimeError(f"Failed to generate HWID: {exc}") from exc


# ── Internal helpers ──────────────────────────────────────────────────────────

def _current_username() -> str:
    """Return the current OS username, trying multiple fallbacks."""
    for fn in (os.getlogin, lambda: os.environ.get("USERNAME", ""),
               lambda: os.environ.get("USER", "unknown")):
        try:
            name = fn()
            if name:
                return name
        except Exception:
            continue
    return "unknown"


def _wmi_system_uuid() -> str:
    """
    Query the Windows System UUID via WMIC.

    Returns the UUID string on success, or ``"unknown"`` on any failure
    (non-Windows, permission denied, WMI not available, etc.).
    """
    if sys.platform != "win32":
        return "unknown"
    try:
        raw = subprocess.check_output(
            ["wmic", "csproduct", "get", "uuid"],
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
        lines = [l.strip() for l in raw.decode("utf-8", errors="ignore").splitlines()
                 if l.strip() and l.strip().lower() != "uuid"]
        return lines[0] if lines else "unknown"
    except Exception:
        return "unknown"


def get_resource_path(relative_path: str) -> str:
    """
    Resolve a bundled-resource path.

    Delegates to :func:`src.utils.get_resource_path` so there is a
    single authoritative implementation.  Kept here for backwards
    compatibility with callers that imported it from this module.
    """
    from src.utils import get_resource_path as _resolve
    return _resolve(relative_path)
