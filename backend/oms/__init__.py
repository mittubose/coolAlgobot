"""
Order Management System (OMS) for XCoin Scalping Bot.

This package provides:
- OrderManager - Central order placement and lifecycle tracking
- PositionManager - Position tracking and management
- PreTradeValidator - Pre-trade risk validation
- RealTimeRiskMonitor - Real-time risk monitoring and kill switch
- Order validation and risk checks
- Position reconciliation with broker
"""

from .order_manager import OrderManager, OrderRejected, OrderSubmissionFailed, OrderNotFound
from .position_manager import PositionManager
from .pre_trade_validator import PreTradeValidator, ValidationResult
from .real_time_monitor import RealTimeRiskMonitor, RiskAlert

__all__ = [
    'OrderManager',
    'PositionManager',
    'PreTradeValidator',
    'RealTimeRiskMonitor',
    'ValidationResult',
    'RiskAlert',
    'OrderRejected',
    'OrderSubmissionFailed',
    'OrderNotFound',
]
