import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULTS = {
    "app": {
        "name": "AI Assistant",
        "version": "0.1.0"
    },
    "logging": {
        "level": "INFO"
    },
    "server": {
        "host": "127.0.0.1",
        "port": 8000
    },
    "ENABLE_CONTINUOUS_LISTENING": False  # Default to False
}

class Config:
    def __init__(self, config_path="config.yaml"):
        """Load configuration from YAML file with defaults."""
        self.config = DEFAULTS.copy()
        try:
            with open(config_path, 'r') as file:
                user_config = yaml.safe_load(file)
                if user_config:
                    self.config.update(user_config)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def get(self, key, default=None):
        """Get configuration value by key."""
        return self.config.get(key, default)

config = Config()