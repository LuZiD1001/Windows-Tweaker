"""Main entry point for LuzidSettings"""

import sys
import os
import ctypes
import logging
import subprocess

from src.gui.auth import AuthWindow
from src.gui.mainwindow_new import LuzidSettings
from src.utils import setup_logging


def check_admin() -> bool:
    """
    Check if application is running with administrator privileges.
    
    Returns:
        True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin():
    """Request administrator privileges and restart application"""
    try:
        # Re-run the script with admin privileges
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{os.path.abspath(__file__)}"',
            None,
            1
        )
        # Exit child process
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to request admin privileges: {e}")
        logger.warning("Continuing without admin - some features may be limited")


def main():
    """Start LuzidSettings application"""
    global logger
    logger = setup_logging(logging.INFO)
    
    logger.info("Starting LuzidSettings...")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Admin: {check_admin()}")
    
    # Optional: Request admin if not already admin
    # Uncomment the line below to enforce admin privileges
    # if not check_admin():
    #     logger.warning("Administrator privileges required. Requesting elevation...")
    #     request_admin()
    #     return  # Exit this instance, wait for elevated instance
    
    if check_admin():
        logger.info("Running with administrator privileges")
    else:
        logger.warning("Running without admin privileges - some features will be limited")
    
    try:
        # Start authentication window
        def launch_app():
            """Launch main application after successful authentication"""
            print("[LAUNCH] In launch_app callback...")
            logger.info("Authentication successful - Launching main application")
            try:
                print("[LAUNCH] Creating LuzidSettings instance...")
                app = LuzidSettings()
                print("[LAUNCH] Starting mainloop...")
                app.mainloop()
                print("[LAUNCH] Application closed")
                logger.info("Application closed")
            except Exception as e:
                print(f"[LAUNCH] Error in app: {type(e).__name__}: {e}")
                logger.error(f"App error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        logger.info("Initializing authentication window...")
        print("[LAUNCH] Creating AuthWindow...")
        auth = AuthWindow(on_success=launch_app)
        print("[LAUNCH] Starting auth mainloop...")
        auth.mainloop()
        print("[LAUNCH] Auth closed")
        
        
    except Exception as e:
        logger.error(f"Fatal error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Keep window open for debugging
        print("\n[ERROR] Press Enter to close...")
        try:
            input()
        except:
            pass


if __name__ == "__main__":
    main()
