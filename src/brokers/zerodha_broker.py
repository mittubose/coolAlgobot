"""
Zerodha Kite Connect Broker Implementation
Complete implementation of BaseBroker for Zerodha
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

from .base_broker import BaseBroker
from ..utils.error_handler import handle_exceptions, retry_on_error
from ..utils.exceptions import (
    BrokerAuthenticationError,
    BrokerAPIError,
    BrokerConnectionError,
    TokenExpiredError,
    OrderPlacementError,
    MarketDataError
)
from ..utils.validators import validate_order_params


class ZerodhaBroker(BaseBroker):
    """Zerodha Kite Connect implementation of BaseBroker"""

    def __init__(self, api_key: str, api_secret: str, redirect_url: str = None):
        """
        Initialize Zerodha broker

        Args:
            api_key: Kite Connect API key
            api_secret: Kite Connect API secret
            redirect_url: OAuth redirect URL
        """
        super().__init__(api_key, api_secret)
        self.broker_name = "Zerodha"
        self.redirect_url = redirect_url or "http://localhost:8080/callback"
        self.kite = KiteConnect(api_key=self.api_key)
        self.logger = logging.getLogger('zerodha')
        self.websocket = None

    # ==================== Authentication Methods ====================

    def get_login_url(self) -> str:
        """Generate Zerodha login URL"""
        login_url = self.kite.login_url()
        self.logger.info(f"Login URL generated: {login_url}")
        return login_url

    @handle_exceptions(context="Generate Zerodha session", notify=True, raise_error=True)
    def generate_session(self, request_token: str) -> Dict[str, Any]:
        """
        Generate access token from request token

        Args:
            request_token: Request token from OAuth callback

        Returns:
            Session data with access token and user info

        Raises:
            BrokerAuthenticationError: If authentication fails
        """
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.user_id = data.get("user_id")
            self.kite.set_access_token(self.access_token)
            self.authenticated = True

            # Save token to file
            self.save_access_token(self.access_token)

            self.logger.info(f"Session generated successfully for user: {self.user_id}")
            return data

        except KiteException as e:
            raise BrokerAuthenticationError(
                f"Zerodha authentication failed: {str(e)}",
                broker_name="Zerodha"
            )
        except Exception as e:
            raise BrokerAuthenticationError(
                f"Unexpected error during authentication: {str(e)}",
                broker_name="Zerodha"
            )

    def verify_token(self) -> bool:
        """Verify if access token is valid"""
        try:
            profile = self.kite.profile()
            self.user_id = profile.get('user_id')
            self.authenticated = True
            self.logger.info(f"Token verified. User: {profile.get('user_name')}")
            return True
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            self.authenticated = False
            return False

    def load_access_token(self) -> bool:
        """Load access token from file"""
        token_file = Path("config/.access_token")

        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    token = f.read().strip()

                if token:
                    self.access_token = token
                    self.kite.set_access_token(token)
                    self.logger.info("Access token loaded from file")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to load access token: {e}")

        return False

    def save_access_token(self, token: str) -> bool:
        """Save access token to file"""
        token_file = Path("config/.access_token")

        try:
            token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, 'w') as f:
                f.write(token)
            self.logger.info("Access token saved to file")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save access token: {e}")
            return False

    # ==================== Market Data Methods ====================

    @retry_on_error(max_retries=3, delay=1, exceptions=(KiteException,), context="Get market quote")
    @handle_exceptions(context="Get market quote", raise_error=True)
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            exchange: Exchange name (NSE, BSE, NFO, etc.)

        Returns:
            Quote data with last_price, volume, ohlc, etc.

        Raises:
            MarketDataError: If unable to fetch quote
        """
        try:
            instrument = f"{exchange}:{symbol}"
            quote = self.kite.quote(instrument)
            return quote.get(instrument, {})
        except KiteException as e:
            raise MarketDataError(
                f"Failed to fetch quote for {symbol}: {str(e)}",
                symbol=symbol
            )
        except Exception as e:
            raise MarketDataError(
                f"Unexpected error fetching quote for {symbol}: {str(e)}",
                symbol=symbol
            )

    def get_historical_data(
        self,
        symbol: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "5minute",
        exchange: str = "NSE"
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV data

        Args:
            symbol: Trading symbol
            from_date: Start date
            to_date: End date
            interval: Time interval (minute, 5minute, day, etc.)
            exchange: Exchange name

        Returns:
            List of OHLCV candles
        """
        try:
            # Get instrument token
            instruments = self.kite.instruments(exchange)
            instrument_token = None

            for inst in instruments:
                if inst['tradingsymbol'] == symbol:
                    instrument_token = inst['instrument_token']
                    break

            if not instrument_token:
                raise ValueError(f"Instrument not found: {symbol}")

            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token,
                from_date,
                to_date,
                interval
            )

            return data

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise

    # ==================== Order Management Methods ====================

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        product: str = "MIS",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        validity: str = "DAY"
    ) -> Dict[str, Any]:
        """
        Place a new order

        Args:
            symbol: Trading symbol
            exchange: Exchange name
            transaction_type: BUY or SELL
            quantity: Number of shares
            order_type: MARKET or LIMIT
            product: MIS (intraday) or CNC (delivery)
            price: Limit price (required for LIMIT orders)
            trigger_price: Stop-loss trigger price
            validity: Order validity (DAY, IOC)

        Returns:
            Order response with order_id
        """
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product=product,
                price=price,
                trigger_price=trigger_price,
                validity=validity
            )

            self.logger.info(f"Order placed: {order_id} - {transaction_type} {quantity} {symbol}")
            return {"order_id": order_id, "status": "success"}

        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            raise

    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Modify an existing order"""
        try:
            result = self.kite.modify_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                order_type=order_type
            )

            self.logger.info(f"Order modified: {order_id}")
            return {"order_id": order_id, "status": "success", "result": result}

        except Exception as e:
            self.logger.error(f"Failed to modify order: {e}")
            raise

    def cancel_order(self, order_id: str, variety: str = "regular") -> Dict[str, Any]:
        """Cancel an order"""
        try:
            result = self.kite.cancel_order(
                variety=variety,
                order_id=order_id
            )

            self.logger.info(f"Order cancelled: {order_id}")
            return {"order_id": order_id, "status": "cancelled", "result": result}

        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            raise

    # ==================== Position & Holdings Methods ====================

    def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current open positions"""
        try:
            positions = self.kite.positions()
            return positions
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            raise

    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get current holdings"""
        try:
            holdings = self.kite.holdings()
            return holdings
        except Exception as e:
            self.logger.error(f"Failed to get holdings: {e}")
            raise

    # ==================== Account & Funds Methods ====================

    def get_margins(self) -> Dict[str, Any]:
        """Get account margin information"""
        try:
            margins = self.kite.margins()
            return margins
        except Exception as e:
            self.logger.error(f"Failed to get margins: {e}")
            raise

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            profile = self.kite.profile()
            return profile
        except Exception as e:
            self.logger.error(f"Failed to get profile: {e}")
            raise

    # ==================== Order Book Methods ====================

    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders for the day"""
        try:
            orders = self.kite.orders()
            return orders
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            raise

    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get order history for a specific order"""
        try:
            history = self.kite.order_history(order_id)
            return history
        except Exception as e:
            self.logger.error(f"Failed to get order history: {e}")
            raise

    def get_trades(self) -> List[Dict[str, Any]]:
        """Get all executed trades for the day"""
        try:
            trades = self.kite.trades()
            return trades
        except Exception as e:
            self.logger.error(f"Failed to get trades: {e}")
            raise

    # ==================== WebSocket Methods ====================

    def connect_websocket(self, on_tick_callback, on_connect_callback=None, on_close_callback=None):
        """
        Connect to Zerodha WebSocket for live data

        Args:
            on_tick_callback: Callback function for tick data
            on_connect_callback: Callback on connection
            on_close_callback: Callback on disconnection
        """
        try:
            from kiteconnect import KiteTicker

            self.websocket = KiteTicker(self.api_key, self.access_token)

            if on_connect_callback:
                self.websocket.on_connect = on_connect_callback

            if on_close_callback:
                self.websocket.on_close = on_close_callback

            self.websocket.on_ticks = on_tick_callback

            # Start WebSocket in background thread
            self.websocket.connect(threaded=True)

            self.logger.info("WebSocket connected")

        except Exception as e:
            self.logger.error(f"Failed to connect WebSocket: {e}")
            raise

    def subscribe_symbols(self, symbols: List[str], mode: str = "quote"):
        """
        Subscribe to symbols for live data

        Args:
            symbols: List of instrument tokens
            mode: Data mode (ltp, quote, full)
        """
        if not self.websocket:
            raise ValueError("WebSocket not connected. Call connect_websocket first.")

        try:
            mode_map = {
                "ltp": self.websocket.MODE_LTP,
                "quote": self.websocket.MODE_QUOTE,
                "full": self.websocket.MODE_FULL
            }

            self.websocket.subscribe(symbols)
            self.websocket.set_mode(mode_map.get(mode, self.websocket.MODE_QUOTE), symbols)

            self.logger.info(f"Subscribed to {len(symbols)} symbols in {mode} mode")

        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
            raise

    def unsubscribe_symbols(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        if not self.websocket:
            raise ValueError("WebSocket not connected")

        try:
            self.websocket.unsubscribe(symbols)
            self.logger.info(f"Unsubscribed from {len(symbols)} symbols")
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe: {e}")
            raise

    # ==================== Helper Methods ====================

    def interactive_login(self) -> 'ZerodhaBroker':
        """
        Interactive login flow for CLI usage

        Returns:
            Authenticated broker instance
        """
        # Try to load existing token
        if self.load_access_token():
            if self.verify_token():
                self.logger.info("Using existing access token")
                return self

        # Generate new token
        print("\n" + "="*60)
        print("ZERODHA KITE CONNECT AUTHENTICATION")
        print("="*60)
        print(f"\n1. Open this URL in your browser:")
        print(f"\n   {self.get_login_url()}\n")
        print("2. Login with your Zerodha credentials")
        print("3. After login, you'll be redirected to a URL")
        print("4. Copy the 'request_token' parameter from that URL")
        print("\n" + "="*60 + "\n")

        request_token = input("Enter request token: ").strip()

        if not request_token:
            raise ValueError("Request token is required")

        # Generate session
        self.generate_session(request_token)

        print("\n✅ Authentication successful!")
        print("="*60 + "\n")

        return self

    def get_kite_instance(self) -> KiteConnect:
        """Get authenticated KiteConnect instance"""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")
        return self.kite
