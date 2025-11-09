-- XCoin Scalping Bot - Database Schema
-- Version: 1.0
-- Created: October 25, 2025
-- Purpose: Production-ready schema for Order Management System

-- ============================================================================
-- DROP EXISTING TABLES (for clean setup)
-- ============================================================================

DROP TABLE IF EXISTS reconciliation_log CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS strategies CASCADE;
DROP TABLE IF EXISTS kill_switch_events CASCADE;
DROP TABLE IF EXISTS daily_stats CASCADE;

-- ============================================================================
-- STRATEGIES TABLE
-- ============================================================================

CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- e.g., 'hammer_rsi', 'double_bottom'
    description TEXT,

    -- Configuration
    config JSONB NOT NULL,  -- Strategy-specific parameters

    -- State
    status VARCHAR(20) NOT NULL DEFAULT 'INACTIVE',  -- ACTIVE, INACTIVE, PAUSED
    mode VARCHAR(20) NOT NULL DEFAULT 'PAPER',       -- PAPER, LIVE

    -- Performance
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    losing_trades INT DEFAULT 0,
    total_pnl DECIMAL(12, 2) DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deployed_at TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'PAUSED', 'ERROR')),
    CONSTRAINT valid_mode CHECK (mode IN ('PAPER', 'LIVE'))
);

CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_strategies_mode ON strategies(mode);

-- ============================================================================
-- ORDERS TABLE
-- ============================================================================

