# Order Management System (OMS) - Implementation Guide

**Version:** 1.0
**Priority:** CRITICAL (P0)
**Estimated Effort:** 60 hours (Weeks 1-4)
**Dependencies:** None (first system to build)
**Status:** Not Started

---

## Executive Summary

The Order Management System (OMS) is the **most critical component** of any algorithmic trading platform. It sits between your strategies and the broker API, providing:

1. **Order Validation** - Prevent invalid/risky orders from reaching the broker
2. **Order Tracking** - Monitor order lifecycle from submission to fill/rejection
3. **Position Management** - Maintain accurate position state
4. **Reconciliation** - Ensure internal state matches broker reality
5. **Audit Trail** - Log every order for compliance and debugging

**Why This Matters:**
- **Without OMS:** Strategies place orders directly → No validation, no tracking, no safety
- **With OMS:** All orders flow through validation → Tracked, monitored, reconciled, safe

**Current Risk Without OMS:**
- Strategies can exceed position limits
- No stop-loss enforcement
- No daily loss limit protection
- Position state can drift from reality
- Orders can be lost in transit
- No way to track what went wrong

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRADING STRATEGY                          │
│  (e.g., Hammer Pattern Detector, RSI Scalper)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ place_order(request)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORDER MANAGEMENT SYSTEM                      │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Pre-Trade       │  │  Order           │  │  Position     │ │
│  │  Validator       │  │  Lifecycle       │  │  Manager      │ │
│  │                  │  │  Tracker         │  │               │ │
│  │  - Risk checks   │  │  - Monitor fills │  │  - Track qty  │ │
│  │  - Balance check │  │  - Update state  │  │  - Calc PnL   │ │
│  │  - Position lim  │  │  - Notify events │  │  - Reconcile  │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ORDER DATABASE                          │   │
│  │  - All orders logged (PENDING → SUBMITTED → FILLED)       │   │
│  │  - Immutable audit trail                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ zerodha.place_order()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ZERODHA KITE API                          │
│  - Order placement                                                │
│  - Order updates (WebSocket)                                      │
│  - Position queries                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### `orders` Table

```sql
CREATE TABLE orders (
    -- Primary identifiers
    id SERIAL PRIMARY KEY,
    broker_order_id VARCHAR(50) UNIQUE,  -- Zerodha's order ID
    strategy_id INT NOT NULL,             -- Which strategy placed this

    -- Order details
    symbol VARCHAR(20) NOT NULL,          -- e.g., "RELIANCE"
    exchange VARCHAR(10) NOT NULL,        -- e.g., "NSE"
    side VARCHAR(4) NOT NULL,             -- "BUY" or "SELL"
    quantity INT NOT NULL,                -- Number of shares/lots
    order_type VARCHAR(10) NOT NULL,      -- "MARKET", "LIMIT", "SL", "SL-M"
    price DECIMAL(10, 2),                 -- Limit price (NULL for market orders)
    trigger_price DECIMAL(10, 2),         -- Stop-loss trigger price

    -- Risk parameters
    stop_loss DECIMAL(10, 2),             -- Stop-loss price
    take_profit DECIMAL(10, 2),           -- Take-profit price
    risk_amount DECIMAL(10, 2),           -- Calculated risk (Entry - SL) * Qty

    -- Order state
    status VARCHAR(20) NOT NULL,          -- PENDING, SUBMITTED, OPEN, FILLED, CANCELLED, REJECTED
    status_message TEXT,                  -- Details (e.g., rejection reason)
    filled_quantity INT DEFAULT 0,        -- How many filled so far
    average_price DECIMAL(10, 2),         -- Average fill price

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),       -- When order created
    submitted_at TIMESTAMP,                            -- When sent to broker
    updated_at TIMESTAMP,                              -- Last status update
    filled_at TIMESTAMP,                               -- When fully filled

    -- Audit
    validation_result JSONB,              -- Results of all pre-trade checks
    error_message TEXT,                   -- Error if order failed

    -- Metadata
    metadata JSONB,                       -- Strategy-specific data

    CONSTRAINT valid_side CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT valid_order_type CHECK (order_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M')),
    CONSTRAINT valid_status CHECK (status IN ('PENDING', 'SUBMITTED', 'OPEN', 'FILLED', 'CANCELLED', 'REJECTED', 'FAILED'))
);

-- Indexes for fast lookups
CREATE INDEX idx_orders_broker_id ON orders(broker_order_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_strategy_id ON orders(strategy_id);
```

