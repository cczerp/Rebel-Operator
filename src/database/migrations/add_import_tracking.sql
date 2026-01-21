-- Migration: Add import tracking fields to listings table
-- Date: 2026-01-21
-- Description: Add fields to track listings imported from external platforms

-- Add platform_source field (which platform this was imported from)
ALTER TABLE listings
ADD COLUMN IF NOT EXISTS platform_source TEXT;

-- Add original_platform_listing_id (the listing ID on the original platform)
ALTER TABLE listings
ADD COLUMN IF NOT EXISTS original_platform_listing_id TEXT;

-- Add imported_at timestamp
ALTER TABLE listings
ADD COLUMN IF NOT EXISTS imported_at TIMESTAMP;

-- Add index for faster duplicate checking
CREATE INDEX IF NOT EXISTS idx_listings_platform_source_id
ON listings(platform_source, original_platform_listing_id)
WHERE platform_source IS NOT NULL;

-- Add index for SKU lookups (for deduplication)
CREATE INDEX IF NOT EXISTS idx_listings_sku
ON listings(sku)
WHERE sku IS NOT NULL;

-- Add comment
COMMENT ON COLUMN listings.platform_source IS 'Platform this listing was imported from (ebay, poshmark, etc.)';
COMMENT ON COLUMN listings.original_platform_listing_id IS 'Original listing ID on the source platform';
COMMENT ON COLUMN listings.imported_at IS 'Timestamp when listing was imported into Rebel Operator';
