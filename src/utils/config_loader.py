"""
Configuration Loader
Loads and validates configuration from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Handles loading and validation of configuration"""

    def __init__(self, config_path: str = None, secrets_path: str = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config.yaml file
            secrets_path: Path to secrets.env file
        """
        # Set default paths
        base_dir = Path(__file__).parent.parent.parent
        self.config_path = config_path or base_dir / "config" / "config.yaml"
        self.secrets_path = secrets_path or base_dir / "config" / "secrets.env"

        self.config = {}
        self.secrets = {}

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from files

        Returns:
            Combined configuration dictionary
        """
        # Load secrets from environment file
        if os.path.exists(self.secrets_path):
            load_dotenv(self.secrets_path)
            self.secrets = {
                'KITE_API_KEY': os.getenv('KITE_API_KEY', ''),
                'KITE_API_SECRET': os.getenv('KITE_API_SECRET', ''),
                'KITE_ACCESS_TOKEN': os.getenv('KITE_ACCESS_TOKEN', ''),
                'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
                'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
                'DB_PASSWORD': os.getenv('DB_PASSWORD', ''),
                'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY', ''),
            }
        else:
            print(f"⚠️  Warning: Secrets file not found at {self.secrets_path}")
            print("   Please copy config/secrets.env.example to config/secrets.env")

        # Load main configuration
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Validate configuration
        self._validate_config()

        # Merge secrets into config
        self._merge_secrets()

        return self.config

    def _validate_config(self):
        """Validate required configuration fields"""
        required_sections = ['broker', 'trading', 'instruments', 'strategies', 'risk']

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate trading mode
        if self.config['trading']['mode'] not in ['paper', 'live']:
            raise ValueError("Trading mode must be 'paper' or 'live'")

        # Warn if attempting to use live mode
        if self.config['trading']['mode'] == 'live':
            print("⚠️  WARNING: Live trading mode enabled!")
            print("   Make sure you have thoroughly tested in paper mode first.")
            response = input("   Type 'YES' to continue with live trading: ")
            if response != 'YES':
                raise ValueError("Live trading mode not confirmed. Exiting for safety.")

        # Validate at least one instrument is enabled
        enabled_instruments = [i for i in self.config['instruments'] if i.get('enabled', True)]
        if not enabled_instruments:
            raise ValueError("No instruments enabled for trading")

        # Validate at least one strategy is enabled
        enabled_strategies = [s for s in self.config['strategies'] if s.get('enabled', True)]
        if not enabled_strategies:
            raise ValueError("No strategies enabled for trading")

    def _merge_secrets(self):
        """Merge secrets into configuration"""
        # Merge API credentials
        if 'KITE_API_KEY' in self.secrets:
            self.config['broker']['api_key'] = self.secrets['KITE_API_KEY']
        if 'KITE_API_SECRET' in self.secrets:
            self.config['broker']['api_secret'] = self.secrets['KITE_API_SECRET']
        if 'KITE_ACCESS_TOKEN' in self.secrets:
            self.config['broker']['access_token'] = self.secrets['KITE_ACCESS_TOKEN']

        # Merge Telegram credentials
        if 'TELEGRAM_BOT_TOKEN' in self.secrets:
            self.config['alerts']['telegram']['bot_token'] = self.secrets['TELEGRAM_BOT_TOKEN']
        if 'TELEGRAM_CHAT_ID' in self.secrets:
            self.config['alerts']['telegram']['chat_id'] = self.secrets['TELEGRAM_CHAT_ID']

        # Merge email password
        if 'EMAIL_PASSWORD' in self.secrets:
            self.config['alerts']['email']['password'] = self.secrets['EMAIL_PASSWORD']

    def get(self, key_path: str, default=None):
        """
        Get configuration value by dot-separated path

        Args:
            key_path: Dot-separated path (e.g., 'trading.capital')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def update(self, key_path: str, value: Any):
        """
        Update configuration value

        Args:
            key_path: Dot-separated path
            value: New value
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)


# Global configuration instance
_config_instance = None


def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
        _config_instance.load()
    return _config_instance


def reload_config():
    """Reload configuration from files"""
    global _config_instance
    _config_instance = ConfigLoader()
    _config_instance.load()
    return _config_instance