### `positions` Table

```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,

    -- Position details
    quantity INT NOT NULL,                -- Positive = long, Negative = short
    average_price DECIMAL(10, 2) NOT NULL,-- Average entry price

    -- PnL tracking
    realized_pnl DECIMAL(12, 2) DEFAULT 0,  -- Closed PnL
    unrealized_pnl DECIMAL(12, 2) DEFAULT 0, -- Open PnL (updated real-time)

    -- Risk management
    stop_loss DECIMAL(10, 2),             -- Position-level stop-loss
    take_profit DECIMAL(10, 2),           -- Position-level take-profit

    -- Timestamps
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,

    -- Metadata
    metadata JSONB,

    CONSTRAINT unique_position UNIQUE(symbol, exchange)
);

CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_open ON positions(closed_at) WHERE closed_at IS NULL;
```

### `trades` Table (Fills)

```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    broker_trade_id VARCHAR(50) UNIQUE,   -- Zerodha's trade ID

    -- Trade details
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity INT NOT NULL,                -- Quantity filled in this trade
    price DECIMAL(10, 2) NOT NULL,        -- Fill price

    -- Costs
    brokerage DECIMAL(10, 2),             -- Brokerage charged
    stt DECIMAL(10, 2),                   -- Securities Transaction Tax
    exchange_txn_charge DECIMAL(10, 2),   -- Exchange transaction charge
    gst DECIMAL(10, 2),                   -- GST on brokerage + txn charge
    stamp_duty DECIMAL(10, 2),            -- Stamp duty
    total_charges DECIMAL(10, 2),         -- Sum of all above

    -- Timestamp
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_executed_at ON trades(executed_at DESC);
```

### `reconciliation_log` Table

```sql
CREATE TABLE reconciliation_log (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,

    -- Mismatch details
    issue_type VARCHAR(50) NOT NULL,      -- UNKNOWN_POSITION, QUANTITY_MISMATCH, etc.
    internal_quantity INT,                -- Our records
    broker_quantity INT,                  -- Broker's records

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT,                      -- How it was resolved

    -- Timestamps
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,

    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_reconciliation_unresolved ON reconciliation_log(resolved) WHERE resolved = FALSE;
CREATE INDEX idx_reconciliation_detected_at ON reconciliation_log(detected_at DESC);
```

---

## Core Components

### 1. Order Manager (`backend/oms/order_manager.py`)

**Responsibility:** Central hub for all order operations

**Key Methods:**

```python
class OrderManager:
    async def place_order(self, order_request: OrderRequest) -> OrderResult
    async def cancel_order(self, order_id: int) -> bool
    async def modify_order(self, order_id: int, new_price: float) -> bool
    async def get_order_status(self, order_id: int) -> OrderStatus
    async def get_active_orders(self) -> List[Order]
    async def reconcile_positions(self) -> ReconciliationReport
```

**Example Usage:**

```python
# In your trading strategy
from backend.oms.order_manager import OrderManager, OrderRequest

order_manager = OrderManager(db, zerodha_client)

# Create order request
order = OrderRequest(
    symbol='RELIANCE',
    exchange='NSE',
    side='BUY',
    quantity=10,
    order_type='LIMIT',
    price=2450.50,
    stop_loss=2430.00,   # 20.50 risk per share = 205 total risk
    take_profit=2491.00, # 40.50 reward per share = 405 total reward
    product='MIS',       # Intraday
    validity='DAY',
    strategy_id=1
)

# Place order (goes through all validations)
try:
    result = await order_manager.place_order(order)

    print(f"Order placed successfully!")
    print(f"Order ID: {result.order_id}")
    print(f"Broker Order ID: {result.broker_order_id}")
    print(f"Status: {result.status}")

except OrderRejected as e:
    print(f"Order rejected: {e.reason}")
    # e.g., "Risk per trade exceeds 2% (₹205 > ₹200)"

except InsufficientBalance as e:
    print(f"Insufficient funds: {e.required} needed, {e.available} available")
```

**Full Implementation:**

