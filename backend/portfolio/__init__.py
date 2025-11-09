"""
Portfolio Management Module
Provides P&L calculation, risk metrics, trade deduplication, and CSV import
"""

from .pnl_calculator import PnLCalculator
from .risk_meter import RiskMeter
from .trade_deduplication import TradeDeduplicator
from .csv_parser import CSVImportParser

# Create alias for backward compatibility
CSVParser = CSVImportParser

__all__ = [
    'PnLCalculator',
    'RiskMeter',
    'TradeDeduplicator',
    'CSVImportParser',
    'CSVParser'  # Alias
]
