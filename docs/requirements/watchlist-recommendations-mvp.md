# Watchlist & Stock Recommendations - MVP Implementation

**Version:** 1.0.0 (Refined)
**Date:** October 22, 2025
**Status:** 📋 Ready for Implementation

---

## Core Philosophy: Start Simple, Iterate Fast

**Remove:**
- ❌ Custom stock scanner (complex, low initial value)
- ❌ ML-based recommendations (premature, needs data)
- ❌ Multiple watchlist groups (over-engineered)
- ❌ User preference settings (can use defaults)
- ❌ Recommendation history tracking (not MVP)
- ❌ Multi-indicator confluence (keep it simple first)

**Keep:**
- ✅ Basic watchlist with real-time prices
- ✅ Pattern-based recommendations (leverage existing code)
- ✅ Simple UI integration
- ✅ Direct link to existing chart

---

## MVP Feature Set

### 1. Simple Watchlist
**What:** A single list of stocks with real-time prices and pattern detection

**UI Location:** Collapsible bottom panel (least intrusive)

**Features:**
- Add/remove stocks (text input, no fancy search)
- Real-time price updates (every 5 seconds)
- Show if pattern detected (simple badge)
- Click stock → loads on main chart

**That's it. No groups, no reordering, no fancy UI.**

### 2. Daily Stock Picks
**What:** Top 5 stocks with high-confidence patterns TODAY

**UI Location:** Card on dashboard homepage (below chart)

**Features:**
- Auto-generated daily (scan NIFTY 50 only)
- Shows top 5 by confidence
- Display: Symbol, Pattern, Confidence %, Entry Price
- Click → View on chart

**That's it. No filters, no customization, no history.**

---

## Simplified UI Design

### Dashboard Layout (Updated)
```
┌──────────────────────────────────────────────────────┐
│ TOPBAR (Account, Funds, Status)                      │
├──────────────────────────────────────────────────────┤
│                                                       │
│ MAIN CONTENT                                         │
│ • Chart (70%) + Pattern Overlay (30%)                │
│ • Stats Row                                          │
│                                                       │
│ TODAY'S TOP PICKS                                    │
│ ┌────────────────────────────────────────────────┐  │
│ │ 🟢 RELIANCE   Hammer      85%   Entry: ₹2,440 │  │
│ │ 🟢 TCS        Doji        78%   Entry: ₹3,240 │  │
│ │ 🟢 INFY       Engulfing   82%   Entry: ₹1,480 │  │
│ │ [View Details]                                  │  │
│ └────────────────────────────────────────────────┘  │
│                                                       │
├──────────────────────────────────────────────────────┤
│ ▲ MY WATCHLIST                             [+ Add]  │
├──────────────────────────────────────────────────────┤
│ RELIANCE  ₹2,450.30  +1.2% 🟢  🔨               [×] │
│ TCS       ₹3,245.50  -0.5% 🔴                    [×] │
│ INFY      ₹1,480.20  +2.1% 🟢  ⭐               [×] │
└──────────────────────────────────────────────────────┘
```

**Key Points:**
- Bottom panel = watchlist (collapsible)
- Top picks card = above watchlist
- Click stock → chart updates to show that stock
- No separate pages, everything on dashboard

---

## Minimal Database Schema

```sql
-- Watchlist (simplified)
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily picks cache (regenerate daily)
CREATE TABLE daily_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    pattern_name VARCHAR(50),
    confidence INTEGER,
    entry_price DECIMAL(10,2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE NOT NULL
);
```

**That's it. 2 tables.**

---

## Minimal API Endpoints

```python
# Watchlist (3 endpoints)
GET    /api/watchlist              # Get all watchlist stocks with current prices
POST   /api/watchlist/add          # Add stock to watchlist
DELETE /api/watchlist/remove       # Remove stock from watchlist

# Recommendations (1 endpoint)
GET    /api/recommendations/today  # Get today's top 5 picks
```

**That's it. 4 endpoints.**

---

## Implementation Plan (1 Week Total)

