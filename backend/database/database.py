"""
Database connection and query layer for XCoin Scalping Bot.

This module provides:
- PostgreSQL connection pooling
- CRUD operations for all models
- Transaction management
- Query helpers
"""

import asyncio
import asyncpg
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from contextlib import asynccontextmanager

from backend.models import (
    Order, OrderRequest, OrderStatus,
    Position, Trade, Strategy, ReconciliationIssue
)
from backend.models.order import order_from_db_row
from backend.models.position import position_from_db_row
from backend.models.trade import trade_from_db_row
from backend.models.strategy import strategy_from_db_row
from backend.models.reconciliation import reconciliation_issue_from_db_row

logger = logging.getLogger(__name__)


class Database:
    """
    Database connection and query manager.

    Handles all database operations with connection pooling,
    transaction management, and error handling.
    """

    def __init__(self, connection_string: str, min_connections: int = 5, max_connections: int = 20):
        """
        Initialize database manager.

        Args:
            connection_string: PostgreSQL connection string
                e.g., "postgresql://user:password@localhost/xcoin"
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """
        Create connection pool.

        Call this once at application startup.
        """
        logger.info(f"Connecting to database...")

        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=60,
                server_settings={
                    'application_name': 'xcoin_scalping_bot'
                }
            )

            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"Connected to PostgreSQL: {version}")

            logger.info(
                f"Connection pool created: "
                f"{self.min_connections}-{self.max_connections} connections"
            )

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """
        Close connection pool.

        Call this at application shutdown.
        """
        if self.pool:
            logger.info("Closing database connection pool...")
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            async with db.transaction() as conn:
                await conn.execute("INSERT ...")
                await conn.execute("UPDATE ...")
                # Auto-commits on success, rolls back on exception
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================

    async def create_order(
        self,
        order_request: OrderRequest,
        status: str = 'PENDING',
        validation_result: Optional[Dict] = None,
        **kwargs
    ) -> int:
        """
        Create a new order in the database.

        Args:
            order_request: Order request object
            status: Initial status (default: PENDING)
            validation_result: Results of pre-trade validation
            **kwargs: Additional fields (status_message, broker_order_id, etc.)

        Returns:
            Order ID (integer)
        """
        query = """
            INSERT INTO orders (
                strategy_id, symbol, exchange, side, quantity,
                order_type, price, trigger_price, product, validity,
                stop_loss, take_profit, risk_amount, risk_reward_ratio,
                status, status_message, validation_result, validation_warnings,
                metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16, $17, $18,
                $19, $20
            )
            RETURNING id
        """

        # Calculate risk metrics
        entry_price = order_request.price if order_request.price else None
        risk_amount = None
        risk_reward_ratio = None

        if entry_price and order_request.stop_loss:
            risk_per_share = abs(entry_price - order_request.stop_loss)
            risk_amount = risk_per_share * order_request.quantity

            if order_request.take_profit:
                reward_per_share = abs(order_request.take_profit - entry_price)
                if risk_per_share > 0:
                    risk_reward_ratio = reward_per_share / risk_per_share

        async with self.pool.acquire() as conn:
            order_id = await conn.fetchval(
                query,
                order_request.strategy_id,
                order_request.symbol,
                order_request.exchange,
                order_request.side.value,
                order_request.quantity,
                order_request.order_type.value,
                order_request.price,
                order_request.trigger_price,
                order_request.product.value,
                order_request.validity.value,
                order_request.stop_loss,
                order_request.take_profit,
                risk_amount,
                risk_reward_ratio,
                status,
                kwargs.get('status_message'),
                validation_result,
                kwargs.get('validation_warnings'),
                order_request.metadata,
                datetime.utcnow()
            )

        logger.info(f"Order created: id={order_id}, {order_request.symbol} {order_request.side.value} {order_request.quantity}")

        return order_id

    async def get_order(self, order_id: int) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order object or None if not found
        """
        query = "SELECT * FROM orders WHERE id = $1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, order_id)

        if row:
            return order_from_db_row(dict(row))

        return None

    async def get_order_by_broker_id(self, broker_order_id: str) -> Optional[Order]:
        """
        Get order by broker order ID.

        Args:
            broker_order_id: Broker's order ID (e.g., Zerodha order ID)

        Returns:
            Order object or None if not found
        """
        query = "SELECT * FROM orders WHERE broker_order_id = $1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, broker_order_id)

        if row:
            return order_from_db_row(dict(row))

        return None

    async def update_order(self, order_id: int, **updates) -> bool:
        """
        Update order fields.

        Args:
            order_id: Order ID
            **updates: Fields to update (e.g., status='FILLED', average_price=2450.50)

        Returns:
            True if updated, False if order not found
        """
        if not updates:
            return False

        # Add updated_at
        updates['updated_at'] = datetime.utcnow()

        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        param_num = 1

        for key, value in updates.items():
            set_clauses.append(f"{key} = ${param_num}")
            values.append(value)
            param_num += 1

        # Add order_id as last parameter
        values.append(order_id)

        query = f"""
            UPDATE orders
            SET {', '.join(set_clauses)}
            WHERE id = ${param_num}
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *values)

        # Check if row was updated
        updated = result.split()[-1] == '1'

        if updated:
            logger.info(f"Order {order_id} updated: {list(updates.keys())}")
        else:
            logger.warning(f"Order {order_id} not found for update")

        return updated

    async def get_active_orders(self) -> List[Order]:
        """
        Get all active orders (PENDING, SUBMITTED, OPEN).

        Returns:
            List of Order objects
        """
        query = """
            SELECT * FROM orders
            WHERE status IN ('PENDING', 'SUBMITTED', 'OPEN')
            ORDER BY created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        orders = [order_from_db_row(dict(row)) for row in rows]

        logger.debug(f"Retrieved {len(orders)} active orders")

        return orders

    async def get_orders_by_strategy(self, strategy_id: int, limit: int = 100) -> List[Order]:
        """
        Get orders for a specific strategy.

        Args:
            strategy_id: Strategy ID
            limit: Maximum orders to return

        Returns:
            List of Order objects
        """
        query = """
            SELECT * FROM orders
            WHERE strategy_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, strategy_id, limit)

        orders = [order_from_db_row(dict(row)) for row in rows]

        return orders

    async def get_today_orders(self) -> List[Order]:
        """
        Get all orders placed today.

        Returns:
            List of Order objects
        """
        query = """
            SELECT * FROM v_today_orders
            ORDER BY created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        orders = [order_from_db_row(dict(row)) for row in rows]

        return orders

    # ========================================================================
    # POSITION OPERATIONS
    # ========================================================================

    async def create_position(
        self,
        symbol: str,
        exchange: str,
        strategy_id: int,
        quantity: int,
        average_price: Decimal,
        product: str,
        **kwargs
    ) -> int:
        """
        Create a new position.

        Args:
            symbol: Symbol (e.g., "RELIANCE")
            exchange: Exchange (e.g., "NSE")
            strategy_id: Strategy ID
            quantity: Quantity (positive = long, negative = short)
            average_price: Average entry price
            product: Product type (MIS or CNC)
            **kwargs: Optional fields (stop_loss, take_profit, etc.)

        Returns:
            Position ID
        """
        query = """
            INSERT INTO positions (
                symbol, exchange, strategy_id, quantity, average_price, product,
                stop_loss, take_profit, entry_order_ids, metadata, opened_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            position_id = await conn.fetchval(
                query,
                symbol,
                exchange,
                strategy_id,
                quantity,
                average_price,
                product,
                kwargs.get('stop_loss'),
                kwargs.get('take_profit'),
                kwargs.get('entry_order_ids', []),
                kwargs.get('metadata', {}),
                datetime.utcnow()
            )

        logger.info(f"Position created: id={position_id}, {symbol} qty={quantity}")

        return position_id

    async def get_position(self, symbol: str, exchange: str = 'NSE', strategy_id: int = None) -> Optional[Position]:
        """
        Get position by symbol.

        Args:
            symbol: Symbol
            exchange: Exchange (default: NSE)
            strategy_id: Strategy ID (optional)

        Returns:
            Position object or None if not found
        """
        if strategy_id:
            query = """
                SELECT * FROM positions
                WHERE symbol = $1 AND exchange = $2 AND strategy_id = $3
                AND closed_at IS NULL
                LIMIT 1
            """
            params = [symbol, exchange, strategy_id]
        else:
            query = """
                SELECT * FROM positions
                WHERE symbol = $1 AND exchange = $2
                AND closed_at IS NULL
                LIMIT 1
            """
            params = [symbol, exchange]

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if row:
            return position_from_db_row(dict(row))

        return None

    async def get_position_by_id(self, position_id: int) -> Optional[Position]:
        """
        Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position object or None if not found
        """
        query = "SELECT * FROM positions WHERE id = $1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, position_id)

        if row:
            return position_from_db_row(dict(row))

        return None

    async def update_position(self, position_id: int, **updates) -> bool:
        """
        Update position fields.

        Args:
            position_id: Position ID
            **updates: Fields to update

        Returns:
            True if updated, False if not found
        """
        if not updates:
            return False

        # Add updated_at
        updates['updated_at'] = datetime.utcnow()

        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        param_num = 1

        for key, value in updates.items():
            set_clauses.append(f"{key} = ${param_num}")
            values.append(value)
            param_num += 1

        values.append(position_id)

        query = f"""
            UPDATE positions
            SET {', '.join(set_clauses)}
            WHERE id = ${param_num}
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *values)

        updated = result.split()[-1] == '1'

        if updated:
            logger.debug(f"Position {position_id} updated: {list(updates.keys())}")

        return updated

    async def get_all_open_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of Position objects
        """
        query = """
            SELECT * FROM positions
            WHERE closed_at IS NULL
            ORDER BY opened_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        positions = [position_from_db_row(dict(row)) for row in rows]

        logger.debug(f"Retrieved {len(positions)} open positions")

        return positions

    async def get_open_position_count(self) -> int:
        """
        Get count of open positions.

        Returns:
            Number of open positions
        """
        query = """
            SELECT COUNT(*) FROM positions
            WHERE closed_at IS NULL
        """

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query)

        return count

    async def close_position(self, position_id: int, realized_pnl: Decimal, exit_order_ids: List[int] = None):
        """
        Close a position.

        Args:
            position_id: Position ID
            realized_pnl: Final realized PnL
            exit_order_ids: IDs of exit orders
        """
        await self.update_position(
            position_id,
            quantity=0,
            realized_pnl=realized_pnl,
            unrealized_pnl=Decimal('0'),
            closed_at=datetime.utcnow(),
            exit_order_ids=exit_order_ids or []
        )

        logger.info(f"Position {position_id} closed: PnL=₹{realized_pnl}")

    # ========================================================================
    # TRADE OPERATIONS
    # ========================================================================

    async def create_trade(
        self,
        order_id: int,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        price: Decimal,
        **kwargs
    ) -> int:
        """
        Create a trade (fill) record.

        Args:
            order_id: Order ID
            symbol: Symbol
            exchange: Exchange
            side: BUY or SELL
            quantity: Filled quantity
            price: Fill price
            **kwargs: Optional fields (brokerage, stt, gst, etc.)

        Returns:
            Trade ID
        """
        query = """
            INSERT INTO trades (
                order_id, position_id, broker_trade_id,
                symbol, exchange, side, quantity, price,
                brokerage, stt, exchange_txn_charge, gst, stamp_duty, sebi_charges,
                executed_at, metadata
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6, $7, $8,
                $9, $10, $11, $12, $13, $14,
                $15, $16
            )
            RETURNING id
        """

        # Trigger will auto-calculate gross_value, total_charges, net_value

        async with self.pool.acquire() as conn:
            trade_id = await conn.fetchval(
                query,
                order_id,
                kwargs.get('position_id'),
                kwargs.get('broker_trade_id'),
                symbol,
                exchange,
                side,
                quantity,
                price,
                kwargs.get('brokerage', Decimal('0')),
                kwargs.get('stt', Decimal('0')),
                kwargs.get('exchange_txn_charge', Decimal('0')),
                kwargs.get('gst', Decimal('0')),
                kwargs.get('stamp_duty', Decimal('0')),
                kwargs.get('sebi_charges', Decimal('0')),
                kwargs.get('executed_at', datetime.utcnow()),
                kwargs.get('metadata', {})
            )

        logger.info(f"Trade created: id={trade_id}, {symbol} {side} {quantity} @ ₹{price}")

        return trade_id

    async def get_trades_for_order(self, order_id: int) -> List[Trade]:
        """
        Get all trades for an order.

        Args:
            order_id: Order ID

        Returns:
            List of Trade objects
        """
        query = """
            SELECT * FROM trades
            WHERE order_id = $1
            ORDER BY executed_at ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, order_id)

        trades = [trade_from_db_row(dict(row)) for row in rows]

        return trades

    async def get_today_trades(self) -> List[Trade]:
        """
        Get all trades executed today.

        Returns:
            List of Trade objects
        """
        query = """
            SELECT * FROM trades
            WHERE DATE(executed_at) = CURRENT_DATE
            ORDER BY executed_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        trades = [trade_from_db_row(dict(row)) for row in rows]

        return trades

    # ========================================================================
    # RECONCILIATION OPERATIONS
    # ========================================================================

    async def log_reconciliation_issue(
        self,
        symbol: str,
        exchange: str,
        issue_type: str,
        severity: str = 'WARNING',
        **kwargs
    ) -> int:
        """
        Log a position reconciliation issue.

        Args:
            symbol: Symbol
            exchange: Exchange
            issue_type: Type of issue (UNKNOWN_POSITION, QUANTITY_MISMATCH, etc.)
            severity: Severity (INFO, WARNING, CRITICAL)
            **kwargs: Additional fields (internal_quantity, broker_quantity, etc.)

        Returns:
            Reconciliation issue ID
        """
        query = """
            INSERT INTO reconciliation_log (
                symbol, exchange, issue_type, severity,
                internal_quantity, broker_quantity, difference,
                internal_avg_price, broker_avg_price,
                detected_at, metadata
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7,
                $8, $9,
                $10, $11
            )
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            issue_id = await conn.fetchval(
                query,
                symbol,
                exchange,
                issue_type,
                severity,
                kwargs.get('internal_quantity'),
                kwargs.get('broker_quantity'),
                kwargs.get('difference'),
                kwargs.get('internal_avg_price'),
                kwargs.get('broker_avg_price'),
                datetime.utcnow(),
                kwargs.get('metadata', {})
            )

        logger.warning(
            f"Reconciliation issue logged: {symbol} - {issue_type} ({severity})"
        )

        return issue_id

    async def get_unresolved_reconciliation_issues(self) -> List[ReconciliationIssue]:
        """
        Get all unresolved reconciliation issues.

        Returns:
            List of ReconciliationIssue objects
        """
        query = """
            SELECT * FROM v_reconciliation_issues
            ORDER BY
                CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'WARNING' THEN 2
                    WHEN 'INFO' THEN 3
                END,
                detected_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        issues = [reconciliation_issue_from_db_row(dict(row)) for row in rows]

        return issues

    async def resolve_reconciliation_issue(
        self,
        issue_id: int,
        resolution: str,
        auto_fixed: bool = False
    ):
        """
        Mark reconciliation issue as resolved.

        Args:
            issue_id: Issue ID
            resolution: Resolution description
            auto_fixed: Whether it was auto-fixed by system
        """
        query = """
            UPDATE reconciliation_log
            SET
                resolved = TRUE,
                resolution = $2,
                auto_fixed = $3,
                resolved_at = $4
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, issue_id, resolution, auto_fixed, datetime.utcnow())

        logger.info(f"Reconciliation issue {issue_id} resolved: {resolution}")

    # ========================================================================
    # ACCOUNT & STATS OPERATIONS
    # ========================================================================

    async def get_today_pnl(self) -> Decimal:
        """
        Get today's net PnL.

        Returns:
            Net PnL for today
        """
        query = "SELECT get_today_pnl()"

        async with self.pool.acquire() as conn:
            pnl = await conn.fetchval(query)

        return Decimal(str(pnl)) if pnl else Decimal('0')

    async def get_today_order_count(self) -> int:
        """
        Get count of orders placed today.

        Returns:
            Number of orders today
        """
        query = """
            SELECT COUNT(*) FROM orders
            WHERE DATE(created_at) = CURRENT_DATE
        """

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query)

        return count

    async def get_today_trade_count(self) -> int:
        """
        Get count of trades executed today.

        Returns:
            Number of trades today
        """
        query = """
            SELECT COUNT(*) FROM trades
            WHERE DATE(executed_at) = CURRENT_DATE
        """

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query)

        return count

    async def get_order_to_trade_ratio(self) -> Decimal:
        """
        Get today's order-to-trade ratio.

        Returns:
            Order-to-trade ratio
        """
        query = "SELECT get_order_to_trade_ratio()"

        async with self.pool.acquire() as conn:
            ratio = await conn.fetchval(query)

        return Decimal(str(ratio)) if ratio else Decimal('0')

    async def update_daily_stats(self, date: date = None):
        """
        Update daily statistics.

        Args:
            date: Date to update (default: today)
        """
        if date is None:
            date = datetime.utcnow().date()

        # This would calculate and update all daily metrics
        # For now, placeholder
        query = """
            INSERT INTO daily_stats (date, created_at)
            VALUES ($1, $2)
            ON CONFLICT (date) DO UPDATE
            SET updated_at = $2
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, date, datetime.utcnow())

        logger.debug(f"Daily stats updated for {date}")

    # ========================================================================
    # STRATEGY OPERATIONS
    # ========================================================================

    async def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy object or None if not found
        """
        query = "SELECT * FROM strategies WHERE id = $1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, strategy_id)

        if row:
            return strategy_from_db_row(dict(row))

        return None

    async def get_all_strategies(self) -> List[Strategy]:
        """
        Get all strategies.

        Returns:
            List of Strategy objects
        """
        query = "SELECT * FROM strategies ORDER BY created_at DESC"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        strategies = [strategy_from_db_row(dict(row)) for row in rows]

        return strategies

    async def get_active_strategies(self) -> List[Strategy]:
        """
        Get all active strategies.

        Returns:
            List of active Strategy objects
        """
        query = """
            SELECT * FROM strategies
            WHERE status = 'ACTIVE'
            ORDER BY created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        strategies = [strategy_from_db_row(dict(row)) for row in rows]

        return strategies

    # ========================================================================
    # KILL SWITCH OPERATIONS
    # ========================================================================

    async def is_kill_switch_active(self) -> bool:
        """
        Check if kill switch is active for today.

        Returns:
            True if kill switch is active, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM kill_switch_events
                WHERE DATE(triggered_at) = CURRENT_DATE
                AND deactivated_at IS NULL
            )
        """

        async with self.pool.acquire() as conn:
            active = await conn.fetchval(query)

        return bool(active)

    async def trigger_kill_switch(self, reason: str, triggered_by: str = 'system'):
        """
        Trigger kill switch (emergency stop trading).

        Args:
            reason: Reason for triggering
            triggered_by: Who/what triggered it (user ID or 'system')
        """
        query = """
            INSERT INTO kill_switch_events (
                triggered_at, reason, triggered_by
            ) VALUES ($1, $2, $3)
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            event_id = await conn.fetchval(
                query,
                datetime.utcnow(),
                reason,
                triggered_by
            )

        logger.critical(
            f"KILL SWITCH ACTIVATED: {reason} (triggered by: {triggered_by})"
        )

        return event_id

    async def deactivate_kill_switch(self, deactivated_by: str = 'admin'):
        """
        Deactivate kill switch (resume trading).

        Args:
            deactivated_by: Who deactivated it (user ID)
        """
        query = """
            UPDATE kill_switch_events
            SET
                deactivated_at = $1,
                deactivated_by = $2
            WHERE DATE(triggered_at) = CURRENT_DATE
            AND deactivated_at IS NULL
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(),
                deactivated_by
            )

        logger.warning(f"Kill switch deactivated by: {deactivated_by}")

    # ========================================================================
    # PNL OPERATIONS
    # ========================================================================

    async def get_today_realized_pnl(self) -> Decimal:
        """
        Get today's realized PnL (from closed positions only).

        Returns:
            Realized PnL for today
        """
        query = """
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM positions
            WHERE DATE(closed_at) = CURRENT_DATE
        """

        async with self.pool.acquire() as conn:
            pnl = await conn.fetchval(query)

        return Decimal(str(pnl)) if pnl else Decimal('0')

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def execute_raw_query(self, query: str, *args) -> List[Dict]:
        """
        Execute raw SQL query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of rows as dictionaries
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)

        return [dict(row) for row in rows]

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if connected, False otherwise
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# ============================================================================
# GLOBAL DATABASE INSTANCE
# ============================================================================

# Global database instance (initialized at startup)
db: Optional[Database] = None


def get_database() -> Database:
    """
    Get global database instance.

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    if db is None:
        raise RuntimeError(
            "Database not initialized. "
            "Call initialize_database() first."
        )
    return db


async def initialize_database(connection_string: str):
    """
    Initialize global database instance.

    Call this at application startup.

    Args:
        connection_string: PostgreSQL connection string
    """
    global db

    db = Database(connection_string)
    await db.connect()

    logger.info("Database initialized")


async def shutdown_database():
    """
    Shutdown global database instance.

    Call this at application shutdown.
    """
    global db

    if db:
        await db.disconnect()
        db = None

    logger.info("Database shutdown")
