# Master Ledger System 📊

**The Four Pillars of Resale Business Management**

A complete separation-of-concerns architecture for managing inventory, sales, shipping, and draft listings.

---

## 🎯 Overview

Traditional listing systems mix everything together. This creates confusion, makes accounting difficult, and prevents clean exports. The Master Ledger System solves this with **4 independent ledgers**:

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER LEDGER SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣  INVENTORY MASTER        2️⃣  SALES & REVENUE            │
│      (What you own)                (Money tracking)          │
│      • MasterItemID                • TransactionID           │
│      • Physical location           • Platform fees           │
│      • Status tracking             • Net payouts             │
│      • Cost basis                  • Profit calculation      │
│                                                               │
│  3️⃣  SHIPPING & FULFILLMENT  4️⃣  DRAFT LISTINGS ⭐          │
│      (Logistics)                   (Pre-publication)         │
│      • Tracking numbers            • Platform-ready          │
│      • Carrier info                • Completeness score      │
│      • Delivery status             • Zero-rework exports     │
│      • Issue resolution            • AI enhancement          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 The Four Ledgers

### 1️⃣ **Inventory Master Ledger**
**Purpose:** Canonical source of truth for all items you own

**Key Concept:** This is NOT a list of listings. It's a list of **physical items**.

**Core Fields:**
```csv
MasterItemID, SKU, Title, Category, Brand, Model, Color, Size
Condition, Quantity, StorageLocation, Status, CostBasis, Currency
PlatformListingIDs, Photos, AcquiredDate
```

**Status Values:**
- `available` - In your possession, not listed
- `listed` - Currently listed on one or more platforms
- `sold` - Sold and shipped
- `archived` - No longer tracking

**Use Cases:**
- Inventory counting
- Storage organization
- Cost basis tracking
- Platform mapping

**Example:**
```csv
INV-2024-0001,NIKE-001,"Vintage Nike Swoosh Hoodie",Apparel,Nike,Vintage,Blue,L,excellent,1,Shelf-A3,listed,25.00,USD,"{\"ebay\": \"123\", \"poshmark\": \"456\"}","[\"img1.jpg\",\"img2.jpg\"]",2024-01-15
```

---

### 2️⃣ **Sales & Revenue Ledger**
**Purpose:** Track money movement (accountant-safe, tax-ready)

**Key Concept:** Only economics. NO inventory logic.

**Core Fields:**
```csv
TransactionID, MasterItemID, Platform, SaleDate, PayoutDate
GrossSaleAmount, PlatformFees, PaymentProcessingFees, ShippingCost
ShippingCharged, TaxCollected, NetPayout, CostBasis, Profit
```

**Automatic Calculations:**
```python
Profit = NetPayout - CostBasis - ShippingCost
```

**Use Cases:**
- Monthly profit tracking
- Platform comparison
- Tax preparation
- Payout reconciliation

**Example:**
```csv
TXN-2024-0001,INV-2024-0001,ebay,2024-01-20 14:30:00,2024-01-25 09:00:00,USD,45.00,6.75,1.50,8.50,10.00,0.00,38.25,25.00,4.75
```

**Key Insight:** Even if you sell the same item multiple times (reprints, copies), each gets its own `TransactionID`. The `MasterItemID` links back to the original inventory item.

---

### 3️⃣ **Shipping & Fulfillment Ledger**
**Purpose:** Log logistics independently from sales

**Key Concept:** Tracks HOW items moved, not WHY.

**Core Fields:**
```csv
ShipmentID, MasterItemID, TransactionID, Carrier, TrackingNumber
ShipDate, DeliveryDate, ShippingCost, DeliveryStatus
IssueReported, IssueType, InsuranceClaimFiled
```

**Delivery Statuses:**
- `pending` - Label created, not shipped
- `in_transit` - Package en route
- `delivered` - Successfully delivered
- `failed` - Delivery failed
- `returned` - Returned to sender

**Use Cases:**
- Tracking number lookup
- Lost package disputes
- Insurance claims
- Carrier performance analysis

