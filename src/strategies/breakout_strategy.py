"""
Breakout Strategy
Trades breakouts from support/resistance levels
"""

import pandas as pd
from typing import Dict, Optional, Tuple


class BreakoutStrategy:
    """
    Breakout Strategy

    Identifies support and resistance levels from recent price action
    Generates BUY signal on resistance breakout
    Generates SELL signal on support breakdown

    Parameters:
        - lookback_period: Periods to look back for S/R (default: 20)
        - breakout_threshold: % above/below level for confirmation (default: 0.5)
        - volume_confirmation: Require volume spike (default: True)
        - volume_multiplier: Volume spike threshold (default: 1.5)
        - timeframe: Candlestick timeframe (default: 5minute)
        - sl_percentage: Stop-loss % from entry (default: 1.5)
        - risk_reward_ratio: Target/SL ratio (default: 2.5)
    """

    def __init__(self, parameters: Dict):
        """
        Initialize Breakout Strategy

        Args:
            parameters: Strategy parameters dict
        """
        self.lookback = parameters.get('lookback_period', 20)
        self.breakout_threshold = parameters.get('breakout_threshold', 0.5)
        self.volume_confirmation = parameters.get('volume_confirmation', True)
        self.volume_multiplier = parameters.get('volume_multiplier', 1.5)
        self.timeframe = parameters.get('timeframe', '5minute')
        self.sl_pct = parameters.get('sl_percentage', 1.5)
        self.risk_reward = parameters.get('risk_reward_ratio', 2.5)

        # State
        self.resistance_level = None
        self.support_level = None

    def generate_signal(
        self,
        symbol: str,
        exchange: str,
        quote: Dict,
        historical_data: pd.DataFrame,
        has_position: bool
    ) -> Optional[Dict]:
        """
        Generate trading signal

        Args:
            symbol: Trading symbol
            exchange: Exchange
            quote: Current quote data
            historical_data: Historical OHLC DataFrame
            has_position: Whether we already have a position

        Returns:
            Signal dict or None
        """
        try:
            # Need enough data
            if len(historical_data) < self.lookback + 10:
                return None

            # Don't enter if already in position
            if has_position:
                return None

            df = historical_data.copy()

            # Identify support and resistance levels
            resistance, support = self._find_support_resistance(df)

            self.resistance_level = resistance
            self.support_level = support

            # Get current values
            current_price = quote.get('last_price', df['close'].iloc[-1])
            current_volume = df['volume'].iloc[-1] if 'volume' in df else 0
            avg_volume = df['volume'].iloc[-self.lookback:].mean() if 'volume' in df else 0

            signal = None

            # Check volume confirmation
            volume_confirmed = True
            if self.volume_confirmation and avg_volume > 0:
                volume_confirmed = current_volume >= (avg_volume * self.volume_multiplier)

            # Resistance breakout - BUY signal
            if resistance and current_price > resistance * (1 + self.breakout_threshold / 100):
                if volume_confirmed:
                    stop_loss = current_price * (1 - self.sl_pct / 100)
                    sl_distance = current_price - stop_loss
                    target = current_price + (sl_distance * self.risk_reward)

                    signal = {
                        'action': 'BUY',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'reason': f'Resistance Breakout at {resistance:.2f} (Price: {current_price:.2f})',
                        'indicators': {
                            'resistance': resistance,
                            'support': support,
                            'breakout_pct': ((current_price - resistance) / resistance * 100),
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0
                        }
                    }

            # Support breakdown - SELL signal (short)
            elif support and current_price < support * (1 - self.breakout_threshold / 100):
                if volume_confirmed:
                    stop_loss = current_price * (1 + self.sl_pct / 100)
                    sl_distance = stop_loss - current_price
                    target = current_price - (sl_distance * self.risk_reward)

                    signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'reason': f'Support Breakdown at {support:.2f} (Price: {current_price:.2f})',
                        'indicators': {
                            'resistance': resistance,
                            'support': support,
                            'breakdown_pct': ((support - current_price) / support * 100),
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0
                        }
                    }

            return signal

        except Exception as e:
            print(f"Error generating Breakout signal: {e}")
            return None

    def _find_support_resistance(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """
        Find support and resistance levels

        Args:
            df: Historical OHLC DataFrame

        Returns:
            Tuple of (resistance, support)
        """
        try:
            # Use recent data
            recent_df = df.iloc[-self.lookback:]

            # Find local maxima (resistance candidates)
            high_peaks = self._find_local_peaks(recent_df['high'].values, order=3)

            # Find local minima (support candidates)
            low_peaks = self._find_local_peaks(-recent_df['low'].values, order=3)

            # Get resistance level (most recent significant high)
            resistance = None
            if len(high_peaks) > 0:
                resistance_prices = recent_df['high'].iloc[high_peaks].values
                resistance = max(resistance_prices[-3:]) if len(resistance_prices) >= 3 else resistance_prices[-1]

            # Get support level (most recent significant low)
            support = None
            if len(low_peaks) > 0:
                support_prices = recent_df['low'].iloc[low_peaks].values
                support = min(support_prices[-3:]) if len(support_prices) >= 3 else support_prices[-1]

            return resistance, support

        except Exception as e:
            print(f"Error finding support/resistance: {e}")
            return None, None

    def _find_local_peaks(self, data, order=3):
        """
        Find local peaks in data

        Args:
            data: Array of values
            order: How many points on each side to use for comparison

        Returns:
            Indices of local peaks
        """
        peaks = []

        for i in range(order, len(data) - order):
            # Check if this point is higher than surrounding points
            is_peak = True

            for j in range(1, order + 1):
                if data[i] <= data[i - j] or data[i] <= data[i + j]:
                    is_peak = False
                    break

            if is_peak:
                peaks.append(i)

        return peaks

    def get_description(self) -> str:
        """Get strategy description"""
        return (
            f"Breakout Strategy\n"
            f"Lookback Period: {self.lookback}\n"
            f"Breakout Threshold: {self.breakout_threshold}%\n"
            f"Volume Confirmation: {self.volume_confirmation}\n"
            f"Risk/Reward: {self.risk_reward}:1\n"
            f"Stop-loss: {self.sl_pct}%"
        )

    def get_parameters(self) -> Dict:
        """Get current parameters"""
        return {
            'lookback_period': self.lookback,
            'breakout_threshold': self.breakout_threshold,
            'volume_confirmation': self.volume_confirmation,
            'volume_multiplier': self.volume_multiplier,
            'timeframe': self.timeframe,
            'sl_percentage': self.sl_pct,
            'risk_reward_ratio': self.risk_reward
        }
