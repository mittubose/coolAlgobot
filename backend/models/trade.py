"""
Trade model and related data structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal


@dataclass
class Trade:
    """
    Trade model (from database).

    Represents an individual trade fill from an order execution.
    """
    # Primary identifiers
    id: int
    order_id: int
    position_id: Optional[int]
    broker_trade_id: Optional[str]

    # Trade details
    symbol: str
    exchange: str
    side: str  # BUY or SELL
    quantity: int
    price: Decimal

    # Transaction costs
    brokerage: Decimal = Decimal('0')
    stt: Decimal = Decimal('0')  # Securities Transaction Tax
    exchange_txn_charge: Decimal = Decimal('0')
    gst: Decimal = Decimal('0')
    stamp_duty: Decimal = Decimal('0')
    sebi_charges: Decimal = Decimal('0')
    total_charges: Decimal = Decimal('0')

    # Net calculation
    gross_value: Decimal = Decimal('0')
    net_value: Decimal = Decimal('0')

    # Timestamp
    executed_at: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Calculate gross_value, total_charges, and net_value if not set."""
        # Calculate gross value
        if self.gross_value == Decimal('0'):
            self.gross_value = self.quantity * self.price

        # Calculate total charges
        if self.total_charges == Decimal('0'):
            self.total_charges = (
                self.brokerage +
                self.stt +
                self.exchange_txn_charge +
                self.gst +
                self.stamp_duty +
                self.sebi_charges
            )

        # Calculate net value
        if self.net_value == Decimal('0'):
            if self.side == 'BUY':
                # Buy costs more (add charges)
                self.net_value = self.gross_value + self.total_charges
            else:
                # Sell gets less (subtract charges)
                self.net_value = self.gross_value - self.total_charges

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.side == 'BUY'

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell trade."""
        return self.side == 'SELL'

    @property
    def charges_percentage(self) -> float:
        """Get charges as percentage of gross value."""
        if self.gross_value == 0:
            return 0.0
        return float((self.total_charges / self.gross_value) * 100)

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'position_id': self.position_id,
            'broker_trade_id': self.broker_trade_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side,
            'quantity': self.quantity,
            'price': float(self.price),
            'brokerage': float(self.brokerage),
            'stt': float(self.stt),
            'exchange_txn_charge': float(self.exchange_txn_charge),
            'gst': float(self.gst),
            'stamp_duty': float(self.stamp_duty),
            'sebi_charges': float(self.sebi_charges),
            'total_charges': float(self.total_charges),
            'gross_value': float(self.gross_value),
            'net_value': float(self.net_value),
            'charges_percentage': self.charges_percentage,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'is_buy': self.is_buy,
            'is_sell': self.is_sell,
            'metadata': self.metadata
        }


def calculate_zerodha_charges(
    side: str,
    quantity: int,
    price: Decimal,
    product: str = 'MIS'
) -> Dict[str, Decimal]:
    """
    Calculate Zerodha transaction charges.

    This is an approximation based on Zerodha's pricing:
    - Brokerage: ₹20 per order or 0.03% (whichever is lower) for intraday
    - Brokerage: 0% for delivery
    - STT: 0.025% on sell side (delivery), 0.025% on both sides (intraday)
    - Exchange txn charge: 0.00325% (NSE)
    - GST: 18% on (brokerage + txn charges)
    - Stamp duty: 0.003% on buy side
    - SEBI charges: ₹10 per crore

    Args:
        side: BUY or SELL
        quantity: Number of shares
        price: Price per share
        product: MIS (intraday) or CNC (delivery)

    Returns:
        Dict with all charge components
    """
    gross_value = quantity * price

    charges = {
        'brokerage': Decimal('0'),
        'stt': Decimal('0'),
        'exchange_txn_charge': Decimal('0'),
        'gst': Decimal('0'),
        'stamp_duty': Decimal('0'),
        'sebi_charges': Decimal('0')
    }

    # Brokerage
    if product == 'MIS':
        # Intraday: ₹20 or 0.03%, whichever is lower
        brokerage_pct = gross_value * Decimal('0.0003')  # 0.03%
        charges['brokerage'] = min(Decimal('20'), brokerage_pct)
    else:
        # Delivery: 0%
        charges['brokerage'] = Decimal('0')

    # STT (Securities Transaction Tax)
    if product == 'MIS':
        # Intraday: 0.025% on sell side
        if side == 'SELL':
            charges['stt'] = gross_value * Decimal('0.00025')
    else:
        # Delivery: 0.1% on sell side
        if side == 'SELL':
            charges['stt'] = gross_value * Decimal('0.001')

    # Exchange transaction charge (NSE: 0.00325%)
    charges['exchange_txn_charge'] = gross_value * Decimal('0.0000325')

    # GST: 18% on (brokerage + exchange charges)
    taxable_amount = charges['brokerage'] + charges['exchange_txn_charge']
    charges['gst'] = taxable_amount * Decimal('0.18')

    # Stamp duty: 0.003% on buy side
    if side == 'BUY':
        charges['stamp_duty'] = gross_value * Decimal('0.00003')

    # SEBI charges: ₹10 per crore (₹10,000,000)
    charges['sebi_charges'] = (gross_value / Decimal('10000000')) * Decimal('10')

    return charges


def trade_from_db_row(row: Dict) -> Trade:
    """
    Create Trade object from database row.

    Args:
        row: Database row as dictionary

    Returns:
        Trade object
    """
    return Trade(
        id=row['id'],
        order_id=row['order_id'],
        position_id=row.get('position_id'),
        broker_trade_id=row.get('broker_trade_id'),
        symbol=row['symbol'],
        exchange=row['exchange'],
        side=row['side'],
        quantity=row['quantity'],
        price=Decimal(str(row['price'])),
        brokerage=Decimal(str(row.get('brokerage', 0))),
        stt=Decimal(str(row.get('stt', 0))),
        exchange_txn_charge=Decimal(str(row.get('exchange_txn_charge', 0))),
        gst=Decimal(str(row.get('gst', 0))),
        stamp_duty=Decimal(str(row.get('stamp_duty', 0))),
        sebi_charges=Decimal(str(row.get('sebi_charges', 0))),
        total_charges=Decimal(str(row.get('total_charges', 0))),
        gross_value=Decimal(str(row.get('gross_value', 0))),
        net_value=Decimal(str(row.get('net_value', 0))),
        executed_at=row.get('executed_at'),
        metadata=row.get('metadata', {})
    )
