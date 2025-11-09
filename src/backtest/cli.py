#!/usr/bin/env python3
"""
Backtest CLI
Command-line interface for running backtests
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtest import StrategyBacktester, PerformanceAnalyzer
from src.utils.ohlc_generator import OHLCGenerator


def load_data(source: str, symbol: str = 'NIFTY50', start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Load OHLC data from source"""

    if source == 'mock':
        # Generate mock data
        generator = OHLCGenerator()

        # Calculate number of candles based on date range
        if start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days = (end - start).days
            candles = days * 75  # ~75 5-minute candles per trading day
        else:
            candles = 1000  # Default

        data = generator.generate_candles(count=candles, timeframe='5m')
        return pd.DataFrame(data)

    elif source.endswith('.csv'):
        # Load from CSV file
        df = pd.DataFrame(source)
        # Ensure required columns
        required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        return df

    else:
        raise ValueError(f"Unknown data source: {source}")


def main():
    parser = argparse.ArgumentParser(description='Backtest trading strategies')

    # Data options
    parser.add_argument('--data', type=str, default='mock',
                       help='Data source: "mock" or path to CSV file')
    parser.add_argument('--symbol', type=str, default='NIFTY50',
                       help='Trading symbol')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD)')

    # Strategy options
    parser.add_argument('--strategy', type=str, required=True,
                       choices=['ema_crossover', 'rsi', 'breakout'],
                       help='Strategy to backtest')

    # EMA Crossover parameters
    parser.add_argument('--fast-ema', type=int, default=9,
                       help='Fast EMA period (default: 9)')
    parser.add_argument('--slow-ema', type=int, default=21,
                       help='Slow EMA period (default: 21)')

    # RSI parameters
    parser.add_argument('--rsi-period', type=int, default=14,
                       help='RSI period (default: 14)')
    parser.add_argument('--oversold', type=int, default=30,
                       help='RSI oversold level (default: 30)')
    parser.add_argument('--overbought', type=int, default=70,
                       help='RSI overbought level (default: 70)')

    # Breakout parameters
    parser.add_argument('--lookback', type=int, default=20,
                       help='Breakout lookback period (default: 20)')
    parser.add_argument('--threshold', type=float, default=1.0,
                       help='Breakout threshold % (default: 1.0)')

    # Risk parameters
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital (default: 100000)')
    parser.add_argument('--commission', type=float, default=20,
                       help='Commission per trade (default: 20)')
    parser.add_argument('--risk-per-trade', type=float, default=2.0,
                       help='Risk per trade % (default: 2.0)')
    parser.add_argument('--stop-loss', type=float, default=2.0,
                       help='Stop loss % (default: 2.0)')
    parser.add_argument('--target', type=float, default=4.0,
                       help='Target % (default: 4.0)')

    # Output options
    parser.add_argument('--output', type=str,
                       help='Output JSON file path')
    parser.add_argument('--trade-log', type=str,
                       help='Trade log CSV file path')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}...")
    data = load_data(args.data, args.symbol, args.start_date, args.end_date)
    print(f"Loaded {len(data)} candles")

    # Initialize backtester
    backtester = StrategyBacktester(
        initial_capital=args.capital,
        commission_per_trade=args.commission,
        risk_per_trade=args.risk_per_trade / 100
    )

    # Run backtest
    print(f"\nRunning {args.strategy} strategy backtest...")
    print(f"Initial capital: ₹{args.capital:,.2f}")
    print("-" * 70)

    if args.strategy == 'ema_crossover':
        result = backtester.backtest_ema_crossover(
            data,
            fast_period=args.fast_ema,
            slow_period=args.slow_ema,
            stop_loss_pct=args.stop_loss,
            target_pct=args.target
        )
    elif args.strategy == 'rsi':
        result = backtester.backtest_rsi_strategy(
            data,
            rsi_period=args.rsi_period,
            oversold_level=args.oversold,
            overbought_level=args.overbought,
            stop_loss_pct=args.stop_loss,
            target_pct=args.target
        )
    elif args.strategy == 'breakout':
        result = backtester.backtest_breakout_strategy(
            data,
            lookback_period=args.lookback,
            breakout_threshold=args.threshold,
            stop_loss_pct=args.stop_loss,
            target_pct=args.target
        )

    # Print results
    print("\n" + backtester.generate_report(result))

    # Save results to JSON
    if args.output:
        output_data = PerformanceAnalyzer.generate_comprehensive_report(result)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")

    # Save trade log to CSV
    if args.trade_log:
        trade_df = PerformanceAnalyzer.generate_trade_log(result)
        trade_path = Path(args.trade_log)
        trade_path.parent.mkdir(parents=True, exist_ok=True)

        trade_df.to_csv(trade_path, index=False)
        print(f"Trade log saved to: {trade_path}")

    # Print detailed analysis if verbose
    if args.verbose:
        print("\n" + "=" * 70)
        print("DETAILED ANALYSIS")
        print("=" * 70)

        # Monthly performance
        monthly = PerformanceAnalyzer.analyze_monthly_performance(result)
        if not monthly.empty:
            print("\nMONTHLY PERFORMANCE:")
            print(monthly.to_string(index=False))

        # Exit reasons
        exit_analysis = PerformanceAnalyzer.analyze_exit_reasons(result)
        if exit_analysis:
            print("\nEXIT REASONS:")
            for reason, count in exit_analysis['counts'].items():
                pnl = exit_analysis['total_pnl'][reason]
                avg = exit_analysis['avg_pnl'][reason]
                print(f"  {reason:20s}: {count:3d} trades, Total P&L: ₹{pnl:>10,.2f}, Avg: ₹{avg:>8,.2f}")

        # Holding periods
        holding = PerformanceAnalyzer.analyze_holding_periods(result)
        if holding:
            print("\nHOLDING PERIODS:")
            print(f"  Average:   {holding['avg_hours']:.1f} hours")
            print(f"  Median:    {holding['median_hours']:.1f} hours")
            print(f"  Min:       {holding['min_hours']:.1f} hours")
            print(f"  Max:       {holding['max_hours']:.1f} hours")

        # Streaks
        streaks = PerformanceAnalyzer.calculate_consecutive_wins_losses(result)
        if streaks:
            print("\nCONSECUTIVE STREAKS:")
            print(f"  Max Winning Streak:  {streaks['max_consecutive_wins']}")
            print(f"  Max Losing Streak:   {streaks['max_consecutive_losses']}")

        # Advanced metrics
        print("\nADVANCED METRICS:")
        print(f"  Recovery Factor:     {PerformanceAnalyzer.calculate_recovery_factor(result):.2f}")
        print(f"  Expectancy:          ₹{PerformanceAnalyzer.calculate_expectancy(result):,.2f}")

    # Return exit code based on profitability
    return 0 if result.total_pnl >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
