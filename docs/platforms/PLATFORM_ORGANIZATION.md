# Platform Organization & Documentation

This directory contains organized documentation for all 50+ supported platforms, including CSV formats, API integrations, and credential management.

---

## 📁 Directory Structure

```
/docs/platforms/
├── PLATFORM_ORGANIZATION.md        ← You are here
├── PLATFORMS_README.md              ← Complete platform list & capabilities
├── PLATFORM_INTEGRATION_PLAN.md    ← Integration roadmap & compliance
│
├── csv-formats/                     ← CSV export formats per platform
│   ├── poshmark/
│   │   ├── README.md               ← Format specification
│   │   ├── sample.csv              ← Sample file
│   │   └── UPLOAD_INSTRUCTIONS.md
│   ├── bonanza/
│   ├── ebay/
│   ├── mercari/
│   └── .../
│
├── api-integrations/                ← API documentation & setup
│   ├── ebay/
│   │   ├── README.md               ← API setup & usage
│   │   ├── AUTHENTICATION.md       ← OAuth flow
│   │   └── EXAMPLES.md             ← Code examples
│   ├── etsy/
│   ├── shopify/
│   ├── tcgplayer/
│   └── .../
│
└── credentials/                     ← Credential management docs
    ├── poshmark/
    │   └── README.md               ← Auth setup & security
    ├── ebay/
    ├── etsy/
    └── .../
```

---

## 🎯 Integration Types

### Type 1: API Integrations ✅ (Fully Automated)

**Platforms:** eBay, Etsy, Shopify, WooCommerce, TCGplayer, Depop, Square, Pinterest

**Capabilities:**
- ✅ Direct API posting
- ✅ Real-time inventory sync
- ✅ Order management
- ✅ Automated status updates
- ✅ Connection testing

**Setup:**
1. Get API credentials from platform
2. Configure in Settings → Platform Integrations
3. Run connection test: `python scripts/test_platform_connections.py <platform>`
4. Start posting!

**Documentation:**
- `/docs/platforms/api-integrations/<platform>/README.md`
- `/docs/platforms/credentials/<platform>/README.md`

---

### Type 2: CSV Bulk Upload ✅ (Semi-Automated)

**Platforms:** Poshmark, Bonanza, Ecrater, Ruby Lane, OfferUp, Grailed, Mercari

**Capabilities:**
- ✅ Automated CSV generation
- ✅ Format validation
- ⚠️ Manual upload to platform required
- ⚠️ Manual inventory sync

**Workflow:**
1. Create listings in Rebel Operator
2. Export to platform-specific CSV: Listings → Export → [Platform] CSV
3. Upload CSV to platform's bulk upload tool
4. Manually update status when sold

**Documentation:**
- `/docs/platforms/csv-formats/<platform>/README.md`
- `/docs/platforms/csv-formats/<platform>/sample.csv`

---

### Type 3: Product Feeds ✅ (Automated Catalog Sync)

**Platforms:** Facebook Shops, Google Shopping

**Capabilities:**
- ✅ Automated feed generation
- ✅ Catalog synchronization
- ✅ Auto-updates on change
- ✅ Multi-product management

**Setup:**
1. Generate product feed
2. Upload to platform's catalog system
3. Platform auto-syncs from feed URL

---

### Type 4: Templates ⚠️ (Manual Only)

**Platforms:** Craigslist, Nextdoor, VarageSale, Chairish

**Capabilities:**
- ✅ Template generation
- ⚠️ Manual copy/paste required
- ❌ No automation (TOS prohibits it)

**Workflow:**
1. Generate listing template
2. Copy/paste into platform's form
3. Manual management

---

## 🔐 Credential Storage

All credentials are stored securely in the `marketplace_credentials` table.

### Database Schema

```sql
CREATE TABLE marketplace_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    username TEXT,                 -- Encrypted
    password TEXT,                 -- Encrypted
    credentials_json TEXT,         -- Encrypted (for API keys, tokens, etc.)
    credential_type TEXT,          -- 'username_password', 'api_key', 'oauth_token'
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, platform)
);
```

### Credential Types

| Type | Platforms | Fields |
|------|-----------|--------|
| **username_password** | Poshmark, Mercari, Grailed | username, password |
| **api_key** | Etsy, TCGplayer | api_key, shop_id (optional) |
| **oauth_token** | eBay, Shopify, Facebook | client_id, client_secret, refresh_token |
| **api_credentials** | WooCommerce | consumer_key, consumer_secret, store_url |

### Security Features

