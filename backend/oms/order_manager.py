"""
OrderManager - Central Order Management System.

This is the HEART of the trading platform. ALL orders MUST flow through this class.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from backend.database.database import Database
from backend.models import Order, OrderRequest, OrderResult, OrderStatus
from backend.oms.position_manager import PositionManager

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Central Order Management System.

    Responsibilities:
    - Validate orders before submission
    - Track order lifecycle (PENDING → SUBMITTED → FILLED)
    - Update positions on fills
    - Reconcile positions with broker
    - Maintain audit trail

    CRITICAL: All order placement MUST go through this class.
    Direct broker API calls are FORBIDDEN.
    """

    def __init__(
        self,
        db: Database,
        broker_client,  # Zerodha client or mock for testing
        position_manager: PositionManager,
        validator=None  # PreTradeValidator (optional for now)
    ):
        """
        Initialize OrderManager.

        Args:
            db: Database instance
            broker_client: Broker API client (Zerodha)
            position_manager: Position manager instance
            validator: Pre-trade validator (optional)
        """
        self.db = db
        self.broker = broker_client
        self.positions = position_manager
        self.validator = validator

        # In-memory cache of active orders
        # Maps order_id -> Order object
        self.active_orders: Dict[int, Order] = {}

        # Background task handles
        self._monitor_task: Optional[asyncio.Task] = None
        self._reconcile_task: Optional[asyncio.Task] = None

        # Shutdown flag
        self._shutdown = False

        logger.info("OrderManager initialized")

    async def start(self):
        """
        Start background tasks.

        Call this after initialization to start:
        - Order monitoring loop
        - Position reconciliation loop
        """
        logger.info("Starting OrderManager background tasks...")

        # Start monitoring active orders
        self._monitor_task = asyncio.create_task(self._monitor_orders())

        # Start position reconciliation
        self._reconcile_task = asyncio.create_task(self._reconciliation_loop())

        logger.info("OrderManager background tasks started")

    async def stop(self):
        """
        Stop background tasks gracefully.

        Call this at application shutdown.
        """
        logger.info("Stopping OrderManager...")

        self._shutdown = True

        # Cancel background tasks
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._reconcile_task:
            self._reconcile_task.cancel()
            try:
                await self._reconcile_task
            except asyncio.CancelledError:
                pass

        logger.info("OrderManager stopped")

    # ========================================================================
    # ORDER PLACEMENT
    # ========================================================================

    async def place_order(self, request: OrderRequest) -> OrderResult:
        """
        Place order with full validation and tracking.

        This is the ONLY way to place orders in the system.

        Flow:
        1. Validate order (if validator provided)
        2. Log to database (status: PENDING)
        3. Submit to broker
        4. Update database (status: SUBMITTED)
        5. Add to active orders for monitoring
        6. Return result

        Args:
            request: Order request object

        Returns:
            OrderResult with order_id, broker_order_id, status

        Raises:
            OrderRejected: If validation fails
            OrderSubmissionFailed: If broker API fails
        """
        logger.info(
            f"Placing order: {request.symbol} {request.side.value} "
            f"{request.quantity} @ {request.order_type.value}"
        )

        # STEP 1: Validate order (if validator provided)
        if self.validator:
            validation = await self.validator.validate_order(request)

            if not validation.is_valid:
                logger.warning(
                    f"Order validation failed: {validation.reason} "
                    f"(check: {validation.failed_check})"
                )

                # Log failed validation to database
                await self.db.create_order(
                    request,
                    status='REJECTED',
                    status_message=f"Validation failed: {validation.reason}",
                    validation_result=validation.to_dict()
                )

                raise OrderRejected(validation.reason, validation.failed_check)

            logger.info("✓ Order passed all validation checks")

        # STEP 2: Log to database BEFORE submitting to broker
        order_id = await self.db.create_order(
            request,
            status='PENDING',
            validation_result=validation.to_dict() if self.validator else None
        )

        logger.info(f"Order logged to database: order_id={order_id}")

        try:
            # STEP 3: Submit to broker
            logger.info(f"Submitting order to broker...")

            broker_response = await self._submit_to_broker(request)
            broker_order_id = broker_response.get('order_id')

            if not broker_order_id:
                raise OrderSubmissionFailed("Broker did not return order_id")

            logger.info(f"✓ Order submitted to broker: broker_order_id={broker_order_id}")

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

            logger.info(f"Order added to active monitoring (total active: {len(self.active_orders)})")

            # STEP 6: Return result
            return OrderResult(
                order_id=order_id,
                broker_order_id=broker_order_id,
                status=OrderStatus.SUBMITTED,
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

    async def _submit_to_broker(self, request: OrderRequest) -> Dict:
        """
        Submit order to broker API.

        Args:
            request: Order request

        Returns:
            Broker response dict with order_id

        Raises:
            Exception if submission fails
        """
        # Prepare broker order parameters
        order_params = {
            'tradingsymbol': request.symbol,
            'exchange': request.exchange,
            'transaction_type': request.side.value,
            'quantity': request.quantity,
            'order_type': request.order_type.value,
            'product': request.product.value,
            'validity': request.validity.value
        }

        # Add price for limit/SL orders
        if request.price:
            order_params['price'] = float(request.price)

        # Add trigger price for SL orders
        if request.trigger_price:
            order_params['trigger_price'] = float(request.trigger_price)

        # Call broker API
        try:
            response = await self.broker.place_order(**order_params)
            return response

        except Exception as e:
            logger.error(f"Broker API error: {e}")
            raise

    # ========================================================================
    # ORDER CANCELLATION
    # ========================================================================

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
        logger.info(f"Cancelling order: {order_id}")

        order = await self.db.get_order(order_id)

        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")

        if order.status not in [OrderStatus.SUBMITTED, OrderStatus.OPEN]:
            raise OrderNotCancellable(
                f"Cannot cancel order in status {order.status.value}"
            )

        try:
            # Cancel at broker
            await self.broker.cancel_order(
                order_id=order.broker_order_id,
                variety='regular'
            )

            logger.info(f"✓ Order cancelled at broker: {order.broker_order_id}")

            # Update database
            await self.db.update_order(
                order_id,
                status='CANCELLED',
                cancelled_at=datetime.utcnow()
            )

            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

            logger.info(f"✓ Order {order_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    # ========================================================================
    # ORDER MODIFICATION
    # ========================================================================

    async def modify_order(
        self,
        order_id: int,
        new_price: Optional[Decimal] = None,
        new_quantity: Optional[int] = None,
        new_trigger_price: Optional[Decimal] = None
    ) -> bool:
        """
        Modify an open order.

        Args:
            order_id: Internal order ID
            new_price: New limit price (optional)
            new_quantity: New quantity (optional)
            new_trigger_price: New trigger price (optional)

        Returns:
            True if modified successfully

        Raises:
            OrderNotFound: If order doesn't exist
            OrderNotModifiable: If order already filled/cancelled
        """
        logger.info(f"Modifying order: {order_id}")

        order = await self.db.get_order(order_id)

        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")

        if order.status not in [OrderStatus.SUBMITTED, OrderStatus.OPEN]:
            raise OrderNotModifiable(
                f"Cannot modify order in status {order.status.value}"
            )

        try:
            # Modify at broker
            modify_params = {
                'order_id': order.broker_order_id,
                'variety': 'regular'
            }

            if new_price:
                modify_params['price'] = float(new_price)
            if new_quantity:
                modify_params['quantity'] = new_quantity
            if new_trigger_price:
                modify_params['trigger_price'] = float(new_trigger_price)

            await self.broker.modify_order(**modify_params)

            logger.info(f"✓ Order modified at broker: {order.broker_order_id}")

            # Update database
            updates = {}
            if new_price:
                updates['price'] = new_price
            if new_quantity:
                updates['quantity'] = new_quantity
            if new_trigger_price:
                updates['trigger_price'] = new_trigger_price

            await self.db.update_order(order_id, **updates)

            logger.info(f"✓ Order {order_id} modified successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to modify order {order_id}: {e}")
            raise

    # ========================================================================
    # ORDER MONITORING (Background Task)
    # ========================================================================

    async def _monitor_orders(self):
        """
        Background task: Monitor active orders for status updates.

        Runs continuously, checking every 1 second.
        """
        logger.info("Order monitoring started")

        while not self._shutdown:
            try:
                if not self.active_orders:
                    # No active orders, sleep longer
                    await asyncio.sleep(5)
                    continue

                # Get order updates from broker
                broker_order_ids = [
                    order.broker_order_id
                    for order in self.active_orders.values()
                    if order.broker_order_id
                ]

                if broker_order_ids:
                    updates = await self._get_order_updates(broker_order_ids)

                    for update in updates:
                        await self._process_order_update(update)

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Order monitoring cancelled")
                break

            except Exception as e:
                logger.error(f"Error in order monitoring: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _get_order_updates(self, broker_order_ids: List[str]) -> List[Dict]:
        """
        Get order updates from broker.

        Args:
            broker_order_ids: List of broker order IDs to check

        Returns:
            List of order update dicts
        """
        try:
            # Get all orders from broker
            all_orders = await self.broker.orders()

            # Filter to our order IDs
            updates = [
                order for order in all_orders
                if order.get('order_id') in broker_order_ids
            ]

            return updates

        except Exception as e:
            logger.error(f"Failed to get order updates from broker: {e}")
            return []

    async def _process_order_update(self, update: Dict):
        """
        Process order status update from broker.

        Args:
            update: Order update dict from broker
        """
        broker_order_id = update.get('order_id')
        new_status = update.get('status')

        # Find internal order ID
        order_id = None
        for oid, order in self.active_orders.items():
            if order.broker_order_id == broker_order_id:
                order_id = oid
                break

        if order_id is None:
            logger.warning(f"Received update for unknown order: {broker_order_id}")
            return

        logger.debug(f"Order {order_id} status update: {new_status}")

        # Map broker status to our status
        status_mapping = {
            'OPEN': OrderStatus.OPEN,
            'COMPLETE': OrderStatus.FILLED,
            'CANCELLED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED
        }

        our_status = status_mapping.get(new_status, OrderStatus.OPEN)

        # Update database
        await self.db.update_order(
            order_id=order_id,
            status=our_status.value,
            filled_quantity=update.get('filled_quantity', 0),
            average_price=Decimal(str(update.get('average_price', 0))) if update.get('average_price') else None,
            status_message=update.get('status_message', ''),
            updated_at=datetime.utcnow()
        )

        # Handle terminal states
        if our_status == OrderStatus.FILLED:
            await self._on_order_filled(order_id, update)
            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

        elif our_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            await self._on_order_terminated(order_id, our_status, update)
            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

    async def _on_order_filled(self, order_id: int, fill_data: Dict):
        """
        Handle order fill.

        Actions:
        1. Log trade with costs
        2. Update position
        3. Calculate PnL if closing position
        4. Trigger achievement check

        Args:
            order_id: Order ID
            fill_data: Fill data from broker
        """
        order = await self.db.get_order(order_id)

        logger.info(
            f"Order {order_id} FILLED: {order.symbol} {order.side.value} "
            f"{order.quantity} @ ₹{fill_data.get('average_price', 0):.2f}"
        )

        # Extract fill details
        filled_qty = fill_data.get('filled_quantity', order.quantity)
        avg_price = Decimal(str(fill_data.get('average_price', 0)))

        # Log trade with transaction costs
        trade_id = await self.db.create_trade(
            order_id=order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side.value,
            quantity=filled_qty,
            price=avg_price,
            broker_trade_id=fill_data.get('trade_id'),
            # Transaction costs from broker
            brokerage=Decimal(str(fill_data.get('brokerage', 0))),
            stt=Decimal(str(fill_data.get('stt', 0))),
            exchange_txn_charge=Decimal(str(fill_data.get('exchange_transaction_charge', 0))),
            gst=Decimal(str(fill_data.get('gst', 0))),
            stamp_duty=Decimal(str(fill_data.get('stamp_duty', 0))),
            executed_at=datetime.utcnow()
        )

        logger.info(f"Trade logged: trade_id={trade_id}")

        # Update position
        await self.positions.update_position_on_fill(
            order=order,
            filled_quantity=filled_qty,
            fill_price=avg_price
        )

        # Check if this closed a position
        position = await self.positions.get_position(order.symbol, order.exchange)

        if position and position.quantity == 0:
            # Position closed - trigger achievement check
            pnl = position.realized_pnl

            logger.info(f"Position closed for {order.symbol}: PnL = ₹{pnl:.2f}")

            # Trigger achievement check via event
            # (This would integrate with achievement system from dashboard)
            await self._trigger_achievement_check({
                'event': 'tradeExecuted',
                'pnl': float(pnl),
                'symbol': order.symbol,
                'time': datetime.utcnow().isoformat(),
                'exitReason': order.metadata.get('exit_reason', 'target')
            })

    async def _on_order_terminated(self, order_id: int, status: OrderStatus, data: Dict):
        """
        Handle order termination (cancelled or rejected).

        Args:
            order_id: Order ID
            status: Terminal status (CANCELLED or REJECTED)
            data: Data from broker
        """
        order = await self.db.get_order(order_id)

        logger.info(
            f"Order {order_id} {status.value}: {order.symbol} "
            f"{order.side.value} {order.quantity}"
        )

        # Log reason
        reason = data.get('status_message', 'Unknown')
        logger.info(f"  Reason: {reason}")

    async def _trigger_achievement_check(self, event_data: Dict):
        """
        Trigger achievement check (integrates with dashboard).

        Args:
            event_data: Event data to pass to achievement system
        """
        # This would broadcast via WebSocket to dashboard
        # For now, just log
        logger.info(f"Achievement check triggered: {event_data}")

    # ========================================================================
    # POSITION RECONCILIATION (Background Task)
    # ========================================================================

    async def _reconciliation_loop(self):
        """
        Background task: Reconcile positions with broker every 30 seconds.
        """
        logger.info("Position reconciliation started")

        while not self._shutdown:
            try:
                await self.reconcile_positions()
                await asyncio.sleep(30)  # Every 30 seconds

            except asyncio.CancelledError:
                logger.info("Position reconciliation cancelled")
                break

            except Exception as e:
                logger.error(f"Error in reconciliation: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def reconcile_positions(self) -> Dict:
        """
        Reconcile internal positions with broker positions.

        Returns:
            Dict with reconciliation results:
            {
                'all_clear': bool,
                'mismatches': List[Dict],
                'unknown_positions': List[Dict]
            }
        """
        logger.debug("Starting position reconciliation...")

        # Get broker positions
        try:
            broker_positions = await self.broker.positions()
        except Exception as e:
            logger.error(f"Failed to get broker positions: {e}")
            return {'all_clear': False, 'error': str(e)}

        # Get internal positions
        internal_positions = await self.positions.get_all_positions_dict()

        mismatches = []
        unknown_positions = []

        # Check all broker positions
        for symbol, broker_pos in broker_positions.items():
            internal_pos = internal_positions.get(symbol)

            if internal_pos is None:
                # Broker has position, we don't
                logger.warning(
                    f"Unknown position detected: {symbol} "
                    f"qty={broker_pos.get('quantity')}"
                )

                unknown_positions.append({
                    'symbol': symbol,
                    'broker_quantity': broker_pos.get('quantity'),
                    'broker_avg_price': broker_pos.get('average_price')
                })

                # Log to database
                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    exchange='NSE',  # Assume NSE
                    issue_type='UNKNOWN_POSITION',
                    severity='CRITICAL',
                    broker_quantity=broker_pos.get('quantity'),
                    broker_avg_price=Decimal(str(broker_pos.get('average_price', 0)))
                )

            elif internal_pos.quantity != broker_pos.get('quantity'):
                # Quantity mismatch
                logger.error(
                    f"Position mismatch for {symbol}: "
                    f"internal={internal_pos.quantity}, "
                    f"broker={broker_pos.get('quantity')}"
                )

                mismatches.append({
                    'symbol': symbol,
                    'internal_quantity': internal_pos.quantity,
                    'broker_quantity': broker_pos.get('quantity'),
                    'difference': broker_pos.get('quantity') - internal_pos.quantity
                })

                # Log to database
                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    exchange=internal_pos.exchange,
                    issue_type='QUANTITY_MISMATCH',
                    severity='CRITICAL',
                    internal_quantity=internal_pos.quantity,
                    broker_quantity=broker_pos.get('quantity'),
                    difference=broker_pos.get('quantity') - internal_pos.quantity
                )

                # CRITICAL: Trust broker, update internal state
                await self.positions.force_update_quantity(
                    symbol=symbol,
                    exchange=internal_pos.exchange,
                    quantity=broker_pos.get('quantity'),
                    reason='RECONCILIATION_FIX'
                )

        # Check for phantom positions (we have, broker doesn't)
        for symbol, internal_pos in internal_positions.items():
            if symbol not in broker_positions and internal_pos.quantity != 0:
                logger.error(
                    f"Phantom position detected: {symbol} "
                    f"qty={internal_pos.quantity}"
                )

                mismatches.append({
                    'symbol': symbol,
                    'internal_quantity': internal_pos.quantity,
                    'broker_quantity': 0,
                    'type': 'PHANTOM_POSITION'
                })

                # Log to database
                await self.db.log_reconciliation_issue(
                    symbol=symbol,
                    exchange=internal_pos.exchange,
                    issue_type='PHANTOM_POSITION',
                    severity='CRITICAL',
                    internal_quantity=internal_pos.quantity,
                    broker_quantity=0
                )

                # Close phantom position
                await self.positions.force_close_position(
                    symbol=symbol,
                    exchange=internal_pos.exchange,
                    reason='RECONCILIATION_FIX'
                )

        all_clear = len(mismatches) == 0 and len(unknown_positions) == 0

        if all_clear:
            logger.debug("✓ Reconciliation complete: All positions match")
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

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    async def get_order(self, order_id: int) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order object or None if not found
        """
        return await self.db.get_order(order_id)

    async def get_active_orders(self) -> List[Order]:
        """
        Get all active orders.

        Returns:
            List of active Order objects
        """
        return await self.db.get_active_orders()

    async def get_orders_by_strategy(self, strategy_id: int) -> List[Order]:
        """
        Get orders for a specific strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            List of Order objects
        """
        return await self.db.get_orders_by_strategy(strategy_id)


# ============================================================================
# EXCEPTIONS
# ============================================================================

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


class OrderNotModifiable(Exception):
    """Order cannot be modified (already filled/cancelled)."""
    pass
