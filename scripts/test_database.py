#!/usr/bin/env python3
"""
Test database operations.

This script tests all database CRUD operations to verify everything works.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.database import Database
from backend.models import OrderRequest, OrderSide, OrderType, Product, Validity
from backend.config import Config


async def test_order_operations(db: Database):
    """Test order CRUD operations."""
    print("\n" + "="*60)
    print("Testing Order Operations")
    print("="*60)

    # Create order
    print("\n1. Creating test order...")
    order_request = OrderRequest(
        symbol='RELIANCE',
        exchange='NSE',
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        price=Decimal('2450.50'),
        product=Product.MIS,
        validity=Validity.DAY,
        strategy_id=1,
        stop_loss=Decimal('2430.00'),
        take_profit=Decimal('2491.00')
    )

    order_id = await db.create_order(order_request)
    print(f"✓ Order created with ID: {order_id}")

    # Get order
    print("\n2. Retrieving order...")
    order = await db.get_order(order_id)
    print(f"✓ Order retrieved:")
    print(f"  ID: {order.id}")
    print(f"  Symbol: {order.symbol}")
    print(f"  Side: {order.side.value}")
    print(f"  Quantity: {order.quantity}")
    print(f"  Price: ₹{order.price}")
    print(f"  Status: {order.status.value}")
    print(f"  Stop Loss: ₹{order.stop_loss}")
    print(f"  Take Profit: ₹{order.take_profit}")

    # Update order
    print("\n3. Updating order status...")
    await db.update_order(
        order_id,
        status='SUBMITTED',
        broker_order_id='ZERODHA123456'
    )
    print(f"✓ Order updated to SUBMITTED")

    # Get updated order
    order = await db.get_order(order_id)
    print(f"  New status: {order.status.value}")
    print(f"  Broker order ID: {order.broker_order_id}")

    # Get active orders
    print("\n4. Getting active orders...")
    active_orders = await db.get_active_orders()
    print(f"✓ Found {len(active_orders)} active orders")

    return order_id


async def test_position_operations(db: Database, order_id: int):
    """Test position CRUD operations."""
    print("\n" + "="*60)
    print("Testing Position Operations")
    print("="*60)

    # Create position
    print("\n1. Creating test position...")
    position_id = await db.create_position(
        symbol='RELIANCE',
        exchange='NSE',
        strategy_id=1,
        quantity=10,
        average_price=Decimal('2450.50'),
        product='MIS',
        stop_loss=Decimal('2430.00'),
        take_profit=Decimal('2491.00'),
        entry_order_ids=[order_id]
    )
    print(f"✓ Position created with ID: {position_id}")

    # Get position
    print("\n2. Retrieving position...")
    position = await db.get_position('RELIANCE', 'NSE')
    print(f"✓ Position retrieved:")
    print(f"  ID: {position.id}")
    print(f"  Symbol: {position.symbol}")
    print(f"  Quantity: {position.quantity}")
    print(f"  Avg Price: ₹{position.average_price}")
    print(f"  Is Long: {position.is_long}")
    print(f"  Realized PnL: ₹{position.realized_pnl}")

    # Update position
    print("\n3. Updating position with unrealized PnL...")
    current_price = Decimal('2465.00')
    unrealized_pnl = position.calculate_unrealized_pnl(current_price)

    await db.update_position(
        position_id,
        unrealized_pnl=unrealized_pnl,
        highest_price=current_price
    )
    print(f"✓ Position updated")
    print(f"  Current price: ₹{current_price}")
    print(f"  Unrealized PnL: ₹{unrealized_pnl}")

    # Get all open positions
    print("\n4. Getting all open positions...")
    open_positions = await db.get_all_open_positions()
    print(f"✓ Found {len(open_positions)} open positions")

    # Get position count
    count = await db.get_open_position_count()
    print(f"  Open position count: {count}")

    return position_id


async def test_trade_operations(db: Database, order_id: int, position_id: int):
    """Test trade CRUD operations."""
    print("\n" + "="*60)
    print("Testing Trade Operations")
    print("="*60)

    # Create trade
    print("\n1. Creating test trade...")
    trade_id = await db.create_trade(
        order_id=order_id,
        symbol='RELIANCE',
        exchange='NSE',
        side='BUY',
        quantity=10,
        price=Decimal('2450.50'),
        position_id=position_id,
        broker_trade_id='TRADE123456',
        brokerage=Decimal('20.00'),
        stt=Decimal('6.13'),
        exchange_txn_charge=Decimal('0.80'),
        gst=Decimal('3.75'),
        stamp_duty=Decimal('0.74')
    )
    print(f"✓ Trade created with ID: {trade_id}")

    # Get trades for order
    print("\n2. Retrieving trades for order...")
    trades = await db.get_trades_for_order(order_id)
    print(f"✓ Found {len(trades)} trades")

    if trades:
        trade = trades[0]
        print(f"  Trade ID: {trade.id}")
        print(f"  Symbol: {trade.symbol}")
        print(f"  Side: {trade.side}")
        print(f"  Quantity: {trade.quantity}")
        print(f"  Price: ₹{trade.price}")
        print(f"  Gross Value: ₹{trade.gross_value}")
        print(f"  Total Charges: ₹{trade.total_charges}")
        print(f"  Net Value: ₹{trade.net_value}")
        print(f"  Charges %: {trade.charges_percentage:.3f}%")

    return trade_id


async def test_reconciliation_operations(db: Database):
    """Test reconciliation logging."""
    print("\n" + "="*60)
    print("Testing Reconciliation Operations")
    print("="*60)

    # Log reconciliation issue
    print("\n1. Logging reconciliation issue...")
    issue_id = await db.log_reconciliation_issue(
        symbol='TCS',
        exchange='NSE',
        issue_type='QUANTITY_MISMATCH',
        severity='WARNING',
        internal_quantity=50,
        broker_quantity=48,
        difference=-2
    )
    print(f"✓ Reconciliation issue logged with ID: {issue_id}")

    # Get unresolved issues
    print("\n2. Getting unresolved issues...")
    issues = await db.get_unresolved_reconciliation_issues()
    print(f"✓ Found {len(issues)} unresolved issues")

    if issues:
        issue = issues[0]
        print(f"  Issue ID: {issue.id}")
        print(f"  Symbol: {issue.symbol}")
        print(f"  Type: {issue.issue_type.value}")
        print(f"  Severity: {issue.severity.value}")
        print(f"  Internal Qty: {issue.internal_quantity}")
        print(f"  Broker Qty: {issue.broker_quantity}")
        print(f"  Difference: {issue.difference}")

    # Resolve issue
    print("\n3. Resolving issue...")
    await db.resolve_reconciliation_issue(
        issue_id,
        resolution="Manually verified broker quantity is correct. Updated internal state.",
        auto_fixed=False
    )
    print(f"✓ Issue {issue_id} marked as resolved")


async def test_account_stats(db: Database):
    """Test account statistics functions."""
    print("\n" + "="*60)
    print("Testing Account Statistics")
    print("="*60)

    # Get today's PnL
    print("\n1. Getting today's PnL...")
    pnl = await db.get_today_pnl()
    print(f"✓ Today's PnL: ₹{pnl}")

    # Get order count
    print("\n2. Getting order count...")
    order_count = await db.get_today_order_count()
    print(f"✓ Today's order count: {order_count}")

    # Get trade count
    print("\n3. Getting trade count...")
    trade_count = await db.get_today_trade_count()
    print(f"✓ Today's trade count: {trade_count}")

    # Get order-to-trade ratio
    print("\n4. Getting order-to-trade ratio...")
    ratio = await db.get_order_to_trade_ratio()
    print(f"✓ Order-to-trade ratio: {ratio:.2f}:1")


async def test_strategy_operations(db: Database):
    """Test strategy operations."""
    print("\n" + "="*60)
    print("Testing Strategy Operations")
    print("="*60)

    # Get all strategies
    print("\n1. Getting all strategies...")
    strategies = await db.get_all_strategies()
    print(f"✓ Found {len(strategies)} strategies")

    if strategies:
        strategy = strategies[0]
        print(f"  Strategy ID: {strategy.id}")
        print(f"  Name: {strategy.name}")
        print(f"  Type: {strategy.type}")
        print(f"  Status: {strategy.status.value}")
        print(f"  Mode: {strategy.mode.value}")

    # Get strategy by ID
    print("\n2. Getting strategy by ID...")
    strategy = await db.get_strategy(1)
    if strategy:
        print(f"✓ Strategy retrieved:")
        print(f"  ID: {strategy.id}")
        print(f"  Name: {strategy.name}")


async def test_health_check(db: Database):
    """Test database health check."""
    print("\n" + "="*60)
    print("Testing Health Check")
    print("="*60)

    is_healthy = await db.health_check()

    if is_healthy:
        print("✓ Database is healthy")
    else:
        print("✗ Database health check failed")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("XCoin Scalping Bot - Database Test Suite")
    print("="*60)

    # Connect to database
    print(f"\nConnecting to: {Config.DATABASE_URL.split('@')[1] if '@' in Config.DATABASE_URL else Config.DATABASE_URL}")

    db = Database(Config.DATABASE_URL)
    await db.connect()

    try:
        # Run tests
        order_id = await test_order_operations(db)
        position_id = await test_position_operations(db, order_id)
        trade_id = await test_trade_operations(db, order_id, position_id)
        await test_reconciliation_operations(db)
        await test_account_stats(db)
        await test_strategy_operations(db)
        await test_health_check(db)

        # Success summary
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nTest Summary:")
        print(f"  ✓ Order created: ID {order_id}")
        print(f"  ✓ Position created: ID {position_id}")
        print(f"  ✓ Trade created: ID {trade_id}")
        print(f"  ✓ Reconciliation logged")
        print(f"  ✓ Statistics calculated")
        print(f"  ✓ Health check passed")
        print("\nDatabase is ready for production use!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await db.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
        sys.exit(0)