- ✅ **Encryption at rest** - All credentials encrypted in database
- ✅ **HTTPS only** - All API calls over secure connections
- ✅ **Scope limiting** - Only request necessary permissions
- ✅ **Auto-expiration** - Tokens refreshed automatically
- ✅ **Access control** - Users can only access their own credentials
- ✅ **Audit logging** - All credential access logged

---

## 🧪 Connection Testing

### Test All Platforms

```bash
python scripts/test_platform_connections.py
```

### Test Specific Platform

```bash
python scripts/test_platform_connections.py ebay
python scripts/test_platform_connections.py shopify etsy
```

### Test for Specific User

```bash
python scripts/test_platform_connections.py --user-id 1
```

### What Gets Tested

**API Platforms:**
- ✅ OAuth token refresh
- ✅ API connectivity
- ✅ Account verification
- ✅ Permission validation

**CSV Platforms:**
- ✅ Credential format validation
- ⚠️ Manual login required for full test

---

## 📊 Platform Status Dashboard

### Fully Integrated (API) - 8 Platforms

| Platform | Status | Automation | Docs |
|----------|--------|------------|------|
| eBay | ✅ Live | Full | [API Docs](api-integrations/ebay/README.md) |
| Etsy | ✅ Live | Full | [API Docs](api-integrations/etsy/README.md) |
| Shopify | ✅ Live | Full | [API Docs](api-integrations/shopify/README.md) |
| WooCommerce | ✅ Live | Full | [API Docs](api-integrations/woocommerce/README.md) |
| TCGplayer | ✅ Live | Full | [API Docs](api-integrations/tcgplayer/README.md) |
| Depop | ⚠️ API Approval | Pending | [API Docs](api-integrations/depop/README.md) |
| Square | ✅ Live | Full | [API Docs](api-integrations/square/README.md) |
| Pinterest | ✅ Live | Catalog | [API Docs](api-integrations/pinterest/README.md) |

### CSV Export Supported - 20+ Platforms

| Platform | CSV Format | Sample | Docs |
|----------|------------|--------|------|
| Poshmark | ✅ | [Sample](csv-formats/poshmark/sample.csv) | [Format](csv-formats/poshmark/README.md) |
| Bonanza | ✅ | [Sample](csv-formats/bonanza/sample.csv) | [Format](csv-formats/bonanza/README.md) |
| Mercari | ✅ | [Sample](csv-formats/mercari/sample.csv) | [Format](csv-formats/mercari/README.md) |
| Grailed | ✅ | [Sample](csv-formats/grailed/sample.csv) | [Format](csv-formats/grailed/README.md) |
| OfferUp | ✅ | [Sample](csv-formats/offerup/sample.csv) | [Format](csv-formats/offerup/README.md) |
| ... | ... | ... | ... |

---

## 🔄 Inventory Synchronization

### How It Works

1. **Create Listing:**
   - Create listing in Rebel Operator
   - Choose platforms to publish to
   - Click "Publish to All Platforms"

2. **Automated Publishing:**
   - API platforms: Posted immediately
   - CSV platforms: CSV generated for download
   - Feed platforms: Added to product feed

3. **Status Tracking:**
   - Each platform tracks status independently
   - Database stores: `pending`, `active`, `failed`, `sold`, `cancelled`

4. **Cross-Platform Cancellation:**
   - When item sells on one platform
   - 15-minute cooldown period
   - Automatically cancels on other platforms
   - Updates inventory quantities

### Database Schema

```sql
CREATE TABLE platform_listings (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    platform_listing_id TEXT,      -- Platform's ID for this listing
    platform_url TEXT,             -- Direct URL to listing
    status TEXT,                   -- pending, active, failed, sold, cancelled
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_synced TIMESTAMP,
    cancel_scheduled_at TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
);
```

---

## 📝 CSV Format Standards

All CSV formats follow these standards:

### Common Fields

| Field | Type | Required | Max Length |
|-------|------|----------|------------|
| Title | String | Yes | Platform-specific |
| Description | String/HTML | Yes | Platform-specific |
| Price | Decimal | Yes | - |
| Quantity | Integer | Yes | - |
| Condition | Enum | Yes | Platform-specific |
| SKU | String | Optional | 50 |
| Brand | String | Optional | 100 |
| Category | String | Yes | Platform-specific |
| Images | URLs | Yes | 1-16 images |

### Condition Mapping

Each platform has its own condition terminology. Our system automatically maps:

