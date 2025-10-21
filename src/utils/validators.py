"""
Input Validation Utilities
Comprehensive validation helpers with detailed error messages
"""

from typing import Any, List, Optional, Union
from datetime import datetime, time as time_type
import re

from .exceptions import (
    ValidationError,
    InvalidSymbolError,
    InvalidQuantityError,
    InvalidPriceError,
    InvalidConfigError
)


class Validator:
    """Base validator class"""

    @staticmethod
    def validate_symbol(symbol: str, exchange: str = None) -> str:
        """
        Validate trading symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange name (NSE, BSE, etc.)

        Returns:
            Validated symbol (uppercase)

        Raises:
            InvalidSymbolError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidSymbolError(symbol if symbol else "None")

        symbol = symbol.strip().upper()

        # Basic validation
        if len(symbol) < 2 or len(symbol) > 20:
            raise InvalidSymbolError(symbol)

        # Symbol should only contain alphanumeric characters and hyphens
        if not re.match(r'^[A-Z0-9-]+$', symbol):
            raise InvalidSymbolError(symbol)

        return symbol

    @staticmethod
    def validate_exchange(exchange: str) -> str:
        """
        Validate exchange name

        Args:
            exchange: Exchange name

        Returns:
            Validated exchange (uppercase)

        Raises:
            ValidationError: If exchange is invalid
        """
        valid_exchanges = ['NSE', 'BSE', 'NFO', 'MCX', 'BFO', 'CDS']

        if not exchange or not isinstance(exchange, str):
            raise ValidationError("Exchange is required", field='exchange')

        exchange = exchange.strip().upper()

        if exchange not in valid_exchanges:
            raise ValidationError(
                f"Invalid exchange: {exchange}. Valid: {', '.join(valid_exchanges)}",
                field='exchange'
            )

        return exchange

    @staticmethod
    def validate_quantity(quantity: int, min_qty: int = 1, max_qty: int = None) -> int:
        """
        Validate order quantity

        Args:
            quantity: Order quantity
            min_qty: Minimum allowed quantity
            max_qty: Maximum allowed quantity

        Returns:
            Validated quantity

        Raises:
            InvalidQuantityError: If quantity is invalid
        """
        if not isinstance(quantity, int):
            raise InvalidQuantityError(quantity, min_qty, max_qty)

        if quantity < min_qty:
            raise InvalidQuantityError(quantity, min_qty, max_qty)

        if max_qty and quantity > max_qty:
            raise InvalidQuantityError(quantity, min_qty, max_qty)

        return quantity

    @staticmethod
    def validate_price(price: float, allow_zero: bool = False) -> float:
        """
        Validate price

        Args:
            price: Price value
            allow_zero: Whether to allow zero price (for market orders)

        Returns:
            Validated price

        Raises:
            InvalidPriceError: If price is invalid
        """
        if not isinstance(price, (int, float)):
            raise InvalidPriceError(price, "Price must be a number")

        if not allow_zero and price <= 0:
            raise InvalidPriceError(price, "Price must be greater than 0")

        if allow_zero and price < 0:
            raise InvalidPriceError(price, "Price cannot be negative")

        # Check for unrealistic prices
        if price > 1000000:
            raise InvalidPriceError(price, "Price seems unrealistic (> 10 lakh)")

        return float(price)

    @staticmethod
    def validate_order_type(order_type: str) -> str:
        """
        Validate order type

        Args:
            order_type: Order type

        Returns:
            Validated order type (uppercase)

        Raises:
            ValidationError: If order type is invalid
        """
        valid_types = ['MARKET', 'LIMIT', 'SL', 'SL-M', 'STOP_LOSS', 'STOP_LOSS_MARKET']

        if not order_type or not isinstance(order_type, str):
            raise ValidationError("Order type is required", field='order_type')

        order_type = order_type.strip().upper()

        if order_type not in valid_types:
            raise ValidationError(
                f"Invalid order type: {order_type}. Valid: {', '.join(valid_types)}",
                field='order_type'
            )

        return order_type

    @staticmethod
    def validate_transaction_type(transaction_type: str) -> str:
        """
        Validate transaction type (BUY/SELL)

        Args:
            transaction_type: Transaction type

        Returns:
            Validated transaction type (uppercase)

        Raises:
            ValidationError: If transaction type is invalid
        """
        valid_types = ['BUY', 'SELL']

        if not transaction_type or not isinstance(transaction_type, str):
            raise ValidationError("Transaction type is required", field='transaction_type')

        transaction_type = transaction_type.strip().upper()

        if transaction_type not in valid_types:
            raise ValidationError(
                f"Invalid transaction type: {transaction_type}. Valid: {', '.join(valid_types)}",
                field='transaction_type'
            )

        return transaction_type

    @staticmethod
    def validate_product_type(product: str) -> str:
        """
        Validate product type

        Args:
            product: Product type

        Returns:
            Validated product type (uppercase)

        Raises:
            ValidationError: If product type is invalid
        """
        valid_products = ['MIS', 'CNC', 'NRML', 'CO', 'BO']

        if not product or not isinstance(product, str):
            raise ValidationError("Product type is required", field='product')

        product = product.strip().upper()

        if product not in valid_products:
            raise ValidationError(
                f"Invalid product type: {product}. Valid: {', '.join(valid_products)}",
                field='product'
            )

        return product

    @staticmethod
    def validate_percentage(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """
        Validate percentage value

        Args:
            value: Percentage value
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated percentage

        Raises:
            ValidationError: If percentage is invalid
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Percentage must be a number, got {type(value)}", field='percentage')

        if value < min_val or value > max_val:
            raise ValidationError(
                f"Percentage must be between {min_val} and {max_val}, got {value}",
                field='percentage'
            )

        return float(value)

    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """
        Validate timeframe

        Args:
            timeframe: Timeframe string

        Returns:
            Validated timeframe

        Raises:
            ValidationError: If timeframe is invalid
        """
        valid_timeframes = [
            '1minute', '3minute', '5minute', '10minute', '15minute', '30minute',
            'hour', 'day', 'week', 'month',
            '1m', '3m', '5m', '10m', '15m', '30m', '1h', '1d', '1w', '1M'
        ]

        if not timeframe or not isinstance(timeframe, str):
            raise ValidationError("Timeframe is required", field='timeframe')

        timeframe = timeframe.strip().lower()

        if timeframe not in valid_timeframes:
            raise ValidationError(
                f"Invalid timeframe: {timeframe}",
                field='timeframe'
            )

        return timeframe

    @staticmethod
    def validate_date_range(from_date: datetime, to_date: datetime) -> tuple:
        """
        Validate date range

        Args:
            from_date: Start date
            to_date: End date

        Returns:
            Tuple of (from_date, to_date)

        Raises:
            ValidationError: If date range is invalid
        """
        if not isinstance(from_date, datetime):
            raise ValidationError("Invalid from_date type", field='from_date')

        if not isinstance(to_date, datetime):
            raise ValidationError("Invalid to_date type", field='to_date')

        if from_date > to_date:
            raise ValidationError(
                "from_date must be before to_date",
                field='date_range'
            )

        if to_date > datetime.now():
            raise ValidationError(
                "to_date cannot be in the future",
                field='to_date'
            )

        return from_date, to_date

    @staticmethod
    def validate_time(time_str: str, time_format: str = '%H:%M') -> time_type:
        """
        Validate time string

        Args:
            time_str: Time string
            time_format: Expected time format

        Returns:
            time object

        Raises:
            ValidationError: If time is invalid
        """
        if not isinstance(time_str, str):
            raise ValidationError("Time must be a string", field='time')

        try:
            time_obj = datetime.strptime(time_str, time_format).time()
            return time_obj
        except ValueError as e:
            raise ValidationError(
                f"Invalid time format. Expected {time_format}, got {time_str}",
                field='time'
            )

    @staticmethod
    def validate_risk_parameters(
        capital: float,
        risk_per_trade: float,
        max_positions: int,
        max_trades_per_day: int
    ) -> dict:
        """
        Validate risk management parameters

        Args:
            capital: Trading capital
            risk_per_trade: Risk percentage per trade
            max_positions: Maximum concurrent positions
            max_trades_per_day: Maximum trades per day

        Returns:
            Dict of validated parameters

        Raises:
            ValidationError: If any parameter is invalid
        """
        errors = {}

        # Validate capital
        if not isinstance(capital, (int, float)) or capital <= 0:
            errors['capital'] = "Capital must be a positive number"

        # Validate risk per trade
        if not isinstance(risk_per_trade, (int, float)) or risk_per_trade <= 0 or risk_per_trade > 10:
            errors['risk_per_trade'] = "Risk per trade must be between 0 and 10%"

        # Validate max positions
        if not isinstance(max_positions, int) or max_positions < 1 or max_positions > 20:
            errors['max_positions'] = "Max positions must be between 1 and 20"

        # Validate max trades per day
        if not isinstance(max_trades_per_day, int) or max_trades_per_day < 1 or max_trades_per_day > 500:
            errors['max_trades_per_day'] = "Max trades per day must be between 1 and 500"

        if errors:
            raise ValidationError(
                f"Risk parameter validation failed: {errors}",
                field='risk_parameters'
            )

        return {
            'capital': float(capital),
            'risk_per_trade': float(risk_per_trade),
            'max_positions': int(max_positions),
            'max_trades_per_day': int(max_trades_per_day)
        }

    @staticmethod
    def validate_strategy_config(config: dict, required_fields: List[str] = None) -> dict:
        """
        Validate strategy configuration

        Args:
            config: Strategy configuration dict
            required_fields: List of required field names

        Returns:
            Validated config

        Raises:
            InvalidConfigError: If config is invalid
        """
        if not isinstance(config, dict):
            raise InvalidConfigError("Strategy config must be a dictionary")

        if not config:
            raise InvalidConfigError("Strategy config cannot be empty")

        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise InvalidConfigError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    field='strategy_config'
                )

        return config

    @staticmethod
    def validate_broker_name(broker_name: str, supported_brokers: List[str] = None) -> str:
        """
        Validate broker name

        Args:
            broker_name: Broker name
            supported_brokers: List of supported broker names

        Returns:
            Validated broker name (lowercase)

        Raises:
            ValidationError: If broker is invalid
        """
        if not broker_name or not isinstance(broker_name, str):
            raise ValidationError("Broker name is required", field='broker_name')

        broker_name = broker_name.strip().lower()

        if supported_brokers and broker_name not in supported_brokers:
            raise ValidationError(
                f"Unsupported broker: {broker_name}. Supported: {', '.join(supported_brokers)}",
                field='broker_name'
            )

        return broker_name

    @staticmethod
    def validate_api_credentials(api_key: str, api_secret: str) -> tuple:
        """
        Validate API credentials

        Args:
            api_key: API key
            api_secret: API secret

        Returns:
            Tuple of (api_key, api_secret)

        Raises:
            ValidationError: If credentials are invalid
        """
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key is required", field='api_key')

        if not api_secret or not isinstance(api_secret, str):
            raise ValidationError("API secret is required", field='api_secret')

        api_key = api_key.strip()
        api_secret = api_secret.strip()

        if len(api_key) < 8:
            raise ValidationError("API key seems too short", field='api_key')

        if len(api_secret) < 8:
            raise ValidationError("API secret seems too short", field='api_secret')

        return api_key, api_secret

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address

        Args:
            email: Email address

        Returns:
            Validated email

        Raises:
            ValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required", field='email')

        email = email.strip().lower()

        # Basic email regex
        email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(f"Invalid email format: {email}", field='email')

        return email

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        Sanitize string input

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove leading/trailing whitespace
        value = value.strip()

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]

        return value


# Convenience functions
def validate_order_params(
    symbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    order_type: str = 'MARKET',
    price: float = None,
    product: str = 'MIS'
) -> dict:
    """
    Validate all order parameters at once

    Returns:
        Dict of validated parameters

    Raises:
        ValidationError: If any parameter is invalid
    """
    validator = Validator()

    validated = {
        'symbol': validator.validate_symbol(symbol, exchange),
        'exchange': validator.validate_exchange(exchange),
        'transaction_type': validator.validate_transaction_type(transaction_type),
        'quantity': validator.validate_quantity(quantity),
        'order_type': validator.validate_order_type(order_type),
        'product': validator.validate_product_type(product)
    }

    # Validate price if provided (required for LIMIT orders)
    if order_type in ['LIMIT', 'SL']:
        if price is None:
            raise ValidationError(f"{order_type} orders require a price", field='price')
        validated['price'] = validator.validate_price(price)
    elif price is not None:
        validated['price'] = validator.validate_price(price, allow_zero=True)

    return validated
