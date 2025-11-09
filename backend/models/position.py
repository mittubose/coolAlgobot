"""
Position model and related data structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal


@dataclass
class Position:
    """
    Position model (from database).

    Represents an open or closed trading position.
    """
    # Primary identifiers
    id: int
    symbol: str
    exchange: str
    strategy_id: int

    # Position details
    quantity: int  # Positive = long, Negative = short
    average_price: Decimal
    product: str  # MIS or CNC

    # PnL tracking
    realized_pnl: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')

    # Risk management
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    time_based_sl_hours: Optional[int] = None

    # Statistics
    entry_order_ids: List[int] = field(default_factory=list)
    exit_order_ids: List[int] = field(default_factory=list)
    highest_price: Optional[Decimal] = None
    lowest_price: Optional[Decimal] = None

    # Timestamps
    opened_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.closed_at is None and self.quantity != 0

    @property
    def is_long(self) -> bool:
        """Check if this is a long position."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if this is a short position."""
        return self.quantity < 0

    @property
    def total_pnl(self) -> Decimal:
        """Get total PnL (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def abs_quantity(self) -> int:
        """Get absolute quantity (always positive)."""
        return abs(self.quantity)

    def calculate_unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """
        Calculate unrealized PnL at current price.

        Args:
            current_price: Current market price

        Returns:
            Unrealized PnL
        """
        if self.quantity == 0:
            return Decimal('0')

        if self.is_long:
            # Long position: profit when price goes up
            unrealized = self.quantity * (current_price - self.average_price)
        else:
            # Short position: profit when price goes down
            unrealized = abs(self.quantity) * (self.average_price - current_price)

        return unrealized

    def should_trigger_stop_loss(self, current_price: Decimal) -> bool:
        """
        Check if stop-loss should be triggered at current price.

        Args:
            current_price: Current market price

        Returns:
            True if stop-loss should trigger
        """
        if not self.stop_loss:
            return False

        if self.is_long:
            # Long position: stop-loss triggers when price drops below SL
            return current_price <= self.stop_loss
        else:
            # Short position: stop-loss triggers when price rises above SL
            return current_price >= self.stop_loss

    def should_trigger_take_profit(self, current_price: Decimal) -> bool:
        """
        Check if take-profit should be triggered at current price.

        Args:
            current_price: Current market price

        Returns:
            True if take-profit should trigger
        """
        if not self.take_profit:
            return False

        if self.is_long:
            # Long position: take-profit triggers when price rises above TP
            return current_price >= self.take_profit
        else:
            # Short position: take-profit triggers when price drops below TP
            return current_price <= self.take_profit

    def update_price_extremes(self, current_price: Decimal):
        """
        Update highest/lowest price seen.

        Args:
            current_price: Current market price
        """
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price

        if self.lowest_price is None or current_price < self.lowest_price:
            self.lowest_price = current_price

        # Update max drawdown
        if self.is_long and self.highest_price:
            # For long: drawdown when price drops from highest
            drawdown = self.highest_price - current_price
            if self.max_drawdown is None or drawdown > self.max_drawdown:
                self.max_drawdown = drawdown

        elif self.is_short and self.lowest_price:
            # For short: drawdown when price rises from lowest
            drawdown = current_price - self.lowest_price
            if self.max_drawdown is None or drawdown > self.max_drawdown:
                self.max_drawdown = drawdown

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'strategy_id': self.strategy_id,
            'quantity': self.quantity,
            'average_price': float(self.average_price),
            'product': self.product,
            'realized_pnl': float(self.realized_pnl),
            'unrealized_pnl': float(self.unrealized_pnl),
            'total_pnl': float(self.total_pnl),
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'max_drawdown': float(self.max_drawdown) if self.max_drawdown else None,
            'time_based_sl_hours': self.time_based_sl_hours,
            'entry_order_ids': self.entry_order_ids,
            'exit_order_ids': self.exit_order_ids,
            'highest_price': float(self.highest_price) if self.highest_price else None,
            'lowest_price': float(self.lowest_price) if self.lowest_price else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'is_open': self.is_open,
            'is_long': self.is_long,
            'is_short': self.is_short,
            'abs_quantity': self.abs_quantity,
            'metadata': self.metadata
        }


def position_from_db_row(row: Dict) -> Position:
    """
    Create Position object from database row.

    Args:
        row: Database row as dictionary

    Returns:
        Position object
    """
    return Position(
        id=row['id'],
        symbol=row['symbol'],
        exchange=row['exchange'],
        strategy_id=row['strategy_id'],
        quantity=row['quantity'],
        average_price=Decimal(str(row['average_price'])),
        product=row['product'],
        realized_pnl=Decimal(str(row.get('realized_pnl', 0))),
        unrealized_pnl=Decimal(str(row.get('unrealized_pnl', 0))),
        stop_loss=Decimal(str(row['stop_loss'])) if row.get('stop_loss') else None,
        take_profit=Decimal(str(row['take_profit'])) if row.get('take_profit') else None,
        max_drawdown=Decimal(str(row['max_drawdown'])) if row.get('max_drawdown') else None,
        time_based_sl_hours=row.get('time_based_sl_hours'),
        entry_order_ids=row.get('entry_order_ids', []),
        exit_order_ids=row.get('exit_order_ids', []),
        highest_price=Decimal(str(row['highest_price'])) if row.get('highest_price') else None,
        lowest_price=Decimal(str(row['lowest_price'])) if row.get('lowest_price') else None,
        opened_at=row.get('opened_at'),
        updated_at=row.get('updated_at'),
        closed_at=row.get('closed_at'),
        metadata=row.get('metadata', {})
    )
