# User Guide - Scalping Bot Dashboard

**Version:** 2.0.0
**Last Updated:** October 22, 2025

A complete guide to using the Scalping Bot Dashboard for algorithmic trading.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Candlestick Chart](#candlestick-chart)
4. [Pattern Recognition](#pattern-recognition)
5. [Bot Controls](#bot-controls)
6. [Trading Modes](#trading-modes)
7. [Account Management](#account-management)
8. [Strategies](#strategies)
9. [Analytics](#analytics)
10. [Settings](#settings)
11. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Dashboard

1. **Start the Dashboard:**
   ```bash
   python src/dashboard/app.py
   ```

2. **Open in Browser:**
   - URL: http://localhost:8050
   - Or: http://0.0.0.0:8050 (accessible from network)

3. **Login:**
   - No login required for paper trading
   - Zerodha authentication required for live trading

---

## Dashboard Overview

### Main Components

```
┌────────────────────────────────────────────────────────┐
│ SIDEBAR                  TOPBAR (Account, Funds, Status)│
├─ Dashboard              ─────────────────────────────────┤
├─ Accounts               CONTENT AREA                     │
├─ Strategies             • Welcome Header                 │
├─ Analytics              • Bot Controls                   │
├─ Notifications          • Stats Row                      │
├─ Settings               • Candlestick Chart + Patterns   │
├─ Implementation Log     • Performance Overview           │
└─ Help                   • Positions & Trades             │
                          • Live Logs                      │
└─────────────────────────────────────────────────────────┘
```

### Key Metrics (Stats Row)

1. **Daily P&L**
   - Today's profit/loss
   - Percentage change
   - Color: Green (profit) / Red (loss)

2. **Total P&L**
   - All-time profit/loss
   - Cumulative since first trade

3. **Win Rate**
   - Percentage of winning trades
   - Win/Total trades displayed

4. **Today's Trades**
   - Number of trades executed today

---

## Candlestick Chart

### Chart Layout

**Location:** Center of dashboard (70% width)

**Features:**
- 100 historical candles (default)
- 5-minute timeframe
- Real-time price updates
- Interactive crosshair
- Pattern markers

### Reading the Chart

#### Candlestick Colors:
- 🟢 **Green:** Bullish candle (close > open)
- 🔴 **Red:** Bearish candle (close < open)

#### Candle Components:
```
    High ──┬─── Wick (upper shadow)
           │
    Open ──┤
           │ Body
  Close ──┤
           │
     Low ──┴─── Wick (lower shadow)
```

#### Pattern Markers:
- **↗️ Green Arrow (below candle):** Bullish pattern detected
- **↘️ Red Arrow (above candle):** Bearish pattern detected
- **⚡ Yellow Circle:** Indecision pattern

### Interacting with the Chart

**Hover:**
- Move mouse over candle to see:
  - Time
  - Open, High, Low, Close (OHLC) values
  - Pattern name (if marker present)

**Price Information:**
- Current price displayed in top-right
- Percentage change from previous candle
- Color-coded (green/red)

---

## Pattern Recognition

### Pattern Overlay Panel

**Location:** Right side of dashboard (30% width)

**Sections:**
1. Candlestick Patterns
2. Indicator Signals

### Candlestick Patterns

#### Pattern Display Format:
```
┌────────────────────────┐
│ ↗️ Hammer         82% │
│ ⚡ Doji           75% │
│ ↘️ Shooting Star  85% │
└────────────────────────┘
```

#### Pattern Icons:
- **↗️** - Bullish pattern (buy signal)
- **↘️** - Bearish pattern (sell signal)
- **⚡** - Indecision pattern (wait)

#### Pattern Types:

**Bullish Reversal Patterns:**
- Hammer
- Inverted Hammer
- Bullish Engulfing
- Piercing
- Morning Star
- Three White Soldiers

**Bearish Reversal Patterns:**
- Shooting Star
- Hanging Man
- Bearish Engulfing
- Dark Cloud Cover
- Evening Star
- Three Black Crows

**Indecision Patterns:**
- Doji
- Dragonfly Doji
- Gravestone Doji
- Spinning Top
- Harami

**Continuation Patterns:**
- Rising Three
- Falling Three
- Marubozu

#### Confidence Score:
- **80-100%:** High confidence (strong signal)
- **60-79%:** Medium confidence (moderate signal)
- **Below 60%:** Low confidence (weak signal)

### Indicator Signals

#### Indicators Displayed:
```
┌────────────────────────┐
│ RSI      Buy      🟢  │
│ MACD     Neutral  ⚪  │
│ BB       Oversold 🟢  │
│ ADX      Strong   ⚡  │
└────────────────────────┘
```

#### Signal Types:
- 🟢 **Buy:** Indicator suggests long position
- 🔴 **Sell:** Indicator suggests short position
- ⚪ **Neutral:** No clear signal

#### Key Indicators:

**Momentum:**
- **RSI (Relative Strength Index)**
  - <30: Oversold (buy signal)
  - >70: Overbought (sell signal)

- **Stochastic**
  - <20: Oversold (buy signal)
  - >80: Overbought (sell signal)

**Trend:**
- **MACD (Moving Average Convergence Divergence)**
  - Bullish cross: Buy signal
  - Bearish cross: Sell signal

- **EMA Cross**
  - Golden cross: Buy signal
  - Death cross: Sell signal

- **ADX (Average Directional Index)**
  - >25: Strong trend
  - <20: Weak trend

**Volatility:**
- **Bollinger Bands**
  - Price < Lower Band: Oversold
  - Price > Upper Band: Overbought

- **ATR (Average True Range)**
  - High: High volatility
  - Low: Low volatility

**Volume:**
- High volume: Strong move
- Low volume: Weak move

---

## Bot Controls

### Control Panel

**Location:** Below header, above charts

**Buttons:**

1. **Mode Selector** (Dropdown)
   - Paper Trading (default)
   - Live Trading

2. **Start** (Primary button)
   - Starts the trading bot
   - Begins pattern detection and order execution
   - Paper trading: Simulated trades
   - Live trading: Real orders (requires confirmation)

3. **Pause** (Secondary button)
   - Pauses bot temporarily
   - No new trades opened
   - Existing positions maintained

4. **Stop** (Secondary button)
   - Stops bot completely
   - No new trades
   - Existing positions kept open

5. **Emergency Stop** (Danger button)
   - Immediately stops bot
   - Cancels all pending orders
   - Closes all open positions
   - Requires confirmation

### Status Indicators

**Status Badge (Top-right):**
- **Stopped:** Bot not running (gray)
- **Running:** Bot active (green, pulsing)
- **Paused:** Bot temporarily halted (yellow)
- **Error:** Bot encountered error (red)

**Topbar Status:**
- **Live:** Connected and trading (green dot)
- **Offline:** Not connected (red dot)

---

## Trading Modes

### Paper Trading Mode

**Description:** Simulated trading with virtual money

**Features:**
- No real money involved
- Test strategies safely
- Full dashboard functionality
- Realistic market simulation

**Use Cases:**
- Testing new strategies
- Learning the platform
- Strategy optimization
- Risk-free practice

**Starting Paper Trading:**
1. Select "Paper Trading" from mode dropdown
2. Click "Start" button
3. Bot begins simulated trading
4. View results in Positions/Trades

### Live Trading Mode

**Description:** Real trading with real money

**⚠️ Warning:** Involves financial risk. Only use with capital you can afford to lose.

**Requirements:**
- Zerodha account with API access
- Sufficient funds in account
- Completed KYC verification
- API credentials configured

**Starting Live Trading:**
1. Ensure Zerodha account is connected
2. Select "Live Trading" from mode dropdown
3. Click "Start" button
4. **Confirm** the warning dialog
5. Bot begins real trading

**Safety Features:**
- Confirmation required
- Risk limits enforced
- Stop-loss automatically set
- Emergency stop available

---

## Account Management

### Connecting Zerodha Account

**Navigation:** Click "Accounts" in sidebar

**Steps:**
1. Click "Connect to Zerodha" button
2. Enter API Key and API Secret
3. Complete OAuth2 authentication
4. Grant permissions
5. Connection confirmed

**Account Info Displayed:**
- Account name
- Available funds
- Used margin
- Connection status

**Multiple Accounts:**
- Add multiple Zerodha accounts
- Switch between accounts from topbar
- Each account isolated

---

## Strategies

### Strategy Selection

**Navigation:** Click "Strategies" in sidebar

**Available Strategies:**
1. **Pattern-Based Scalping** (Default)
   - Uses candlestick pattern recognition
   - Quick entries/exits
   - Small profit targets

2. **Momentum Trading**
   - Follows strong trends
   - Uses RSI, MACD
   - Larger position sizes

3. **Mean Reversion**
   - Trades overbought/oversold
   - Bollinger Bands
   - Counter-trend trades

4. **Custom Strategy**
   - Build your own
   - Combine indicators
   - Set custom rules

### Strategy Configuration

**Parameters:**
- Entry conditions
- Exit conditions
- Stop-loss percentage
- Take-profit target
- Position size
- Max concurrent trades
- Trading hours
- Symbol selection

### Enabling/Disabling Strategies

1. Go to Strategies page
2. Toggle strategy on/off
3. Click "Save Configuration"
4. Restart bot if running

---

## Analytics

### Performance Metrics

**Navigation:** Click "Analytics" in sidebar

**Metrics Displayed:**

**Profitability:**
- Total P&L
- Daily P&L
- Weekly P&L
- Monthly P&L
- Win rate
- Average win
- Average loss
- Profit factor

**Trade Statistics:**
- Total trades
- Winning trades
- Losing trades
- Average trade duration
- Max consecutive wins/losses

**Risk Metrics:**
- Max drawdown
- Sharpe ratio
- Risk/reward ratio
- Volatility

**Charts:**
- Equity curve
- Drawdown chart
- Win/loss distribution
- Hourly performance heatmap

### Exporting Data

**Export Options:**
- CSV format
- JSON format
- Excel format

**Data Available:**
- Trade history
- Performance metrics
- Account statements

---

## Settings

### General Settings

**Navigation:** Click "Settings" in sidebar

**Sections:**

1. **Trading Parameters**
   - Default position size
   - Max daily loss
   - Max concurrent trades
   - Trading hours (start/end)

2. **Risk Management**
   - Stop-loss percentage
   - Take-profit percentage
   - Max position size
   - Max exposure

3. **Notifications**
   - Telegram bot token
   - Email address
   - Alert preferences
   - Notification frequency

4. **Dashboard Preferences**
   - Theme (dark/light)
   - Chart timeframe
   - Stats refresh rate
   - Language (if multi-language)

5. **API Configuration**
   - Zerodha API credentials
   - Webhook URLs
   - API rate limits

---

## Troubleshooting

### Common Issues

#### 1. Dashboard Won't Load

**Problem:** Browser shows connection error

**Solutions:**
- Check if dashboard is running: `python src/dashboard/app.py`
- Verify port 8050 is not blocked
- Try different browser
- Check firewall settings

#### 2. Patterns Not Showing

**Problem:** Pattern overlay is empty

**Solutions:**
- Check if bot is running
- Verify API endpoint: `http://localhost:8050/api/patterns/all`
- Check browser console for errors
- Refresh page (F5)

#### 3. Chart Not Updating

**Problem:** Candlestick chart frozen

**Solutions:**
- Check network connection
- Verify OHLC endpoint: `http://localhost:8050/api/chart/ohlc`
- Clear browser cache
- Restart dashboard server

#### 4. Bot Won't Start

**Problem:** "Start" button does nothing

**Solutions:**
- Check bot status in logs
- Verify configuration file
- Ensure API credentials are valid (live mode)
- Check available funds (live mode)

#### 5. Zerodha Connection Failed

**Problem:** "Authentication Required" banner shows

**Solutions:**
- Re-enter API credentials
- Check API key validity
- Verify permissions granted
- Check Zerodha API status

### Getting Help

**Resources:**
- **FAQ:** See `docs/FAQ.md`
- **Implementation Log:** `/implementation-log` page
- **Help Page:** Click "Help" in sidebar
- **Logs:** Check `logs/` folder
- **GitHub Issues:** Report bugs

**Log Files:**
- Application logs: `logs/app.log`
- Trading logs: `logs/trading.log`
- Error logs: `logs/error.log`

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Refresh page |
| `Ctrl/Cmd + R` | Reload dashboard |
| `Esc` | Close modals |
| `?` | Show keyboard shortcuts (future) |

---

## Best Practices

### Trading:
1. **Start with Paper Trading**
   - Test strategies first
   - Understand bot behavior
   - Optimize parameters

2. **Risk Management**
   - Set appropriate stop-losses
   - Don't risk more than 2% per trade
   - Diversify across symbols
   - Monitor daily loss limits

3. **Strategy Selection**
   - Choose strategies matching market conditions
   - Don't over-optimize
   - Keep it simple

4. **Monitoring**
   - Check dashboard regularly
   - Review trade logs
   - Analyze performance weekly
   - Adjust strategies as needed

### Dashboard:
1. **Keep Browser Open**
   - Dashboard provides real-time updates
   - Monitor bot status
   - Quick emergency stop access

2. **Use Multiple Screens**
   - Chart on one screen
   - Pattern overlay visible
   - Quick monitoring

3. **Regular Backups**
   - Export trade history
   - Save configuration files
   - Backup API credentials securely

---

## Next Steps

- ✅ **Completed Setup** → Start Paper Trading
- ✅ **Tested Strategies** → Switch to Live Trading
- ✅ **Live Trading Active** → Monitor & Optimize

**See Also:**
- [Quick Start Guide](./QUICKSTART.md)
- [FAQ](./FAQ.md)
- [Changelog](./CHANGELOG.md)
- [Implementation Log](./IMPLEMENTATION_LOG.md)

---

**Last Updated:** October 22, 2025
**Version:** 2.0.0
**For Support:** See FAQ or create GitHub issue
