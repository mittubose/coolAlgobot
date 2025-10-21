"""
Database Models
SQLAlchemy ORM models for trades, strategies, sessions, etc.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, ForeignKey, Enum, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class OrderSide(enum.Enum):
    """Order side enum"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(enum.Enum):
    """Order type enum"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class OrderStatus(enum.Enum):
    """Order status enum"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TradeStatus(enum.Enum):
    """Trade status enum"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


class SessionStatus(enum.Enum):
    """Trading session status"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


# ==================== Trade Model ====================

class Trade(Base):
    """Trade model - records individual trade executions"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Trade identification
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    trade_id = Column(String(100), unique=True, index=True)

    # Trade details
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)

    # Order details
    order_type = Column(Enum(OrderType), nullable=False)
    product = Column(String(20), default='MIS')  # MIS, CNC, NRML
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)

    # P&L and fees
    pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    trailing_stop_loss = Column(Float, nullable=True)

    # Strategy information
    strategy_name = Column(String(100), nullable=True, index=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=True)

    # Session information
    session_id = Column(Integer, ForeignKey('trading_sessions.id'), nullable=True)

    # Timestamps
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=True)
    hold_duration = Column(Integer, nullable=True)  # Duration in seconds

    # Additional metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    broker_response = Column(JSON, nullable=True)  # Raw broker response

    # Relationships
    strategy = relationship("Strategy", back_populates="trades")
    session = relationship("TradingSession", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side.value}, pnl={self.pnl})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side.value if self.side else None,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'status': self.status.value if self.status else None,
            'strategy_name': self.strategy_name,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
        }


# ==================== Trading Session Model ====================

class TradingSession(Base):
    """Trading session - groups trades by session"""
    __tablename__ = 'trading_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Session details
    session_name = Column(String(200), nullable=True)
    mode = Column(String(20), default='paper')  # paper, live
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)

    # Timestamps
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds

    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    # P&L metrics
    total_pnl = Column(Float, default=0.0)
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)

    # Capital metrics
    starting_capital = Column(Float, nullable=True)
    ending_capital = Column(Float, nullable=True)
    peak_capital = Column(Float, nullable=True)

    # Additional metadata
    broker_name = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    config_snapshot = Column(JSON, nullable=True)  # Config at session start

    # Relationships
    trades = relationship("Trade", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TradingSession(id={self.id}, mode={self.mode}, trades={self.total_trades}, pnl={self.total_pnl})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_name': self.session_name,
            'mode': self.mode,
            'status': self.status.value if self.status else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'total_pnl': self.total_pnl,
        }


# ==================== Strategy Model ====================

class Strategy(Base):
    """Strategy configuration and performance"""
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Strategy identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # Strategy configuration
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=False)  # Strategy parameters
    timeframe = Column(String(20), nullable=True)  # 1m, 5m, 15m, 1h, etc.

    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)

    # Risk metrics
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_traded_at = Column(DateTime, nullable=True)

    # Metadata
    version = Column(String(20), default='1.0.0')
    tags = Column(JSON, nullable=True)  # List of tags
    is_template = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey('strategies.id'), nullable=True)  # If cloned from template

    # Relationships
    trades = relationship("Trade", back_populates="strategy")

    def __repr__(self):
        return f"<Strategy(id={self.id}, name={self.name}, enabled={self.enabled})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'enabled': self.enabled,
            'config': self.config,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'total_pnl': self.total_pnl,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ==================== Position Model ====================

class Position(Base):
    """Current open positions"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Position identification
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    product = Column(String(20), default='MIS')

    # Position details
    quantity = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    last_price = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)

    # Entry details
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    strategy_name = Column(String(100), nullable=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)

    # Status
    is_open = Column(Boolean, default=True, index=True)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Position(symbol={self.symbol}, quantity={self.quantity}, pnl={self.pnl})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'last_price': self.last_price,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'strategy_name': self.strategy_name,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
        }


# ==================== Alert Model ====================

class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # trade, error, risk, system
    severity = Column(String(20), default='info')  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Related entities
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=True)

    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_sent = Column(Boolean, default=False)  # Sent via Telegram/Email

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Metadata
    alert_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Alert(type={self.alert_type}, severity={self.severity}, title={self.title})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ==================== Audit Log Model ====================

class AuditLog(Base):
    """SEBI compliance audit trail (5-year retention)"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # order, config_change, login, etc.
    event_category = Column(String(50), nullable=False)  # trading, system, config
    description = Column(Text, nullable=False)

    # User/System information
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    broker_name = Column(String(50), nullable=True)

    # Related entities
    order_id = Column(String(100), nullable=True, index=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Data snapshot
    before_data = Column(JSON, nullable=True)  # State before change
    after_data = Column(JSON, nullable=True)   # State after change
    audit_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AuditLog(type={self.event_type}, timestamp={self.timestamp})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
        }
