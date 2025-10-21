"""
Broker Factory
Creates broker instances based on broker name
"""

from typing import Dict, Any
from .base_broker import BaseBroker
from .zerodha_broker import ZerodhaBroker
from .kotak_broker import KotakBroker
from .angel_broker import AngelBroker


class BrokerFactory:
    """Factory class for creating broker instances"""

    # Supported brokers
    BROKERS = {
        'zerodha': ZerodhaBroker,
        'kotak': KotakBroker,
        'angel': AngelBroker,
        'angel_one': AngelBroker,  # Alias
        'kotak_securities': KotakBroker,  # Alias
    }

    @classmethod
    def create_broker(cls, broker_name: str, api_key: str, api_secret: str, **kwargs) -> BaseBroker:
        """
        Create a broker instance

        Args:
            broker_name: Name of the broker (zerodha, kotak, angel, etc.)
            api_key: Broker API key
            api_secret: Broker API secret
            **kwargs: Additional broker-specific parameters

        Returns:
            Broker instance

        Raises:
            ValueError: If broker not supported
        """
        broker_name = broker_name.lower().strip()

        if broker_name not in cls.BROKERS:
            supported = ', '.join(cls.BROKERS.keys())
            raise ValueError(
                f"Broker '{broker_name}' not supported. "
                f"Supported brokers: {supported}"
            )

        broker_class = cls.BROKERS[broker_name]
        return broker_class(api_key, api_secret, **kwargs)

    @classmethod
    def get_supported_brokers(cls) -> Dict[str, str]:
        """
        Get list of supported brokers

        Returns:
            Dictionary of broker names and their display names
        """
        return {
            'zerodha': 'Zerodha Kite Connect',
            'kotak': 'Kotak Securities Neo API',
            'angel': 'Angel One SmartAPI',
            'upstox': 'Upstox API (Coming Soon)',
            'icici': 'ICICI Direct (Coming Soon)',
            'fyers': 'Fyers API (Coming Soon)',
        }

    @classmethod
    def is_broker_supported(cls, broker_name: str) -> bool:
        """
        Check if a broker is supported

        Args:
            broker_name: Name of the broker

        Returns:
            True if supported, False otherwise
        """
        return broker_name.lower().strip() in cls.BROKERS


# Convenience function
def create_broker(broker_name: str, api_key: str, api_secret: str, **kwargs) -> BaseBroker:
    """
    Create a broker instance (convenience function)

    Args:
        broker_name: Name of the broker
        api_key: Broker API key
        api_secret: Broker API secret
        **kwargs: Additional broker-specific parameters

    Returns:
        Broker instance
    """
    return BrokerFactory.create_broker(broker_name, api_key, api_secret, **kwargs)
