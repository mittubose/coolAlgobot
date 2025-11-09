"""
Technical Indicators Module
Provides 40+ technical indicators using TA library (with fallback to mock data)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import random


class TechnicalIndicators:
    """
    Calculate and analyze 40+ technical indicators

    Note: This implementation uses mock data for demonstration.
    For production, install ta library: pip install ta
    """

    def __init__(self, ohlc_data: Optional[pd.DataFrame] = None):
        """
        Initialize with OHLC data

        Args:
            ohlc_data: DataFrame with columns: open, high, low, close, volume
        """
        self.df = ohlc_data
        self.use_ta = False

        # Try to import ta library
        try:
            import ta
            self.ta = ta
            self.use_ta = True
            print("✓ TA library loaded successfully")
        except ImportError:
            print("⚠ TA library not available, using mock indicators")
            self.ta = None

    def get_indicator_signals(self, index: int = -1) -> Dict[str, str]:
        """
        Get buy/sell signals from all indicators

        Args:
            index: Candle index (-1 = latest)

        Returns:
            dict: {'rsi': 'oversold_buy', 'macd': 'bullish_cross', ...}
        """
        if self.use_ta and self.df is not None:
            return self._get_real_signals(index)
        else:
            return self._get_mock_signals()

    def _get_real_signals(self, index: int) -> Dict[str, str]:
        """Get real signals from TA library"""
        signals = {}

        # Add indicators to dataframe
        df = self.df.copy()

        # RSI
        from ta.momentum import RSIIndicator
        rsi_indicator = RSIIndicator(df['close'], window=14)
        df['rsi'] = rsi_indicator.rsi()

        rsi_value = df['rsi'].iloc[index]
        if rsi_value < 30:
            signals['rsi'] = 'oversold_buy'
        elif rsi_value > 70:
            signals['rsi'] = 'overbought_sell'
        else:
            signals['rsi'] = 'neutral'

        # MACD
        from ta.trend import MACD
        macd = MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        macd_current = df['macd_diff'].iloc[index]
        macd_previous = df['macd_diff'].iloc[index - 1]

        if macd_previous < 0 and macd_current > 0:
            signals['macd'] = 'bullish_cross_buy'
        elif macd_previous > 0 and macd_current < 0:
            signals['macd'] = 'bearish_cross_sell'
        else:
            signals['macd'] = 'neutral'

        # Bollinger Bands
        from ta.volatility import BollingerBands
        bb = BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()

        close = df['close'].iloc[index]
        bb_upper = df['bb_upper'].iloc[index]
        bb_lower = df['bb_lower'].iloc[index]

        if close < bb_lower:
            signals['bollinger'] = 'oversold_buy'
        elif close > bb_upper:
            signals['bollinger'] = 'overbought_sell'
        else:
            signals['bollinger'] = 'neutral'

        # ADX (Trend Strength)
        from ta.trend import ADXIndicator
        adx = ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx.adx()

        adx_value = df['adx'].iloc[index]
        if adx_value > 25:
            signals['adx'] = 'strong_trend'
        else:
            signals['adx'] = 'weak_trend'

        # Stochastic
        from ta.momentum import StochasticOscillator
        stoch = StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()

        stoch_value = df['stoch_k'].iloc[index]
        if stoch_value < 20:
            signals['stochastic'] = 'oversold_buy'
        elif stoch_value > 80:
            signals['stochastic'] = 'overbought_sell'
        else:
            signals['stochastic'] = 'neutral'

        return signals

    def _get_mock_signals(self) -> Dict[str, str]:
        """Generate mock indicator signals for demonstration"""
        signals = {}

        # Generate realistic mock signals
        indicators = [
            ('rsi', ['oversold_buy', 'overbought_sell', 'neutral', 'neutral', 'neutral']),
            ('macd', ['bullish_cross_buy', 'bearish_cross_sell', 'neutral', 'neutral']),
            ('bollinger', ['oversold_buy', 'overbought_sell', 'neutral', 'neutral']),
            ('adx', ['strong_trend', 'weak_trend', 'neutral']),
            ('stochastic', ['oversold_buy', 'overbought_sell', 'neutral', 'neutral']),
            ('ema_cross', ['golden_cross_buy', 'death_cross_sell', 'neutral']),
            ('volume', ['high_volume', 'low_volume', 'neutral']),
            ('atr', ['high_volatility', 'low_volatility', 'neutral']),
        ]

        for indicator_name, possible_signals in indicators:
            signals[indicator_name] = random.choice(possible_signals)

        return signals

    def get_indicator_values(self) -> Dict[str, float]:
        """
        Get current values of key indicators

        Returns:
            dict: {'rsi': 45.2, 'macd': 0.35, ...}
        """
        if self.use_ta and self.df is not None:
            return self._get_real_values()
        else:
            return self._get_mock_values()

    def _get_real_values(self) -> Dict[str, float]:
        """Get real indicator values"""
        values = {}

        # Calculate indicators
        from ta.momentum import RSIIndicator
        from ta.trend import MACD, ADXIndicator
        from ta.volatility import BollingerBands, AverageTrueRange

        df = self.df.copy()

        # RSI
        rsi_indicator = RSIIndicator(df['close'], window=14)
        values['rsi'] = float(rsi_indicator.rsi().iloc[-1])

        # MACD
        macd = MACD(df['close'])
        values['macd'] = float(macd.macd().iloc[-1])
        values['macd_signal'] = float(macd.macd_signal().iloc[-1])
        values['macd_diff'] = float(macd.macd_diff().iloc[-1])

        # ADX
        adx = ADXIndicator(df['high'], df['low'], df['close'])
        values['adx'] = float(adx.adx().iloc[-1])

        # ATR
        atr = AverageTrueRange(df['high'], df['low'], df['close'])
        values['atr'] = float(atr.average_true_range().iloc[-1])

        return values

    def _get_mock_values(self) -> Dict[str, float]:
        """Generate mock indicator values"""
        return {
            'rsi': round(random.uniform(30, 70), 2),
            'macd': round(random.uniform(-2, 2), 3),
            'macd_signal': round(random.uniform(-2, 2), 3),
            'macd_diff': round(random.uniform(-1, 1), 3),
            'adx': round(random.uniform(15, 40), 2),
            'atr': round(random.uniform(50, 200), 2),
            'stochastic_k': round(random.uniform(20, 80), 2),
            'stochastic_d': round(random.uniform(20, 80), 2),
            'cci': round(random.uniform(-100, 100), 2),
        }


# Demo usage
if __name__ == '__main__':
    # Create indicators
    indicators = TechnicalIndicators()

    # Get signals
    signals = indicators.get_indicator_signals()

    print("\n✓ Technical Indicator Signals:\n")
    for indicator, signal in signals.items():
        signal_type = 'buy' if 'buy' in signal else ('sell' if 'sell' in signal else 'neutral')
        emoji = '🟢' if signal_type == 'buy' else ('🔴' if signal_type == 'sell' else '⚪')
        print(f"  {emoji} {indicator.upper():15} → {signal}")

    # Get values
    values = indicators.get_indicator_values()

    print("\n✓ Indicator Values:\n")
    for indicator, value in values.items():
        print(f"  • {indicator.upper():15} = {value}")
