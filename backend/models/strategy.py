"""
Strategy model and related data structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum


class StrategyStatus(Enum):
    """Strategy status enum."""
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    PAUSED = 'PAUSED'
    ERROR = 'ERROR'


class StrategyMode(Enum):
    """Strategy mode enum."""
    PAPER = 'PAPER'  # Paper trading (simulated)
    LIVE = 'LIVE'    # Live trading (real money)


@dataclass
class Strategy:
    """
    Strategy model (from database).

    Represents a trading strategy configuration.
    """
    # Primary identifiers
    id: int
    name: str
    type: str  # e.g., 'hammer_rsi', 'double_bottom', 'manual'
    description: Optional[str] = None

    # Configuration
    config: Dict = field(default_factory=dict)

    # State
    status: StrategyStatus = StrategyStatus.INACTIVE
    mode: StrategyMode = StrategyMode.PAPER

    # Performance
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: Decimal = Decimal('0')

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None

    def __post_init__(self):
        """Convert string enums to enum types."""
        if isinstance(self.status, str):
            self.status = StrategyStatus(self.status)
        if isinstance(self.mode, str):
            self.mode = StrategyMode(self.mode)

    @property
    def is_active(self) -> bool:
        """Check if strategy is active."""
        return self.status == StrategyStatus.ACTIVE

    @property
    def is_live(self) -> bool:
        """Check if strategy is in live trading mode."""
        return self.mode == StrategyMode.LIVE

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def avg_win(self) -> Optional[Decimal]:
        """Calculate average winning trade (would need trade data)."""
        # This would need to query trades table
        # Placeholder for now
        return None

    @property
    def avg_loss(self) -> Optional[Decimal]:
        """Calculate average losing trade (would need trade data)."""
        # This would need to query trades table
        # Placeholder for now
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'config': self.config,
            'status': self.status.value,
            'mode': self.mode.value,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': float(self.total_pnl),
            'win_rate': self.win_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'is_active': self.is_active,
            'is_live': self.is_live
        }


def strategy_from_db_row(row: Dict) -> Strategy:
    """
    Create Strategy object from database row.

    Args:
        row: Database row as dictionary

    Returns:
        Strategy object
    """
    return Strategy(
        id=row['id'],
        name=row['name'],
        type=row['type'],
        description=row.get('description'),
        config=row.get('config', {}),
        status=StrategyStatus(row.get('status', 'INACTIVE')),
        mode=StrategyMode(row.get('mode', 'PAPER')),
        total_trades=row.get('total_trades', 0),
        winning_trades=row.get('winning_trades', 0),
        losing_trades=row.get('losing_trades', 0),
        total_pnl=Decimal(str(row.get('total_pnl', 0))),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
        deployed_at=row.get('deployed_at')
    )
