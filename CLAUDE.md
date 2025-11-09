# CLAUDE.md - Scalping Bot Trading System

**Last Updated:** October 31, 2025
**Project:** Python-based Algorithmic Trading Bot for Indian Stock Markets
**Tech Stack:** Flask + Python + PostgreSQL + Zerodha/Angel/Kotak API
**Claude Version:** Optimized for Claude Sonnet 4.5+

> 📘 **Note to Claude:** This file provides complete project context. Read this FIRST before any task.

---

## 🎯 Project Mission

Build a **production-ready algorithmic trading bot** for daily scalping on Indian stock markets with:
- **50+ candlestick patterns** + **16+ chart patterns** automated detection
- **1-click strategy backtesting** with detailed analytics (no external dependencies)
- **Flask dashboard** with dark theme design and real-time updates
- **Real-time pattern recognition** using TA-Lib + custom algorithms
- **Order Management System (OMS)** with 4 core modules
- **Multi-broker support** (Zerodha, Angel One, Kotak Securities)
- **Comprehensive risk management** (2% rule, kill switch, position limits)

---

## 📁 Project Structure

```
scalping-bot/
├── src/
│   ├── dashboard/              # Flask web application
│   │   ├── app.py             # Main Flask app with routes
│   │   ├── templates/         # 24+ HTML templates
│   │   └── static/            # CSS, JS, images
│   ├── analysis/              # Pattern detection & technical analysis
│   │   ├── candlestick_patterns.py  # 50+ candlestick patterns
│   │   ├── chart_patterns.py        # 16 chart patterns
│   │   └── technical_indicators.py  # EMA, RSI, MACD, BB, ATR, etc.
│   ├── strategies/            # Trading strategies
│   │   ├── base_strategy.py   # Base strategy class
│   │   ├── ema_crossover.py   # EMA crossover strategy
│   │   ├── rsi_strategy.py    # RSI-based strategy
│   │   └── breakout.py        # Breakout strategy
│   ├── brokers/               # Broker integrations
│   │   ├── broker_factory.py  # Factory pattern
│   │   ├── zerodha.py         # Zerodha Kite Connect
│   │   ├── angel.py           # Angel One SmartAPI
│   │   └── kotak.py           # Kotak Securities
│   ├── backtest/              # Backtesting engine (no dependencies)
│   │   ├── backtest_engine.py # Core backtest logic
│   │   ├── strategy_runner.py # Strategy interface
│   │   ├── performance_metrics.py  # 20+ metrics
│   │   └── cli.py             # Command-line interface
│   └── utils/                 # Utilities
│       └── config_loader.py   # Configuration management
├── backend/
│   ├── database/              # Database layer
│   │   ├── database.py        # PostgreSQL + asyncpg
│   │   └── sync_db.py         # Sync operations
│   ├── oms/                   # Order Management System
│   │   ├── order_manager.py   # Order creation & execution
│   │   ├── position_manager.py # Position tracking & P&L
│   │   ├── pre_trade_validator.py  # 7 validation checks
│   │   └── real_time_monitor.py    # Risk monitoring
│   ├── portfolio/             # Portfolio management
│   │   ├── pnl_calculator.py  # FIFO P&L calculation
│   │   ├── risk_meter.py      # Risk metrics & VaR
│   │   ├── trade_deduplication.py  # Duplicate detection
│   │   └── csv_parser.py      # CSV import (multi-broker)
│   ├── models/                # Data models
│   │   ├── order.py           # Order model
│   │   ├── position.py        # Position model
│   │   ├── trade.py           # Trade model
│   │   └── strategy.py        # Strategy model
│   ├── api/                   # REST API routes
│   │   ├── oms_routes.py      # OMS endpoints
│   │   ├── strategy_routes.py # Strategy endpoints
│   │   └── portfolio_routes.py # Portfolio endpoints
│   └── config.py              # Configuration class
├── config/
│   ├── config.yaml            # Main configuration
│   ├── secrets.env            # API credentials (gitignored)
│   └── secrets.env.example    # Example secrets file
├── tests/
│   ├── security/              # Security tests (CSRF, auth)
│   └── unit/                  # Unit tests (config, encryption)
├── logs/                      # Application logs
├── results/                   # Backtest results
├── USER_GUIDE.md              # Complete user manual (50+ pages)
├── HELP_AND_FAQ.md            # Interactive help with FAQ
├── QUICKSTART.md              # 5-minute setup guide
├── run_dashboard.py           # Dashboard launcher
└── requirements.txt           # Python dependencies
```

