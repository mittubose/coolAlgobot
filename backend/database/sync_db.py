"""
Synchronous Database Wrapper for Portfolio & Strategy APIs

Simple psycopg2-based database wrapper that doesn't use async.
Used by Flask routes that need synchronous database access.
"""

import os
import psycopg2
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Synchronous database connection wrapper using psycopg2

    This is separate from the async Database class used by the OMS system.
    """

    def __init__(self, connection_string: str = None):
        """
        Initialize database connection pool

        Args:
            connection_string: PostgreSQL connection string (optional, uses DATABASE_URL env var if not provided)
        """
        # Get connection string from env if not provided
        if not connection_string:
            connection_string = os.getenv('DATABASE_URL', 'postgresql://mittuharibose@localhost:5432/scalping_bot')

        self.connection_string = connection_string
        self.pool = None

        logger.info(f"Database initialized with connection string")

    def connect(self):
        """
        Create connection pool
        """
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.connection_string
            )

            # Test connection
            conn = self.pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            self.pool.putconn(conn)

            logger.info(f"Connected to PostgreSQL: {version[:50]}...")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_connection(self):
        """
        Get a connection from the pool

        Returns:
            psycopg2 connection object
        """
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")

        return self.pool.getconn()

    def put_connection(self, conn):
        """
        Return a connection to the pool

        Args:
            conn: Connection to return
        """
        if self.pool:
            self.pool.putconn(conn)

    def close(self):
        """
        Close all connections in the pool
        """
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Global database instance
_db_instance = None


def get_database() -> Database:
    """
    Get global database instance (singleton pattern)

    Returns:
        Database instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = Database()
        _db_instance.connect()

    return _db_instance
