# Scalping Bot - Algorithmic Trading Software

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A minimal, easy-to-use algorithmic trading system for daily scalping strategies on Indian equity markets through **Zerodha Kite Connect API**.

## ⚠️ Important Disclaimer

**Trading involves substantial risk of loss. This software is provided for educational purposes. Always:**
- Test thoroughly in paper trading mode before using real money
- Only trade with capital you can afford to lose
- Understand the risks and strategies before deploying
- Comply with SEBI regulations for algorithmic trading
- Monitor the bot's performance regularly

## ✨ Features

### Core Features
- ✅ **Real-time Market Data** - WebSocket streaming for live prices
- ✅ **Multiple Trading Strategies** - EMA+RSI, Bollinger Bands, and more
- ✅ **Automated Order Execution** - Fast, reliable order placement
- ✅ **Position Tracking** - Real-time P&L monitoring
- ✅ **Risk Management** - Stop-loss, position sizing, daily limits
- ✅ **Paper Trading** - Test without real money
- ✅ **Backtesting Engine** - Validate strategies on historical data
- ✅ **Web Dashboard** - Monitor trades and performance
- ✅ **Alerts** - Telegram and email notifications

### Safety Features
- 🛡️ Mandatory stop-loss on every trade
- 🛡️ Daily loss limits (auto-halt trading)
- 🛡️ Maximum position size limits
- 🛡️ Circuit breakers for consecutive losses
- 🛡️ Emergency kill switch
- 🛡️ Comprehensive audit logs

### SEBI Compliance
- 📋 Unique Algorithm IDs
- 📋 Static IP configuration
- 📋 Complete audit trails (5-year retention)
- 📋 White-box strategy documentation

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.10 or higher
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 1GB for logs and data
- **Internet**: Stable connection with low latency

### Account Requirements
- Active Zerodha trading account
- Kite Connect API subscription (₹2,000/month)
- Sufficient trading capital (recommended: ₹50,000+)
- Static IP address (for SEBI compliance)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the repository
cd scalping-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Run setup wizard
python main.py --setup

# Follow the prompts to:
# - Copy secrets.env.example to secrets.env
# - Add your API credentials
# - Review config.yaml settings
```

### 3. Authentication

```bash
# Authenticate with Zerodha
python main.py --auth

# Follow the instructions to:
# 1. Open the login URL in your browser
# 2. Login with Zerodha credentials
# 3. Copy the request token
# 4. Paste it back in the terminal
```

### 4. Paper Trading

```bash
# Start paper trading (simulated, no real money)
python main.py --paper

# Monitor in the web dashboard: http://localhost:8050
```

### 5. Go Live (when ready)

```bash
# ⚠️ Only after thorough testing!
python main.py --live
```

## 📁 Project Structure

```
scalping-bot/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── secrets.env.example      # Credentials template
│   └── secrets.env              # Your credentials (create this)
├── src/
│   ├── auth/                    # Authentication
│   │   └── zerodha_auth.py
│   ├── data/                    # Market data handlers
│   │   ├── market_data.py
│   │   └── historical_data.py
│   ├── strategy/                # Trading strategies
│   │   ├── base_strategy.py
│   │   ├── ema_rsi_strategy.py
│   │   └── bb_breakout_strategy.py
│   ├── execution/               # Order execution
│   │   ├── order_manager.py
│   │   └── position_tracker.py
│   ├── risk/                    # Risk management
│   │   └── risk_manager.py
│   ├── dashboard/               # Web dashboard
│   │   └── app.py
│   └── utils/                   # Utilities
│       ├── logger.py
│       ├── config_loader.py
│       └── alerts.py
├── logs/                        # Log files
├── data/                        # Historical data
├── tests/                       # Unit tests
├── docs/                        # Documentation
│   ├── FAQ.md
│   ├── STRATEGY_GUIDE.md
│   └── API_REFERENCE.md
├── main.py                      # Main entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## ⚙️ Configuration

### Main Configuration (`config/config.yaml`)

```yaml
trading:
  mode: paper              # 'paper' or 'live'
  capital: 100000          # Starting capital (₹)
  risk_per_trade_percent: 1.0
  max_positions: 3
  max_trades_per_day: 50

instruments:
  - symbol: RELIANCE
    exchange: NSE
    enabled: true
  # Add more instruments...

strategies:
  - name: ema_rsi
    enabled: true
    params:
      fast_ema: 9
      slow_ema: 21
      # ... more parameters

risk:
  max_daily_loss_percent: 2.0
  circuit_breaker:
    consecutive_losses: 3
```

### API Credentials (`config/secrets.env`)

```bash
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
TELEGRAM_BOT_TOKEN=optional_telegram_token
```

**⚠️ Never commit `secrets.env` to version control!**

## 📊 Trading Strategies

### 1. EMA Crossover + RSI Filter

**Entry Conditions:**
- Fast EMA (9) crosses above Slow EMA (21)
- RSI (14) between 40-60 (neutral zone)
- Volume > 1.2x average

**Exit Conditions:**
- Target: +0.8% profit
- Stop-loss: -0.4% loss
- Trailing stop after +0.3% profit
- Time-based: Close after 5 minutes

### 2. Bollinger Bands Breakout

