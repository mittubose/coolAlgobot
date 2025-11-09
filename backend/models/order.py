"""
Order models and related data structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(Enum):
    """Order status enum."""
    PENDING = 'PENDING'           # Created, not yet submitted to broker
    SUBMITTED = 'SUBMITTED'       # Submitted to broker
    OPEN = 'OPEN'                 # Acknowledged by broker, waiting for fill
    FILLED = 'FILLED'             # Fully filled
    CANCELLED = 'CANCELLED'       # Cancelled by user or system
    REJECTED = 'REJECTED'         # Rejected by broker or pre-trade validation
    FAILED = 'FAILED'             # Failed to submit to broker


class OrderType(Enum):
    """Order type enum."""
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    SL = 'SL'          # Stop-loss limit
    SL_M = 'SL-M'      # Stop-loss market


class OrderSide(Enum):
    """Order side enum."""
    BUY = 'BUY'
    SELL = 'SELL'


class Product(Enum):
    """Product type enum."""
    MIS = 'MIS'  # Margin Intraday Square-off
    CNC = 'CNC'  # Cash and Carry (delivery)


class Validity(Enum):
    """Order validity enum."""
    DAY = 'DAY'  # Valid for the day
    IOC = 'IOC'  # Immediate or Cancel


@dataclass
class OrderRequest:
    """
    Request to place a new order.

    This is what strategies create when they want to place an order.
    """
    # Required fields
    symbol: str
    exchange: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    product: Product
    validity: Validity
    strategy_id: int

    # Optional fields (required for limit/SL orders)
    price: Optional[Decimal] = None
    trigger_price: Optional[Decimal] = None

    # Risk parameters (REQUIRED by risk management)
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate order request."""
        # Convert enums if strings provided
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.product, str):
            self.product = Product(self.product)
        if isinstance(self.validity, str):
            self.validity = Validity(self.validity)

        # Convert to Decimal if needed
        if self.price is not None and not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if self.trigger_price is not None and not isinstance(self.trigger_price, Decimal):
            self.trigger_price = Decimal(str(self.trigger_price))
        if self.stop_loss is not None and not isinstance(self.stop_loss, Decimal):
            self.stop_loss = Decimal(str(self.stop_loss))
        if self.take_profit is not None and not isinstance(self.take_profit, Decimal):
            self.take_profit = Decimal(str(self.take_profit))

        # Validation
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if self.order_type in [OrderType.LIMIT, OrderType.SL] and self.price is None:
            raise ValueError(f"{self.order_type.value} orders require price")

        if self.order_type in [OrderType.SL, OrderType.SL_M] and self.trigger_price is None:
            raise ValueError(f"{self.order_type.value} orders require trigger_price")

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage."""
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': float(self.price) if self.price else None,
            'trigger_price': float(self.trigger_price) if self.trigger_price else None,
            'product': self.product.value,
            'validity': self.validity.value,
            'strategy_id': self.strategy_id,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'metadata': self.metadata
        }


@dataclass
class Order:
    """
    Order model (from database).

    Represents an order at any stage of its lifecycle.
    """
    # Primary identifiers
    id: int
    broker_order_id: Optional[str]
    strategy_id: int

    # Order details
    symbol: str
    exchange: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[Decimal]
    trigger_price: Optional[Decimal]
    product: Product
    validity: Validity

    # Risk parameters
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    risk_amount: Optional[Decimal]
    risk_reward_ratio: Optional[Decimal]

    # Order state
    status: OrderStatus
    status_message: Optional[str] = None
    filled_quantity: int = 0
    average_price: Optional[Decimal] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Validation & Audit
    validation_result: Optional[Dict] = None
    validation_warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Convert string enums to enum types."""
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.product, str):
            self.product = Product(self.product)
        if isinstance(self.validity, str):
            self.validity = Validity(self.validity)
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)

    @property
    def is_active(self) -> bool:
        """Check if order is still active (not terminal)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.OPEN]

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == OrderSide.BUY

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == OrderSide.SELL

    @property
    def fill_percentage(self) -> float:
        """Get fill percentage (0-100)."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'broker_order_id': self.broker_order_id,
            'strategy_id': self.strategy_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': float(self.price) if self.price else None,
            'trigger_price': float(self.trigger_price) if self.trigger_price else None,
            'product': self.product.value,
            'validity': self.validity.value,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'risk_amount': float(self.risk_amount) if self.risk_amount else None,
            'risk_reward_ratio': float(self.risk_reward_ratio) if self.risk_reward_ratio else None,
            'status': self.status.value,
            'status_message': self.status_message,
            'filled_quantity': self.filled_quantity,
            'average_price': float(self.average_price) if self.average_price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'validation_result': self.validation_result,
            'validation_warnings': self.validation_warnings,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'is_active': self.is_active,
            'is_filled': self.is_filled,
            'fill_percentage': self.fill_percentage
        }