---

## ⚡ Essential Commands

### Development Workflow

```bash
# Install dependencies
pip install -r requirements.txt

# Start Flask dashboard
python run_dashboard.py
# OR with environment
FLASK_ENV=development python run_dashboard.py
# Dashboard runs at http://localhost:5000

# Start with custom database
DATABASE_URL="postgresql://user:pass@localhost:5432/scalping_bot" python run_dashboard.py
```

### Testing

```bash
# Run all tests (38 tests, 100% passing)
python3 -m pytest tests/ -v

# Run specific test categories
python3 -m pytest tests/security/ -v  # Security tests
python3 -m pytest tests/unit/ -v      # Unit tests

# Run with coverage
python3 -m pytest tests/ --cov=src --cov=backend --cov-report=html

# Run specific test
python3 -m pytest tests/unit/test_config_loader.py::TestConfigLoader::test_env_var_substitution -v
```

### Backtesting

```bash
# EMA Crossover strategy
python3 src/backtest/cli.py \
  --strategy ema_crossover \
  --capital 100000 \
  --fast-ema 9 \
  --slow-ema 21 \
  --stop-loss 2.0 \
  --target 4.0 \
  --verbose

# RSI strategy
python3 src/backtest/cli.py \
  --strategy rsi \
  --capital 100000 \
  --rsi-period 14 \
  --oversold 30 \
  --overbought 70

# Breakout strategy
python3 src/backtest/cli.py \
  --strategy breakout \
  --capital 100000 \
  --lookback 20 \
  --threshold 1.0

# Save results
python3 src/backtest/cli.py \
  --strategy ema_crossover \
  --output results/backtest_ema.json \
  --trade-log results/trades_ema.csv
```

### Database Operations

```bash
# Connect to PostgreSQL
psql -d scalping_bot

# View tables
\dt

# Check user profiles
SELECT id, name, email, default_broker FROM user_profiles;

# Check orders
SELECT id, symbol, side, quantity, status FROM orders ORDER BY created_at DESC LIMIT 10;

# Check positions
SELECT * FROM positions WHERE status = 'open';
```

### Linting & Formatting

```bash
# Python linting (PEP 8)
flake8 src/ backend/ --max-line-length=100

# Python formatting
black src/ backend/

# Check formatting without changes
black src/ backend/ --check
```

---

## 🎨 Code Style Guidelines

### Python

