# Frequently Asked Questions (FAQ)

## Table of Contents
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Trading](#trading)
- [Technical Issues](#technical-issues)
- [Risk & Safety](#risk--safety)
- [Compliance](#compliance)
- [Performance](#performance)

---

## Getting Started

### Q: What do I need to get started with the Scalping Bot?

**A:** You need:
1. **Zerodha Trading Account** - Active demat and trading account
2. **Kite Connect API Access** - Subscribe at https://kite.trade (₹2,000/month)
3. **Trading Capital** - Recommended minimum ₹50,000
4. **Python 3.10+** - Installed on your system
5. **Stable Internet** - Low-latency connection
6. **Static IP** - Required for SEBI compliance

### Q: Is this software free?

**A:** Yes, the software is free and open-source (MIT License). However, you'll need:
- Zerodha Kite Connect subscription: ₹2,000/month
- Trading capital
- Optional: VPS hosting (₹500-1,500/month)

### Q: How do I get API credentials?

**A:**
1. Login to https://kite.trade
2. Click "Create App"
3. Fill in app details:
   - Name: Your bot name
   - Redirect URL: `http://localhost:8080/callback`
   - Type: Connect
4. Submit and get your API Key and Secret
5. Add them to `config/secrets.env`

### Q: Can beginners use this bot?

**A:** While the bot is designed to be user-friendly, you should have:
- Basic understanding of algorithmic trading
- Knowledge of technical indicators (EMA, RSI, etc.)
- Risk management principles
- Some Python familiarity (for troubleshooting)

**Start with paper trading for at least 1-2 months!**

---

## Configuration

### Q: How do I configure the bot for my trading style?

**A:** Edit `config/config.yaml`:

```yaml
trading:
  capital: 100000           # Your capital
  risk_per_trade_percent: 1.0  # Risk per trade (1-2%)
  max_positions: 3          # Concurrent trades

strategies:
  - name: ema_rsi
    enabled: true           # Enable/disable strategies
    params:
      fast_ema: 9           # Customize parameters
      slow_ema: 21
```

### Q: Which instruments should I trade?

**A:** Start with:
- **Liquid large-cap stocks**: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK
- **Characteristics**:
  - Average volume > 1M shares/day
  - Tight bid-ask spreads
  - Lower volatility (1-2% daily)

Avoid:
- Penny stocks
- Illiquid stocks
- Stocks in F&O ban

### Q: How do I add a new instrument?

**A:** In `config/config.yaml`:

```yaml
instruments:
  - symbol: SBIN           # Stock symbol
    exchange: NSE          # NSE or BSE
    lot_size: 1            # Usually 1 for equities
    enabled: true          # Enable trading
```

### Q: Can I run multiple strategies simultaneously?

**A:** Yes! Enable multiple strategies in config:

```yaml
strategies:
  - name: ema_rsi
    enabled: true

  - name: bb_breakout
    enabled: true
```

The bot will trade signals from all enabled strategies, subject to risk limits.

---

## Trading

### Q: What's the difference between paper and live trading?

**A:**

| Feature | Paper Trading | Live Trading |
|---------|--------------|--------------|
| Real Money | ❌ No | ✅ Yes |
| Market Data | ✅ Live | ✅ Live |
| Order Execution | 🔸 Simulated | ✅ Real |
| Risk | ❌ None | ⚠️ Capital at risk |
| Purpose | Testing | Production |

**Always test in paper mode first!**

### Q: How long should I paper trade before going live?

**A:** Minimum recommendations:
- **2 months** of consistent paper trading
- **100+ trades** executed
- **Positive net P&L** over multiple weeks
- **Tested across different market conditions** (trending, sideways, volatile)
- **All edge cases handled** (connection issues, errors, etc.)

### Q: What time should the bot run?

**A:**
- **Market hours**: 9:15 AM - 3:30 PM IST
- **Best times for scalping**:
  - 9:15-10:30 AM (high volatility)
  - 2:30-3:20 PM (closing moves)
- **Avoid**: 12:00-1:00 PM (low volume)

The bot automatically stops trading at 3:20 PM to square off positions.

### Q: How many trades will the bot make per day?

**A:** Depends on:
- Market volatility
- Number of instruments
- Strategy parameters
- Signal frequency

Typical range: **5-20 trades per day**

You can limit with `max_trades_per_day` in config.

### Q: What's the expected win rate?

**A:** Realistic expectations:
- **Win rate**: 50-60%
- **Risk-reward**: 1:1.5 to 1:2
- **Monthly return**: 5-15% (in favorable conditions)

**Remember**: No strategy wins 100% of the time!

### Q: Can I manually override the bot?

**A:** Yes, through the web dashboard:
- Pause/resume trading
- Close all positions
- Enable/disable specific strategies
- Emergency stop button

**Never interfere during active trades unless absolutely necessary.**

---

## Technical Issues

### Q: The bot won't start. What should I check?

**A:** Troubleshooting checklist:

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Verify dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check configuration**:
   - `config/config.yaml` exists and is valid
   - `config/secrets.env` contains API credentials

4. **Review logs**:
   ```bash
   tail -f logs/system.log
   ```

### Q: Authentication keeps failing

**A:** Common causes:

1. **Invalid credentials**
   - Verify API key and secret in `secrets.env`
   - Check for spaces or quotes in credentials

2. **Expired access token**
   - Re-authenticate: `python main.py --auth`
   - Access tokens expire daily

3. **Kite Connect subscription**
   - Ensure subscription is active at https://kite.trade

4. **Network issues**
   - Check internet connection
   - Verify no firewall blocking

### Q: WebSocket keeps disconnecting

**A:** Solutions:

1. **Check internet stability**
   - Use wired connection over WiFi
   - Test latency: `ping kite.zerodha.com`

2. **Verify Zerodha API status**
   - Check https://status.zerodha.com

3. **Adjust reconnection settings** in `config/config.yaml`:
   ```yaml
   advanced:
     websocket_reconnect_attempts: 10
     websocket_reconnect_delay: 10
   ```

4. **Consider VPS hosting**
   - Better uptime and lower latency

### Q: Orders are being rejected

**A:** Common reasons:

1. **Insufficient margin**
   - Check available funds in Zerodha
   - Reduce position size

2. **Price limits**
   - Order price outside circuit limits
   - Use MARKET orders for scalping

3. **RMS blocks**
   - Zerodha Risk Management System blocks
   - Check with broker

4. **Order rate limits**
   - Too many orders too quickly
   - Adjust `order_rate_limit` in config

### Q: High CPU/memory usage

**A:** Optimization tips:

1. **Reduce tick buffer size**:
   ```yaml
   advanced:
     tick_buffer_size: 200  # Default: 500
   ```

2. **Limit instruments**:
   - Trade fewer stocks simultaneously
   - Disable unused strategies

3. **Adjust log level**:
   ```yaml
   logging:
     level: INFO  # Use INFO instead of DEBUG
   ```

4. **Close other applications**
   - Free up system resources

---

## Risk & Safety

### Q: How does the bot manage risk?

**A:** Multiple layers:

1. **Per-trade risk**: Maximum 1-2% of capital
2. **Position sizing**: ATR-based or fixed-risk
3. **Stop-loss**: Mandatory on every trade
4. **Daily limits**: 2% max daily loss
5. **Circuit breakers**: Halt after 3 consecutive losses
6. **Maximum exposure**: 25% of capital

### Q: What happens if the bot loses money?

**A:**
- **Small losses**: Normal part of trading, covered by wins
- **Daily limit reached**: Bot auto-halts trading
- **Circuit breaker triggered**: Requires manual review to restart
- **Persistent losses**: Review and adjust strategy parameters

**Trading involves risk. Only trade what you can afford to lose.**

### Q: Can the bot go into unlimited loss?

**A:** No, protections in place:

1. **Stop-loss on every trade** - Limits per-trade loss
2. **Daily loss limit** - Halts trading at 2% loss
3. **Position size limits** - Caps maximum exposure
4. **No overnight positions** - All squared off before 3:20 PM

**However, gaps and slippage can cause losses beyond stop-loss.**

### Q: How do I use the emergency stop?

**A:** Three ways:

1. **Web dashboard**: Click "Emergency Stop" button
2. **Keyboard**: Press `Ctrl+C` in terminal
3. **Kill process**: `pkill -f main.py`

The bot will:
- Cancel all pending orders
- Close all open positions (MARKET orders)
- Disconnect from API
- Save logs

### Q: What if my internet/power goes down?

**A:** Risks:

- Open positions remain open
- Stop-losses may not execute
- Orders may not be cancelled

**Mitigation**:
- Use UPS for power backup
- Keep 4G/5G backup internet
- Consider VPS hosting (99.9% uptime)
- Set broker-level stop-losses as backup

---

## Compliance

### Q: Is algorithmic trading legal in India?

**A:** Yes, but regulated by SEBI. Requirements:
- Algorithm must be registered with exchange
- Unique Algo ID for each strategy
- Static IP address
- Complete audit trails (5-year retention)
- Broker approval for high-frequency trading

### Q: Do I need SEBI approval?

**A:**
- **Retail traders**: No direct SEBI approval needed for basic algos
- **High-frequency trading**: May need broker pre-approval
- **Black-box strategies**: Provider must be SEBI-registered Research Analyst

**Consult your broker for latest requirements.**

### Q: How do I register my algorithm?

**A:**
1. Document strategy logic (white-box format)
2. Contact your broker (Zerodha)
3. Provide strategy details and Algo ID
4. Get approval from exchange
5. Configure Algo ID in `config/config.yaml`:
   ```yaml
   compliance:
     algo_id: YOUR_ALGO_ID
     static_ip: YOUR_STATIC_IP
   ```

### Q: What records must I maintain?

**A:** SEBI requires:
- All order requests and responses
- Strategy signals and decisions
- Market data at decision time
- Risk checks applied
- System logs

**The bot automatically maintains all required audit trails.**

---

## Performance

### Q: How do I measure bot performance?

**A:** Key metrics:

1. **Total Return**: Net profit/loss
2. **Win Rate**: % of profitable trades
3. **Profit Factor**: Gross profit / Gross loss
4. **Sharpe Ratio**: Risk-adjusted returns
5. **Maximum Drawdown**: Largest peak-to-trough loss
6. **Average trade duration**: Typical holding period

View in dashboard or backtest reports.

### Q: My bot is underperforming. What should I do?

**A:** Diagnostic steps:

1. **Review trades**:
   - Check `logs/trades.log`
   - Identify losing patterns

2. **Analyze market conditions**:
   - Trending vs. sideways
   - High vs. low volatility
   - Strategy may not suit current market

3. **Check execution quality**:
   - Slippage levels
   - Order fill rates
   - Latency issues

4. **Backtest parameters**:
   - Test different parameter combinations
   - Avoid overfitting

5. **Consider market regime change**:
   - Strategies perform differently in different markets
   - May need to adjust or switch strategies

### Q: How do I optimize strategy parameters?

**A:**

1. **Run backtests** with different parameters:
   ```bash
   python main.py --backtest
   ```

2. **Use parameter sweep**:
   - Test range of values (e.g., EMA: 5-20)
   - Measure performance metrics

3. **Validate out-of-sample**:
   - Train on 70% of data
   - Test on remaining 30%

4. **Walk-forward analysis**:
   - Optimize on rolling windows
   - Validate on next period

**Warning**: Over-optimization leads to curve-fitting!

### Q: Can I backtest before going live?

**A:** Yes, strongly recommended!

```bash
python main.py --backtest
```

Backtesting:
- Uses historical data
- Simulates strategy execution
- Includes slippage and costs
- Generates performance reports

**Backtest for at least 6-12 months of data.**

---

## Additional Questions

### Q: Can I use this with other brokers?

**A:** Currently, only Zerodha is supported.

Adding other brokers requires:
- Implementing broker-specific API client
- Adapting order management
- Testing thoroughly

Planned for future versions: Upstox, Angel One, Finvasia.

### Q: Does the bot work with options or futures?

**A:** Phase 1 supports only **equity cash** trading.

Options and futures support planned for v1.1.

### Q: Can I run multiple bots simultaneously?

**A:** Yes, but:
- Use different config files
- Different port for each dashboard
- Monitor total capital allocation
- Avoid trading same instruments on multiple bots

### Q: How do I update the bot?

**A:**

1. **Backup current setup**:
   ```bash
   cp -r config config.backup
   cp -r logs logs.backup
   ```

2. **Update code**:
   ```bash
   git pull  # If using git
   ```

3. **Update dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Review config changes**:
   - Check for new parameters
   - Merge with your config

5. **Test thoroughly** before going live

### Q: Where can I get help?

**A:**

1. **Check documentation**:
   - README.md
   - FAQ.md (this file)
   - STRATEGY_GUIDE.md

2. **Review logs**:
   - `logs/system.log` - System events
   - `logs/errors.log` - Errors only

3. **Community**:
   - GitHub Issues
   - Zerodha TradingQ&A forum
   - Algorithmic trading communities

4. **Professional help**:
   - Consider hiring a developer
   - Consult with algo trading experts

---

## Still Have Questions?

If your question isn't answered here:

1. Check other documentation files
2. Search GitHub Issues
3. Review system logs
4. Create a new GitHub Issue with:
   - Detailed description
   - Steps to reproduce
   - Relevant log excerpts
   - System information

---

**Happy Trading! Remember to always test thoroughly and trade responsibly.**

*Last updated: 2025-10-17*
