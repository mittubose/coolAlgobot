"""
Configuration management for XCoin Scalping Bot.

Loads configuration from environment variables and config files.
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Application configuration."""

    # ========================================================================
    # DATABASE
    # ========================================================================

    # PostgreSQL connection string
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/xcoin_dev'
    )

    # Connection pool settings
    DB_MIN_CONNECTIONS = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
    DB_MAX_CONNECTIONS = int(os.getenv('DB_MAX_CONNECTIONS', '20'))

    # ========================================================================
    # ZERODHA API
    # ========================================================================

    ZERODHA_API_KEY = os.getenv('ZERODHA_API_KEY', '')
    ZERODHA_API_SECRET = os.getenv('ZERODHA_API_SECRET', '')
    ZERODHA_ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN', '')

    # ========================================================================
    # RISK MANAGEMENT
    # ========================================================================

    # Maximum risk per trade (2% of account)
    MAX_RISK_PER_TRADE = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))

    # Maximum daily loss (6% of account)
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '0.06'))

    # Maximum drawdown (15% from peak)
    MAX_DRAWDOWN = float(os.getenv('MAX_DRAWDOWN', '0.15'))

    # Maximum open positions
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))

    # Minimum risk-reward ratio
    MIN_RISK_REWARD = float(os.getenv('MIN_RISK_REWARD', '2.0'))
    MIN_RISK_REWARD_RATIO = MIN_RISK_REWARD  # Alias for validator

    # Maximum position size (shares)
    MAX_POSITION_SIZE = int(os.getenv('MAX_POSITION_SIZE', '1000'))

    # Maximum quantity per order
    MAX_QUANTITY_PER_ORDER = int(os.getenv('MAX_QUANTITY_PER_ORDER', '10000'))

    # Price sanity check (±10% of LTP)
    PRICE_SANITY_PCT = float(os.getenv('PRICE_SANITY_PCT', '0.10'))
    MAX_PRICE_DEVIATION_PCT = PRICE_SANITY_PCT  # Alias for validator

    # Maximum position loss (5% of account)
    MAX_POSITION_LOSS_PCT = float(os.getenv('MAX_POSITION_LOSS_PCT', '0.05'))

    # Order-to-position ratio (max pending orders per position)
    MAX_ORDER_TO_POSITION_RATIO = int(os.getenv('MAX_ORDER_TO_POSITION_RATIO', '3'))

    # ========================================================================
    # APPLICATION
    # ========================================================================

    # Application mode (development, production)
    APP_MODE = os.getenv('APP_MODE', 'development')

    # Debug mode
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

    # Log level
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Dashboard host/port
    DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '8050'))

    # ========================================================================
    # ALERTS
    # ========================================================================

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Email (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', '')

    # ========================================================================
    # PATHS
    # ========================================================================

    BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BASE_DIR / 'logs'
    DATA_DIR = BASE_DIR / 'data'

    @classmethod
    def get_risk_config(cls) -> Dict[str, Any]:
        """
        Get risk management configuration.

        Returns:
            Dict with all risk parameters
        """
        return {
            'max_risk_per_trade': cls.MAX_RISK_PER_TRADE,
            'max_daily_loss': cls.MAX_DAILY_LOSS,
            'max_drawdown': cls.MAX_DRAWDOWN,
            'max_positions': cls.MAX_POSITIONS,
            'min_risk_reward': cls.MIN_RISK_REWARD,
            'max_position_size': cls.MAX_POSITION_SIZE,
            'price_sanity_pct': cls.PRICE_SANITY_PCT,
            'max_position_loss_pct': cls.MAX_POSITION_LOSS_PCT
        }

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration.

        Returns:
            True if valid, raises ValueError otherwise
        """
        errors = []

        # Check database URL
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL not set")

        # Check Zerodha credentials (only if needed)
        # if not cls.ZERODHA_API_KEY:
        #     errors.append("ZERODHA_API_KEY not set")

        # Check risk parameters are sensible
        if cls.MAX_RISK_PER_TRADE <= 0 or cls.MAX_RISK_PER_TRADE > 0.10:
            errors.append("MAX_RISK_PER_TRADE must be between 0 and 0.10 (10%)")

        if cls.MAX_DAILY_LOSS <= 0 or cls.MAX_DAILY_LOSS > 0.20:
            errors.append("MAX_DAILY_LOSS must be between 0 and 0.20 (20%)")

        if cls.MAX_POSITIONS <= 0 or cls.MAX_POSITIONS > 10:
            errors.append("MAX_POSITIONS must be between 1 and 10")

        if cls.MIN_RISK_REWARD < 1.0:
            errors.append("MIN_RISK_REWARD must be at least 1.0")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (safe values only)."""
        print("\n" + "="*60)
        print("XCoin Scalping Bot - Configuration")
        print("="*60)
        print(f"App Mode: {cls.APP_MODE}")
        print(f"Debug: {cls.DEBUG}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"\nDatabase:")
        print(f"  URL: {cls.DATABASE_URL.split('@')[1] if '@' in cls.DATABASE_URL else cls.DATABASE_URL}")
        print(f"  Connections: {cls.DB_MIN_CONNECTIONS}-{cls.DB_MAX_CONNECTIONS}")
        print(f"\nRisk Management:")
        print(f"  Max Risk Per Trade: {cls.MAX_RISK_PER_TRADE:.1%}")
        print(f"  Max Daily Loss: {cls.MAX_DAILY_LOSS:.1%}")
        print(f"  Max Drawdown: {cls.MAX_DRAWDOWN:.1%}")
        print(f"  Max Positions: {cls.MAX_POSITIONS}")
        print(f"  Min Risk-Reward: {cls.MIN_RISK_REWARD}:1")
        print(f"  Max Position Size: {cls.MAX_POSITION_SIZE} shares")
        print(f"\nDashboard:")
        print(f"  Host: {cls.DASHBOARD_HOST}")
        print(f"  Port: {cls.DASHBOARD_PORT}")
        print(f"\nZerodha API:")
        print(f"  API Key: {'*' * 10 if cls.ZERODHA_API_KEY else 'NOT SET'}")
        print(f"  Access Token: {'*' * 10 if cls.ZERODHA_ACCESS_TOKEN else 'NOT SET'}")
        print(f"\nAlerts:")
        print(f"  Telegram: {'Configured' if cls.TELEGRAM_BOT_TOKEN else 'NOT SET'}")
        print(f"  Email: {'Configured' if cls.SMTP_USER else 'NOT SET'}")
        print("="*60 + "\n")


# Create directories if they don't exist
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
