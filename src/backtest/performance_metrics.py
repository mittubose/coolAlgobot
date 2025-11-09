"""
Performance Metrics Analyzer
Advanced performance analysis and visualization
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

from .backtest_engine import BacktestResult, Trade


class PerformanceAnalyzer:
    """
    Advanced performance analysis for backtest results

    Provides:
    - Monthly/daily performance breakdown
    - Trade distribution analysis
    - Time-based metrics
    - Risk-adjusted returns
    """

    @staticmethod
    def analyze_monthly_performance(result: BacktestResult) -> pd.DataFrame:
        """
        Analyze performance by month

        Args:
            result: BacktestResult object

        Returns:
            DataFrame with monthly breakdown
        """
        if not result.trades:
            return pd.DataFrame()

        trades_data = []
        for trade in result.trades:
            if trade.exit_time:
                trades_data.append({
                    'date': trade.exit_time,
                    'pnl': trade.pnl,
                    'pnl_percent': trade.pnl_percent
                })

        df = pd.DataFrame(trades_data)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')

        monthly = df.groupby('month').agg({
            'pnl': ['sum', 'mean', 'count'],
            'pnl_percent': 'mean'
        }).round(2)

        monthly.columns = ['total_pnl', 'avg_pnl', 'num_trades', 'avg_return_pct']
        monthly = monthly.reset_index()
        monthly['month'] = monthly['month'].astype(str)

        return monthly

    @staticmethod
    def analyze_trade_distribution(result: BacktestResult) -> Dict:
        """
        Analyze trade P&L distribution

        Args:
            result: BacktestResult object

        Returns:
            Dictionary with distribution statistics
        """
        if not result.trades:
            return {}

        pnl_values = [t.pnl for t in result.trades]
        pnl_percent_values = [t.pnl_percent for t in result.trades]

        return {
            'pnl_mean': np.mean(pnl_values),
            'pnl_median': np.median(pnl_values),
            'pnl_std': np.std(pnl_values),
            'pnl_min': min(pnl_values),
            'pnl_max': max(pnl_values),
            'pnl_25th_percentile': np.percentile(pnl_values, 25),
            'pnl_75th_percentile': np.percentile(pnl_values, 75),
            'return_mean_pct': np.mean(pnl_percent_values),
            'return_median_pct': np.median(pnl_percent_values),
            'return_std_pct': np.std(pnl_percent_values)
        }

    @staticmethod
    def analyze_exit_reasons(result: BacktestResult) -> Dict:
        """
        Analyze how trades were exited

        Args:
            result: BacktestResult object

        Returns:
            Dictionary with exit reason breakdown
        """
        if not result.trades:
            return {}

        exit_counts = {}
        exit_pnl = {}

        for trade in result.trades:
            reason = trade.exit_reason
            exit_counts[reason] = exit_counts.get(reason, 0) + 1
            exit_pnl[reason] = exit_pnl.get(reason, 0) + trade.pnl

        return {
            'counts': exit_counts,
            'total_pnl': exit_pnl,
            'avg_pnl': {
                reason: exit_pnl[reason] / exit_counts[reason]
                for reason in exit_counts
            }
        }

    @staticmethod
    def analyze_holding_periods(result: BacktestResult) -> Dict:
        """
        Analyze trade holding periods

        Args:
            result: BacktestResult object

        Returns:
            Dictionary with holding period statistics
        """
        if not result.trades:
            return {}

        holding_periods = []
        for trade in result.trades:
            if trade.exit_time and trade.entry_time:
                # Convert to datetime if needed
                exit_time = pd.to_datetime(trade.exit_time)
                entry_time = pd.to_datetime(trade.entry_time)
                duration = (exit_time - entry_time).total_seconds() / 3600  # hours
                holding_periods.append(duration)

        if not holding_periods:
            return {}

        return {
            'avg_hours': np.mean(holding_periods),
            'median_hours': np.median(holding_periods),
            'min_hours': min(holding_periods),
            'max_hours': max(holding_periods),
            'std_hours': np.std(holding_periods)
        }

    @staticmethod
    def calculate_consecutive_wins_losses(result: BacktestResult) -> Dict:
        """
        Calculate consecutive wins and losses

        Args:
            result: BacktestResult object

        Returns:
            Dictionary with consecutive streak statistics
        """
        if not result.trades:
            return {}

        current_win_streak = 0
        current_loss_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for trade in result.trades:
            if trade.pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)

        return {
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': max_loss_streak
        }

    @staticmethod
    def calculate_recovery_factor(result: BacktestResult) -> float:
        """
        Calculate recovery factor (Net Profit / Max Drawdown)

        Args:
            result: BacktestResult object

        Returns:
            Recovery factor
        """
        if result.max_drawdown == 0:
            return 0.0

        return result.total_pnl / result.max_drawdown

    @staticmethod
    def calculate_expectancy(result: BacktestResult) -> float:
        """
        Calculate expectancy (average expected profit per trade)

        Args:
            result: BacktestResult object

        Returns:
            Expectancy value
        """
        if result.total_trades == 0:
            return 0.0

        win_rate = result.win_rate / 100
        loss_rate = 1 - win_rate

        expectancy = (win_rate * result.avg_win) - (loss_rate * abs(result.avg_loss))
        return expectancy

    @staticmethod
    def generate_comprehensive_report(result: BacktestResult) -> Dict:
        """
        Generate comprehensive performance analysis

        Args:
            result: BacktestResult object

        Returns:
            Dictionary with all performance metrics
        """
        analyzer = PerformanceAnalyzer()

        return {
            'basic_metrics': result.to_dict(),
            'monthly_performance': analyzer.analyze_monthly_performance(result).to_dict('records'),
            'trade_distribution': analyzer.analyze_trade_distribution(result),
            'exit_reasons': analyzer.analyze_exit_reasons(result),
            'holding_periods': analyzer.analyze_holding_periods(result),
            'consecutive_streaks': analyzer.calculate_consecutive_wins_losses(result),
            'recovery_factor': analyzer.calculate_recovery_factor(result),
            'expectancy': analyzer.calculate_expectancy(result)
        }

    @staticmethod
    def generate_trade_log(result: BacktestResult) -> pd.DataFrame:
        """
        Generate detailed trade log

        Args:
            result: BacktestResult object

        Returns:
            DataFrame with all trades
        """
        if not result.trades:
            return pd.DataFrame()

        trades_data = []
        for idx, trade in enumerate(result.trades, 1):
            trades_data.append({
                'trade_num': idx,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'symbol': trade.symbol,
                'side': trade.side,
                'quantity': trade.quantity,
                'entry_price': round(trade.entry_price, 2),
                'exit_price': round(trade.exit_price, 2) if trade.exit_price else None,
                'stop_loss': round(trade.stop_loss, 2) if trade.stop_loss else None,
                'target': round(trade.target, 2) if trade.target else None,
                'pnl': round(trade.pnl, 2),
                'pnl_percent': round(trade.pnl_percent, 2),
                'commission': round(trade.commission, 2),
                'exit_reason': trade.exit_reason,
                'status': trade.status
            })

        return pd.DataFrame(trades_data)
