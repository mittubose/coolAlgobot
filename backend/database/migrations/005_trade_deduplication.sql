-- Migration 005: Trade Deduplication Support
-- Add trade hash column for duplicate detection
-- Date: October 26, 2025

-- Add trade_hash column to portfolio_trades
ALTER TABLE portfolio_trades
ADD COLUMN IF NOT EXISTS trade_hash VARCHAR(64);

-- Create index on trade_hash for fast lookup
CREATE INDEX IF NOT EXISTS idx_portfolio_trades_hash ON portfolio_trades(trade_hash);

-- Create composite index for duplicate detection
CREATE INDEX IF NOT EXISTS idx_portfolio_trades_duplicate_check
ON portfolio_trades(portfolio_id, symbol, trade_date, trade_type);

-- Add comments
COMMENT ON COLUMN portfolio_trades.trade_hash IS 'SHA256 hash for duplicate detection';

-- Create function to generate trade hash (optional, for database-level hashing)
CREATE OR REPLACE FUNCTION generate_trade_hash(
    p_symbol VARCHAR,
    p_trade_date DATE,
    p_trade_type VARCHAR,
    p_quantity DECIMAL,
    p_price DECIMAL,
    p_order_id VARCHAR
) RETURNS VARCHAR AS $$
BEGIN
    RETURN encode(
        digest(
            CONCAT(
                UPPER(p_symbol), '|',
                p_trade_date::TEXT, '|',
                UPPER(p_trade_type), '|',
                p_quantity::TEXT, '|',
                p_price::TEXT, '|',
                COALESCE(p_order_id, '')
            ),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION generate_trade_hash IS 'Generate SHA256 hash for trade deduplication';
