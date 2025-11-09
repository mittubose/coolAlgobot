# Product Requirements Document (PRD)
## Daily Scalping Algorithmic Trading Software for Zerodha

**Version:** 1.0  
**Last Updated:** October 17, 2025  
**Product Owner:** Self-Implementation Project  
**Target Platform:** Zerodha Kite Connect API

---

## 1. Executive Summary

### 1.1 Product Vision
A self-hosted, Python-based algorithmic trading system designed for daily scalping strategies on Indian equity markets through Zerodha Kite Connect API. The system will automate high-frequency intraday trades based on technical indicators while maintaining strict risk controls and SEBI compliance.

### 1.2 Key Objectives
- Execute 10-50 scalping trades daily with 30-second to 5-minute holding periods
- Achieve <100ms order execution latency
- Maintain 100% SEBI compliance for retail algo trading (October 2025 regulations)
- Provide real-time monitoring and manual override capabilities
- Enable backtesting and paper trading before live deployment

### 1.3 Success Metrics
- System uptime: >99.5% during market hours (9:15 AM - 3:30 PM IST)
- Order execution success rate: >95%
- Maximum daily drawdown: <2% of capital
- Win rate target: >55% with risk-reward ratio of 1:1.5
- False signal rate: <30%

---

## 2. Product Scope

### 2.1 In Scope
- Real-time market data streaming via WebSocket
- Technical indicator-based scalping strategies (EMA, RSI, MACD, Bollinger Bands)
- Automated order placement and management
- Position tracking and P&L monitoring
- Risk management system (stop-loss, position sizing, daily limits)
- Backtesting engine for historical data
- Paper trading mode
- Logging and audit trails
- Web-based monitoring dashboard
- SEBI compliance features (Algo ID, static IP, registration support)

### 2.2 Out of Scope (Phase 1)
- Multi-broker support (only Zerodha)
- Options and futures trading (equities only)
- Machine learning/AI-based strategies
- Mobile application
- Social trading/signal sharing
- Multi-user support
- Cloud deployment (local/VPS only)

---

## 3. User Personas

### Primary User: Individual Retail Trader
- **Background:** Active trader with Zerodha account, basic programming knowledge
- **Goals:** Automate scalping to reduce emotional trading, improve consistency
- **Pain Points:** Manual execution delays, emotional decision-making, missing opportunities
- **Technical Skills:** Intermediate Python, can modify configuration files

---

## 4. Functional Requirements

### 4.1 Authentication & Connection Module

**FR-1.1: Zerodha API Authentication**
- Implement OAuth2 login flow with TOTP 2FA
- Store access tokens securely (encrypted, environment variables)
- Auto-refresh tokens before expiry
- Handle session timeout gracefully

**FR-1.2: Connection Management**
- Establish WebSocket connection for real-time data
- Implement reconnection logic with exponential backoff
- Monitor connection health with heartbeat/ping
- Log all connection events

