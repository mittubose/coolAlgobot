"""
Order Manager
Handles order placement, modification, cancellation, and tracking
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from src.utils.logger import setup_logger
from src.database import get_session, Trade


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = 'pending'
    PLACED = 'placed'
    OPEN = 'open'
    COMPLETE = 'complete'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'
    FAILED = 'failed'


class OrderManager:
    """
    Manages order execution and tracking
    - Place, modify, cancel orders
    - Track order status
    - Maintain order book
    - Log all orders to database
    """

    def __init__(self, broker, mode='paper'):
        """
        Initialize Order Manager

        Args:
            broker: Broker instance
            mode: 'paper' or 'live' trading mode
        """
        self.broker = broker
        self.mode = mode
        self.logger = setup_logger('order_manager')

        # Order tracking
        self.orders = {}  # {order_id: order_data}
        self.pending_orders = []  # List of pending order IDs
        self.completed_orders = []  # List of completed order IDs

        # Thread safety
        self.lock = threading.Lock()

        # Paper trading simulation
        self.paper_order_id = 1000000

        self.logger.info(f"OrderManager initialized in {mode} mode")

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = 'MARKET',
        price: float = None,
        trigger_price: float = None,
        product: str = 'MIS',
        validity: str = 'DAY',
        strategy_name: str = None,
        tag: str = None
    ) -> Optional[Dict]:
        """
        Place an order

        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, BSE, NFO, etc.)
            transaction_type: BUY or SELL
            quantity: Number of shares/lots
            order_type: MARKET, LIMIT, SL, SL-M
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            product: MIS, CNC, NRML
            validity: DAY, IOC
            strategy_name: Associated strategy name
            tag: Custom tag for the order

        Returns:
            Order response dict or None
        """
        try:
            self.logger.info(
                f"Placing {order_type} {transaction_type} order: "
                f"{quantity} x {symbol} @ {price or 'MARKET'}"
            )

            with self.lock:
                if self.mode == 'paper':
                    # Paper trading simulation
                    order_response = self._place_paper_order(
                        symbol, exchange, transaction_type, quantity,
                        order_type, price, trigger_price, product, validity, tag
                    )
                else:
                    # Live trading
                    order_response = self.broker.place_order(
                        symbol=symbol,
                        exchange=exchange,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        order_type=order_type,
                        price=price,
                        trigger_price=trigger_price,
                        product=product,
                        validity=validity,
                        tag=tag
                    )

                if order_response:
                    order_id = order_response.get('order_id')

                    # Store order
                    self.orders[order_id] = {
                        'order_id': order_id,
                        'symbol': symbol,
                        'exchange': exchange,
                        'transaction_type': transaction_type,
                        'quantity': quantity,
                        'order_type': order_type,
                        'price': price,
                        'trigger_price': trigger_price,
                        'product': product,
                        'validity': validity,
                        'status': OrderStatus.PLACED.value,
                        'placed_at': datetime.now(),
                        'strategy_name': strategy_name,
                        'tag': tag,
                        'response': order_response
                    }

                    self.pending_orders.append(order_id)

                    # Log to database
                    self._log_order_to_db(self.orders[order_id])

                    self.logger.info(f"Order placed successfully: {order_id}")
                    return order_response

                else:
                    self.logger.error("Failed to place order - no response from broker")
                    return None

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    def _place_paper_order(
        self, symbol, exchange, transaction_type, quantity,
        order_type, price, trigger_price, product, validity, tag
    ) -> Dict:
        """Simulate order placement in paper trading mode"""
        self.paper_order_id += 1
        order_id = f"PAPER_{self.paper_order_id}"

        return {
            'order_id': order_id,
            'status': 'COMPLETE' if order_type == 'MARKET' else 'OPEN',
            'message': 'Order placed successfully (PAPER TRADING)'
        }

    def modify_order(
        self,
        order_id: str,
        quantity: int = None,
        price: float = None,
        order_type: str = None,
        trigger_price: float = None
    ) -> bool:
        """
        Modify an existing order

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            order_type: New order type
            trigger_price: New trigger price

        Returns:
            True if successful, False otherwise
        """
        try:
            if order_id not in self.orders:
                self.logger.error(f"Order {order_id} not found")
                return False

            self.logger.info(f"Modifying order: {order_id}")

            with self.lock:
                if self.mode == 'paper':
                    # Paper trading simulation
                    success = True
                else:
                    # Live trading
                    success = self.broker.modify_order(
                        order_id=order_id,
                        quantity=quantity,
                        price=price,
                        order_type=order_type,
                        trigger_price=trigger_price
                    )

                if success:
                    # Update local order
                    if quantity:
                        self.orders[order_id]['quantity'] = quantity
                    if price:
                        self.orders[order_id]['price'] = price
                    if order_type:
                        self.orders[order_id]['order_type'] = order_type
                    if trigger_price:
                        self.orders[order_id]['trigger_price'] = trigger_price

                    self.orders[order_id]['modified_at'] = datetime.now()

                    self.logger.info(f"Order {order_id} modified successfully")
                    return True
                else:
                    self.logger.error(f"Failed to modify order {order_id}")
                    return False

        except Exception as e:
            self.logger.error(f"Error modifying order {order_id}: {e}")
            return False

    def cancel_order(self, order_id: str, variety: str = 'regular') -> bool:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel
            variety: Order variety (regular, amo, co, iceberg)

        Returns:
            True if successful, False otherwise
        """
        try:
            if order_id not in self.orders:
                self.logger.error(f"Order {order_id} not found")
                return False

            self.logger.info(f"Cancelling order: {order_id}")

            with self.lock:
                if self.mode == 'paper':
                    # Paper trading simulation
                    success = True
                else:
                    # Live trading
                    success = self.broker.cancel_order(order_id, variety)

                if success:
                    self.orders[order_id]['status'] = OrderStatus.CANCELLED.value
                    self.orders[order_id]['cancelled_at'] = datetime.now()

                    if order_id in self.pending_orders:
                        self.pending_orders.remove(order_id)

                    self.logger.info(f"Order {order_id} cancelled successfully")
                    return True
                else:
                    self.logger.error(f"Failed to cancel order {order_id}")
                    return False

        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[str]:
        """
        Get current status of an order

        Args:
            order_id: Order ID

        Returns:
            Order status string or None
        """
        try:
            if self.mode == 'paper':
                # Return local status for paper trading
                if order_id in self.orders:
                    return self.orders[order_id]['status']
            else:
                # Fetch from broker for live trading
                order_info = self.broker.get_order_history(order_id)
                if order_info and len(order_info) > 0:
                    latest = order_info[-1]
                    status = latest.get('status')

                    # Update local order
                    if order_id in self.orders:
                        self.orders[order_id]['status'] = status

                    return status

            return None

        except Exception as e:
            self.logger.error(f"Error getting order status for {order_id}: {e}")
            return None

    def update_order_statuses(self):
        """Update status for all pending orders"""
        try:
            if not self.pending_orders:
                return

            self.logger.debug(f"Updating status for {len(self.pending_orders)} pending orders")

            for order_id in list(self.pending_orders):
                status = self.get_order_status(order_id)

                if status in ['COMPLETE', 'CANCELLED', 'REJECTED']:
                    # Move to completed
                    self.pending_orders.remove(order_id)
                    self.completed_orders.append(order_id)

                    if status == 'COMPLETE':
                        # Update trade in database
                        self._update_trade_in_db(order_id)

        except Exception as e:
            self.logger.error(f"Error updating order statuses: {e}")

    def get_orders(self, status: str = None) -> List[Dict]:
        """
        Get orders, optionally filtered by status

        Args:
            status: Filter by status (pending, complete, cancelled, etc.)

        Returns:
            List of order dicts
        """
        if status:
            return [
                order for order in self.orders.values()
                if order['status'].lower() == status.lower()
            ]
        return list(self.orders.values())

    def get_pending_orders(self) -> List[Dict]:
        """Get all pending orders"""
        return [self.orders[oid] for oid in self.pending_orders if oid in self.orders]

    def get_completed_orders(self) -> List[Dict]:
        """Get all completed orders"""
        return [self.orders[oid] for oid in self.completed_orders if oid in self.orders]

    def cancel_all_orders(self) -> int:
        """
        Cancel all pending orders

        Returns:
            Number of orders cancelled
        """
        cancelled_count = 0

        for order_id in list(self.pending_orders):
            if self.cancel_order(order_id):
                cancelled_count += 1

        self.logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count

    def _log_order_to_db(self, order_data: Dict):
        """Log order to database"""
        try:
            with get_session() as session:
                trade = Trade(
                    order_id=order_data['order_id'],
                    symbol=order_data['symbol'],
                    exchange=order_data['exchange'],
                    side=order_data['transaction_type'],
                    quantity=order_data['quantity'],
                    order_type=order_data['order_type'],
                    entry_price=order_data.get('price'),
                    product_type=order_data['product'],
                    strategy_name=order_data.get('strategy_name'),
                    status='open',
                    entry_time=order_data['placed_at']
                )
                session.add(trade)
                session.commit()

        except Exception as e:
            self.logger.error(f"Error logging order to database: {e}")

    def _update_trade_in_db(self, order_id: str):
        """Update trade in database when order completes"""
        try:
            if order_id not in self.orders:
                return

            order_data = self.orders[order_id]

            with get_session() as session:
                trade = session.query(Trade).filter_by(order_id=order_id).first()
                if trade:
                    trade.status = 'closed'
                    trade.exit_time = datetime.now()
                    # Additional fields would be updated here (exit_price, pnl, etc.)
                    session.commit()

        except Exception as e:
            self.logger.error(f"Error updating trade in database: {e}")

    def get_summary(self) -> Dict:
        """
        Get summary of order manager status

        Returns:
            Dict with status information
        """
        return {
            'mode': self.mode,
            'total_orders': len(self.orders),
            'pending_orders': len(self.pending_orders),
            'completed_orders': len(self.completed_orders),
            'orders_by_status': {
                'pending': len([o for o in self.orders.values() if o['status'] == 'PENDING']),
                'open': len([o for o in self.orders.values() if o['status'] == 'OPEN']),
                'complete': len([o for o in self.orders.values() if o['status'] == 'COMPLETE']),
                'cancelled': len([o for o in self.orders.values() if o['status'] == 'CANCELLED']),
                'rejected': len([o for o in self.orders.values() if o['status'] == 'REJECTED']),
            }
        }

    def cleanup(self):
        """Cleanup resources"""
        self.cancel_all_orders()
        self.logger.info("OrderManager cleaned up")
