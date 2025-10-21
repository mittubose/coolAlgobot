"""
Position Tracker
Tracks open positions, calculates P&L, manages stop-loss and targets
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.logger import setup_logger
from src.database import get_session, Position, Trade


class PositionTracker:
    """
    Tracks and manages trading positions
    - Monitor open positions
    - Calculate real-time P&L
    - Track stop-loss and targets
    - Update position status
    """

    def __init__(self, broker, market_data_handler):
        """
        Initialize Position Tracker

        Args:
            broker: Broker instance
            market_data_handler: MarketDataHandler instance for live prices
        """
        self.broker = broker
        self.market_data = market_data_handler
        self.logger = setup_logger('position_tracker')

        # Position tracking
        self.positions = {}  # {symbol: position_data}

        # Thread safety
        self.lock = threading.Lock()

        # P&L tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.total_pnl = 0.0

        self.logger.info("PositionTracker initialized")

    def add_position(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        entry_price: float,
        stop_loss: float = None,
        target: float = None,
        strategy_name: str = None,
        order_id: str = None
    ) -> bool:
        """
        Add a new position

        Args:
            symbol: Trading symbol
            exchange: Exchange
            side: BUY or SELL
            quantity: Position size
            entry_price: Entry price
            stop_loss: Stop-loss price
            target: Target price
            strategy_name: Associated strategy
            order_id: Original order ID

        Returns:
            True if successful
        """
        try:
            key = f"{exchange}:{symbol}"

            with self.lock:
                # Check if position already exists
                if key in self.positions:
                    # Add to existing position
                    existing = self.positions[key]

                    if existing['side'] == side:
                        # Same direction - average the price
                        total_qty = existing['quantity'] + quantity
                        avg_price = (
                            (existing['entry_price'] * existing['quantity']) +
                            (entry_price * quantity)
                        ) / total_qty

                        existing['quantity'] = total_qty
                        existing['entry_price'] = avg_price
                        existing['updated_at'] = datetime.now()

                        self.logger.info(
                            f"Added to existing position {key}: "
                            f"{quantity} @ {entry_price}, new avg: {avg_price}"
                        )
                    else:
                        # Opposite direction - reduce or reverse position
                        if quantity >= existing['quantity']:
                            # Close and potentially reverse
                            closed_qty = existing['quantity']
                            remaining_qty = quantity - closed_qty

                            # Calculate P&L for closed portion
                            pnl = self._calculate_pnl(
                                existing['entry_price'],
                                entry_price,
                                closed_qty,
                                existing['side']
                            )
                            self.realized_pnl += pnl

                            if remaining_qty > 0:
                                # Reverse position
                                existing['side'] = side
                                existing['quantity'] = remaining_qty
                                existing['entry_price'] = entry_price
                            else:
                                # Position closed
                                del self.positions[key]
                                self._log_position_close(key, pnl)

                            self.logger.info(
                                f"Position {key} modified/closed, P&L: {pnl:.2f}"
                            )
                        else:
                            # Partial close
                            existing['quantity'] -= quantity

                            pnl = self._calculate_pnl(
                                existing['entry_price'],
                                entry_price,
                                quantity,
                                existing['side']
                            )
                            self.realized_pnl += pnl

                            self.logger.info(
                                f"Partially closed position {key}, P&L: {pnl:.2f}"
                            )
                else:
                    # New position
                    self.positions[key] = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'side': side,
                        'quantity': quantity,
                        'entry_price': entry_price,
                        'current_price': entry_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'strategy_name': strategy_name,
                        'order_id': order_id,
                        'unrealized_pnl': 0.0,
                        'opened_at': datetime.now(),
                        'updated_at': datetime.now()
                    }

                    # Save to database
                    self._save_position_to_db(self.positions[key])

                    self.logger.info(
                        f"New position opened: {key} {side} {quantity} @ {entry_price}"
                    )

                return True

        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False

    def update_positions(self):
        """Update current prices and P&L for all positions"""
        try:
            if not self.positions:
                return

            symbols_to_update = list(self.positions.keys())

            # Get current prices
            for key in symbols_to_update:
                position = self.positions[key]
                symbol = position['symbol']
                exchange = position['exchange']

                # Get current price
                current_price = self.market_data.get_last_price(symbol, exchange)

                if current_price:
                    with self.lock:
                        position['current_price'] = current_price

                        # Calculate unrealized P&L
                        pnl = self._calculate_pnl(
                            position['entry_price'],
                            current_price,
                            position['quantity'],
                            position['side']
                        )
                        position['unrealized_pnl'] = pnl
                        position['updated_at'] = datetime.now()

                        # Check stop-loss and target
                        self._check_exit_conditions(key, position)

            # Update total unrealized P&L
            self.unrealized_pnl = sum(
                pos['unrealized_pnl'] for pos in self.positions.values()
            )
            self.total_pnl = self.realized_pnl + self.unrealized_pnl

        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

    def _calculate_pnl(
        self,
        entry_price: float,
        exit_price: float,
        quantity: int,
        side: str
    ) -> float:
        """
        Calculate P&L

        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Position size
            side: BUY or SELL

        Returns:
            P&L amount
        """
        if side.upper() == 'BUY':
            return (exit_price - entry_price) * quantity
        else:  # SELL
            return (entry_price - exit_price) * quantity

    def _check_exit_conditions(self, key: str, position: Dict):
        """Check if stop-loss or target is hit"""
        current_price = position['current_price']
        stop_loss = position.get('stop_loss')
        target = position.get('target')
        side = position['side']

        exit_triggered = False
        exit_reason = None

        if side.upper() == 'BUY':
            # Long position
            if stop_loss and current_price <= stop_loss:
                exit_triggered = True
                exit_reason = 'stop_loss'
            elif target and current_price >= target:
                exit_triggered = True
                exit_reason = 'target'
        else:
            # Short position
            if stop_loss and current_price >= stop_loss:
                exit_triggered = True
                exit_reason = 'stop_loss'
            elif target and current_price <= target:
                exit_triggered = True
                exit_reason = 'target'

        if exit_triggered:
            self.logger.warning(
                f"Exit condition triggered for {key}: {exit_reason} at {current_price}"
            )
            # TODO: Trigger order to close position
            # This should be handled by the strategy executor or order manager

    def close_position(
        self,
        symbol: str,
        exchange: str,
        exit_price: float = None
    ) -> Optional[float]:
        """
        Close a position

        Args:
            symbol: Trading symbol
            exchange: Exchange
            exit_price: Exit price (if None, uses current price)

        Returns:
            Realized P&L or None
        """
        try:
            key = f"{exchange}:{symbol}"

            if key not in self.positions:
                self.logger.error(f"Position {key} not found")
                return None

            position = self.positions[key]

            # Get exit price
            if exit_price is None:
                exit_price = self.market_data.get_last_price(symbol, exchange)

            if exit_price is None:
                self.logger.error(f"Cannot close position {key}: no exit price")
                return None

            # Calculate P&L
            pnl = self._calculate_pnl(
                position['entry_price'],
                exit_price,
                position['quantity'],
                position['side']
            )

            self.realized_pnl += pnl

            # Remove position
            with self.lock:
                del self.positions[key]

            # Log to database
            self._log_position_close(key, pnl, exit_price)

            self.logger.info(
                f"Position {key} closed at {exit_price}, P&L: {pnl:.2f}"
            )

            return pnl

        except Exception as e:
            self.logger.error(f"Error closing position {key}: {e}")
            return None

    def close_all_positions(self) -> float:
        """
        Close all open positions

        Returns:
            Total realized P&L from closures
        """
        total_pnl = 0.0

        for key in list(self.positions.keys()):
            position = self.positions[key]
            pnl = self.close_position(position['symbol'], position['exchange'])
            if pnl is not None:
                total_pnl += pnl

        self.logger.info(f"All positions closed, total P&L: {total_pnl:.2f}")
        return total_pnl

    def get_position(self, symbol: str, exchange: str) -> Optional[Dict]:
        """
        Get position data

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            Position dict or None
        """
        key = f"{exchange}:{symbol}"
        return self.positions.get(key)

    def get_all_positions(self) -> List[Dict]:
        """Get all open positions"""
        return list(self.positions.values())

    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)

    def has_position(self, symbol: str, exchange: str) -> bool:
        """Check if position exists"""
        key = f"{exchange}:{symbol}"
        return key in self.positions

    def get_total_exposure(self) -> float:
        """
        Get total capital exposure

        Returns:
            Total exposure amount
        """
        total = 0.0
        for position in self.positions.values():
            exposure = position['entry_price'] * position['quantity']
            total += exposure
        return total

    def _save_position_to_db(self, position: Dict):
        """Save position to database"""
        try:
            with get_session() as session:
                db_position = Position(
                    symbol=position['symbol'],
                    exchange=position['exchange'],
                    side=position['side'],
                    quantity=position['quantity'],
                    average_price=position['entry_price'],
                    last_price=position['current_price'],
                    unrealized_pnl=position['unrealized_pnl'],
                    stop_loss=position.get('stop_loss'),
                    target=position.get('target'),
                    strategy_name=position.get('strategy_name')
                )
                session.add(db_position)
                session.commit()

        except Exception as e:
            self.logger.error(f"Error saving position to database: {e}")

    def _log_position_close(self, key: str, pnl: float, exit_price: float = None):
        """Log position closure to database"""
        try:
            # Update Position table
            # Update Trade table
            # This would update the relevant database records
            pass

        except Exception as e:
            self.logger.error(f"Error logging position close: {e}")

    def get_summary(self) -> Dict:
        """
        Get summary of position tracker status

        Returns:
            Dict with status information
        """
        positions_by_side = {'BUY': 0, 'SELL': 0}
        for pos in self.positions.values():
            positions_by_side[pos['side']] = positions_by_side.get(pos['side'], 0) + 1

        return {
            'total_positions': len(self.positions),
            'positions_by_side': positions_by_side,
            'realized_pnl': round(self.realized_pnl, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'total_pnl': round(self.total_pnl, 2),
            'total_exposure': round(self.get_total_exposure(), 2),
            'positions': self.get_all_positions()
        }

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("PositionTracker cleaned up")