```python
# File: backend/oms/order_manager.py

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
import logging

from backend.database import Database
from backend.zerodha_client import ZerodhaClient
from backend.oms.validators import PreTradeValidator
from backend.oms.position_manager import PositionManager
from backend.models import Order, OrderRequest, OrderResult, OrderStatus

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Central Order Management System.

    ALL orders MUST flow through this class.
    Direct calls to zerodha_client.place_order() are FORBIDDEN.
    """

    def __init__(
        self,
        db: Database,
        zerodha: ZerodhaClient,
        validator: PreTradeValidator,
        position_manager: PositionManager
    ):
        self.db = db
        self.zerodha = zerodha
        self.validator = validator
        self.positions = position_manager

        # In-memory cache of active orders
        self.active_orders: Dict[int, Order] = {}

        # Start background tasks
        asyncio.create_task(self._monitor_orders())
        asyncio.create_task(self._reconciliation_loop())

    async def place_order(self, request: OrderRequest) -> OrderResult:
        """
        Place order with full validation and tracking.

        Flow:
        1. Validate order (risk checks, balance, limits)
        2. Log to database (status: PENDING)
        3. Submit to broker
        4. Update database (status: SUBMITTED)
        5. Add to active orders for monitoring
        6. Return result

        Args:
            request: Order request with all parameters

        Returns:
            OrderResult with order_id, broker_order_id, status

        Raises:
            OrderRejected: If validation fails
            InsufficientBalance: If not enough funds
            OrderSubmissionFailed: If broker API fails
        """
        logger.info(f"Placing order: {request.symbol} {request.side} {request.quantity}")

        # STEP 1: Validate order
        validation = await self.validator.validate_order(request)

        if not validation.is_valid:
            logger.warning(f"Order validation failed: {validation.reason}")

            # Log failed validation to database
            await self.db.create_order(
                request,
                status='REJECTED',
                status_message=f"Validation failed: {validation.reason}",
                validation_result=validation.to_dict()
            )

            raise OrderRejected(validation.reason, validation.failed_check)

        logger.info(f"Order passed all validation checks")

        # STEP 2: Log to database BEFORE submitting to broker
        order_id = await self.db.create_order(
            request,
            status='PENDING',
            validation_result=validation.to_dict()
        )

        logger.info(f"Order logged to database: order_id={order_id}")

        try:
            # STEP 3: Submit to Zerodha
            logger.info(f"Submitting order to Zerodha...")

            broker_response = await self.zerodha.place_order(
                tradingsymbol=request.symbol,
                exchange=request.exchange,
                transaction_type=request.side,
                quantity=request.quantity,
                order_type=request.order_type,
                price=request.price if request.order_type in ['LIMIT', 'SL'] else None,
                trigger_price=request.trigger_price if request.order_type in ['SL', 'SL-M'] else None,
                product=request.product,
                validity=request.validity
            )

            broker_order_id = broker_response['order_id']

            logger.info(f"Order submitted successfully: broker_order_id={broker_order_id}")

            # STEP 4: Update database with broker order ID
            await self.db.update_order(
                order_id,
                broker_order_id=broker_order_id,
                status='SUBMITTED',
                submitted_at=datetime.utcnow()
            )

            # STEP 5: Add to active orders for monitoring
            order = await self.db.get_order(order_id)
            self.active_orders[order_id] = order

            logger.info(f"Order added to active monitoring")

            # STEP 6: Return result
            return OrderResult(
                order_id=order_id,
                broker_order_id=broker_order_id,
                status='SUBMITTED',
                message='Order submitted successfully'
            )

        except Exception as e:
            # Broker API failed - log error to database
            logger.error(f"Failed to submit order to broker: {e}")

            await self.db.update_order(
                order_id,
                status='FAILED',
                error_message=str(e),
                updated_at=datetime.utcnow()
            )

            raise OrderSubmissionFailed(f"Broker API error: {e}")

    async def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Internal order ID

        Returns:
            True if cancelled successfully

        Raises:
            OrderNotFound: If order doesn't exist
            OrderNotCancellable: If order already filled/cancelled
        """
        order = await self.db.get_order(order_id)

        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")

        if order.status not in ['SUBMITTED', 'OPEN']:
            raise OrderNotCancellable(
                f"Cannot cancel order in status {order.status}"
            )

        try:
            # Cancel at broker
            await self.zerodha.cancel_order(
                order_id=order.broker_order_id,
                variety='regular'
            )

            # Update database
            await self.db.update_order(
                order_id,
                status='CANCELLED',
                updated_at=datetime.utcnow()
            )

            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

            logger.info(f"Order {order_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    async def _monitor_orders(self):
        """
        Background task: Monitor active orders for status updates.
        Runs continuously, checking every 1 second.
        """
        logger.info("Order monitoring started")

        while True:
            try:
                if not self.active_orders:
                    await asyncio.sleep(1)
                    continue

                # Get order updates from Zerodha
                broker_order_ids = [
                    order.broker_order_id
                    for order in self.active_orders.values()
                ]

                updates = await self.zerodha.get_order_updates(broker_order_ids)

                for update in updates:
                    await self._process_order_update(update)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in order monitoring: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_order_update(self, update: Dict):
        """
        Process order status update from broker.

        Updates database and triggers actions based on new status.
        """
        broker_order_id = update['order_id']
        new_status = update['status']

        # Find internal order ID
        order_id = None
        for oid, order in self.active_orders.items():
            if order.broker_order_id == broker_order_id:
                order_id = oid
                break

        if order_id is None:
            logger.warning(f"Received update for unknown order: {broker_order_id}")
            return

        logger.info(f"Order {order_id} status update: {new_status}")

        # Update database
        await self.db.update_order_status(
            order_id=order_id,
            status=new_status,
            filled_quantity=update.get('filled_quantity', 0),
            average_price=update.get('average_price', 0),
            status_message=update.get('status_message', ''),
            updated_at=datetime.utcnow()
        )

        # Handle terminal states
        if new_status == 'FILLED':
            await self._on_order_filled(order_id, update)
            del self.active_orders[order_id]

        elif new_status in ['CANCELLED', 'REJECTED']:
            await self._on_order_terminated(order_id, new_status, update)
            del self.active_orders[order_id]

    async def _on_order_filled(self, order_id: int, fill_data: Dict):
        """
        Handle order fill.

        Actions:
        1. Update position
        2. Log trade with costs
        3. Calculate PnL if closing position
        4. Trigger achievement check
        """
        order = await self.db.get_order(order_id)

        logger.info(f"Order {order_id} filled: {order.quantity} @ ₹{fill_data['average_price']:.2f}")

        # Update position
        await self.positions.update_position(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_data['average_price']
        )

        # Log trade with costs
        await self.db.create_trade(
            order_id=order_id,
            broker_trade_id=fill_data.get('trade_id'),
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side,
            quantity=order.quantity,
            price=fill_data['average_price'],
            brokerage=fill_data.get('brokerage', 0),
            stt=fill_data.get('stt', 0),
            exchange_txn_charge=fill_data.get('exchange_txn_charge', 0),
            gst=fill_data.get('gst', 0),
            stamp_duty=fill_data.get('stamp_duty', 0),
            total_charges=fill_data.get('total_charges', 0)
        )

        # Check if this closed a position
        position = await self.positions.get_position(order.symbol)

        if position and position.quantity == 0:  # Position closed
            pnl = position.realized_pnl

            logger.info(f"Position closed for {order.symbol}: PnL = ₹{pnl:.2f}")

            # Trigger achievement check (frontend)
            # This would be sent via WebSocket to dashboard
            await self.broadcast_event('tradeExecuted', {
                'pnl': float(pnl),
                'symbol': order.symbol,
                'time': datetime.utcnow().isoformat(),
                'exitReason': order.metadata.get('exit_reason', 'target')
            })

    async def _reconciliation_loop(self):
        """
        Background task: Reconcile positions with broker every 30 seconds.
        """
        logger.info("Position reconciliation started")

        while True:
            try:
                await self.reconcile_positions()
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in reconciliation: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def reconcile_positions(self) -> Dict:
        """
        Reconcile internal positions with broker positions.

        Returns dict with reconciliation results:
        {
            'mismatches': [],
            'unknown_positions': [],
            'all_clear': True/False
        }
        """
        logger.info("Starting position reconciliation...")

        # Get broker positions
        broker_positions = await self.zerodha.get_positions()

        # Get internal positions
        internal_positions = await self.positions.get_all_positions()

        mismatches = []
        unknown_positions = []

        # Check all broker positions
        for symbol, broker_pos in broker_positions.items():
            internal_pos = internal_positions.get(symbol)

            if internal_pos is None:
                # We don't have this position
                logger.warning(f"Unknown position detected: {symbol} qty={broker_pos.quantity}")

                unknown_positions.append({
                    'symbol': symbol,
                    'broker_quantity': broker_pos.quantity,
                    'broker_avg_price': broker_pos.average_price
                })

                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    issue_type='UNKNOWN_POSITION',
                    broker_quantity=broker_pos.quantity,
                    metadata={'broker_position': broker_pos.to_dict()}
                )

            elif internal_pos.quantity != broker_pos.quantity:
                # Quantity mismatch
                logger.error(
                    f"Position mismatch for {symbol}: "
                    f"internal={internal_pos.quantity}, broker={broker_pos.quantity}"
                )

                mismatches.append({
                    'symbol': symbol,
                    'internal_quantity': internal_pos.quantity,
                    'broker_quantity': broker_pos.quantity,
                    'difference': broker_pos.quantity - internal_pos.quantity
                })

                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    issue_type='QUANTITY_MISMATCH',
                    internal_quantity=internal_pos.quantity,
                    broker_quantity=broker_pos.quantity
                )

                # CRITICAL: Trust broker, update internal state
                await self.positions.force_update_quantity(
                    symbol=symbol,
                    quantity=broker_pos.quantity,
                    reason='RECONCILIATION_FIX'
                )

        # Check for internal positions not at broker
        for symbol, internal_pos in internal_positions.items():
            if symbol not in broker_positions and internal_pos.quantity != 0:
                logger.error(f"Phantom position detected: {symbol} qty={internal_pos.quantity}")

                mismatches.append({
                    'symbol': symbol,
                    'internal_quantity': internal_pos.quantity,
                    'broker_quantity': 0,
                    'type': 'PHANTOM_POSITION'
                })

                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    issue_type='PHANTOM_POSITION',
                    internal_quantity=internal_pos.quantity,
                    broker_quantity=0
                )

                # Close phantom position
                await self.positions.force_close_position(
                    symbol=symbol,
                    reason='RECONCILIATION_FIX'
                )

        all_clear = len(mismatches) == 0 and len(unknown_positions) == 0

        if all_clear:
            logger.info("✓ Reconciliation complete: All positions match")
        else:
            logger.warning(
                f"⚠ Reconciliation issues: "
                f"{len(mismatches)} mismatches, {len(unknown_positions)} unknown"
            )

        return {
            'all_clear': all_clear,
            'mismatches': mismatches,
            'unknown_positions': unknown_positions,
            'timestamp': datetime.utcnow().isoformat()
        }


class OrderRejected(Exception):
    """Order rejected during validation."""
    def __init__(self, reason: str, failed_check: str = None):
        self.reason = reason
        self.failed_check = failed_check
        super().__init__(reason)


class OrderSubmissionFailed(Exception):
    """Order submission to broker failed."""
    pass


class OrderNotFound(Exception):
    """Order not found in database."""
    pass


class OrderNotCancellable(Exception):
    """Order cannot be cancelled (already filled/cancelled)."""
    pass
```

