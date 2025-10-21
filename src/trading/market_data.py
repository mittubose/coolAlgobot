"""
Market Data Handler
Handles real-time and historical market data feeds
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from queue import Queue
import pandas as pd

from src.utils.logger import setup_logger


class MarketDataHandler:
    """
    Handles market data feeds from brokers
    - Real-time quote updates via WebSocket
    - Historical data fetching
    - Data caching and buffering
    - Event-driven callbacks for price updates
    """

    def __init__(self, broker, symbols: List[str] = None):
        """
        Initialize Market Data Handler

        Args:
            broker: Broker instance (must implement BaseBroker interface)
            symbols: List of symbols to track
        """
        self.broker = broker
        self.symbols = symbols or []
        self.logger = setup_logger('market_data')

        # Data storage
        self.quotes = {}  # Current quotes: {symbol: quote_data}
        self.ohlc_data = {}  # OHLC data: {symbol: {interval: DataFrame}}
        self.tick_data = {}  # Tick by tick data: {symbol: [ticks]}

        # WebSocket tracking
        self.ws_connected = False
        self.ws_thread = None
        self.ws_stop_event = threading.Event()

        # Callbacks
        self.quote_callbacks = []  # Called on every quote update
        self.tick_callbacks = []  # Called on every tick

        # Update queue for thread-safe updates
        self.update_queue = Queue()

        self.logger.info(f"MarketDataHandler initialized for {len(self.symbols)} symbols")

    def add_symbol(self, symbol: str, exchange: str = 'NSE'):
        """Add a symbol to track"""
        full_symbol = f"{exchange}:{symbol}"
        if full_symbol not in self.symbols:
            self.symbols.append(full_symbol)
            self.logger.info(f"Added symbol: {full_symbol}")

    def remove_symbol(self, symbol: str, exchange: str = 'NSE'):
        """Remove a symbol from tracking"""
        full_symbol = f"{exchange}:{symbol}"
        if full_symbol in self.symbols:
            self.symbols.remove(full_symbol)
            self.logger.info(f"Removed symbol: {full_symbol}")

    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict]:
        """
        Get current quote for a symbol

        Returns:
            Dict with quote data or None
        """
        try:
            quote = self.broker.get_quote(symbol, exchange)
            self.quotes[f"{exchange}:{symbol}"] = quote
            return quote
        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    def get_quotes(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """
        Get quotes for multiple symbols

        Args:
            symbols: List of symbols, if None uses self.symbols

        Returns:
            Dict mapping symbol to quote data
        """
        symbols_to_fetch = symbols or self.symbols
        quotes = {}

        try:
            for symbol in symbols_to_fetch:
                # Parse exchange:symbol format
                if ':' in symbol:
                    exchange, sym = symbol.split(':', 1)
                else:
                    exchange, sym = 'NSE', symbol

                quote = self.get_quote(sym, exchange)
                if quote:
                    quotes[symbol] = quote

            return quotes
        except Exception as e:
            self.logger.error(f"Error fetching multiple quotes: {e}")
            return quotes

    def get_historical_data(
        self,
        symbol: str,
        exchange: str = 'NSE',
        interval: str = '5minute',
        from_date: datetime = None,
        to_date: datetime = None,
        continuous: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data

        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Timeframe (minute, 5minute, 15minute, day, etc.)
            from_date: Start date
            to_date: End date
            continuous: Whether to fetch continuous data for futures

        Returns:
            DataFrame with OHLC data or None
        """
        try:
            # Default to last 30 days if dates not provided
            if not to_date:
                to_date = datetime.now()
            if not from_date:
                from_date = to_date - timedelta(days=30)

            self.logger.info(
                f"Fetching historical data for {symbol} "
                f"from {from_date} to {to_date}, interval: {interval}"
            )

            # Fetch from broker
            df = self.broker.get_historical_data(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                continuous=continuous
            )

            if df is not None and not df.empty:
                # Cache the data
                key = f"{exchange}:{symbol}"
                if key not in self.ohlc_data:
                    self.ohlc_data[key] = {}
                self.ohlc_data[key][interval] = df

                self.logger.info(f"Fetched {len(df)} candles for {symbol}")
                return df
            else:
                self.logger.warning(f"No historical data returned for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

    def start_live_feed(self, callback: Callable = None):
        """
        Start live market data feed via WebSocket

        Args:
            callback: Function to call on each tick (optional)
        """
        if self.ws_connected:
            self.logger.warning("Live feed already running")
            return

        if callback:
            self.add_tick_callback(callback)

        self.ws_stop_event.clear()
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()

        self.logger.info("Live market data feed started")

    def stop_live_feed(self):
        """Stop live market data feed"""
        if not self.ws_connected:
            self.logger.warning("Live feed not running")
            return

        self.ws_stop_event.set()

        if self.ws_thread:
            self.ws_thread.join(timeout=5)

        self.ws_connected = False
        self.logger.info("Live market data feed stopped")

    def _run_websocket(self):
        """Internal method to run WebSocket in a thread"""
        try:
            # Connect WebSocket
            self.broker.connect_websocket()
            self.ws_connected = True

            # Subscribe to symbols
            if self.symbols:
                self.broker.subscribe_symbols(self.symbols)

            # Set callback for incoming ticks
            def on_tick(ws, ticks):
                self._handle_tick_data(ticks)

            self.broker.set_websocket_callback('tick', on_tick)

            # Keep running until stop event
            while not self.ws_stop_event.is_set():
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            self.ws_connected = False

        finally:
            try:
                self.broker.disconnect_websocket()
            except:
                pass

    def _handle_tick_data(self, ticks):
        """
        Handle incoming tick data from WebSocket

        Args:
            ticks: List of tick data from broker
        """
        try:
            for tick in ticks:
                # Update quotes
                instrument_token = tick.get('instrument_token')
                symbol = tick.get('tradable', True) and tick.get('instrument_token')

                # Store tick
                if symbol:
                    if symbol not in self.tick_data:
                        self.tick_data[symbol] = []
                    self.tick_data[symbol].append(tick)

                    # Keep only last 1000 ticks per symbol
                    if len(self.tick_data[symbol]) > 1000:
                        self.tick_data[symbol] = self.tick_data[symbol][-1000:]

                # Update current quote
                self.quotes[symbol] = tick

                # Call registered callbacks
                for callback in self.tick_callbacks:
                    try:
                        callback(tick)
                    except Exception as e:
                        self.logger.error(f"Error in tick callback: {e}")

        except Exception as e:
            self.logger.error(f"Error handling tick data: {e}")

    def add_quote_callback(self, callback: Callable):
        """
        Add a callback function for quote updates

        Args:
            callback: Function(quote_data) to call on quote updates
        """
        if callback not in self.quote_callbacks:
            self.quote_callbacks.append(callback)

    def add_tick_callback(self, callback: Callable):
        """
        Add a callback function for tick updates

        Args:
            callback: Function(tick_data) to call on tick updates
        """
        if callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remove a callback function"""
        if callback in self.quote_callbacks:
            self.quote_callbacks.remove(callback)
        if callback in self.tick_callbacks:
            self.tick_callbacks.remove(callback)

    def get_cached_ohlc(
        self,
        symbol: str,
        exchange: str = 'NSE',
        interval: str = '5minute'
    ) -> Optional[pd.DataFrame]:
        """
        Get cached OHLC data

        Returns:
            Cached DataFrame or None
        """
        key = f"{exchange}:{symbol}"
        if key in self.ohlc_data and interval in self.ohlc_data[key]:
            return self.ohlc_data[key][interval]
        return None

    def get_last_price(self, symbol: str, exchange: str = 'NSE') -> Optional[float]:
        """
        Get last traded price for a symbol

        Returns:
            Last price or None
        """
        key = f"{exchange}:{symbol}"
        if key in self.quotes:
            return self.quotes[key].get('last_price')

        # Fetch fresh quote
        quote = self.get_quote(symbol, exchange)
        if quote:
            return quote.get('last_price')

        return None

    def is_market_open(self) -> bool:
        """
        Check if market is currently open

        Returns:
            True if market is open, False otherwise
        """
        # Simple implementation - can be enhanced
        now = datetime.now()
        weekday = now.weekday()

        # Monday = 0, Sunday = 6
        if weekday >= 5:  # Saturday or Sunday
            return False

        # Market hours: 9:15 AM to 3:30 PM
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def get_summary(self) -> Dict:
        """
        Get summary of market data handler status

        Returns:
            Dict with status information
        """
        return {
            'symbols_tracked': len(self.symbols),
            'symbols': self.symbols,
            'ws_connected': self.ws_connected,
            'cached_quotes': len(self.quotes),
            'cached_ohlc_datasets': sum(len(v) for v in self.ohlc_data.values()),
            'tick_data_symbols': len(self.tick_data),
            'callbacks_registered': len(self.quote_callbacks) + len(self.tick_callbacks),
            'market_open': self.is_market_open()
        }

    def cleanup(self):
        """Cleanup resources"""
        self.stop_live_feed()
        self.quotes.clear()
        self.ohlc_data.clear()
        self.tick_data.clear()
        self.quote_callbacks.clear()
        self.tick_callbacks.clear()
        self.logger.info("MarketDataHandler cleaned up")
