"""
RSI Strategy
Relative Strength Index based mean reversion strategy
"""

import pandas as pd
from typing import Dict, Optional


class RSIStrategy:
    """
    RSI Strategy

    Generates BUY signal when RSI is oversold (< lower_threshold)
    Generates SELL signal when RSI is overbought (> upper_threshold)
    Exits when RSI returns to middle range

    Parameters:
        - rsi_period: RSI calculation period (default: 14)
        - oversold_threshold: Oversold level (default: 30)
        - overbought_threshold: Overbought level (default: 70)
        - middle_exit: Exit when RSI crosses middle (default: 50)
        - timeframe: Candlestick timeframe (default: 5minute)
        - sl_percentage: Stop-loss % from entry (default: 2.0)
        - target_percentage: Target % from entry (default: 3.0)
    """

    def __init__(self, parameters: Dict):
        """
        Initialize RSI Strategy

        Args:
            parameters: Strategy parameters dict
        """
        self.rsi_period = parameters.get('rsi_period', 14)
        self.oversold = parameters.get('oversold_threshold', 30)
        self.overbought = parameters.get('overbought_threshold', 70)
        self.middle_exit = parameters.get('middle_exit', 50)
        self.timeframe = parameters.get('timeframe', '5minute')
        self.sl_pct = parameters.get('sl_percentage', 2.0)
        self.target_pct = parameters.get('target_percentage', 3.0)

        # State
        self.last_rsi = None
        self.entry_side = None

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
            # Need enough data for RSI
            if len(historical_data) < self.rsi_period + 10:
                return None

            # Calculate RSI
            df = historical_data.copy()
            df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

            # Get current values
            rsi_current = df['rsi'].iloc[-1]
            rsi_prev = df['rsi'].iloc[-2]
            current_price = quote.get('last_price', df['close'].iloc[-1])

            signal = None

            if not has_position:
                # Entry signals

                # Oversold - potential BUY
                if rsi_prev < self.oversold and rsi_current >= self.oversold:
                    stop_loss = current_price * (1 - self.sl_pct / 100)
                    target = current_price * (1 + self.target_pct / 100)

                    signal = {
                        'action': 'BUY',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'reason': f'RSI Oversold Reversal (RSI: {rsi_current:.2f})',
                        'indicators': {
                            'rsi': rsi_current,
                            'threshold': self.oversold
                        }
                    }
                    self.entry_side = 'BUY'

                # Overbought - potential SELL (short)
                elif rsi_prev > self.overbought and rsi_current <= self.overbought:
                    stop_loss = current_price * (1 + self.sl_pct / 100)
                    target = current_price * (1 - self.target_pct / 100)

                    signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'reason': f'RSI Overbought Reversal (RSI: {rsi_current:.2f})',
                        'indicators': {
                            'rsi': rsi_current,
                            'threshold': self.overbought
                        }
                    }
                    self.entry_side = 'SELL'

            else:
                # Exit signals

                # Exit long position when RSI crosses above middle
                if (self.entry_side == 'BUY' and
                    rsi_prev < self.middle_exit and
                    rsi_current >= self.middle_exit):

                    signal = {
                        'action': 'CLOSE',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'reason': f'RSI Exit Signal - Long (RSI: {rsi_current:.2f})'
                    }

                # Exit short position when RSI crosses below middle
                elif (self.entry_side == 'SELL' and
                      rsi_prev > self.middle_exit and
                      rsi_current <= self.middle_exit):

                    signal = {
                        'action': 'CLOSE',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'reason': f'RSI Exit Signal - Short (RSI: {rsi_current:.2f})'
                    }

            # Update state
            self.last_rsi = rsi_current
            if signal and signal['action'] == 'CLOSE':
                self.entry_side = None

            return signal

        except Exception as e:
            print(f"Error generating RSI signal: {e}")
            return None

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            prices: Price series
            period: RSI period

        Returns:
            RSI series
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_description(self) -> str:
        """Get strategy description"""
        return (
            f"RSI Mean Reversion Strategy\n"
            f"RSI Period: {self.rsi_period}\n"
            f"Oversold: {self.oversold}, Overbought: {self.overbought}\n"
            f"Exit Level: {self.middle_exit}\n"
            f"Stop-loss: {self.sl_pct}%, Target: {self.target_pct}%"
        )

    def get_parameters(self) -> Dict:
        """Get current parameters"""
        return {
            'rsi_period': self.rsi_period,
            'oversold_threshold': self.oversold,
            'overbought_threshold': self.overbought,
            'middle_exit': self.middle_exit,
            'timeframe': self.timeframe,
            'sl_percentage': self.sl_pct,
            'target_percentage': self.target_pct
        }
