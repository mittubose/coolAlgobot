"""
EMA Crossover Strategy
Classic moving average crossover strategy using Exponential Moving Averages
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta


class EMACrossoverStrategy:
    """
    EMA Crossover Strategy

    Generates BUY signal when fast EMA crosses above slow EMA
    Generates SELL signal when fast EMA crosses below slow EMA

    Parameters:
        - fast_period: Fast EMA period (default: 9)
        - slow_period: Slow EMA period (default: 21)
        - timeframe: Candlestick timeframe (default: 5minute)
        - risk_reward_ratio: Target/SL ratio (default: 2.0)
        - atr_sl_multiplier: ATR multiplier for stop-loss (default: 1.5)
    """

    def __init__(self, parameters: Dict):
        """
        Initialize EMA Crossover Strategy

        Args:
            parameters: Strategy parameters dict
        """
        self.fast_period = parameters.get('fast_period', 9)
        self.slow_period = parameters.get('slow_period', 21)
        self.timeframe = parameters.get('timeframe', '5minute')
        self.risk_reward = parameters.get('risk_reward_ratio', 2.0)
        self.atr_multiplier = parameters.get('atr_sl_multiplier', 1.5)

        # State
        self.last_signal = None
        self.ema_fast_prev = None
        self.ema_slow_prev = None

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
            # Need enough data for slow EMA
            if len(historical_data) < self.slow_period + 10:
                return None

            # Calculate EMAs
            df = historical_data.copy()
            df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()

            # Get latest values
            ema_fast_current = df['ema_fast'].iloc[-1]
            ema_slow_current = df['ema_slow'].iloc[-1]

            # Get previous values (for crossover detection)
            ema_fast_prev = df['ema_fast'].iloc[-2]
            ema_slow_prev = df['ema_slow'].iloc[-2]

            current_price = quote.get('last_price', df['close'].iloc[-1])

            # Calculate ATR for stop-loss
            atr = self._calculate_atr(df, period=14)
            stop_loss_distance = atr * self.atr_multiplier

            # Detect crossover
            signal = None

            # Bullish crossover (fast crosses above slow)
            if (ema_fast_prev <= ema_slow_prev and
                ema_fast_current > ema_slow_current and
                not has_position):

                stop_loss = current_price - stop_loss_distance
                target = current_price + (stop_loss_distance * self.risk_reward)

                signal = {
                    'action': 'BUY',
                    'symbol': symbol,
                    'exchange': exchange,
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'reason': f'EMA Bullish Crossover (Fast: {ema_fast_current:.2f}, Slow: {ema_slow_current:.2f})',
                    'indicators': {
                        'ema_fast': ema_fast_current,
                        'ema_slow': ema_slow_current,
                        'atr': atr
                    }
                }

            # Bearish crossover (fast crosses below slow) - exit long or enter short
            elif (ema_fast_prev >= ema_slow_prev and
                  ema_fast_current < ema_slow_current):

                if has_position:
                    # Exit signal
                    signal = {
                        'action': 'CLOSE',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'reason': f'EMA Bearish Crossover (Fast: {ema_fast_current:.2f}, Slow: {ema_slow_current:.2f})'
                    }
                else:
                    # Short signal (if shorting enabled)
                    stop_loss = current_price + stop_loss_distance
                    target = current_price - (stop_loss_distance * self.risk_reward)

                    signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'reason': f'EMA Bearish Crossover (Fast: {ema_fast_current:.2f}, Slow: {ema_slow_current:.2f})',
                        'indicators': {
                            'ema_fast': ema_fast_current,
                            'ema_slow': ema_slow_current,
                            'atr': atr
                        }
                    }

            # Update state
            self.ema_fast_prev = ema_fast_current
            self.ema_slow_prev = ema_slow_current
            self.last_signal = signal

            return signal

        except Exception as e:
            print(f"Error generating EMA signal: {e}")
            return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range

        Args:
            df: DataFrame with OHLC data
            period: ATR period

        Returns:
            ATR value
        """
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr.iloc[-1]

    def get_description(self) -> str:
        """Get strategy description"""
        return (
            f"EMA Crossover Strategy\n"
            f"Fast EMA: {self.fast_period}, Slow EMA: {self.slow_period}\n"
            f"Timeframe: {self.timeframe}\n"
            f"Risk/Reward: {self.risk_reward}:1\n"
            f"Stop-loss: {self.atr_multiplier}x ATR"
        )

    def get_parameters(self) -> Dict:
        """Get current parameters"""
        return {
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'timeframe': self.timeframe,
            'risk_reward_ratio': self.risk_reward,
            'atr_sl_multiplier': self.atr_multiplier
        }
