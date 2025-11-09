"""
Watchlist Manager
Handles CRUD operations for the watchlist
"""

import sqlite3
from typing import List, Dict, Optional
import logging
from datetime import datetime

from .db_manager import get_db_connection

logger = logging.getLogger(__name__)


class WatchlistManager:
    """Manage watchlist operations"""

    @staticmethod
    def add_stock(symbol: str) -> bool:
        """
        Add a stock to the watchlist

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')

        Returns:
            bool: True if added successfully, False otherwise
        """
        symbol = symbol.upper().strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO watchlist (symbol)
                VALUES (?)
            ''', (symbol,))

            conn.commit()
            logger.info(f"Added {symbol} to watchlist")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Stock {symbol} already in watchlist")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding stock to watchlist: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def remove_stock(symbol: str) -> bool:
        """
        Remove a stock from the watchlist

        Args:
            symbol: Stock symbol to remove

        Returns:
            bool: True if removed successfully, False otherwise
        """
        symbol = symbol.upper().strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                DELETE FROM watchlist
                WHERE symbol = ?
            ''', (symbol,))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Removed {symbol} from watchlist")
                return True
            else:
                logger.warning(f"Stock {symbol} not found in watchlist")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error removing stock from watchlist: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_all() -> List[Dict]:
        """
        Get all stocks in the watchlist

        Returns:
            List[Dict]: List of watchlist entries
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, symbol, added_at
                FROM watchlist
                ORDER BY added_at DESC
            ''')

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting watchlist: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_symbols() -> List[str]:
        """
        Get list of symbols in watchlist

        Returns:
            List[str]: List of stock symbols
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT symbol FROM watchlist ORDER BY added_at DESC')
            rows = cursor.fetchall()
            return [row['symbol'] for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting watchlist symbols: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def is_in_watchlist(symbol: str) -> bool:
        """
        Check if a stock is in the watchlist

        Args:
            symbol: Stock symbol to check

        Returns:
            bool: True if in watchlist, False otherwise
        """
        symbol = symbol.upper().strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM watchlist
                WHERE symbol = ?
            ''', (symbol,))

            result = cursor.fetchone()
            return result['count'] > 0

        except sqlite3.Error as e:
            logger.error(f"Error checking watchlist: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def clear_all() -> int:
        """
        Clear all stocks from the watchlist

        Returns:
            int: Number of stocks removed
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM watchlist')
            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"Cleared {deleted_count} stocks from watchlist")
            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Error clearing watchlist: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    @staticmethod
    def get_count() -> int:
        """
        Get number of stocks in watchlist

        Returns:
            int: Count of watchlist stocks
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COUNT(*) as count FROM watchlist')
            result = cursor.fetchone()
            return result['count']

        except sqlite3.Error as e:
            logger.error(f"Error getting watchlist count: {e}")
            return 0
        finally:
            conn.close()


if __name__ == '__main__':
    # Test watchlist operations
    logging.basicConfig(level=logging.INFO)

    # Initialize database first
    from .db_manager import init_database
    init_database()

    # Test operations
    wm = WatchlistManager()

    print("\n=== Testing Watchlist Manager ===")

    # Add stocks
    print("\nAdding stocks...")
    wm.add_stock('RELIANCE')
    wm.add_stock('TCS')
    wm.add_stock('INFY')

    # Get all
    print(f"\nWatchlist: {wm.get_all()}")
    print(f"Symbols: {wm.get_symbols()}")
    print(f"Count: {wm.get_count()}")

    # Check if in watchlist
    print(f"\nIs RELIANCE in watchlist? {wm.is_in_watchlist('RELIANCE')}")
    print(f"Is HDFC in watchlist? {wm.is_in_watchlist('HDFC')}")

    # Remove stock
    print("\nRemoving TCS...")
    wm.remove_stock('TCS')
    print(f"Symbols after removal: {wm.get_symbols()}")

    # Clear all
    print("\nClearing watchlist...")
    cleared = wm.clear_all()
    print(f"Cleared {cleared} stocks")
    print(f"Final count: {wm.get_count()}")
