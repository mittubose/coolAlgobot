#!/usr/bin/env python3
"""
Test Error Handling System
Demonstrates error handling, logging, and validation
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import (
    get_error_handler,
    handle_error,
    handle_exceptions,
    retry_on_error,
    Validator,
    validate_order_params
)
from src.utils.exceptions import (
    ValidationError,
    InvalidSymbolError,
    BrokerAuthenticationError,
    OrderPlacementError
)


def test_custom_exceptions():
    """Test custom exception classes"""
    print("\n" + "=" * 60)
    print("TEST 1: Custom Exception Classes")
    print("=" * 60)

    try:
        raise InvalidSymbolError("INVALID@SYMBOL")
    except InvalidSymbolError as e:
        print(f"✅ Caught InvalidSymbolError: {e.message}")
        print(f"   Error Code: {e.error_code}")
        print(f"   Details: {e.to_dict()}")

    try:
        raise BrokerAuthenticationError("Invalid API credentials", broker_name="Zerodha")
    except BrokerAuthenticationError as e:
        print(f"✅ Caught BrokerAuthenticationError: {e.message}")
        print(f"   Broker: {e.broker_name}")


def test_validation():
    """Test validation helpers"""
    print("\n" + "=" * 60)
    print("TEST 2: Validation Helpers")
    print("=" * 60)

    validator = Validator()

    # Test valid inputs
    try:
        symbol = validator.validate_symbol("reliance")
        print(f"✅ Valid symbol: {symbol}")

        exchange = validator.validate_exchange("NSE")
        print(f"✅ Valid exchange: {exchange}")

        quantity = validator.validate_quantity(10, min_qty=1)
        print(f"✅ Valid quantity: {quantity}")

        price = validator.validate_price(2500.50)
        print(f"✅ Valid price: {price}")

    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    # Test invalid inputs
    print("\n   Testing invalid inputs:")
    try:
        validator.validate_symbol("")  # Empty symbol
    except InvalidSymbolError as e:
        print(f"✅ Caught invalid symbol: {e.message}")

    try:
        validator.validate_price(-100)  # Negative price
    except Exception as e:
        print(f"✅ Caught invalid price: {e}")


def test_order_validation():
    """Test complete order validation"""
    print("\n" + "=" * 60)
    print("TEST 3: Order Parameter Validation")
    print("=" * 60)

    # Valid order
    try:
        params = validate_order_params(
            symbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            quantity=1,
            order_type="MARKET",
            product="MIS"
        )
        print(f"✅ Valid order params: {params}")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    # Invalid order (LIMIT without price)
    print("\n   Testing invalid order:")
    try:
        params = validate_order_params(
            symbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            quantity=1,
            order_type="LIMIT",  # LIMIT requires price
            product="MIS"
        )
    except ValidationError as e:
        print(f"✅ Caught validation error: {e.message}")


def test_error_handler():
    """Test error handler"""
    print("\n" + "=" * 60)
    print("TEST 4: Error Handler")
    print("=" * 60)

    error_handler = get_error_handler()

    # Simulate some errors
    try:
        raise OrderPlacementError(
            "Insufficient funds",
            symbol="RELIANCE",
            order_details={"quantity": 100, "price": 2500}
        )
    except Exception as e:
        error_details = handle_error(
            error=e,
            context="Test order placement",
            severity="error",
            notify=False
        )
        print(f"✅ Error handled: {error_details['error_type']}")

    # Get statistics
    stats = error_handler.get_error_statistics()
    print(f"\n   Error Statistics:")
    print(f"   Total Errors: {stats['total_errors']}")
    if stats['last_error']:
        print(f"   Last Error: {stats['last_error']['error_type']}")


@handle_exceptions(context="Test function", notify=False, default_return="ERROR")
def test_decorator():
    """Test error handling decorator"""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling Decorator")
    print("=" * 60)

    # This will raise an error but should be handled by decorator
    raise ValueError("This error should be caught by decorator")


@retry_on_error(max_retries=3, delay=0.5, exceptions=(ValueError,))
def test_retry_decorator():
    """Test retry decorator"""
    print("\n" + "=" * 60)
    print("TEST 6: Retry Decorator")
    print("=" * 60)

    # Simulate a function that fails twice then succeeds
    if not hasattr(test_retry_decorator, 'attempt_count'):
        test_retry_decorator.attempt_count = 0

    test_retry_decorator.attempt_count += 1

    if test_retry_decorator.attempt_count < 3:
        print(f"   Attempt {test_retry_decorator.attempt_count}: Failing...")
        raise ValueError("Temporary error")
    else:
        print(f"   Attempt {test_retry_decorator.attempt_count}: Success!")
        return "SUCCESS"


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("SCALPING BOT - ERROR HANDLING & VALIDATION TEST SUITE")
    print("=" * 80)

    try:
        # Run tests
        test_custom_exceptions()
        test_validation()
        test_order_validation()
        test_error_handler()

        result = test_decorator()
        print(f"   Decorator returned: {result}")

        result = test_retry_decorator()
        print(f"   Retry decorator returned: {result}")

        # Final summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

        error_handler = get_error_handler()
        stats = error_handler.get_error_statistics()
        print(f"\nFinal Error Statistics:")
        print(f"  Total Errors Handled: {stats['total_errors']}")
        print(f"  Recent Errors: {len(stats['recent_errors'])}")

        print("\nError log file: logs/errors.log")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
