# Quick Start Guide

Get up and running with Scalping Bot in 10 minutes!

## Step 1: Install Python Dependencies

```bash
# Make sure you're in the scalping-bot directory
cd scalping-bot

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Get API Credentials

1. Go to **https://kite.trade**
2. Login with your Zerodha account
3. Click **"Create App"**
4. Fill in:
   - **App Name**: ScalpingBot
   - **Redirect URL**: `http://localhost:8080/callback`
   - **Type**: Connect
5. Click **Submit**
6. Copy your **API Key** and **API Secret**

## Step 3: Configure Credentials

```bash
# Copy the example secrets file
cp config/secrets.env.example config/secrets.env

# Edit with your credentials
nano config/secrets.env  # or use any text editor
```

Add your credentials:
```bash
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
```

Save and close.

## Step 4: Run Setup Wizard

```bash
python main.py --setup
```

Follow the prompts to review your configuration.

## Step 5: Authenticate

```bash
python main.py --auth
```

1. Copy the URL shown in the terminal
2. Open it in your browser
3. Login with Zerodha credentials
4. Copy the `request_token` from the redirect URL
5. Paste it back in the terminal

You should see: ✅ **Authentication successful!**

## Step 6: Start Paper Trading

```bash
python main.py --paper
```

The bot will:
- Connect to live market data
- Generate trading signals
- Simulate order execution (no real money!)
- Display performance in logs

Open **http://localhost:8050** in your browser to see the dashboard.

## Step 7: Monitor Performance

- Watch the terminal for log output
- Check the web dashboard for real-time status
- Review logs in the `logs/` directory

**Press Ctrl+C to stop**

---

## Next Steps

### Test Thoroughly
- Run in paper mode for at least 2 months
- Trade through different market conditions
- Review all trades and understand why they were taken

### Optimize Settings
- Adjust strategy parameters in `config/config.yaml`
- Tune risk management settings
- Add/remove instruments based on liquidity

### Go Live (When Ready)
```bash
python main.py --live
```

⚠️ **Only after thorough testing!**

---

## Common Commands

```bash
# Show help
python main.py --help-detailed

# Run setup wizard
python main.py --setup

# Authenticate
python main.py --auth

# Paper trading
python main.py --paper

# Backtesting
python main.py --backtest

# Live trading (careful!)
python main.py --live
```

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Authentication failed"
- Check API credentials in `config/secrets.env`
- Verify Kite Connect subscription is active
- Try re-authenticating: `python main.py --auth`

### "WebSocket disconnected"
- Check internet connection
- Verify Zerodha API status at https://status.zerodha.com

### More help
- See `docs/FAQ.md` for detailed troubleshooting
- Check logs in `logs/` directory

---

## Configuration Checklist

Before going live, verify:

- [ ] API credentials configured
- [ ] Successfully authenticated
- [ ] Trading capital set correctly
- [ ] Risk limits configured (max daily loss, position size)
- [ ] Instruments selected (liquid, high-volume stocks)
- [ ] Strategy parameters reviewed
- [ ] Stop-loss enabled (mandatory!)
- [ ] Paper traded for 2+ months
- [ ] Positive net P&L in paper trading
- [ ] Static IP configured (SEBI compliance)
- [ ] Emergency procedures understood

---

## File Structure

```
scalping-bot/
├── config/
│   ├── config.yaml          ← Configure trading here
│   └── secrets.env          ← Add API credentials here
├── logs/                    ← Check logs here
├── main.py                  ← Run this
└── docs/
    ├── FAQ.md               ← Read for troubleshooting
    └── README.md            ← Full documentation
```

---

## Support

- **Documentation**: See `README.md` and `docs/`
- **FAQ**: Check `docs/FAQ.md`
- **Issues**: GitHub Issues
- **Community**: Zerodha TradingQ&A forum

---

**You're all set! Happy trading! 📈**

Remember: Always test in paper mode first, and never trade more than you can afford to lose.
