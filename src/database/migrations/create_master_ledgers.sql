-- ============================================================================
-- MASTER LEDGER SYSTEM - Database Schema
-- ============================================================================
-- Creates 4 separate ledgers with clean separation of concerns:
-- 1. Inventory Master Ledger (what you own)
-- 2. Sales & Revenue Ledger (financial transactions)
-- 3. Shipping & Fulfillment Ledger (logistics)
-- 4. Draft Listings Ledger (pre-publication prep)
--
-- Date: 2026-01-21
-- ============================================================================

-- ============================================================================
-- 1️⃣ INVENTORY MASTER LEDGER
-- ============================================================================
-- Purpose: Canonical list of assets (items you own)
-- This is the source of truth for physical inventory

CREATE TABLE IF NOT EXISTS inventory_master (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- Identity
    master_item_id TEXT UNIQUE NOT NULL,        -- Canonical ID (e.g., "INV-2024-001")
    sku TEXT,                                    -- Internal SKU / barcode

    -- Item details
    title TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    model TEXT,
    color TEXT,
    size TEXT,
    condition TEXT,                              -- Standardized condition

    -- Inventory tracking
    quantity INTEGER DEFAULT 1,
    storage_location TEXT,                       -- Physical location (e.g., "Shelf A-3")
    status TEXT DEFAULT 'available',             -- available, listed, sold, archived

    -- Financial
    cost_basis DECIMAL(10,2),                   -- What you paid for it
    currency TEXT DEFAULT 'USD',

    -- Platform mapping (JSON)
    platform_listing_ids TEXT,                   -- JSON: {"ebay": "123", "poshmark": "456"}

    -- Images
    photos TEXT,                                 -- JSON array of photo URLs

    -- Metadata
    notes TEXT,
    acquired_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    CONSTRAINT unique_master_item_id UNIQUE(master_item_id)
);

