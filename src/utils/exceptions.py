"""
Custom Exception Classes
Comprehensive error types for better error handling and debugging
"""


class ScalpingBotError(Exception):
    """Base exception for all scalping bot errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or 'GENERAL_ERROR'
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


# ==================== Broker Errors ====================

class BrokerError(ScalpingBotError):
    """Base class for broker-related errors"""
    def __init__(self, message: str, broker_name: str = None, **kwargs):
        super().__init__(message, error_code='BROKER_ERROR', **kwargs)
        self.broker_name = broker_name
        self.details['broker'] = broker_name


class BrokerAuthenticationError(BrokerError):
    """Broker authentication failed"""
    def __init__(self, message: str, broker_name: str = None):
        super().__init__(
            message,
            broker_name=broker_name
        )
        self.error_code = 'BROKER_AUTH_ERROR'


class BrokerConnectionError(BrokerError):
    """Failed to connect to broker"""
    def __init__(self, message: str, broker_name: str = None):
        super().__init__(message, broker_name=broker_name)
        self.error_code = 'BROKER_CONNECTION_ERROR'


class BrokerAPIError(BrokerError):
    """Broker API returned an error"""
    def __init__(self, message: str, broker_name: str = None, status_code: int = None, response: dict = None):
        super().__init__(message, broker_name=broker_name)
        self.error_code = 'BROKER_API_ERROR'
        self.status_code = status_code
        self.details['status_code'] = status_code
        self.details['response'] = response


class BrokerNotSupportedError(BrokerError):
    """Broker is not supported"""
    def __init__(self, broker_name: str, supported_brokers: list = None):
        message = f"Broker '{broker_name}' is not supported"
        if supported_brokers:
            message += f". Supported brokers: {', '.join(supported_brokers)}"
        super().__init__(message, broker_name=broker_name)
        self.error_code = 'BROKER_NOT_SUPPORTED'
        self.details['supported_brokers'] = supported_brokers


class InvalidCredentialsError(BrokerError):
    """Invalid API credentials"""
    def __init__(self, message: str = "Invalid API credentials", broker_name: str = None):
        super().__init__(message, broker_name=broker_name)
        self.error_code = 'INVALID_CREDENTIALS'


class TokenExpiredError(BrokerError):
    """Authentication token expired"""
    def __init__(self, message: str = "Authentication token has expired", broker_name: str = None):
        super().__init__(message, broker_name=broker_name)
        self.error_code = 'TOKEN_EXPIRED'


# ==================== Trading Errors ====================

class TradingError(ScalpingBotError):
    """Base class for trading-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='TRADING_ERROR', **kwargs)


class OrderPlacementError(TradingError):
    """Failed to place order"""
    def __init__(self, message: str, symbol: str = None, order_details: dict = None):
        super().__init__(message)
        self.error_code = 'ORDER_PLACEMENT_ERROR'
        self.details['symbol'] = symbol
        self.details['order_details'] = order_details


class OrderModificationError(TradingError):
    """Failed to modify order"""
    def __init__(self, message: str, order_id: str = None):
        super().__init__(message)
        self.error_code = 'ORDER_MODIFICATION_ERROR'
        self.details['order_id'] = order_id


class OrderCancellationError(TradingError):
    """Failed to cancel order"""
    def __init__(self, message: str, order_id: str = None):
        super().__init__(message)
        self.error_code = 'ORDER_CANCELLATION_ERROR'
        self.details['order_id'] = order_id


class InsufficientFundsError(TradingError):
    """Insufficient funds to place order"""
    def __init__(self, required: float, available: float):
        message = f"Insufficient funds. Required: ₹{required:,.2f}, Available: ₹{available:,.2f}"
        super().__init__(message)
        self.error_code = 'INSUFFICIENT_FUNDS'
        self.details['required'] = required
        self.details['available'] = available


class PositionNotFoundError(TradingError):
    """Position not found"""
    def __init__(self, symbol: str):
        super().__init__(f"Position not found for symbol: {symbol}")
        self.error_code = 'POSITION_NOT_FOUND'
        self.details['symbol'] = symbol


class RiskLimitExceededError(TradingError):
    """Risk limit exceeded"""
    def __init__(self, limit_type: str, limit_value: float, current_value: float):
        message = f"{limit_type} exceeded. Limit: {limit_value}, Current: {current_value}"
        super().__init__(message)
        self.error_code = 'RISK_LIMIT_EXCEEDED'
        self.details['limit_type'] = limit_type
        self.details['limit_value'] = limit_value
        self.details['current_value'] = current_value


