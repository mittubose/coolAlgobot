"""
Base Broker Class
Abstract base class for all broker integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class BaseBroker(ABC):
    """
    Abstract base class for broker integrations.
    All broker implementations must inherit from this class.
    """

    def __init__(self, api_key: str, api_secret: str, **kwargs):
        """
        Initialize broker connection

        Args:
            api_key: Broker API key
            api_secret: Broker API secret
            **kwargs: Additional broker-specific parameters
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.user_id = None
        self.authenticated = False
        self.broker_name = "Unknown"

    # ==================== Authentication Methods ====================

    @abstractmethod
    def get_login_url(self) -> str:
        """
        Generate broker login URL for OAuth2 flow

        Returns:
            Login URL string
        """
        pass

    @abstractmethod
    def generate_session(self, request_token: str) -> Dict[str, Any]:
        """
        Generate access token from request token

        Args:
            request_token: Request token from OAuth callback

        Returns:
            Session data dictionary with access_token, user info, etc.
        """
        pass

    @abstractmethod
    def verify_token(self) -> bool:
        """
        Verify if current access token is valid

        Returns:
            True if token is valid, False otherwise
        """
        pass

    def load_access_token(self) -> bool:
        """
        Load saved access token from file

        Returns:
            True if token loaded successfully, False otherwise
        """
        pass

    def save_access_token(self, token: str) -> bool:
        """
        Save access token to file

        Args:
            token: Access token to save

        Returns:
            True if saved successfully
        """
        pass

    # ==================== Market Data Methods ====================

    @abstractmethod
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            exchange: Exchange name (NSE, BSE, NFO, etc.)

        Returns:
            Quote data with last_price, volume, ohlc, etc.
        """
        pass

    @abstractmethod
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
        pass

    # ==================== Order Management Methods ====================

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,  # BUY or SELL
        quantity: int,
        order_type: str = "MARKET",  # MARKET or LIMIT
        product: str = "MIS",  # MIS (intraday) or CNC (delivery)
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
        pass

    @abstractmethod
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Modify an existing order

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New limit price
            trigger_price: New trigger price
            order_type: New order type

        Returns:
            Modification response
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, variety: str = "regular") -> Dict[str, Any]:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel
            variety: Order variety (regular, amo, co, etc.)

        Returns:
            Cancellation response
        """
        pass

    # ==================== Position & Holdings Methods ====================

    @abstractmethod
    def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get current open positions

        Returns:
            Dictionary with 'net' and 'day' position lists
        """
        pass

    @abstractmethod
    def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Get current holdings (delivery positions)

        Returns:
            List of holdings
        """
        pass

    # ==================== Account & Funds Methods ====================

    @abstractmethod
    def get_margins(self) -> Dict[str, Any]:
        """
        Get account margin and balance information

        Returns:
            Margin data with available balance, used margin, etc.
        """
        pass

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile information

        Returns:
            User profile with name, email, broker details
        """
        pass

    # ==================== Order Book Methods ====================

    @abstractmethod
    def get_orders(self) -> List[Dict[str, Any]]:
        """
        Get all orders for the day

        Returns:
            List of orders
        """
        pass

    @abstractmethod
    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get order history for a specific order

        Args:
            order_id: Order ID

        Returns:
            List of order updates/history
        """
        pass

    @abstractmethod
    def get_trades(self) -> List[Dict[str, Any]]:
        """
        Get all executed trades for the day

        Returns:
            List of trades
        """
        pass

    # ==================== WebSocket Methods ====================

    @abstractmethod
    def connect_websocket(self, on_tick_callback, on_connect_callback=None, on_close_callback=None):
        """
        Connect to broker's WebSocket for live data

        Args:
            on_tick_callback: Callback function for tick data
            on_connect_callback: Callback on connection
            on_close_callback: Callback on disconnection
        """
        pass

    @abstractmethod
    def subscribe_symbols(self, symbols: List[str], mode: str = "quote"):
        """
        Subscribe to symbols for live data

        Args:
            symbols: List of instrument tokens or symbols
            mode: Data mode (ltp, quote, full)
        """
        pass

    @abstractmethod
    def unsubscribe_symbols(self, symbols: List[str]):
        """
        Unsubscribe from symbols

        Args:
            symbols: List of instrument tokens or symbols
        """
        pass

    # ==================== Utility Methods ====================

    def get_broker_name(self) -> str:
        """Get broker name"""
        return self.broker_name

    def is_authenticated(self) -> bool:
        """Check if broker is authenticated"""
        return self.authenticated

    def logout(self):
        """Logout and clear session"""
        self.access_token = None
        self.authenticated = False
        self.user_id = None

    def __repr__(self):
        return f"<{self.broker_name}Broker(authenticated={self.authenticated}, user_id={self.user_id})>"
