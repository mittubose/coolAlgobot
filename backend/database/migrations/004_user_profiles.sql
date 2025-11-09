-- Migration 004: User Profiles System
-- Add support for multiple user profiles and broker accounts
-- Date: October 26, 2025

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    default_broker VARCHAR(50) DEFAULT 'zerodha',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(email)
);

-- Create broker_accounts table (links profiles to portfolios)
CREATE TABLE IF NOT EXISTS broker_accounts (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER REFERENCES user_profiles(id) ON DELETE CASCADE,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    broker VARCHAR(50) NOT NULL,
    account_number VARCHAR(50),
    account_name VARCHAR(100),
    is_default BOOLEAN DEFAULT false,
    api_key VARCHAR(255),
    access_token TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_profile_id, broker, account_number)
);

-- Add user_profile_id to portfolios table
ALTER TABLE portfolios
ADD COLUMN IF NOT EXISTS user_profile_id INTEGER REFERENCES user_profiles(id) ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_broker_accounts_user_profile ON broker_accounts(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_broker_accounts_portfolio ON broker_accounts(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_broker_accounts_broker ON broker_accounts(broker);
CREATE INDEX IF NOT EXISTS idx_portfolios_user_profile ON portfolios(user_profile_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_profile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_profile_timestamp
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_user_profile_timestamp();

CREATE TRIGGER trigger_update_broker_account_timestamp
BEFORE UPDATE ON broker_accounts
FOR EACH ROW
EXECUTE FUNCTION update_user_profile_timestamp();

-- Insert default user profile
INSERT INTO user_profiles (name, email, default_broker, is_active)
VALUES ('Default User', NULL, 'zerodha', true)
ON CONFLICT (email) DO NOTHING;

-- Link existing portfolios to default user profile
UPDATE portfolios
SET user_profile_id = (SELECT id FROM user_profiles WHERE name = 'Default User' LIMIT 1)
WHERE user_profile_id IS NULL;

-- Create default broker account for existing Zerodha portfolio
INSERT INTO broker_accounts (user_profile_id, portfolio_id, broker, account_name, is_default, is_active)
SELECT
    (SELECT id FROM user_profiles WHERE name = 'Default User' LIMIT 1),
    id,
    broker,
    name,
    true,
    true
FROM portfolios
WHERE broker = 'zerodha' AND id = 1
ON CONFLICT (user_profile_id, broker, account_number) DO NOTHING;

-- Add comments
COMMENT ON TABLE user_profiles IS 'User profiles for the trading system';
COMMENT ON TABLE broker_accounts IS 'Broker account mappings to portfolios';
COMMENT ON COLUMN broker_accounts.api_key IS 'Encrypted API key for broker integration';
COMMENT ON COLUMN broker_accounts.access_token IS 'Encrypted access token for broker API';