**Entry Conditions:**
- Price breaks above/below Bollinger Bands
- RSI confirms momentum (>60 long, <40 short)
- MACD histogram shows direction

**Exit Conditions:**
- Price reverts to middle band
- Fixed stop-loss: 1 ATR
- Target: 1.5 ATR

See `docs/STRATEGY_GUIDE.md` for detailed configuration options.

## 🎯 Risk Management

### Position Sizing
- Risk per trade: 1-2% of capital
- ATR-based sizing for volatility adjustment
- Maximum exposure: 25% of total capital

### Stop-Loss
- Mandatory on every trade
- Options: Fixed percentage, ATR-based, or trailing
- Never move stop-loss to increase risk

### Daily Limits
- Maximum daily loss: 2% of capital
- Maximum trades per day: 50
- Auto-halt on limits reached

### Circuit Breakers
- Halt after 3 consecutive losses
- Halt on excessive API errors
- Halt on abnormal slippage (>0.5%)

## 📈 Monitoring & Alerts

### Web Dashboard
- Real-time position tracking
- Live P&L updates
- Trade history
- Strategy performance metrics
- Manual controls (pause/resume, emergency stop)

Access at: `http://localhost:8050`

### Telegram Alerts
Configure in `config/config.yaml`:
```yaml
alerts:
  telegram:
    enabled: true
    bot_token: YOUR_BOT_TOKEN
    chat_id: YOUR_CHAT_ID
```

Receive notifications for:
- Trade executions
- Errors and warnings
- Daily P&L summary
- Risk limit alerts

## 🧪 Testing

### Paper Trading
```bash
python main.py --paper
```
- Connects to live market data
- Simulates order execution
- Tracks virtual P&L
- No real money at risk

### Backtesting
```bash
python main.py --backtest
```
- Tests strategies on historical data
- Includes realistic slippage and costs
- Generates performance reports

### Unit Tests
```bash
pytest tests/
pytest tests/ --cov=src  # With coverage
```

## 🔒 Security Best Practices

1. **Protect Your Credentials**
   - Never commit `secrets.env` to version control
   - Use environment variables for sensitive data
   - Rotate API keys periodically

2. **Secure Your System**
   - Use firewall to restrict access
   - Keep Python and dependencies updated
   - Run with minimal privileges

3. **Monitor Access**
   - Review logs regularly
   - Set up alerts for suspicious activity
   - Use static IP for trading

## 📚 Documentation

- **[FAQ](docs/FAQ.md)** - Common questions and troubleshooting
- **[Strategy Guide](docs/STRATEGY_GUIDE.md)** - Configure and optimize strategies
- **[API Reference](docs/API_REFERENCE.md)** - Code documentation

## 🐛 Troubleshooting

### Common Issues

**Authentication fails:**
- Verify API credentials in `config/secrets.env`
- Check if Kite Connect subscription is active
- Ensure request token is copied correctly

**WebSocket disconnects:**
- Check internet connection
- Verify Zerodha API status
- Review reconnection settings in config

**Orders rejected:**
- Verify sufficient margin
- Check order size limits
- Review broker-specific restrictions

See `docs/FAQ.md` for more troubleshooting tips.

## 📖 Learning Resources

### Zerodha Kite Connect
- [Official Documentation](https://kite.trade/docs/connect/v3/)
- [Python Client](https://github.com/zerodha/pykiteconnect)
- [API Forum](https://kite.trade/forum/)

### Algorithmic Trading
- [QuantInsti](https://www.quantinsti.com/) - Algo trading courses
- [Backtrader Documentation](https://www.backtrader.com/docu/)
- [Python for Finance](https://www.oreilly.com/library/view/python-for-finance/9781492024323/)

### SEBI Regulations
- [SEBI Algo Trading Circular](https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Legal & Compliance

### SEBI Regulations (Effective Oct 2025)
- All algorithms must be registered with exchanges
- Each strategy must have a unique Algo ID
- Mandatory static IP for order routing
- Complete audit trails required (5-year retention)
- White-box algorithms preferred over black-box

### Disclaimer
This software is provided "as is" without warranty of any kind. The authors and contributors are not responsible for any financial losses incurred through the use of this software. Users are solely responsible for:
- Testing and validation
- Risk management
- Regulatory compliance
- Financial outcomes

**Trading involves substantial risk. Only trade with money you can afford to lose.**

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/scalping-bot/issues)
- **Questions**: See `docs/FAQ.md`
- **Updates**: Check releases for new versions

## 🎯 Roadmap

### v1.0 (Current)
- [x] Core trading engine
- [x] EMA+RSI strategy
- [x] Risk management
- [x] Paper trading
- [x] Web dashboard
- [x] Telegram alerts

### v1.1 (Planned)
- [ ] Additional strategies (VWAP, Supertrend)
- [ ] Advanced backtesting with walk-forward analysis
- [ ] Options trading support
- [ ] Machine learning signal filters
- [ ] Mobile app for monitoring

### v2.0 (Future)
- [ ] Multi-broker support
- [ ] Cloud deployment
- [ ] Strategy marketplace
- [ ] Advanced analytics
- [ ] Multi-user support

---

**Happy Trading! 📈 Remember: Always test thoroughly before going live!**

Made with ❤️ for the Indian algo trading community.