CREATE TABLE orders (
    -- Primary identifiers
    id SERIAL PRIMARY KEY,
    broker_order_id VARCHAR(50) UNIQUE,     -- Zerodha's order ID
    strategy_id INT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,

    -- Order details
    symbol VARCHAR(20) NOT NULL,            -- e.g., "RELIANCE", "TCS"
    exchange VARCHAR(10) NOT NULL,          -- e.g., "NSE", "BSE"
    side VARCHAR(4) NOT NULL,               -- "BUY" or "SELL"
    quantity INT NOT NULL CHECK (quantity > 0),
    order_type VARCHAR(10) NOT NULL,        -- "MARKET", "LIMIT", "SL", "SL-M"
    price DECIMAL(10, 2),                   -- Limit price (NULL for market orders)
    trigger_price DECIMAL(10, 2),           -- Stop-loss trigger price
    product VARCHAR(10) NOT NULL,           -- "MIS" (intraday), "CNC" (delivery)
    validity VARCHAR(10) NOT NULL,          -- "DAY", "IOC"

    -- Risk parameters
    stop_loss DECIMAL(10, 2),               -- Stop-loss price
    take_profit DECIMAL(10, 2),             -- Take-profit price
    risk_amount DECIMAL(10, 2),             -- Calculated risk: (Entry - SL) * Qty
    risk_reward_ratio DECIMAL(5, 2),        -- RR ratio (e.g., 2.50 for 2.5:1)

    -- Order state
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    status_message TEXT,                    -- Details (e.g., rejection reason)
    filled_quantity INT DEFAULT 0,          -- Partially filled quantity
    average_price DECIMAL(10, 2),           -- Average fill price

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMP,                 -- When sent to broker
    updated_at TIMESTAMP,                   -- Last status update
    filled_at TIMESTAMP,                    -- When fully filled
    cancelled_at TIMESTAMP,                 -- When cancelled

    -- Validation & Audit
    validation_result JSONB,                -- Results of all pre-trade checks
    validation_warnings TEXT[],             -- Any warnings during validation
    error_message TEXT,                     -- Error if order failed

    -- Metadata
    metadata JSONB,                         -- Strategy-specific data, exit reasons, etc.

    -- Constraints
    CONSTRAINT valid_side CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT valid_order_type CHECK (order_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M')),
    CONSTRAINT valid_status CHECK (status IN ('PENDING', 'SUBMITTED', 'OPEN', 'FILLED', 'CANCELLED', 'REJECTED', 'FAILED')),
    CONSTRAINT valid_product CHECK (product IN ('MIS', 'CNC')),
    CONSTRAINT valid_validity CHECK (validity IN ('DAY', 'IOC'))
);

-- Indexes for fast lookups
CREATE INDEX idx_orders_broker_id ON orders(broker_order_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_strategy_id ON orders(strategy_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_filled_at ON orders(filled_at DESC) WHERE filled_at IS NOT NULL;

-- Index for finding active orders (for monitoring)
CREATE INDEX idx_orders_active ON orders(status)
    WHERE status IN ('SUBMITTED', 'OPEN');

-- ============================================================================
-- POSITIONS TABLE
-- ============================================================================

CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    strategy_id INT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,

    -- Position details
    quantity INT NOT NULL,                  -- Positive = long, Negative = short
    average_price DECIMAL(10, 2) NOT NULL,  -- Average entry price
    product VARCHAR(10) NOT NULL,           -- MIS or CNC

    -- PnL tracking
    realized_pnl DECIMAL(12, 2) DEFAULT 0,  -- Closed PnL
    unrealized_pnl DECIMAL(12, 2) DEFAULT 0,-- Open PnL (updated real-time)

    -- Risk management
    stop_loss DECIMAL(10, 2),               -- Position-level stop-loss
    take_profit DECIMAL(10, 2),             -- Position-level take-profit
    max_drawdown DECIMAL(10, 2),            -- Maximum adverse excursion
    time_based_sl_hours INT,                -- Auto-close after N hours

    -- Statistics
    entry_order_ids INT[],                  -- IDs of orders that opened this position
    exit_order_ids INT[],                   -- IDs of orders that closed this position
    highest_price DECIMAL(10, 2),           -- Highest price seen while holding
    lowest_price DECIMAL(10, 2),            -- Lowest price seen while holding

    -- Timestamps
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,

    -- Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT unique_position UNIQUE(symbol, exchange, strategy_id, product),
    CONSTRAINT valid_product CHECK (product IN ('MIS', 'CNC'))
);

CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_strategy_id ON positions(strategy_id);
CREATE INDEX idx_positions_open ON positions(closed_at) WHERE closed_at IS NULL;
CREATE INDEX idx_positions_closed ON positions(closed_at DESC) WHERE closed_at IS NOT NULL;

-- ============================================================================
-- TRADES TABLE (Fills)
-- ============================================================================

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    position_id INT REFERENCES positions(id) ON DELETE SET NULL,
    broker_trade_id VARCHAR(50) UNIQUE,     -- Zerodha's trade ID

    -- Trade details
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL,          -- Fill price

    -- Transaction costs
    brokerage DECIMAL(10, 4) DEFAULT 0,     -- Brokerage charged
    stt DECIMAL(10, 4) DEFAULT 0,           -- Securities Transaction Tax
    exchange_txn_charge DECIMAL(10, 4) DEFAULT 0,
    gst DECIMAL(10, 4) DEFAULT 0,           -- GST on brokerage + charges
    stamp_duty DECIMAL(10, 4) DEFAULT 0,
    sebi_charges DECIMAL(10, 4) DEFAULT 0,
    total_charges DECIMAL(10, 4) DEFAULT 0, -- Sum of all above

    -- Net calculation
    gross_value DECIMAL(12, 2),             -- quantity * price
    net_value DECIMAL(12, 2),               -- gross_value +/- total_charges

    -- Timestamp
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB,

    CONSTRAINT valid_side CHECK (side IN ('BUY', 'SELL'))
);

CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_position_id ON trades(position_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_executed_at ON trades(executed_at DESC);
CREATE INDEX idx_trades_broker_id ON trades(broker_trade_id);

-- ============================================================================
-- RECONCILIATION LOG TABLE
-- ============================================================================

CREATE TABLE reconciliation_log (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,

    -- Mismatch details
    issue_type VARCHAR(50) NOT NULL,        -- UNKNOWN_POSITION, QUANTITY_MISMATCH, PHANTOM_POSITION
    severity VARCHAR(20) NOT NULL,          -- INFO, WARNING, CRITICAL

    internal_quantity INT,                  -- Our records
    broker_quantity INT,                    -- Broker's records
    difference INT,                         -- Difference

    internal_avg_price DECIMAL(10, 2),      -- Our average price
    broker_avg_price DECIMAL(10, 2),        -- Broker's average price

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT,                        -- How it was resolved
    auto_fixed BOOLEAN DEFAULT FALSE,       -- Was it auto-fixed by system?

    -- Timestamps
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,

    -- Metadata
    metadata JSONB,

    CONSTRAINT valid_issue_type CHECK (issue_type IN ('UNKNOWN_POSITION', 'QUANTITY_MISMATCH', 'PHANTOM_POSITION', 'PRICE_MISMATCH', 'OTHER')),
    CONSTRAINT valid_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL'))
);

CREATE INDEX idx_reconciliation_symbol ON reconciliation_log(symbol);
CREATE INDEX idx_reconciliation_unresolved ON reconciliation_log(resolved)
    WHERE resolved = FALSE;
CREATE INDEX idx_reconciliation_severity ON reconciliation_log(severity)
    WHERE severity = 'CRITICAL';
CREATE INDEX idx_reconciliation_detected_at ON reconciliation_log(detected_at DESC);

-- ============================================================================
-- KILL SWITCH EVENTS TABLE
-- ============================================================================

CREATE TABLE kill_switch_events (
    id SERIAL PRIMARY KEY,

    -- Event details
    reason VARCHAR(100) NOT NULL,           -- DAILY_LOSS_LIMIT_BREACHED, DRAWDOWN_LIMIT_BREACHED, MANUAL
    triggered_by VARCHAR(50),               -- SYSTEM or USER_ID

    -- State at trigger time
    account_balance DECIMAL(12, 2),
    today_pnl DECIMAL(12, 2),
    open_positions_count INT,
    positions_closed_count INT,

    -- Close results
    close_results JSONB,                    -- Array of close order results

    -- Timestamps
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    deactivated_at TIMESTAMP,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    -- Metadata
    metadata JSONB,

    CONSTRAINT valid_status CHECK (status IN ('ACTIVE', 'COMPLETED', 'DEACTIVATED', 'FAILED'))
);

CREATE INDEX idx_kill_switch_triggered_at ON kill_switch_events(triggered_at DESC);
CREATE INDEX idx_kill_switch_status ON kill_switch_events(status);

-- ============================================================================
-- DAILY STATS TABLE
-- ============================================================================

CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Trading stats
    total_orders INT DEFAULT 0,
    total_trades INT DEFAULT 0,
    filled_orders INT DEFAULT 0,
    cancelled_orders INT DEFAULT 0,
    rejected_orders INT DEFAULT 0,

    -- PnL
    gross_pnl DECIMAL(12, 2) DEFAULT 0,
    total_charges DECIMAL(12, 2) DEFAULT 0,
    net_pnl DECIMAL(12, 2) DEFAULT 0,

    -- Win/Loss
    winning_trades INT DEFAULT 0,
    losing_trades INT DEFAULT 0,
    win_rate DECIMAL(5, 2),                 -- Percentage

    -- Position stats
    max_positions_held INT DEFAULT 0,
    symbols_traded TEXT[],

    -- Risk metrics
    max_drawdown DECIMAL(12, 2),
    peak_balance DECIMAL(12, 2),

    -- Compliance
    order_to_trade_ratio DECIMAL(5, 2),
    kill_switch_triggered BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_daily_stats_date ON daily_stats(date DESC);

-- ============================================================================
-- VIEWS (for easy querying)
-- ============================================================================

-- Active positions with unrealized PnL
CREATE OR REPLACE VIEW v_active_positions AS
SELECT
    p.id,
    p.symbol,
    p.exchange,
    p.quantity,
    p.average_price,
    p.realized_pnl,
    p.unrealized_pnl,
    p.stop_loss,
    p.take_profit,
    p.opened_at,
    s.name as strategy_name,
    s.mode as strategy_mode
FROM positions p
JOIN strategies s ON p.strategy_id = s.id
WHERE p.closed_at IS NULL
ORDER BY p.opened_at DESC;

-- Today's orders summary
CREATE OR REPLACE VIEW v_today_orders AS
SELECT
    o.id,
    o.broker_order_id,
    o.symbol,
    o.side,
    o.quantity,
    o.order_type,
    o.price,
    o.status,
    o.created_at,
    o.filled_at,
    s.name as strategy_name
FROM orders o
JOIN strategies s ON o.strategy_id = s.id
WHERE DATE(o.created_at) = CURRENT_DATE
ORDER BY o.created_at DESC;

-- Unresolved reconciliation issues
CREATE OR REPLACE VIEW v_reconciliation_issues AS
SELECT
    id,
    symbol,
    exchange,
    issue_type,
    severity,
    internal_quantity,
    broker_quantity,
    difference,
    detected_at,
    EXTRACT(EPOCH FROM (NOW() - detected_at))/3600 as hours_unresolved
FROM reconciliation_log
WHERE resolved = FALSE
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'WARNING' THEN 2
        WHEN 'INFO' THEN 3
    END,
    detected_at DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update position unrealized PnL
CREATE OR REPLACE FUNCTION update_position_pnl(
    p_position_id INT,
    p_current_price DECIMAL(10, 2)
) RETURNS VOID AS $$
DECLARE
    v_quantity INT;
    v_avg_price DECIMAL(10, 2);
    v_unrealized_pnl DECIMAL(12, 2);
BEGIN
    -- Get position details
    SELECT quantity, average_price INTO v_quantity, v_avg_price
    FROM positions
    WHERE id = p_position_id;

    -- Calculate unrealized PnL
    IF v_quantity > 0 THEN
        -- Long position
        v_unrealized_pnl := v_quantity * (p_current_price - v_avg_price);
    ELSE
        -- Short position
        v_unrealized_pnl := ABS(v_quantity) * (v_avg_price - p_current_price);
    END IF;

    -- Update position
    UPDATE positions
    SET
        unrealized_pnl = v_unrealized_pnl,
        updated_at = NOW()
    WHERE id = p_position_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate today's PnL
CREATE OR REPLACE FUNCTION get_today_pnl()
RETURNS DECIMAL(12, 2) AS $$
DECLARE
    v_pnl DECIMAL(12, 2);
BEGIN
    SELECT COALESCE(SUM(net_value), 0) INTO v_pnl
    FROM trades
    WHERE DATE(executed_at) = CURRENT_DATE;

    RETURN v_pnl;
END;
$$ LANGUAGE plpgsql;

-- Function to get order-to-trade ratio
CREATE OR REPLACE FUNCTION get_order_to_trade_ratio()
RETURNS DECIMAL(5, 2) AS $$
DECLARE
    v_orders INT;
    v_trades INT;
    v_ratio DECIMAL(5, 2);
BEGIN
    SELECT COUNT(*) INTO v_orders
    FROM orders
    WHERE DATE(created_at) = CURRENT_DATE;

    SELECT COUNT(*) INTO v_trades
    FROM trades
    WHERE DATE(executed_at) = CURRENT_DATE;

    IF v_trades = 0 THEN
        RETURN 0;
    END IF;

    v_ratio := v_orders::DECIMAL / v_trades::DECIMAL;

    RETURN v_ratio;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_stats_updated_at
    BEFORE UPDATE ON daily_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-calculate gross_value and net_value on trades
CREATE OR REPLACE FUNCTION calculate_trade_values()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate gross value
    NEW.gross_value := NEW.quantity * NEW.price;

    -- Calculate total charges
    NEW.total_charges := COALESCE(NEW.brokerage, 0) +
                        COALESCE(NEW.stt, 0) +
                        COALESCE(NEW.exchange_txn_charge, 0) +
                        COALESCE(NEW.gst, 0) +
                        COALESCE(NEW.stamp_duty, 0) +
                        COALESCE(NEW.sebi_charges, 0);

    -- Calculate net value
    IF NEW.side = 'BUY' THEN
        NEW.net_value := NEW.gross_value + NEW.total_charges;  -- Buy costs more
    ELSE
        NEW.net_value := NEW.gross_value - NEW.total_charges;  -- Sell gets less
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_trade_values_trigger
    BEFORE INSERT OR UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION calculate_trade_values();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default strategy (for testing)
INSERT INTO strategies (name, type, description, config, status, mode)
VALUES (
    'Manual Trading',
    'manual',
    'Default strategy for manual orders',
    '{"risk_per_trade": 0.02, "max_positions": 5}'::jsonb,
    'ACTIVE',
    'PAPER'
);

-- Insert today's daily stats record (if not exists)
INSERT INTO daily_stats (date, created_at)
VALUES (CURRENT_DATE, NOW())
ON CONFLICT (date) DO NOTHING;

-- ============================================================================
-- GRANT PERMISSIONS (adjust based on your setup)
-- ============================================================================

-- If you have a specific database user, grant permissions
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO xcoin_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO xcoin_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO xcoin_user;

-- ============================================================================
-- SCHEMA INFORMATION
-- ============================================================================

COMMENT ON TABLE orders IS 'All trading orders (pending, submitted, filled, rejected)';
COMMENT ON TABLE positions IS 'Open and closed positions';
COMMENT ON TABLE trades IS 'Individual trade fills from order executions';
COMMENT ON TABLE reconciliation_log IS 'Position reconciliation issues between internal state and broker';
COMMENT ON TABLE kill_switch_events IS 'Emergency kill switch activation events';
COMMENT ON TABLE daily_stats IS 'Daily trading statistics and metrics';

COMMENT ON COLUMN orders.validation_result IS 'JSON object with results of all pre-trade validation checks';
COMMENT ON COLUMN positions.unrealized_pnl IS 'Updated in real-time as price changes';
COMMENT ON COLUMN trades.total_charges IS 'Sum of all transaction costs (brokerage, taxes, charges)';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Verify schema creation
SELECT 'Schema created successfully!' as status;

-- Show table sizes (will be 0 initially)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
