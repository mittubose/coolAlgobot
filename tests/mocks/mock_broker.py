"""
Mock Broker Client for testing.

Simulates Zerodha Kite Connect API responses without requiring real API credentials.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import random
import string

logger = logging.getLogger(__name__)


class MockBrokerClient:
    """
    Mock broker client that simulates Zerodha Kite Connect API.

    Features:
    - Simulates order placement, cancellation, modification
    - Auto-fills orders after configurable delay
    - Simulates realistic broker responses
    - Tracks positions
    - Configurable fill behavior (instant, delayed, partial, reject)
    """

    def __init__(
        self,
        fill_delay: float = 0.5,
        fill_probability: float = 0.95,
        simulate_slippage: bool = True
    ):
        """
        Initialize mock broker.

        Args:
            fill_delay: Seconds before auto-filling orders (default: 0.5)
            fill_probability: Probability order fills (default: 0.95 = 95%)
            simulate_slippage: Whether to simulate price slippage (default: True)
        """
        self.fill_delay = fill_delay
        self.fill_probability = fill_probability
        self.simulate_slippage = simulate_slippage

        # Order tracking
        self.orders: Dict[str, Dict] = {}  # broker_order_id -> order_dict
        self.order_counter = 1000

        # Position tracking
        self.positions: Dict[str, Dict] = {}  # symbol -> position_dict

        # Fill tasks
        self.fill_tasks: Dict[str, asyncio.Task] = {}

        logger.info(
            f"MockBrokerClient initialized: "
            f"fill_delay={fill_delay}s, fill_prob={fill_probability}"
        )

    # ========================================================================
    # ORDER PLACEMENT
    # ========================================================================

    async def place_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        product: str,
        validity: str,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        **kwargs
    ) -> Dict:
        """
        Place order (mock).

        Args:
            tradingsymbol: Symbol (e.g., "RELIANCE")
            exchange: Exchange (e.g., "NSE")
            transaction_type: "BUY" or "SELL"
            quantity: Order quantity
            order_type: "MARKET", "LIMIT", "SL", "SL-M"
            product: "MIS" or "CNC"
            validity: "DAY" or "IOC"
            price: Limit price (optional)
            trigger_price: Stop loss trigger (optional)

        Returns:
            Dict with order_id
        """
        # Generate broker order ID
        broker_order_id = self._generate_order_id()

        # Create order record
        order = {
            'order_id': broker_order_id,
            'tradingsymbol': tradingsymbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'order_type': order_type,
            'product': product,
            'validity': validity,
            'price': price,
            'trigger_price': trigger_price,
            'status': 'OPEN',
            'filled_quantity': 0,
            'average_price': 0,
            'placed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        self.orders[broker_order_id] = order

        logger.info(
            f"Order placed: {broker_order_id} - "
            f"{tradingsymbol} {transaction_type} {quantity} @ "
            f"{order_type} {price if price else 'MARKET'}"
        )

        # Start auto-fill task
        fill_task = asyncio.create_task(
            self._auto_fill_order(broker_order_id)
        )
        self.fill_tasks[broker_order_id] = fill_task

        return {'order_id': broker_order_id}

    async def _auto_fill_order(self, broker_order_id: str):
        """
        Automatically fill order after delay.

        Args:
            broker_order_id: Broker order ID
        """
        try:
            # Wait for fill delay
            await asyncio.sleep(self.fill_delay)

            order = self.orders.get(broker_order_id)

            if not order or order['status'] != 'OPEN':
                # Order cancelled or already filled
                return

            # Decide if order fills based on probability
            if random.random() > self.fill_probability:
                # Order rejected
                order['status'] = 'REJECTED'
                order['status_message'] = 'Simulated rejection'
                order['updated_at'] = datetime.utcnow()
                logger.info(f"Order {broker_order_id} REJECTED (simulated)")
                return

            # Fill order
            fill_price = self._calculate_fill_price(order)

            order['status'] = 'COMPLETE'
            order['filled_quantity'] = order['quantity']
            order['average_price'] = fill_price
            order['updated_at'] = datetime.utcnow()

            # Calculate transaction costs
            costs = self._calculate_transaction_costs(
                order['transaction_type'],
                order['quantity'],
                fill_price,
                order['product']
            )

            order.update(costs)

            logger.info(
                f"Order {broker_order_id} FILLED: "
                f"{order['quantity']} @ ₹{fill_price:.2f}"
            )

            # Update position
            self._update_position(order)

        except asyncio.CancelledError:
            logger.debug(f"Fill task cancelled for {broker_order_id}")
        except Exception as e:
            logger.error(f"Error auto-filling order {broker_order_id}: {e}")

    def _calculate_fill_price(self, order: Dict) -> float:
        """
        Calculate fill price with optional slippage.

        Args:
            order: Order dict

        Returns:
            Fill price
        """
        if order['order_type'] == 'MARKET':
            # Market order - use trigger price or estimate
            base_price = order['trigger_price'] if order['trigger_price'] else 2450.0

            if self.simulate_slippage:
                # Add random slippage (±0.1%)
                slippage_pct = random.uniform(-0.001, 0.001)
                fill_price = base_price * (1 + slippage_pct)
            else:
                fill_price = base_price

        else:
            # Limit/SL order - fill at specified price
            fill_price = order['price']

            if self.simulate_slippage:
                # Small improvement for limit orders (better fill)
                if order['transaction_type'] == 'BUY':
                    # Buy slightly lower
                    fill_price *= random.uniform(0.999, 1.0)
                else:
                    # Sell slightly higher
                    fill_price *= random.uniform(1.0, 1.001)

        return round(fill_price, 2)

    def _calculate_transaction_costs(
        self,
        side: str,
        quantity: int,
        price: float,
        product: str
    ) -> Dict:
        """
        Calculate realistic transaction costs (Zerodha).

        Args:
            side: BUY or SELL
            quantity: Quantity
            price: Price
            product: MIS or CNC

        Returns:
            Dict with cost breakdown
        """
        gross_value = quantity * price

        costs = {}

        # Brokerage
        if product == 'MIS':
            # Intraday: ₹20 or 0.03%, whichever is lower
            brokerage_pct = gross_value * 0.0003
            costs['brokerage'] = min(20.0, brokerage_pct)
        else:
            # Delivery: 0%
            costs['brokerage'] = 0.0

        # STT (Securities Transaction Tax)
        if product == 'MIS':
            # Intraday: 0.025% on sell side
            if side == 'SELL':
                costs['stt'] = gross_value * 0.00025
            else:
                costs['stt'] = 0.0
        else:
            # Delivery: 0.1% on sell side
            if side == 'SELL':
                costs['stt'] = gross_value * 0.001
            else:
                costs['stt'] = 0.0

        # Exchange transaction charge (NSE: 0.00325%)
        costs['exchange_transaction_charge'] = gross_value * 0.0000325

        # GST: 18% on (brokerage + exchange charges)
        taxable = costs['brokerage'] + costs['exchange_transaction_charge']
        costs['gst'] = taxable * 0.18

        # Stamp duty: 0.003% on buy side
        if side == 'BUY':
            costs['stamp_duty'] = gross_value * 0.00003
        else:
            costs['stamp_duty'] = 0.0

        # SEBI charges: ₹10 per crore
        costs['sebi_charges'] = (gross_value / 10000000) * 10

        # Round all to 2 decimals
        for key in costs:
            costs[key] = round(costs[key], 2)

        return costs

    def _update_position(self, order: Dict):
        """
        Update internal position tracking.

        Args:
            order: Filled order
        """
        symbol = order['tradingsymbol']

        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'average_price': 0,
                'realized_pnl': 0
            }

        position = self.positions[symbol]

        if order['transaction_type'] == 'BUY':
            new_quantity = position['quantity'] + order['quantity']

            if position['quantity'] >= 0:
                # Adding to long or opening long
                total_cost = (position['quantity'] * position['average_price']) + \
                           (order['quantity'] * order['average_price'])
                position['average_price'] = total_cost / new_quantity if new_quantity > 0 else 0
            else:
                # Reducing short position - calculate realized PnL
                closed_qty = min(order['quantity'], abs(position['quantity']))
                realized_pnl = closed_qty * (position['average_price'] - order['average_price'])
                position['realized_pnl'] += realized_pnl

            position['quantity'] = new_quantity

        else:  # SELL
            new_quantity = position['quantity'] - order['quantity']

            if position['quantity'] <= 0:
                # Adding to short or opening short
                total_cost = (abs(position['quantity']) * position['average_price']) + \
                           (order['quantity'] * order['average_price'])
                position['average_price'] = total_cost / abs(new_quantity) if new_quantity != 0 else 0
            else:
                # Reducing long position - calculate realized PnL
                closed_qty = min(order['quantity'], position['quantity'])
                realized_pnl = closed_qty * (order['average_price'] - position['average_price'])
                position['realized_pnl'] += realized_pnl

            position['quantity'] = new_quantity

        logger.debug(
            f"Position updated: {symbol} qty={position['quantity']} "
            f"avg=₹{position['average_price']:.2f}"
        )

    # ========================================================================
    # ORDER CANCELLATION
    # ========================================================================

    async def cancel_order(self, order_id: str, variety: str = 'regular') -> Dict:
        """
        Cancel order (mock).

        Args:
            order_id: Broker order ID
            variety: Order variety

        Returns:
            Dict with order_id
        """
        order = self.orders.get(order_id)

        if not order:
            raise Exception(f"Order {order_id} not found")

        if order['status'] != 'OPEN':
            raise Exception(f"Order {order_id} cannot be cancelled (status: {order['status']})")

        # Cancel the fill task
        if order_id in self.fill_tasks:
            self.fill_tasks[order_id].cancel()
            del self.fill_tasks[order_id]

        # Update order status
        order['status'] = 'CANCELLED'
        order['updated_at'] = datetime.utcnow()

        logger.info(f"Order {order_id} cancelled")

        return {'order_id': order_id}

    # ========================================================================
    # ORDER MODIFICATION
    # ========================================================================

    async def modify_order(
        self,
        order_id: str,
        variety: str = 'regular',
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        **kwargs
    ) -> Dict:
        """
        Modify order (mock).

        Args:
            order_id: Broker order ID
            variety: Order variety
            quantity: New quantity (optional)
            price: New price (optional)
            trigger_price: New trigger price (optional)

        Returns:
            Dict with order_id
        """
        order = self.orders.get(order_id)

        if not order:
            raise Exception(f"Order {order_id} not found")

        if order['status'] != 'OPEN':
            raise Exception(f"Order {order_id} cannot be modified (status: {order['status']})")

        # Update fields
        if quantity is not None:
            order['quantity'] = quantity
        if price is not None:
            order['price'] = price
        if trigger_price is not None:
            order['trigger_price'] = trigger_price

        order['updated_at'] = datetime.utcnow()

        logger.info(f"Order {order_id} modified")

        return {'order_id': order_id}

    # ========================================================================
    # ORDER QUERIES
    # ========================================================================

    async def orders(self) -> List[Dict]:
        """
        Get all orders (mock).

        Returns:
            List of order dicts
        """
        return list(self.orders.values())

    async def order_history(self, order_id: str) -> List[Dict]:
        """
        Get order history (mock).

        Args:
            order_id: Broker order ID

        Returns:
            List of order state dicts
        """
        order = self.orders.get(order_id)

        if not order:
            return []

        return [order]

    # ========================================================================
    # POSITION QUERIES
    # ========================================================================

    async def positions(self) -> Dict[str, Dict]:
        """
        Get positions (mock).

        Returns:
            Dict of symbol -> position
        """
        # Filter out closed positions
        open_positions = {
            symbol: pos
            for symbol, pos in self.positions.items()
            if pos['quantity'] != 0
        }

        return open_positions

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _generate_order_id(self) -> str:
        """
        Generate unique broker order ID.

        Returns:
            Order ID string
        """
        order_id = f"MOCK{self.order_counter:06d}"
        self.order_counter += 1
        return order_id

    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get order by ID.

        Args:
            order_id: Broker order ID

        Returns:
            Order dict or None
        """
        return self.orders.get(order_id)

    def reset(self):
        """
        Reset mock broker state.

        Clears all orders and positions.
        """
        # Cancel all pending fill tasks
        for task in self.fill_tasks.values():
            task.cancel()

        self.orders.clear()
        self.positions.clear()
        self.fill_tasks.clear()
        self.order_counter = 1000

        logger.info("MockBrokerClient reset")

    # ========================================================================
    # CONFIGURATION METHODS
    # ========================================================================

    def set_fill_delay(self, delay: float):
        """
        Set fill delay for future orders.

        Args:
            delay: Seconds before auto-fill
        """
        self.fill_delay = delay
        logger.info(f"Fill delay set to {delay}s")

    def set_fill_probability(self, probability: float):
        """
        Set fill probability for future orders.

        Args:
            probability: Probability (0.0 to 1.0)
        """
        if not 0 <= probability <= 1:
            raise ValueError("Probability must be between 0 and 1")

        self.fill_probability = probability
        logger.info(f"Fill probability set to {probability}")

    def enable_slippage(self, enabled: bool = True):
        """
        Enable/disable price slippage simulation.

        Args:
            enabled: Whether to simulate slippage
        """
        self.simulate_slippage = enabled
        logger.info(f"Slippage simulation {'enabled' if enabled else 'disabled'}")