| Internal | eBay | Poshmark | Grailed | TCGplayer |
|----------|------|----------|---------|-----------|
| new_with_tags | New with tags (1000) | New with tags | New/Never Worn | Near Mint |
| new_without_tags | New other (1500) | New without tags | New | Near Mint |
| excellent | Used (3000) | Like new | Gently Used | Lightly Played |
| good | Used (3000) | Good | Used | Moderately Played |
| fair | Used (3000) | Fair | Well Worn | Heavily Played |
| poor | For parts (7000) | Poor | Damaged | Damaged |

### Image Format Requirements

| Platform | Min Size | Recommended | Max Count | Format |
|----------|----------|-------------|-----------|--------|
| eBay | 500x500 | 1600x1600 | 12 | JPG, PNG |
| Poshmark | 400x400 | 1200x1200 | 8 | JPG, PNG |
| Etsy | 570x570 | 2000x2000 | 10 | JPG, PNG, GIF |
| Grailed | 600x800 | 1200x1600 | 8 | JPG, PNG |
| TCGplayer | 300x300 | 800x800 | 8 | JPG, PNG |

---

## 🚀 Quick Start Guide

### 1. Add Platform Credentials

```bash
# Via Web UI:
Settings → Platform Integrations → Choose Platform → Configure

# Or via API:
POST /api/settings/platform-credentials
{
    "platform": "ebay",
    "credentials": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "refresh_token": "your_refresh_token"
    }
}
```

### 2. Test Connection

```bash
python scripts/test_platform_connections.py ebay
```

### 3. Create & Publish Listing

```bash
# Via Web UI:
Listings → Create New → Fill Form → Publish to All Platforms

# Or via API:
POST /api/publish
{
    "listing_id": 123,
    "platforms": ["ebay", "etsy", "shopify"]
}
```

### 4. Monitor Status

```bash
# Check platform_listings table
SELECT * FROM platform_listings WHERE listing_id = 123;

# Or via Web UI:
Listings → View Listing → Platform Status
```

---

## 🛠️ Troubleshooting

### Common Issues

#### "Invalid Credentials" Error

**API Platforms:**
- Verify API keys are correct
- Check token hasn't expired
- Run connection test script
- Regenerate tokens if needed

**CSV Platforms:**
- Credentials are for CSV generation only
- Actual login happens on platform website
- Verify credentials by logging in manually

#### "CSV Upload Failed"

- Check CSV format matches platform requirements
- Verify all required fields are present
- Check image URLs are accessible
- Review platform's error message

#### "Connection Timeout"

- Check internet connection
- Verify platform API is not down
- Try again in a few minutes
- Check rate limits

#### "Rate Limit Exceeded"

- API platforms have daily/hourly limits
- Wait before retrying
- Check platform documentation for limits
- Upgrade to higher tier if needed

---

## 📚 Additional Resources

### Official Platform Documentation

- **eBay:** https://developer.ebay.com
- **Etsy:** https://developers.etsy.com
- **Shopify:** https://shopify.dev
- **WooCommerce:** https://woocommerce.github.io/woocommerce-rest-api-docs/
- **TCGplayer:** https://docs.tcgplayer.com

### Internal Documentation

- `/src/adapters/` - Platform adapter implementations
- `/src/csv_exporters/` - CSV generation code
- `/src/publisher/` - Publishing orchestration
- `/src/sync/` - Inventory synchronization

### Scripts & Tools

- `/scripts/test_platform_connections.py` - Connection testing
- `/scripts/test_ollama.py` - AI analyzer testing
- `/src/database/db.py` - Database schema

---

## 📞 Support

### Getting Help

1. **Check documentation** in this folder
2. **Run connection test** to diagnose issues
3. **Check platform's official docs** for API changes
4. **Review error logs** in application logs

### Contributing

To add a new platform:

1. Create folder in `csv-formats/` or `api-integrations/`
2. Add README.md with format/API documentation
3. Create sample CSV (if applicable)
4. Add adapter in `/src/adapters/`
5. Add connection test in `/scripts/test_platform_connections.py`
6. Update this document

---

## ✅ Compliance Checklist

All integrations are 100% TOS-compliant:

- ✅ API integrations use official APIs only
- ✅ CSV uploads are manual (where required by TOS)
- ✅ No automated scraping or bot activity
- ✅ Rate limits respected with backoff
- ✅ OAuth flows follow platform requirements
- ✅ User consent required for all integrations
- ✅ Data privacy and security maintained

---

**Last Updated:** 2026-01-21
**Platforms Supported:** 50+
**Fully Automated:** 8 platforms
**CSV Export:** 20+ platforms
