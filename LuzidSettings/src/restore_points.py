"""
LuzidSettings - System Restore Point Manager
Creates and lists Windows System Restore Points via WMI/PowerShell.
Used as a safety net BEFORE applying any tweaks.
"""

import subprocess
import threading
import json
import os
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RestorePoint:
    sequence_number: int
    description: str
    creation_time: str
    restore_type: str


class RestorePointManager:
    """
    Create and list Windows System Restore Points.
    Requires admin rights and System Protection enabled on C:.
    """
    
    LUZID_MARKER = "LuzidSettings"
    
    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._last_created: Optional[str] = None
    
    def on(self, event: str, cb: Callable):
        self._callbacks[event] = cb
    
    def _emit(self, event: str, *args):
        if event in self._callbacks:
            self._callbacks[event](*args)
    
    def create_async(self, description: str = None, progress_cb: Optional[Callable] = None):
        """Create restore point asynchronously"""
        label = description or f"{self.LUZID_MARKER} — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        threading.Thread(
            target=self._create_restore_point,
            args=(label, progress_cb),
            daemon=True
        ).start()
    
    def _create_restore_point(self, description: str, progress_cb: Optional[Callable]):
        try:
            if progress_cb:
                progress_cb("Creating System Restore Point…", 0.3)
            
            # PowerShell command to create restore point
            ps_cmd = (
                f'Checkpoint-Computer -Description "{description}" '
                f'-RestorePointType MODIFY_SETTINGS'
            )
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self._last_created = description
                if progress_cb:
                    progress_cb(f"✓ Restore point created: {description}", 1.0)
                self._emit("on_created", True, description)
                logger.info(f"Restore point created: {description}")
            else:
                err = result.stderr.strip()[:100]
                if progress_cb:
                    progress_cb(f"⚠ Could not create restore point: {err}", 1.0)
                self._emit("on_created", False, err)
                logger.warning(f"Restore point failed: {err}")
        
        except subprocess.TimeoutExpired:
            msg = "Restore point timed out (System Protection may be off)"
            if progress_cb:
                progress_cb(f"⚠ {msg}", 1.0)
            self._emit("on_created", False, msg)
        except Exception as e:
            msg = str(e)[:80]
            if progress_cb:
                progress_cb(f"⚠ Error: {msg}", 1.0)
            self._emit("on_created", False, msg)
    
    def list_restore_points(self) -> List[RestorePoint]:
        """Get list of existing restore points"""
        try:
            ps_cmd = (
                "Get-ComputerRestorePoint | "
                "Select-Object SequenceNumber, Description, CreationTime, RestorePointType | "
                "ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                return []
            
            raw = json.loads(result.stdout)
            if isinstance(raw, dict):
                raw = [raw]
            
            points = []
            for item in raw:
                points.append(RestorePoint(
                    sequence_number=item.get("SequenceNumber", 0),
                    description=item.get("Description", "Unknown"),
                    creation_time=str(item.get("CreationTime", "")),
                    restore_type=str(item.get("RestorePointType", ""))
                ))
            return sorted(points, key=lambda p: p.sequence_number, reverse=True)
        
        except Exception as e:
            logger.debug(f"List restore points: {e}")
            return []
    
    def list_luzid_points(self) -> List[RestorePoint]:
        """Return only restore points created by LuzidSettings"""
        return [p for p in self.list_restore_points()
                if self.LUZID_MARKER in p.description]
    
    @staticmethod
    def is_protection_enabled() -> bool:
        """Check if System Protection is enabled for C:"""
        try:
            ps_cmd = (
                "Get-WmiObject -Class SystemRestore -Namespace root/default | "
                "Where-Object {$_.Drive -eq 'C:\\\\'} | "
                "Select-Object -ExpandProperty RPSessionInterval"
            )
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and result.stdout.strip() != "0"
        except Exception:
            return False
    
    def get_last_created(self) -> Optional[str]:
        return self._last_created
