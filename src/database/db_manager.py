"""
Database Manager
Handles SQLite database connection and schema initialization
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent / 'data'
DB_PATH = DB_DIR / 'scalping_bot.db'


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database

    Returns:
        sqlite3.Connection: Database connection
    """
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn


def init_database() -> None:
    """
    Initialize the database with required tables
    Creates watchlist and daily_picks tables if they don't exist
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create daily_picks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                pattern_name VARCHAR(50),
                confidence INTEGER,
                entry_price DECIMAL(10,2),
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE NOT NULL
            )
        ''')

        # Create index on date for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_picks_date
            ON daily_picks(date)
        ''')

        conn.commit()
        logger.info("Database initialized successfully")

    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def clear_old_picks(days_to_keep: int = 7) -> None:
    """
    Clear daily picks older than specified days

    Args:
        days_to_keep: Number of days to keep (default: 7)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM daily_picks
            WHERE date < DATE('now', ? || ' days')
        ''', (f'-{days_to_keep}',))

        deleted_count = cursor.rowcount
        conn.commit()

        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} old daily picks")

    except sqlite3.Error as e:
        logger.error(f"Error clearing old picks: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_db_stats() -> dict:
    """
    Get database statistics

    Returns:
        dict: Database statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get watchlist count
        cursor.execute('SELECT COUNT(*) as count FROM watchlist')
        watchlist_count = cursor.fetchone()['count']

        # Get today's picks count
        cursor.execute('''
            SELECT COUNT(*) as count FROM daily_picks
            WHERE date = DATE('now')
        ''')
        today_picks_count = cursor.fetchone()['count']

        # Get database size
        db_size = os.path.getsize(DB_PATH) if DB_PATH.exists() else 0
        db_size_mb = db_size / (1024 * 1024)

        return {
            'watchlist_count': watchlist_count,
            'today_picks_count': today_picks_count,
            'db_size_mb': round(db_size_mb, 2),
            'db_path': str(DB_PATH)
        }

    except sqlite3.Error as e:
        logger.error(f"Error getting database stats: {e}")
        return {}
    finally:
        conn.close()


if __name__ == '__main__':
    # Initialize database when run directly
    logging.basicConfig(level=logging.INFO)
    init_database()
    print("Database initialized successfully!")
    print(f"Database location: {DB_PATH}")
    print(f"Database stats: {get_db_stats()}")
