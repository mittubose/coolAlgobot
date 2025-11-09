-- =====================================================
-- Migration 003: Portfolio Import & Tracking System
-- =====================================================
-- Date: October 26, 2025
-- Purpose: Multi-portfolio management with CSV import,
--          real-time P&L calculation, FIFO trade matching,
--          and risk scoring
-- =====================================================

-- ==================== PORTFOLIOS TABLE ====================
-- Stores portfolio metadata (Zerodha, Upstox, Manual, etc.)
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(20) DEFAULT 'stocks', -- stocks, forex, crypto, commodities
    broker VARCHAR(50), -- zerodha, upstox, icici, manual
    account_number VARCHAR(50),
    initial_capital DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    current_value DECIMAL(15, 2) DEFAULT 0.00,
    total_invested DECIMAL(15, 2) DEFAULT 0.00,
    total_withdrawn DECIMAL(15, 2) DEFAULT 0.00,
    realized_pnl DECIMAL(15, 2) DEFAULT 0.00,
    unrealized_pnl DECIMAL(15, 2) DEFAULT 0.00,
    total_pnl DECIMAL(15, 2) DEFAULT 0.00,
    total_return_pct DECIMAL(8, 4) DEFAULT 0.0000, -- Percentage return

    -- Status tracking
    status VARCHAR(20) DEFAULT 'active', -- active, closed, archived
    is_primary BOOLEAN DEFAULT false, -- Primary portfolio for user

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_import_at TIMESTAMP,
    last_calculated_at TIMESTAMP
);

-- Indexes for fast lookups
CREATE INDEX idx_portfolios_status ON portfolios(status);
CREATE INDEX idx_portfolios_broker ON portfolios(broker);


-- ==================== PORTFOLIO_TRADES TABLE ====================
-- Stores all buy/sell transactions (imported from CSV or manual)
-- Note: Separate from 'trades' table (used by OMS)
CREATE TABLE IF NOT EXISTS portfolio_trades (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Trade details
    symbol VARCHAR(20) NOT NULL, -- RELIANCE, INFY, SBIN, etc.
    exchange VARCHAR(20), -- NSE, BSE, MCX, etc.
    trade_date DATE NOT NULL,
    trade_time TIME,

    -- Action and quantity
    action VARCHAR(10) NOT NULL, -- BUY, SELL
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(12, 4) NOT NULL CHECK (price > 0),

    -- Fees and charges
    brokerage DECIMAL(10, 2) DEFAULT 0.00,
    stt DECIMAL(10, 2) DEFAULT 0.00, -- Securities Transaction Tax
    exchange_charges DECIMAL(10, 2) DEFAULT 0.00,
    gst DECIMAL(10, 2) DEFAULT 0.00,
    sebi_charges DECIMAL(10, 2) DEFAULT 0.00,
    stamp_duty DECIMAL(10, 2) DEFAULT 0.00,
    total_charges DECIMAL(10, 2) DEFAULT 0.00,

    -- Trade value
    gross_value DECIMAL(15, 2), -- quantity * price
    net_value DECIMAL(15, 2), -- gross_value ± total_charges

    -- P&L (calculated for SELL trades)
    realized_pnl DECIMAL(15, 2),

    -- Import metadata
    import_source VARCHAR(50), -- zerodha_csv, upstox_csv, manual, api
    import_batch_id VARCHAR(100), -- Group imports together
    order_id VARCHAR(50), -- Broker order ID
    trade_id VARCHAR(50), -- Broker trade ID

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('BUY', 'SELL'))
);

-- Indexes for fast queries
CREATE INDEX idx_portfolio_trades_portfolio_id ON portfolio_trades(portfolio_id);
CREATE INDEX idx_portfolio_trades_symbol ON portfolio_trades(symbol);
CREATE INDEX idx_portfolio_trades_trade_date ON portfolio_trades(trade_date);
CREATE INDEX idx_portfolio_trades_action ON portfolio_trades(action);
CREATE INDEX idx_portfolio_trades_import_batch ON portfolio_trades(import_batch_id);
CREATE INDEX idx_portfolio_trades_symbol_date ON portfolio_trades(portfolio_id, symbol, trade_date);


-- ==================== HOLDINGS TABLE ====================
-- Current positions (real-time calculated from trades)
CREATE TABLE IF NOT EXISTS holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Symbol details
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20),

    -- Position details
    quantity INT NOT NULL CHECK (quantity >= 0),
    avg_buy_price DECIMAL(12, 4) NOT NULL, -- FIFO average price
    total_invested DECIMAL(15, 2), -- quantity * avg_buy_price

    -- Current market data
    current_price DECIMAL(12, 4),
    current_value DECIMAL(15, 2), -- quantity * current_price

    -- P&L metrics
    unrealized_pnl DECIMAL(15, 2), -- current_value - total_invested
    unrealized_pnl_pct DECIMAL(8, 4), -- (unrealized_pnl / total_invested) * 100
    day_change DECIMAL(15, 2), -- Today's price change impact
    day_change_pct DECIMAL(8, 4),

    -- Risk metrics
    weight DECIMAL(5, 4), -- Position size as % of portfolio (0.0000-1.0000)

    -- Metadata
    first_buy_date DATE,
    last_buy_date DATE,
    last_updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_portfolio_symbol UNIQUE(portfolio_id, symbol)
);

-- Indexes for fast lookups
CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id);
CREATE INDEX idx_holdings_symbol ON holdings(symbol);
CREATE INDEX idx_holdings_weight ON holdings(weight DESC); -- For concentration checks


