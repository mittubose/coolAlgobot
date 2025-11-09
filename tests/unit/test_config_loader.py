"""
Unit Tests for Configuration Loader
Tests environment variable substitution and validation
"""

import pytest
import os
import yaml
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class"""

    @pytest.fixture
    def test_config_file(self, tmp_path):
        """Create a temporary config file"""
        config_data = {
            'broker': {
                'name': 'zerodha',
                'api_key': '${TEST_API_KEY}',
                'api_secret': '${TEST_API_SECRET}',
                'redirect_url': '${REDIRECT_URL:http://localhost:8080/callback}'
            },
            'trading': {
                'mode': 'paper',
                'capital': 100000
            },
            'instruments': [{'symbol': 'RELIANCE', 'enabled': True}],
            'strategies': [{'name': 'test_strategy', 'enabled': True}],
            'risk': {'max_daily_loss_percent': 2.0},
            'alerts': {
                'telegram': {'bot_token': '', 'chat_id': ''},
                'email': {'password': ''}
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return config_file

    @pytest.fixture
    def test_secrets_file(self, tmp_path):
        """Create a temporary secrets file"""
        secrets_file = tmp_path / "secrets.env"
        with open(secrets_file, 'w') as f:
            f.write("TEST_API_KEY=test_key_123\n")
            f.write("TEST_API_SECRET=test_secret_456\n")

        return secrets_file

    @pytest.fixture
    def config_loader(self, test_config_file, test_secrets_file):
        """Create ConfigLoader instance with test files"""
        return ConfigLoader(
            config_path=str(test_config_file),
            secrets_path=str(test_secrets_file)
        )

    def test_load_config_success(self, config_loader):
        """Test successful configuration loading"""
        config = config_loader.load()

        assert config is not None
        assert 'broker' in config
        assert 'trading' in config

    def test_env_var_substitution(self, config_loader):
        """Test environment variable substitution"""
        config = config_loader.load()

        # Should substitute from secrets.env
        assert config['broker']['api_key'] == 'test_key_123'
        assert config['broker']['api_secret'] == 'test_secret_456'

    def test_env_var_with_default_value(self, config_loader):
        """Test environment variable with default value"""
        config = config_loader.load()

        # REDIRECT_URL not set, should use default
        assert config['broker']['redirect_url'] == 'http://localhost:8080/callback'

    def test_missing_config_file_raises_error(self, tmp_path):
        """Test that missing config file raises error"""
        loader = ConfigLoader(
            config_path=str(tmp_path / "nonexistent.yaml"),
            secrets_path=str(tmp_path / "secrets.env")
        )

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_get_value_by_path(self, config_loader):
        """Test getting config value by dot-separated path"""
        config_loader.load()

        api_key = config_loader.get('broker.api_key')
        mode = config_loader.get('trading.mode')

        assert api_key == 'test_key_123'
        assert mode == 'paper'

    def test_get_nonexistent_value_returns_default(self, config_loader):
        """Test getting non-existent value returns default"""
        config_loader.load()

        value = config_loader.get('nonexistent.path', 'default_value')

        assert value == 'default_value'

    def test_update_config_value(self, config_loader):
        """Test updating configuration value"""
        config_loader.load()

        config_loader.update('trading.mode', 'live')
        updated_mode = config_loader.get('trading.mode')

        assert updated_mode == 'live'

    def test_validation_catches_missing_sections(self, tmp_path):
        """Test that validation catches missing required sections"""
        # Create config with missing section
        incomplete_config = {
            'broker': {'name': 'zerodha'},
            # Missing: trading, instruments, strategies, risk
        }

        config_file = tmp_path / "incomplete.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(incomplete_config, f)

        loader = ConfigLoader(
            config_path=str(config_file),
            secrets_path=str(tmp_path / "secrets.env")
        )

        with pytest.raises(ValueError, match="Missing required configuration section"):
            loader.load()

    def test_validation_requires_at_least_one_instrument(self, tmp_path):
        """Test that validation requires at least one enabled instrument"""
        config_data = {
            'broker': {'name': 'zerodha'},
            'trading': {'mode': 'paper'},
            'instruments': [{'symbol': 'RELIANCE', 'enabled': False}],  # All disabled
            'strategies': [{'name': 'test', 'enabled': True}],
            'risk': {}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(config_path=str(config_file), secrets_path=str(tmp_path / "secrets.env"))

        with pytest.raises(ValueError, match="No instruments enabled"):
            loader.load()

    def test_validation_requires_at_least_one_strategy(self, tmp_path):
        """Test that validation requires at least one enabled strategy"""
        config_data = {
            'broker': {'name': 'zerodha'},
            'trading': {'mode': 'paper'},
            'instruments': [{'symbol': 'RELIANCE', 'enabled': True}],
            'strategies': [{'name': 'test', 'enabled': False}],  # All disabled
            'risk': {}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(config_path=str(config_file), secrets_path=str(tmp_path / "secrets.env"))

        with pytest.raises(ValueError, match="No strategies enabled"):
            loader.load()

    def test_env_var_not_set_shows_warning(self, config_loader, caplog):
        """Test that unset environment variable logs warning"""
        import logging
        caplog.set_level(logging.WARNING)

        config = config_loader.load()

        # Check that warning was logged for unset variable
        # (depends on config having ${UNSET_VAR})

    def test_nested_env_vars(self, tmp_path):
        """Test deeply nested environment variable substitution"""
        config_data = {
            'broker': {
                'settings': {
                    'nested': {
                        'value': '${NESTED_VAR:default_nested}'
                    }
                }
            },
            'trading': {'mode': 'paper'},
            'instruments': [{'symbol': 'TEST', 'enabled': True}],
            'strategies': [{'name': 'test', 'enabled': True}],
            'risk': {}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(config_path=str(config_file), secrets_path=str(tmp_path / "secrets.env"))
        config = loader.load()

        assert config['broker']['settings']['nested']['value'] == 'default_nested'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
