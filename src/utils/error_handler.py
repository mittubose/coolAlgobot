"""
Error Handler
Centralized error handling with logging, notifications, and recovery
"""

import logging
import traceback
import sys
from typing import Optional, Callable, Any
from datetime import datetime
from functools import wraps
from pathlib import Path

from .exceptions import ScalpingBotError
from .logger import get_logger


class ErrorHandler:
    """Centralized error handling system"""

    def __init__(self, logger_name: str = 'error_handler'):
        self.logger = get_logger(logger_name)
        self.error_log_file = Path("logs/errors.log")
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Error statistics
        self.error_count = 0
        self.last_error = None
        self.error_history = []
        self.max_history = 100

    def handle_error(
        self,
        error: Exception,
        context: str = None,
        severity: str = 'error',
        notify: bool = True,
        raise_error: bool = False
    ) -> dict:
        """
        Handle an error with logging, notification, and optional re-raise

        Args:
            error: The exception object
            context: Additional context about where the error occurred
            severity: 'debug', 'info', 'warning', 'error', 'critical'
            notify: Whether to send notifications
            raise_error: Whether to re-raise the exception

        Returns:
            Error details dictionary
        """
        # Increment error count
        self.error_count += 1

        # Get error details
        error_details = self._extract_error_details(error, context)

        # Log the error
        self._log_error(error_details, severity)

        # Save to error history
        self._save_to_history(error_details)

        # Send notifications if needed
        if notify:
            self._send_notification(error_details)

        # Update last error
        self.last_error = error_details

        # Re-raise if requested
        if raise_error:
            raise error

        return error_details

    def _extract_error_details(self, error: Exception, context: str = None) -> dict:
        """Extract detailed information from an exception"""

        # Base details
        details = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }

        # Add custom error details if it's a ScalpingBotError
        if isinstance(error, ScalpingBotError):
            details['error_code'] = error.error_code
            details['custom_details'] = error.details
            details['error_dict'] = error.to_dict()

        # Add system information
        details['python_version'] = sys.version
        details['error_count'] = self.error_count

        return details

    def _log_error(self, error_details: dict, severity: str):
        """Log error with appropriate severity level"""

        log_message = (
            f"Error occurred: {error_details['error_type']} - {error_details['error_message']}"
        )

        if error_details['context']:
            log_message += f" (Context: {error_details['context']})"

        # Log based on severity
        log_func = getattr(self.logger, severity.lower(), self.logger.error)
        log_func(log_message, extra={'error_details': error_details})

        # Write to error log file
        self._write_to_error_log(error_details)

    def _write_to_error_log(self, error_details: dict):
        """Write error to dedicated error log file"""
        try:
            with open(self.error_log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Timestamp: {error_details['timestamp']}\n")
                f.write(f"Error Type: {error_details['error_type']}\n")
                f.write(f"Error Message: {error_details['error_message']}\n")
                if error_details['context']:
                    f.write(f"Context: {error_details['context']}\n")
                f.write(f"\nTraceback:\n{error_details['traceback']}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            self.logger.error(f"Failed to write to error log file: {e}")

    def _save_to_history(self, error_details: dict):
        """Save error to in-memory history"""
        self.error_history.append(error_details)

        # Keep only last N errors
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def _send_notification(self, error_details: dict):
        """Send error notification (placeholder for alerts system integration)"""
        # TODO: Integrate with alerts system (Telegram/Email)
        # For now, just log that notification would be sent
        self.logger.debug(f"Error notification triggered: {error_details['error_type']}")

    def get_error_statistics(self) -> dict:
        """Get error statistics"""
        return {
            'total_errors': self.error_count,
            'last_error': self.last_error,
            'recent_errors': self.error_history[-10:] if self.error_history else []
        }

    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_count = 0
        self.last_error = None
        self.logger.info("Error history cleared")


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    context: str = None,
    severity: str = 'error',
    notify: bool = False,
    raise_error: bool = False
) -> dict:
    """
    Convenience function to handle errors

    Args:
        error: The exception object
        context: Additional context
        severity: Error severity level
        notify: Send notifications
        raise_error: Re-raise the exception

    Returns:
        Error details dictionary
    """
    handler = get_error_handler()
    return handler.handle_error(error, context, severity, notify, raise_error)


# ==================== Decorators ====================

def handle_exceptions(
    context: str = None,
    severity: str = 'error',
    notify: bool = False,
    default_return: Any = None,
    raise_error: bool = False
):
    """
    Decorator to automatically handle exceptions in functions

    Args:
        context: Context description
        severity: Log severity level
        notify: Send notifications on error
        default_return: Value to return on error (if not re-raising)
        raise_error: Whether to re-raise exceptions

    Usage:
        @handle_exceptions(context="Placing order", notify=True)
        def place_order(symbol, quantity):
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Build context
                func_context = context or f"Function: {func.__name__}"

                # Handle the error
                handle_error(
                    error=e,
                    context=func_context,
                    severity=severity,
                    notify=notify,
                    raise_error=raise_error
                )

                # Return default value if not re-raising
                if not raise_error:
                    return default_return

        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    context: str = None
):
    """
    Decorator to retry function on specific exceptions

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch
        context: Context description

    Usage:
        @retry_on_error(max_retries=3, delay=1, exceptions=(NetworkError,))
        def fetch_market_data(symbol):
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Log retry attempt
                        logger = get_logger(func.__module__)
                        retry_context = context or f"Function: {func.__name__}"
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {retry_context} "
                            f"after error: {str(e)}"
                        )

                        # Wait before retrying
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # Max retries exceeded, handle error
                        handle_error(
                            error=e,
                            context=f"{context or func.__name__} (after {max_retries} retries)",
                            severity='error',
                            notify=True,
                            raise_error=True
                        )

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def validate_input(**validations):
    """
    Decorator to validate function inputs

    Args:
        **validations: Field validators as keyword arguments

    Usage:
        @validate_input(
            symbol=lambda x: isinstance(x, str) and len(x) > 0,
            quantity=lambda x: isinstance(x, int) and x > 0
        )
        def place_order(symbol, quantity):
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from inspect import signature

            # Get function signature
            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each field
            for field, validator in validations.items():
                if field in bound_args.arguments:
                    value = bound_args.arguments[field]

                    # Run validator
                    if callable(validator):
                        if not validator(value):
                            from .exceptions import ValidationError
                            error = ValidationError(
                                f"Validation failed for field '{field}' with value: {value}",
                                field=field
                            )
                            handle_error(
                                error=error,
                                context=f"Input validation for {func.__name__}",
                                raise_error=True
                            )

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ==================== Context Managers ====================

class error_context:
    """
    Context manager for error handling

    Usage:
        with error_context("Fetching market data", notify=True):
            data = fetch_data()
    """

    def __init__(
        self,
        context: str,
        severity: str = 'error',
        notify: bool = False,
        raise_error: bool = True
    ):
        self.context = context
        self.severity = severity
        self.notify = notify
        self.raise_error = raise_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            handle_error(
                error=exc_val,
                context=self.context,
                severity=self.severity,
                notify=self.notify,
                raise_error=self.raise_error
            )
            return not self.raise_error  # Suppress exception if not re-raising
        return False