### Day 1-2: Database + Backend Logic
- [ ] Create SQLite database with 2 tables
- [ ] Write `watchlist_manager.py` (CRUD operations)
- [ ] Write `recommendation_engine.py` (scan NIFTY 50, find patterns)
- [ ] Test pattern detection on multiple stocks

### Day 3-4: API Endpoints
- [ ] Add 4 API endpoints to `app.py`
- [ ] Mock Kite API integration (use OHLC generator for now)
- [ ] Test endpoints with Postman/curl

### Day 5-6: Frontend UI
- [ ] Create collapsible watchlist panel (HTML/CSS)
- [ ] Create "Today's Top Picks" card
- [ ] JavaScript: Add/remove watchlist stocks
- [ ] JavaScript: Click stock → update chart symbol
- [ ] Wire up API calls

### Day 7: Testing & Polish
- [ ] Test add/remove watchlist
- [ ] Test top picks generation
- [ ] Test chart symbol switching
- [ ] Fix bugs, polish UI

---

## Simplified Algorithm

### Recommendation Engine (Pattern-Based Only)

```python
def generate_daily_recommendations():
    """
    Scan NIFTY 50 stocks, find high-confidence patterns
    """
    NIFTY_50 = [
        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
        'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'BAJFINANCE',
        # ... (top 50)
    ]

    recommendations = []

    for symbol in NIFTY_50:
        # Get OHLC data (mock or real)
        ohlc = fetch_ohlc(symbol, timeframe='5m', count=100)

        # Detect patterns (reuse existing code)
        patterns = detect_patterns(ohlc)

        # Filter high-confidence bullish patterns only
        for pattern in patterns:
            if pattern['confidence'] > 75 and pattern['type'] == 'bullish':
                recommendations.append({
                    'symbol': symbol,
                    'pattern': pattern['name'],
                    'confidence': pattern['confidence'],
                    'entry_price': ohlc[-1]['close'],  # Current price
                    'timestamp': datetime.now()
                })

    # Sort by confidence, return top 5
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    return recommendations[:5]
```

**That's it. Simple pattern scan, top 5 results.**

---

## Simplified Backend Structure

```
src/
├── analysis/
│   ├── candlestick_patterns.py      (existing - reuse)
│   ├── technical_indicators.py      (existing - reuse)
│   └── recommendation_engine.py     (NEW - 50 lines)
│
├── database/
│   ├── db_manager.py                (NEW - 100 lines)
│   └── watchlist_manager.py         (NEW - 80 lines)
│
├── utils/
│   └── ohlc_generator.py            (existing - reuse)
│
└── dashboard/
    ├── app.py                        (extend with 4 endpoints)
    └── templates/
        └── dashboard.html            (add watchlist + top picks UI)
```

**Total new code: ~300 lines**

---

## What We're NOT Building (Yet)

### Out of Scope for MVP:
1. ❌ **Stock Scanner** - Too complex, can add later
2. ❌ **Custom Filters** - Use defaults (NIFTY 50, confidence > 75%)
3. ❌ **User Preferences** - Everyone gets same recommendations
4. ❌ **Watchlist Groups** - Single flat list only
5. ❌ **Recommendation History** - No tracking, just today's picks
6. ❌ **Performance Tracking** - Can add after we have data
7. ❌ **Alerts/Notifications** - Not MVP, manual checking only
8. ❌ **ML Models** - No data yet, stick to rule-based
9. ❌ **Multi-Indicator Confluence** - Pattern-based only
10. ❌ **Real Kite API** - Use mock data first

### Can Be Added Later (v2.0):
- Advanced scanner with custom criteria
- Personalization and filters
- Recommendation history and performance tracking
- Push notifications for watchlist patterns
- More sophisticated algorithms
- Real Zerodha API integration

---

## Success Criteria for MVP

### Must Have:
- ✅ Add 5 stocks to watchlist
- ✅ See real-time prices (or at least refresh on page load)
- ✅ Remove stocks from watchlist
- ✅ See today's top 5 pattern-based picks
- ✅ Click stock → chart updates to that symbol
- ✅ Pattern badge shows on watchlist if detected

