# XCoin Scalping Bot - Quick Start Guide (5 Minutes)

**⚡ Get trading in 5 minutes!**

---

## Step 1: Install (1 minute)

```bash
cd scalping-bot
pip install -r requirements.txt
```

---

## Step 2: Database Setup (1 minute)

```bash
# Set database URL
export DATABASE_URL="postgresql://postgres:password@localhost:5432/scalping_bot"

# Create database
psql -U postgres -c "CREATE DATABASE scalping_bot;"

# Initialize schema
python -c "from src.database.db import init_db; init_db()"
```

---

## Step 3: Configure Broker (2 minutes)

Create `config/secrets.env`:

```bash
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
```

---

## Step 4: Start Dashboard (30 seconds)

```bash
python run_dashboard.py
```

Open: http://localhost:8050

---

## Step 5: First Strategy (30 seconds)

1. Go to **Strategies** → **Create New**
2. Select **EMA Crossover** template
3. Click **Save**

---

## Step 6: Backtest (1 minute)

1. Click **Backtest** button
2. Date range: Last 6 months
3. Click **Run**
4. Review results

---

## Step 7: Paper Trading (Ready!)

1. Go to **Home**
2. Click **Start Bot**
3. Select **Paper Trading** mode
4. Click **Confirm**

**✅ You're now paper trading!**

---

## What to Do Next

- Monitor dashboard for 15-20 days
- Review trades daily
- Check USER_GUIDE.md for details
- Go live only after validation

---

## Need Help?

**Quick References:**
- `USER_GUIDE.md` - Complete guide (30+ pages)
- `QUICK_VERIFICATION_SUMMARY.txt` - System status
- `ISSUES_AND_FIXES.md` - Troubleshooting

**Support:**
- Check logs: `tail -f logs/system.log`
- GitHub Issues: [Your Repo]
- Email: support@yourproject.com

---

**⚠️ IMPORTANT:**
- Always start with Paper Trading
- Never skip backtesting
- Use stop-losses on every trade
- Risk max 2% per trade
- Monitor daily during first month

---

**Happy Trading! 🚀**