CREATE INDEX idx_inventory_user_id ON inventory_master(user_id);
CREATE INDEX idx_inventory_sku ON inventory_master(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_inventory_status ON inventory_master(status);
CREATE INDEX idx_inventory_storage ON inventory_master(storage_location) WHERE storage_location IS NOT NULL;

COMMENT ON TABLE inventory_master IS 'Master inventory ledger - canonical source of truth for all items owned';
COMMENT ON COLUMN inventory_master.master_item_id IS 'Unique identifier for this inventory item (e.g., INV-2024-001)';
COMMENT ON COLUMN inventory_master.status IS 'Inventory status: available, listed, sold, archived';
COMMENT ON COLUMN inventory_master.platform_listing_ids IS 'JSON map of platform to listing ID';


-- ============================================================================
-- 2️⃣ SALES & REVENUE LEDGER
-- ============================================================================
-- Purpose: Track money movement (cleanly, accountant-safe)
-- No inventory logic - ONLY economics

CREATE TABLE IF NOT EXISTS sales_ledger (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- Identity
    transaction_id TEXT UNIQUE NOT NULL,         -- e.g., "TXN-2024-001"
    master_item_id TEXT REFERENCES inventory_master(master_item_id),

    -- Platform details
    platform TEXT NOT NULL,                      -- ebay, poshmark, mercari, etc.
    platform_order_id TEXT,                      -- Platform's order/transaction ID
    platform_listing_id TEXT,                    -- Platform's listing ID

    -- Dates
    sale_date TIMESTAMP NOT NULL,
    payout_date TIMESTAMP,

    -- Money (all amounts in same currency)
    currency TEXT DEFAULT 'USD',
    gross_sale_amount DECIMAL(10,2) NOT NULL,   -- What buyer paid
    platform_fees DECIMAL(10,2) DEFAULT 0,       -- eBay/Poshmark fees
    payment_processing_fees DECIMAL(10,2) DEFAULT 0,  -- PayPal/Stripe fees
    shipping_cost DECIMAL(10,2) DEFAULT 0,       -- What you paid for shipping
    shipping_charged DECIMAL(10,2) DEFAULT 0,    -- What buyer paid for shipping
    tax_collected DECIMAL(10,2) DEFAULT 0,       -- Sales tax collected
    net_payout DECIMAL(10,2),                    -- What hit your bank account

    -- Profit calculation (optional but helpful)
    cost_basis DECIMAL(10,2),                    -- What you paid for the item
    profit DECIMAL(10,2),                        -- net_payout - cost_basis - shipping_cost

    -- Buyer info (optional, for support)
    buyer_username TEXT,
    buyer_location TEXT,

    -- Status
    payout_status TEXT DEFAULT 'pending',        -- pending, paid, disputed, refunded

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_user_id ON sales_ledger(user_id);
CREATE INDEX idx_sales_master_item_id ON sales_ledger(master_item_id);
CREATE INDEX idx_sales_platform ON sales_ledger(platform);
CREATE INDEX idx_sales_date ON sales_ledger(sale_date);
CREATE INDEX idx_sales_payout_date ON sales_ledger(payout_date) WHERE payout_date IS NOT NULL;
CREATE INDEX idx_sales_transaction_id ON sales_ledger(transaction_id);

COMMENT ON TABLE sales_ledger IS 'Sales & revenue ledger - financial transactions only, no inventory logic';
COMMENT ON COLUMN sales_ledger.net_payout IS 'Amount that actually hit your bank account';
COMMENT ON COLUMN sales_ledger.profit IS 'Calculated profit: net_payout - cost_basis - shipping_cost';


-- ============================================================================
-- 3️⃣ SHIPPING & FULFILLMENT LEDGER
-- ============================================================================
-- Purpose: Log logistics independently from sales
-- For tracking, disputes, lost package resolution

CREATE TABLE IF NOT EXISTS shipping_ledger (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- Identity
    shipment_id TEXT UNIQUE NOT NULL,            -- e.g., "SHIP-2024-001"
    master_item_id TEXT REFERENCES inventory_master(master_item_id),
    transaction_id TEXT REFERENCES sales_ledger(transaction_id),

    -- Carrier details
    carrier TEXT NOT NULL,                       -- USPS, UPS, FedEx, DHL, etc.
    service_type TEXT,                           -- Priority, Ground, Express, etc.
    tracking_number TEXT,
    label_source TEXT,                           -- stamps.com, pirateship, platform, etc.

    -- Dates
    label_created_date DATE,
    ship_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,

    -- Costs
    shipping_cost DECIMAL(10,2),                -- What you paid
    insurance_cost DECIMAL(10,2) DEFAULT 0,
    currency TEXT DEFAULT 'USD',

    -- Package details
    weight_oz DECIMAL(6,2),                     -- Package weight in ounces
    dimensions TEXT,                             -- "10x8x6" or JSON
    package_type TEXT,                           -- flat, box, padded, etc.

    -- Delivery status
    delivery_status TEXT DEFAULT 'pending',      -- pending, in_transit, delivered, failed, returned
    delivery_proof TEXT,                         -- Signature, photo, etc.

    -- Issues & resolution
    issue_reported BOOLEAN DEFAULT FALSE,
    issue_type TEXT,                             -- lost, damaged, delayed, etc.
    issue_resolution TEXT,
    insurance_claim_filed BOOLEAN DEFAULT FALSE,
    claim_amount DECIMAL(10,2),

    -- Addresses (for disputes)
    ship_to_address TEXT,
    ship_from_address TEXT,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipping_user_id ON shipping_ledger(user_id);
CREATE INDEX idx_shipping_master_item_id ON shipping_ledger(master_item_id);
CREATE INDEX idx_shipping_transaction_id ON shipping_ledger(transaction_id);
CREATE INDEX idx_shipping_tracking ON shipping_ledger(tracking_number) WHERE tracking_number IS NOT NULL;
CREATE INDEX idx_shipping_carrier ON shipping_ledger(carrier);
CREATE INDEX idx_shipping_status ON shipping_ledger(delivery_status);
CREATE INDEX idx_shipping_date ON shipping_ledger(ship_date);

COMMENT ON TABLE shipping_ledger IS 'Shipping & fulfillment ledger - logistics tracking independent of sales';
COMMENT ON COLUMN shipping_ledger.delivery_status IS 'Shipment status: pending, in_transit, delivered, failed, returned';


-- ============================================================================
-- 4️⃣ DRAFT LISTINGS LEDGER ⭐
-- ============================================================================
-- Purpose: Prepare listings BEFORE they exist on any platform
-- The holy grail for zero-rework exports

CREATE TABLE IF NOT EXISTS draft_listings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- Identity
    draft_id TEXT UNIQUE NOT NULL,               -- e.g., "DRAFT-2024-001"
    master_item_id TEXT REFERENCES inventory_master(master_item_id),

    -- Target platform
    target_platforms TEXT,                       -- JSON array: ["ebay", "poshmark", "mercari"]
    primary_platform TEXT,                       -- Which platform to optimize for

    -- Core listing fields
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    quantity INTEGER DEFAULT 1,
    condition TEXT,

    -- Categorization
    category TEXT,
    subcategory TEXT,

    -- Item specifics
    brand TEXT,
    model TEXT,
    size TEXT,
    color TEXT,
    material TEXT,

    -- Images
    photos TEXT,                                 -- JSON array of photo URLs/paths
    primary_photo_index INTEGER DEFAULT 0,

    -- SEO & keywords
    keywords TEXT,                               -- JSON array
    search_terms TEXT,                           -- JSON array

    -- Shipping details
    shipping_price DECIMAL(10,2),
    shipping_service TEXT,
    ships_from_location TEXT,
    handling_time_days INTEGER,

    -- Returns
    returns_accepted BOOLEAN DEFAULT TRUE,
    return_period_days INTEGER DEFAULT 30,

    -- Platform-specific requirements
    platform_requirements TEXT,                  -- JSON: per-platform required fields status
    completeness_score INTEGER,                  -- 0-100% how complete this draft is

    -- AI enhancement
    ai_enhanced BOOLEAN DEFAULT FALSE,
    ai_provider TEXT,
    ai_enhancement_date TIMESTAMP,

    -- Status & workflow
    status TEXT DEFAULT 'draft',                 -- draft, ready, published, archived
    ready_for_platforms TEXT,                    -- JSON array: ["ebay", "poshmark"] (which platforms this is ready for)

    -- Publishing history
    published_to_platforms TEXT,                 -- JSON: {"ebay": {"id": "123", "date": "2024-01-21"}}

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

CREATE INDEX idx_drafts_user_id ON draft_listings(user_id);
CREATE INDEX idx_drafts_master_item_id ON draft_listings(master_item_id);
CREATE INDEX idx_drafts_status ON draft_listings(status);
CREATE INDEX idx_drafts_target_platforms ON draft_listings USING gin(to_tsvector('english', target_platforms));
CREATE INDEX idx_drafts_completeness ON draft_listings(completeness_score);

COMMENT ON TABLE draft_listings IS 'Draft listings ledger - prepare listings before platform publication';
COMMENT ON COLUMN draft_listings.completeness_score IS 'Percentage (0-100) of required fields completed';
COMMENT ON COLUMN draft_listings.ready_for_platforms IS 'JSON array of platforms this draft is ready to publish to';
COMMENT ON COLUMN draft_listings.platform_requirements IS 'JSON map of platform-specific required field statuses';


-- ============================================================================
-- RELATIONSHIPS & CONSTRAINTS
-- ============================================================================

-- Add foreign key from existing listings table to inventory_master (optional migration)
-- ALTER TABLE listings ADD COLUMN master_item_id TEXT REFERENCES inventory_master(master_item_id);

-- Ensure transaction_id is unique
ALTER TABLE sales_ledger ADD CONSTRAINT unique_transaction_id UNIQUE(transaction_id);

-- Ensure shipment_id is unique
ALTER TABLE shipping_ledger ADD CONSTRAINT unique_shipment_id UNIQUE(shipment_id);

-- Ensure draft_id is unique
ALTER TABLE draft_listings ADD CONSTRAINT unique_draft_id UNIQUE(draft_id);


-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to generate sequential master_item_id
CREATE OR REPLACE FUNCTION generate_master_item_id(user_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    seq_num INTEGER;
    item_id TEXT;
BEGIN
    year_part := TO_CHAR(CURRENT_DATE, 'YYYY');

    -- Get next sequence number for this user this year
    SELECT COALESCE(MAX(
        CAST(SUBSTRING(master_item_id FROM 'INV-\d{4}-(\d+)') AS INTEGER)
    ), 0) + 1
    INTO seq_num
    FROM inventory_master
    WHERE user_id = user_id_param
      AND master_item_id LIKE 'INV-' || year_part || '-%';

    item_id := 'INV-' || year_part || '-' || LPAD(seq_num::TEXT, 4, '0');
    RETURN item_id;
END;
$$ LANGUAGE plpgsql;

-- Function to generate transaction_id
CREATE OR REPLACE FUNCTION generate_transaction_id(user_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    seq_num INTEGER;
    txn_id TEXT;
BEGIN
    year_part := TO_CHAR(CURRENT_DATE, 'YYYY');

    SELECT COALESCE(MAX(
        CAST(SUBSTRING(transaction_id FROM 'TXN-\d{4}-(\d+)') AS INTEGER)
    ), 0) + 1
    INTO seq_num
    FROM sales_ledger
    WHERE user_id = user_id_param
      AND transaction_id LIKE 'TXN-' || year_part || '-%';

    txn_id := 'TXN-' || year_part || '-' || LPAD(seq_num::TEXT, 4, '0');
    RETURN txn_id;
END;
$$ LANGUAGE plpgsql;

-- Function to generate shipment_id
CREATE OR REPLACE FUNCTION generate_shipment_id(user_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    seq_num INTEGER;
    ship_id TEXT;
BEGIN
    year_part := TO_CHAR(CURRENT_DATE, 'YYYY');

    SELECT COALESCE(MAX(
        CAST(SUBSTRING(shipment_id FROM 'SHIP-\d{4}-(\d+)') AS INTEGER)
    ), 0) + 1
    INTO seq_num
    FROM shipping_ledger
    WHERE user_id = user_id_param
      AND shipment_id LIKE 'SHIP-' || year_part || '-%';

    ship_id := 'SHIP-' || year_part || '-' || LPAD(seq_num::TEXT, 4, '0');
    RETURN ship_id;
END;
$$ LANGUAGE plpgsql;

-- Function to generate draft_id
CREATE OR REPLACE FUNCTION generate_draft_id(user_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    seq_num INTEGER;
    draft_id_result TEXT;
BEGIN
    year_part := TO_CHAR(CURRENT_DATE, 'YYYY');

    SELECT COALESCE(MAX(
        CAST(SUBSTRING(draft_id FROM 'DRAFT-\d{4}-(\d+)') AS INTEGER)
    ), 0) + 1
    INTO seq_num
    FROM draft_listings
    WHERE user_id = user_id_param
      AND draft_id LIKE 'DRAFT-' || year_part || '-%';

    draft_id_result := 'DRAFT-' || year_part || '-' || LPAD(seq_num::TEXT, 4, '0');
    RETURN draft_id_result;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- Complete inventory view (joins master with current sales/shipping status)
CREATE OR REPLACE VIEW inventory_complete AS
SELECT
    i.*,
    s.sale_date,
    s.platform AS sold_platform,
    s.gross_sale_amount AS sold_price,
    s.net_payout,
    sh.tracking_number,
    sh.delivery_status,
    sh.carrier
FROM inventory_master i
LEFT JOIN sales_ledger s ON i.master_item_id = s.master_item_id
LEFT JOIN shipping_ledger sh ON s.transaction_id = sh.transaction_id;

-- Profit summary view
CREATE OR REPLACE VIEW profit_summary AS
SELECT
    user_id,
    platform,
    DATE_TRUNC('month', sale_date) AS month,
    COUNT(*) AS num_sales,
    SUM(gross_sale_amount) AS total_revenue,
    SUM(platform_fees + payment_processing_fees) AS total_fees,
    SUM(shipping_cost) AS total_shipping_costs,
    SUM(net_payout) AS total_payout,
    SUM(profit) AS total_profit,
    AVG(profit) AS avg_profit_per_sale
FROM sales_ledger
WHERE payout_status = 'paid'
GROUP BY user_id, platform, DATE_TRUNC('month', sale_date);

-- Draft readiness view
CREATE OR REPLACE VIEW draft_readiness AS
SELECT
    user_id,
    status,
    target_platforms,
    COUNT(*) AS num_drafts,
    AVG(completeness_score) AS avg_completeness,
    COUNT(*) FILTER (WHERE completeness_score >= 90) AS ready_to_publish
FROM draft_listings
GROUP BY user_id, status, target_platforms;


-- ============================================================================
-- GRANTS (Optional - adjust per your security model)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_master TO authenticated_users;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sales_ledger TO authenticated_users;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON shipping_ledger TO authenticated_users;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON draft_listings TO authenticated_users;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN sales_ledger.platform_fees IS 'Platform fees (eBay, Poshmark, etc.)';
COMMENT ON COLUMN sales_ledger.payment_processing_fees IS 'PayPal, Stripe, etc. fees';
COMMENT ON COLUMN shipping_ledger.label_source IS 'Where you bought the label (stamps.com, pirateship, platform)';
COMMENT ON COLUMN draft_listings.target_platforms IS 'JSON array of platforms you plan to publish to';
COMMENT ON COLUMN draft_listings.published_to_platforms IS 'JSON map of platform to {id, date} when published';
