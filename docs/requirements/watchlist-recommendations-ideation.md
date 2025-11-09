# Watchlist & Stock Recommendations - Feature Ideation

**Version:** 1.0.0
**Date:** October 22, 2025
**Status:** 📋 Ideation Phase

---

## Table of Contents

1. [Overview](#overview)
2. [User Stories](#user-stories)
3. [Feature Components](#feature-components)
4. [UI/UX Design Concepts](#uiux-design-concepts)
5. [Recommendation Algorithms](#recommendation-algorithms)
6. [Data Requirements](#data-requirements)
7. [Integration Points](#integration-points)
8. [Implementation Phases](#implementation-phases)
9. [Technical Architecture](#technical-architecture)
10. [Success Metrics](#success-metrics)

---

## Overview

### Purpose
Provide users with:
1. **Personalized Watchlist** - Track favorite stocks/instruments
2. **AI-Powered Recommendations** - Suggest trading opportunities based on patterns, indicators, and user preferences
3. **Real-Time Alerts** - Notify when watchlist stocks meet entry criteria

### Value Proposition
- **Save Time:** Automated opportunity discovery across multiple stocks
- **Data-Driven:** Recommendations based on proven technical patterns
- **Personalized:** Learn from user's trading history and preferences
- **Risk-Aware:** Filter by volatility, liquidity, risk tolerance

---

## User Stories

### Watchlist Management
```
As a trader, I want to:
- Add stocks to my watchlist with one click
- Organize watchlist into custom groups (e.g., "Tech", "NIFTY 50", "Momentum Plays")
- See real-time prices and key metrics for all watchlist stocks
- Receive alerts when watchlist stocks show entry signals
- Remove or reorder stocks easily
```

### Stock Recommendations
```
As a trader, I want to:
- Receive daily stock recommendations based on technical analysis
- See WHY a stock is recommended (pattern detected, indicator signal, etc.)
- Filter recommendations by risk level, sector, market cap
- View recommendation performance history
- Follow/ignore specific recommendation strategies
```

### Discovery
```
As a trader, I want to:
- Discover trending stocks in my market (NSE, BSE)
- Find stocks with specific patterns (e.g., "show me all hammer patterns today")
- Search stocks by technical criteria (e.g., "RSI < 30 and volume spike")
- Browse top gainers/losers with pattern context
```

---

## Feature Components

### 1. Watchlist Panel

**Location:** New sidebar panel or dedicated page

**Key Elements:**
```
┌─────────────────────────────────────┐
│ MY WATCHLIST            [+ Add]     │
├─────────────────────────────────────┤
│ 📊 NIFTY 50 Stocks (12)      [▼]   │
│   RELIANCE     2,450.30  +1.2% 🟢  │
│   TCS          3,245.50  -0.5% 🔴  │
│   INFY         1,480.20  +2.1% 🟢  │
│                                      │
│ ⚡ Momentum Plays (5)         [▼]   │
│   TATAMOTORS     585.40  +3.8% 🟢  │
│   ADANIPORTS     780.10  +2.5% 🟢  │
│                                      │
│ 🎯 High Probability (8)      [▼]   │
│   HDFCBANK     1,680.50  +0.8% 🟢  │
└─────────────────────────────────────┘
```

**Features:**
- Collapsible groups
- Real-time price updates
- Color-coded performance
- Quick "Trade Now" button
- Pattern badges (e.g., 🔨 Hammer detected)

### 2. Recommendations Feed

**Location:** Dashboard homepage or dedicated "Discover" page

**Key Elements:**
```
┌─────────────────────────────────────────────────────────┐
│ RECOMMENDED FOR YOU                 [Filter] [Settings] │
├─────────────────────────────────────────────────────────┤
│ ⭐ HIGH CONFIDENCE (3)                                   │
│                                                           │
│ 🟢 RELIANCE - Strong Bullish Setup                      │
│ ├─ Entry: ₹2,440 | Target: ₹2,520 | SL: ₹2,400         │
│ ├─ Patterns: Hammer + Bullish Engulfing                 │
│ ├─ Indicators: RSI(42), MACD Bullish Cross             │
│ ├─ Confidence: 85% | Risk: Medium                       │
│ └─ [View Chart] [Add to Watchlist] [Trade]             │
│                                                           │
│ 🟢 TCS - Oversold Bounce Play                           │
│ ├─ Entry: ₹3,240 | Target: ₹3,310 | SL: ₹3,200         │
│ ├─ Patterns: Dragonfly Doji                             │
│ ├─ Indicators: RSI(28), BB Lower Band Touch            │
│ ├─ Confidence: 78% | Risk: Low                          │
│ └─ [View Chart] [Add to Watchlist] [Trade]             │
│                                                           │
│ ⚡ MODERATE CONFIDENCE (5)                     [Show All]│
│                                                           │
│ 🟡 INFY - Continuation Pattern                          │
│ ├─ Confidence: 65% | Risk: Medium                       │
│ └─ [View Details]                                        │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Tiered by confidence (High/Moderate/Low)
- Clear entry/exit/stop-loss levels
- Pattern + indicator explanation
- One-click actions
- Performance tracking per recommendation

### 3. Stock Scanner

**Location:** Dedicated "Scanner" page

**Key Elements:**
```
┌─────────────────────────────────────────────────────────┐
│ STOCK SCANNER                                           │
├─────────────────────────────────────────────────────────┤
│ Preset Scans:                                           │
│ [Hammer Patterns] [Oversold RSI] [Bollinger Squeeze]   │
│ [Volume Breakout] [MACD Cross] [Gap Up/Down]           │
│                                                           │
│ Custom Scan:                                             │
│ ┌───────────────────────────────────────────────────┐  │
│ │ RSI        < 30                           [+]     │  │
│ │ Volume     > 1.5x Avg                     [+]     │  │
│ │ Price      > 20 EMA                       [+]     │  │
│ └───────────────────────────────────────────────────┘  │
│                              [Run Scan] [Save Preset]   │
│                                                           │
│ Results (23 stocks found):                              │
│ ┌───────────────────────────────────────────────────┐  │
│ │ RELIANCE  ₹2,450  RSI: 28  Vol: 2.1x  🟢 +1.2%   │  │
│ │ TCS       ₹3,245  RSI: 29  Vol: 1.8x  🔴 -0.5%   │  │
│ │ ...                                                │  │
│ └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Pre-built scans for common patterns
- Custom scan builder (technical criteria)
- Save custom scans as presets
- Export results to watchlist
- Schedule scans (daily/hourly)

### 4. Recommendation Settings

**Location:** Settings page

**Configuration Options:**
```
┌─────────────────────────────────────────────────────────┐
│ RECOMMENDATION PREFERENCES                              │
├─────────────────────────────────────────────────────────┤
│ Trading Style:                                           │
│ ○ Scalping (< 1 hour)                                   │
│ ● Intraday (same day)                                   │
│ ○ Swing (2-5 days)                                      │
│ ○ Positional (> 1 week)                                 │
│                                                           │
│ Risk Tolerance:                                          │
│ ○ Low  ● Medium  ○ High  ○ Aggressive                   │
│                                                           │
│ Preferred Sectors: (Select multiple)                    │
│ ☑ Banking  ☑ IT  ☐ Pharma  ☑ Auto  ☐ Energy            │
│                                                           │
│ Market Cap:                                              │
│ ☑ Large Cap (> ₹20,000 Cr)                              │
│ ☑ Mid Cap (₹5,000-20,000 Cr)                            │
│ ☐ Small Cap (< ₹5,000 Cr)                               │
│                                                           │
│ Minimum Confidence: [75%] ────────○──────── 100%        │
│                                                           │
│ Pattern Preferences:                                     │
│ ☑ Candlestick Patterns                                   │
│ ☑ Indicator Signals                                      │
│ ☐ Chart Patterns (H&S, Triangles)                       │
│ ☑ Volume Analysis                                        │
│                                                           │
│ Alert Preferences:                                       │
│ ☑ Push Notifications                                     │
│ ☑ Email Alerts                                           │
│ ☑ Telegram Messages                                      │
│ Alert Frequency: [Real-time] ▼                          │
│                                                           │
│               [Save Preferences] [Reset to Default]     │
└─────────────────────────────────────────────────────────┘
```

---

## UI/UX Design Concepts

### Design Option 1: Sidebar Watchlist Panel

**Layout:**
```
┌──────────────┬────────────────────────────────────────┐
│              │ TOPBAR (Account, Funds)                │
│ SIDEBAR      ├────────────────────────────────────────┤
│ ─ Dashboard  │                                        │
│ ─ Watchlist  │   MAIN CONTENT AREA                   │
│ ─ Discover   │   (Chart + Stats)                     │
│ ─ Scanner    │                                        │
│ ─ Strategies │                                        │
│              │                                        │
│ MY WATCHLIST │                                        │
│ ┌──────────┐ │                                        │
│ │RELIANCE  │ │                                        │
│ │+1.2% 🟢  │ │                                        │
│ ├──────────┤ │                                        │
│ │TCS       │ │                                        │
│ │-0.5% 🔴  │ │                                        │
│ └──────────┘ │                                        │
└──────────────┴────────────────────────────────────────┘
```

**Pros:**
- Always visible
- Quick access
- Doesn't disrupt main chart

**Cons:**
- Limited space (max 5-8 stocks visible)

### Design Option 2: Dedicated Watchlist Page

**Layout:**
```
Full-width page with grid of watchlist cards:

┌──────────────┬──────────────┬──────────────┐
│ RELIANCE     │ TCS          │ INFY         │
│ ₹2,450  +1.2%│ ₹3,245 -0.5% │ ₹1,480 +2.1% │
│ 🔨 Hammer    │ 📊 RSI: 45   │ 🟢 Buy Signal│
│ [View] [Trade│              │              │
├──────────────┼──────────────┼──────────────┤
│ HDFCBANK     │ TATAMOTORS   │ ADANIPORTS   │
│ ...          │ ...          │ ...          │
└──────────────┴──────────────┴──────────────┘
```

**Pros:**
- More detailed information
- Better visualization
- Multiple watchlist support

**Cons:**
- Requires navigation away from main dashboard

### Design Option 3: Collapsible Bottom Panel

**Layout:**
```
Dashboard with collapsible watchlist at bottom:

┌────────────────────────────────────────────┐
│ Main Dashboard Content                     │
│ (Chart + Stats + Patterns)                 │
│                                             │
├─────────────────────────────────────────────
│ ▲ WATCHLIST (Click to expand)             │
├─────────────────────────────────────────────
│ RELIANCE +1.2%  │ TCS -0.5%  │ INFY +2.1% │
└─────────────────────────────────────────────
```

**Pros:**
- Doesn't take space when collapsed
- Expandable for details
- Visible ticker strip

**Cons:**
- Less intuitive
- Requires interaction

### Recommendation: **Hybrid Approach**

**Sidebar Mini-Watchlist + Dedicated Page:**
- Sidebar shows top 5-8 stocks (most important)
- "View All" button links to dedicated watchlist page
- Recommendations feed on dashboard homepage
- Scanner as separate tool

---

## Recommendation Algorithms

### Algorithm 1: Pattern-Based Recommendations

**Logic:**
```python
def generate_pattern_recommendations(stocks: List[str]) -> List[Recommendation]:
    """
    Recommend stocks with high-confidence candlestick patterns
    """
    recommendations = []

    for stock in stocks:
        ohlc_data = fetch_ohlc(stock, timeframe='5m', count=100)
        patterns = detect_patterns(ohlc_data)

        # Filter high-confidence bullish patterns
        high_conf_patterns = [p for p in patterns
                             if p['confidence'] > 75
                             and p['type'] == 'bullish']

        if high_conf_patterns:
            # Calculate entry/exit based on pattern
            entry_price = calculate_entry(ohlc_data, patterns)
            stop_loss = calculate_stop_loss(entry_price, risk=0.02)
            target = calculate_target(entry_price, reward=0.04)

            recommendations.append({
                'stock': stock,
                'patterns': high_conf_patterns,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'target': target,
                'confidence': max([p['confidence'] for p in patterns]),
                'reason': f"{len(high_conf_patterns)} bullish patterns detected"
            })

    return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)
```

**Strength:** Simple, explainable, based on proven patterns

### Algorithm 2: Multi-Indicator Confluence

**Logic:**
```python
def generate_confluence_recommendations(stocks: List[str]) -> List[Recommendation]:
    """
    Recommend stocks where multiple indicators agree
    """
    recommendations = []

    for stock in stocks:
        ohlc_data = fetch_ohlc(stock)
        indicators = calculate_indicators(ohlc_data)

        # Count bullish signals
        bullish_signals = 0
        reasons = []

        if indicators['rsi'] < 30:
            bullish_signals += 1
            reasons.append("RSI oversold")

        if indicators['macd_cross'] == 'bullish':
            bullish_signals += 1
            reasons.append("MACD bullish cross")

        if indicators['bb_position'] == 'lower':
            bullish_signals += 1
            reasons.append("Price at BB lower band")

        if indicators['ema_cross'] == 'golden':
            bullish_signals += 2  # Stronger signal
            reasons.append("Golden cross (EMA)")

        # Minimum 3 signals for recommendation
        if bullish_signals >= 3:
            confidence = min(bullish_signals * 15 + 40, 100)

            recommendations.append({
                'stock': stock,
                'confluence_score': bullish_signals,
                'confidence': confidence,
                'reasons': reasons,
                'indicators': indicators
            })

    return sorted(recommendations, key=lambda x: x['confluence_score'], reverse=True)
```

**Strength:** More robust, reduces false signals

### Algorithm 3: Machine Learning Score (Future Enhancement)

**Logic:**
```python
def generate_ml_recommendations(stocks: List[str], user_profile: Dict) -> List[Recommendation]:
    """
    Use ML model trained on historical patterns + user preferences
    """
    model = load_trained_model('pattern_success_predictor.pkl')
    recommendations = []

    for stock in stocks:
        features = extract_features(stock)  # OHLC, patterns, indicators, volume
        user_features = extract_user_features(user_profile)  # Win rate, preferred patterns

        combined_features = np.concatenate([features, user_features])

        # Predict probability of successful trade
        success_probability = model.predict_proba(combined_features)[0][1]

        if success_probability > 0.70:
            recommendations.append({
                'stock': stock,
                'ml_score': success_probability * 100,
                'confidence': int(success_probability * 100),
                'personalized': True
            })

    return recommendations
```

**Strength:** Learns from data, personalized, improves over time

### Recommendation Strategy: **Ensemble Approach**

Combine all three algorithms:
1. Run pattern-based algorithm (fast, explainable)
2. Run multi-indicator confluence (validation)
3. Apply ML scoring (future enhancement)
4. Rank by weighted confidence score
5. Filter by user preferences (risk, sector, etc.)

---

## Data Requirements

### Real-Time Market Data

**Source: Zerodha Kite Connect API**

**Endpoints Needed:**
```python
# 1. Get quote (real-time price)
GET https://api.kite.trade/quote
Params: instruments (e.g., "NSE:RELIANCE", "NSE:TCS")

# 2. Get historical data (OHLC)
GET https://api.kite.trade/instruments/historical/{instrument_token}/{interval}
Params: from_date, to_date, interval (minute, 5minute, day)

# 3. Get market depth
GET https://api.kite.trade/quote/ohlc
Params: instruments

# 4. Get instrument list
GET https://api.kite.trade/instruments
Returns: All tradable instruments
```

**Data Frequency:**
- Real-time quotes: Every 1 second (WebSocket)
- OHLC updates: Every 1 minute (for pattern detection)
- Watchlist refresh: Every 2 seconds
- Recommendation scan: Every 5 minutes (or on-demand)

### Static Data

**Required:**
- Instrument master list (NSE/BSE symbols)
- Sector classification
- Market cap data
- Historical volatility metrics

**Source:**
- Download from Kite API daily
- Cache in local database (SQLite or PostgreSQL)

### User Data

**Store in Database:**
```sql
-- Watchlist table
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    symbol VARCHAR(20),
    group_name VARCHAR(50),
    added_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Recommendations history
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    recommended_at TIMESTAMP,
    entry_price DECIMAL,
    target_price DECIMAL,
    stop_loss DECIMAL,
    confidence INTEGER,
    patterns TEXT,  -- JSON
    status VARCHAR(20),  -- active, hit_target, hit_sl, expired
    actual_outcome VARCHAR(20)
);

-- User preferences
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    trading_style VARCHAR(20),
    risk_tolerance VARCHAR(20),
    preferred_sectors TEXT,  -- JSON array
    min_confidence INTEGER,
    alert_enabled BOOLEAN
);
```

---

## Integration Points

### 1. Existing Dashboard Integration

**Pattern Recognition System:**
- Reuse existing `candlestick_patterns.py`
- Reuse existing `technical_indicators.py`
- Extend with recommendation scoring logic

**API Endpoints to Add:**
```python
# Watchlist endpoints
GET  /api/watchlist/all
POST /api/watchlist/add
DELETE /api/watchlist/remove/{symbol}
PUT /api/watchlist/reorder

# Recommendations endpoints
GET  /api/recommendations/daily
GET  /api/recommendations/scan
POST /api/recommendations/filter

# Scanner endpoints
GET  /api/scanner/presets
POST /api/scanner/custom
POST /api/scanner/save-preset
```

**Dashboard UI:**
- Add "Watchlist" link to sidebar
- Add "Discover" page for recommendations
- Add "Scanner" page
- Integrate watchlist mini-panel (collapsible)

### 2. Zerodha Kite API Integration

**Authentication:**
- Reuse existing OAuth2 flow
- Store access token securely

**WebSocket for Real-Time Data:**
```python
from kiteconnect import KiteTicker

def start_ticker(access_token, watchlist_symbols):
    kws = KiteTicker(api_key, access_token)

    @kws.on_ticks
    def on_ticks(ws, ticks):
        # Update watchlist prices in real-time
        update_watchlist_prices(ticks)

    @kws.on_connect
    def on_connect(ws, response):
        ws.subscribe(watchlist_symbols)
        ws.set_mode(ws.MODE_QUOTE, watchlist_symbols)

    kws.connect(threaded=True)
```

### 3. Notification System Integration

**Trigger Alerts When:**
- Watchlist stock shows entry signal
- New high-confidence recommendation
- Scanner finds matching stock

**Alert Channels:**
- Telegram bot (reuse existing)
- Email (reuse existing)
- Push notifications (browser API)

---

## Implementation Phases

### Phase 1: Basic Watchlist (Week 1)
**Goal:** Users can add/remove stocks and see prices

**Tasks:**
- [ ] Create watchlist database schema
- [ ] Build watchlist API endpoints (add/remove/get)
- [ ] Design watchlist UI (sidebar panel)
- [ ] Integrate Kite API for real-time quotes
- [ ] Display watchlist with prices
- [ ] Manual refresh + auto-refresh (every 2s)

**Deliverables:**
- Functional watchlist panel
- Real-time price updates
- Persistent storage

### Phase 2: Pattern-Based Recommendations (Week 2)
**Goal:** Generate daily stock recommendations

**Tasks:**
- [ ] Extend pattern recognition for multi-stock analysis
- [ ] Build recommendation algorithm (pattern-based)
- [ ] Create recommendations API endpoint
- [ ] Design recommendations feed UI
- [ ] Calculate entry/exit/stop-loss levels
- [ ] Display recommendations with confidence scores

**Deliverables:**
- Daily recommendation feed
- Clear entry/exit criteria
- Pattern explanations

### Phase 3: Stock Scanner (Week 3)
**Goal:** Allow users to scan stocks by criteria

**Tasks:**
- [ ] Build scan engine (technical criteria)
- [ ] Create pre-built scan presets
- [ ] Design scanner UI page
- [ ] Implement custom scan builder
- [ ] Add "save preset" functionality
- [ ] Export scan results to watchlist

**Deliverables:**
- Stock scanner tool
- 10+ pre-built scans
- Custom scan builder

### Phase 4: User Preferences & Personalization (Week 4)
**Goal:** Personalize recommendations

**Tasks:**
- [ ] Create user preferences database
- [ ] Build preferences UI (settings page)
- [ ] Implement recommendation filtering by preferences
- [ ] Add sector/market cap filters
- [ ] Implement confidence threshold slider
- [ ] Track recommendation performance

**Deliverables:**
- Personalized recommendations
- User preference settings
- Performance tracking

### Phase 5: Advanced Features (Week 5-6)
**Goal:** Enhance with alerts and analytics

**Tasks:**
- [ ] Implement watchlist alerts (entry signals)
- [ ] Add recommendation history page
- [ ] Build recommendation performance analytics
- [ ] Add multi-timeframe support
- [ ] Implement watchlist groups/folders
- [ ] Add "Trade Now" quick action buttons

**Deliverables:**
- Alert system integration
- Recommendation analytics
- Enhanced watchlist organization

### Phase 6: ML-Based Recommendations (Future)
**Goal:** Improve recommendations with machine learning

**Tasks:**
- [ ] Collect historical recommendation data
- [ ] Train ML model on successful patterns
- [ ] Integrate ML scoring into recommendations
- [ ] A/B test ML vs rule-based recommendations
- [ ] Implement user feedback loop

**Deliverables:**
- ML-powered recommendations
- Continuous learning system

---

## Technical Architecture

### Backend Components

```
src/
├── analysis/
│   ├── candlestick_patterns.py      (existing)
│   ├── technical_indicators.py      (existing)
│   ├── recommendation_engine.py     (NEW)
│   ├── stock_scanner.py             (NEW)
│   └── ml_predictor.py              (NEW - Phase 6)
│
├── data/
│   ├── kite_data_fetcher.py         (NEW)
│   ├── instrument_master.py         (NEW)
│   └── market_cache.py              (NEW)
│
├── database/
│   ├── watchlist_manager.py         (NEW)
│   ├── recommendations_manager.py   (NEW)
│   └── user_preferences.py          (NEW)
│
└── dashboard/
    ├── app.py                        (extend with new endpoints)
    └── templates/
        ├── watchlist.html            (NEW)
        ├── recommendations.html      (NEW)
        └── scanner.html              (NEW)
```

### Database Schema

```sql
-- Watchlist
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) DEFAULT 'NSE',
    group_name VARCHAR(50) DEFAULT 'Default',
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

-- Recommendations
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timeframe VARCHAR(10) DEFAULT '5m',
    entry_price DECIMAL(10,2),
    target_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    confidence INTEGER,
    patterns TEXT,  -- JSON: ["Hammer", "Bullish Engulfing"]
    indicators TEXT,  -- JSON: {"RSI": 28, "MACD": "bullish"}
    status VARCHAR(20) DEFAULT 'active',  -- active, hit_target, hit_sl, expired, ignored
    actual_entry DECIMAL(10,2),
    actual_exit DECIMAL(10,2),
    pnl DECIMAL(10,2),
    expired_at TIMESTAMP
);

-- User Preferences
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    trading_style VARCHAR(20) DEFAULT 'intraday',  -- scalping, intraday, swing, positional
    risk_tolerance VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, aggressive
    preferred_sectors TEXT,  -- JSON: ["Banking", "IT", "Auto"]
    market_cap TEXT,  -- JSON: ["Large", "Mid"]
    min_confidence INTEGER DEFAULT 75,
    alert_enabled BOOLEAN DEFAULT 1,
    alert_channels TEXT,  -- JSON: ["telegram", "email", "push"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan Presets
CREATE TABLE scan_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    criteria TEXT NOT NULL,  -- JSON: [{"indicator": "RSI", "operator": "<", "value": 30}]
    is_public BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instrument Master (cached from Kite API)
CREATE TABLE instruments (
    instrument_token INTEGER PRIMARY KEY,
    exchange VARCHAR(10),
    tradingsymbol VARCHAR(50),
    name VARCHAR(200),
    expiry DATE,
    strike DECIMAL(10,2),
    tick_size DECIMAL(10,4),
    lot_size INTEGER,
    instrument_type VARCHAR(20),
    segment VARCHAR(20),
    exchange_token INTEGER,
    sector VARCHAR(50),
    market_cap VARCHAR(20),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints Summary

```
Watchlist:
  GET    /api/watchlist/all
  POST   /api/watchlist/add
  DELETE /api/watchlist/remove/<symbol>
  PUT    /api/watchlist/reorder
  POST   /api/watchlist/create-group

Recommendations:
  GET    /api/recommendations/daily
  GET    /api/recommendations/history
  POST   /api/recommendations/filter
  POST   /api/recommendations/feedback  (mark as useful/not useful)

Scanner:
  GET    /api/scanner/presets
  POST   /api/scanner/run
  POST   /api/scanner/save-preset
  DELETE /api/scanner/preset/<id>

Preferences:
  GET    /api/preferences
  PUT    /api/preferences/update

Market Data:
  GET    /api/market/quote/<symbol>
  GET    /api/market/ohlc/<symbol>
  GET    /api/market/instruments
  WS     /ws/tickers  (WebSocket for real-time)
```

---

## Success Metrics

### User Engagement
- **Watchlist Adoption:** % of users who add stocks to watchlist
- **Watchlist Size:** Average number of stocks per user
- **Daily Active Users:** Users who check recommendations daily
- **Scanner Usage:** Number of scans run per day

### Recommendation Quality
- **Accuracy:** % of recommendations that hit target
- **Win Rate:** % of profitable recommendations
- **Average Return:** Average P&L per recommendation
- **False Positive Rate:** % of recommendations that hit stop-loss

### User Satisfaction
- **Recommendation Feedback:** Thumbs up/down ratio
- **Feature Usage:** Most used recommendation filters
- **Alert Response Rate:** % of alerts that lead to trades
- **User Retention:** Users returning to check recommendations

### Technical Performance
- **API Response Time:** < 500ms for watchlist, < 2s for scans
- **Real-Time Latency:** < 1s for price updates
- **Scan Speed:** Complete scan of 1000+ stocks in < 10s
- **Uptime:** 99.5%+ for recommendation service

---

## Risk & Challenges

### Technical Challenges
1. **Rate Limits:** Kite API has rate limits (3 req/s)
   - **Mitigation:** Batch requests, cache aggressively, use WebSocket

2. **Data Latency:** Real-time data delays
   - **Mitigation:** WebSocket connection, show "delayed by Xs" indicator

3. **Scalability:** Scanning 1000+ stocks
   - **Mitigation:** Parallel processing, incremental scans, cache results

4. **Database Size:** Historical recommendations grow large
   - **Mitigation:** Archive old data, pagination, indexing

### Business Risks
1. **False Signals:** Bad recommendations hurt user trust
   - **Mitigation:** High confidence threshold (75%+), clear disclaimers

2. **Over-Reliance:** Users blindly follow recommendations
   - **Mitigation:** Education, show reasoning, encourage user analysis

3. **Market Conditions:** Patterns fail in choppy markets
   - **Mitigation:** Market regime detection, adjust confidence scores

### Compliance & Legal
1. **SEBI Regulations:** Providing stock tips may require license
   - **Mitigation:** Clearly label as "educational", "not financial advice"

2. **Data Privacy:** User trading preferences are sensitive
   - **Mitigation:** Encrypt database, secure API, no third-party sharing

---

## Next Steps

### Immediate Actions (This Week)
1. **Review & Approve** this ideation document
2. **Prioritize Features:** Decide which phases to implement first
3. **Mockup UI:** Create visual mockups for watchlist and recommendations pages
4. **Test Kite API:** Verify rate limits and data availability
5. **Database Design:** Finalize schema and create tables

### Development Kickoff (Next Week)
1. **Phase 1 Implementation:** Build basic watchlist
2. **Set Up Database:** Create tables, seed instrument master
3. **Integrate Kite API:** Fetch real-time quotes
4. **Build Watchlist UI:** Sidebar panel + dedicated page

### Questions to Resolve
1. Should watchlist be per-user or global?
2. How many stocks should scanner support (100? 500? 1000+)?
3. Should recommendations be push-based (alerts) or pull-based (user checks)?
4. What timeframes for recommendations (intraday only, or swing too)?
5. Should ML-based recommendations be in scope for v1.0?

---

## Appendix

### Inspiration & References

**Similar Features in Trading Platforms:**
- **TradingView:** Advanced scanner, watchlist with alerts
- **Zerodha Kite:** Basic watchlist, market depth
- **Upstox Pro:** Curated watchlists, recommendation widgets
- **5paisa:** Pre-built scans, stock ideas

**Key Differentiators for Our Implementation:**
- Pattern-based recommendations (not just price alerts)
- Confidence scoring (explainable AI)
- Tight integration with bot's pattern recognition
- Personalized based on user's trading history

### Technical Libraries

**Python Libraries:**
- `kiteconnect` - Zerodha API wrapper
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `ta-lib` - Technical analysis (if available)
- `sklearn` - ML models (Phase 6)
- `websocket` - Real-time data streaming

**Frontend:**
- Existing: Chart.js, Lucide icons
- New: DataTables.js (for scanner results table)
- New: Select2 (for multi-select dropdowns)

---

**Document Status:** Ready for Review
**Next Step:** Create UI mockups and approve implementation plan
**Estimated Timeline:** 6 weeks for full implementation (Phases 1-5)

