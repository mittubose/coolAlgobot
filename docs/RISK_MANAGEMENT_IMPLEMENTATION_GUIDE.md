# Risk Management System - Implementation Guide

**Version:** 1.0
**Priority:** CRITICAL (P0)
**Estimated Effort:** 50 hours (Weeks 5-6)
**Dependencies:** OMS must be complete
**Status:** Not Started

---

## Executive Summary

The Risk Management System is your **financial safety net**. It prevents catastrophic losses through:

1. **Pre-Trade Validation** - Block risky orders BEFORE they reach the market
2. **Real-Time Monitoring** - Watch positions and kill switch if limits breached
3. **Position-Level Controls** - Auto-close positions approaching stop-loss
4. **Account-Level Controls** - Daily loss limits, max positions, max risk
5. **Emergency Controls** - Kill switch to close everything instantly

**Why This Matters:**
- **Without Risk Management:** One bad trade can wipe out weeks of profits
- **With Risk Management:** Max loss is controlled, predictable, recoverable

**Real-World Example:**
- Strategy wins 9 trades: +₹500, +₹600, +₹450 ... = +₹4,500
- Strategy loses 1 trade without stop-loss: -₹10,000
- **Net result: -₹5,500 (disaster)**

With risk management:
- Same 9 winning trades: +₹4,500
- Losing trade auto-closed at stop-loss: -₹200
- **Net result: +₹4,300 (success)**

---

## Risk Management Rules (NEVER VIOLATE)

### Rule 1: Maximum Risk Per Trade = 2% of Account

```
Example:
- Account balance: ₹100,000
- Max risk per trade: ₹2,000

BUY Order:
- Entry: ₹2,450
- Stop-loss: ₹2,430
- Risk per share: ₹20
- Max quantity: ₹2,000 / ₹20 = 100 shares

If you want 200 shares:
- Risk: 200 × ₹20 = ₹4,000
- ❌ REJECTED: Exceeds 2% limit
```

### Rule 2: Maximum Daily Loss = 6% of Account

```
Example:
- Account balance: ₹100,000
- Max daily loss: ₹6,000

Current day's trades:
- Trade 1: -₹1,500
- Trade 2: -₹2,000
- Trade 3: -₹2,000
- Total: -₹5,500

Next trade potential loss: ₹1,000
- Current loss + potential: ₹5,500 + ₹1,000 = ₹6,500
- ❌ REJECTED: Would exceed daily limit
```

### Rule 3: Minimum Risk-Reward Ratio = 2:1

```
Example:
BUY Order:
- Entry: ₹2,450
- Stop-loss: ₹2,430 (risk: ₹20/share)
- Take-profit: ₹2,491 (reward: ₹41/share)
- RR Ratio: ₹41 / ₹20 = 2.05:1
- ✓ ACCEPTED

BAD Order:
- Entry: ₹2,450
- Stop-loss: ₹2,430 (risk: ₹20/share)
- Take-profit: ₹2,470 (reward: ₹20/share)
- RR Ratio: ₹20 / ₹20 = 1:1
- ❌ REJECTED: Below 2:1 minimum
```

### Rule 4: Maximum Open Positions = 5

```
No more than 5 symbols at any time.

Current positions:
1. RELIANCE: 100 shares
2. TCS: 50 shares
3. INFY: 75 shares
4. HDFC: 200 shares
5. ICICI: 150 shares

Try to open 6th position:
- ❌ REJECTED: Max positions limit reached
- Must close one position first
```

### Rule 5: Stop-Loss is MANDATORY

```
ALL orders MUST have stop-loss defined.

Order without stop-loss:
- ❌ REJECTED: Stop-loss required

Order with stop-loss = entry price:
- ❌ REJECTED: Stop-loss cannot equal entry

Order with stop-loss on wrong side:
- BUY at ₹2,450 with SL at ₹2,480 (above entry)
- ❌ REJECTED: Stop-loss must be below entry for BUY
```

### Rule 6: Price Sanity Check = ±10% of LTP

