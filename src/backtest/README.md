# Backtesting Engine

Production-ready backtesting system for trading strategies without external dependencies (no backtrader required).

## Features

- ✅ **Complete OHLCV simulation** - Process historical data candle by candle
- ✅ **Stop-loss & target execution** - Automatic exit on SL/target hit
- ✅ **Position sizing** - Risk-based position calculation (default 2% risk per trade)
- ✅ **Commission & slippage** - Realistic cost modeling
- ✅ **Multiple concurrent positions** - Support up to 5 simultaneous trades
- ✅ **Comprehensive metrics** - 20+ performance metrics including Sharpe ratio, drawdown, profit factor
- ✅ **Built-in strategies** - EMA Crossover, RSI, Breakout
- ✅ **Custom strategy support** - Easy to add your own strategies

## Quick Start

### Command Line

```bash
# EMA Crossover strategy
python src/backtest/cli.py \
  --strategy ema_crossover \
  --capital 100000 \
  --fast-ema 9 \
  --slow-ema 21 \
  --stop-loss 2.0 \
  --target 4.0 \
  --verbose

# RSI strategy
python src/backtest/cli.py \
  --strategy rsi \
  --capital 100000 \
  --rsi-period 14 \
  --oversold 30 \
  --overbought 70 \
  --verbose

# Breakout strategy
python src/backtest/cli.py \
  --strategy breakout \
  --capital 100000 \
  --lookback 20 \
  --threshold 1.0 \
  --verbose

# Save results
python src/backtest/cli.py \
  --strategy ema_crossover \
  --output results/backtest_ema.json \
  --trade-log results/trades_ema.csv
```

### Python API

```python
from src.backtest import StrategyBacktester, PerformanceAnalyzer
import pandas as pd

# Load your OHLCV data
data = pd.DataFrame({
    'time': [...],
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Initialize backtester
backtester = StrategyBacktester(
    initial_capital=100000,
    commission_per_trade=20,
    risk_per_trade=0.02  # 2%
)

# Run backtest
result = backtester.backtest_ema_crossover(
    data,
    fast_period=9,
    slow_period=21,
    stop_loss_pct=2.0,
    target_pct=4.0
)

# Print report
print(backtester.generate_report(result))

# Get detailed analysis
analysis = PerformanceAnalyzer.generate_comprehensive_report(result)
print(f"Total P&L: ₹{result.total_pnl:,.2f}")
print(f"Win Rate: {result.win_rate:.1f}%")
print(f"Max Drawdown: {result.max_drawdown_percent:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

## Custom Strategy

```python
from src.backtest import BacktestEngine

def my_custom_strategy(historical_data, params):
    """
    Custom strategy function

    Args:
        historical_data: DataFrame with OHLCV data up to current point
        params: Strategy parameters dict

    Returns:
        Signal dict or None
    """
    if len(historical_data) < 50:
        return None

    df = historical_data.copy()
    current_price = df.iloc[-1]['close']

    # Your strategy logic here
    # ...

    if buy_condition:
        return {
            'action': 'BUY',
            'symbol': 'STOCK',
            'price': current_price,
            'stop_loss': current_price * 0.98,
            'target': current_price * 1.04
        }

    if sell_condition:
        return {
            'action': 'CLOSE',
            'symbol': 'STOCK'
        }

    return None

