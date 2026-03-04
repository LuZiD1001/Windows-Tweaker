"""Configuration management including Supabase credentials"""

import os
from typing import Optional

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv is not installed, skip loading .env
    pass


class Config:
    """Application configuration"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL",
        "https://hwrypfhfbafuajziital.supabase.co"
    )
    SUPABASE_KEY: str = os.getenv(
        "SUPABASE_KEY",
        "DEIN_SUPABASE_ANON_KEY"
    )
    
    # Application Settings
    APP_VERSION = "3.0.0"
    APP_NAME = "LuzidSettings"
    APP_SUBTITLE = "CERTIFIED CUSTOMER BUILD"
    
    # Window Settings
    WINDOW_WIDTH = 1480
    WINDOW_HEIGHT = 1000
    WINDOW_RESIZABLE = False
    
    # Security
    REQUIRE_ADMIN = True
    REQUIRE_LICENSE = True
    
    # Licensing Table
    LICENSE_TABLE = "licenses"
    LICENSE_COLUMNS = ["key", "hwid", "created_at", "valid_until"]
    
    @classmethod
    def is_valid(cls) -> bool:
        """Validate configuration is complete"""
        return (
            cls.SUPABASE_URL != "" and
            cls.SUPABASE_KEY != "DEIN_SUPABASE_ANON_KEY"
        )