**Example:**
```csv
SHIP-2024-0001,INV-2024-0001,TXN-2024-0001,USPS,Priority,9405511899564298765432,2024-01-21,2024-01-23,8.50,delivered,FALSE,,,
```

**Why Separate?** Sometimes you ship without selling (transfers, returns). Sometimes items sell without shipping (digital goods, local pickup). Keeping them separate maintains flexibility.

---

### 4️⃣ **Draft Listings Ledger** ⭐
**Purpose:** Prepare listings BEFORE they exist on any platform

**Key Concept:** The holy grail. Zero-rework, platform-ready listings.

**Core Fields:**
```csv
DraftID, MasterItemID, TargetPlatforms, Title, Description
Price, Condition, Category, Brand, Size, Color, Photos
Keywords, CompletenessScore, ReadyForPlatforms, Status
```

**Completeness Score:** 0-100% based on required fields for target platforms

**Target Platforms:** JSON array `["ebay", "poshmark", "mercari"]`

**Ready For Platforms:** JSON array of platforms this draft meets requirements for

**Platform Requirements:** JSON map showing which required fields are complete:
```json
{
  "ebay": {
    "title": true,
    "description": true,
    "price": true,
    "photos": true,
    "category": false  ← Missing!
  },
  "poshmark": {
    "title": true,
    "brand": true,
    ...
  }
}
```

**Use Cases:**
- AI-assisted listing prep
- Bulk listing workflows
- Platform-specific CSV translation
- Pre-publication review

**Example:**
```csv
DRAFT-2024-0001,INV-2024-0001,"[\"ebay\",\"poshmark\"]",ebay,"Vintage Nike Swoosh Hoodie","Great condition...",45.00,excellent,Apparel,Nike,L,Blue,"[\"img1.jpg\"]","[\"vintage\",\"nike\"]",85,"[\"poshmark\"]",draft
```

**The Workflow:**
1. **Create draft** from inventory item
2. **AI enhances** with descriptions, keywords
3. **Check completeness** for each platform
4. **Export platform-specific CSVs** when ready
5. **Track publishing** to platforms

---

## 🗄️ Database Schema

### Table Relationships

```
                    ┌──────────────────┐
                    │  inventory_master │
                    │  (What you own)   │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
       ┌────────▼──────┐ ┌──▼────────┐ ┌▼─────────────┐
       │ draft_listings │ │sales_ledger│ │draft_listings│
       │ (Pre-pub prep) │ │ (Money)    │ │(Pre-pub prep)│
       └────────────────┘ └──────┬─────┘ └──────────────┘
                                 │
                         ┌───────▼────────┐
                         │shipping_ledger │
                         │  (Logistics)   │
                         └────────────────┘
```

### Key Relationships:
- `draft_listings.master_item_id` → `inventory_master.master_item_id`
- `sales_ledger.master_item_id` → `inventory_master.master_item_id`
- `shipping_ledger.master_item_id` → `inventory_master.master_item_id`
- `shipping_ledger.transaction_id` → `sales_ledger.transaction_id`

### Migration

Run the migration to create all 4 ledgers:

```bash
psql $DATABASE_URL < src/database/migrations/create_master_ledgers.sql
```

This creates:
- 4 ledger tables
- Helper functions for ID generation
- Indexes for performance
- Convenience views (`inventory_complete`, `profit_summary`, `draft_readiness`)

---

## 📡 API Endpoints

### Export Endpoints

#### Export Single Ledger

```http
GET /api/ledgers/export/<ledger_type>?status=listed&platform=ebay
```

**Path Parameters:**
- `ledger_type`: `inventory`, `sales`, `shipping`, or `drafts`

**Query Parameters (vary by ledger):**

**Inventory:**
- `status`: available, listed, sold, archived
- `category`: Filter by category
- `storage_location`: Filter by location

**Sales:**
- `platform`: ebay, poshmark, etc.
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `payout_status`: pending, paid, disputed, refunded

