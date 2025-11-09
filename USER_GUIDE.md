# XCoin Scalping Bot - Complete User Guide

**Version:** 1.0
**Last Updated:** October 30, 2025
**For:** Zerodha/Angel One/Kotak Securities Users

> ⚠️ **IMPORTANT:** Always start with Paper Trading mode. Never start with live trading.

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start)
2. [Complete Setup Guide](#complete-setup)
3. [Understanding the Dashboard](#dashboard-guide)
4. [Creating Your First Strategy](#first-strategy)
5. [Running Backtests](#backtesting)
6. [Paper Trading](#paper-trading)
7. [Going Live](#live-trading)
8. [Risk Management](#risk-management)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

---

## Quick Start (5 Minutes) {#quick-start}

### Prerequisites
- Python 3.8+ installed
- PostgreSQL database running
- Zerodha/Angel One/Kotak account with API access

### 1. Install Dependencies

```bash
cd scalping-bot
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Set database URL
export DATABASE_URL="postgresql://username:password@localhost:5432/scalping_bot"

# Initialize database
python -c "from src.database.db import init_db; init_db()"
```

### 3. Configure Broker API

Create `config/secrets.env`:

```bash
# Zerodha credentials
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here

# For Angel One (optional)
ANGEL_API_KEY=your_angel_key
ANGEL_API_SECRET=your_angel_secret

# For Kotak (optional)
KOTAK_API_KEY=your_kotak_key
KOTAK_API_SECRET=your_kotak_secret
```

### 4. Start Dashboard

```bash
python run_dashboard.py
```

Open browser: http://localhost:8050

**✅ You're ready!** The dashboard is now running.

---

## Complete Setup Guide {#complete-setup}

### Step 1: Environment Setup

#### Install System Dependencies

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
- Download PostgreSQL from https://www.postgresql.org/download/windows/
- Run installer and follow wizard

#### Create Virtual Environment

```bash
cd scalping-bot
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Database Setup

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE scalping_bot;

# Create user (optional)
CREATE USER scalping_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE scalping_bot TO scalping_user;

# Exit
\q
```

#### Set Database URL

```bash
# Add to your shell profile (~/.bashrc or ~/.zshrc)
export DATABASE_URL="postgresql://scalping_user:your_secure_password@localhost:5432/scalping_bot"

# OR create .env file in project root
echo "DATABASE_URL=postgresql://scalping_user:your_secure_password@localhost:5432/scalping_bot" > .env
```

#### Initialize Database Schema

```bash
python -c "from src.database.db import init_db; init_db()"
```

**Expected output:**
```
✅ Database initialized successfully
✅ Created tables: users, strategies, trades, positions, sessions, orders, watchlist
```

### Step 3: Broker Authentication

#### Option A: Zerodha Kite Connect

1. **Get API Credentials:**
   - Login to https://kite.trade
   - Go to "API" section
   - Click "Create new app"
   - Note down API Key and API Secret

2. **Configure Credentials:**

Create `config/secrets.env`:
```bash
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
```

3. **Authenticate:**
   - Start dashboard: `python run_dashboard.py`
   - Go to Settings → Broker Configuration
   - Click "Connect Zerodha"
   - Login with Zerodha credentials
   - Authorize the app

#### Option B: Angel One SmartAPI

1. **Get API Credentials:**
   - Login to https://smartapi.angelbroking.com
   - Register for API access
   - Note down API Key and Client Code

2. **Configure:**
```bash
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_CODE=your_client_code
ANGEL_PASSWORD=your_password
ANGEL_TOTP_SECRET=your_totp_secret
```

#### Option C: Kotak Securities

1. **Get API Credentials:**
   - Contact Kotak Securities for API access
   - Complete KYC and documentation
   - Receive Consumer Key and Consumer Secret

2. **Configure:**
```bash
KOTAK_CONSUMER_KEY=your_consumer_key
KOTAK_CONSUMER_SECRET=your_consumer_secret
KOTAK_ACCESS_TOKEN=your_access_token
```

### Step 4: Verify Installation

```bash
# Test dashboard
python run_dashboard.py

# In another terminal, test API
curl http://localhost:8050/api/status

# Expected response:
{
  "status": "stopped",
  "mode": "paper",
  "authenticated": false
}
```

**✅ Setup complete!**

---

## Understanding the Dashboard {#dashboard-guide}

### Dashboard Overview

The dashboard is your control center with 7 main sections:

#### 1. **Home/Dashboard** (`/`)
- Bot status (Running/Stopped/Paused)
- Current P&L (Daily/Total/Unrealized)
- Active positions
- Recent trades
- Quick controls (Start/Stop/Pause/Emergency Stop)

#### 2. **Strategies** (`/strategies`)
- View all strategies
- Create new strategy
- Edit existing strategies
- Enable/Disable strategies
- Backtest strategies
- Deploy strategies

#### 3. **Analytics** (`/analytics`)
- Performance charts
- Trade statistics
- Win/loss analysis
- Monthly breakdown
- Pattern detection statistics

#### 4. **Portfolio** (`/portfolio`)
- Holdings overview
- Position tracker
- P&L calculator
- Portfolio import from CSV

#### 5. **Settings** (`/settings`)
- Trading settings (timeframe, symbols)
- Risk management settings
- Broker configuration
- Alert settings (Telegram/Email)
- Logging settings

#### 6. **Accounts** (`/accounts`)
- User profile
- Broker connection status
- API usage statistics
- Account balance

#### 7. **History** (`/history`)
- Trade history with filters
- Session logs
- Error logs
- Pattern detection history

### Navigation Tips

- Use the top navigation bar for main sections
- Bottom-right shows connection status
- Top-right shows current mode (Paper/Live)
- Click bot status for quick control panel

---

## Creating Your First Strategy {#first-strategy}

### Via Dashboard (Recommended for Beginners)

#### Step 1: Navigate to Strategies

1. Click "Strategies" in navigation
2. Click "Create New Strategy" button

#### Step 2: Choose Strategy Type

Select from templates:

**1. EMA Crossover** (Trend Following)
- Best for: Trending markets
- Difficulty: Beginner
- Win Rate: 45-55%

**2. RSI Strategy** (Mean Reversion)
- Best for: Range-bound markets
- Difficulty: Beginner
- Win Rate: 50-60%

**3. Breakout Strategy** (Momentum)
- Best for: High volatility
- Difficulty: Intermediate
- Win Rate: 40-50%

**4. Custom Strategy** (Advanced)
- Best for: Experienced traders
- Difficulty: Advanced
- Win Rate: Varies

#### Step 3: Configure Parameters

**For EMA Crossover:**

```yaml
Strategy Name: My EMA Strategy
Description: 9/21 EMA crossover on 5-minute chart

Parameters:
  Fast EMA Period: 9
  Slow EMA Period: 21
  Timeframe: 5m

Symbols:
  - NIFTY 50
  - RELIANCE
  - TCS

Risk Management:
  Stop Loss: 2%
  Target: 4%
  Risk per Trade: 2%
  Max Positions: 3
```

**For RSI Strategy:**

```yaml
Strategy Name: RSI Oversold/Overbought
Description: Buy oversold, sell overbought

Parameters:
  RSI Period: 14
  Oversold Level: 30
  Overbought Level: 70
  Timeframe: 5m

Symbols:
  - BANKNIFTY
  - HDFC BANK
  - ICICI BANK

Risk Management:
  Stop Loss: 1.5%
  Target: 3%
  Risk per Trade: 2%
  Max Positions: 5
```

#### Step 4: Backtest Before Deployment

**CRITICAL: Always backtest first!**

1. Click "Backtest" button
2. Select date range (recommend 6 months)
3. Set initial capital (₹100,000 default)
4. Click "Run Backtest"

**Review Results:**
- Total P&L
- Win Rate (aim for >50%)
- Max Drawdown (should be <15%)
- Profit Factor (should be >1.5)
- Sharpe Ratio (should be >1.0)

**Decision Tree:**
```
Win Rate > 50% AND Profit Factor > 1.5?
  YES → Proceed to Paper Trading
  NO  → Adjust parameters and backtest again
```

#### Step 5: Save Strategy

1. Review all parameters
2. Click "Save Strategy"
3. Strategy appears in strategy list

### Via Code (Advanced Users)

Create file `strategies/my_custom_strategy.py`:

```python
from src.strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.fast_ema = config.get('fast_ema', 9)
        self.slow_ema = config.get('slow_ema', 21)

    def generate_signal(self, data):
        """
        Generate trading signal

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Signal dict or None
        """
        if len(data) < self.slow_ema + 1:
            return None

        # Calculate EMAs
        data['ema_fast'] = data['close'].ewm(span=self.fast_ema).mean()
        data['ema_slow'] = data['close'].ewm(span=self.slow_ema).mean()

        current = data.iloc[-1]
        previous = data.iloc[-2]

        # Bullish crossover
        if (previous['ema_fast'] <= previous['ema_slow'] and
            current['ema_fast'] > current['ema_slow']):

            return {
                'action': 'BUY',
                'symbol': current['symbol'],
                'price': current['close'],
                'stop_loss': current['close'] * 0.98,
                'target': current['close'] * 1.04
            }

        # Bearish crossover
        elif (previous['ema_fast'] >= previous['ema_slow'] and
              current['ema_fast'] < current['ema_slow']):

            return {
                'action': 'CLOSE',
                'symbol': current['symbol']
            }

        return None
```

---

## Running Backtests {#backtesting}

### Via Dashboard

1. Go to Strategies
2. Click on strategy
3. Click "Backtest" button
4. Configure:
   - Date range
   - Initial capital
   - Commission per trade
5. Click "Run"
6. Review detailed report

### Via Command Line

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
  --trade-log results/trades_ema.csv \
  --verbose
```

### Interpreting Results

**Key Metrics Explained:**

**1. Win Rate**
- **Good:** 50-60%
- **Excellent:** >60%
- **Warning:** <45%

**2. Profit Factor**
- **Good:** 1.5-2.0
- **Excellent:** >2.0
- **Warning:** <1.2

**3. Max Drawdown**
- **Good:** 5-10%
- **Acceptable:** 10-15%
- **Warning:** >15%

**4. Sharpe Ratio**
- **Good:** 1.0-2.0
- **Excellent:** >2.0
- **Warning:** <0.5

**5. Total Return**
- **Good:** 15-30% annual
- **Excellent:** >30% annual
- **Warning:** <10% annual

### Example Report Analysis

```
======================================================================
BACKTEST RESULTS
======================================================================

Period: 2024-01-01 to 2024-06-30
Duration: 181 days

CAPITAL:
  Initial Capital:  ₹  100,000.00
  Final Capital:    ₹  112,450.00      ✅ GOOD (12.45% in 6 months)
  Peak Capital:     ₹  118,200.00
  Total P&L:        ₹   12,450.00

TRADES:
  Total Trades:               47
  Winning Trades:             28 (59.6%)    ✅ EXCELLENT
  Losing Trades:              19

PROFIT/LOSS:
  Gross Profit:     ₹   28,920.00
  Gross Loss:       ₹   15,530.00
  Avg Win:          ₹    1,032.86
  Avg Loss:         ₹     -817.37
  Profit Factor:             1.86      ✅ GOOD

RISK METRICS:
  Max Drawdown:     ₹    5,750.00 (4.87%)  ✅ EXCELLENT
  Sharpe Ratio:              1.42          ✅ GOOD

======================================================================

✅ DECISION: PROCEED TO PAPER TRADING
```

---

## Paper Trading {#paper-trading}

### What is Paper Trading?

Paper trading simulates real trading using:
- ✅ Live market data
- ✅ Actual strategy signals
- ✅ Real-time position tracking
- ✅ Realistic order execution
- ❌ NO real money involved

**Purpose:** Validate strategy in live market conditions before risking capital.

### Starting Paper Trading

#### Step 1: Ensure Broker Authentication

1. Go to Settings → Broker Configuration
2. Verify broker connection (should show green checkmark)
3. If not connected, click "Connect" and authenticate

#### Step 2: Select Strategy

1. Go to Strategies
2. Click on backtested strategy
3. Verify parameters are correct

#### Step 3: Deploy in Paper Mode

1. Click "Deploy Strategy" button
2. **IMPORTANT:** Select "Paper Trading" mode
3. Configure:
   ```
   Mode: Paper Trading ← VERIFY THIS!
   Initial Capital: ₹100,000
   Max Positions: 3
   Daily Loss Limit: ₹2,000
   ```
4. Click "Start Paper Trading"

#### Step 4: Start Bot

1. Go to Home/Dashboard
2. Click "Start Bot" button
3. Confirm mode is **Paper**
4. Bot status changes to "Running"

### Monitoring Paper Trading

#### Real-Time Dashboard

Monitor these metrics:

**1. Position Status**
- Open positions
- Entry price vs current price
- Unrealized P&L
- Time in trade

**2. Trade Log**
- Entry/exit times
- Reasons (signal/stop-loss/target)
- P&L per trade
- Cumulative P&L

**3. Performance Metrics**
- Win rate (updating live)
- Average win/loss
- Current drawdown
- Daily P&L

#### Daily Checklist

**Morning (9:00 AM):**
- [ ] Check bot is running
- [ ] Review overnight positions (if any)
- [ ] Verify broker connection
- [ ] Check for any errors in logs

**During Market Hours:**
- [ ] Monitor positions every hour
- [ ] Check for pattern detections
- [ ] Verify signals are being generated
- [ ] Ensure orders are being placed correctly

**End of Day (3:30 PM):**
- [ ] Review all trades executed
- [ ] Calculate daily P&L
- [ ] Check for any missed signals
- [ ] Review error logs

### Paper Trading Duration

**Minimum:** 5-10 trading days
**Recommended:** 15-20 trading days
**Ideal:** 1 month (20-25 trading days)

**Validation Criteria:**

After paper trading period, check:

```
✅ Win Rate > 50%
✅ Profit Factor > 1.5
✅ Max Daily Drawdown < 5%
✅ No critical errors
✅ Orders executed as expected
✅ Stop-losses working correctly
✅ Risk limits respected

ALL ABOVE CRITERIA MET?
  YES → Proceed to Live Trading
  NO  → Continue paper trading or adjust strategy
```

### Common Paper Trading Issues

**Issue 1: No signals generated**
- **Cause:** Market not meeting entry conditions
- **Solution:** Normal behavior, wait for signals

**Issue 2: Orders not filling**
- **Cause:** Price moved away before order placed
- **Solution:** Normal slippage, adjust order type

**Issue 3: Stop-loss not hit**
- **Cause:** Price didn't reach stop-loss level
- **Solution:** Normal behavior, position still open

**Issue 4: High slippage**
- **Cause:** Volatile market or illiquid stocks
- **Solution:** Trade more liquid symbols or adjust parameters

---

## Going Live {#live-trading}

### Pre-Live Checklist

**MANDATORY - DO NOT SKIP:**

- [ ] ✅ Backtested for 6+ months
- [ ] ✅ Paper traded for 15+ days
- [ ] ✅ Win rate >50% in paper trading
- [ ] ✅ Profit factor >1.5 in paper trading
- [ ] ✅ No critical errors during paper trading
- [ ] ✅ Comfortable with strategy behavior
- [ ] ✅ Understand all parameters
- [ ] ✅ Risk limits configured correctly
- [ ] ✅ Emergency contact available
- [ ] ✅ Can monitor during market hours

**If ANY checkbox above is unchecked, DO NOT go live!**

### Starting Live Trading

#### Step 1: Final Configuration Review

1. Go to Settings → Risk Management
2. Verify ALL risk parameters:

```yaml
Risk Management:
  # CRITICAL PARAMETERS
  Risk per Trade: 2%           ← Max loss per trade
  Max Positions: 3             ← Never exceed this
  Daily Loss Limit: ₹2,000     ← Bot stops at this loss
  Max Drawdown: 10%            ← Circuit breaker

  # POSITION SIZING
  Min Position Size: ₹10,000
  Max Position Size: ₹50,000

  # SAFETY LIMITS
  Max Orders per Minute: 10
  Max Orders per Day: 100

  # STOP-LOSS
  Always Use Stop-Loss: true   ← NEVER disable this
  Trailing Stop: false         ← Enable if desired
```

#### Step 2: Start with Small Capital

**Day 1-3:**
- Start with ₹10,000-20,000
- Max 1-2 positions
- Monitor every trade closely

**Week 1:**
- If profitable, increase to ₹50,000
- Max 2-3 positions

**Month 1:**
- If consistently profitable, increase to full capital
- Max 3-5 positions

#### Step 3: Deploy in Live Mode

1. Go to Strategies
2. Click on validated strategy
3. Click "Deploy Strategy"
4. **SELECT "LIVE TRADING" MODE**
5. **DOUBLE-CHECK:** Mode shows "LIVE" in RED
6. Configure limits:
   ```
   Mode: LIVE TRADING ⚠️
   Initial Capital: ₹20,000 (start small!)
   Max Positions: 2
   Daily Loss Limit: ₹500
   ```
7. Click "Confirm Live Trading"
8. Enter OTP/2FA code

#### Step 4: Monitor Closely

**First Day:**
- Monitor EVERY trade in real-time
- Be ready to hit Emergency Stop
- Verify P&L calculations match broker

**First Week:**
- Check dashboard every 30 minutes
- Review end-of-day reports
- Compare with paper trading results

**First Month:**
- Weekly performance review
- Adjust parameters if needed
- Scale up slowly if profitable

### Emergency Procedures

#### Emergency Stop Button

**When to use:**
- Market crash or extreme volatility
- Bot behaving unexpectedly
- Large unexpected loss
- Technical issues with broker

**What it does:**
1. Cancels all pending orders
2. Closes all open positions at market price
3. Stops bot immediately
4. Sends alert notifications
5. Logs emergency stop reason

**How to use:**
1. Click red "Emergency Stop" button (top-right)
2. Confirm action
3. Bot stops within 1-2 seconds
4. Review logs and positions

#### Manual Intervention

**If bot won't stop:**

```bash
# Kill process
pkill -f "run_dashboard.py"

# Or find and kill
ps aux | grep python
kill -9 <process_id>
```

**Close positions manually:**
1. Login to broker platform
2. Go to Positions
3. Click "Exit All" or close manually

### Daily Monitoring Routine

**Pre-Market (9:00 AM):**
```
[ ] Start dashboard
[ ] Verify bot status
[ ] Check broker connection
[ ] Review yesterday's trades
[ ] Check for any system alerts
```

**During Market (9:15 AM - 3:30 PM):**
```
[ ] Monitor every 30 minutes
[ ] Check open positions
[ ] Verify P&L is reasonable
[ ] Watch for any errors
[ ] Have emergency stop ready
```

**Post-Market (3:30 PM+):**
```
[ ] Stop bot
[ ] Review all trades
[ ] Calculate actual P&L
[ ] Compare with backtest expectations
[ ] Update trading journal
[ ] Plan for tomorrow
```

---

## Risk Management {#risk-management}

### Understanding Risk Limits

#### 1. Risk per Trade (Default: 2%)

**What it means:**
- Maximum loss allowed on single trade
- Calculated as % of total capital

**Example:**
```
Capital: ₹100,000
Risk per Trade: 2%
Max Loss: ₹2,000

If entry = ₹1,000 and stop-loss = ₹980:
Risk per share = ₹20
Position size = ₹2,000 / ₹20 = 100 shares
```

**Recommendation:**
- Beginner: 1-2%
- Intermediate: 2-3%
- Advanced: 3-5% (max)
- **Never exceed 5%**

#### 2. Max Positions (Default: 5)

**What it means:**
- Maximum number of simultaneous open positions
- Limits portfolio concentration

**Recommendation:**
- Small capital (<₹1L): 2-3 positions
- Medium capital (₹1-5L): 3-5 positions
- Large capital (>₹5L): 5-10 positions

#### 3. Daily Loss Limit (Default: 6%)

**What it means:**
- Maximum loss allowed in single day
- Bot automatically stops at this limit

**Example:**
```
Capital: ₹100,000
Daily Loss Limit: 6%
Max Daily Loss: ₹6,000

If 3 consecutive losses total ₹6,000:
Bot automatically stops trading
```

**Recommendation:**
- Conservative: 3-5%
- Moderate: 5-8%
- Aggressive: 8-10%
- **Never exceed 10%**

#### 4. Risk-Reward Ratio (Default: 2:1)

**What it means:**
- Target profit should be at least 2x risk

**Example:**
```
Entry: ₹1,000
Stop-Loss: ₹980 (₹20 risk)
Target: ₹1,040+ (₹40+ reward)
Ratio: 40/20 = 2:1 ✅
```

**Minimum acceptable:** 1.5:1
**Recommended:** 2:1 or better
**Ideal:** 3:1

### Position Sizing Calculator

Use this formula:

```
Position Size = (Account Capital × Risk % per Trade) / (Entry Price - Stop-Loss Price)
```

**Example:**
```
Account: ₹100,000
Risk: 2% = ₹2,000
Entry: ₹500
Stop-Loss: ₹490
Risk per Share: ₹10

Position Size = ₹2,000 / ₹10 = 200 shares
Total Investment = 200 × ₹500 = ₹100,000 (requires full capital)

Better: Reduce to 100 shares = ₹50,000 (50% capital utilization)
```

### Stop-Loss Types

#### 1. Fixed Stop-Loss
- Set at fixed percentage below entry
- Simple and reliable
- Example: 2% below entry

#### 2. Trailing Stop-Loss
- Moves up as price moves up
- Locks in profits
- Example: Trail by 1.5%

#### 3. Time-Based Stop
- Exit after fixed time period
- Useful for intraday strategies
- Example: Exit at 3:15 PM regardless of P&L

#### 4. Volatility-Based Stop
- Based on ATR (Average True Range)
- Adapts to market conditions
- Example: 2× ATR below entry

---

## Troubleshooting {#troubleshooting}

### Common Issues and Solutions

#### Issue 1: Dashboard Won't Start

**Symptoms:**
```
python run_dashboard.py
Error: No module named 'flask'
```

**Solutions:**

**A. Virtual environment not activated**
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

**B. Dependencies not installed**
```bash
pip install -r requirements.txt
```

**C. Port already in use**
```bash
# Find process using port 8050
lsof -i :8050

# Kill it
kill -9 <PID>

# Or use different port
python run_dashboard.py --port 8051
```

#### Issue 2: Database Connection Failed

**Symptoms:**
```
Error: could not connect to server
```

**Solutions:**

**A. PostgreSQL not running**
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Windows
net start postgresql-x64-14
```

**B. Wrong database URL**
```bash
# Check current URL
echo $DATABASE_URL

# Set correct URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/scalping_bot"
```

**C. Database doesn't exist**
```bash
psql -U postgres -c "CREATE DATABASE scalping_bot;"
```

#### Issue 3: Broker Authentication Failed

**Symptoms:**
```
Error: Invalid API credentials
```

**Solutions:**

**A. Wrong credentials**
1. Double-check API key and secret
2. Ensure no extra spaces
3. Regenerate credentials if needed

**B. Token expired**
```bash
# Delete old token
rm config/.zerodha_token

# Re-authenticate via dashboard
```

**C. API not enabled**
- Login to broker platform
- Enable API access
- Wait 24 hours for activation

#### Issue 4: No Trading Signals Generated

**Symptoms:**
- Bot running but no trades
- Signal count = 0

**Possible Causes:**

**A. Market conditions don't meet criteria**
- **Solution:** Normal behavior, wait for valid setup

**B. Wrong symbols configured**
```bash
# Check configured symbols
# Go to Strategy → Edit → Symbols
# Ensure symbols are correct: "RELIANCE", "TCS", etc.
```

**C. Insufficient historical data**
```bash
# Strategy needs minimum candles (usually 50-200)
# Wait for enough data to accumulate
```

#### Issue 5: Orders Not Being Placed

**Symptoms:**
- Signals generated but no orders
- Order count = 0

**Solutions:**

**A. Insufficient balance**
```bash
# Check account balance
# Ensure balance > position size + margin
```

**B. Risk limits exceeded**
```bash
# Check:
# - Daily loss limit not hit
# - Max positions not reached
# - Risk per trade not exceeded
```

**C. Broker API issues**
```bash
# Check broker platform
# Verify API is working
# Check for maintenance windows
```

#### Issue 6: Stop-Loss Not Working

**Symptoms:**
- Loss exceeded stop-loss level
- Position not closed

**Solutions:**

**A. Gaps in price**
- Stop-loss hit but price gapped down
- Order executed at next available price
- **This is normal market behavior**

**B. Stop-loss disabled**
```bash
# Check risk settings
# Ensure "Always Use Stop-Loss" = true
```

**C. Technical issue**
```bash
# Check error logs
tail -f logs/errors.log

# Look for failed order attempts
```

#### Issue 7: High Slippage

**Symptoms:**
- Entry/exit prices differ significantly from expected
- P&L lower than backtest

**Solutions:**

**A. Trade more liquid stocks**
```bash
# Avoid small-cap stocks
# Use large-cap stocks:
# - RELIANCE, TCS, INFY, HDFC BANK, ICICI BANK
```

**B. Use limit orders**
```yaml
# In strategy config
order_type: limit
limit_offset: 0.1%  # 0.1% from market price
```

**C. Reduce order size**
```bash
# Large orders have more slippage
# Split into smaller orders
```

#### Issue 8: Pattern Detection Not Working

**Symptoms:**
```
Error: No module named 'scipy'
```

**Solutions:**

**A. Install missing dependency**
```bash
pip install scipy numpy pandas
```

**B. Chart patterns not showing**
```bash
# Ensure minimum data
# Chart patterns need 30-50 candles minimum
```

---

## Advanced Features {#advanced-features}

### Custom Indicators

Create file `src/indicators/my_indicator.py`:

```python
import pandas as pd

def calculate_vwap(df):
    """Calculate Volume Weighted Average Price"""
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

def calculate_supertrend(df, period=10, multiplier=3):
    """Calculate Supertrend indicator"""
    hl2 = (df['high'] + df['low']) / 2
    atr = df['high'].sub(df['low']).rolling(period).mean()

    upper = hl2 + (multiplier * atr)
    lower = hl2 - (multiplier * atr)

    # Supertrend logic
    df['supertrend'] = 0
    for i in range(period, len(df)):
        if df['close'].iloc[i] > upper.iloc[i]:
            df['supertrend'].iloc[i] = 1  # Uptrend
        elif df['close'].iloc[i] < lower.iloc[i]:
            df['supertrend'].iloc[i] = -1  # Downtrend

    return df
```

### Strategy Optimization

**Optimize parameters systematically:**

```python
# File: optimize_strategy.py
from src.backtest import StrategyBacktester
import pandas as pd

# Parameter ranges to test
fast_ema_range = range(5, 15, 2)  # 5, 7, 9, 11, 13
slow_ema_range = range(15, 30, 5)  # 15, 20, 25

results = []

for fast in fast_ema_range:
    for slow in slow_ema_range:
        if fast >= slow:
            continue

        backtester = StrategyBacktester()
        result = backtester.backtest_ema_crossover(
            data,
            fast_period=fast,
            slow_period=slow
        )

        results.append({
            'fast': fast,
            'slow': slow,
            'total_pnl': result.total_pnl,
            'win_rate': result.win_rate,
            'sharpe': result.sharpe_ratio
        })

# Find best parameters
df_results = pd.DataFrame(results)
best = df_results.loc[df_results['sharpe'].idxmax()]
print(f"Best parameters: Fast={best['fast']}, Slow={best['slow']}")
```

### Multi-Symbol Trading

**Trade multiple symbols simultaneously:**

```python
symbols = [
    {'symbol': 'RELIANCE', 'exchange': 'NSE'},
    {'symbol': 'TCS', 'exchange': 'NSE'},
    {'symbol': 'INFY', 'exchange': 'NSE'},
    {'symbol': 'HDFC BANK', 'exchange': 'NSE'},
    {'symbol': 'ICICI BANK', 'exchange': 'NSE'}
]

# Configure strategy
strategy_config = {
    'name': 'Multi-Symbol EMA',
    'symbols': symbols,
    'strategy_type': 'ema_crossover',
    'parameters': {
        'fast_ema': 9,
        'slow_ema': 21
    }
}
```

### Alert Integration

**Configure Telegram alerts:**

```python
# File: config/alerts.yaml
alerts:
  telegram:
    enabled: true
    bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"

  notifications:
    - event: trade_opened
      message: "🟢 New trade: {symbol} @ ₹{price}"

    - event: trade_closed
      message: "🔴 Closed: {symbol}, P&L: ₹{pnl}"

    - event: stop_loss_hit
      message: "⚠️ Stop-loss hit: {symbol}, Loss: ₹{loss}"

    - event: target_hit
      message: "🎯 Target hit: {symbol}, Profit: ₹{profit}"

    - event: daily_limit_reached
      message: "🛑 Daily loss limit reached! Bot stopped."
```

### Performance Tracking

**Export trade log to Excel:**

```python
from src.backtest import PerformanceAnalyzer
import pandas as pd

# Get trades from database
trades = get_all_trades()  # Your function

# Generate trade log
trade_log = PerformanceAnalyzer.generate_trade_log(trades)

# Export to Excel
trade_log.to_excel('trade_log.xlsx', index=False)

# Add summary sheet
with pd.ExcelWriter('trade_log.xlsx', mode='a') as writer:
    summary = {
        'Total Trades': len(trades),
        'Win Rate': calculate_win_rate(trades),
        'Total P&L': sum(t.pnl for t in trades),
        'Avg Win': calculate_avg_win(trades),
        'Avg Loss': calculate_avg_loss(trades)
    }
    pd.DataFrame([summary]).to_excel(writer, sheet_name='Summary', index=False)
```

---

## Best Practices

### 1. Trading Discipline

- ✅ Always use stop-losses
- ✅ Never override bot decisions emotionally
- ✅ Stick to tested parameters
- ✅ Review performance weekly
- ✅ Keep detailed trading journal
- ❌ Never increase position size after losses
- ❌ Never remove stop-losses manually
- ❌ Never trade without backtesting

### 2. System Maintenance

**Daily:**
- Check logs for errors
- Verify broker connection
- Review day's trades

**Weekly:**
- Analyze performance metrics
- Compare with backtest expectations
- Optimize parameters if needed

**Monthly:**
- Full system review
- Update strategy if markets changed
- Review risk parameters

### 3. Capital Management

**Golden Rules:**
- Start small (₹10,000-20,000)
- Scale up slowly (10-20% per month)
- Never risk more than 2% per trade
- Keep 50% cash reserve
- Diversify across strategies

### 4. Record Keeping

**What to track:**
- Every trade (entry/exit/P&L)
- Daily P&L
- Weekly performance
- Parameter changes
- Market conditions
- Emotions/thoughts

**Why it matters:**
- Identify patterns
- Improve decision-making
- Tax reporting
- Performance analysis

---

## Emergency Contacts

**Technical Support:**
- GitHub Issues: [Your Repo URL]
- Email: support@yourproject.com

**Broker Support:**
- Zerodha: 080-4040-2020
- Angel One: 022-3926-9999
- Kotak: 1800-102-4500

**SEBI Complaints:**
- SCORES Portal: scores.gov.in
- Phone: 1800-266-7575

---

## Appendix

### Glossary

- **Paper Trading:** Simulated trading with live data but no real money
- **Backtest:** Testing strategy on historical data
- **Slippage:** Difference between expected and actual execution price
- **Stop-Loss:** Order to exit position at predefined loss level
- **Position Sizing:** Calculating number of shares to trade
- **Risk-Reward Ratio:** Ratio of potential profit to potential loss
- **Drawdown:** Peak-to-trough decline in capital
- **Sharpe Ratio:** Risk-adjusted return measure
- **Win Rate:** Percentage of profitable trades

### Keyboard Shortcuts

- `Ctrl + S` - Start bot
- `Ctrl + X` - Stop bot
- `Ctrl + P` - Pause bot
- `Ctrl + E` - Emergency stop
- `Ctrl + R` - Refresh dashboard
- `Ctrl + L` - View logs

### Command Line Reference

```bash
# Start dashboard
python run_dashboard.py

# Start with custom port
python run_dashboard.py --port 8051

# Debug mode
python run_dashboard.py --debug

# Backtest
python src/backtest/cli.py --strategy <name> --verbose

# Initialize database
python -c "from src.database.db import init_db; init_db()"

# Check bot status
curl http://localhost:8050/api/status
```

---

**Version History:**
- v1.0 - Initial release (Oct 30, 2025)

**Need Help?**
- Read QUICK_VERIFICATION_SUMMARY.txt
- Check SYSTEM_VERIFICATION_REPORT.md
- Review ISSUES_AND_FIXES.md
- Contact support

---

**⚠️ FINAL WARNING:** Algorithmic trading involves substantial risk of loss. Never trade with money you cannot afford to lose. Always start with paper trading. Past performance does not guarantee future results.
