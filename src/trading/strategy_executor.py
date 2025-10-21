"""
Strategy Executor
Executes trading strategies with integrated risk management
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable

from src.utils.logger import setup_logger
from src.database import get_session, Strategy, TradingSession, Trade
from .market_data import MarketDataHandler
from .order_manager import OrderManager
from .position_tracker import PositionTracker
from .risk_manager import RiskManager


class StrategyExecutor:
    """
    Executes trading strategies
    - Manages strategy lifecycle
    - Coordinates market data, orders, positions, and risk
    - Generates trading signals
    - Executes trades based on signals
    """

    def __init__(
        self,
        broker,
        strategy_config: Dict,
        risk_config: Dict,
        mode: str = 'paper'
    ):
        """
        Initialize Strategy Executor

        Args:
            broker: Broker instance
            strategy_config: Strategy configuration dict
            risk_config: Risk management configuration
            mode: 'paper' or 'live' trading mode
        """
        self.broker = broker
        self.strategy_config = strategy_config
        self.mode = mode
        self.logger = setup_logger('strategy_executor')

        # Extract strategy details
        self.strategy_name = strategy_config.get('name', 'unknown')
        self.strategy_type = strategy_config.get('strategy_type', 'custom')
        self.parameters = strategy_config.get('parameters', {})
        self.symbols = strategy_config.get('symbols', [])

        # Initialize components
        self.market_data = MarketDataHandler(broker, self.symbols)
        self.order_manager = OrderManager(broker, mode)
        self.position_tracker = PositionTracker(broker, self.market_data)
        self.risk_manager = RiskManager(risk_config)

        # Execution state
        self.running = False
        self.paused = False
        self.executor_thread = None
        self.stop_event = threading.Event()

        # Session tracking
        self.session_id = None
        self.session_start = None
        self.trades_count = 0

        # Signal callback
        self.signal_callback = None

        self.logger.info(
            f"StrategyExecutor initialized: {self.strategy_name} "
            f"in {mode} mode with {len(self.symbols)} symbols"
        )

    def start(self):
        """Start strategy execution"""
        if self.running:
            self.logger.warning("Strategy already running")
            return False

        try:
            # Create trading session
            self._create_session()

            # Start market data feed
            self.market_data.start_live_feed(callback=self._on_tick)

            # Start execution thread
            self.stop_event.clear()
            self.running = True
            self.paused = False

            self.executor_thread = threading.Thread(
                target=self._execution_loop,
                daemon=True
            )
            self.executor_thread.start()

            self.logger.info(f"Strategy '{self.strategy_name}' started")
            return True

        except Exception as e:
            self.logger.error(f"Error starting strategy: {e}")
            return False

    def stop(self):
        """Stop strategy execution"""
        if not self.running:
            self.logger.warning("Strategy not running")
            return False

        try:
            self.logger.info(f"Stopping strategy '{self.strategy_name}'...")

            # Stop execution loop
            self.stop_event.set()
            self.running = False

            # Wait for thread to finish
            if self.executor_thread:
                self.executor_thread.join(timeout=5)

            # Stop market data feed
            self.market_data.stop_live_feed()

            # Close session
            self._close_session()

            self.logger.info(f"Strategy '{self.strategy_name}' stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping strategy: {e}")
            return False

    def pause(self):
        """Pause strategy execution"""
        if not self.running:
            return False

        self.paused = True
        self.logger.info(f"Strategy '{self.strategy_name}' paused")
        return True

    def resume(self):
        """Resume strategy execution"""
        if not self.running or not self.paused:
            return False

        self.paused = False
        self.logger.info(f"Strategy '{self.strategy_name}' resumed")
        return True

    def emergency_stop(self):
        """
        Emergency stop - close all positions and stop strategy
        """
        try:
            self.logger.critical("EMERGENCY STOP triggered")

            # Cancel all pending orders
            self.order_manager.cancel_all_orders()

            # Close all positions
            self.position_tracker.close_all_positions()

            # Stop strategy
            self.stop()

            self.logger.info("Emergency stop completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            return False

    def _execution_loop(self):
        """Main execution loop running in separate thread"""
        self.logger.info("Execution loop started")

        try:
            while not self.stop_event.is_set():
                if self.paused:
                    time.sleep(1)
                    continue

                # Update positions with latest prices
                self.position_tracker.update_positions()

                # Update order statuses
                self.order_manager.update_order_statuses()

                # Generate and process signals
                self._process_signals()

                # Sleep interval (can be configurable)
                time.sleep(self.parameters.get('scan_interval', 5))

        except Exception as e:
            self.logger.error(f"Error in execution loop: {e}")

        finally:
            self.logger.info("Execution loop stopped")

    def _process_signals(self):
        """Process trading signals for all symbols"""
        try:
            for symbol_config in self.symbols:
                # Parse symbol
                if isinstance(symbol_config, dict):
                    symbol = symbol_config.get('symbol')
                    exchange = symbol_config.get('exchange', 'NSE')
                else:
                    symbol = symbol_config
                    exchange = 'NSE'

                # Generate signal
                signal = self._generate_signal(symbol, exchange)

                if signal:
                    self._execute_signal(signal)

        except Exception as e:
            self.logger.error(f"Error processing signals: {e}")

    def _generate_signal(self, symbol: str, exchange: str) -> Optional[Dict]:
        """
        Generate trading signal for a symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            Signal dict or None
        """
        try:
            # Get current quote
            quote = self.market_data.get_quote(symbol, exchange)
            if not quote:
                return None

            # Check if already have position
            has_position = self.position_tracker.has_position(symbol, exchange)

            # Strategy-specific signal generation
            signal = None

            if self.strategy_type == 'ema_crossover':
                signal = self._ema_crossover_signal(symbol, exchange, quote, has_position)
            elif self.strategy_type == 'rsi_strategy':
                signal = self._rsi_signal(symbol, exchange, quote, has_position)
            elif self.strategy_type == 'breakout':
                signal = self._breakout_signal(symbol, exchange, quote, has_position)
            else:
                # Custom strategy - call callback if provided
                if self.signal_callback:
                    signal = self.signal_callback(symbol, exchange, quote, has_position)

            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def _execute_signal(self, signal: Dict):
        """
        Execute a trading signal

        Args:
            signal: Signal dict with action, symbol, price, etc.
        """
        try:
            action = signal.get('action')  # BUY, SELL, CLOSE
            symbol = signal.get('symbol')
            exchange = signal.get('exchange', 'NSE')
            price = signal.get('price')
            stop_loss = signal.get('stop_loss')
            target = signal.get('target')

            self.logger.info(f"Executing signal: {action} {symbol} @ {price}")

            if action == 'CLOSE':
                # Close existing position
                self.position_tracker.close_position(symbol, exchange, price)
                return

            # Calculate position size
            if stop_loss:
                quantity, risk = self.risk_manager.calculate_position_size(
                    price, stop_loss, action
                )
            else:
                # Default quantity if no stop-loss
                quantity = signal.get('quantity', 1)
                risk = 0

            if quantity == 0:
                self.logger.warning(f"Position size calculated as 0, skipping signal")
                return

            # Validate trade with risk manager
            current_positions = self.position_tracker.get_position_count()
            allowed, reason = self.risk_manager.validate_trade(
                quantity, price, current_positions
            )

            if not allowed:
                self.logger.warning(f"Trade validation failed: {reason}")
                return

            # Place order
            order_response = self.order_manager.place_order(
                symbol=symbol,
                exchange=exchange,
                transaction_type=action,
                quantity=quantity,
                order_type='MARKET',
                product='MIS',
                strategy_name=self.strategy_name
            )

            if order_response:
                # Add position to tracker
                self.position_tracker.add_position(
                    symbol=symbol,
                    exchange=exchange,
                    side=action,
                    quantity=quantity,
                    entry_price=price,
                    stop_loss=stop_loss,
                    target=target,
                    strategy_name=self.strategy_name,
                    order_id=order_response.get('order_id')
                )

                self.trades_count += 1

                self.logger.info(
                    f"Trade executed: {action} {quantity} x {symbol} @ {price}"
                )

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")

    def _ema_crossover_signal(
        self, symbol: str, exchange: str, quote: Dict, has_position: bool
    ) -> Optional[Dict]:
        """
        Generate EMA crossover signal
        (Placeholder - would need historical data and EMA calculation)
        """
        # This is a placeholder - actual implementation would:
        # 1. Get historical data
        # 2. Calculate EMAs
        # 3. Check for crossover
        # 4. Generate signal
        return None

    def _rsi_signal(
        self, symbol: str, exchange: str, quote: Dict, has_position: bool
    ) -> Optional[Dict]:
        """
        Generate RSI-based signal
        (Placeholder - would need historical data and RSI calculation)
        """
        # Placeholder implementation
        return None

    def _breakout_signal(
        self, symbol: str, exchange: str, quote: Dict, has_position: bool
    ) -> Optional[Dict]:
        """
        Generate breakout signal
        (Placeholder - would need support/resistance levels)
        """
        # Placeholder implementation
        return None

    def set_signal_callback(self, callback: Callable):
        """
        Set custom signal generation callback

        Args:
            callback: Function(symbol, exchange, quote, has_position) -> signal_dict
        """
        self.signal_callback = callback
        self.logger.info("Custom signal callback registered")

    def _on_tick(self, tick_data):
        """
        Handle incoming tick data

        Args:
            tick_data: Tick data from market feed
        """
        # This is called for every tick
        # Can be used for very high-frequency strategies
        pass

    def _create_session(self):
        """Create a new trading session in database"""
        try:
            with get_session() as db_session:
                session = TradingSession(
                    session_name=f"{self.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    strategy_name=self.strategy_name,
                    mode=self.mode,
                    status='active',
                    starting_capital=self.risk_manager.starting_capital,
                    current_capital=self.risk_manager.current_capital,
                    config_snapshot=self.strategy_config
                )
                db_session.add(session)
                db_session.commit()

                self.session_id = session.id
                self.session_start = datetime.now()

                self.logger.info(f"Trading session created: {session.id}")

        except Exception as e:
            self.logger.error(f"Error creating session: {e}")

    def _close_session(self):
        """Close the current trading session"""
        try:
            if not self.session_id:
                return

            with get_session() as db_session:
                session = db_session.query(TradingSession).filter_by(
                    id=self.session_id
                ).first()

                if session:
                    session.status = 'completed'
                    session.end_time = datetime.now()
                    session.ending_capital = self.risk_manager.current_capital
                    session.total_trades = self.trades_count
                    session.total_pnl = self.position_tracker.total_pnl
                    session.realized_pnl = self.position_tracker.realized_pnl
                    session.unrealized_pnl = self.position_tracker.unrealized_pnl

                    # Calculate duration
                    if self.session_start:
                        duration = (datetime.now() - self.session_start).total_seconds()
                        session.duration_seconds = int(duration)

                    db_session.commit()

                    self.logger.info(f"Trading session closed: {session.id}")

        except Exception as e:
            self.logger.error(f"Error closing session: {e}")

    def get_summary(self) -> Dict:
        """
        Get summary of strategy executor status

        Returns:
            Dict with status information
        """
        return {
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type,
            'mode': self.mode,
            'running': self.running,
            'paused': self.paused,
            'session_id': self.session_id,
            'trades_count': self.trades_count,
            'symbols': self.symbols,
            'market_data': self.market_data.get_summary(),
            'orders': self.order_manager.get_summary(),
            'positions': self.position_tracker.get_summary(),
            'risk': self.risk_manager.get_summary()
        }

    def cleanup(self):
        """Cleanup all resources"""
        self.stop()
        self.market_data.cleanup()
        self.order_manager.cleanup()
        self.position_tracker.cleanup()
        self.logger.info("StrategyExecutor cleaned up")
