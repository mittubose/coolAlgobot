# Neural Network Trading - Quick Start Guide

**Get started with ML trading in 10 minutes!**

---

## 🚀 Quick Start (10 Minutes)

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/mittuharibose/Documents/Mittu/Others/Learn/Algo_learning/scalping-bot

# Install PyTorch and ML dependencies
pip install torch==2.1.2 scikit-learn==1.3.2 scipy==1.11.4

# Or install all requirements
pip install -r requirements.txt
```

### Step 2: Run Example (3 minutes)

```bash
# Run complete ML example (generates sample data, trains model, backtests)
python examples/ml_strategy_example.py
```

**Expected Output**:
```
==================================================================
EXAMPLE 1: Feature Engineering
==================================================================
Generating 500 days of sample OHLCV data...
✓ Generated data from 2022-08-29 to 2024-01-10

Engineered Features:
  Shape: (500, 12)
  Features: ['rsi', 'macd', 'roc', 'sma_ratio', 'adx', 'atr',
             'bb_width', 'vwap_deviation', 'volume_ratio',
             'stochastic', 'cci', 'price_momentum']

==================================================================
EXAMPLE 3: Train TCN Model
==================================================================
Training model...
Epoch 5/50: Train Loss: 0.6821, Train Acc: 0.5423, Val Loss: 0.6789, Val Acc: 0.5512
  → New best validation accuracy: 0.5512

Early stopping triggered after 23 epochs. Best val accuracy: 0.5823

Test Set Performance:
  Loss: 0.6445
  Accuracy: 0.5641

✓ Model saved to results/tcn_model.pth

==================================================================
✓ All examples completed successfully!
==================================================================
```

### Step 3: Check Results (1 minute)

```bash
ls -lh results/

# You should see:
# - tcn_model.pth (trained model checkpoint)
# - feature_normalization_params.json (normalization parameters)
```

### Step 4: Use Model for Trading (4 minutes)

```python
# Create file: test_ml_strategy.py

import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

import pandas as pd
import numpy as np
from src.strategies.tcn_ml_strategy import TCNMLStrategy

# Load your OHLCV data (or use sample)
# Must have columns: open, high, low, close, volume
ohlc_df = pd.read_csv('data/your_data.csv', index_col='date', parse_dates=True)

# Initialize strategy with trained model
strategy = TCNMLStrategy(parameters={
    'model_path': 'results/tcn_model.pth',
    'confidence_threshold': 0.6,
    'risk_per_trade': 0.02,
    'enable_volatility_scaling': True
})

print(strategy.get_description())

# Generate signal
quote = {'last_price': ohlc_df['close'].iloc[-1]}

signal = strategy.generate_signal(
    symbol='RELIANCE',
    exchange='NSE',
    quote=quote,
    historical_data=ohlc_df,
    has_position=False
)

if signal:
    print(f"\n✓ Signal Generated:")
    print(f"  Action: {signal['action']}")
    print(f"  Price: ₹{signal['price']:.2f}")
    print(f"  Confidence: {signal['confidence']:.2%}")
    print(f"  Stop Loss: ₹{signal['stop_loss']:.2f}")
    print(f"  Target: ₹{signal['target']:.2f}")
    print(f"  Reason: {signal['reason']}")
else:
    print("\n○ No signal (insufficient confidence or data)")
```

```bash
# Run it
python test_ml_strategy.py
```

---

## 📊 Next Steps

### Option A: Backtest on Your Data

```python
# File: backtest_my_data.py

from src.ml import MLBacktestEngine
import pandas as pd

# Load YOUR historical data
df = pd.read_csv('data/RELIANCE_1year.csv', index_col='date', parse_dates=True)

# Create backtest engine
engine = MLBacktestEngine(
    initial_capital=100000,
    train_period=200,  # 200 days training
    test_period=50,    # 50 days testing
    commission_per_trade=20,
    device='cpu'
)

# Run backtest
results = engine.run_walk_forward_backtest(
    df,
    training_params={
        'epochs': 30,
        'batch_size': 32,
        'lr': 0.001
    },
    verbose=True
)

# Print results
print(f"\n{'='*70}")
print(f"BACKTEST RESULTS")
print(f"{'='*70}")
print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Total Trades: {results['total_trades']}")
print(f"{'='*70}")

# Save results
engine.save_results('results/')
```

```bash
python backtest_my_data.py
```

### Option B: Tune Hyperparameters

```python
# Try different confidence thresholds
thresholds = [0.55, 0.60, 0.65, 0.70]

for threshold in thresholds:
    strategy = TCNMLStrategy(parameters={
        'model_path': 'results/tcn_model.pth',
        'confidence_threshold': threshold
    })

    # Test and compare...
```

### Option C: Paper Trade

```python
# Integrate with your dashboard (run_dashboard.py)
# The TCN strategy is now available in strategy list!

