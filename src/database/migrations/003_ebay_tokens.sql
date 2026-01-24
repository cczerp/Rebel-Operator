-- Migration: eBay OAuth Tokens Storage
-- Description: Creates table for storing eBay OAuth tokens with encryption support
-- Date: 2026-01-24

-- Create ebay_tokens table
CREATE TABLE IF NOT EXISTS ebay_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- OAuth tokens (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,

    -- Token metadata
    expires_at TIMESTAMP NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',

    -- Environment tracking
    environment VARCHAR(20) NOT NULL DEFAULT 'sandbox', -- 'sandbox' or 'production'

    -- Scopes granted
    scopes TEXT, -- JSON array of granted scopes

    -- eBay user info (optional, for display)
    ebay_user_id VARCHAR(255),
    ebay_username VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key to users table
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Ensure one active connection per user per environment
    UNIQUE(user_id, environment)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_ebay_tokens_user_id ON ebay_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_ebay_tokens_expires_at ON ebay_tokens(expires_at);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ebay_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ebay_tokens_updated_at
    BEFORE UPDATE ON ebay_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_ebay_tokens_updated_at();

-- Comments for documentation
COMMENT ON TABLE ebay_tokens IS 'Stores eBay OAuth tokens for Inventory API access';
COMMENT ON COLUMN ebay_tokens.access_token IS 'Encrypted eBay access token (valid for 2 hours)';
COMMENT ON COLUMN ebay_tokens.refresh_token IS 'Encrypted eBay refresh token (valid for 18 months)';
COMMENT ON COLUMN ebay_tokens.expires_at IS 'When the access token expires (UTC)';
COMMENT ON COLUMN ebay_tokens.environment IS 'sandbox or production environment';
COMMENT ON COLUMN ebay_tokens.scopes IS 'JSON array of OAuth scopes granted';