---

## Testing Strategy

### Unit Tests

```python
# File: tests/oms/test_order_manager.py

import pytest
from unittest.mock import AsyncMock, Mock, patch
from backend.oms.order_manager import OrderManager, OrderRejected
from backend.models import OrderRequest

@pytest.fixture
async def order_manager():
    """Create OrderManager with mocked dependencies."""
    db = AsyncMock()
    zerodha = AsyncMock()
    validator = AsyncMock()
    position_manager = AsyncMock()

    om = OrderManager(db, zerodha, validator, position_manager)

    # Stop background tasks for testing
    for task in asyncio.all_tasks():
        if 'monitor' in str(task) or 'reconciliation' in str(task):
            task.cancel()

    return om


@pytest.mark.asyncio
async def test_place_order_success(order_manager):
    """Test successful order placement flow."""
    # Setup
    order_request = OrderRequest(
        symbol='RELIANCE',
        exchange='NSE',
        side='BUY',
        quantity=10,
        order_type='LIMIT',
        price=2450.50,
        stop_loss=2430.00,
        take_profit=2491.00,
        product='MIS',
        validity='DAY',
        strategy_id=1
    )

    # Mock validation success
    order_manager.validator.validate_order.return_value = Mock(is_valid=True)

    # Mock database create_order
    order_manager.db.create_order.return_value = 123  # order_id

    # Mock Zerodha API response
    order_manager.zerodha.place_order.return_value = {'order_id': 'Z123456'}

    # Execute
    result = await order_manager.place_order(order_request)

    # Assert
    assert result.order_id == 123
    assert result.broker_order_id == 'Z123456'
    assert result.status == 'SUBMITTED'

    # Verify database was updated
    assert order_manager.db.create_order.call_count == 1
    assert order_manager.db.update_order.call_count == 1


@pytest.mark.asyncio
async def test_place_order_validation_failure(order_manager):
    """Test order rejected due to validation failure."""
    order_request = OrderRequest(
        symbol='RELIANCE',
        exchange='NSE',
        side='BUY',
        quantity=1000,  # Too large
        order_type='MARKET',
        product='MIS',
        validity='DAY',
        strategy_id=1
    )

    # Mock validation failure
    order_manager.validator.validate_order.return_value = Mock(
        is_valid=False,
        reason='Quantity exceeds max position size',
        failed_check='Position Limit'
    )

    # Execute & Assert
    with pytest.raises(OrderRejected) as exc_info:
        await order_manager.place_order(order_request)

    assert 'Quantity exceeds max position size' in str(exc_info.value)

    # Verify order was NOT sent to broker
    order_manager.zerodha.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_reconciliation_quantity_mismatch(order_manager):
    """Test reconciliation detects and fixes quantity mismatch."""
    # Setup internal position
    order_manager.positions.get_all_positions.return_value = {
        'RELIANCE': Mock(symbol='RELIANCE', quantity=10, average_price=2450.00)
    }

    # Setup broker position (different quantity)
    order_manager.zerodha.get_positions.return_value = {
        'RELIANCE': Mock(symbol='RELIANCE', quantity=8, average_price=2450.00)
    }

    # Execute
    result = await order_manager.reconcile_positions()

    # Assert
    assert result['all_clear'] is False
    assert len(result['mismatches']) == 1
    assert result['mismatches'][0]['symbol'] == 'RELIANCE'
    assert result['mismatches'][0]['internal_quantity'] == 10
    assert result['mismatches'][0]['broker_quantity'] == 8

    # Verify position was corrected
    order_manager.positions.force_update_quantity.assert_called_once_with(
        symbol='RELIANCE',
        quantity=8,
        reason='RECONCILIATION_FIX'
    )

    # Verify issue was logged
    order_manager.db.log_reconciliation_issue.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_order_success(order_manager):
    """Test successful order cancellation."""
    # Setup
    order = Mock(
        id=123,
        broker_order_id='Z123456',
        status='OPEN'
    )
    order_manager.db.get_order.return_value = order
    order_manager.zerodha.cancel_order.return_value = {'status': 'success'}

    # Execute
    result = await order_manager.cancel_order(123)

    # Assert
    assert result is True
    order_manager.zerodha.cancel_order.assert_called_once_with(
        order_id='Z123456',
        variety='regular'
    )
    order_manager.db.update_order.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_order_already_filled(order_manager):
    """Test cancellation fails for filled order."""
    # Setup
    order = Mock(
        id=123,
        broker_order_id='Z123456',
        status='FILLED'
    )
    order_manager.db.get_order.return_value = order

    # Execute & Assert
    with pytest.raises(OrderNotCancellable):
        await order_manager.cancel_order(123)

    # Verify broker API was NOT called
    order_manager.zerodha.cancel_order.assert_not_called()
```

