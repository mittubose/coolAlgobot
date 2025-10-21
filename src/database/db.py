"""
Database Connection Manager
Handles database initialization, sessions, and connection pooling
"""

import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class Database:
    """Database connection manager"""

    def __init__(self, database_url: str = None, echo: bool = False):
        """
        Initialize database connection

        Args:
            database_url: Database connection URL (default: SQLite)
            echo: Enable SQL query logging
        """
        self.logger = logging.getLogger('database')

        # Default to SQLite if no URL provided
        if not database_url:
            db_path = Path("data/trading.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        self.database_url = database_url
        self.echo = echo

        # Create engine
        if database_url.startswith('sqlite'):
            # SQLite-specific settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )

            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        else:
            # PostgreSQL/MySQL settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True  # Test connections before use
            )

        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        self.logger.info(f"Database initialized: {database_url}")

    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(self.engine)
            self.logger.warning("All database tables dropped")
        except Exception as e:
            self.logger.error(f"Failed to drop tables: {e}")
            raise

    def reset_database(self):
        """Reset database (drop and recreate all tables)"""
        self.drop_tables()
        self.create_tables()
        self.logger.info("Database reset complete")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session (context manager)

        Usage:
            with db.get_session() as session:
                # Use session here
                pass
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        self.Session.remove()
        self.engine.dispose()
        self.logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global database instance
_db_instance: Optional[Database] = None


def init_database(database_url: str = None, echo: bool = False) -> Database:
    """
    Initialize global database instance

    Args:
        database_url: Database connection URL
        echo: Enable SQL query logging

    Returns:
        Database instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = Database(database_url, echo)
        _db_instance.create_tables()

    return _db_instance


def get_database() -> Database:
    """
    Get global database instance

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    global _db_instance

    if _db_instance is None:
        # Auto-initialize with defaults
        return init_database()

    return _db_instance


@contextmanager
def get_session() -> Session:
    """
    Get a database session (convenience function)

    Usage:
        from src.database import get_session

        with get_session() as session:
            trades = session.query(Trade).all()
    """
    db = get_database()
    with db.get_session() as session:
        yield session


# ==================== Helper Functions ====================

def execute_query(query_func, *args, **kwargs):
    """
    Execute a database query with automatic session management

    Args:
        query_func: Function that takes a session as first argument
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments

    Returns:
        Query result
    """
    with get_session() as session:
        return query_func(session, *args, **kwargs)


def safe_add(obj):
    """
    Safely add object to database

    Args:
        obj: SQLAlchemy model instance
    """
    with get_session() as session:
        session.add(obj)


def safe_delete(obj):
    """
    Safely delete object from database

    Args:
        obj: SQLAlchemy model instance
    """
    with get_session() as session:
        session.delete(obj)


def safe_update(model, filter_by: dict, update_data: dict):
    """
    Safely update database records

    Args:
        model: SQLAlchemy model class
        filter_by: Filter criteria (dict)
        update_data: Data to update (dict)

    Returns:
        Number of rows updated
    """
    with get_session() as session:
        count = session.query(model).filter_by(**filter_by).update(update_data)
        return count
