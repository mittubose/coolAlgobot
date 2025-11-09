-- Strategy Library System Migration
-- Adds: backtest_results, strategy_ratings, strategy_usage tables
-- Extends: strategies table with library features

-- Extend strategies table
ALTER TABLE strategies
ADD COLUMN IF NOT EXISTS category VARCHAR(50),
ADD COLUMN IF NOT EXISTS tags TEXT[],
ADD COLUMN IF NOT EXISTS complexity VARCHAR(20) DEFAULT 'intermediate',
ADD COLUMN IF NOT EXISTS timeframe VARCHAR(10),
ADD COLUMN IF NOT EXISTS asset_class VARCHAR(20) DEFAULT 'stocks',
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0.0';

-- Backtest results
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_id INT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(12, 2) NOT NULL,
    total_return DECIMAL(8, 4),
    sharpe_ratio DECIMAL(6, 3),
    max_drawdown DECIMAL(8, 4),
    win_rate DECIMAL(5, 4),
    profit_factor DECIMAL(6, 3),
    total_trades INT,
    equity_curve JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Strategy ratings
CREATE TABLE IF NOT EXISTS strategy_ratings (
    id SERIAL PRIMARY KEY,
    strategy_id INT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(strategy_id, user_id)
);

-- Strategy usage tracking
CREATE TABLE IF NOT EXISTS strategy_usage (
    id SERIAL PRIMARY KEY,
    strategy_id INT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id INT NOT NULL,
    total_runs INT DEFAULT 0,
    user_total_pnl DECIMAL(12, 2) DEFAULT 0,
    first_used_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    UNIQUE(strategy_id, user_id)
);

COMMIT;
