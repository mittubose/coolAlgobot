"""
OHLC Data Generator
Generates realistic candlestick data for charts
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class OHLCGenerator:
    """Generate realistic OHLC (Open/High/Low/Close) candlestick data"""

    def __init__(self, base_price: float = 50000, volatility: float = 0.02):
        """
        Initialize generator

        Args:
            base_price: Starting price
            volatility: Price movement volatility (0.02 = 2%)
        """
        self.base_price = base_price
        self.volatility = volatility
        self.current_price = base_price

    def generate_candle(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Generate a single OHLC candle

        Returns:
            dict: {time, open, high, low, close, volume}
        """
        # Open price
        open_price = self.current_price

        # Generate price movement
        price_change = random.uniform(-self.volatility, self.volatility)
        close_price = open_price * (1 + price_change)

        # High and Low (ensure realistic wicks)
        volatility_range = abs(close_price - open_price) * random.uniform(1.2, 2.0)
        high_price = max(open_price, close_price) + (volatility_range * random.uniform(0.3, 0.7))
        low_price = min(open_price, close_price) - (volatility_range * random.uniform(0.3, 0.7))

        # Volume (random but realistic)
        volume = random.randint(1000, 10000)

        # Update current price for next candle
        self.current_price = close_price

        return {
            'time': timestamp.strftime('%Y-%m-%d %H:%M'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        }

    def generate_candles(self, count: int = 100, timeframe: str = '5m') -> List[Dict[str, Any]]:
        """
        Generate multiple OHLC candles

        Args:
            count: Number of candles to generate
            timeframe: Timeframe (5m, 15m, 1h, etc.)

        Returns:
            list: Array of OHLC candles
        """
        # Parse timeframe
        interval_minutes = self._parse_timeframe(timeframe)

        # Generate candles
        candles = []
        current_time = datetime.now() - timedelta(minutes=interval_minutes * count)

        for i in range(count):
            candle = self.generate_candle(current_time)
            candles.append(candle)
            current_time += timedelta(minutes=interval_minutes)

        return candles

    def _parse_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return timeframe_map.get(timeframe, 5)

    def generate_trending_candles(
        self,
        count: int = 100,
        timeframe: str = '5m',
        trend: str = 'bullish'
    ) -> List[Dict[str, Any]]:
        """
        Generate candles with a specific trend

        Args:
            count: Number of candles
            timeframe: Timeframe
            trend: 'bullish', 'bearish', or 'sideways'

        Returns:
            list: Array of OHLC candles
        """
        # Adjust volatility based on trend
        if trend == 'bullish':
            trend_bias = 0.005  # Slight upward bias
        elif trend == 'bearish':
            trend_bias = -0.005  # Slight downward bias
        else:
            trend_bias = 0  # Sideways

        interval_minutes = self._parse_timeframe(timeframe)
        candles = []
        current_time = datetime.now() - timedelta(minutes=interval_minutes * count)

        for i in range(count):
            # Generate candle with trend bias
            open_price = self.current_price

            # Add trend bias to price movement
            price_change = random.uniform(-self.volatility, self.volatility) + trend_bias
            close_price = open_price * (1 + price_change)

            # High and Low
            volatility_range = abs(close_price - open_price) * random.uniform(1.2, 2.0)
            high_price = max(open_price, close_price) + (volatility_range * random.uniform(0.3, 0.7))
            low_price = min(open_price, close_price) - (volatility_range * random.uniform(0.3, 0.7))

            # Volume
            volume = random.randint(1000, 10000)

            # Update current price
            self.current_price = close_price

            candle = {
                'time': current_time.strftime('%Y-%m-%d %H:%M'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            }

            candles.append(candle)
            current_time += timedelta(minutes=interval_minutes)

        return candles

    def add_pattern_candles(
        self,
        candles: List[Dict[str, Any]],
        pattern_type: str,
        position: int = -1
    ) -> List[Dict[str, Any]]:
        """
        Inject a specific pattern into candles

        Args:
            candles: Existing candle data
            pattern_type: 'hammer', 'doji', 'engulfing', etc.
            position: Index to insert pattern (-1 = last)

        Returns:
            list: Modified candle data
        """
        if position == -1:
            position = len(candles) - 1

        if position >= len(candles):
            return candles

        base_candle = candles[position]
        base_price = base_candle['close']

        if pattern_type == 'hammer':
            # Hammer: small body, long lower wick
            body_size = base_price * 0.002  # 0.2% body
            wick_size = base_price * 0.015  # 1.5% lower wick

            candles[position] = {
                **base_candle,
                'open': base_price - body_size / 2,
                'close': base_price + body_size / 2,
                'high': base_price + body_size / 2 + (wick_size * 0.2),
                'low': base_price - wick_size
            }

        elif pattern_type == 'doji':
            # Doji: open = close
            wick_size = base_price * 0.01

            candles[position] = {
                **base_candle,
                'open': base_price,
                'close': base_price,
                'high': base_price + wick_size,
                'low': base_price - wick_size
            }

        elif pattern_type == 'shooting_star':
            # Shooting star: small body, long upper wick
            body_size = base_price * 0.002
            wick_size = base_price * 0.015

            candles[position] = {
                **base_candle,
                'open': base_price + body_size / 2,
                'close': base_price - body_size / 2,
                'high': base_price + wick_size,
                'low': base_price - body_size / 2 - (wick_size * 0.2)
            }

        return candles


# Convenience function
def generate_ohlc_data(
    count: int = 100,
    timeframe: str = '5m',
    symbol: str = 'NIFTY50',
    trend: str = 'sideways'
) -> Dict[str, Any]:
    """
    Generate OHLC data for API response

    Args:
        count: Number of candles
        timeframe: Timeframe
        symbol: Symbol name
        trend: Market trend

    Returns:
        dict: Complete OHLC data response
    """
    generator = OHLCGenerator(base_price=50000, volatility=0.015)
    candles = generator.generate_trending_candles(count, timeframe, trend)

    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'candles': candles,
        'count': len(candles)
    }


# Demo usage
if __name__ == '__main__':
    # Generate sample data
    data = generate_ohlc_data(50, '5m', 'NIFTY50', 'bullish')

    print(f"✓ Generated {data['count']} candles for {data['symbol']}")
    print(f"  Timeframe: {data['timeframe']}")
    print(f"\nLast 3 candles:")
    for candle in data['candles'][-3:]:
        print(f"  {candle['time']}: O={candle['open']:.2f} H={candle['high']:.2f} "
              f"L={candle['low']:.2f} C={candle['close']:.2f}")