### Nice to Have:
- Auto-refresh watchlist prices (every 5 seconds)
- Smooth animations
- Mobile responsive

### Out of Scope:
- Everything else mentioned above

---

## Risk Mitigation (MVP)

### Technical Risks:
1. **Pattern Detection Slow** → Limit to NIFTY 50 only, cache results
2. **API Rate Limits** → Use mock data for MVP, add Kite later
3. **Database Performance** → SQLite is fine for 50 stocks
4. **UI Performance** → Watchlist limited to 20 stocks max

### Product Risks:
1. **False Signals** → Clear disclaimer: "Educational only, not advice"
2. **User Confusion** → Simple UI, clear labels, tooltips
3. **Low Adoption** → Show top picks prominently, easy to try

---

## Development Checklist

### Backend (Day 1-4):
- [ ] Create database schema (2 tables)
- [ ] Write `db_manager.py` (init DB, basic queries)
- [ ] Write `watchlist_manager.py` (add/remove/get)
- [ ] Write `recommendation_engine.py` (generate daily picks)
- [ ] Add 4 API endpoints to `app.py`
- [ ] Test with curl/Postman

### Frontend (Day 5-6):
- [ ] Design watchlist panel (collapsible bottom)
- [ ] Design top picks card (above watchlist)
- [ ] JavaScript: Add/remove watchlist
- [ ] JavaScript: Update chart on click
- [ ] JavaScript: Fetch and display top picks
- [ ] CSS: Polish and responsive

### Integration (Day 7):
- [ ] Wire up all API calls
- [ ] Test end-to-end flow
- [ ] Fix bugs
- [ ] Add disclaimers and tooltips
- [ ] Deploy and test in browser

---

## MVP Code Estimate

### New Files:
| File | Lines | Purpose |
|------|-------|---------|
| `src/database/db_manager.py` | 100 | Database connection, schema creation |
| `src/database/watchlist_manager.py` | 80 | Watchlist CRUD operations |
| `src/analysis/recommendation_engine.py` | 120 | Generate daily picks |
| `src/dashboard/app.py` (additions) | 100 | 4 new API endpoints |
| `templates/dashboard.html` (additions) | 200 | Watchlist panel + top picks card |

**Total: ~600 lines of code**

### Modified Files:
- `src/dashboard/app.py` - Add 4 endpoints
- `src/dashboard/templates/dashboard.html` - Add UI components

---

## Next Steps

### Immediate (Today):
1. ✅ Review this MVP document
2. Create todo list in TodoWrite
3. Set up database schema
4. Start backend implementation

### This Week:
1. Build backend (Day 1-4)
2. Build frontend (Day 5-6)
3. Test and polish (Day 7)

### Next Week:
1. User testing
2. Bug fixes
3. Plan v2.0 features based on feedback

---

## Questions Resolved

1. **Watchlist per-user or global?** → Global for MVP (single user)
2. **How many stocks?** → NIFTY 50 only (50 stocks)
3. **Push or pull recommendations?** → Pull only (user checks dashboard)
4. **Timeframes?** → Intraday only (5-minute candles)
5. **ML in v1.0?** → No, pattern-based only

---

## Why This MVP Works

### Advantages:
1. **Fast to Build** → 1 week vs 6 weeks
2. **Leverage Existing Code** → Reuse pattern detection
3. **Low Risk** → No complex features to fail
4. **Easy to Test** → Simple workflows
5. **Room to Grow** → Can expand based on real usage
6. **Immediate Value** → Users get stock ideas TODAY

### What Users Get:
- Daily pattern-based stock picks (5 stocks)
- Personal watchlist with live prices
- One-click chart viewing
- Pattern detection on watchlist

### What We Learn:
- Do users actually use recommendations?
- Which patterns perform best?
- What features do they ask for?
- Is pattern-based approach valuable?

**Then we build v2.0 based on real data.**

---

**Document Status:** ✅ Ready for Implementation
**Timeline:** 1 week (7 days)
**Estimated Effort:** 600 lines of code
**Next Step:** Create database schema and start backend

