"""Settings and configuration management"""

import json
from pathlib import Path


class ConfigManager:
    """Manage application settings"""

    DEFAULT_CONFIG = {
        "theme": "dark",
        "window_width": 800,
        "window_height": 600,
    }

    def __init__(self, config_path: str = "config.json"):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file or use defaults.
        Falls back to defaults if file is missing or corrupt.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    loaded = json.load(f)
                    # Merge with defaults so new keys are always present
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    return merged
            except (json.JSONDecodeError, OSError):
                pass  # Fall through to defaults
        return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str, default=None):
        """Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value, auto_save: bool = True) -> None:
        """Set configuration value and optionally auto-save.
        
        Args:
            key: Configuration key
            value: Value to set
            auto_save: Whether to immediately persist the change (default: True)
        """
        self.config[key] = value
        if auto_save:
            self.save_config()