### Integration Tests

```python
# File: tests/oms/test_oms_integration.py

import pytest
from backend.oms.order_manager import OrderManager
from backend.database import Database
from tests.mocks.zerodha_mock import MockZerodhaClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_order_lifecycle():
    """
    Test complete order lifecycle from placement to fill.
    Uses real database and mock Zerodha API.
    """
    # Setup
    db = Database('postgresql://localhost/xcoin_test')
    zerodha = MockZerodhaClient()  # Mock that simulates fills
    validator = PreTradeValidator(config, account_manager)
    position_manager = PositionManager(db)

    om = OrderManager(db, zerodha, validator, position_manager)

    # Place order
    order_request = OrderRequest(
        symbol='RELIANCE',
        exchange='NSE',
        side='BUY',
        quantity=10,
        order_type='LIMIT',
        price=2450.50,
        stop_loss=2430.00,
        take_profit=2491.00,
        product='MIS',
        validity='DAY',
        strategy_id=1
    )

    result = await om.place_order(order_request)

    assert result.status == 'SUBMITTED'
    order_id = result.order_id

    # Simulate fill from broker
    await zerodha.simulate_fill(
        order_id=result.broker_order_id,
        quantity=10,
        price=2450.50
    )

    # Wait for order monitoring to process update
    await asyncio.sleep(2)

    # Check order status in database
    order = await db.get_order(order_id)
    assert order.status == 'FILLED'
    assert order.filled_quantity == 10
    assert order.average_price == 2450.50

    # Check position was created
    position = await position_manager.get_position('RELIANCE')
    assert position.quantity == 10
    assert position.average_price == 2450.50

    # Check trade was logged
    trades = await db.get_trades_for_order(order_id)
    assert len(trades) == 1
    assert trades[0].quantity == 10
    assert trades[0].price == 2450.50
```