# Run backtest
engine = BacktestEngine(initial_capital=100000)
result = engine.run_backtest(data, my_custom_strategy, params={})
```

## Performance Metrics

### Basic Metrics
- Total trades, winning/losing trades, win rate
- Gross profit/loss, average win/loss
- Total P&L (absolute and percentage)
- Total commission paid

### Risk Metrics
- **Max Drawdown** - Largest peak-to-trough decline
- **Profit Factor** - Gross profit / gross loss (>1.5 is good)
- **Sharpe Ratio** - Risk-adjusted return (>1.0 is good, >2.0 is excellent)
- **Recovery Factor** - Net profit / max drawdown

### Trade Analysis
- Exit reason breakdown (stop-loss, target, signal, end-of-backtest)
- Holding period statistics (min, max, average)
- Consecutive win/loss streaks
- Monthly performance breakdown
- Trade distribution (percentiles, standard deviation)

### Advanced Metrics
- **Expectancy** - Average expected profit per trade
- **Equity curve** - Capital over time
- **Trade log** - Complete trade-by-trade record

## Exit Reasons

Trades can exit for the following reasons:

1. **`target_hit`** - Take profit level reached
2. **`stop_loss`** - Stop-loss level hit
3. **`signal`** - Exit signal from strategy (e.g., opposite signal)
4. **`backtest_end`** - End of backtest period (forces close)

## Data Format

Input data must be a pandas DataFrame with these columns:

```python
{
    'time': datetime,      # Timestamp
    'open': float,         # Opening price
    'high': float,         # High price
    'low': float,          # Low price
    'close': float,        # Closing price
    'volume': int          # Volume
}
```

## CLI Options

```bash
# Data options
--data mock              # Use mock data (default)
--data path/to/data.csv  # Load from CSV file
--symbol NIFTY50         # Trading symbol
--start-date 2024-01-01  # Start date
--end-date 2024-10-01    # End date

# Strategy selection
--strategy ema_crossover|rsi|breakout

# EMA Crossover parameters
--fast-ema 9             # Fast EMA period
--slow-ema 21            # Slow EMA period

# RSI parameters
--rsi-period 14          # RSI period
--oversold 30            # Oversold level
--overbought 70          # Overbought level

# Breakout parameters
--lookback 20            # Lookback period
--threshold 1.0          # Breakout threshold %

# Risk parameters
--capital 100000         # Initial capital
--commission 20          # Commission per trade
--risk-per-trade 2.0     # Risk per trade %
--stop-loss 2.0          # Stop loss %
--target 4.0             # Target %

# Output options
--output results.json    # Save results to JSON
--trade-log trades.csv   # Save trade log to CSV
--verbose                # Detailed analysis
```

## Integration with Dashboard

The backtesting engine integrates with the dashboard via the `/api/strategies/<id>/backtest` endpoint:

```python
POST /api/strategies/123/backtest
{
    "period": "6months",
    "initial_capital": 100000,
    "commission": 20,
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
}
```

## Example Results

```
======================================================================
BACKTEST RESULTS
======================================================================

Period: 2024-01-01 to 2024-06-30
Duration: 181 days

CAPITAL:
  Initial Capital:  ₹  100,000.00
  Final Capital:    ₹  112,450.00
  Peak Capital:     ₹  118,200.00
  Total P&L:        ₹   12,450.00 (+12.45%)

TRADES:
  Total Trades:               47
  Winning Trades:             28 (59.6%)
  Losing Trades:              19

PROFIT/LOSS:
  Gross Profit:     ₹   28,920.00
  Gross Loss:       ₹   15,530.00
  Avg Win:          ₹    1,032.86
  Avg Loss:         ₹     -817.37
  Largest Win:      ₹    3,200.00
  Largest Loss:     ₹   -2,100.00
  Profit Factor:             1.86

RISK METRICS:
  Max Drawdown:     ₹    5,750.00 (4.87%)
  Sharpe Ratio:              1.42

COSTS:
  Total Commission: ₹      940.00

======================================================================
```

## Best Practices

1. **Realistic parameters** - Use actual commission rates and slippage
2. **Sufficient data** - Backtest on at least 6 months of data
3. **Out-of-sample testing** - Test on data not used for optimization
4. **Multiple timeframes** - Test on different market conditions
5. **Risk management** - Always use stop-losses and position sizing
6. **Paper trading** - Test strategies in paper mode before live trading

## Known Limitations

- **Look-ahead bias prevention** - Strategy only receives data up to current candle
- **Intraday only** - Designed for intraday strategies (positions closed at end)
- **Single symbol** - Currently supports one symbol at a time
- **No partial fills** - Orders assumed to fill completely at price
- **Fixed slippage** - Uses percentage-based slippage model

## Future Enhancements

- [ ] Multi-symbol backtesting
- [ ] Options and futures support
- [ ] Walk-forward optimization
- [ ] Monte Carlo simulation
- [ ] Portfolio-level backtesting
- [ ] Real broker data integration
- [ ] Genetic algorithm optimization