**Shipping:**
- `carrier`: USPS, UPS, FedEx, etc.
- `delivery_status`: pending, in_transit, delivered, etc.
- `issue_reported`: true/false

**Drafts:**
- `status`: draft, ready, published, archived
- `primary_platform`: ebay, poshmark, etc.
- `min_completeness`: 0-100

**Response:** CSV file download

---

#### Export All Ledgers

```http
GET /api/ledgers/export/all
```

**Response:** ZIP file containing all 4 ledgers as separate CSVs

---

### Stats & Analysis

#### Get Ledger Statistics

```http
GET /api/ledgers/stats
```

**Response:**
```json
{
  "inventory": {
    "total_items": 150,
    "available": 45,
    "listed": 80,
    "sold": 25,
    "total_value": 4500.00
  },
  "sales": {
    "total_sales": 250,
    "total_revenue": 12500.00,
    "total_profit": 5600.00,
    "avg_profit_per_sale": 22.40
  },
  "shipping": {
    "total_shipments": 240,
    "in_transit": 5,
    "delivered": 230,
    "issues": 5
  },
  "drafts": {
    "total_drafts": 60,
    "ready_to_publish": 30,
    "avg_completeness": 75.5
  }
}
```

---

#### Profit by Platform

```http
GET /api/ledgers/sales/profit-by-platform?start_date=2024-01-01&end_date=2024-12-31
```

**Response:**
```json
{
  "ebay": {
    "revenue": 5000.00,
    "profit": 2000.00,
    "num_sales": 50
  },
  "poshmark": {
    "revenue": 3500.00,
    "profit": 1500.00,
    "num_sales": 40
  }
}
```

---

#### Monthly Profit Trend

```http
GET /api/ledgers/sales/monthly-profit?months=12
```

**Response:**
```json
[
  {"month": "2024-01", "revenue": 5000.00, "profit": 2000.00, "num_sales": 45},
  {"month": "2024-02", "revenue": 6000.00, "profit": 2500.00, "num_sales": 52},
  ...
]
```

---

### ID Generation

```http
GET /api/ledgers/generate-id/<id_type>
```

**Path Parameters:**
- `id_type`: `master_item`, `transaction`, `shipment`, or `draft`

**Response:**
```json
{"id": "INV-2024-0042"}
```

**ID Formats:**
- Master Item: `INV-YYYY-####`
- Transaction: `TXN-YYYY-####`
- Shipment: `SHIP-YYYY-####`
- Draft: `DRAFT-YYYY-####`

IDs are **sequential per user per year**.

---

## 💡 Usage Examples

### Scenario 1: Add New Inventory Item

```python
# 1. Generate master_item_id
GET /api/ledgers/generate-id/master_item
→ "INV-2024-0042"

# 2. Create inventory record
INSERT INTO inventory_master (
    user_id, master_item_id, title, category, brand,
    quantity, storage_location, status, cost_basis
) VALUES (
    1, 'INV-2024-0042', 'Vintage Nike Hoodie', 'Apparel', 'Nike',
    1, 'Shelf-A3', 'available', 25.00
);

# 3. Create draft listing
INSERT INTO draft_listings (
    user_id, draft_id, master_item_id, target_platforms,
    title, condition, price, status
) VALUES (
    1, 'DRAFT-2024-0042', 'INV-2024-0042', '["ebay", "poshmark"]',
    'Vintage Nike Hoodie Size L', 'excellent', 45.00, 'draft'
);
```

---

### Scenario 2: Item Sells on eBay