**Priority:** Critical  
**Open Source Options:** 
- `pykiteconnect` - Official Zerodha Python client (https://github.com/zerodha/pykiteconnect)
- `python-dotenv` - Environment variable management

---

### 4.2 Market Data Module

**FR-2.1: Real-Time Data Streaming**
- Subscribe to tick data for selected instruments (5-10 stocks)
- Process LTP, bid/ask, volume updates
- Handle 500-1000 ticks per second
- Store tick data in memory buffer (last 500 ticks)

**FR-2.2: Historical Data Fetching**
- Fetch OHLCV data for backtesting (1-min, 5-min candles)
- Cache historical data locally (SQLite/CSV)
- Update historical data daily

**FR-2.3: Data Processing Pipeline**
- Calculate technical indicators in real-time
- Maintain rolling windows (e.g., last 50 candles for EMA)
- Normalize data for consistency

**Priority:** Critical  
**Open Source Options:**
- `kiteconnect.ticker` - WebSocket streaming
- `pandas` - Data manipulation
- `TA-Lib` / `pandas-ta` - Technical indicators library

---

### 4.3 Strategy Engine Module

**FR-3.1: Scalping Strategy Implementation**

**Strategy 1: EMA Crossover + RSI Filter**
- Entry Signal:
  - Fast EMA (9) crosses above Slow EMA (21)
  - RSI(14) between 40-60 (avoid overbought/oversold)
  - Volume > 1.2x average volume (last 20 periods)
- Exit Signal:
  - Target: +0.5-1% from entry
  - Stop-loss: -0.3% from entry
  - Trailing stop after +0.3% profit
  - Time-based exit: Close position after 5 minutes if no target hit

**Strategy 2: Bollinger Bands Breakout**
- Entry Signal:
  - Price breaks above upper band OR below lower band
  - RSI confirms (>60 for long, <40 for short)
  - MACD histogram shows momentum
- Exit Signal:
  - Price reverts to middle band
  - Fixed stop-loss: 1 ATR from entry
  - Target: 1.5 ATR from entry

**Strategy 3: VWAP + Volume Spike**
- Entry Signal:
  - Price crosses VWAP with volume spike (>2x average)
  - Price momentum confirmed by 5-period EMA direction
- Exit Signal:
  - Price returns to VWAP
  - Fixed 0.4% stop-loss, 0.6% target

**FR-3.2: Signal Generation**
- Process data every tick or candle close
- Generate BUY/SELL/HOLD signals with confidence scores
- Queue signals for execution module

**FR-3.3: Strategy Configuration**
- Load strategy parameters from config file (YAML/JSON)
- Support multiple strategies running simultaneously
- Enable/disable strategies without code changes

**Priority:** Critical  
**Open Source Options:**
- `backtrader` - Strategy framework (https://github.com/mementum/backtrader)
- `TA-Lib` / `pandas-ta` - Indicator calculations
- Custom Python classes for strategy logic

---

### 4.4 Order Execution Module

**FR-4.1: Order Placement**
- Place MARKET orders for instant execution (scalping requirement)
- Place LIMIT orders when spread is favorable
- Support bracket orders (entry + SL + target in one order)
- Handle order modifications (stop-loss adjustment)

**FR-4.2: Order Management System (OMS)**
- Track order lifecycle: PENDING → OPEN → COMPLETE/REJECTED/CANCELLED
- Store all orders in database with timestamps
- Match executed orders with positions
- Handle partial fills

**FR-4.3: Position Management**
- Track open positions in real-time
- Calculate unrealized P&L continuously
- Auto-close positions at 3:20 PM (before market close)
- Support multiple positions (max 3-5 concurrent trades)

**FR-4.4: Error Handling**
- Retry failed orders (max 3 attempts)
- Handle insufficient margin errors
- Log all API errors with context
- Alert user on critical errors (Telegram/Email)

**Priority:** Critical  
**Open Source Options:**
- `pykiteconnect.kite.place_order()` - Order placement
- Custom OMS layer for tracking
- `Redis` - In-memory order state management (optional)

---

### 4.5 Risk Management Module

**FR-5.1: Position Sizing**
- Calculate position size based on:
  - Available capital
  - Risk per trade (1-2% of capital)
  - Stock volatility (ATR-based sizing)
- Enforce maximum position size per stock
- Limit total exposure to 25% of capital

**FR-5.2: Stop-Loss Management**
- Mandatory stop-loss for every trade
- Support fixed percentage, ATR-based, and trailing stops
- Execute stop-loss immediately (MARKET order)
- Never modify stop-loss to extend risk

**FR-5.3: Daily Loss Limits**
- Track cumulative daily P&L
- Halt trading if daily loss exceeds 2% of capital
- Require manual override to resume trading
- Send alert when approaching limit (1.5% loss)

**FR-5.4: Maximum Trade Limits**
- Cap at 50 trades per day
- Limit orders per second (1 order/sec to avoid rate limits)
- Block trading during high volatility events (VIX spike)

**FR-5.5: Circuit Breakers**
- Auto-shutdown on:
  - 3 consecutive losing trades
  - API errors exceeding threshold (10 errors/minute)
  - Abnormal slippage (>0.5% from expected price)
- Require manual review before restarting

**Priority:** Critical  
**Open Source Options:**
- Custom Python logic
- `numpy` - Mathematical calculations for sizing

---

### 4.6 Backtesting Module

**FR-6.1: Historical Simulation**
- Run strategies on 6-12 months historical data
- Simulate order execution with realistic slippage (0.05%)
- Include brokerage costs (₹20 per order or 0.03% for intraday)
- Support walk-forward analysis

**FR-6.2: Performance Metrics**
- Total return, CAGR, Sharpe ratio
- Maximum drawdown, win rate, profit factor
- Average win/loss ratio
- Expectancy per trade
- Generate detailed trade log

**FR-6.3: Optimization**
- Test parameter combinations (grid search)
- Identify optimal indicator periods
- Prevent overfitting (out-of-sample validation)

**Priority:** High  
**Open Source Options:**
- `backtrader` - Backtesting framework (https://github.com/mementum/backtrader)
- `QuantConnect LEAN` - Advanced backtesting (https://github.com/QuantConnect/Lean)
- `pandas` + custom code for simple backtests

---

### 4.7 Monitoring & Logging Module

**FR-7.1: Real-Time Dashboard**
- Web-based interface (Flask/Dash)
- Display:
  - Current positions and P&L
  - Today's trades (entry, exit, profit/loss)
  - Open orders
  - Strategy status (active/paused)
  - Connection status
  - Risk metrics (daily loss, position count)
- Update every 1 second

**FR-7.2: Logging System**
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Structured JSON logs with timestamps
- Separate log files:
  - `system.log` - Application events
  - `trades.log` - All trade executions
  - `errors.log` - Errors only
  - `signals.log` - Strategy signals
- Rotate logs daily, compress old logs

**FR-7.3: Alerting System**
- Send alerts via:
  - Telegram bot messages
  - Email (critical errors only)
  - SMS (optional, via external service)
- Alert triggers:
  - Daily loss limit reached
  - System errors
  - Manual intervention required
  - End-of-day summary

**Priority:** High  
**Open Source Options:**
- `Flask` / `Dash` - Web dashboard (https://github.com/plotly/dash)
- `structlog` - Structured logging
- `python-telegram-bot` - Telegram notifications (https://github.com/python-telegram-bot/python-telegram-bot)
- `Grafana` + `Prometheus` - Advanced monitoring (optional)

---

### 4.8 Configuration Module

**FR-8.1: Configuration Files**
- `config.yaml` - Main configuration
  - Broker credentials (API key, redirect URL)
  - Strategy parameters
  - Risk limits
  - Instrument list
- `secrets.env` - Sensitive data (API secret, access token)
- Allow hot-reload of non-critical configs

**FR-8.2: Instrument Selection**
- Define watchlist (5-10 liquid stocks)
- Criteria: Average volume >1M shares/day, volatility 1-3%
- Examples: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK

**Priority:** Medium  
**Open Source Options:**
- `PyYAML` - YAML parsing
- `python-dotenv` - Environment variables

---

### 4.9 SEBI Compliance Module

**FR-9.1: Algo Registration Support**
- Generate algo strategy description (white-box format)
- Maintain unique Algo ID for each strategy
- Tag all orders with Algo ID (as per SEBI circular)

**FR-9.2: Static IP Configuration**
- Configure static IP for order routing
- Register IP with Zerodha
- Log IP address with each order

**FR-9.3: Audit Trails**
- Store complete audit trail:
  - Strategy logic and version
  - All order requests and responses
  - Market data at decision time
  - Risk checks applied
- Retain audit logs for 5 years

**FR-9.4: Kill Switch**
- Manual emergency shutdown button
- Instantly cancel all orders and close positions
- Disconnect from API

**Priority:** Critical (Regulatory)  
**Open Source Options:**
- Custom logging + database storage
- `PostgreSQL` / `SQLite` - Audit trail storage

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR-1:** Order execution latency <100ms (95th percentile)
- **NFR-2:** Dashboard refresh rate: 1 second
- **NFR-3:** Process 1000 ticks/second without data loss
- **NFR-4:** Strategy signal generation <50ms per update

### 5.2 Reliability
- **NFR-5:** System uptime 99.5% during market hours
- **NFR-6:** Auto-restart on crash (systemd/supervisor)
- **NFR-7:** Graceful degradation on API issues
- **NFR-8:** Data backup daily (trade logs, configs)

### 5.3 Security
- **NFR-9:** Encrypt API credentials at rest (AES-256)
- **NFR-10:** Use HTTPS for dashboard
- **NFR-11:** Implement rate limiting on dashboard access
- **NFR-12:** No credentials in code or logs

### 5.4 Scalability
- **NFR-13:** Support 10 instruments simultaneously
- **NFR-14:** Handle 50 trades/day without performance degradation
- **NFR-15:** Database size <1GB per month (optimized logging)

### 5.5 Maintainability
- **NFR-16:** Modular code architecture (separate modules)
- **NFR-17:** 80%+ code documentation
- **NFR-18:** Unit tests for critical functions
- **NFR-19:** Version control (Git)

### 5.6 Usability
- **NFR-20:** Configuration via simple YAML files (no code changes)
- **NFR-21:** Dashboard accessible on mobile browsers
- **NFR-22:** Clear error messages with actionable guidance

---

## 6. System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER INTERFACE                    │
│  Web Dashboard (Flask/Dash) + Telegram Alerts      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              APPLICATION LAYER                      │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  Strategy  │ │     Risk     │ │    Config    │ │
│  │   Engine   │ │  Management  │ │   Manager    │ │
│  └────────────┘ └──────────────┘ └──────────────┘ │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   Order    │ │   Position   │ │   Logging    │ │
│  │ Management │ │   Tracker    │ │   System     │ │
│  └────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              DATA LAYER                             │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │Market Data │ │  Order Queue │ │   Database   │ │
│  │  Handler   │ │  (In-Memory) │ │  (SQLite/    │ │
│  │(WebSocket) │ │              │ │  PostgreSQL) │ │
│  └────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         ZERODHA KITE CONNECT API                    │
│  REST API (Orders, Positions, Holdings)             │
│  WebSocket API (Real-time Market Data)              │
└─────────────────────────────────────────────────────┘
```

### 6.2 Component Interaction Flow

**Normal Trading Flow:**
1. WebSocket receives tick data → Market Data Handler
2. Market Data Handler updates indicators → Strategy Engine
3. Strategy Engine generates signal → Risk Management check
4. Risk Management approves → Order Management System
5. OMS places order via Kite API → Position Tracker
6. Position Tracker monitors P&L → Risk Management (stop-loss check)
7. All events logged → Database + Dashboard

**Error Flow:**
1. API error detected → Error Handler
2. Error Handler logs error → Logging System
3. If critical → Alert System (Telegram/Email)
4. If recoverable → Retry logic
5. If unrecoverable → Circuit Breaker → Manual intervention required

---

## 7. Technology Stack

### 7.1 Core Technologies

| Component | Technology | Justification |
|-----------|-----------|--------------|
| **Programming Language** | Python 3.10+ | Rich ecosystem, fast development, excellent libraries |
| **API Client** | `pykiteconnect` | Official Zerodha library, well-maintained |
| **Data Processing** | `pandas`, `numpy` | Industry standard for time-series analysis |
| **Technical Indicators** | `pandas-ta` or `TA-Lib` | Comprehensive indicator library |
| **Web Dashboard** | `Flask` or `Dash` | Lightweight, easy to deploy |
| **Database** | `SQLite` (dev), `PostgreSQL` (prod) | SQLite for simplicity, PostgreSQL for production |
| **Logging** | `structlog` | Structured JSON logs for easy parsing |
| **Configuration** | `PyYAML` | Human-readable config files |
| **Alerts** | `python-telegram-bot` | Free, instant notifications |
| **Testing** | `pytest` | Standard Python testing framework |
| **Backtesting** | `backtrader` | Open-source, extensible framework |

### 7.2 Development Tools
- **IDE:** VS Code / PyCharm
- **Version Control:** Git + GitHub/GitLab
- **Dependency Management:** `pip` + `requirements.txt` or `poetry`
- **Environment Management:** `venv` or `conda`

### 7.3 Infrastructure
- **Hosting:** Local PC or VPS (DigitalOcean, AWS Lightsail)
- **OS:** Ubuntu 22.04 LTS
- **Process Management:** `systemd` or `supervisor`
- **Networking:** Static IP (required for SEBI compliance)
- **Backup:** Daily cron job to backup database and configs

---

## 8. Existing Open-Source Solutions & Libraries

### 8.1 Complete Trading Bots (Reference/Inspiration)

| Project | Language | Stars | Description | Link |
|---------|----------|-------|-------------|------|
| **Freqtrade** | Python | 36K+ | Crypto trading bot, excellent architecture | https://github.com/freqtrade/freqtrade |
| **Jesse** | Python | 5K+ | Algo trading framework with backtesting | https://github.com/jesse-ai/jesse |
| **Backtrader** | Python | 13K+ | Backtesting and live trading framework | https://github.com/mementum/backtrader |
| **QuantConnect LEAN** | C#/Python | 9K+ | Institutional-grade algo trading engine | https://github.com/QuantConnect/Lean |
| **Hummingbot** | Python | 7K+ | Market-making and arbitrage bot | https://github.com/hummingbot/hummingbot |

**Recommendation:** Study Freqtrade's architecture for modular design patterns, but build custom solution for Indian markets/Zerodha specifics.

### 8.2 Core Libraries

#### Market Data & API
- **pykiteconnect**: https://github.com/zerodha/pykiteconnect (Official Zerodha client)
- **CCXT**: https://github.com/ccxt/ccxt (Multi-exchange support, not for Zerodha)

#### Technical Analysis
- **pandas-ta**: https://github.com/twopirllc/pandas-ta (150+ indicators, easy syntax)
- **TA-Lib**: https://github.com/mrjbq7/ta-lib (Traditional, requires C library installation)
- **finta**: https://github.com/peerchemist/finta (Pure Python, no dependencies)

#### Backtesting
- **backtrader**: https://github.com/mementum/backtrader (Most popular Python framework)
- **bt**: https://github.com/pmorissette/bt (Flexible, uses pandas)
- **vectorbt**: https://github.com/polakowo/vectorbt (Fast, vectorized backtesting)

#### Dashboard & Visualization
- **Dash by Plotly**: https://github.com/plotly/dash (Interactive dashboards)
- **Streamlit**: https://github.com/streamlit/streamlit (Rapid prototyping)
- **Flask**: https://github.com/pallets/flask (Lightweight web framework)

#### Logging & Monitoring
- **structlog**: https://github.com/hynek/structlog (Structured logging)
- **loguru**: https://github.com/Delgan/loguru (Simplified logging)
- **Prometheus Python client**: https://github.com/prometheus/client_python (Metrics)

#### Alerts
- **python-telegram-bot**: https://github.com/python-telegram-bot/python-telegram-bot
- **apprise**: https://github.com/caronc/apprise (Multi-channel notifications)

#### Database & Storage
- **SQLAlchemy**: https://github.com/sqlalchemy/sqlalchemy (ORM for database)
- **TinyDB**: https://github.com/msiemens/tinydb (Lightweight JSON database)

### 8.3 Zerodha-Specific Resources

#### Kite Connect Examples
- **Zerodha Official Samples**: https://github.com/zerodhatech/pykiteconnect/tree/master/examples
- **Community Projects**: Search GitHub for "kiteconnect" tag

#### Indian Market Data
- **NSE Tools**: https://github.com/vsjha18/nsetools (NSE data scraper)
- **yfinance**: https://github.com/ranaroussi/yfinance (Yahoo Finance API, includes NSE)

---

## 9. Detailed Task Breakdown

### Phase 1: Foundation (Weeks 1-2)

**Task 1.1: Environment Setup**
- [ ] Install Python 3.10+, create virtual environment
- [ ] Install dependencies: `pykiteconnect`, `pandas`, `pandas-ta`, `flask`, `structlog`, `pytest`
- [ ] Create project folder structure:
  ```
  scalping-bot/
  ├── config/
  │   ├── config.yaml
  │   └── secrets.env
  ├── src/
  │   ├── __init__.py
  │   ├── auth/
  │   │   └── zerodha_auth.py
  │   ├── data/
  │   │   ├── market_data.py
  │   │   └── historical_data.py
  │   ├── strategy/
  │   │   ├── base_strategy.py
  │   │   ├── ema_rsi_strategy.py
  │   │   └── bb_breakout_strategy.py
  │   ├── execution/
  │   │   ├── order_manager.py
  │   │   └── position_tracker.py
  │   ├── risk/
  │   │   └── risk_manager.py
  │   ├── backtest/
  │   │   └── backtest_engine.py
  │   ├── dashboard/
  │   │   └── app.py
  │   └── utils/
  │       ├── logger.py
  │       ├── config_loader.py
  │       └── alerts.py
  ├── logs/
  ├── data/
  │   └── historical/
  ├── tests/
  ├── main.py
  ├── requirements.txt
  └── README.md
  ```

**Task 1.2: Zerodha Authentication**
- [ ] Implement OAuth2 login flow
- [ ] Store access token securely
- [ ] Implement token refresh logic
- [ ] Test login with real Zerodha account

**Task 1.3: Configuration Management**
- [ ] Create YAML config schema
- [ ] Implement config loader with validation
- [ ] Set up environment variable management

**Deliverable:** Working authentication and project skeleton

---

### Phase 2: Market Data Pipeline (Weeks 3-4)

**Task 2.1: WebSocket Data Streaming**
- [ ] Connect to Kite WebSocket API
- [ ] Subscribe to 5 instruments (start with RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK)
- [ ] Implement tick data handler
- [ ] Store ticks in memory buffer (circular buffer, last 500 ticks)
- [ ] Handle reconnection on disconnect

**Task 2.2: Historical Data Fetching**
- [ ] Fetch 1-min and 5-min OHLCV data
- [ ] Store in SQLite database
- [ ] Implement daily data update script

**Task 2.3: Technical Indicators**
- [ ] Implement EMA calculation (9, 21 periods)
- [ ] Implement RSI calculation (14 period)
- [ ] Implement Bollinger Bands (20, 2σ)
- [ ] Implement MACD (12, 26, 9)
- [ ] Implement ATR (14 period)
- [ ] Test indicators against known values

**Deliverable:** Real-time data pipeline with indicators

---

### Phase 3: Strategy Implementation (Weeks 5-6)

**Task 3.1: Base Strategy Framework**
- [ ] Create abstract strategy class
- [ ] Define signal interface (BUY/SELL/HOLD)
- [ ] Implement strategy lifecycle (init, process, cleanup)

**Task 3.2: EMA-RSI Strategy**
- [ ] Code entry conditions
- [ ] Code exit conditions (target, stop-loss, time-based)
- [ ] Implement trailing stop logic
- [ ] Unit tests for strategy

**Task 3.3: Bollinger Bands Strategy**
- [ ] Code breakout detection
- [ ] Code reversal exit
- [ ] ATR-based stop-loss
- [ ] Unit tests

**Task 3.4: Strategy Manager**
- [ ] Load strategies from config
- [ ] Run multiple strategies in parallel
- [ ] Aggregate signals (conflict resolution)

**Deliverable:** Working strategy engine with 2 strategies

---

### Phase 4: Order Execution (Weeks 7-8)

**Task 4.1: Order Manager**
- [ ] Implement order placement (MARKET, LIMIT)
- [ ] Implement order modification
- [ ] Implement order cancellation
- [ ] Handle order responses (SUCCESS, REJECTED, PENDING)

**Task 4.2: Position Tracker**
- [ ] Track open positions in real-time
- [ ] Calculate realized/unrealized P&L
- [ ] Match orders to positions
- [ ] Implement position closing logic

**Task 4.3: Order Queue & Rate Limiting**
- [ ] Implement order queue (FIFO)
- [ ] Rate limiting (1 order/sec)
- [ ] Retry logic for failed orders
- [ ] Error handling

**Task 4.4: Integration Testing**
- [ ] Test with paper trading account
- [ ] Simulate order lifecycle
- [ ] Test error scenarios

**Deliverable:** Fully functional order execution system

---

### Phase 5: Risk Management (Week 9)

**Task 5.1: Position Sizing**
- [ ] Implement risk-based sizing (1% risk per trade)
- [ ] ATR-based sizing
- [ ] Maximum position size limits

**Task 5.2: Stop-Loss System**
- [ ] Automatic stop-loss placement
- [ ] Trailing stop implementation
- [ ] Emergency stop-loss (MARKET order)

**Task 5.3: Daily Limits**
- [ ] Track daily P&L
- [ ] Halt on 2% daily loss
- [ ] Halt on 50 trades/day
- [ ] Circuit breaker logic

**Task 5.4: Risk Checks**
- [ ] Pre-trade risk validation
- [ ] Exposure limits (25% of capital)
- [ ] Volatility filters (skip trading on high VIX)

**Deliverable:** Complete risk management system

---

### Phase 6: Backtesting (Weeks 10-11)

**Task 6.1: Backtest Engine**
- [ ] Integrate `backtrader` framework
- [ ] Create data feed from historical database
- [ ] Implement slippage model (0.05%)
- [ ] Include brokerage costs (₹20/order)

**Task 6.2: Strategy Backtests**
- [ ] Run EMA-RSI strategy on 12 months data
- [ ] Run BB Breakout strategy on 12 months data
- [ ] Generate performance reports

**Task 6.3: Optimization**
- [ ] Parameter grid search (EMA periods, RSI thresholds)
- [ ] Walk-forward analysis
- [ ] Out-of-sample validation

**Task 6.4: Performance Analysis**
- [ ] Calculate Sharpe ratio, max drawdown
- [ ] Generate equity curve
- [ ] Trade-by-trade analysis

**Deliverable:** Validated strategies with backtested results

---

### Phase 7: Monitoring & Dashboard (Weeks 12-13)

**Task 7.1: Logging System**
- [ ] Implement structured logging (JSON format)
- [ ] Separate log files (system, trades, errors, signals)
- [ ] Log rotation (daily)
- [ ] Error logging with stack traces

**Task 7.2: Web Dashboard**
- [ ] Create Flask/Dash app
- [ ] Real-time position display
- [ ] Trade history table
- [ ] P&L chart (daily, cumulative)
- [ ] Strategy status indicators
- [ ] Manual controls (pause/resume, emergency stop)

**Task 7.3: Telegram Alerts**
- [ ] Set up Telegram bot
- [ ] Send trade notifications
- [ ] Send error alerts
- [ ] Daily summary report

**Task 7.4: Dashboard Deployment**
- [ ] Run dashboard on local network
- [ ] Secure with password (basic auth)
- [ ] Test on mobile browser

**Deliverable:** Functional monitoring dashboard

---

### Phase 8: SEBI Compliance (Week 14)

**Task 8.1: Algo Registration**
- [ ] Document strategy logic (white-box format)
- [ ] Generate unique Algo ID
- [ ] Tag orders with Algo ID

**Task 8.2: Static IP Setup**
- [ ] Configure static IP on VPS/local network
- [ ] Register IP with Zerodha
- [ ] Verify IP in all order requests

**Task 8.3: Audit Trail**
- [ ] Store all orders in database (permanent)
- [ ] Store strategy decisions (signals + market data)
- [ ] Store risk check results
- [ ] Implement audit log export

**Task 8.4: Kill Switch**
- [ ] Implement emergency shutdown button
- [ ] Cancel all pending orders
- [ ] Close all positions
- [ ] Disconnect from API

**Deliverable:** SEBI-compliant trading system

---

### Phase 9: Testing & Deployment (Weeks 15-16)

**Task 9.1: Paper Trading**
- [ ] Run system in paper trading mode (no real money)
- [ ] Monitor for 2-4 weeks
- [ ] Log all trades and errors
- [ ] Validate risk limits

**Task 9.2: System Hardening**
- [ ] Handle edge cases (market holidays, circuit breakers)
- [ ] Test reconnection on network failure
- [ ] Test behavior on API downtime
- [ ] Test auto-restart on crash

**Task 9.3: Performance Optimization**
- [ ] Profile code for bottlenecks
- [ ] Optimize indicator calculations
- [ ] Reduce memory usage

**Task 9.4: Documentation**
- [ ] Write user manual (setup, configuration, operation)
- [ ] Document troubleshooting steps
- [ ] Code documentation (docstrings)
- [ ] Create deployment checklist

**Task 9.5: Production Deployment**
- [ ] Deploy on VPS with static IP
- [ ] Set up `systemd` service for auto-start
- [ ] Configure backups (daily cron job)
- [ ] Run final smoke tests

**Deliverable:** Production-ready system

---

### Phase 10: Live Trading & Iteration (Ongoing)

**Task 10.1: Go Live**
- [ ] Start with small capital (₹10,000 - ₹50,000)
- [ ] Enable only 1 strategy initially
- [ ] Monitor closely for first week

**Task 10.2: Performance Monitoring**
- [ ] Daily performance review
- [ ] Weekly strategy analysis
- [ ] Monthly P&L reporting

**Task 10.3: Continuous Improvement**
- [ ] Refine strategy parameters based on live results
- [ ] Fix bugs and edge cases
- [ ] Add new strategies
- [ ] Optimize execution (reduce slippage)

**Deliverable:** Profitable live trading system

---

## 10. Risk & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| API downtime during market hours | Medium | High | Implement local caching, fallback to manual trading |
| Strategy underperformance in live market | High | High | Extensive backtesting, paper trading, start with small capital |
| Regulatory non-compliance (SEBI) | Low | Critical | Implement all compliance features from day 1 |
| Order execution failures | Medium | Medium | Retry logic, error alerts, circuit breakers |
| Network connectivity issues | Medium | High | Redundant internet connection (4G backup), auto-reconnect |
| Over-optimization (curve fitting) | High | Medium | Out-of-sample testing, walk-forward analysis |
| Market gaps (opening, circuit breakers) | Low | High | Avoid holding overnight positions, pre-market checks |
| Bugs causing financial loss | Medium | Critical | Extensive testing, paper trading, start small |

---

## 11. Cost Estimate

### 11.1 Development Costs
- **Time:** 16 weeks (4 months) at 20 hours/week = 320 hours
- **Effort Value:** Self-development (₹0 if self-implemented)
- **Learning Resources:** QuantInsti courses, YouTube tutorials (₹0 - ₹5,000)

### 11.2 Operational Costs (Monthly)

| Item | Cost |
|------|------|
| Zerodha Kite Connect API | ₹500/month |
| VPS (DigitalOcean, 2GB RAM) | ₹800/month |
| Static IP | Included in VPS |
| Domain (optional) | ₹100/month |
| Backup storage | ₹0 (local) |
| **Total** | **₹1,400/month** |

### 11.3 Trading Costs (Per Trade)
- Brokerage: ₹0 (Zerodha intraday is ₹0 brokerage)
- STT: 0.025% on sell side
- Exchange charges: ~₹0.00325 per ₹100
- GST: 18% on brokerage
- SEBI charges: ₹10 per crore
- Stamp duty: 0.003% on buy side

**Effective cost:** ₹5-10 per intraday trade

---

## 12. Success Criteria

### 12.1 Technical Success
- [ ] System runs continuously during market hours for 30 days without crashes
- [ ] 95%+ order execution success rate
- [ ] <100ms average order latency
- [ ] Zero SEBI compliance violations

### 12.2 Financial Success
- [ ] Positive net P&L after 3 months of live trading
- [ ] Maximum drawdown <5% of capital
- [ ] Win rate >50%
- [ ] Sharpe ratio >1.0

### 12.3 Operational Success
- [ ] Able to run system unattended during market hours
- [ ] Dashboard provides all necessary information for decision-making
- [ ] Alerts are timely and actionable
- [ ] Easy to modify strategy parameters

---

## 13. Future Enhancements (Post-Launch)

### Phase 2 Features
- Options trading strategies (iron condor, straddles)
- Multi-broker support (Upstox, Angel One)
- Machine learning-based signal filtering
- Sentiment analysis (news, Twitter)
- Advanced order types (iceberg, TWAP)

### Phase 3 Features
- Cloud deployment (AWS, GCP)
- Mobile app (React Native)
- Multi-user support (SaaS model)
- Strategy marketplace (share/sell strategies)
- Advanced analytics (trade journal, pattern recognition)

---

## 14. References & Resources

### 14.1 Official Documentation
- Zerodha Kite Connect: https://kite.trade/docs/connect/v3/
- SEBI Algo Trading Circular: https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html

### 14.2 Learning Resources
- QuantInsti Algo Trading Course: https://www.quantinsti.com/
- Backtrader Documentation: https://www.backtrader.com/docu/
- Python for Finance (Yves Hilpisch book)

### 14.3 Community
- Zerodha TradingQ&A: https://tradingqanda.com/
- Reddit r/algotrading: https://www.reddit.com/r/algotrading/
- QuantConnect Community: https://www.quantconnect.com/forum/

---

## 15. Appendix

### A. Sample Configuration File

```yaml
# config.yaml

broker:
  name: zerodha
  api_key: YOUR_API_KEY
  redirect_url: http://localhost:8080/callback

trading:
  mode: paper  # paper, live
  capital: 100000  # ₹1 lakh
  risk_per_trade_percent: 1.0
  max_positions: 3
  max_trades_per_day: 50

instruments:
  - symbol: RELIANCE
    exchange: NSE
    lot_size: 1
  - symbol: TCS
    exchange: NSE
    lot_size: 1
  - symbol: INFY
    exchange: NSE
    lot_size: 1

strategies:
  - name: ema_rsi
    enabled: true
    params:
      fast_ema: 9
      slow_ema: 21
      rsi_period: 14
      rsi_min: 40
      rsi_max: 60
      target_percent: 0.8
      stoploss_percent: 0.4
      trailing_stop_trigger: 0.3

  - name: bb_breakout
    enabled: false
    params:
      bb_period: 20
      bb_std: 2.0
      rsi_period: 14
      target_atr_mult: 1.5
      stoploss_atr_mult: 1.0

risk:
  max_daily_loss_percent: 2.0
  max_position_size_percent: 25.0
  circuit_breaker:
    consecutive_losses: 3
    api_errors_per_minute: 10
    abnormal_slippage_percent: 0.5

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  format: json
  rotation: daily

alerts:
  telegram:
    enabled: true
    bot_token: YOUR_BOT_TOKEN
    chat_id: YOUR_CHAT_ID
  email:
    enabled: false
    smtp_server: smtp.gmail.com
    smtp_port: 587
    from_email: [email protected]
    to_email: [email protected]

dashboard:
  host: 0.0.0.0
  port: 8050
  refresh_rate: 1  # seconds
```

### B. Sample Database Schema

```sql
-- trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,  -- BUY, SELL
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    order_id VARCHAR(50),
    status VARCHAR(20),  -- PENDING, COMPLETE, REJECTED
    pnl REAL,
    commission REAL,
    algo_id VARCHAR(50)
);

-- positions table
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL,
    opened_at DATETIME NOT NULL,
    closed_at DATETIME
);

-- orders table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10),  -- MARKET, LIMIT
    action VARCHAR(10),  -- BUY, SELL
    quantity INTEGER NOT NULL,
    price REAL,
    order_id VARCHAR(50),
    status VARCHAR(20),
    reason TEXT,
    algo_id VARCHAR(50)
);

-- signals table (for audit)
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    signal VARCHAR(10),  -- BUY, SELL, HOLD
    confidence REAL,
    market_data TEXT,  -- JSON of indicators at signal time
    risk_approved BOOLEAN
);
```

### C. Sample Strategy Code

```python
# src/strategy/ema_rsi_strategy.py

from .base_strategy import BaseStrategy
import pandas as pd

class EmaRsiStrategy(BaseStrategy):
    """
    EMA Crossover with RSI Filter Strategy
    
    Entry: Fast EMA crosses above Slow EMA + RSI 40-60 + Volume spike
    Exit: Target 0.8%, Stop-loss 0.4%, Trailing stop after 0.3%
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.fast_ema = config['fast_ema']
        self.slow_ema = config['slow_ema']
        self.rsi_period = config['rsi_period']
        self.rsi_min = config['rsi_min']
        self.rsi_max = config['rsi_max']
        self.target_pct = config['target_percent']
        self.sl_pct = config['stoploss_percent']
        
    def calculate_indicators(self, df):
        """Calculate EMA, RSI, Volume"""
        df['ema_fast'] = df['close'].ewm(span=self.fast_ema).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_ema).mean()
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume moving average
        df['vol_ma'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def generate_signal(self, df):
        """Generate BUY/SELL/HOLD signal"""
        if len(df) < max(self.slow_ema, self.rsi_period):
            return 'HOLD', 0.0
        
        df = self.calculate_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # BUY signal
        if (prev['ema_fast'] <= prev['ema_slow'] and 
            latest['ema_fast'] > latest['ema_slow'] and
            self.rsi_min < latest['rsi'] < self.rsi_max and
            latest['volume'] > 1.2 * latest['vol_ma']):
            
            confidence = self._calculate_confidence(df)
            return 'BUY', confidence
        
        # SELL signal (for exiting longs, not shorting)
        if latest['ema_fast'] < latest['ema_slow']:
            return 'SELL', 0.8
        
        return 'HOLD', 0.0
    
    def _calculate_confidence(self, df):
        """Calculate signal confidence 0-1"""
        latest = df.iloc[-1]
        
        # Factors: RSI position, volume strength, EMA separation
        rsi_score = (60 - abs(latest['rsi'] - 50)) / 10  # Higher for RSI near 50
        vol_score = min(latest['volume'] / latest['vol_ma'], 2.0) / 2.0  # Cap at 2x
        ema_sep = abs(latest['ema_fast'] - latest['ema_slow']) / latest['close']
        ema_score = min(ema_sep * 100, 1.0)  # Cap at 1.0
        
        confidence = (rsi_score * 0.4 + vol_score * 0.3 + ema_score * 0.3)
        return max(0.0, min(confidence, 1.0))
    
    def get_stop_loss(self, entry_price):
        """Calculate stop-loss price"""
        return entry_price * (1 - self.sl_pct / 100)
    
    def get_target(self, entry_price):
        """Calculate target price"""
        return entry_price * (1 + self.target_pct / 100)
```

---

## Document Control

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-17 | Self | Initial PRD creation |

**Approval:**
- [ ] Self-reviewed and approved for implementation

**Next Review Date:** 2025-11-17 (1 month)

---

*End of PRD*