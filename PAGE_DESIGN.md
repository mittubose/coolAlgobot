# 🎨 Scalping Bot - Page Design & Content Strategy

## 1. 📊 DASHBOARD (Home)
**Purpose:** Quick overview and bot control center

**Content:**
- Welcome header with user name
- Bot status badge (Running/Stopped/Paused)
- **Connect to Zerodha** banner (if not connected)
- Quick control panel (Start/Stop/Pause/Emergency Stop)
- **4 Key Metrics:** Daily P&L, Total P&L, Win Rate, Today's Trades
- **Performance Chart:** Equity curve (1H/1D/1W/1M)
- **2 Cards:** Current Positions + Recent Trades
- **Live Logs** viewer (System/Trades/Errors)

**Key Actions:**
- Start/Stop bot
- Emergency stop all
- Connect to broker

---

## 2. 🧠 STRATEGIES
**Purpose:** Browse, manage, and deploy trading strategies

**Content:**
- **Page Header:** "Strategy Catalog" with "Create New Strategy" button
- **Filter Tabs:** All | Active | Paused | Templates
- **Strategy Grid:** 3 columns of strategy cards

**Each Strategy Card Shows:**
- Strategy name + icon
- Status badge (Active/Paused/Draft)
- **Mini Metrics:** Win Rate, Profit Factor, Total Trades
- **Mini Equity Curve** (sparkline)
- **Config Preview:** Symbol, Timeframe, Risk%
- **Quick Actions:**
  - 🚀 Deploy (1-Click) - green button
  - 📊 Backtest - secondary button  
  - ⚙️ Configure - icon button
  - 📋 Duplicate - icon button
- Last updated timestamp

**Example Strategies to Show:**
1. EMA Cross + RSI (Active) - NIFTY 5m
2. Bollinger Bands Breakout (Paused) - BANKNIFTY 15m
3. VWAP Mean Reversion (Draft) - RELIANCE 1m

**Key Actions:**
- Deploy strategy instantly
- Run backtest
- Edit configuration
- Create new strategy

---

## 3. 📈 ANALYTICS
**Purpose:** Deep performance analysis and comparisons

**Content:**
- **Page Header:** "Analytics Dashboard"
- **Time Range Selector:** 7D | 30D | 90D | 1Y | All
- **Compare Mode Toggle:** Select up to 3 strategies

**Sections:**
1. **Cumulative P&L Chart** (large, primary)
   - Multi-line if comparing strategies
   - Hover tooltips with exact values

2. **Key Metrics Grid** (4 cards):
   - Total Return %
   - Sharpe Ratio
   - Max Drawdown
   - Average Win/Loss

3. **Strategy Comparison Table** (if compare mode):
   | Metric | Strategy 1 | Strategy 2 | Strategy 3 |
   | Total Return | +12.5% | +8.3% | -2.1% |
   | Win Rate | 58% | 62% | 45% |
   | Profit Factor | 1.87 | 2.12 | 0.91 |

4. **Trade Heatmap** (Hour × Day of Week)
   - Shows best/worst trading hours
   - Color coded (green = profit, red = loss)

5. **Monthly Performance Calendar**
   - Each day colored by P&L
   - Click to see day's trades

6. **Top/Worst Trades** (2 columns)
   - Top 10 winning trades
   - Top 10 losing trades

**Key Actions:**
- Export reports (PDF/CSV)
- Compare strategies
- Filter by date range

---

## 4. 💼 ACCOUNTS
**Purpose:** Manage broker connections and funds

**Content:**
- **Page Header:** "Accounts & Broker Connections"

**Sections:**
1. **Connection Status Card:**
   - Zerodha logo
   - Status: Connected ✓ / Not Connected ✗
   - User ID/Account info
   - "Connect" or "Disconnect" button
   - Last synced timestamp

2. **Funds Overview** (3 cards):
   - **Available Balance:** ₹100,000
   - **Used Margin:** ₹25,000
   - **P&L Today:** +₹5,250

3. **API Configuration:**
   - API Key input (masked)
   - API Secret input (masked)
   - "Update Credentials" button
   - "Test Connection" button

4. **Connection History:**
   - Table of past connections
   - Timestamp, Status, Duration

**Key Actions:**
- Connect to Zerodha (OAuth flow)
- Update API credentials
- View fund details
- Test connection

---

## 5. ⚙️ SETTINGS
**Purpose:** Configure bot behavior and parameters

**Content:**
- **Page Header:** "Settings & Configuration"
- **Tabbed Interface:**

**Tab 1: Trading Settings**
- Default timeframe (dropdown)
- Default risk per trade (slider: 0.5% - 5%)
- Max concurrent positions (number input)
- Allow weekend trading (toggle)

