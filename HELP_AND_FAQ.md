# XCoin Scalping Bot - Help & FAQ

**Complete help system with answers to all common questions**

---

## 📑 Table of Contents

### Quick Links
- [🔍 Search Help Topics](#search-help)
- [🎯 Getting Started](#getting-started-faq)
- [📊 Trading Operations](#trading-faq)
- [📈 Chart & Indicators](#chart-faq)
- [⚠️ Stop-Loss Management](#stop-loss-faq)
- [💰 Risk & Money Management](#risk-faq)
- [🔧 Technical Issues](#technical-faq)
- [🚨 Emergency Situations](#emergency-faq)

### User Flows
- [📖 Complete User Journey](#user-journey)
- [🎬 Taking Your First Trade](#first-trade-flow)
- [📊 Adding Indicators to Charts](#indicators-flow)
- [🛡️ Setting Stop-Loss](#stop-loss-flow)
- [🔄 Moving Stop-Loss](#moving-stop-loss-flow)
- [⚡ Quick Actions Guide](#quick-actions)

---

## 🔍 Search Help Topics {#search-help}

### How to Search This Document

**Method 1: Browser Search**
- Press `Ctrl + F` (Windows/Linux) or `Cmd + F` (Mac)
- Type your keyword
- Navigate through results

**Method 2: Navigate by Topic**
- Use Table of Contents above
- Click section links
- Bookmark frequently used sections

**Method 3: Quick Search by Keywords**

```
Need help with...          → Go to section...
├─ Setting up             → Getting Started FAQ
├─ Taking trades          → First Trade Flow
├─ Stop-loss issues       → Stop-Loss FAQ
├─ Charts not loading     → Technical FAQ
├─ Bot won't start        → Technical FAQ
├─ Broker errors          → Trading FAQ
├─ Pattern detection      → Chart FAQ
├─ Emergency situations   → Emergency FAQ
└─ Risk management        → Risk FAQ
```

---

## 🎯 Getting Started FAQ {#getting-started-faq}

### Q1: What are the system requirements?

**Minimum Requirements:**
- **OS:** Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python:** 3.8 or higher
- **RAM:** 4 GB minimum, 8 GB recommended
- **Storage:** 2 GB free space
- **Database:** PostgreSQL 12+
- **Internet:** Stable broadband connection (10+ Mbps)

**Recommended Setup:**
- **OS:** Ubuntu 22.04 or macOS (for production)
- **Python:** 3.10+
- **RAM:** 16 GB
- **Storage:** 10 GB SSD
- **Database:** PostgreSQL 14+
- **Internet:** 50+ Mbps with backup connection

---

### Q2: How do I install the bot?

**Step-by-Step Installation:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/scalping-bot.git
cd scalping-bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup database
export DATABASE_URL="postgresql://user:pass@localhost:5432/scalping_bot"
python -c "from src.database.db import init_db; init_db()"

# 5. Configure broker
# Create config/secrets.env with your API credentials

# 6. Start dashboard
python run_dashboard.py
```

**Detailed Guide:** See [QUICKSTART.md](QUICKSTART.md)

---

### Q3: Which broker should I use?

**Broker Comparison:**

| Feature | Zerodha | Angel One | Kotak |
|---------|---------|-----------|-------|
| **API Cost** | Free | Free | Paid |
| **Setup Difficulty** | Easy | Easy | Moderate |
| **Documentation** | Excellent | Good | Average |
| **Support** | Best | Good | Good |
| **Recommended For** | Beginners | Intermediate | Advanced |
| **Latency** | <200ms | <300ms | <250ms |

**Recommendation:** Start with **Zerodha Kite Connect**
- Most popular in India
- Best documentation
- Large community support
- Easy authentication
- Free API access

---

### Q4: Do I need TA-Lib installed?

**Short Answer:** No, but recommended.

**Without TA-Lib:**
- ✅ All features work
- ✅ Pattern detection functional
- ✅ Backtesting operational
- ⚠️ Slightly slower calculations

**With TA-Lib:**
- ✅ Faster indicator calculations
- ✅ More accurate patterns
- ✅ Better performance

**Install TA-Lib (Optional):**

```bash
# macOS
brew install ta-lib

# Ubuntu/Linux
sudo apt-get install ta-lib

# Then install Python wrapper
pip install TA-Lib
```

---

### Q5: How much capital do I need to start?

**Minimum Requirements:**

**Paper Trading:**
- ₹0 (virtual money)
- Recommended: Simulate with ₹100,000

**Live Trading:**
- Absolute minimum: ₹10,000
- Recommended minimum: ₹50,000
- Comfortable start: ₹100,000+

**Capital Allocation:**
```
Total Capital: ₹100,000
├─ Trading Capital: ₹70,000 (70%)
├─ Cash Reserve: ₹20,000 (20%)
└─ Emergency Fund: ₹10,000 (10%)

Per Trade Risk: ₹1,400 (2% of ₹70,000)
Max Positions: 3-5
Position Size: ₹14,000-23,000 each
```

**Important:** Start small, scale gradually based on performance.

---

## 📊 Trading Operations FAQ {#trading-faq}

### Q6: How do I start the bot?

**Complete Start Process:**

**Step 1: Authenticate Broker**
```
1. Open dashboard: http://localhost:8050
2. Go to Settings → Broker Configuration
3. Click "Connect to Zerodha"
4. Enter Zerodha credentials
5. Authorize the app
6. Verify green checkmark appears
```

**Step 2: Select Strategy**
```
1. Go to Strategies page
2. Choose existing strategy OR
3. Click "Create New Strategy"
4. Configure parameters
5. Click "Save"
```

**Step 3: Backtest (MANDATORY)**
```
1. Click "Backtest" button
2. Set date range (6 months minimum)
3. Click "Run Backtest"
4. Review results
5. Verify win rate >50%, profit factor >1.5
```

**Step 4: Deploy in Paper Mode**
```
1. Click "Deploy Strategy"
2. Select "Paper Trading" mode
3. Set capital: ₹100,000
4. Set max positions: 3
5. Click "Confirm"
```

**Step 5: Start Bot**
```
1. Go to Home/Dashboard
2. Click "Start Bot" button
3. Confirm mode is "Paper"
4. Bot status changes to "Running"
5. Monitor dashboard
```

---

### Q7: Why isn't my bot generating signals?

**Common Reasons:**

**1. Market Conditions Don't Meet Criteria**
- **Cause:** Price action doesn't match strategy rules
- **Solution:** Normal behavior, wait for valid setup
- **Example:** EMA crossover needs crossover to occur

**2. Insufficient Historical Data**
- **Cause:** Strategy needs minimum candles (50-200)
- **Solution:** Wait 30-60 minutes for data accumulation
- **Check:** Dashboard shows data loading progress

**3. Wrong Symbol Configuration**
- **Cause:** Symbols not correctly formatted
- **Solution:** Use exact exchange symbols
- **Examples:**
  - ✅ Correct: "RELIANCE", "TCS", "INFY"
  - ❌ Wrong: "Reliance Industries", "tcs", "Infosys"

**4. Strategy Disabled**
- **Cause:** Strategy marked as disabled
- **Solution:** Go to Strategies → Enable strategy

**5. Risk Limits Reached**
- **Cause:** Daily loss limit or max positions exceeded
- **Solution:** Wait for next day or close positions

**How to Debug:**
```bash
# Check logs
tail -f logs/signals.log

# Look for:
# - "Signal generated: BUY/SELL"
# - "Insufficient data, need X more candles"
# - "No valid setup detected"
```

---

### Q8: How do I take a manual trade?

**Method 1: Via Dashboard (Recommended)**

```
Step 1: Open Trade Panel
├─ Click "Manual Trade" button (top-right)
└─ Trade panel slides in from right

Step 2: Select Symbol
├─ Search: Type "RELIANCE"
├─ Select from dropdown
└─ Current price displays

Step 3: Choose Direction
├─ Click "BUY" (green) for long
└─ Click "SELL" (red) for short

Step 4: Set Quantity
├─ Enter number of shares
├─ Calculator shows total investment
└─ Risk calculator shows max loss

Step 5: Set Stop-Loss (REQUIRED)
├─ Enter stop-loss price OR
├─ Enter stop-loss percentage
├─ System validates 2:1 risk-reward
└─ Adjust if validation fails

Step 6: Set Target (Optional)
├─ Enter target price
├─ Risk-reward ratio displays
└─ Target should be 2x stop-loss distance

Step 7: Review & Confirm
├─ Review all parameters
├─ Check risk per trade (<2%)
├─ Verify account balance sufficient
└─ Click "Place Order"

Step 8: Confirmation
├─ Order ID displays
├─ Position appears in "Open Positions"
└─ P&L starts tracking
```

**Method 2: Via API (Advanced)**

```python
from src.trading.order_manager import OrderManager

# Initialize
order_manager = OrderManager(broker, mode='paper')

# Place order
response = order_manager.place_order(
    symbol='RELIANCE',
    exchange='NSE',
    transaction_type='BUY',
    quantity=10,
    order_type='MARKET',
    product='MIS',
    stop_loss=2400,  # ₹2,400
    target=2500      # ₹2,500
)

print(f"Order ID: {response['order_id']}")
```

**Important Validations:**
```
✅ Symbol exists
✅ Sufficient balance
✅ Stop-loss set
✅ Risk <2% per trade
✅ Max positions not exceeded
✅ Risk-reward ratio ≥1.5:1
✅ Broker connected
```

---

### Q9: How do I close a position manually?

**Method 1: Quick Close**

```
1. Go to Dashboard → Open Positions
2. Find position to close
3. Click "Close" button (red X)
4. Confirm closure
5. Position closes at market price
6. P&L calculated and displayed
```

**Method 2: Limit Order Close**

```
1. Click position row
2. Expand details panel
3. Click "Close with Limit"
4. Enter desired exit price
5. Click "Place Order"
6. Order waits for price to reach
```

**Method 3: Emergency Close All**

```
1. Click "Emergency Stop" button (top-right)
2. Confirm action
3. ALL positions close immediately
4. ALL pending orders cancelled
5. Bot stops automatically
```

---

### Q10: What do the position colors mean?

**Position Status Colors:**

🟢 **Green Position**
- In profit (unrealized P&L > 0)
- Current price above entry (BUY)
- Current price below entry (SELL)

🔴 **Red Position**
- In loss (unrealized P&L < 0)
- Current price below entry (BUY)
- Current price above entry (SELL)

🟡 **Yellow Position**
- Near stop-loss (within 0.5%)
- Warning: Position may close soon

🔵 **Blue Position**
- Near target (within 0.5%)
- Approaching profit target

⚪ **Gray Position**
- Closed position
- Historical record

**Position Details Display:**
```
Symbol: RELIANCE                 🟢 +₹450 (+2.3%)
Entry: ₹1,950 | Current: ₹1,995
Qty: 10 | Value: ₹19,500
Stop-Loss: ₹1,911 (-2%)         ⚠️ 4.2% away
Target: ₹2,028 (+4%)            🎯 1.7% away
Time: 2h 15m
```

---

## 📈 Chart & Indicators FAQ {#chart-faq}

### Q11: How do I view charts in the dashboard?

**Access Charts:**

```
Method 1: From Dashboard
├─ Click symbol name in positions table
└─ Chart opens in modal/sidebar

Method 2: From Chart Page
├─ Navigate to Charts (menu)
├─ Select symbol from dropdown
├─ Chart loads with default indicators
└─ Click fullscreen for larger view

Method 3: Quick View
├─ Hover over symbol name
└─ Mini chart preview appears
```

**Chart Features:**
- 📊 Candlestick/Line/Bar/Heikin-Ashi
- 📈 Multiple timeframes (1m, 5m, 15m, 1h, 1d)
- 🎯 Pattern markers
- 📍 Entry/exit points marked
- 📏 Drawing tools
- 💾 Save layouts

---

### Q12: How do I add indicators to a chart?

**Step-by-Step Guide:**

**Adding Indicator:**

```
Step 1: Open Indicators Panel
├─ Click "Indicators" button (top of chart)
└─ Panel slides from left

Step 2: Browse or Search
├─ Browse categories:
│   ├─ Trend (EMA, SMA, MACD)
│   ├─ Momentum (RSI, Stochastic)
│   ├─ Volatility (Bollinger, ATR)
│   └─ Volume (OBV, VWAP)
└─ Or search: Type "EMA" in search box

Step 3: Select Indicator
├─ Click indicator name
├─ Configuration panel opens
└─ Set parameters

Step 4: Configure Parameters
├─ Example: EMA
│   ├─ Period: 9 (fast) or 21 (slow)
│   ├─ Source: Close price
│   ├─ Color: Blue
│   └─ Line width: 2
└─ Click "Apply"

Step 5: Verify Indicator
├─ Indicator appears on chart
├─ Legend shows in top-left
└─ Can drag/resize if needed
```

**Popular Indicator Combinations:**

**For Trend Trading:**
```
Primary Chart:
├─ EMA 9 (blue)
├─ EMA 21 (orange)
└─ EMA 50 (red)

Lower Panel 1:
└─ MACD (12, 26, 9)

Lower Panel 2:
└─ Volume
```

**For Swing Trading:**
```
Primary Chart:
├─ Bollinger Bands (20, 2)
└─ SMA 200 (black)

Lower Panel 1:
└─ RSI (14)

Lower Panel 2:
└─ ATR (14)
```

**For Scalping:**
```
Primary Chart:
├─ VWAP (red)
├─ EMA 5 (green)
└─ EMA 13 (blue)

Lower Panel:
└─ Volume with MA
```

---

### Q13: How do I see pattern detections on the chart?

**Automatic Pattern Markers:**

**Candlestick Patterns:**
```
Display on Chart:
├─ 🟢 Bullish patterns (green markers)
│   ├─ Position: Below candle
│   ├─ Icon: ▲ or 🔼
│   └─ Tooltip: Pattern name + confidence
│
└─ 🔴 Bearish patterns (red markers)
    ├─ Position: Above candle
    ├─ Icon: ▼ or 🔽
    └─ Tooltip: Pattern name + confidence

Example Display:
                     ▼
                Shooting Star (85%)
     │───────────────────────────│
     │        ▲                   │
     │   Hammer (92%)             │
```

**Chart Patterns:**
```
Display on Chart:
├─ Drawn automatically
├─ Support/Resistance lines
├─ Pattern boundaries highlighted
├─ Target projection shown
└─ Label with pattern name

Example: Double Bottom
     Resistance ═════════════ (Target)
                 /\    /\
                /  \  /  \
               /    \/    \
     Support ════════════════ (Entry)
            │<─ Double Bottom ─>│
```

**Toggle Pattern Display:**
```
1. Click "Patterns" button (chart toolbar)
2. Select patterns to show:
   ☑ Candlestick Patterns
   ☑ Chart Patterns
   ☑ Support/Resistance
   ☐ Fibonacci Levels
3. Click "Apply"
```

**Pattern Information Panel:**
```
Click any pattern marker to see:
├─ Pattern Name
├─ Confidence Score
├─ Signal Type (Bullish/Bearish)
├─ Entry Level
├─ Stop-Loss Level
├─ Target Level
└─ Historical Win Rate
```

---

### Q14: Can I draw on the chart?

**Yes! Drawing Tools Available:**

**Access Drawing Tools:**
```
Toolbar Location: Left side of chart

Available Tools:
├─ ✏️  Trendline
├─ ─  Horizontal Line
├─ │  Vertical Line
├─ ▭  Rectangle
├─ 📏 Fibonacci Retracement
├─ 📐 Fibonacci Extension
├─ ➡️ Arrow
├─ 💬 Text Label
└─ 🗑️ Eraser
```

**Drawing Trendline Example:**

```
Step 1: Select Trendline Tool
├─ Click ✏️ icon
└─ Cursor changes to crosshair

Step 2: Draw Line
├─ Click first point (start)
├─ Move to second point
└─ Click to complete

Step 3: Customize (optional)
├─ Right-click line
├─ Select "Properties"
├─ Change:
│   ├─ Color
│   ├─ Width
│   ├─ Style (solid/dashed)
│   └─ Extension (project forward)
└─ Click "Save"

Step 4: Move/Delete
├─ Click line to select
├─ Drag to move
├─ Delete key to remove
└─ Or use eraser tool
```

**Save Drawings:**
```
1. Complete your analysis
2. Click "Save Layout" (top-right)
3. Name: "RELIANCE Support Levels"
4. Click "Save"
5. Access later: Layouts dropdown
```

---

## ⚠️ Stop-Loss Management FAQ {#stop-loss-faq}

### Q15: How do I set a stop-loss when taking a trade?

**Method 1: Percentage-Based (Recommended for Beginners)**

```
When Placing Order:

1. Enter Symbol: RELIANCE
2. Enter Quantity: 10 shares
3. Entry Price: ₹2,000

4. Set Stop-Loss:
   ├─ Select "Percentage" tab
   ├─ Enter: 2% (default)
   ├─ Calculated SL: ₹1,960
   └─ Risk per share: ₹40

5. Risk Calculation Displays:
   ├─ Total Risk: ₹400 (10 shares × ₹40)
   ├─ % of Capital: 0.4%
   └─ ✅ Within 2% limit

6. Set Target (Auto-calculated):
   ├─ Risk-Reward: 2:1
   ├─ Target: ₹2,080
   └─ Potential Profit: ₹800
```

**Method 2: Price-Based (Advanced)**

```
When Placing Order:

1. Symbol: TCS @ ₹3,500

2. Set Stop-Loss:
   ├─ Select "Price" tab
   ├─ Identify support: ₹3,450
   ├─ Enter SL: ₹3,445 (just below support)
   └─ Risk: ₹55 per share

3. System Validates:
   ├─ Risk per share: ₹55
   ├─ Quantity: Calculate based on 2% rule
   ├─ Suggested Quantity: 36 shares
   │   (₹2,000 risk ÷ ₹55 = 36 shares)
   └─ Total Investment: ₹126,000

4. Adjust if needed:
   ├─ If investment too high
   ├─ Reduce quantity
   └─ Or select closer SL
```

**Method 3: Indicator-Based**

```
Using ATR (Average True Range):

1. Add ATR indicator to chart
2. Note ATR value: e.g., ₹45
3. Entry: ₹2,000
4. Calculate SL:
   ├─ ATR Multiplier: 2× (conservative)
   ├─ SL Distance: ₹45 × 2 = ₹90
   ├─ Stop-Loss: ₹2,000 - ₹90 = ₹1,910
   └─ Risk: 4.5%

5. Enter in order form:
   └─ Stop-Loss: ₹1,910
```

**Validation Checks:**
```
✅ Stop-loss is set (never skip!)
✅ Stop-loss is below entry (for BUY)
✅ Stop-loss is above entry (for SELL)
✅ Risk per trade < 2%
✅ Risk-reward ratio ≥ 1.5:1
✅ Stop-loss at logical level (support/resistance)
❌ Stop-loss too tight (<1%)
❌ Stop-loss too wide (>5%)
```

---

### Q16: How do I move my stop-loss?

**Manual Stop-Loss Adjustment:**

**Step-by-Step Process:**

```
Step 1: Access Position
├─ Go to Dashboard → Open Positions
├─ Click position row to expand
└─ Details panel opens

Step 2: View Current Stop-Loss
├─ Current Entry: ₹2,000
├─ Current SL: ₹1,960 (-2%)
├─ Current Price: ₹2,050 (+2.5%)
└─ Unrealized P&L: +₹500

Step 3: Modify Stop-Loss
├─ Click "Modify SL" button
├─ New stop-loss panel opens
└─ Choose method:

Method A: Move to Breakeven
├─ Click "Move to Breakeven"
├─ New SL: ₹2,000 (entry price)
├─ Risk: 0 (locked in breakeven)
└─ Click "Update"

Method B: Trailing Stop
├─ Click "Enable Trailing"
├─ Set trail amount: ₹25 (or 1.25%)
├─ SL moves automatically
└─ Follows price up, never down

Method C: Manual Price
├─ Enter new SL price: ₹2,020
├─ New risk: 0
├─ Profit locked: +₹200
└─ Click "Update"

Step 4: Confirmation
├─ Order modified message
├─ New SL displays in position
└─ Modify recorded in log
```

**Trailing Stop-Loss Example:**

```
Scenario: RELIANCE @ ₹2,000 entry, ₹1,960 SL

Time    Price   Action              Stop-Loss
──────────────────────────────────────────────
09:15   ₹2,000  Enter BUY          ₹1,960
09:20   ₹2,025  Enable trailing    ₹1,960 (no change)
09:30   ₹2,050  Trail triggers     ₹1,985 (+₹25)
09:45   ₹2,080  Trail triggers     ₹2,015 (+₹30)
10:00   ₹2,100  Trail triggers     ₹2,035 (+₹20)
10:15   ₹2,095  Price drops         ₹2,035 (no change)
10:30   ₹2,030  SL Hit              Position Closed

Result: Locked profit = ₹30/share instead of original ₹40 risk
```

**Best Practices:**

```
Moving Stop-Loss Rules:

✅ DO:
├─ Move to breakeven after 1:1 RR
├─ Trail stops in strong trends
├─ Widen SL if consolidating
├─ Move based on support/resistance
└─ Lock in partial profits

❌ DON'T:
├─ Move SL further from entry
├─ Remove SL completely
├─ Move SL based on emotions
├─ Change SL during panic
└─ Move SL just to avoid loss
```

---

### Q17: What is a trailing stop-loss?

**Trailing Stop-Loss Explained:**

**How It Works:**

```
Concept:
└─ Stop-loss "trails" price at fixed distance
   └─ Moves UP with price (for BUY orders)
   └─ Moves DOWN with price (for SELL orders)
   └─ NEVER moves against you

Example:
Entry: ₹1,000
Trailing Distance: ₹20 (2%)

Price Movement:
₹1,000 → ₹1,020 → SL: ₹1,000 (unchanged, below threshold)
₹1,020 → ₹1,030 → SL: ₹1,010 (moved up ₹10)
₹1,030 → ₹1,050 → SL: ₹1,030 (moved up ₹20)
₹1,050 → ₹1,040 → SL: ₹1,030 (unchanged, price dropped)
₹1,040 → ₹1,029 → EXIT (SL hit at ₹1,030)

Final P&L: +₹30/share (original risk was -₹20)
```

**Configure Trailing Stop:**

```
Method 1: At Order Placement
├─ Place order as normal
├─ Check "Enable Trailing Stop"
├─ Select:
│   ├─ Fixed Amount: ₹20
│   └─ Or Percentage: 2%
└─ Trailing activates when order fills

Method 2: For Existing Position
├─ Go to position
├─ Click "Modify SL"
├─ Click "Enable Trailing"
├─ Set trail distance
└─ Click "Activate"
```

**Trailing Stop Types:**

**1. Fixed Amount Trail**
```
Entry: ₹2,000
Trail: ₹30

Price    Stop-Loss
₹2,000   ₹1,970 (initial)
₹2,050   ₹2,020 (+₹50 profit locked)
₹2,100   ₹2,070 (+₹100 profit locked)
```

**2. Percentage Trail**
```
Entry: ₹2,000
Trail: 1.5%

Price    Stop-Loss
₹2,000   ₹1,970 (2% below)
₹2,050   ₹2,019 (1.5% below)
₹2,100   ₹2,068 (1.5% below)
```

**3. ATR-Based Trail**
```
Entry: ₹2,000
ATR: ₹45
Trail: 2× ATR = ₹90

Price    Stop-Loss
₹2,000   ₹1,910 (₹90 below)
₹2,150   ₹2,060 (₹90 below)
₹2,200   ₹2,110 (₹90 below)
```

**Best For:**
- ✅ Strong trending markets
- ✅ Breakout trades
- ✅ Momentum strategies
- ✅ Multi-day swing trades
- ❌ Range-bound markets
- ❌ Volatile choppy markets

---

### Q18: Why did my stop-loss not execute at the exact price?

**Common Reasons:**

**1. Slippage (Most Common)**

```
Scenario:
Your Order: Stop-Loss at ₹1,950
Market Price Gap:
├─ Last Trade: ₹1,955
├─ Price Gaps Down: ₹1,940
└─ Your Exit: ₹1,940 (₹10 slippage)

Reason:
├─ No buyers at ₹1,950
├─ Next available price: ₹1,940
└─ This is NORMAL market behavior

Solutions:
├─ Trade liquid stocks (>₹100 avg volume)
├─ Avoid earnings announcements
├─ Use limit orders (may not fill)
└─ Accept slippage as cost of business
```

**2. Price Gaps**

```
Overnight Gap:
Day 1 Close: ₹2,000
Stop-Loss: ₹1,960
Day 2 Open: ₹1,900 (gap down)
Execution: ₹1,900 (₹60 more loss than expected)

Circuit Breaker:
├─ Stock hits lower circuit (-20%)
├─ No trading at your SL level
├─ Position stuck until circuit opens
└─ May execute at worse price next day
```

**3. Low Liquidity**

```
Small-Cap Stock:
Order: Sell 1000 shares @ ₹1,950 SL
Available Buyers:
├─ ₹1,950: 200 shares
├─ ₹1,948: 300 shares
├─ ₹1,945: 500 shares

Execution:
├─ 200 shares @ ₹1,950
├─ 300 shares @ ₹1,948
├─ 500 shares @ ₹1,945
└─ Average: ₹1,947 (₹3 slippage)
```

**How to Minimize Slippage:**

```
✅ Trade liquid stocks:
├─ RELIANCE
├─ TCS
├─ INFY
├─ HDFC BANK
└─ ICICI BANK

✅ Avoid:
├─ Small-cap stocks
├─ Pre/post market hours
├─ Low volume periods
├─ News/earnings times

✅ Use limit orders:
├─ Guarantees price
└─ But may not fill
```

---

## 💰 Risk & Money Management FAQ {#risk-faq}

### Q19: What does "2% risk per trade" mean?

**Complete Explanation:**

**Definition:**
```
2% Risk Rule:
└─ Maximum loss on single trade = 2% of total capital

Example:
Capital: ₹100,000
2% Risk: ₹2,000
```

**Calculation:**

```
Scenario 1: RELIANCE Trade
────────────────────────────
Total Capital: ₹100,000
Max Risk per Trade: ₹2,000 (2%)

Entry Price: ₹2,000
Stop-Loss: ₹1,960
Risk per Share: ₹40

Position Size Calculation:
├─ Max Risk: ₹2,000
├─ Risk per Share: ₹40
└─ Position Size: ₹2,000 ÷ ₹40 = 50 shares

Trade Setup:
├─ Buy: 50 shares @ ₹2,000
├─ Total Investment: ₹100,000
├─ Stop-Loss: ₹1,960
└─ Max Loss if SL hit: ₹2,000 (2% of capital)
```

**Why 2%?**

```
Survival Math:

With 2% risk per trade:
├─ 10 consecutive losses = -20% drawdown
├─ Still have ₹80,000 capital
├─ Possible to recover
└─ Can continue trading

With 10% risk per trade:
├─ 5 consecutive losses = -50% drawdown
├─ Only ₹50,000 left
├─ Need 100% gain to break even
└─ Very difficult to recover

Professional Traders:
├─ Beginner: 1-2% risk
├─ Intermediate: 2-3% risk
├─ Advanced: 3-5% risk (maximum)
└─ Never exceed 5%
```

**Real Example:**

```
Capital: ₹100,000
Risk: 2% = ₹2,000 per trade
Max Positions: 3

Scenario: 3 Active Trades
────────────────────────────
Trade 1: RELIANCE
├─ Entry: ₹2,000
├─ SL: ₹1,960
├─ Quantity: 50 shares
└─ Risk: ₹2,000

Trade 2: TCS
├─ Entry: ₹3,500
├─ SL: ₹3,430
├─ Quantity: 28 shares
└─ Risk: ₹1,960

Trade 3: INFY
├─ Entry: ₹1,800
├─ SL: ₹1,765
├─ Quantity: 57 shares
└─ Risk: ₹1,995

Total Risk Exposure:
├─ Combined Risk: ₹5,955
├─ % of Capital: 5.955%
└─ Max 3 trades × 2% = 6% total risk
```

---

### Q20: How many positions should I have open simultaneously?

**Position Limits by Capital:**

```
Capital Range          Max Positions
────────────────────────────────────────
₹10,000 - ₹25,000     1-2 positions
₹25,000 - ₹50,000     2-3 positions
₹50,000 - ₹100,000    3-4 positions
₹100,000 - ₹500,000   4-6 positions
₹500,000+             6-10 positions
```

**Reasoning:**

```
Why Not More Positions?

Risk Concentration:
├─ 10 positions × 2% each = 20% total risk
├─ Market crash could hit all positions
├─ Potential 15-20% drawdown
└─ Too risky for most traders

Monitoring Difficulty:
├─ Each position needs attention
├─ 5 positions = manageable
├─ 10+ positions = hard to monitor
└─ Quality > Quantity

Capital Efficiency:
├─ Small accounts spread thin
├─ Position sizes too small
├─ Commission eats profits
└─ Better to focus on fewer trades
```

**Recommended Setup:**

```
Conservative (Beginner):
├─ Max Positions: 3
├─ Risk per Trade: 1.5%
└─ Total Risk: 4.5%

Moderate (Intermediate):
├─ Max Positions: 5
├─ Risk per Trade: 2%
└─ Total Risk: 10%

Aggressive (Advanced):
├─ Max Positions: 8
├─ Risk per Trade: 2.5%
└─ Total Risk: 20%
```

**Diversification Rules:**

```
✅ DO:
├─ Spread across sectors
├─ Mix of strategies
├─ Different timeframes
└─ Uncorrelated symbols

Example Portfolio:
1. RELIANCE (Energy) - Swing trade
2. TCS (IT) - Trend following
3. HDFC BANK (Finance) - Breakout
4. INFY (IT) - Mean reversion
5. ICICI BANK (Finance) - Scalp

❌ DON'T:
├─ All positions in same sector
├─ All using same strategy
├─ All in small-cap stocks
└─ All highly correlated

Bad Example:
1. TCS (IT)
2. INFY (IT)
3. WIPRO (IT)
4. HCL TECH (IT)
└─ All move together!
```

---

## 🔧 Technical Issues FAQ {#technical-faq}

### Q21: Dashboard won't start - "Port already in use"

**Problem:**
```
python run_dashboard.py

Error: OSError: [Errno 48] Address already in use
Port 8050 is already allocated
```

**Solutions:**

**Option 1: Kill existing process**

```bash
# Find process using port 8050
lsof -i :8050

# Output:
# COMMAND   PID   USER
# python    1234  youruser

# Kill it
kill -9 1234

# Try again
python run_dashboard.py
```

**Option 2: Use different port**

```bash
# Start on port 8051
python run_dashboard.py --port 8051

# Open browser
http://localhost:8051
```

**Option 3: Find and kill all Python processes**

```bash
# List all Python processes
ps aux | grep python

# Kill all (careful!)
pkill -f python

# Or kill specific
kill -9 <PID>
```

---

### Q22: "Module not found" errors

**Problem:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solutions:**

**Check 1: Virtual environment activated?**

```bash
# Check if venv active
which python
# Should show: /path/to/scalping-bot/venv/bin/python

# If not, activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

**Check 2: Dependencies installed?**

```bash
# Install all dependencies
pip install -r requirements.txt

# Check installed packages
pip list | grep flask

# Should show:
# Flask    2.3.0
```

**Check 3: Correct Python version?**

```bash
# Check version
python --version
# Need: 3.8+

# If wrong version
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Q23: Database connection failed

**Problem:**
```
Error: could not connect to server: Connection refused
Is the server running on host "localhost" and accepting TCP/IP connections on port 5432?
```

**Solutions:**

**Check 1: PostgreSQL running?**

```bash
# Check status
# macOS
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql

# If not running, start it
brew services start postgresql       # macOS
sudo systemctl start postgresql      # Linux
```

**Check 2: Database exists?**

```bash
# List databases
psql -U postgres -l

# If scalping_bot not in list, create it
psql -U postgres -c "CREATE DATABASE scalping_bot;"
```

**Check 3: Connection URL correct?**

```bash
# Check current URL
echo $DATABASE_URL

# Should be:
# postgresql://username:password@localhost:5432/scalping_bot

# If wrong, set it
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/scalping_bot"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/scalping_bot"' >> ~/.bashrc
```

**Check 4: Credentials correct?**

```bash
# Test connection
psql -U postgres -d scalping_bot

# If password wrong
psql -U postgres
ALTER USER postgres PASSWORD 'newpassword';
\q

# Update DATABASE_URL with new password
```

---

## 🚨 Emergency Situations FAQ {#emergency-faq}

### Q24: Emergency Stop - When to use it?

**Use Emergency Stop When:**

```
Critical Situations:
├─ ⚠️ Market crash or extreme volatility
├─ ⚠️ Bot behaving unexpectedly
├─ ⚠️ Large unexpected losses
├─ ⚠️ Broker API errors
├─ ⚠️ Need to stop immediately
└─ ⚠️ Technical issues detected
```

**How to Execute:**

```
Step 1: Click Emergency Stop Button
├─ Location: Top-right corner (red button)
├─ Icon: 🛑 or ⚠️
└─ Click once

Step 2: Confirm Action
├─ Warning popup appears
├─ Message: "This will close ALL positions and stop the bot"
├─ Button: "Yes, Emergency Stop"
└─ Click to confirm

Step 3: System Actions (Automatic)
├─ [1-2 sec] Cancel all pending orders
├─ [2-3 sec] Close all positions at market price
├─ [3-4 sec] Stop bot execution
├─ [4-5 sec] Send alert notifications
└─ [Done] Display summary

Step 4: Review Results
├─ Number of positions closed
├─ Total P&L (realized)
├─ Emergency stop timestamp
└─ Positions log
```

**What Happens:**

```
Execution Sequence:
01. Log emergency stop trigger
02. Cancel pending orders (ALL)
03. Get current positions
04. For each position:
    ├─ Calculate current P&L
    ├─ Place market exit order
    ├─ Wait for confirmation
    └─ Record trade
05. Stop strategy executor
06. Update bot status: STOPPED
07. Send alerts (Telegram/Email)
08. Generate emergency report
```

**After Emergency Stop:**

```
1. Review Logs
   ├─ Go to History → Logs
   ├─ Filter: Emergency Stop
   └─ Analyze what happened

2. Check Positions
   ├─ All should be closed
   ├─ Verify with broker platform
   └─ Check P&L

3. Identify Cause
   ├─ Market event?
   ├─ Technical issue?
   ├─ Strategy problem?
   └─ Fix before restarting

4. Don't Restart Immediately
   ├─ Wait 30+ minutes
   ├─ Ensure issue resolved
   ├─ Review risk parameters
   └─ Start in paper mode first
```

---

### Q25: What if bot won't stop?

**Escalation Steps:**

**Level 1: UI Emergency Stop (Try First)**

```bash
1. Click Emergency Stop button
2. Wait 10 seconds
3. Refresh page
4. Check bot status
```

**Level 2: Kill Dashboard Process**

```bash
# Find Python process
ps aux | grep run_dashboard

# Kill it
kill -9 <PID>

# Or kill all Python
pkill -f python
```

**Level 3: Manual Position Closure**

```bash
1. Login to broker platform (Zerodha/Angel)
2. Go to Positions
3. Click "Exit All Positions"
4. Confirm
5. All positions close at market price
```

**Level 4: Cancel Orders Manually**

```bash
1. In broker platform
2. Go to Orders
3. Select "Pending Orders"
4. Click "Cancel All"
5. Confirm cancellation
```

**Level 5: Contact Broker**

```bash
Zerodha: 080-4040-2020
Angel One: 022-3926-9999
Kotak: 1800-102-4500

Say: "I need to close all positions immediately"
```

---

## 📖 Complete User Journey {#user-journey}

**From Installation to Profitable Trading**

### Phase 1: Setup (Day 1)

```
Hour 1: Installation
├─ Install Python, PostgreSQL
├─ Clone repository
├─ Create virtual environment
├─ Install dependencies
└─ ✅ Verify installation

Hour 2: Configuration
├─ Setup database
├─ Configure broker API
├─ Authenticate Zerodha
├─ Verify connection
└─ ✅ Dashboard accessible

Hour 3: Learn Interface
├─ Explore dashboard
├─ Navigate sections
├─ Try demo features
├─ Read documentation
└─ ✅ Comfortable with UI
```

### Phase 2: Strategy Development (Days 2-7)

```
Day 2-3: Learn Strategies
├─ Study EMA Crossover
├─ Study RSI Strategy
├─ Study Breakout Strategy
├─ Understand parameters
└─ ✅ Know how they work

Day 4-5: Backtesting
├─ Backtest EMA (6 months)
├─ Backtest RSI (6 months)
├─ Backtest Breakout (6 months)
├─ Compare results
├─ Select best strategy
└─ ✅ Strategy validated

Day 6-7: Optimization
├─ Test different parameters
├─ Run multiple backtests
├─ Find optimal settings
├─ Document findings
└─ ✅ Strategy optimized
```

### Phase 3: Paper Trading (Days 8-25)

```
Week 2: Initial Paper Trading
├─ Deploy strategy (paper mode)
├─ Monitor daily
├─ Track 20+ trades
├─ Review performance
└─ ✅ System working

Week 3: Refinement
├─ Identify issues
├─ Adjust parameters
├─ Test modifications
├─ Continue monitoring
└─ ✅ Performance improving

Week 4: Validation
├─ Achieve 50%+ win rate
├─ Profit factor >1.5
├─ Max drawdown <10%
├─ Consistent results
└─ ✅ Ready for live trading
```

### Phase 4: Live Trading (Month 2+)

```
Week 5: Small Start
├─ Deploy with ₹10,000
├─ Max 1-2 positions
├─ Monitor every trade
├─ Verify executions
└─ ✅ Real money profitable

Week 6-8: Scale Up
├─ Increase to ₹25,000
├─ Max 2-3 positions
├─ Continue monitoring
├─ Build confidence
└─ ✅ Consistent profits

Month 3+: Full Scale
├─ Deploy full capital
├─ Max 3-5 positions
├─ Regular monitoring
├─ Ongoing optimization
└─ ✅ Sustained profitability
```

---

## 🎬 Taking Your First Trade {#first-trade-flow}

**Complete Step-by-Step Guide**

### Prerequisites

```
Before You Start:
☑ Dashboard running
☑ Broker authenticated
☑ Account balance sufficient (₹10,000+)
☑ Paper trading mode (for first time)
☑ Chart with indicator loaded
☑ Strategy understood
```

### Step-by-Step Trade Execution

**Step 1: Identify Opportunity**

```
On Chart Page:
1. Select symbol: RELIANCE
2. Timeframe: 5 minutes
3. Add indicators:
   ├─ EMA 9 (fast)
   └─ EMA 21 (slow)

4. Wait for signal:
   ├─ Watch for EMA crossover
   ├─ EMA 9 crosses above EMA 21
   └─ ✅ Bullish signal confirmed

5. Verify conditions:
   ├─ Volume above average? ✅
   ├─ Price above VWAP? ✅
   ├─ No major resistance nearby? ✅
   └─ All conditions met!
```

**Step 2: Open Trade Panel**

```
Click "New Trade" button
├─ Location: Top-right corner
├─ Or press: Ctrl + N
└─ Trade panel slides in from right
```

**Step 3: Enter Trade Details**

```
Symbol Section:
├─ Search: Type "RELIANCE"
├─ Select: RELIANCE from dropdown
├─ Current Price: ₹2,000 (displays)
└─ Exchange: NSE (auto-selected)

Direction Section:
├─ Click "BUY" button (green)
├─ Trade Type: INTRADAY (MIS)
└─ Order Type: MARKET (for quick execution)

Quantity Section:
├─ Method: Select "Risk-Based"
├─ Capital: ₹100,000
├─ Risk: 2% = ₹2,000
└─ System calculates quantity
```

**Step 4: Set Stop-Loss**

```
Stop-Loss Section:
├─ Required: YES (cannot skip)
├─ Method: Select "Percentage"
├─ Enter: 2%
├─ Calculated SL: ₹1,960
└─ Risk per share: ₹40

Position Size Auto-Calculated:
├─ Max Risk: ₹2,000
├─ Risk per Share: ₹40
├─ Quantity: 50 shares
└─ Total Investment: ₹100,000
```

**Step 5: Set Target**

```
Target Section:
├─ Method: Select "Risk-Reward"
├─ Ratio: 2:1 (recommended)
├─ Calculated Target: ₹2,080
└─ Potential Profit: ₹4,000

Risk-Reward Display:
├─ Risk: ₹2,000 (₹40 × 50)
├─ Reward: ₹4,000 (₹80 × 50)
├─ Ratio: 2:1 ✅
└─ Status: GOOD
```

**Step 6: Review Order**

```
Order Summary Panel:
──────────────────────────
Symbol: RELIANCE
Direction: BUY
Quantity: 50 shares
Order Type: MARKET

Entry: ₹2,000 (approx)
Stop-Loss: ₹1,960
Target: ₹2,080

Investment: ₹100,000
Max Loss: ₹2,000 (2%)
Max Profit: ₹4,000 (4%)
Risk-Reward: 2:1 ✅

Validations:
✅ Sufficient balance
✅ Risk within limits
✅ Stop-loss set
✅ Max positions OK
✅ Risk-reward acceptable
──────────────────────────
```

**Step 7: Place Order**

```
Final Confirmation:
1. Review all details one last time
2. Check mode: PAPER TRADING ✅
3. Click "Place Order" button (green)
4. Confirmation dialog appears:

   ┌─────────────────────────────┐
   │  Confirm Order              │
   ├─────────────────────────────┤
   │  BUY 50 RELIANCE @ ₹2,000   │
   │  Stop-Loss: ₹1,960          │
   │  Target: ₹2,080             │
   │                             │
   │  [Cancel] [Confirm]         │
   └─────────────────────────────┘

5. Click "Confirm"
6. Order submitted to broker
```

**Step 8: Order Confirmation**

```
Success Message:
┌──────────────────────────┐
│  ✅ Order Placed         │
├──────────────────────────┤
│  Order ID: 240125001     │
│  Status: COMPLETE        │
│  Avg Price: ₹2,001       │
│  Qty Filled: 50          │
│                          │
│  [View Position]         │
└──────────────────────────┘

What Happens Next:
├─ Position appears in "Open Positions"
├─ P&L tracking starts
├─ Stop-loss order placed
├─ Target order placed (optional)
└─ Real-time monitoring active
```

**Step 9: Monitor Position**

```
Position Dashboard:
┌────────────────────────────────────────┐
│ RELIANCE               🟢 +₹50 (+0.5%) │
├────────────────────────────────────────┤
│ Entry: ₹2,001 | Current: ₹2,011        │
│ Qty: 50 | Investment: ₹100,050         │
│                                        │
│ Stop-Loss: ₹1,960 ⚠️ 2.5% away        │
│ Target: ₹2,080 🎯 3.4% away            │
│                                        │
│ Time in Trade: 5 minutes               │
│ High: ₹2,015 | Low: ₹1,998             │
│                                        │
│ [Modify SL] [Close Position]           │
└────────────────────────────────────────┘
```

**Step 10: Exit Strategy**

```
Three Exit Scenarios:

Scenario A: Target Hit ✅
├─ Price reaches ₹2,080
├─ Target order executes
├─ Position closes automatically
├─ Profit: ₹3,950 (₹4,000 - ₹50 commission)
└─ Result: +3.95% gain

Scenario B: Stop-Loss Hit ❌
├─ Price drops to ₹1,960
├─ Stop-loss order executes
├─ Position closes automatically
├─ Loss: ₹2,050 (₹2,000 + ₹50 commission)
└─ Result: -2.05% loss

Scenario C: Manual Exit 🔄
├─ You decide to exit
├─ Click "Close Position"
├─ Exit at current market price
├─ P&L calculated
└─ Position removed from dashboard
```

---

## 📊 Adding Indicators to Charts {#indicators-flow}

**Complete Guide to Chart Indicators**

### Step 1: Access Chart

```
Navigate to Chart:
├─ Method 1: Click "Charts" in menu
├─ Method 2: Click symbol name in positions
└─ Method 3: Press Ctrl + C (shortcut)

Chart Loads:
├─ Default view: Candlestick
├─ Default timeframe: 5 minutes
├─ Default indicators: None
└─ Ready to customize
```

### Step 2: Open Indicators Panel

```
Click "Indicators" Button:
├─ Location: Top-left of chart
├─ Icon: 📊 or "Indicators"
├─ Shortcut: Press 'I' key
└─ Panel slides from left

Indicators Panel Layout:
┌─────────────────────────┐
│ 🔍 Search Indicators    │
├─────────────────────────┤
│ 📈 Trend                │
│  ├─ EMA                 │
│  ├─ SMA                 │
│  └─ MACD                │
│                         │
│ 📊 Momentum             │
│  ├─ RSI                 │
│  ├─ Stochastic          │
│  └─ CCI                 │
│                         │
│ 📉 Volatility           │
│  ├─ Bollinger Bands     │
│  ├─ ATR                 │
│  └─ Keltner Channels    │
│                         │
│ 📦 Volume               │
│  ├─ Volume              │
│  ├─ OBV                 │
│  └─ VWAP                │
└─────────────────────────┘
```

### Step 3: Add First Indicator (EMA Example)

```
Select EMA:
1. Click "Trend" category
2. Click "EMA" (Exponential Moving Average)
3. Configuration panel opens:

┌─────────────────────────────┐
│ EMA Configuration           │
├─────────────────────────────┤
│ Period: [9]                 │
│ Source: [Close] ▼           │
│ Offset: [0]                 │
│                             │
│ Style:                      │
│ ├─ Color: [🔵 Blue]         │
│ ├─ Width: [2] ━━━━          │
│ └─ Style: [Solid] ▼         │
│                             │
│ [Cancel] [Apply]            │
└─────────────────────────────┘

4. Keep default Period: 9
5. Click "Apply"
6. EMA 9 appears on chart in blue
```

### Step 4: Add Second Indicator (EMA 21)

```
Repeat Process:
1. Click "+" or "Add Indicator"
2. Select "EMA" again
3. Configure:
   ├─ Period: 21
   ├─ Source: Close
   ├─ Color: Orange
   └─ Width: 2
4. Click "Apply"
5. EMA 21 appears on chart in orange

Chart Now Shows:
├─ Price candles (black/white)
├─ EMA 9 (blue line)
└─ EMA 21 (orange line)
```

### Step 5: Add RSI (Separate Panel)

```
Add RSI Indicator:
1. Click "Add Indicator"
2. Select "Momentum" → "RSI"
3. Configure:
   ├─ Period: 14
   ├─ Overbought: 70
   ├─ Oversold: 30
   └─ Color: Purple
4. Click "Apply"

RSI Panel Appears:
├─ Location: Below main chart
├─ Shows RSI line (0-100)
├─ Horizontal lines at 70 (overbought)
├─ Horizontal lines at 30 (oversold)
└─ Can resize by dragging border
```

### Step 6: Add Volume

```
Add Volume:
1. Click "Add Indicator"
2. Select "Volume" → "Volume"
3. Configure:
   ├─ Show MA: Yes
   ├─ MA Period: 20
   ├─ Up Color: Green
   ├─ Down Color: Red
   └─ Style: Histogram
4. Click "Apply"

Volume Panel Appears:
├─ Location: Below RSI panel
├─ Green bars: Up volume
├─ Red bars: Down volume
├─ Orange line: 20-period MA
└─ Adjustable height
```

### Step 7: Customize Indicator Settings

```
Edit Existing Indicator:
1. Hover over indicator name (top-left of chart)
2. Settings icon appears (⚙️)
3. Click settings icon
4. Modify parameters
5. Click "Apply" to update

Example: Change EMA 9 to EMA 8:
├─ Click EMA 9 settings
├─ Change Period: 9 → 8
├─ Click "Apply"
└─ Indicator updates immediately

Remove Indicator:
├─ Click settings icon
├─ Click "Remove" button
└─ Indicator disappears from chart
```

### Step 8: Save Layout

```
Save Your Setup:
1. Click "Layouts" dropdown (top-right)
2. Click "Save Layout"
3. Name: "EMA + RSI + Volume"
4. Click "Save"

Load Saved Layout:
├─ Click "Layouts" dropdown
├─ Select "EMA + RSI + Volume"
└─ All indicators load automatically

Share Layout:
├─ Click "Export Layout"
├─ Copy code
├─ Share with others
└─ Others click "Import Layout"
```

### Popular Indicator Combinations

**Setup 1: Trend Following**
```
Main Chart:
├─ EMA 9 (Fast)
├─ EMA 21 (Medium)
└─ EMA 50 (Slow)

Lower Panel 1:
└─ MACD (12, 26, 9)

Lower Panel 2:
└─ Volume with MA

Use Case:
└─ Identify trend direction and momentum
```

**Setup 2: Mean Reversion**
```
Main Chart:
├─ Bollinger Bands (20, 2)
└─ SMA 200

Lower Panel 1:
└─ RSI (14)

Lower Panel 2:
└─ Stochastic (14, 3, 3)

Use Case:
└─ Find overbought/oversold conditions
```

**Setup 3: Scalping**
```
Main Chart:
├─ VWAP
├─ EMA 5
└─ EMA 13

Lower Panel:
└─ Volume

Use Case:
└─ Quick trades around VWAP
```

**Setup 4: Breakout Trading**
```
Main Chart:
├─ Donchian Channels (20)
└─ SMA 50

Lower Panel 1:
└─ ATR (14) - Volatility

Lower Panel 2:
└─ Volume

Use Case:
└─ Identify breakouts with volatility confirmation
```

---

## 🛡️ Setting Stop-Loss on Chart {#stop-loss-flow}

**Visual Stop-Loss Management**

### Method 1: Drag and Drop (Interactive)

```
After Entering Trade:
1. Position appears on chart
2. Entry line drawn (blue)
3. Stop-loss line drawn (red)
4. Target line drawn (green)

Interactive Lines:
┌─────────────────────────────┐
│                             │
│         ━━━━━━━━━━━  Green   Target ₹2,080
│                             │
│     ▲ Entry Point           │
│     ━━━━━━━━━━━  Blue    Entry ₹2,000
│                             │
│         ━━━━━━━━━━━  Red     Stop-Loss ₹1,960
│                             │
└─────────────────────────────┘

To Adjust Stop-Loss:
├─ 1. Hover over red line
├─ 2. Cursor changes to ↕️
├─ 3. Click and drag line
├─ 4. Release at desired price
├─ 5. Confirmation popup appears
└─ 6. Click "Update" to confirm

New SL updates:
├─ Position table
├─ Risk calculation
├─ Broker order
└─ All displays synchronized
```

### Method 2: Right-Click Menu

```
Set SL via Chart:
1. Right-click on chart at desired price
2. Menu appears:

   ┌──────────────────────┐
   │ Set Stop-Loss Here   │
   │ Set Target Here      │
   │ ├───────────────     │
   │ Draw Trendline       │
   │ Add Horizontal Line  │
   │ Properties          │
   └──────────────────────┘

3. Click "Set Stop-Loss Here"
4. Confirmation dialog:

   ┌─────────────────────────────┐
   │ Update Stop-Loss?           │
   ├─────────────────────────────┤
   │ Current SL: ₹1,960          │
   │ New SL: ₹1,980              │
   │                             │
   │ This will:                  │
   │ ✓ Reduce risk               │
   │ ✓ Lock in ₹10/share profit  │
   │ ✓ Update broker order       │
   │                             │
   │ [Cancel] [Update]           │
   └─────────────────────────────┘

5. Click "Update"
6. Stop-loss line moves to new price
7. Order modified at broker
```

### Method 3: Support/Resistance Based

```
Using Chart Levels:
1. Identify support level
2. Click "Draw Horizontal Line" tool
3. Draw line at support (e.g., ₹1,955)
4. Right-click the line
5. Select "Set as Stop-Loss"
6. Confirmation appears
7. SL set just below support (₹1,950)

Smart SL Placement:
Entry: ₹2,000
Support: ₹1,955
SL: ₹1,950 (₹5 below support)

Reasoning:
├─ Allows for natural price movement
├─ Protects if support breaks
├─ Risk: ₹50/share (2.5%)
└─ Professional placement
```

---

## 🔄 Moving Stop-Loss on Chart {#moving-stop-loss-flow}

**Dynamic Stop-Loss Management**

### Scenario: Profitable Trade

```
Initial Setup:
Entry: ₹2,000
Stop-Loss: ₹1,960 (-2%)
Target: ₹2,080 (+4%)
Current Price: ₹2,040 (+2%)
Unrealized P&L: +₹2,000

Chart Display:
₹2,100  ━━━━━━━━━━━━━━  Target

₹2,040  ✱ Current Price
        │
₹2,020  │ Price rising
        │
₹2,000  ━━━━━━━━━━━━━━  Entry (your position)

₹1,960  ━━━━━━━━━━━━━━  Stop-Loss (initial)
```

### Step 1: Move to Breakeven

```
When to Move:
├─ Price +1% above entry (₹2,020)
├─ Or 1:1 risk-reward hit
└─ Reduces risk to zero

How to Move:
1. Click "Breakeven" button (chart toolbar)
   OR
2. Drag SL line to entry price (₹2,000)
   OR
3. Right-click entry line → "Move SL to Here"

Result:
Entry: ₹2,000
Stop-Loss: ₹2,000 (was ₹1,960)  ✅ Moved to breakeven
Target: ₹2,080
Current: ₹2,040

Benefits:
├─ Risk: 0 (was ₹2,000)
├─ Can't lose money now
├─ Still targeting +₹4,000 profit
└─ Trade is "free"

Chart Updates:
₹2,080  ━━━━━━━━━━━━━━  Target

₹2,040  ✱ Current

₹2,000  ━━━━━━━━━━━━━━  Entry + SL (both)
```

### Step 2: Trail Stop-Loss

```
When to Trail:
├─ Price continues higher (₹2,060)
├─ Want to lock in profit
└─ Use trailing stop

Enable Trailing:
1. Click "Trailing Stop" button
2. Set trail distance: ₹25 (or 1.25%)
3. Click "Activate"

How It Works:
Price: ₹2,060
Trail: ₹25
SL: ₹2,035

Price: ₹2,080 → SL moves to ₹2,055
Price: ₹2,100 → SL moves to ₹2,075
Price: ₹2,090 → SL stays at ₹2,075 (doesn't move down)

Chart Display:
₹2,100  ✱ Current (highest)
        │
₹2,075  ━━━━━━━━━━━━━━  SL (trailing)
        │
₹2,000  ━━━━━━━━━━━━━━  Entry

Profit Locked: ₹75/share (₹3,750 total)
```

### Step 3: Partial Exit Strategy

```
Strategy: Exit Half at Target, Trail Rest

Current Situation:
Entry: ₹2,000
Position: 50 shares
Current: ₹2,080 (target hit!)
P&L: +₹4,000

Partial Exit:
1. Target hit: ₹2,080
2. Exit 25 shares (50%)
3. Move SL to ₹2,040 on remaining 25
4. Let rest run with trailing stop

Result:
├─ Exited: 25 shares @ ₹2,080
│   └─ Profit: ₹2,000
│
└─ Remaining: 25 shares
    ├─ Entry: ₹2,000
    ├─ SL: ₹2,040 (locked +₹40/share = ₹1,000)
    └─ Trailing enabled

Chart Shows:
₹2,100
        ✱ Current
₹2,080  ━━━━━━━━━━━━━━  Partial exit (25 shares)

₹2,040  ━━━━━━━━━━━━━━  SL for remaining (25 shares)

₹2,000  ━━━━━━━━━━━━━━  Entry

Total Profit So Far: ₹2,000
Potential Additional: ₹1,000+ (trailing)
```

---

## ⚡ Quick Actions Guide {#quick-actions}

**Keyboard Shortcuts & Fast Operations**

### Essential Keyboard Shortcuts

```
Navigation:
Ctrl + D    → Dashboard/Home
Ctrl + S    → Strategies
Ctrl + C    → Charts
Ctrl + H    → History
Ctrl + ,    → Settings

Trading:
Ctrl + N    → New Trade
Ctrl + X    → Close Position
Ctrl + E    → Emergency Stop
Ctrl + P    → Pause Bot
Ctrl + R    → Resume Bot

Chart Operations:
I           → Indicators Panel
D           → Drawing Tools
F           → Fullscreen
+/-         → Zoom In/Out
←/→         → Previous/Next Timeframe

General:
Ctrl + F    → Search
Ctrl + K    → Command Palette
ESC         → Close Panel/Dialog
?           → Show Shortcuts
```

### Quick Trade Buttons

```
Dashboard Quick Actions:

┌──────────────────────────────┐
│ [Start Bot] [Stop Bot]       │
│ [Pause] [Emergency Stop]     │
│                              │
│ Per Position:                │
│ [Close] [Modify SL] [Trail]  │
│ [Breakeven] [Add Size]       │
└──────────────────────────────┘
```

### One-Click Operations

```
Common Tasks:

1. Close All Positions
   ├─ Click "Emergency Stop"
   ├─ All close at market
   └─ <5 seconds

2. Move All to Breakeven
   ├─ Select all profitable positions
   ├─ Click "Bulk Actions" → "Breakeven All"
   └─ All SL move to entry

3. Enable Trailing on All
   ├─ Select all positions
   ├─ Click "Enable Trailing"
   └─ Set one distance, applies to all

4. Quick Strategy Deploy
   ├─ Strategy List → Hover → Click "▶"
   ├─ Confirms paper mode
   └─ Deploys instantly
```

---

**END OF HELP & FAQ DOCUMENT**

---

## 📞 Still Need Help?

**Documentation:**
- USER_GUIDE.md - Complete manual (50+ pages)
- QUICKSTART.md - 5-minute setup
- SYSTEM_VERIFICATION_REPORT.md - Technical details

**Support Channels:**
- GitHub Issues: Report bugs
- Email: support@yourproject.com
- Community: Forum/Discord

**Broker Support:**
- Zerodha: 080-4040-2020
- Angel One: 022-3926-9999
- Kotak: 1800-102-4500

---

**Last Updated:** October 30, 2025
**Version:** 1.0
**Feedback:** help@xcoin.com
