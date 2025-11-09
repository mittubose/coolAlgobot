# Scalping Bot - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Broker Setup](#broker-setup)
4. [Strategy Development](#strategy-development)
5. [Running Strategies](#running-strategies)
6. [API Reference](#api-reference)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd scalping-bot

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 init_database.py
```

### 2. Configure Broker Credentials

Edit `config/secrets.env`:
```env
API_SECRET=your_broker_api_secret_here
```

Edit `config/config.yaml`:
```yaml
broker:
  name: zerodha
  api_key: your_api_key_here
  redirect_url: http://127.0.0.1:8050/callback
```

### 3. Start Dashboard

```bash
python3 run_dashboard.py
```

Visit `http://localhost:8050` in your browser.

---

## Configuration

### Risk Management Settings

Edit `config/config.yaml`:

```yaml
risk:
  capital: 100000              # Total trading capital
  max_risk_per_trade: 1.0      # Max % of capital to risk per trade
  max_position_size: 10.0      # Max % of capital per position
  max_daily_loss: 3000         # Max daily loss in rupees
  max_daily_loss_pct: 3.0      # Max daily loss as % of capital
  max_positions: 3             # Maximum concurrent positions
  max_drawdown_pct: 10.0       # Max drawdown before stopping
```

### Trading Settings

```yaml
trading:
  mode: paper                  # paper or live
  timeframe: 5minute           # Default timeframe
  market_hours:
    start: "09:15"
    end: "15:30"
```

---

## Broker Setup

### Zerodha Kite Connect

1. **Get API Credentials:**
   - Sign up at https://kite.trade/
   - Create an app and get API key & secret

2. **Configure:**
   ```python
   from src.brokers import create_broker

   broker = create_broker('zerodha', api_key, api_secret)
   broker.interactive_login()  # Follow OAuth flow
   ```

3. **Test Connection:**
   ```bash
   curl -X POST http://localhost:8050/api/broker/test
   ```

### Adding New Brokers

Implement the `BaseBroker` interface in `src/brokers/`:

```python
from src.brokers.base_broker import BaseBroker

class MyBroker(BaseBroker):
    def authenticate(self):
        # Implement authentication
        pass

    def place_order(self, **kwargs):
        # Implement order placement
        pass

    # Implement all required methods...
```

---

## Strategy Development

### Using Built-in Strategies

#### 1. EMA Crossover Strategy

```python
from src.brokers import create_broker
from src.trading import StrategyExecutor
from src.strategies import EMACrossoverStrategy

# Broker setup
broker = create_broker('zerodha', api_key, api_secret)
broker.interactive_login()

# Strategy configuration
strategy_config = {
    'name': 'EMA_9_21',
    'strategy_type': 'ema_crossover',
    'symbols': [
        {'symbol': 'RELIANCE', 'exchange': 'NSE'},
        {'symbol': 'TCS', 'exchange': 'NSE'}
    ],
    'parameters': {
        'fast_period': 9,
        'slow_period': 21,
        'timeframe': '5minute',
        'risk_reward_ratio': 2.0,
        'atr_sl_multiplier': 1.5,
        'scan_interval': 5
    }
}

# Risk configuration
risk_config = {
    'capital': 100000,
    'max_risk_per_trade': 1.0,
    'max_position_size': 10.0,
    'max_daily_loss': 3000,
    'max_positions': 3
}

# Create executor
executor = StrategyExecutor(
    broker=broker,
    strategy_config=strategy_config,
    risk_config=risk_config,
    mode='paper'
)

# Start trading
executor.start()

# Check status
print(executor.get_summary())

# Stop when done
executor.stop()
```

#### 2. RSI Strategy

```python
strategy_config = {
    'name': 'RSI_Reversal',
    'strategy_type': 'rsi_strategy',
    'symbols': ['RELIANCE', 'INFY'],
    'parameters': {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70,
        'middle_exit': 50,
        'timeframe': '5minute',
        'sl_percentage': 2.0,
        'target_percentage': 3.0
    }
}
```

#### 3. Breakout Strategy

```python
strategy_config = {
    'name': 'Breakout_Trade',
    'strategy_type': 'breakout',
    'symbols': ['NIFTY', 'BANKNIFTY'],
    'parameters': {
        'lookback_period': 20,
        'breakout_threshold': 0.5,
        'volume_confirmation': True,
        'volume_multiplier': 1.5,
        'timeframe': '15minute',
        'sl_percentage': 1.5,
        'risk_reward_ratio': 2.5
    }
}
```

### Creating Custom Strategies

#### Option 1: Using Callback Function

```python
def my_custom_strategy(symbol, exchange, quote, has_position):
    """
    Custom signal generation logic

    Args:
        symbol: Trading symbol
        exchange: Exchange name
        quote: Current quote dict
        has_position: Boolean indicating existing position

    Returns:
        Signal dict or None
    """
    ltp = quote.get('last_price')

    # Your custom logic here
    if not has_position and ltp < 2500:
        return {
            'action': 'BUY',
            'symbol': symbol,
            'exchange': exchange,
            'price': ltp,
            'stop_loss': ltp * 0.98,
            'target': ltp * 1.04,
            'reason': 'Price below 2500'
        }

    elif has_position and ltp > 2600:
        return {
            'action': 'CLOSE',
            'symbol': symbol,
            'exchange': exchange,
            'price': ltp,
            'reason': 'Target reached'
        }

    return None

# Register callback
executor.set_signal_callback(my_custom_strategy)
```

#### Option 2: Creating Strategy Class

```python
# src/strategies/my_strategy.py

import pandas as pd
from typing import Dict, Optional

class MyCustomStrategy:
    def __init__(self, parameters: Dict):
        self.param1 = parameters.get('param1', default_value)
        self.param2 = parameters.get('param2', default_value)

    def generate_signal(
        self,
        symbol: str,
        exchange: str,
        quote: Dict,
        historical_data: pd.DataFrame,
        has_position: bool
    ) -> Optional[Dict]:
        """Generate trading signal"""

        # Your logic using historical_data
        # Calculate indicators
        # Detect patterns
        # Return signal dict or None

        return None

    def get_description(self) -> str:
        return "My Custom Strategy Description"

    def get_parameters(self) -> Dict:
        return {'param1': self.param1, 'param2': self.param2}
```

---

## Running Strategies

### Via Python Script

```python
# run_strategy.py

from src.brokers import create_broker
from src.trading import StrategyExecutor

# Setup
broker = create_broker('zerodha', api_key, api_secret)
broker.interactive_login()

# Start trading
executor = StrategyExecutor(broker, strategy_config, risk_config, mode='paper')
executor.start()

# Run until interrupted
try:
    while True:
        time.sleep(60)
        status = executor.get_summary()
        print(f"Status: {status}")
except KeyboardInterrupt:
    print("Stopping...")
    executor.stop()
```

### Via Dashboard API

```bash
# Create strategy via API
curl -X POST http://localhost:8050/api/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Strategy",
    "description": "EMA crossover on Nifty 50",
    "strategy_type": "ema_crossover",
    "parameters": {
      "fast_period": 9,
      "slow_period": 21,
      "symbols": ["RELIANCE", "TCS"]
    }
  }'

# Deploy strategy
curl -X POST http://localhost:8050/api/strategies/1/deploy \
  -H "Content-Type: application/json" \
  -d '{"mode": "paper"}'

# Check status
curl http://localhost:8050/api/engine/status
```

---

## API Reference

### Strategy Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | List all strategies |
| GET | `/api/strategies/<id>` | Get strategy details |
| POST | `/api/strategies` | Create new strategy |
| PUT | `/api/strategies/<id>` | Update strategy |
| DELETE | `/api/strategies/<id>` | Delete strategy |
| POST | `/api/strategies/<id>/deploy` | Deploy strategy |
| POST | `/api/strategies/<id>/backtest` | Run backtest |
| GET | `/api/strategies/templates` | Get templates |

### Settings Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings/trading` | Update trading settings |
| PUT | `/api/settings/risk` | Update risk settings |
| PUT | `/api/settings/alerts` | Update alert settings |

### Broker Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/brokers/supported` | List supported brokers |
| GET | `/api/broker/current` | Get current broker |
| POST | `/api/broker/configure` | Configure broker |
| POST | `/api/broker/test` | Test connection |

### Trading Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/engine/status` | Get engine status |
| POST | `/api/engine/start` | Start engine |
| POST | `/api/engine/stop` | Stop engine |

---

## Monitoring & Logging

### Log Files

Logs are stored in `logs/` directory:

- `system.log` - System events and errors
- `trades.log` - Trade executions
- `signals.log` - Trading signals
- `errors.log` - Error messages

### Viewing Logs

```bash
# Tail system log
tail -f logs/system.log

# View recent trades
tail -n 50 logs/trades.log

# Search for errors
grep "ERROR" logs/system.log
```

### Dashboard Monitoring

1. **Main Dashboard** - Real-time P&L, positions, stats
2. **Strategies Page** - Strategy performance
3. **Analytics Page** - Charts and metrics
4. **History Page** - Trade history

---

## Troubleshooting

### Common Issues

#### 1. "Authentication Failed"

```bash
# Check API credentials
cat config/secrets.env
cat config/config.yaml

# Re-authenticate
python3 -c "from src.brokers import create_broker; \
broker = create_broker('zerodha', 'key', 'secret'); \
broker.interactive_login()"
```

#### 2. "Database Error"

```bash
# Reinitialize database
python3 init_database.py

# Check database file
ls -lh data/trading.db
```

#### 3. "Module Import Error"

```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

#### 4. "Trading Halted - Daily Loss Limit"

Check `config/config.yaml` risk settings:
```yaml
risk:
  max_daily_loss: 3000  # Increase if needed
```

Wait until next day or manually reset:
```python
from src.trading import RiskManager

risk_manager = RiskManager(risk_config)
risk_manager.resume_trading()
```

---

## Advanced Usage

### Paper Trading vs Live Trading

```python
# Paper trading (simulated)
executor = StrategyExecutor(broker, strategy_config, risk_config, mode='paper')

# Live trading (real money!)
executor = StrategyExecutor(broker, strategy_config, risk_config, mode='live')
```

Always test strategies in paper trading mode first!

### Emergency Stop

```python
# Stop everything and close all positions
executor.emergency_stop()
```

### Position Management

```python
# Check current positions
positions = executor.position_tracker.get_all_positions()
print(f"Open positions: {len(positions)}")

# Close specific position
executor.position_tracker.close_position('RELIANCE', 'NSE')

# Get P&L summary
summary = executor.position_tracker.get_summary()
print(f"Total P&L: {summary['total_pnl']}")
```

### Custom Risk Rules

```python
# Create custom risk manager
from src.trading import RiskManager

custom_risk_config = {
    'capital': 200000,
    'max_risk_per_trade': 0.5,  # More conservative
    'max_position_size': 5.0,
    'max_daily_loss': 2000,
    'max_positions': 2,          # Fewer concurrent positions
    'max_drawdown_pct': 5.0      # Tighter drawdown limit
}

risk_manager = RiskManager(custom_risk_config)
```

---

## Best Practices

### 1. Start with Paper Trading
Always test new strategies in paper trading mode before going live.

### 2. Set Appropriate Risk Limits
- Never risk more than 1-2% per trade
- Set daily loss limits
- Use position sizing

### 3. Monitor Regularly
- Check dashboard frequently
- Review logs daily
- Analyze performance weekly

### 4. Backtest First
Run backtests before deploying strategies:
```bash
curl -X POST http://localhost:8050/api/strategies/1/backtest \
  -d '{"start_date": "2024-01-01", "end_date": "2024-10-01"}'
```

### 5. Keep Logs
Maintain detailed logs for audit and analysis.

### 6. Use Version Control
Track strategy changes in git.

---

## Support

- **Documentation:** See `docs/` directory
- **FAQ:** See `docs/FAQ.md`
- **Implementation Guide:** See `IMPLEMENTATION_SUMMARY.md`

---

*Last Updated: October 21, 2025*
