#!/usr/bin/env python3
"""
Database Initialization Script
Creates database tables and sets up initial data
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import init_database, get_session
from src.database.models import Strategy, TradingSession
from src.utils.config_loader import ConfigLoader
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('init_db')


def create_default_strategies():
    """Create default strategy templates from config"""
    try:
        # Load config
        config = ConfigLoader()
        config.load()

        strategies_config = config.get('strategies', [])

        with get_session() as session:
            for strategy_config in strategies_config:
                strategy_name = strategy_config.get('name')

                # Check if strategy already exists
                existing = session.query(Strategy).filter_by(name=strategy_name).first()

                if not existing:
                    strategy = Strategy(
                        name=strategy_name,
                        display_name=strategy_config.get('description', strategy_name),
                        description=strategy_config.get('description', ''),
                        enabled=strategy_config.get('enabled', True),
                        config=strategy_config.get('params', {}),
                        is_template=True,
                        version='1.0.0'
                    )

                    session.add(strategy)
                    logger.info(f"Created strategy: {strategy_name}")
                else:
                    logger.info(f"Strategy already exists: {strategy_name}")

        logger.info("Default strategies created successfully")

    except Exception as e:
        logger.error(f"Failed to create default strategies: {e}")
        raise


def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION")
    print("="*60 + "\n")

    try:
        # Initialize database
        print("1. Initializing database...")
        db = init_database(echo=False)
        print("   ✅ Database initialized")

        # Create tables
        print("\n2. Creating tables...")
        db.create_tables()
        print("   ✅ Tables created")

        # Create default strategies
        print("\n3. Creating default strategies...")
        create_default_strategies()
        print("   ✅ Default strategies created")

        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print("\nDatabase location: data/trading.db")
        print("\nTables created:")
        print("  - trades")
        print("  - trading_sessions")
        print("  - strategies")
        print("  - positions")
        print("  - alerts")
        print("  - audit_logs")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