**Tab 2: Risk Management**
- Max daily loss limit (₹ input)
- Max position size (₹ input)
- Stop-loss type (dropdown: Fixed/ATR/Support)
- Default stop-loss % (slider)

**Tab 3: Alerts & Notifications**
- **Telegram Settings:**
  - Enable Telegram (toggle)
  - Bot token (input)
  - Chat ID (input)
- **Email Settings:**
  - Enable email (toggle)
  - Email address (input)
- **Alert Types** (checkboxes):
  - ✓ Trade executed
  - ✓ Stop-loss hit
  - ✓ Daily loss limit reached
  - ✓ Bot stopped/paused

**Tab 4: System**
- Theme (dropdown: Dark/Light)
- Logging level (dropdown: Info/Debug/Error)
- Auto-restart on error (toggle)
- Clear cache button

**Key Actions:**
- Save settings
- Reset to defaults
- Export configuration

---

## 6. 📜 HISTORY
**Purpose:** View all past trades and sessions

**Content:**
- **Page Header:** "Trade History & Sessions"
- **Filter Bar:**
  - Date range picker
  - Strategy filter (dropdown)
  - Status filter (All/Profit/Loss)
  - Search by symbol

**Sections:**
1. **Session Summary Cards** (top row):
   - Total Sessions: 47
   - Total Trades: 342
   - Win Rate: 58.2%
   - Net P&L: +₹15,240

2. **Trade Log Table:**
   | Time | Strategy | Symbol | Side | Entry | Exit | P&L | % |
   | 10:15 | EMA-RSI | NIFTY | BUY | 19,850 | 19,920 | +350 | +0.35% |
   | 11:30 | BB-Break | BANKNIFTY | SELL | 44,100 | 44,050 | +250 | +0.11% |
   
   - Sortable columns
   - Color-coded P&L
   - Pagination (50 per page)
   - Export to CSV

3. **Session History:**
   - List of trading sessions
   - Date, Duration, Trades count, Net P&L
   - Click to expand details

**Key Actions:**
- Filter trades
- Export history
- View session details

---

## 7. 🔔 NOTIFICATIONS
**Purpose:** View alerts and system messages

**Content:**
- **Page Header:** "Notifications & Alerts"
- **Filter Tabs:** All | Trades | System | Errors

**Notification Cards:**
```
┌─────────────────────────────────────┐
│ 🟢 Trade Executed                   │
│ EMA-RSI strategy bought NIFTY @...  │
│ 2 minutes ago                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🔴 Stop-Loss Hit                    │
│ Position closed at loss ₹250        │
│ 15 minutes ago                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⚠️  Daily Loss Limit Warning         │
│ 80% of daily limit reached          │
│ 1 hour ago                          │
└─────────────────────────────────────┘
```

**Features:**
- Unread count badge
- Mark as read
- Clear all
- Auto-refresh

---

## 8. ❓ HELP
**Purpose:** Documentation and support

**Content:**
- **Page Header:** "Help & Documentation"
- **Quick Links Cards:**
  - Getting Started Guide
  - Strategy Creation Tutorial
  - API Documentation
  - FAQ

**FAQ Accordion:**
```
▶ How do I connect to Zerodha?
▶ How to create a new strategy?
▶ What is paper trading mode?
▶ How to interpret backtest results?
▶ How to set stop-loss levels?
```

**Sections:**
1. **Video Tutorials** (if available)
2. **Documentation Links**
3. **Contact Support** form
4. **System Info:**
   - Version: 1.0.0
   - Last updated: Oct 18, 2025

---

## 9. 👤 PROFILE
**Purpose:** User account and preferences

**Content:**
- **Page Header:** "Profile & Preferences"

**Sections:**
1. **User Info Card:**
   - Profile picture placeholder
   - Name: Mittu Haribose
   - Email: mittu@example.com
   - Member since: Oct 2025
   - "Edit Profile" button

2. **Trading Stats:**
   - Total trading days: 47
   - Favorite strategy: EMA-RSI
   - Best trade: +₹2,500
   - Total P&L: +₹15,240

3. **Preferences:**
   - Default dashboard view (dropdown)
   - Chart theme (dropdown)
   - Timezone (dropdown)
   - Language (dropdown)

4. **Security:**
   - Change password
   - Two-factor authentication (toggle)
   - Active sessions list

**Key Actions:**
- Update profile
- Change password
- Manage sessions

---

## 🎨 Design Consistency

**All Pages Share:**
- Same sidebar navigation
- Same topbar with account/funds/status
- Glassmorphism card styling
- Ultra-compact spacing
- Mobile responsive (hamburger menu <768px)
- Same color scheme (cyan accent, dark theme)

**Page-Specific Variations:**
- Different header titles
- Different icon in header
- Unique content sections
- Page-specific action buttons
