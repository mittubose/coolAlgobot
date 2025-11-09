"""
PositionManager - Position tracking and management.

Manages all open and closed positions with PnL tracking.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from backend.database.database import Database
from backend.models import Position, Order

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Position tracking and management.

    Responsibilities:
    - Track open positions
    - Update positions on order fills
    - Calculate realized/unrealized PnL
    - Close positions
    - Provide position statistics
    """

    def __init__(self, db: Database):
        """
        Initialize PositionManager.

        Args:
            db: Database instance
        """
        self.db = db

        logger.info("PositionManager initialized")

    # ========================================================================
    # POSITION UPDATES
    # ========================================================================

    async def update_position_on_fill(
        self,
        order: Order,
        filled_quantity: int,
        fill_price: Decimal
    ):
        """
        Update position when an order is filled.

        Args:
            order: Filled order
            filled_quantity: Quantity filled
            fill_price: Fill price
        """
        logger.info(
            f"Updating position for {order.symbol}: "
            f"{order.side.value} {filled_quantity} @ ₹{fill_price}"
        )

        # Get existing position
        position = await self.get_position(order.symbol, order.exchange)

        if position is None:
            # No existing position - create new
            await self._create_position_from_order(
                order, filled_quantity, fill_price
            )
        else:
            # Update existing position
            await self._update_existing_position(
                position, order, filled_quantity, fill_price
            )

    async def _create_position_from_order(
        self,
        order: Order,
        quantity: int,
        price: Decimal
    ):
        """
        Create new position from order fill.

        Args:
            order: Order that created the position
            quantity: Filled quantity
            price: Fill price
        """
        # Determine position quantity (positive for BUY, negative for SELL)
        position_quantity = quantity if order.is_buy else -quantity

        logger.info(
            f"Creating new position: {order.symbol} qty={position_quantity} @ ₹{price}"
        )

        await self.db.create_position(
            symbol=order.symbol,
            exchange=order.exchange,
            strategy_id=order.strategy_id,
            quantity=position_quantity,
            average_price=price,
            product=order.product.value,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            entry_order_ids=[order.id],
            metadata={
                'entry_time': datetime.utcnow().isoformat(),
                'entry_reason': order.metadata.get('entry_reason', 'signal')
            }
        )

    async def _update_existing_position(
        self,
        position: Position,
        order: Order,
        quantity: int,
        price: Decimal
    ):
        """
        Update existing position with new fill.

        This handles:
        - Adding to position
        - Reducing position
        - Closing position
        - Reversing position (close and open opposite)

        Args:
            position: Existing position
            order: New order
            quantity: Filled quantity
            price: Fill price
        """
        logger.info(
            f"Updating position {position.symbol}: "
            f"current_qty={position.quantity}, "
            f"fill={'+' if order.is_buy else '-'}{quantity}"
        )

        # Calculate new quantity
        if order.is_buy:
            new_quantity = position.quantity + quantity
        else:
            new_quantity = position.quantity - quantity

        # Determine action based on position change
        if position.is_long and order.is_buy:
            # Adding to long position
            await self._add_to_position(position, quantity, price, order.id)

        elif position.is_short and order.is_sell:
            # Adding to short position
            await self._add_to_position(position, quantity, price, order.id)

        elif position.is_long and order.is_sell:
            # Reducing/closing long position
            if abs(quantity) >= position.quantity:
                # Closing position (or reversing)
                await self._close_position(position, quantity, price, order.id)

                # If reversing, create new short position
                if quantity > position.quantity:
                    remaining_qty = quantity - position.quantity
                    await self._create_position_from_order(order, remaining_qty, price)
            else:
                # Partial close
                await self._reduce_position(position, quantity, price, order.id)

        elif position.is_short and order.is_buy:
            # Reducing/closing short position
            if quantity >= abs(position.quantity):
                # Closing position (or reversing)
                await self._close_position(position, quantity, price, order.id)

                # If reversing, create new long position
                if quantity > abs(position.quantity):
                    remaining_qty = quantity - abs(position.quantity)
                    await self._create_position_from_order(order, remaining_qty, price)
            else:
                # Partial close
                await self._reduce_position(position, quantity, price, order.id)

    async def _add_to_position(
        self,
        position: Position,
        quantity: int,
        price: Decimal,
        order_id: int
    ):
        """
        Add to existing position (averaging up/down).

        Args:
            position: Existing position
            quantity: Quantity to add
            price: Fill price
            order_id: Order ID
        """
        # Calculate new average price
        total_cost = (position.quantity * position.average_price) + (quantity * price)
        new_quantity = position.quantity + quantity if position.is_long else position.quantity - quantity
        new_avg_price = total_cost / abs(new_quantity)

        logger.info(
            f"Adding to position {position.symbol}: "
            f"old_avg=₹{position.average_price:.2f}, "
            f"new_avg=₹{new_avg_price:.2f}"
        )

        # Update entry order IDs
        entry_order_ids = position.entry_order_ids.copy()
        entry_order_ids.append(order_id)

        await self.db.update_position(
            position.id,
            quantity=new_quantity,
            average_price=new_avg_price,
            entry_order_ids=entry_order_ids
        )

    async def _reduce_position(
        self,
        position: Position,
        quantity: int,
        price: Decimal,
        order_id: int
    ):
        """
        Partially close position.

        Args:
            position: Existing position
            quantity: Quantity to close
            price: Exit price
            order_id: Order ID
        """
        # Calculate realized PnL on closed portion
        if position.is_long:
            realized_pnl = quantity * (price - position.average_price)
            new_quantity = position.quantity - quantity
        else:
            realized_pnl = quantity * (position.average_price - price)
            new_quantity = position.quantity + quantity

        logger.info(
            f"Reducing position {position.symbol}: "
            f"close_qty={quantity}, realized_pnl=₹{realized_pnl:.2f}"
        )

        # Update exit order IDs
        exit_order_ids = position.exit_order_ids.copy()
        exit_order_ids.append(order_id)

        await self.db.update_position(
            position.id,
            quantity=new_quantity,
            realized_pnl=position.realized_pnl + realized_pnl,
            exit_order_ids=exit_order_ids
        )

    async def _close_position(
        self,
        position: Position,
        quantity: int,
        price: Decimal,
        order_id: int
    ):
        """
        Fully close position.

        Args:
            position: Existing position
            quantity: Close quantity
            price: Exit price
            order_id: Order ID
        """
        # Calculate final realized PnL
        if position.is_long:
            realized_pnl = position.quantity * (price - position.average_price)
        else:
            realized_pnl = abs(position.quantity) * (position.average_price - price)

        # Add any existing realized PnL
        total_realized_pnl = position.realized_pnl + realized_pnl

        logger.info(
            f"Closing position {position.symbol}: "
            f"final_pnl=₹{total_realized_pnl:.2f}"
        )

        # Update exit order IDs
        exit_order_ids = position.exit_order_ids.copy()
        exit_order_ids.append(order_id)

        # Close position
        await self.db.close_position(
            position.id,
            realized_pnl=total_realized_pnl,
            exit_order_ids=exit_order_ids
        )

    # ========================================================================
    # POSITION QUERIES
    # ========================================================================

    async def get_position(
        self,
        symbol: str,
        exchange: str = 'NSE',
        strategy_id: int = None
    ) -> Optional[Position]:
        """
        Get position by symbol.

        Args:
            symbol: Symbol
            exchange: Exchange (default: NSE)
            strategy_id: Strategy ID (optional)

        Returns:
            Position object or None if not found
        """
        return await self.db.get_position(symbol, exchange, strategy_id)

    async def get_all_open_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of Position objects
        """
        return await self.db.get_all_open_positions()

    async def get_all_positions_dict(self) -> Dict[str, Position]:
        """
        Get all open positions as dict keyed by symbol.

        Returns:
            Dict of symbol -> Position
        """
        positions = await self.db.get_all_open_positions()
        return {pos.symbol: pos for pos in positions}

    async def get_open_position_count(self) -> int:
        """
        Get count of open positions.

        Returns:
            Number of open positions
        """
        return await self.db.get_open_position_count()

    # ========================================================================
    # REAL-TIME PNL UPDATES
    # ========================================================================

    async def update_unrealized_pnl(self, symbol: str, current_price: Decimal):
        """
        Update unrealized PnL for a position at current price.

        Args:
            symbol: Symbol
            current_price: Current market price
        """
        position = await self.get_position(symbol)

        if position and position.is_open:
            # Calculate unrealized PnL
            unrealized_pnl = position.calculate_unrealized_pnl(current_price)

            # Update price extremes
            position.update_price_extremes(current_price)

            # Update in database
            await self.db.update_position(
                position.id,
                unrealized_pnl=unrealized_pnl,
                highest_price=position.highest_price,
                lowest_price=position.lowest_price,
                max_drawdown=position.max_drawdown
            )

    async def update_all_unrealized_pnl(self, price_dict: Dict[str, Decimal]):
        """
        Update unrealized PnL for all positions.

        Args:
            price_dict: Dict of symbol -> current_price
        """
        positions = await self.get_all_open_positions()

        for position in positions:
            current_price = price_dict.get(position.symbol)

            if current_price:
                await self.update_unrealized_pnl(position.symbol, current_price)

    # ========================================================================
    # POSITION STATISTICS
    # ========================================================================

    async def get_total_unrealized_pnl(self) -> Decimal:
        """
        Get total unrealized PnL across all open positions.

        Returns:
            Total unrealized PnL
        """
        positions = await self.get_all_open_positions()
        total = sum(pos.unrealized_pnl for pos in positions)
        return Decimal(str(total))

    async def get_total_realized_pnl(self) -> Decimal:
        """
        Get total realized PnL across all positions (including closed).

        Returns:
            Total realized PnL
        """
        # This would need a database query to sum all positions
        # For now, approximate with open positions
        positions = await self.get_all_open_positions()
        total = sum(pos.realized_pnl for pos in positions)
        return Decimal(str(total))

    async def get_position_risk(self, symbol: str) -> Dict:
        """
        Get risk metrics for a position.

        Args:
            symbol: Symbol

        Returns:
            Dict with risk metrics
        """
        position = await self.get_position(symbol)

        if not position or not position.is_open:
            return {}

        # Get current price (would come from market data feed)
        # For now, use average price
        current_price = position.average_price

        # Calculate metrics
        unrealized_pnl = position.calculate_unrealized_pnl(current_price)
        pnl_pct = (unrealized_pnl / (position.average_price * abs(position.quantity))) * 100

        return {
            'symbol': position.symbol,
            'quantity': position.quantity,
            'average_price': float(position.average_price),
            'current_price': float(current_price),
            'unrealized_pnl': float(unrealized_pnl),
            'unrealized_pnl_pct': float(pnl_pct),
            'stop_loss': float(position.stop_loss) if position.stop_loss else None,
            'take_profit': float(position.take_profit) if position.take_profit else None,
            'max_drawdown': float(position.max_drawdown) if position.max_drawdown else None
        }

    # ========================================================================
    # FORCED UPDATES (for reconciliation)
    # ========================================================================

    async def force_update_quantity(
        self,
        symbol: str,
        exchange: str,
        quantity: int,
        reason: str
    ):
        """
        Force update position quantity (for reconciliation).

        Args:
            symbol: Symbol
            exchange: Exchange
            quantity: New quantity
            reason: Reason for force update
        """
        logger.warning(
            f"Force updating position quantity: {symbol} -> {quantity} "
            f"(reason: {reason})"
        )

        position = await self.get_position(symbol, exchange)

        if position:
            await self.db.update_position(
                position.id,
                quantity=quantity,
                metadata={
                    **position.metadata,
                    'force_updated': True,
                    'force_update_reason': reason,
                    'force_update_time': datetime.utcnow().isoformat()
                }
            )
        else:
            logger.error(f"Cannot force update non-existent position: {symbol}")

    async def force_close_position(
        self,
        symbol: str,
        exchange: str,
        reason: str
    ):
        """
        Force close position (for reconciliation).

        Args:
            symbol: Symbol
            exchange: Exchange
            reason: Reason for force close
        """
        logger.warning(
            f"Force closing position: {symbol} (reason: {reason})"
        )

        position = await self.get_position(symbol, exchange)

        if position:
            await self.db.close_position(
                position.id,
                realized_pnl=position.realized_pnl,  # No additional PnL
                exit_order_ids=[]  # No exit order
            )

            # Update metadata
            await self.db.update_position(
                position.id,
                metadata={
                    **position.metadata,
                    'force_closed': True,
                    'force_close_reason': reason,
                    'force_close_time': datetime.utcnow().isoformat()
                }
            )
        else:
            logger.error(f"Cannot force close non-existent position: {symbol}")