-- ==================== PORTFOLIO SNAPSHOTS TABLE ====================
-- Daily/hourly snapshots for performance tracking
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Snapshot timestamp
    snapshot_date DATE NOT NULL,
    snapshot_time TIME DEFAULT '15:30:00', -- Market close time

    -- Portfolio value metrics
    total_value DECIMAL(15, 2) NOT NULL,
    total_invested DECIMAL(15, 2),
    cash_balance DECIMAL(15, 2) DEFAULT 0.00,

    -- P&L metrics
    realized_pnl DECIMAL(15, 2) DEFAULT 0.00,
    unrealized_pnl DECIMAL(15, 2) DEFAULT 0.00,
    total_pnl DECIMAL(15, 2),
    total_return_pct DECIMAL(8, 4),

    -- Daily change
    day_pnl DECIMAL(15, 2),
    day_return_pct DECIMAL(8, 4),

    -- Risk metrics
    volatility DECIMAL(8, 4), -- Historical volatility
    max_drawdown DECIMAL(8, 4), -- From peak
    sharpe_ratio DECIMAL(6, 3),

    -- Holdings count
    total_holdings INT DEFAULT 0,

    -- Metadata (JSONB for flexibility)
    top_gainers JSONB, -- [{symbol, pnl, pct}, ...]
    top_losers JSONB,
    sector_allocation JSONB, -- {technology: 30%, finance: 25%, ...}
    risk_score DECIMAL(3, 2), -- 0.00-10.00 (Risk meter)

    -- Unique constraint (one snapshot per day)
    CONSTRAINT unique_portfolio_snapshot UNIQUE(portfolio_id, snapshot_date)
);

-- Indexes for time-series queries
CREATE INDEX idx_snapshots_portfolio_id ON portfolio_snapshots(portfolio_id);
CREATE INDEX idx_snapshots_date ON portfolio_snapshots(snapshot_date DESC);


-- ==================== PORTFOLIO TRANSACTIONS TABLE ====================
-- Cash deposits/withdrawals tracking
CREATE TABLE IF NOT EXISTS portfolio_transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Transaction details
    transaction_type VARCHAR(20) NOT NULL, -- DEPOSIT, WITHDRAWAL
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    transaction_date DATE NOT NULL,

    -- Description
    description TEXT,
    reference_number VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraint
    CONSTRAINT valid_transaction_type CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAWAL'))
);

CREATE INDEX idx_portfolio_transactions_portfolio_id ON portfolio_transactions(portfolio_id);


-- ==================== IMPORT HISTORY TABLE ====================
-- Track CSV import jobs
CREATE TABLE IF NOT EXISTS import_history (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- Import details
    import_batch_id VARCHAR(100) NOT NULL UNIQUE,
    filename VARCHAR(255),
    broker VARCHAR(50), -- zerodha, upstox, generic
    import_type VARCHAR(20), -- csv, excel, api

    -- Import stats
    total_rows INT DEFAULT 0,
    success_rows INT DEFAULT 0,
    failed_rows INT DEFAULT 0,
    skipped_rows INT DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,

    -- Date range of imported trades
    start_date DATE,
    end_date DATE,

    -- Metadata
    imported_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Store failed rows for review
    failed_records JSONB
);

CREATE INDEX idx_import_history_portfolio_id ON import_history(portfolio_id);
CREATE INDEX idx_import_history_status ON import_history(status);


-- ==================== TRIGGERS ====================

-- Update portfolios.updated_at on changes
CREATE OR REPLACE FUNCTION update_portfolio_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_portfolio_timestamp
BEFORE UPDATE ON portfolios
FOR EACH ROW
EXECUTE FUNCTION update_portfolio_timestamp();

-- Update portfolio_trades.updated_at on changes
CREATE TRIGGER trigger_update_portfolio_trade_timestamp
BEFORE UPDATE ON portfolio_trades
FOR EACH ROW
EXECUTE FUNCTION update_portfolio_timestamp();


-- ==================== VIEWS ====================

-- Portfolio summary view (fast query)
CREATE OR REPLACE VIEW portfolio_summary AS
SELECT
    p.id,
    p.name,
    p.type,
    p.broker,
    p.current_value,
    p.total_invested,
    p.total_pnl,
    p.total_return_pct,
    p.status,
    COUNT(DISTINCT h.id) as holdings_count,
    COUNT(DISTINCT t.id) as trades_count,
    MAX(t.trade_date) as last_trade_date,
    p.created_at,
    p.updated_at
FROM portfolios p
LEFT JOIN holdings h ON h.portfolio_id = p.id AND h.quantity > 0
LEFT JOIN portfolio_trades t ON t.portfolio_id = p.id
GROUP BY p.id;


-- ==================== INITIAL DATA ====================

-- Default portfolio for quick setup
INSERT INTO portfolios (name, description, type, broker, initial_capital, status)
VALUES
    ('Zerodha Main', 'Primary Zerodha trading account', 'stocks', 'zerodha', 100000.00, 'active')
ON CONFLICT (name) DO NOTHING;


-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Tables created:
--   1. portfolios (multi-portfolio support)
--   2. portfolio_trades (all buy/sell transactions)
--   3. holdings (current positions, FIFO-calculated)
--   4. portfolio_snapshots (daily performance tracking)
--   5. portfolio_transactions (cash deposits/withdrawals)
--   6. import_history (CSV import tracking)
--
-- Views created:
--   1. portfolio_summary (fast portfolio overview)
--
-- Next steps:
--   - Create CSV import parser (Python)
--   - Build portfolio API endpoints (Flask)
--   - Implement P&L calculation engine (FIFO)
--   - Create import wizard UI (React)
-- =====================================================