class MaxPositionsExceededError(TradingError):
    """Maximum number of positions exceeded"""
    def __init__(self, max_positions: int, current_positions: int):
        message = f"Maximum positions exceeded. Max: {max_positions}, Current: {current_positions}"
        super().__init__(message)
        self.error_code = 'MAX_POSITIONS_EXCEEDED'
        self.details['max_positions'] = max_positions
        self.details['current_positions'] = current_positions


class MaxTradesExceededError(TradingError):
    """Maximum daily trades exceeded"""
    def __init__(self, max_trades: int, current_trades: int):
        message = f"Maximum daily trades exceeded. Max: {max_trades}, Today: {current_trades}"
        super().__init__(message)
        self.error_code = 'MAX_TRADES_EXCEEDED'
        self.details['max_trades'] = max_trades
        self.details['current_trades'] = current_trades


class CircuitBreakerTriggeredError(TradingError):
    """Circuit breaker triggered"""
    def __init__(self, reason: str, consecutive_losses: int = None):
        message = f"Circuit breaker triggered: {reason}"
        super().__init__(message)
        self.error_code = 'CIRCUIT_BREAKER_TRIGGERED'
        self.details['reason'] = reason
        self.details['consecutive_losses'] = consecutive_losses


# ==================== Strategy Errors ====================

class StrategyError(ScalpingBotError):
    """Base class for strategy-related errors"""
    def __init__(self, message: str, strategy_name: str = None, **kwargs):
        super().__init__(message, error_code='STRATEGY_ERROR', **kwargs)
        self.strategy_name = strategy_name
        self.details['strategy'] = strategy_name


class StrategyNotFoundError(StrategyError):
    """Strategy not found"""
    def __init__(self, strategy_name: str):
        super().__init__(f"Strategy '{strategy_name}' not found", strategy_name=strategy_name)
        self.error_code = 'STRATEGY_NOT_FOUND'


class StrategyConfigError(StrategyError):
    """Invalid strategy configuration"""
    def __init__(self, message: str, strategy_name: str = None, config_errors: dict = None):
        super().__init__(message, strategy_name=strategy_name)
        self.error_code = 'STRATEGY_CONFIG_ERROR'
        self.details['config_errors'] = config_errors


class StrategyExecutionError(StrategyError):
    """Strategy execution failed"""
    def __init__(self, message: str, strategy_name: str = None, exception: Exception = None):
        super().__init__(message, strategy_name=strategy_name)
        self.error_code = 'STRATEGY_EXECUTION_ERROR'
        self.details['exception'] = str(exception) if exception else None


class BacktestError(StrategyError):
    """Backtesting failed"""
    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(message, strategy_name=strategy_name)
        self.error_code = 'BACKTEST_ERROR'


# ==================== Data Errors ====================

class DataError(ScalpingBotError):
    """Base class for data-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='DATA_ERROR', **kwargs)


class MarketDataError(DataError):
    """Failed to fetch market data"""
    def __init__(self, message: str, symbol: str = None):
        super().__init__(message)
        self.error_code = 'MARKET_DATA_ERROR'
        self.details['symbol'] = symbol


class HistoricalDataError(DataError):
    """Failed to fetch historical data"""
    def __init__(self, message: str, symbol: str = None, from_date: str = None, to_date: str = None):
        super().__init__(message)
        self.error_code = 'HISTORICAL_DATA_ERROR'
        self.details['symbol'] = symbol
        self.details['from_date'] = from_date
        self.details['to_date'] = to_date


class DataValidationError(DataError):
    """Data validation failed"""
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message)
        self.error_code = 'DATA_VALIDATION_ERROR'
        self.details['field'] = field
        self.details['value'] = str(value) if value else None


# ==================== Database Errors ====================

class DatabaseError(ScalpingBotError):
    """Base class for database errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='DATABASE_ERROR', **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Failed to connect to database"""
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message)
        self.error_code = 'DATABASE_CONNECTION_ERROR'


class RecordNotFoundError(DatabaseError):
    """Database record not found"""
    def __init__(self, model: str, record_id: any = None):
        message = f"{model} not found"
        if record_id:
            message += f" (ID: {record_id})"
        super().__init__(message)
        self.error_code = 'RECORD_NOT_FOUND'
        self.details['model'] = model
        self.details['record_id'] = record_id


class DatabaseIntegrityError(DatabaseError):
    """Database integrity constraint violation"""
    def __init__(self, message: str, constraint: str = None):
        super().__init__(message)
        self.error_code = 'DATABASE_INTEGRITY_ERROR'
        self.details['constraint'] = constraint


# ==================== Configuration Errors ====================

class ConfigurationError(ScalpingBotError):
    """Base class for configuration errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='CONFIGURATION_ERROR', **kwargs)