---

## Deployment Checklist

Before deploying OMS to production:

- [ ] All unit tests passing (90%+ coverage)
- [ ] All integration tests passing
- [ ] Load testing completed (1000 orders/min)
- [ ] Reconciliation tested with mismatches
- [ ] Order rejection scenarios tested
- [ ] Database indexes created
- [ ] Monitoring dashboard operational
- [ ] Alert system configured
- [ ] Documentation complete
- [ ] Code review by 2+ team members
- [ ] Security audit passed

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Order Success Rate:** % of orders successfully submitted
   - Target: >99.5%
   - Alert if <98%

2. **Order Fill Rate:** % of submitted orders that fill
   - Target: >95% (depends on strategy)
   - Alert if sudden drop >10%

3. **Reconciliation Issues:** # of mismatches per day
   - Target: 0
   - Alert on ANY mismatch

4. **Order Latency:** Time from place_order() call to broker submission
   - Target: <100ms (95th percentile)
   - Alert if >500ms

5. **Position Accuracy:** % of reconciliations with all_clear=True
   - Target: 100%
   - Alert on any failure

### Alert Configuration

```python
# File: backend/oms/alerts.py

class OMSAlertsConfig:
    """Alert thresholds for OMS monitoring."""

    # Order success rate alerts
    ORDER_SUCCESS_RATE_WARNING = 0.98   # 98%
    ORDER_SUCCESS_RATE_CRITICAL = 0.95  # 95%

    # Reconciliation alerts
    RECONCILIATION_MISMATCH_WARNING = 1    # Any mismatch
    RECONCILIATION_MISMATCH_CRITICAL = 5   # 5+ mismatches

    # Latency alerts
    ORDER_LATENCY_WARNING_MS = 500
    ORDER_LATENCY_CRITICAL_MS = 1000

    # Position accuracy
    POSITION_ACCURACY_CRITICAL = 0.99  # <99% accuracy
```

