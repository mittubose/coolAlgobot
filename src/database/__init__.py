"""
Database Module
Handles all database operations, models, and persistence
"""

from .db import Database, get_session, init_database, get_database
from .models import (
    Base,
    Trade,
    TradingSession,
    Strategy,
    Position,
    Alert,
    AuditLog
)

# Watchlist and recommendations (SQLite-based)
from .db_manager import get_db_connection, init_database as init_watchlist_db
from .watchlist_manager import WatchlistManager

__all__ = [
    'Database',
    'get_session',
    'init_database',
    'get_database',
    'Base',
    'Trade',
    'TradingSession',
    'Strategy',
    'Position',
    'Alert',
    'AuditLog',
    'get_db_connection',
    'init_watchlist_db',
    'WatchlistManager'
]
