"""
Reconciliation models and related data structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum


class IssueType(Enum):
    """Reconciliation issue type enum."""
    UNKNOWN_POSITION = 'UNKNOWN_POSITION'      # Broker has position, we don't
    QUANTITY_MISMATCH = 'QUANTITY_MISMATCH'    # Quantities don't match
    PHANTOM_POSITION = 'PHANTOM_POSITION'      # We have position, broker doesn't
    PRICE_MISMATCH = 'PRICE_MISMATCH'          # Average prices don't match
    OTHER = 'OTHER'


class Severity(Enum):
    """Issue severity enum."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    CRITICAL = 'CRITICAL'


@dataclass
class ReconciliationIssue:
    """
    Reconciliation issue model (from database).

    Represents a mismatch between internal position state and broker state.
    """
    # Primary identifier
    id: int
    symbol: str
    exchange: str

    # Issue details
    issue_type: IssueType
    severity: Severity

    # Mismatch details
    internal_quantity: Optional[int] = None
    broker_quantity: Optional[int] = None
    difference: Optional[int] = None

    internal_avg_price: Optional[Decimal] = None
    broker_avg_price: Optional[Decimal] = None

    # Resolution
    resolved: bool = False
    resolution: Optional[str] = None
    auto_fixed: bool = False

    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Convert string enums to enum types."""
        if isinstance(self.issue_type, str):
            self.issue_type = IssueType(self.issue_type)
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical issue."""
        return self.severity == Severity.CRITICAL

    @property
    def hours_unresolved(self) -> float:
        """Get hours since issue was detected."""
        if self.resolved:
            return 0.0

        delta = datetime.utcnow() - self.detected_at
        return delta.total_seconds() / 3600

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'internal_quantity': self.internal_quantity,
            'broker_quantity': self.broker_quantity,
            'difference': self.difference,
            'internal_avg_price': float(self.internal_avg_price) if self.internal_avg_price else None,
            'broker_avg_price': float(self.broker_avg_price) if self.broker_avg_price else None,
            'resolved': self.resolved,
            'resolution': self.resolution,
            'auto_fixed': self.auto_fixed,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'hours_unresolved': self.hours_unresolved,
            'is_critical': self.is_critical,
            'metadata': self.metadata
        }


def reconciliation_issue_from_db_row(row: Dict) -> ReconciliationIssue:
    """
    Create ReconciliationIssue object from database row.

    Args:
        row: Database row as dictionary

    Returns:
        ReconciliationIssue object
    """
    return ReconciliationIssue(
        id=row['id'],
        symbol=row['symbol'],
        exchange=row['exchange'],
        issue_type=IssueType(row['issue_type']),
        severity=Severity(row['severity']),
        internal_quantity=row.get('internal_quantity'),
        broker_quantity=row.get('broker_quantity'),
        difference=row.get('difference'),
        internal_avg_price=Decimal(str(row['internal_avg_price'])) if row.get('internal_avg_price') else None,
        broker_avg_price=Decimal(str(row['broker_avg_price'])) if row.get('broker_avg_price') else None,
        resolved=row.get('resolved', False),
        resolution=row.get('resolution'),
        auto_fixed=row.get('auto_fixed', False),
        detected_at=row.get('detected_at'),
        resolved_at=row.get('resolved_at'),
        metadata=row.get('metadata', {})
    )