```python
# 1. Generate transaction_id
GET /api/ledgers/generate-id/transaction
→ "TXN-2024-0123"

# 2. Record sale
INSERT INTO sales_ledger (
    user_id, transaction_id, master_item_id, platform,
    sale_date, gross_sale_amount, platform_fees,
    shipping_cost, net_payout, cost_basis, profit
) VALUES (
    1, 'TXN-2024-0123', 'INV-2024-0042', 'ebay',
    NOW(), 45.00, 6.75, 8.50, 29.75, 25.00, 4.75
);

# 3. Update inventory status
UPDATE inventory_master
SET status = 'sold'
WHERE master_item_id = 'INV-2024-0042';

# 4. Generate shipment_id and record shipping
GET /api/ledgers/generate-id/shipment
→ "SHIP-2024-0123"

INSERT INTO shipping_ledger (
    user_id, shipment_id, master_item_id, transaction_id,
    carrier, tracking_number, ship_date, shipping_cost
) VALUES (
    1, 'SHIP-2024-0123', 'INV-2024-0042', 'TXN-2024-0123',
    'USPS', '9405511899564298765432', '2024-01-21', 8.50
);
```

---

### Scenario 3: Export for Tax Season

```bash
# Export sales ledger for tax year
curl -O "http://localhost:5000/api/ledgers/export/sales?start_date=2024-01-01&end_date=2024-12-31"
→ sales_ledger_20250121_143022.csv

# Contains all needed info for Schedule C:
# - Gross revenue
# - Platform fees (business expenses)
# - Shipping costs
# - Net income
# - Cost of goods sold
```

---

### Scenario 4: Bulk Create Drafts from Inventory

```python
# 1. Get all available inventory
SELECT master_item_id, title, brand, condition, cost_basis
FROM inventory_master
WHERE status = 'available' AND user_id = 1;

# 2. For each item, create draft
for item in available_items:
    draft_id = generate_draft_id()
    INSERT INTO draft_listings (
        draft_id, master_item_id, title, target_platforms,
        price, status
    ) VALUES (
        draft_id, item.master_item_id, item.title,
        '["ebay", "mercari"]',
        item.cost_basis * 2.5,  # 2.5x markup
        'draft'
    );

# 3. AI enhance all drafts
for draft in new_drafts:
    ai_enhance(draft)  # Adds description, keywords, photos

# 4. Export platform-specific CSVs when ready
GET /api/ledgers/export/drafts?status=ready&min_completeness=90
→ drafts_ledger_20250121_143022.csv
```

---

## 🎨 Frontend Integration

### Dashboard Widget

```html
<div class="ledger-stats-widget">
    <div class="stat">
        <h3>Inventory</h3>
        <p class="big-number">150</p>
        <small>80 listed · 45 available · 25 sold</small>
    </div>
    <div class="stat">
        <h3>Revenue (MTD)</h3>
        <p class="big-number">$6,420.00</p>
        <small>+12% vs last month</small>
    </div>
    <div class="stat">
        <h3>Profit (MTD)</h3>
        <p class="big-number">$2,840.00</p>
        <small>44% margin</small>
    </div>
    <div class="stat">
        <h3>Drafts Ready</h3>
        <p class="big-number">30</p>
        <small>60 total · 85% avg completeness</small>
    </div>
</div>
```

---

### Export All Button

```html
<button onclick="exportAllLedgers()">
    📊 Export All Ledgers (ZIP)
</button>

<script>
async function exportAllLedgers() {
    const response = await fetch('/api/ledgers/export/all');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ledgers_${new Date().toISOString().split('T')[0]}.zip`;
    a.click();
}
</script>
```

---

### Platform-Specific Draft Export

```html
<form onsubmit="exportDraftsFor(event)">
    <label>Platform:</label>
    <select id="platform">
        <option value="ebay">eBay</option>
        <option value="poshmark">Poshmark</option>
        <option value="mercari">Mercari</option>
    </select>

    <label>Min Completeness:</label>
    <input type="range" id="completeness" min="0" max="100" value="90">
    <span id="completeness-value">90%</span>

    <button type="submit">Export Ready Drafts</button>
</form>

