# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.0] - 2025-10-22

### Added ✨
- **Real-Time Candlestick Chart**
  - TradingView Lightweight Charts integration
  - 100 OHLC candles (5-minute timeframe)
  - Green/Red color-coded candlesticks
  - Interactive crosshair and tooltips
  - Responsive chart sizing

- **Pattern Overlay System**
  - Compact sidebar panel (320px)
  - Real-time pattern detection
  - Pattern markers on chart candles
  - Visual indicators (🟢 bullish, 🔴 bearish, 🟡 indecision)
  - Confidence scoring (0-100%)

- **Pattern Recognition Engine**
  - 50+ candlestick patterns (hammer, doji, engulfing, etc.)
  - 40+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
  - Pattern confidence scores
  - Pattern type classification

- **New API Endpoints**
  - `GET /api/chart/ohlc` - Candlestick data
  - `POST /api/chart/patterns-sync` - Pattern synchronization
  - `GET /api/patterns/all` - Complete pattern data
  - `GET /api/patterns/candlestick` - Candlestick patterns only
  - `GET /api/patterns/indicators` - Indicator signals only

- **OHLC Data Generator**
  - Realistic candlestick generation
  - Configurable volatility
  - Trend simulation (bullish/bearish/sideways)
  - Multiple timeframes (1m, 5m, 15m, 1h, 1d)

### Changed 🔄
- **Dashboard Layout**
  - Redesigned from full-width pattern widget to 70/30 split
  - Chart (70%) + Pattern Overlay (30%)
  - Improved mobile responsive layout
  - Reduced spacing (50% more compact)

- **Pattern Display**
  - Changed from full cards to compact single-line format
  - Added emoji icons for pattern types
  - Simplified indicator chips

- **UI Styling**
  - Enhanced glassmorphism effects
  - Improved dark theme consistency
  - Better color-coding for signals

### Fixed 🐛
- Mobile hamburger menu toggle
- Sidebar overlay z-index issues
- Chart responsiveness on window resize
- Pattern marker positioning

---

## [v1.0.0] - 2025-10-20

### Added ✨
- **Initial Dashboard Release**
  - Ultra-compact design (v2.1 tokens)
  - Real-time monitoring
  - Stats row (Daily P&L, Win Rate, Trades)
  - Performance overview chart
  - Current positions display
  - Recent trades log
  - Live system logs

- **Bot Controls**
  - Start/Stop/Pause buttons
  - Emergency stop functionality
  - Mode selection (Paper/Live trading)
  - Status indicators

- **Account Integration**
  - Zerodha API authentication setup
  - Account selector in topbar
  - Funds display
  - Connection status

- **Dashboard Pages** (HTML templates)
  - Main Dashboard (`/`)
  - Accounts (`/accounts`)
  - Strategies (`/strategies`)
  - Analytics (`/analytics`)
  - Notifications (`/notifications`)
  - Settings (`/settings`)
  - Help (`/help`)
  - Implementation Log (`/implementation-log`)

- **Configuration Management**
  - YAML-based config
  - Environment variables support
  - Risk management parameters
  - Trading hours configuration

- **Logging System**
  - JSON & text log formats
  - Structured logging
  - Log rotation
  - Log viewer in dashboard

- **Alert System**
  - Telegram notifications
  - Email alerts
  - In-dashboard alerts

### Technical
- **Backend**
  - Flask + Flask-CORS
  - Modular architecture
  - RESTful API design
  - Mock data endpoints

- **Frontend**
  - Chart.js for graphs
  - Lucide icons
  - Glassmorphism styling
  - Mobile-first responsive design

- **Documentation**
  - README.md
  - QUICKSTART.md
  - FAQ.md
  - DASHBOARD_GUIDE.md

---

## [v0.1.0] - 2025-10-15 (Initial Concept)

### Added
- Project initialization
- Directory structure
- Basic Flask app scaffolding
- Configuration templates

---

## Upcoming Features 🔮

### Planned for v2.1.0
- [ ] Real Zerodha Kite API integration
- [ ] Live market data via WebSocket
- [ ] Multiple timeframe buttons (1m, 5m, 15m, 1h, 1d)
- [ ] Volume overlay on candlestick chart
- [ ] Pattern click interactions (highlight on chart)

### Planned for v3.0.0
- [ ] Chart pattern detection (H&S, Double Bottom, Triangles)
- [ ] Visual pattern overlays on chart
- [ ] Drawing tools (trendlines, fibonacci)
- [ ] Pattern-based strategy templates
- [ ] Backtest pattern strategies
- [ ] Historical pattern performance tracking

---

## Legend

- ✨ **Added** - New features
- 🔄 **Changed** - Changes to existing functionality
- 🐛 **Fixed** - Bug fixes
- 🗑️ **Removed** - Removed features
- 🔒 **Security** - Security improvements
- ⚡ **Performance** - Performance improvements
- 📚 **Documentation** - Documentation updates

---

**Format Guide:**
```markdown
## [Version] - YYYY-MM-DD

### Added
- Feature description

### Changed
- Change description

### Fixed
- Bug fix description
```

---

Last Updated: October 22, 2025