```
Prevents "fat-finger" errors.

Current LTP: ₹2,450
- Lower bound: ₹2,205 (90% of LTP)
- Upper bound: ₹2,695 (110% of LTP)

Order at ₹2,500:
- Within bounds
- ✓ ACCEPTED

Order at ₹3,000:
- ₹3,000 > ₹2,695 (upper bound)
- ❌ REJECTED: Price too far from LTP
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       TRADING STRATEGY                            │
│  Detects hammer pattern, wants to place BUY order               │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ OrderRequest
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ORDER MANAGEMENT SYSTEM                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              PRE-TRADE VALIDATOR                            │ │
│  │                                                              │ │
│  │  ✓ Balance Check         ✓ Risk Per Trade (2%)            │ │
│  │  ✓ Position Limit (5)    ✓ Daily Loss Limit (6%)          │ │
│  │  ✓ Stop-Loss Required    ✓ Risk-Reward Ratio (2:1)        │ │
│  │  ✓ Price Sanity (±10%)   ✓ Order-to-Trade Ratio           │ │
│  │  ✓ Quantity Limits       ✓ Circuit Breaker Check          │ │
│  │                                                              │ │
│  │  IF ALL PASS → Submit order to broker                       │ │
│  │  IF ANY FAIL → Reject order, log reason                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ Order Submitted
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                  REAL-TIME RISK MONITOR                           │
│  (Runs continuously, checks every 1 second)                       │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Account-Level Monitoring:                                  │ │
│  │  - Today's PnL: -₹5,500 / -₹6,000 limit (92% used)        │ │
│  │  - Drawdown: 12% / 15% limit (80% used)                    │ │
│  │  - Open Positions: 4 / 5 limit                              │ │
│  │                                                              │ │
│  │  IF daily loss >= ₹6,000 → KILL SWITCH                     │ │
│  │  IF drawdown >= 15% → KILL SWITCH                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Position-Level Monitoring:                                 │ │
│  │  - RELIANCE: LTP ₹2,431, SL ₹2,430 → CLOSE (SL hit)       │ │
│  │  - TCS: Unrealized PnL -₹4,800 → CLOSE (5% loss)          │ │
│  │  - INFY: Held 6 hours → WARN (time-based SL)              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  KILL SWITCH (Emergency Stop All)                           │ │
│  │  - Close ALL positions at market price                       │ │
│  │  - Block new orders                                          │ │
│  │  - Send critical alerts                                      │ │
│  │  - Notify user in dashboard                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Pre-Trade Validator

**File:** `backend/risk/pre_trade_validator.py`

**Purpose:** Validate every order BEFORE submitting to broker

### Implementation

```python
# File: backend/risk/pre_trade_validator.py

import logging
from typing import Optional, List
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

