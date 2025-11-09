"""
Strategy Backtester
Provides convenient interface to backtest trading strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta

from .backtest_engine import BacktestEngine, BacktestResult
from src.utils.logger import setup_logger


class StrategyBacktester:
    """
    High-level interface for backtesting trading strategies

    Supports:
    - EMA Crossover
    - RSI Strategy
    - Breakout Strategy
    - Custom strategies
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_per_trade: float = 20,
        risk_per_trade: float = 0.02
    ):
        """
        Initialize strategy backtester

        Args:
            initial_capital: Starting capital
            commission_per_trade: Commission per trade
            risk_per_trade: Maximum risk per trade (as fraction)
        """
        self.engine = BacktestEngine(
            initial_capital=initial_capital,
            commission_per_trade=commission_per_trade,
            risk_per_trade=risk_per_trade
        )
        self.logger = setup_logger('strategy_backtester')

    def backtest_ema_crossover(
        self,
        data: pd.DataFrame,
        fast_period: int = 9,
        slow_period: int = 21,
        stop_loss_pct: float = 2.0,
        target_pct: float = 4.0
    ) -> BacktestResult:
        """
        Backtest EMA Crossover strategy

        Args:
            data: OHLCV DataFrame
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            stop_loss_pct: Stop loss percentage
            target_pct: Target percentage

        Returns:
            BacktestResult
        """
        self.logger.info(f"Backtesting EMA Crossover (Fast: {fast_period}, Slow: {slow_period})")

        def strategy_func(historical_data: pd.DataFrame, params: Dict) -> Optional[Dict]:
            """EMA Crossover signal generation"""
            if len(historical_data) < slow_period + 1:
                return None

            # Calculate EMAs
            df = historical_data.copy()
            df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

            # Get current and previous values
            current = df.iloc[-1]
            previous = df.iloc[-2]

            current_price = current['close']

            # Bullish crossover (fast crosses above slow)
            if (previous['ema_fast'] <= previous['ema_slow'] and
                current['ema_fast'] > current['ema_slow']):

                return {
                    'action': 'BUY',
                    'symbol': 'SIGNAL',
                    'price': current_price,
                    'stop_loss': current_price * (1 - stop_loss_pct / 100),
                    'target': current_price * (1 + target_pct / 100)
                }

            # Bearish crossover (fast crosses below slow) - close position
            elif (previous['ema_fast'] >= previous['ema_slow'] and
                  current['ema_fast'] < current['ema_slow']):

                return {
                    'action': 'CLOSE',
                    'symbol': 'SIGNAL'
                }

            return None

        params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'stop_loss_pct': stop_loss_pct,
            'target_pct': target_pct
        }

        return self.engine.run_backtest(data, strategy_func, params)

    def backtest_rsi_strategy(
        self,
        data: pd.DataFrame,
        rsi_period: int = 14,
        oversold_level: int = 30,
        overbought_level: int = 70,
        stop_loss_pct: float = 2.0,
        target_pct: float = 4.0
    ) -> BacktestResult:
        """
        Backtest RSI Strategy

        Args:
            data: OHLCV DataFrame
            rsi_period: RSI calculation period
            oversold_level: RSI oversold threshold
            overbought_level: RSI overbought threshold
            stop_loss_pct: Stop loss percentage
            target_pct: Target percentage

        Returns:
            BacktestResult
        """
        self.logger.info(f"Backtesting RSI Strategy (Period: {rsi_period}, "
                        f"Oversold: {oversold_level}, Overbought: {overbought_level})")

        def calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
            """Calculate RSI"""
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        def strategy_func(historical_data: pd.DataFrame, params: Dict) -> Optional[Dict]:
            """RSI signal generation"""
            if len(historical_data) < rsi_period + 1:
                return None

            # Calculate RSI
            df = historical_data.copy()
            df['rsi'] = calculate_rsi(df['close'], rsi_period)

            # Get current and previous values
            current = df.iloc[-1]
            previous = df.iloc[-2]

            current_price = current['close']
            current_rsi = current['rsi']
            previous_rsi = previous['rsi']

            if pd.isna(current_rsi) or pd.isna(previous_rsi):
                return None

            # Buy signal: RSI crosses above oversold level
            if previous_rsi <= oversold_level and current_rsi > oversold_level:
                return {
                    'action': 'BUY',
                    'symbol': 'SIGNAL',
                    'price': current_price,
                    'stop_loss': current_price * (1 - stop_loss_pct / 100),
                    'target': current_price * (1 + target_pct / 100)
                }

            # Sell signal: RSI crosses below overbought level
            elif previous_rsi >= overbought_level and current_rsi < overbought_level:
                return {
                    'action': 'CLOSE',
                    'symbol': 'SIGNAL'
                }

            return None

        params = {
            'rsi_period': rsi_period,
            'oversold_level': oversold_level,
            'overbought_level': overbought_level,
            'stop_loss_pct': stop_loss_pct,
            'target_pct': target_pct
        }

        return self.engine.run_backtest(data, strategy_func, params)

    def backtest_breakout_strategy(
        self,
        data: pd.DataFrame,
        lookback_period: int = 20,
        breakout_threshold: float = 1.0,
        stop_loss_pct: float = 2.0,
        target_pct: float = 4.0
    ) -> BacktestResult:
        """
        Backtest Breakout Strategy

        Args:
            data: OHLCV DataFrame
            lookback_period: Period to look back for high/low
            breakout_threshold: Percentage above high for breakout
            stop_loss_pct: Stop loss percentage
            target_pct: Target percentage

        Returns:
            BacktestResult
        """
        self.logger.info(f"Backtesting Breakout Strategy (Lookback: {lookback_period})")

        def strategy_func(historical_data: pd.DataFrame, params: Dict) -> Optional[Dict]:
            """Breakout signal generation"""
            if len(historical_data) < lookback_period + 1:
                return None

            df = historical_data.copy()

            # Get current candle
            current = df.iloc[-1]
            current_price = current['close']

            # Calculate lookback high/low (excluding current candle)
            lookback_data = df.iloc[-(lookback_period+1):-1]
            lookback_high = lookback_data['high'].max()
            lookback_low = lookback_data['low'].min()

            # Calculate breakout level
            breakout_level = lookback_high * (1 + breakout_threshold / 100)

            # Buy signal: Price breaks above lookback high
            if current_price > breakout_level:
                return {
                    'action': 'BUY',
                    'symbol': 'SIGNAL',
                    'price': current_price,
                    'stop_loss': lookback_low,  # Use lookback low as stop
                    'target': current_price * (1 + target_pct / 100)
                }

            return None

        params = {
            'lookback_period': lookback_period,
            'breakout_threshold': breakout_threshold,
            'stop_loss_pct': stop_loss_pct,
            'target_pct': target_pct
        }

        return self.engine.run_backtest(data, strategy_func, params)

    def backtest_custom_strategy(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        strategy_params: Dict = None
    ) -> BacktestResult:
        """
        Backtest custom strategy

        Args:
            data: OHLCV DataFrame
            strategy_func: Custom strategy function
            strategy_params: Strategy parameters

        Returns:
            BacktestResult
        """
        self.logger.info("Backtesting custom strategy")

        return self.engine.run_backtest(data, strategy_func, strategy_params)

    def generate_report(self, result: BacktestResult) -> str:
        """
        Generate human-readable backtest report

        Args:
            result: BacktestResult object

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        report.append("BACKTEST RESULTS")
        report.append("=" * 70)
        report.append("")

        # Period
        report.append(f"Period: {result.start_date.date()} to {result.end_date.date()}")
        report.append(f"Duration: {result.duration_days} days")
        report.append("")

        # Capital
        report.append("CAPITAL:")
        report.append(f"  Initial Capital:  ₹{result.initial_capital:>12,.2f}")
        report.append(f"  Final Capital:    ₹{result.final_capital:>12,.2f}")
        report.append(f"  Peak Capital:     ₹{result.peak_capital:>12,.2f}")
        report.append(f"  Total P&L:        ₹{result.total_pnl:>12,.2f} ({result.total_pnl_percent:+.2f}%)")
        report.append("")

        # Trades
        report.append("TRADES:")
        report.append(f"  Total Trades:     {result.total_trades:>12}")
        report.append(f"  Winning Trades:   {result.winning_trades:>12} ({result.win_rate:.1f}%)")
        report.append(f"  Losing Trades:    {result.losing_trades:>12}")
        report.append("")

        # Profit/Loss
        report.append("PROFIT/LOSS:")
        report.append(f"  Gross Profit:     ₹{result.gross_profit:>12,.2f}")
        report.append(f"  Gross Loss:       ₹{result.gross_loss:>12,.2f}")
        report.append(f"  Avg Win:          ₹{result.avg_win:>12,.2f}")
        report.append(f"  Avg Loss:         ₹{result.avg_loss:>12,.2f}")
        report.append(f"  Largest Win:      ₹{result.largest_win:>12,.2f}")
        report.append(f"  Largest Loss:     ₹{result.largest_loss:>12,.2f}")
        report.append(f"  Profit Factor:    {result.profit_factor:>13.2f}")
        report.append("")

        # Risk metrics
        report.append("RISK METRICS:")
        report.append(f"  Max Drawdown:     ₹{result.max_drawdown:>12,.2f} ({result.max_drawdown_percent:.2f}%)")
        report.append(f"  Sharpe Ratio:     {result.sharpe_ratio:>13.2f}")
        report.append("")

        # Costs
        report.append("COSTS:")
        report.append(f"  Total Commission: ₹{result.total_commission:>12,.2f}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)
