"""
Logging System
Structured logging with JSON format and multiple log files
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom text formatter with colors for console output"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format: [TIMESTAMP] LEVEL: message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"{color}[{timestamp}] {record.levelname:8s}{reset}: {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)

        return formatted


class LoggerSetup:
    """Setup and configure logging system"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize logger setup

        Args:
            config: Logging configuration
        """
        self.config = config
        self.loggers = {}

    def setup(self):
        """Configure all loggers"""
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.get('level', 'INFO')))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler
        self._add_console_handler(root_logger)

        # Add file handlers
        log_format = self.config.get('format', 'json')
        rotation = self.config.get('rotation', 'daily')

        # System log
        self._add_file_handler(
            root_logger,
            self.config['files']['system'],
            log_format,
            rotation
        )

        # Create specialized loggers
        self._setup_specialized_loggers(log_format, rotation)

    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler with text formatting"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(TextFormatter())
        logger.addHandler(console_handler)

    def _add_file_handler(self, logger: logging.Logger, filepath: str,
                          log_format: str, rotation: str):
        """Add file handler with specified format and rotation"""
        # Create parent directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Choose handler based on rotation type
        if rotation == 'daily':
            handler = TimedRotatingFileHandler(
                filepath,
                when='midnight',
                interval=1,
                backupCount=self.config.get('backup_count', 30)
            )
        else:  # size-based rotation
            max_bytes = self.config.get('max_file_size_mb', 100) * 1024 * 1024
            handler = RotatingFileHandler(
                filepath,
                maxBytes=max_bytes,
                backupCount=self.config.get('backup_count', 10)
            )

        # Set formatter
        if log_format == 'json':
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))

        logger.addHandler(handler)

    def _setup_specialized_loggers(self, log_format: str, rotation: str):
        """Setup specialized loggers for trades, errors, signals"""
        # Trade logger
        trade_logger = logging.getLogger('trades')
        trade_logger.setLevel(logging.INFO)
        trade_logger.propagate = False
        self._add_file_handler(
            trade_logger,
            self.config['files']['trades'],
            log_format,
            rotation
        )
        self.loggers['trades'] = trade_logger

        # Error logger
        error_logger = logging.getLogger('errors')
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False
        self._add_file_handler(
            error_logger,
            self.config['files']['errors'],
            log_format,
            rotation
        )
        self.loggers['errors'] = error_logger

        # Signal logger
        signal_logger = logging.getLogger('signals')
        signal_logger.setLevel(logging.INFO)
        signal_logger.propagate = False
        self._add_file_handler(
            signal_logger,
            self.config['files']['signals'],
            log_format,
            rotation
        )
        self.loggers['signals'] = signal_logger

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger by name"""
        if name in self.loggers:
            return self.loggers[name]
        return logging.getLogger(name)


# Helper functions for logging with extra data
def log_trade(logger: logging.Logger, message: str, trade_data: Dict[str, Any]):
    """Log trade with structured data"""
    record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, message, (), None
    )
    record.extra_data = trade_data
    logger.handle(record)


def log_signal(logger: logging.Logger, message: str, signal_data: Dict[str, Any]):
    """Log trading signal with structured data"""
    record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, message, (), None
    )
    record.extra_data = signal_data
    logger.handle(record)


def log_error(logger: logging.Logger, message: str, error_data: Dict[str, Any] = None):
    """Log error with structured data"""
    record = logger.makeRecord(
        logger.name, logging.ERROR, '', 0, message, (), None
    )
    if error_data:
        record.extra_data = error_data
    logger.handle(record)


# Global logger instance
_logger_setup = None


def setup_logging(config: Dict[str, Any]) -> LoggerSetup:
    """Setup global logging system"""
    global _logger_setup
    _logger_setup = LoggerSetup(config)
    _logger_setup.setup()
    return _logger_setup


def get_logger(name: str = 'scalping_bot') -> logging.Logger:
    """Get logger instance"""
    if _logger_setup:
        return _logger_setup.get_logger(name)
    return logging.getLogger(name)