---

## Next Steps

Once OMS is complete (Week 4), proceed to:

1. **Risk Management System** (Week 5-6)
   - Pre-trade validators use OMS
   - Real-time monitoring uses OMS position data
   - Kill switch uses OMS.close_all_positions()

2. **Backtesting Engine** (Week 7-8)
   - Use OMS interfaces for consistent behavior
   - Backtest engine implements same OMS interface
   - Easy swap between paper/live trading

3. **Dashboard Integration** (Week 9)
   - Real-time order updates via WebSocket
   - Position display from OMS
   - Order history from OMS database

---

## Conclusion

The Order Management System is the **foundation** of your trading platform. Every other system depends on it:

- Risk management reads OMS positions
- Strategies place orders through OMS
- Backtesting uses OMS interfaces
- Dashboard displays OMS data
- Alerts triggered by OMS events

**Take your time building this right. Rushing OMS = financial loss.**

Estimated timeline:
- Week 1: Core OMS + database (20 hours)
- Week 2: Order lifecycle + monitoring (20 hours)
- Week 3: Position management + reconciliation (10 hours)
- Week 4: Testing + integration (10 hours)

**Total: 60 hours = 1.5 months part-time OR 1.5 weeks full-time**

---

*Document Version: 1.0*
*Last Updated: October 25, 2025*
*Next Review: After Week 2 completion*