@dataclass
class OrderResult:
    """
    Result of order placement.

    Returned by OrderManager.place_order()
    """
    order_id: int
    broker_order_id: Optional[str]
    status: OrderStatus
    message: str

    # Validation details (if rejected)
    validation_result: Optional[Dict] = None

    @property
    def is_success(self) -> bool:
        """Check if order was successfully submitted."""
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.OPEN]

    @property
    def is_rejected(self) -> bool:
        """Check if order was rejected."""
        return self.status in [OrderStatus.REJECTED, OrderStatus.FAILED]

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'order_id': self.order_id,
            'broker_order_id': self.broker_order_id,
            'status': self.status.value,
            'message': self.message,
            'validation_result': self.validation_result,
            'is_success': self.is_success,
            'is_rejected': self.is_rejected
        }


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_risk_metrics(order: OrderRequest, entry_price: Decimal) -> Dict:
    """
    Calculate risk metrics for an order.

    Args:
        order: Order request
        entry_price: Estimated entry price

    Returns:
        Dict with risk_amount and risk_reward_ratio
    """
    risk_amount = None
    risk_reward_ratio = None

    if order.stop_loss:
        # Calculate risk amount
        risk_per_share = abs(entry_price - order.stop_loss)
        risk_amount = risk_per_share * order.quantity

        # Calculate risk-reward ratio
        if order.take_profit:
            reward_per_share = abs(order.take_profit - entry_price)
            if risk_per_share > 0:
                risk_reward_ratio = reward_per_share / risk_per_share

    return {
        'risk_amount': float(risk_amount) if risk_amount else None,
        'risk_reward_ratio': float(risk_reward_ratio) if risk_reward_ratio else None
    }


def order_from_db_row(row: Dict) -> Order:
    """
    Create Order object from database row.

    Args:
        row: Database row as dictionary

    Returns:
        Order object
    """
    return Order(
        id=row['id'],
        broker_order_id=row.get('broker_order_id'),
        strategy_id=row['strategy_id'],
        symbol=row['symbol'],
        exchange=row['exchange'],
        side=OrderSide(row['side']),
        quantity=row['quantity'],
        order_type=OrderType(row['order_type']),
        price=Decimal(str(row['price'])) if row.get('price') else None,
        trigger_price=Decimal(str(row['trigger_price'])) if row.get('trigger_price') else None,
        product=Product(row['product']),
        validity=Validity(row['validity']),
        stop_loss=Decimal(str(row['stop_loss'])) if row.get('stop_loss') else None,
        take_profit=Decimal(str(row['take_profit'])) if row.get('take_profit') else None,
        risk_amount=Decimal(str(row['risk_amount'])) if row.get('risk_amount') else None,
        risk_reward_ratio=Decimal(str(row['risk_reward_ratio'])) if row.get('risk_reward_ratio') else None,
        status=OrderStatus(row['status']),
        status_message=row.get('status_message'),
        filled_quantity=row.get('filled_quantity', 0),
        average_price=Decimal(str(row['average_price'])) if row.get('average_price') else None,
        created_at=row.get('created_at'),
        submitted_at=row.get('submitted_at'),
        updated_at=row.get('updated_at'),
        filled_at=row.get('filled_at'),
        cancelled_at=row.get('cancelled_at'),
        validation_result=row.get('validation_result'),
        validation_warnings=row.get('validation_warnings', []),
        error_message=row.get('error_message'),
        metadata=row.get('metadata', {})
    )