from backend.models import OrderRequest
from backend.account_manager import AccountManager
from backend.oms.position_manager import PositionManager

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of order validation."""
    is_valid: bool
    failed_check: Optional[str] = None
    reason: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self):
        return {
            'is_valid': self.is_valid,
            'failed_check': self.failed_check,
            'reason': self.reason,
            'warnings': self.warnings,
            'timestamp': datetime.utcnow().isoformat()
        }


@dataclass
class CheckResult:
    """Result of individual risk check."""
    passed: bool
    reason: Optional[str] = None
    severity: str = 'ERROR'  # ERROR, WARNING, INFO


class PreTradeValidator:
    """
    Comprehensive pre-trade risk validation.

    ALL orders MUST pass ALL checks before submission.
    """

    def __init__(
        self,
        account: AccountManager,
        positions: PositionManager,
        config: dict
    ):
        self.account = account
        self.positions = positions
        self.config = config

        # Risk limits (from config or defaults)
        self.MAX_RISK_PER_TRADE = config.get('max_risk_per_trade', 0.02)  # 2%
        self.MAX_DAILY_LOSS = config.get('max_daily_loss', 0.06)          # 6%
        self.MAX_POSITIONS = config.get('max_positions', 5)
        self.MIN_RISK_REWARD = config.get('min_risk_reward', 2.0)         # 2:1
        self.MAX_POSITION_SIZE = config.get('max_position_size', 1000)    # shares
        self.PRICE_SANITY_PCT = config.get('price_sanity_pct', 0.10)     # ±10%

    async def validate_order(self, order: OrderRequest) -> ValidationResult:
        """
        Run all pre-trade validation checks.

        Returns ValidationResult with is_valid=True if all checks pass.
        Returns ValidationResult with is_valid=False and reason if any check fails.
        """
        logger.info(f"Validating order: {order.symbol} {order.side} {order.quantity}")

        checks = [
            ('Balance Check', self.check_balance(order)),
            ('Position Limit', self.check_position_limits(order)),
            ('Risk Per Trade', self.check_risk_per_trade(order)),
            ('Daily Loss Limit', self.check_daily_loss_limit(order)),
            ('Stop-Loss Required', self.check_stop_loss_required(order)),
            ('Risk-Reward Ratio', self.check_risk_reward_ratio(order)),
            ('Price Sanity', self.check_price_sanity(order)),
            ('Quantity Limits', self.check_quantity_limits(order)),
            ('Order-to-Trade Ratio', self.check_order_to_trade_ratio()),
            ('Circuit Breaker', self.check_circuit_breaker(order))
        ]

        warnings = []

        for check_name, check_coro in checks:
            result = await check_coro

            if not result.passed:
                logger.warning(f"❌ {check_name} FAILED: {result.reason}")

                return ValidationResult(
                    is_valid=False,
                    failed_check=check_name,
                    reason=result.reason,
                    warnings=warnings
                )

            elif result.severity == 'WARNING':
                warnings.append(f"{check_name}: {result.reason}")

        logger.info(f"✓ All validation checks passed")

        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )

    async def check_balance(self, order: OrderRequest) -> CheckResult:
        """
        Check if sufficient account balance for order.

        Required balance = quantity × price + buffer (5%)
        """
        account_balance = await self.account.get_available_balance()

        # Calculate required funds
        if order.order_type == 'MARKET':
            # For market orders, estimate with ±2% buffer
            ltp = await self.get_ltp(order.symbol)
            estimated_price = ltp * 1.02  # 2% buffer for slippage
        else:
            estimated_price = order.price

        required_balance = order.quantity * estimated_price

        # Add 5% buffer for costs (brokerage, taxes)
        required_balance *= 1.05

        if account_balance < required_balance:
            return CheckResult(
                passed=False,
                reason=(
                    f"Insufficient balance. "
                    f"Required: ₹{required_balance:,.2f}, "
                    f"Available: ₹{account_balance:,.2f}"
                )
            )

        return CheckResult(passed=True)

    async def check_position_limits(self, order: OrderRequest) -> CheckResult:
        """
        Check if opening this position would exceed max positions limit.

        Max positions = 5 (configurable)
        """
        current_positions = await self.positions.get_open_position_count()

        # Check if we already have a position in this symbol
        existing_position = await self.positions.get_position(order.symbol)

        if existing_position and existing_position.quantity != 0:
            # Adding to existing position - OK
            return CheckResult(passed=True)

        # Opening new position
        if current_positions >= self.MAX_POSITIONS:
            return CheckResult(
                passed=False,
                reason=(
                    f"Maximum positions limit reached "
                    f"({current_positions}/{self.MAX_POSITIONS}). "
                    f"Close a position before opening new one."
                )
            )

        return CheckResult(passed=True)

    async def check_risk_per_trade(self, order: OrderRequest) -> CheckResult:
        """
        Check if risk per trade <= 2% of account balance.

        Risk = |Entry Price - Stop Loss| × Quantity
        """
        if order.stop_loss is None:
            # This should be caught by check_stop_loss_required first
            return CheckResult(
                passed=False,
                reason="Stop-loss is required to calculate risk"
            )

        # Calculate risk amount
        entry_price = order.price if order.order_type != 'MARKET' else await self.get_ltp(order.symbol)
        risk_per_share = abs(entry_price - order.stop_loss)
        total_risk = risk_per_share * order.quantity

        # Get account balance
        account_balance = await self.account.get_balance()
        max_risk_allowed = account_balance * self.MAX_RISK_PER_TRADE

        if total_risk > max_risk_allowed:
            return CheckResult(
                passed=False,
                reason=(
                    f"Risk per trade ₹{total_risk:,.2f} exceeds "
                    f"maximum ₹{max_risk_allowed:,.2f} "
                    f"({self.MAX_RISK_PER_TRADE * 100:.0f}% of account). "
                    f"Reduce quantity to {int(max_risk_allowed / risk_per_share)} shares."
                )
            )

        # Warning if risk > 1% (conservative)
        if total_risk > account_balance * 0.01:
            return CheckResult(
                passed=True,
                reason=f"Risk is {total_risk / account_balance:.1%} of account (>1%)",
                severity='WARNING'
            )

        return CheckResult(passed=True)

    async def check_daily_loss_limit(self, order: OrderRequest) -> CheckResult:
        """
        Check if potential daily loss <= 6% of account balance.

        Current day's PnL + potential loss from this order <= 6%
        """
        today_pnl = await self.account.get_today_pnl()
        account_balance = await self.account.get_balance()

        max_daily_loss = account_balance * self.MAX_DAILY_LOSS

        # If already at or beyond daily limit, reject all orders
        if today_pnl <= -max_daily_loss:
            return CheckResult(
                passed=False,
                reason=(
                    f"Daily loss limit reached. "
                    f"Today's PnL: ₹{today_pnl:,.2f} "
                    f"(limit: -₹{max_daily_loss:,.2f}). "
                    f"No new orders allowed today."
                )
            )

        # Calculate potential loss from this order
        if order.stop_loss:
            entry_price = order.price if order.order_type != 'MARKET' else await self.get_ltp(order.symbol)
            potential_loss = abs(entry_price - order.stop_loss) * order.quantity

            # Check if current loss + potential loss exceeds limit
            total_potential_loss = abs(today_pnl) + potential_loss

            if total_potential_loss > max_daily_loss:
                return CheckResult(
                    passed=False,
                    reason=(
                        f"Order would exceed daily loss limit. "
                        f"Current loss: ₹{abs(today_pnl):,.2f}, "
                        f"Potential additional: ₹{potential_loss:,.2f}, "
                        f"Total: ₹{total_potential_loss:,.2f} "
                        f"(limit: ₹{max_daily_loss:,.2f})"
                    )
                )

        # Warning if approaching limit (>80% used)
        loss_pct_used = abs(today_pnl) / max_daily_loss
        if loss_pct_used > 0.80:
            return CheckResult(
                passed=True,
                reason=f"Close to daily loss limit ({loss_pct_used:.0%} used)",
                severity='WARNING'
            )

        return CheckResult(passed=True)

    async def check_stop_loss_required(self, order: OrderRequest) -> CheckResult:
        """
        Ensure stop-loss is defined for all orders.

        This is NON-NEGOTIABLE. Every order MUST have stop-loss.
        """
        if order.stop_loss is None:
            return CheckResult(
                passed=False,
                reason="Stop-loss is required for all orders. No exceptions."
            )

        # Get entry price
        entry_price = order.price if order.order_type != 'MARKET' else await self.get_ltp(order.symbol)

        # Validate stop-loss is on correct side
        if order.side == 'BUY':
            # For BUY orders, stop-loss must be BELOW entry
            if order.stop_loss >= entry_price:
                return CheckResult(
                    passed=False,
                    reason=(
                        f"Invalid stop-loss for BUY order. "
                        f"Stop-loss (₹{order.stop_loss:.2f}) must be below "
                        f"entry price (₹{entry_price:.2f})"
                    )
                )

        elif order.side == 'SELL':
            # For SELL orders, stop-loss must be ABOVE entry
            if order.stop_loss <= entry_price:
                return CheckResult(
                    passed=False,
                    reason=(
                        f"Invalid stop-loss for SELL order. "
                        f"Stop-loss (₹{order.stop_loss:.2f}) must be above "
                        f"entry price (₹{entry_price:.2f})"
                    )
                )

        # Validate stop-loss is not too tight (< 0.5% from entry)
        stop_loss_pct = abs(entry_price - order.stop_loss) / entry_price
        if stop_loss_pct < 0.005:  # 0.5%
            return CheckResult(
                passed=True,
                reason=f"Very tight stop-loss ({stop_loss_pct:.2%} from entry)",
                severity='WARNING'
            )

        return CheckResult(passed=True)

    async def check_risk_reward_ratio(self, order: OrderRequest) -> CheckResult:
        """
        Ensure risk-reward ratio >= 2:1.

        Minimum 2:1 required, prefer 3:1 or better.
        """
        if order.stop_loss is None or order.take_profit is None:
            return CheckResult(
                passed=False,
                reason="Both stop-loss and take-profit are required to calculate risk-reward ratio"
            )

        # Get entry price
        entry_price = order.price if order.order_type != 'MARKET' else await self.get_ltp(order.symbol)

        # Calculate risk and reward
        risk = abs(entry_price - order.stop_loss)
        reward = abs(order.take_profit - entry_price)

        if risk == 0:
            return CheckResult(
                passed=False,
                reason="Stop-loss cannot equal entry price"
            )

        rr_ratio = reward / risk

        if rr_ratio < self.MIN_RISK_REWARD:
            return CheckResult(
                passed=False,
                reason=(
                    f"Risk-reward ratio {rr_ratio:.2f}:1 is below "
                    f"minimum {self.MIN_RISK_REWARD:.1f}:1. "
                    f"Risk: ₹{risk:.2f}/share, Reward: ₹{reward:.2f}/share. "
                    f"Adjust take-profit to at least ₹{entry_price + (risk * self.MIN_RISK_REWARD):.2f}"
                )
            )

        # Warning if RR is exactly 2:1 (prefer better)
        if 2.0 <= rr_ratio < 2.5:
            return CheckResult(
                passed=True,
                reason=f"Low risk-reward ratio ({rr_ratio:.2f}:1). Consider aiming for 3:1 or better.",
                severity='WARNING'
            )

        return CheckResult(passed=True)

    async def check_price_sanity(self, order: OrderRequest) -> CheckResult:
        """
        Ensure order price is within ±10% of Last Traded Price (LTP).

        Prevents "fat-finger" errors (e.g., typing 24500 instead of 2450).
        """
        if order.order_type == 'MARKET':
            # Market orders don't have price, skip this check
            return CheckResult(passed=True)

        # Get current LTP
        ltp = await self.get_ltp(order.symbol)

        # Calculate bounds
        lower_bound = ltp * (1 - self.PRICE_SANITY_PCT)
        upper_bound = ltp * (1 + self.PRICE_SANITY_PCT)

        if order.price < lower_bound or order.price > upper_bound:
            return CheckResult(
                passed=False,
                reason=(
                    f"Order price ₹{order.price:.2f} is outside ±{self.PRICE_SANITY_PCT * 100:.0f}% "
                    f"of LTP ₹{ltp:.2f}. "
                    f"Valid range: ₹{lower_bound:.2f} - ₹{upper_bound:.2f}. "
                    f"This may be a fat-finger error."
                )
            )

        return CheckResult(passed=True)

    async def check_quantity_limits(self, order: OrderRequest) -> CheckResult:
        """
        Check if order quantity is within allowed limits.

        Max quantity per order = 1000 shares (configurable)
        """
        if order.quantity <= 0:
            return CheckResult(
                passed=False,
                reason="Order quantity must be greater than zero"
            )

        if order.quantity > self.MAX_POSITION_SIZE:
            return CheckResult(
                passed=False,
                reason=(
                    f"Order quantity {order.quantity} exceeds "
                    f"maximum {self.MAX_POSITION_SIZE} shares per order"
                )
            )

        # Get exchange-specific lot size
        lot_size = await self.get_lot_size(order.symbol, order.exchange)

        if order.quantity % lot_size != 0:
            return CheckResult(
                passed=False,
                reason=(
                    f"Order quantity {order.quantity} is not a multiple "
                    f"of lot size {lot_size} for {order.symbol}"
                )
            )

        return CheckResult(passed=True)

    async def check_order_to_trade_ratio(self) -> CheckResult:
        """
        Check order-to-trade ratio to prevent excessive order spam.

        Exchanges have limits (e.g., 20:1 for NSE).
        We enforce 10:1 to be conservative.
        """
        # Get today's stats
        today_orders = await self.account.get_today_order_count()
        today_trades = await self.account.get_today_trade_count()

        if today_trades == 0:
            # No trades yet, allow some initial orders
            if today_orders > 20:
                return CheckResult(
                    passed=False,
                    reason=f"Too many orders ({today_orders}) with no trades today"
                )
            return CheckResult(passed=True)

        ratio = today_orders / today_trades

        if ratio > 10:
            return CheckResult(
                passed=False,
                reason=(
                    f"Order-to-trade ratio ({ratio:.1f}:1) exceeds limit (10:1). "
                    f"Orders: {today_orders}, Trades: {today_trades}. "
                    f"This may indicate strategy issues or market manipulation."
                )
            )

        return CheckResult(passed=True)

    async def check_circuit_breaker(self, order: OrderRequest) -> CheckResult:
        """
        Check if symbol is in circuit breaker or trading halt.
        """
        # Get market status for symbol
        market_status = await self.get_market_status(order.symbol, order.exchange)

        if market_status.get('status') != 'OPEN':
            return CheckResult(
                passed=False,
                reason=f"Market is {market_status.get('status')} for {order.symbol}"
            )

        # Check for circuit breaker
        if market_status.get('circuit_breaker'):
            return CheckResult(
                passed=False,
                reason=f"{order.symbol} is in circuit breaker (limit hit)"
            )

        # Check for trading halt
        if market_status.get('trading_halt'):
            return CheckResult(
                passed=False,
                reason=f"{order.symbol} trading is halted: {market_status.get('halt_reason')}"
            )

        return CheckResult(passed=True)

    # Helper methods

    async def get_ltp(self, symbol: str) -> Decimal:
        """Get Last Traded Price for symbol."""
        # This would query your market data feed
        # For now, placeholder
        from backend.market_data import MarketData
        market_data = MarketData()
        ltp = await market_data.get_ltp(symbol)
        return Decimal(str(ltp))

    async def get_lot_size(self, symbol: str, exchange: str) -> int:
        """Get lot size for symbol."""
        # Query instrument master
        from backend.instruments import InstrumentMaster
        instruments = InstrumentMaster()
        instrument = await instruments.get(symbol, exchange)
        return instrument.lot_size

    async def get_market_status(self, symbol: str, exchange: str) -> dict:
        """Get market status for symbol."""
        from backend.market_data import MarketData
        market_data = MarketData()
        return await market_data.get_status(symbol, exchange)
```

### Usage Example

```python
from backend.risk.pre_trade_validator import PreTradeValidator
from backend.models import OrderRequest

validator = PreTradeValidator(account_manager, position_manager, config)

order = OrderRequest(
    symbol='RELIANCE',
    exchange='NSE',
    side='BUY',
    quantity=100,
    order_type='LIMIT',
    price=2450.50,
    stop_loss=2430.00,
    take_profit=2491.00,
    product='MIS',
    validity='DAY'
)

result = await validator.validate_order(order)

if result.is_valid:
    print("✓ Order validated, safe to submit")
    if result.warnings:
        for warning in result.warnings:
            print(f"⚠ {warning}")
else:
    print(f"❌ Order rejected: {result.reason}")
    print(f"Failed check: {result.failed_check}")
```

---

## Component 2: Real-Time Risk Monitor

**File:** `backend/risk/real_time_monitor.py`

**Purpose:** Monitor positions and account in real-time, trigger kill switch if needed

### Implementation

```python
# File: backend/risk/real_time_monitor.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from backend.account_manager import AccountManager
from backend.oms.position_manager import PositionManager
from backend.oms.order_manager import OrderManager
from backend.alerts import AlertManager
from backend.websocket import WebSocketManager

logger = logging.getLogger(__name__)


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and kill switch.

    Runs continuously, checking:
    - Account-level risk (daily loss, drawdown)
    - Position-level risk (stop-loss hits, excessive losses)
    - Circuit breakers

    Auto-triggers kill switch if critical limits breached.
    """

    def __init__(
        self,
        account: AccountManager,
        positions: PositionManager,
        orders: OrderManager,
        alerts: AlertManager,
        websocket: WebSocketManager,
        config: dict
    ):
        self.account = account
        self.positions = positions
        self.orders = orders
        self.alerts = alerts
        self.websocket = websocket
        self.config = config

        # Risk limits
        self.MAX_DAILY_LOSS_PCT = config.get('max_daily_loss', 0.06)      # 6%
        self.MAX_DRAWDOWN_PCT = config.get('max_drawdown', 0.15)          # 15%
        self.MAX_POSITION_LOSS_PCT = config.get('max_position_loss', 0.05)  # 5%

        # Kill switch state
        self.kill_switch_active = False
        self.kill_switch_reason = None
        self.kill_switch_triggered_at = None

    async def start(self):
        """Start real-time monitoring."""
        logger.info("🚨 Real-time risk monitoring started")

        # Start monitoring loops
        await asyncio.gather(
            self.monitor_account_risk(),
            self.monitor_position_risk(),
            self.broadcast_risk_updates()
        )

    async def monitor_account_risk(self):
        """
        Monitor account-level risk metrics.
        Checks every 1 second.
        """
        logger.info("Account risk monitoring started")

        while True:
            try:
                if self.kill_switch_active:
                    await asyncio.sleep(5)
                    continue

                # Get account metrics
                today_pnl = await self.account.get_today_pnl()
                account_balance = await self.account.get_balance()
                peak_balance_today = await self.account.get_peak_balance_today()

                # Check daily loss limit
                max_daily_loss = account_balance * self.MAX_DAILY_LOSS_PCT
                if today_pnl <= -max_daily_loss:
                    logger.critical(
                        f"🚨 DAILY LOSS LIMIT BREACHED: "
                        f"₹{today_pnl:,.2f} (limit: -₹{max_daily_loss:,.2f})"
                    )
                    await self.trigger_kill_switch('DAILY_LOSS_LIMIT_BREACHED')

                # Check drawdown limit
                current_balance = account_balance + today_pnl
                drawdown = (peak_balance_today - current_balance) / peak_balance_today

                if drawdown >= self.MAX_DRAWDOWN_PCT:
                    logger.critical(
                        f"🚨 DRAWDOWN LIMIT BREACHED: "
                        f"{drawdown:.2%} (limit: {self.MAX_DRAWDOWN_PCT:.2%})"
                    )
                    await self.trigger_kill_switch('DRAWDOWN_LIMIT_BREACHED')

                # Warning alerts (80% of limit)
                if today_pnl <= -(max_daily_loss * 0.80):
                    await self.alerts.send_warning(
                        title='Approaching Daily Loss Limit',
                        message=f"Today's PnL: ₹{today_pnl:,.2f} ({abs(today_pnl) / max_daily_loss:.0%} of limit)",
                        priority='HIGH'
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in account risk monitoring: {e}")
                await asyncio.sleep(5)

    async def monitor_position_risk(self):
        """
        Monitor position-level risk metrics.
        Checks every 1 second.
        """
        logger.info("Position risk monitoring started")

        while True:
            try:
                if self.kill_switch_active:
                    await asyncio.sleep(5)
                    continue

                # Get all open positions
                positions = await self.positions.get_all_open_positions()

                for position in positions:
                    await self.check_position(position)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in position risk monitoring: {e}")
                await asyncio.sleep(5)

    async def check_position(self, position):
        """
        Check individual position for risk events.
        """
        symbol = position.symbol

        # Get current price
        ltp = await self.get_ltp(symbol)

        # Check stop-loss
        if position.stop_loss:
            stop_loss_hit = (
                (position.quantity > 0 and ltp <= position.stop_loss) or
                (position.quantity < 0 and ltp >= position.stop_loss)
            )

            if stop_loss_hit:
                logger.warning(f"⚠ Stop-loss hit for {symbol} at ₹{ltp:.2f}")
                await self.close_position(
                    symbol=symbol,
                    reason='STOP_LOSS_HIT',
                    price=ltp
                )

        # Check for excessive unrealized loss (5% of account)
        unrealized_pnl = await self.positions.get_unrealized_pnl(symbol, ltp)
        account_balance = await self.account.get_balance()
        max_position_loss = account_balance * self.MAX_POSITION_LOSS_PCT

        if unrealized_pnl <= -max_position_loss:
            logger.error(
                f"⚠ Excessive loss on {symbol}: "
                f"₹{unrealized_pnl:,.2f} (limit: -₹{max_position_loss:,.2f})"
            )
            await self.close_position(
                symbol=symbol,
                reason='EXCESSIVE_LOSS',
                price=ltp
            )

        # Check time-based stop-loss (if configured)
        if position.time_based_sl_hours:
            hours_held = (datetime.utcnow() - position.opened_at).total_seconds() / 3600

            if hours_held >= position.time_based_sl_hours:
                logger.info(f"Time-based stop-loss triggered for {symbol} ({hours_held:.1f} hours)")
                await self.close_position(
                    symbol=symbol,
                    reason='TIME_BASED_SL',
                    price=ltp
                )

    async def close_position(self, symbol: str, reason: str, price: float):
        """
        Close position at market price.
        """
        logger.info(f"Closing position: {symbol} (reason: {reason})")

        position = await self.positions.get_position(symbol)

        if position.quantity == 0:
            logger.warning(f"No open position for {symbol}")
            return

        # Determine order side (opposite of position)
        side = 'SELL' if position.quantity > 0 else 'BUY'

        # Place market order to close
        close_order = OrderRequest(
            symbol=symbol,
            exchange=position.exchange,
            side=side,
            quantity=abs(position.quantity),
            order_type='MARKET',
            product=position.product,
            validity='DAY',
            metadata={'exit_reason': reason}
        )

        try:
            result = await self.orders.place_order(close_order)
            logger.info(f"Position close order submitted: {result.order_id}")

            # Send alert
            await self.alerts.send_info(
                title=f'Position Closed: {symbol}',
                message=f'Reason: {reason}\nQuantity: {abs(position.quantity)}\nPrice: ₹{price:.2f}'
            )

        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")

            await self.alerts.send_critical(
                title=f'FAILED TO CLOSE POSITION: {symbol}',
                message=f'Reason: {reason}\nError: {e}\n\nMANUAL INTERVENTION REQUIRED'
            )

    async def trigger_kill_switch(self, reason: str):
        """
        EMERGENCY: Close ALL positions immediately.

        This is the nuclear option. Use only when critical limits breached.
        """
        if self.kill_switch_active:
            logger.warning("Kill switch already active, skipping")
            return

        self.kill_switch_active = True
        self.kill_switch_reason = reason
        self.kill_switch_triggered_at = datetime.utcnow()

        logger.critical(f"🚨🚨🚨 KILL SWITCH ACTIVATED: {reason} 🚨🚨🚨")

        # Send critical alert IMMEDIATELY
        await self.alerts.send_critical(
            title='🚨 KILL SWITCH ACTIVATED',
            message=(
                f"Reason: {reason}\n"
                f"Time: {datetime.utcnow().isoformat()}\n"
                f"Action: Closing all positions\n\n"
                f"Check dashboard immediately!"
            )
        )

        # Broadcast to dashboard
        await self.websocket.broadcast({
            'type': 'KILL_SWITCH_ACTIVATED',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Get all open positions
        positions = await self.positions.get_all_open_positions()

        logger.critical(f"Closing {len(positions)} open positions...")

        close_results = []

        # Close each position
        for position in positions:
            try:
                ltp = await self.get_ltp(position.symbol)

                await self.close_position(
                    symbol=position.symbol,
                    reason=f'KILL_SWITCH_{reason}',
                    price=ltp
                )

                close_results.append({
                    'symbol': position.symbol,
                    'status': 'SUBMITTED',
                    'quantity': position.quantity
                })

            except Exception as e:
                logger.error(f"Failed to close {position.symbol}: {e}")

                close_results.append({
                    'symbol': position.symbol,
                    'status': 'FAILED',
                    'error': str(e)
                })

        # Log kill switch event
        await self.account.log_kill_switch_event(
            reason=reason,
            close_results=close_results,
            triggered_at=self.kill_switch_triggered_at
        )

        logger.critical(f"Kill switch completed. {len(positions)} positions submitted for closure.")

    async def deactivate_kill_switch(self):
        """
        Deactivate kill switch (manual intervention required).
        """
        if not self.kill_switch_active:
            logger.warning("Kill switch not active")
            return

        logger.info("Deactivating kill switch")

        self.kill_switch_active = False

        await self.websocket.broadcast({
            'type': 'KILL_SWITCH_DEACTIVATED',
            'timestamp': datetime.utcnow().isoformat()
        })

        await self.alerts.send_info(
            title='Kill Switch Deactivated',
            message='Trading can resume. Review what went wrong before placing new orders.'
        )

    async def broadcast_risk_updates(self):
        """
        Broadcast risk metrics to dashboard every 2 seconds.
        """
        while True:
            try:
                # Get account metrics
                today_pnl = await self.account.get_today_pnl()
                account_balance = await self.account.get_balance()
                open_positions = await self.positions.get_open_position_count()

                # Calculate total risk from open positions
                total_risk = 0
                positions = await self.positions.get_all_open_positions()

                for position in positions:
                    if position.stop_loss:
                        ltp = await self.get_ltp(position.symbol)
                        position_risk = abs(ltp - position.stop_loss) * abs(position.quantity)
                        total_risk += position_risk

                # Determine risk level
                max_daily_loss = account_balance * self.MAX_DAILY_LOSS_PCT
                loss_pct_used = abs(today_pnl) / max_daily_loss if today_pnl < 0 else 0

                if loss_pct_used >= 0.90 or self.kill_switch_active:
                    risk_level = 'CRITICAL'
                elif loss_pct_used >= 0.70:
                    risk_level = 'HIGH'
                elif loss_pct_used >= 0.50:
                    risk_level = 'MEDIUM'
                else:
                    risk_level = 'LOW'

                # Broadcast to dashboard
                await self.websocket.broadcast({
                    'type': 'riskUpdate',
                    'data': {
                        'today_pnl': float(today_pnl),
                        'account_balance': float(account_balance),
                        'open_positions': open_positions,
                        'total_risk': float(total_risk),
                        'risk_level': risk_level,
                        'loss_pct_used': float(loss_pct_used),
                        'kill_switch_active': self.kill_switch_active,
                        'kill_switch_reason': self.kill_switch_reason,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error broadcasting risk updates: {e}")
                await asyncio.sleep(5)

    async def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price."""
        from backend.market_data import MarketData
        market_data = MarketData()
        return await market_data.get_ltp(symbol)
```

---

## Next Steps

1. **Week 5: Implement Pre-Trade Validator** (20 hours)
   - Write all validation checks
   - Unit tests (90% coverage)
   - Integration with OMS

2. **Week 6: Implement Real-Time Monitor** (20 hours)
   - Account monitoring loop
   - Position monitoring loop
   - Kill switch logic
   - WebSocket broadcasting

3. **Week 6: Kill Switch UI** (10 hours)
   - Dashboard component
   - Real-time risk metrics display
   - Emergency stop button
   - Alert visualization

**Total: 50 hours**

---

*Document Version: 1.0*
*Last Updated: October 25, 2025*