# In dashboard, select:
# Strategy: "TCN Neural Network"
# Mode: "Paper Trading"
# Capital: ₹10,000 (start small)
```

---

## 🎯 Performance Checklist

Before going live, ensure:

- [ ] **Backtest Return**: >15% over 6 months
- [ ] **Sharpe Ratio**: >1.0
- [ ] **Max Drawdown**: <15%
- [ ] **Win Rate**: >50%
- [ ] **Paper Trading**: 30 days profitable
- [ ] **Model Retraining**: Set up monthly schedule
- [ ] **Emergency Stop**: Tested and working

---

## ⚠️ Common Issues

### Issue 1: "Model not found"

```bash
# Solution: Train model first
python examples/ml_strategy_example.py

# Check it exists
ls results/tcn_model.pth
```

### Issue 2: "Insufficient data"

```bash
# Solution: Need 200+ candles minimum

# Check your data
python -c "
import pandas as pd
df = pd.read_csv('data/your_data.csv')
print(f'Data points: {len(df)}')
"

# If <200, download more historical data
```

### Issue 3: "CUDA out of memory"

```python
# Solution: Use CPU instead
engine = MLBacktestEngine(device='cpu')  # Change from 'cuda'
```

### Issue 4: "Model always predicts 0.5"

```python
# Solution: Train longer or balance classes

# Check class distribution
from src.ml import TimeSeriesDataPipeline
pipeline = TimeSeriesDataPipeline()
labels = pipeline.create_labels_from_future_returns(df['close'], threshold=0.01)
print(f"Class 0: {(labels==0).sum()}, Class 1: {(labels==1).sum()}")

# If very imbalanced (>70/30), use balancing:
X_balanced, y_balanced = pipeline.balance_classes(X, y, method='undersample')
```

---

## 📚 Learn More

- **Complete Guide**: `src/ml/README.md` (50+ pages)
- **Implementation Details**: `ML_IMPLEMENTATION_SUMMARY.md`
- **Example Code**: `examples/ml_strategy_example.py`
- **Tests**: `tests/ml/test_feature_engineering.py`

---

## 🎓 How It Works (Simple Explanation)

1. **Features**: Calculates 12 indicators (RSI, MACD, etc.) and normalizes them
2. **Windows**: Takes last 64 candles as input sequence
3. **Model**: Neural network learns patterns from historical data
4. **Probability**: Outputs 0-1 (0=bearish, 1=bullish)
5. **Scaling**: Adjusts position size based on market volatility
6. **Signal**: If probability >0.6, generates BUY signal

```
64 candles → 12 features → Neural Network → 0.75 probability → BUY signal
```

---

## 🚀 Ready to Go Live?

### Pre-Flight Checklist

```bash
# 1. Backtest passed? (6 months, >15% return, Sharpe >1.0)
python backtest_my_data.py

# 2. Paper trade for 30 days
# Use dashboard with mode='paper'

# 3. Set up monitoring
# Track daily: P&L, win rate, Sharpe ratio

# 4. Start small
# Initial capital: ₹10,000-20,000

# 5. Emergency stop ready
# Test kill switch in dashboard

# 6. Model retraining scheduled
# Set calendar reminder: Retrain every 30 days
```

### Go Live Command

```python
# When ready (after paper trading success)
from src.strategies.tcn_ml_strategy import TCNMLStrategy
from backend.oms.order_manager import OrderManager

strategy = TCNMLStrategy(parameters={
    'model_path': 'results/tcn_model.pth',
    'confidence_threshold': 0.6,
    'enable_volatility_scaling': True
})

order_manager = OrderManager(
    broker=your_broker,
    capital=10000,  # START SMALL!
    mode='live'     # ⚠️ REAL MONEY
)

# Your trading loop here...
```

---

## 💡 Pro Tips

1. **Start Conservative**: Use threshold=0.65 (fewer trades, higher quality)
2. **Monitor Daily**: Check model confidence distribution
3. **Retrain Monthly**: Markets change, model needs updates
4. **Compare Strategies**: Run ML + EMA simultaneously, pick better performer
5. **Log Everything**: Save all predictions for later analysis

---

## 🎉 Success!

You now have a working neural network trading strategy!

**What You Built**:
- ✅ 12-feature engineering pipeline
- ✅ TCN neural network model
- ✅ Volatility-scaled position sizing
- ✅ Walk-forward backtesting
- ✅ Live trading integration

**Time to First Trade**: 10 minutes (with examples)
**Time to Production**: 30-60 days (with proper testing)

---

**Questions? Check**:
- `src/ml/README.md` - Full documentation
- `examples/ml_strategy_example.py` - Working code
- `ML_IMPLEMENTATION_SUMMARY.md` - Complete overview

**Happy Trading! 🚀📈**