<script>
async function exportDraftsFor(e) {
    e.preventDefault();
    const platform = document.getElementById('platform').value;
    const completeness = document.getElementById('completeness').value;

    window.location.href = `/api/ledgers/export/drafts?primary_platform=${platform}&min_completeness=${completeness}&status=ready`;
}
</script>
```

---

## 📊 Reports & Analytics

### Built-in Views

#### Inventory Complete View
Joins inventory with sales and shipping status:
```sql
SELECT * FROM inventory_complete
WHERE user_id = 1 AND status = 'sold';
```

Returns: `master_item_id, title, brand, sale_date, sold_price, net_payout, tracking_number, delivery_status`

---

#### Profit Summary View
Monthly profit by platform:
```sql
SELECT * FROM profit_summary
WHERE user_id = 1 AND month >= '2024-01-01';
```

Returns: `platform, month, num_sales, total_revenue, total_fees, total_payout, total_profit, avg_profit_per_sale`

---

#### Draft Readiness View
Draft completion status:
```sql
SELECT * FROM draft_readiness
WHERE user_id = 1;
```

Returns: `status, target_platforms, num_drafts, avg_completeness, ready_to_publish`

---

## 🔐 Security & Best Practices

### Data Isolation
- All queries filtered by `user_id`
- No cross-user data visibility
- Indexes optimize filtered queries

### ID Generation
- Sequential IDs per user per year
- Format: `PREFIX-YEAR-####`
- Prevents ID conflicts
- Year-based organization

### Financial Data
- All amounts stored as `DECIMAL(10,2)`
- Currency field for multi-currency support
- Automatic profit calculation
- Tax-ready exports

### Data Integrity
- Foreign key constraints
- Unique constraints on IDs
- Indexed lookups
- Transaction safety

---

## 🚀 Migration from Existing System

If you have existing listings in the old `listings` table:

```sql
-- Option 1: Migrate to inventory_master
INSERT INTO inventory_master (
    user_id, master_item_id, title, category, condition,
    quantity, status, photos, sku, cost
)
SELECT
    user_id,
    'INV-2024-' || LPAD(ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at)::TEXT, 4, '0'),
    title,
    category,
    condition,
    quantity,
    CASE status
        WHEN 'active' THEN 'listed'
        WHEN 'sold' THEN 'sold'
        ELSE 'available'
    END,
    photos,
    sku,
    cost
FROM listings;

-- Option 2: Link existing listings to new system
ALTER TABLE listings ADD COLUMN master_item_id TEXT REFERENCES inventory_master(master_item_id);
```

---

## 💡 Tips & Tricks

### Use Master Item IDs Everywhere
- Print labels with QR codes containing `master_item_id`
- Scan to lookup storage location
- Track item through entire lifecycle

### Draft First, Publish Later
- Create drafts for all inventory
- Let AI enhance in batch
- Export platform-specific CSVs when ready
- Zero manual rework

### Reconcile Payouts
- Export sales ledger monthly
- Compare `net_payout` to bank deposits
- Track pending vs paid status
- Catch missing payouts

### Storage Location Labels
- Use consistent format: `Shelf-Row-Position` (e.g., `A-3-2`)
- Sort exports by storage_location
- Pick in order for efficient fulfillment

### Track Cost Basis
- Always record cost_basis when acquiring inventory
- Automatic profit calculation
- Tax-deductible cost of goods sold
- ROI tracking

---

## 📞 Support

### Common Issues

**"Master item ID already exists"**
- Use `generate_master_item_id()` function
- Sequential IDs prevent duplicates

**"Transaction ID not found"**
- Ensure sale is recorded in `sales_ledger` first
- Then link shipment via `transaction_id`

**"Export shows no data"**
- Check filters are not too restrictive
- Verify user_id is correct
- Try export without filters first

---

## 🎯 What's Next?

With the Master Ledger System, you now have:

✅ **Clean data architecture**
✅ **Accountant-ready exports**
✅ **Platform-independent tracking**
✅ **Tax-season simplicity**
✅ **Zero-rework publishing**

**Recommended Next Steps:**

1. **Run migration** to create tables
2. **Import existing inventory** into `inventory_master`
3. **Create drafts** for available items
4. **AI enhance drafts** in bulk
5. **Export & publish** to platforms
6. **Track sales** in `sales_ledger`
7. **Generate monthly reports** for profit tracking

---

**Last Updated:** 2026-01-21
**Version:** 1.0
**Status:** ✅ Production Ready