class ConfigFileNotFoundError(ConfigurationError):
    """Configuration file not found"""
    def __init__(self, file_path: str):
        super().__init__(f"Configuration file not found: {file_path}")
        self.error_code = 'CONFIG_FILE_NOT_FOUND'
        self.details['file_path'] = file_path


class InvalidConfigError(ConfigurationError):
    """Invalid configuration"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.error_code = 'INVALID_CONFIG'
        self.details['field'] = field


class MissingConfigError(ConfigurationError):
    """Required configuration missing"""
    def __init__(self, field: str):
        super().__init__(f"Required configuration missing: {field}")
        self.error_code = 'MISSING_CONFIG'
        self.details['field'] = field


# ==================== Validation Errors ====================

class ValidationError(ScalpingBotError):
    """Base class for validation errors"""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, error_code='VALIDATION_ERROR', **kwargs)
        self.field = field
        self.details['field'] = field


class InvalidSymbolError(ValidationError):
    """Invalid trading symbol"""
    def __init__(self, symbol: str):
        super().__init__(f"Invalid symbol: {symbol}", field='symbol')
        self.error_code = 'INVALID_SYMBOL'
        self.details['symbol'] = symbol


class InvalidQuantityError(ValidationError):
    """Invalid quantity"""
    def __init__(self, quantity: int, min_qty: int = None, max_qty: int = None):
        message = f"Invalid quantity: {quantity}"
        if min_qty:
            message += f" (min: {min_qty})"
        if max_qty:
            message += f" (max: {max_qty})"
        super().__init__(message, field='quantity')
        self.error_code = 'INVALID_QUANTITY'
        self.details.update({'quantity': quantity, 'min': min_qty, 'max': max_qty})


class InvalidPriceError(ValidationError):
    """Invalid price"""
    def __init__(self, price: float, reason: str = None):
        message = f"Invalid price: {price}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, field='price')
        self.error_code = 'INVALID_PRICE'
        self.details['price'] = price
        self.details['reason'] = reason


# ==================== System Errors ====================

class SystemError(ScalpingBotError):
    """Base class for system errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='SYSTEM_ERROR', **kwargs)


class BotNotRunningError(SystemError):
    """Trading bot is not running"""
    def __init__(self):
        super().__init__("Trading bot is not running")
        self.error_code = 'BOT_NOT_RUNNING'


class BotAlreadyRunningError(SystemError):
    """Trading bot is already running"""
    def __init__(self):
        super().__init__("Trading bot is already running")
        self.error_code = 'BOT_ALREADY_RUNNING'


class EmergencyStopError(SystemError):
    """Emergency stop activated"""
    def __init__(self, reason: str):
        super().__init__(f"Emergency stop: {reason}")
        self.error_code = 'EMERGENCY_STOP'
        self.details['reason'] = reason


class TimeoutError(SystemError):
    """Operation timed out"""
    def __init__(self, operation: str, timeout: int):
        super().__init__(f"{operation} timed out after {timeout}s")
        self.error_code = 'TIMEOUT_ERROR'
        self.details['operation'] = operation
        self.details['timeout'] = timeout


# ==================== Network Errors ====================

class NetworkError(ScalpingBotError):
    """Base class for network errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code='NETWORK_ERROR', **kwargs)


class APIRateLimitError(NetworkError):
    """API rate limit exceeded"""
    def __init__(self, retry_after: int = None):
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)
        self.error_code = 'RATE_LIMIT_EXCEEDED'
        self.details['retry_after'] = retry_after


class WebSocketError(NetworkError):
    """WebSocket connection error"""
    def __init__(self, message: str):
        super().__init__(message)
        self.error_code = 'WEBSOCKET_ERROR'