**CRITICAL RULES:**
- ✅ **PEP 8 compliance** (enforced by flake8)
- ✅ **Type hints** on all function signatures
- ✅ **Google-style docstrings** for classes and public methods
- ✅ **f-strings** for formatting → ❌ **NOT** `.format()` or `%`
- ✅ **Max line length: 100 chars**
- ✅ **Black formatter** (run before commit)

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `OrderManager`, `PatternDetector`)
- Functions/variables: `snake_case` (e.g., `calculate_profit`, `is_order_valid`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_POSITION_SIZE`, `API_BASE_URL`)
- Private methods: `_leading_underscore` (e.g., `_validate_order`, `_execute_trade`)

**Example (GOOD):**
```python
from typing import Optional, Dict
import pandas as pd

def detect_hammer_pattern(
    df: pd.DataFrame,
    index: int = -1,
    confidence_threshold: float = 0.7
) -> Optional[Dict]:
    """
    Detect hammer candlestick pattern with confidence scoring.

    Args:
        df: OHLC dataframe with columns [open, high, low, close, volume]
        index: Candle index to analyze (-1 for most recent)
        confidence_threshold: Minimum confidence to return signal (0.0-1.0)

    Returns:
        Pattern dict with confidence score, or None if not detected.

    Example:
        >>> result = detect_hammer_pattern(df, index=-1)
        >>> if result and result['confidence'] > 0.75:
        >>>     print(f"Hammer detected: {result['confidence']:.0%}")
    """
    candle = df.iloc[index]
    body = abs(candle['close'] - candle['open'])
    lower_shadow = min(candle['open'], candle['close']) - candle['low']

    # Hammer criteria: lower shadow > 2x body
    if lower_shadow < 2 * body:
        return None

    confidence = min(1.0, lower_shadow / (3 * body))

    if confidence < confidence_threshold:
        return None

    return {
        'pattern': 'hammer',
        'confidence': confidence,
        'signal': 'bullish_reversal',
        'candle_time': candle.name
    }
```

---

### Flask Routes

**CRITICAL RULES:**
- ✅ **Blueprint organization** for modular routes
- ✅ **Error handling** with try/except and proper status codes
- ✅ **CSRF protection** enabled (Flask-WTF)
- ✅ **Rate limiting** (Flask-Limiter)
- ✅ **JSON responses** with consistent structure

**Example Route:**
```python
from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect

bp = Blueprint('oms', __name__, url_prefix='/api/oms')
limiter = Limiter()
csrf = CSRFProtect()

@bp.route('/orders', methods=['POST'])
@limiter.limit("10 per minute")
@csrf.exempt  # If API endpoint
def create_order():
    """
    Create new order

    Request:
        {
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 50,
            "price": 2500.00,
            "stop_loss": 2450.00,
            "target": 2600.00
        }

    Returns:
        {
            "success": true,
            "order_id": "ORD123456",
            "message": "Order placed successfully"
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['symbol', 'side', 'quantity', 'price']
        if not all(field in data for field in required):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Create order via OMS
        order_manager = get_order_manager()
        order = order_manager.create_order(
            symbol=data['symbol'],
            side=data['side'],
            quantity=data['quantity'],
            price=data['price'],
            stop_loss=data.get('stop_loss'),
            target=data.get('target')
        )

        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Order placed successfully'
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Order creation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
```

---

## 🧪 Testing Strategy

### Coverage Status
- **Overall:** 100% tests passing (38/38)
- **Security tests:** 11/11 passing (CSRF, sessions, rate limiting)
- **Unit tests:** 27/27 passing (config, encryption, validation)

### Test Types

**Security Tests** (`tests/security/`)
- CSRF protection validation
- Session security (HttpOnly, SameSite)
- Rate limiting enforcement
- Authentication checks

**Unit Tests** (`tests/unit/`)
- Configuration loader (env var substitution)
- Encryption utilities
- Token storage
- Config validation

**Example Test:**
```python
import pytest
from src.utils.config_loader import ConfigLoader

class TestConfigLoader:
    @pytest.fixture
    def config_loader(self, tmp_path):
        """Create test config loader"""
        config_file = tmp_path / "config.yaml"
        secrets_file = tmp_path / "secrets.env"

        # Create test files
        config_file.write_text("""
broker:
  api_key: ${TEST_API_KEY}
  api_secret: ${TEST_SECRET}
trading:
  mode: paper
""")
        secrets_file.write_text("TEST_API_KEY=key123\nTEST_SECRET=secret456")

        return ConfigLoader(
            config_path=str(config_file),
            secrets_path=str(secrets_file)
        )

    def test_env_var_substitution(self, config_loader):
        """Test environment variable substitution"""
        config = config_loader.load()

        assert config['broker']['api_key'] == 'key123'
        assert config['broker']['api_secret'] == 'secret456'
```

---

## 🔐 Security Best Practices

### API Keys & Secrets

**CRITICAL: NEVER commit secrets to git!**

```bash
# ✅ CORRECT: Use config/secrets.env (gitignored)
# config/secrets.env
KITE_API_KEY=your_key_here
KITE_API_SECRET=your_secret_here
KITE_ACCESS_TOKEN=your_token_here
TELEGRAM_BOT_TOKEN=your_bot_token
DB_PASSWORD=your_db_password

# ✅ CORRECT: Reference in code
api_key = os.getenv('KITE_API_KEY')

# ❌ WRONG: Hardcoded secrets
api_key = "abc123def456"  # NEVER DO THIS
```

### SQL Injection Prevention

```python
# ✅ CORRECT: Parameterized queries (asyncpg)
async with pool.acquire() as conn:
    result = await conn.fetch(
        "SELECT * FROM orders WHERE symbol = $1",
        symbol
    )

# ❌ WRONG: String concatenation
query = f"SELECT * FROM orders WHERE symbol = '{symbol}'"  # VULNERABLE
```

### CSRF Protection

```python
# Flask app already has CSRF protection enabled
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect(app)

# For API endpoints (if needed), exempt specific routes
@app.route('/api/external', methods=['POST'])
@csrf.exempt
def external_api():
    # Only exempt if truly necessary (e.g., external webhooks)
    pass
```

---

## 🚨 Critical Trading Rules

### Order Validation (MUST CHECK BEFORE EVERY ORDER)

The `PreTradeValidator` class performs 7 critical checks:

```python
from backend.oms.pre_trade_validator import PreTradeValidator

validator = PreTradeValidator(
    max_position_size=5,
    max_risk_per_trade=0.02,  # 2%
    max_daily_loss=0.06,      # 6%
    min_risk_reward_ratio=2.0
)

# Validation checks performed:
# 1. Sufficient account balance
# 2. Stop-loss is set (mandatory)
# 3. Position sizing limits (max 5 positions)
# 4. Risk per trade (max 2% of capital)
# 5. Risk-reward ratio (min 2:1)
# 6. Daily loss limit (max 6%)
# 7. Open positions count

is_valid, errors = validator.validate_order(order_data)
if not is_valid:
    raise ValidationError(f"Order validation failed: {errors}")
```

### Risk Management Rules

**NEVER violate these limits:**
- ✅ Max risk per trade: **2% of account balance**
- ✅ Max open positions: **5 simultaneous trades**
- ✅ Min risk-reward ratio: **2:1** (preferably 3:1)
- ✅ Max daily loss: **6% of account balance**
- ✅ Stop-loss: **ALWAYS set** (no exceptions)
- ✅ Kill switch: **Auto-triggers** at daily loss limit

---

## 📚 Key Files & Entry Points

### Main Application
- `run_dashboard.py` - **Start here** - Launches Flask dashboard
- `src/dashboard/app.py` - Flask app with all routes (325+ lines)
- `config/config.yaml` - Main configuration file
- `config/secrets.env` - API credentials (create from .example)

### Pattern Detection
- `src/analysis/candlestick_patterns.py` - 50+ candlestick patterns
- `src/analysis/chart_patterns.py` - 16 chart patterns (1000+ lines)
- `src/analysis/technical_indicators.py` - Technical indicators

### Order Management System (OMS)
- `backend/oms/order_manager.py` - Order creation & execution
- `backend/oms/position_manager.py` - Position tracking & P&L
- `backend/oms/pre_trade_validator.py` - 7 validation checks
- `backend/oms/real_time_monitor.py` - Risk monitoring & kill switch

### Strategies
- `src/strategies/base_strategy.py` - Base strategy class
- `src/strategies/ema_crossover.py` - EMA crossover (12/26)
- `src/strategies/rsi_strategy.py` - RSI-based entry/exit
- `src/strategies/breakout.py` - Support/resistance breakouts

### Backtesting
- `src/backtest/backtest_engine.py` - Core backtest engine (500+ lines)
- `src/backtest/strategy_runner.py` - High-level strategy interface
- `src/backtest/performance_metrics.py` - 20+ performance metrics
- `src/backtest/cli.py` - Command-line interface
- `src/backtest/README.md` - Complete backtesting documentation

### Database
- `backend/database/database.py` - PostgreSQL with asyncpg
- Tables: orders, positions, trades, strategies, user_profiles, reconciliation_log, kill_switch_events

---

## 🛠️ Debugging & Troubleshooting

### Common Issues & Solutions

**Issue: "Port 5000 already in use"**
```bash
# Solution 1: Kill existing process
lsof -ti:5000 | xargs kill -9

# Solution 2: Use different port
FLASK_RUN_PORT=5001 python run_dashboard.py
```

**Issue: "Module not found" errors**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

**Issue: Database connection fails**
```bash
# Check PostgreSQL is running
psql -l

# Create database if missing
createdb scalping_bot

# Test connection
psql -d scalping_bot -c "SELECT version();"
```

**Issue: TA-Lib installation fails**
```bash
# macOS
brew install ta-lib
pip install TA-Lib

# Ubuntu/Debian
sudo apt-get install ta-lib
pip install TA-Lib

# Windows
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib-0.4.XX-cpXX-cpXX-win_amd64.whl
```

---

## 📊 Performance Metrics

### Current System Status
- **Test Pass Rate:** 100% (38/38 tests)
- **Components Operational:** 13/13 major components
- **Production Ready:** ✅ YES
- **Known Issues:** 0 blocking issues

### Performance Characteristics
- Flask app startup: < 1 second
- Database init: < 2 seconds
- OMS init: < 500ms
- Strategy load: < 100ms each
- API response time: < 200ms (typical)

---

## 🎯 System Architecture

### Component Overview

**1. Flask Dashboard** (`src/dashboard/`)
- 24+ HTML templates
- Real-time updates via AJAX
- CSRF protection, rate limiting
- Session management

**2. Order Management System** (`backend/oms/`)
- **OrderManager**: Order creation, validation, broker integration
- **PositionManager**: Position aggregation, P&L tracking
- **PreTradeValidator**: 7 risk validation checks
- **RealTimeMonitor**: Position monitoring, kill switch

**3. Pattern Detection** (`src/analysis/`)
- **CandlestickPatternDetector**: 50+ patterns with confidence scoring
- **ChartPatternDetector**: 16 classical chart patterns
- **TechnicalIndicators**: EMA, RSI, MACD, Bollinger Bands, ATR, etc.

**4. Backtesting Engine** (`src/backtest/`)
- No external dependencies (no backtrader required)
- Complete OHLCV simulation
- Stop-loss & target execution
- 20+ performance metrics

**5. Broker Integration** (`src/brokers/`)
- Zerodha Kite Connect (primary)
- Angel One SmartAPI
- Kotak Securities
- Factory pattern for broker selection

**6. Database Layer** (`backend/database/`)
- PostgreSQL with asyncpg
- Connection pooling (5-20 configurable)
- 7+ tables with full CRUD operations

---

## 📞 Documentation

### User Documentation
- **USER_GUIDE.md** - Complete 50-page user manual
- **HELP_AND_FAQ.md** - Interactive help with 25+ FAQs
- **QUICKSTART.md** - 5-minute setup guide
- **src/backtest/README.md** - Backtesting documentation

### Access Help in Dashboard
- Navigate to http://localhost:5000/help
- Interactive search functionality
- Step-by-step guides for all features
- FAQ with expandable sections

---

## ⚠️ Important Warnings

### NEVER Commit These
```bash
# Add to .gitignore:
config/secrets.env        # API credentials
*.log                     # Log files
__pycache__/             # Python cache
*.pyc                    # Compiled Python
.pytest_cache/           # Pytest cache
results/*.json           # Backtest results
logs/*.log               # Application logs
.DS_Store                # macOS files
```

### ALWAYS Ask Before
1. **Deploying strategies to LIVE trading** → Real money at risk
2. **Modifying database schema** → Could break production
3. **Changing validation rules** → Could bypass safety checks
4. **Updating broker API calls** → Could break order execution
5. **Modifying risk limits** → Could increase exposure

---

## 🎉 Quick Start

```bash
# 1. Clone repository
git clone <repository_url>
cd scalping-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets
cp config/secrets.env.example config/secrets.env
# Edit config/secrets.env with your API keys

# 4. Create database
createdb scalping_bot

# 5. Start dashboard
python run_dashboard.py

# 6. Open browser
open http://localhost:5000

# 7. Start with paper trading!
# Select "Paper Trading" mode in dashboard
```

---

## 🤖 Current Implementation Status

**Phase 1: Core Infrastructure** ✅ COMPLETE
- [x] Flask dashboard (24+ templates)
- [x] Database layer (PostgreSQL + asyncpg)
- [x] Configuration management
- [x] Security (CSRF, rate limiting, sessions)

**Phase 2: Trading System** ✅ COMPLETE
- [x] Order Management System (4 modules)
- [x] Position tracking & P&L
- [x] Pre-trade validation (7 checks)
- [x] Risk monitoring & kill switch
- [x] Multi-broker support (3 brokers)

**Phase 3: Pattern Recognition** ✅ COMPLETE
- [x] 50+ candlestick patterns
- [x] 16 chart patterns
- [x] Technical indicators
- [x] Confidence scoring

**Phase 4: Strategy & Backtesting** ✅ COMPLETE
- [x] 3 built-in strategies
- [x] Backtesting engine (no dependencies)
- [x] 20+ performance metrics
- [x] CLI interface

**Phase 5: Documentation** ✅ COMPLETE
- [x] User guide (50+ pages)
- [x] Interactive help system
- [x] FAQ (25+ questions)
- [x] Quick start guide

**Overall Status: 100% PRODUCTION-READY**

---

*Last updated: October 31, 2025*
*Maintained by: Development Team*
*System Status: ✅ All tests passing, 0 blocking issues, Production-ready*
