# eBay API Integration

## Overview

eBay has a **full API integration** supporting automated listing management.

**Integration Type:** API (REST)
**Automation Level:** Fully automated
**Connection Test:** OAuth token verification
**API Version:** eBay Trading API / Inventory API

---

## Integration Capabilities

### ✅ Fully Supported Features

| Feature | Status | API Endpoint |
|---------|--------|--------------|
| **Create Listings** | ✅ Automated | `POST /sell/inventory/v1/inventory_item` |
| **Update Listings** | ✅ Automated | `PUT /sell/inventory/v1/inventory_item/{sku}` |
| **Delete/End Listings** | ✅ Automated | `DELETE /sell/inventory/v1/inventory_item/{sku}` |
| **Inventory Sync** | ✅ Real-time | `GET /sell/inventory/v1/inventory_item` |
| **Order Management** | ✅ Automated | `GET /sell/fulfillment/v1/order` |
| **Shipping Updates** | ✅ Automated | `POST /sell/fulfillment/v1/order/{orderId}/shipping_fulfillment` |
| **Bulk Upload** | ✅ CSV Fallback | File Exchange API |

---

## Required Credentials

### Option 1: OAuth Tokens (Recommended)

| Credential | Type | Purpose | Expires |
|------------|------|---------|---------|
| **Client ID** | String | Application identifier | Never |
| **Client Secret** | String (encrypted) | Application secret | Never |
| **Refresh Token** | String (encrypted) | Generate access tokens | 18 months |
| **Access Token** | String (auto-generated) | API requests | 2 hours |

### Option 2: CSV Export (Fallback)

| Credential | Type | Purpose |
|------------|------|---------|
| **Username** | String | eBay username |
| **Password** | String (encrypted) | Account password (for CSV portal) |

---

## Setup Instructions

### Step 1: Create eBay Developer Account

1. Go to https://developer.ebay.com
2. Sign in with your eBay account
3. Click **Create an Application**
4. Fill out application details:
   - **Application Title:** Rebel Operator Integration
   - **Platform:** Production (or Sandbox for testing)
   - **Callback URL:** Your app's OAuth callback URL

5. **Grant Scopes:**
   Required scopes for full integration:
   ```
   https://api.ebay.com/oauth/api_scope/sell.inventory
   https://api.ebay.com/oauth/api_scope/sell.inventory.readonly
   https://api.ebay.com/oauth/api_scope/sell.marketing
   https://api.ebay.com/oauth/api_scope/sell.account
   https://api.ebay.com/oauth/api_scope/sell.fulfillment
   ```

### Step 2: Get OAuth Tokens

1. Copy **Client ID** and **Client Secret**
2. Generate **User Token**:
   ```bash
   # Authorization URL
   https://auth.ebay.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI&scope=https://api.ebay.com/oauth/api_scope/sell.inventory
   ```

3. Exchange authorization code for tokens:
   ```bash
   POST https://api.ebay.com/identity/v1/oauth2/token
   Content-Type: application/x-www-form-urlencoded
   Authorization: Basic base64(client_id:client_secret)

   grant_type=authorization_code&code=YOUR_AUTH_CODE&redirect_uri=YOUR_REDIRECT_URI
   ```

4. Save the **refresh_token** (valid for 18 months)

### Step 3: Configure in Rebel Operator

1. Go to **Settings** → **Platform Integrations**
2. Find **eBay** in the General Marketplaces section
3. Click **Configure**
4. Enter your API credentials:
   - **Client ID:** From developer account
   - **Client Secret:** From developer account
   - **Refresh Token:** From OAuth flow
5. Click **Test Connection**
6. If successful, click **Save**

---

## API Configuration

### Environment Variables

Add to your `.env` file:

```bash
# eBay API Credentials
EBAY_CLIENT_ID=your_client_id_here
EBAY_CLIENT_SECRET=your_client_secret_here
EBAY_REFRESH_TOKEN=your_refresh_token_here

# eBay API Environment (sandbox or production)
EBAY_ENVIRONMENT=production

# eBay Site (EBAY-US, EBAY-GB, EBAY-DE, etc.)
EBAY_SITE=EBAY-US
```

### Database Storage

```sql
INSERT INTO marketplace_credentials (
    user_id,
    platform,
    credentials_json,
    credential_type
) VALUES (
    1,
    'ebay',
    '{"client_id": "...", "client_secret": "...", "refresh_token": "..."}',
    'oauth_token'
);
```

---

## Connection Testing

### Automated Test Script

Run this to verify your eBay API connection:

```bash
python scripts/test_ebay_connection.py
```

### Test Steps:

1. **Token Refresh Test:**
   - Exchanges refresh token for new access token
   - Verifies token is valid
   - Saves new access token

2. **API Connectivity Test:**
   - Calls `GET /sell/account/v1/policy` endpoint
   - Verifies API credentials work
   - Checks account status

3. **Inventory Read Test:**
   - Calls `GET /sell/inventory/v1/inventory_item`
   - Verifies read permissions
   - Lists existing inventory (if any)

4. **Create Test Listing (Optional):**
   - Creates a test listing in sandbox
   - Verifies write permissions
   - Deletes test listing after

### Expected Output:

```
✅ eBay API Connection Test
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Token refresh successful
✅ API connectivity verified
✅ Account access confirmed
✅ Inventory permissions OK
✅ Write permissions OK

🎉 eBay integration is fully functional!
```

---

## Listing Creation

### API Request Example

```python
POST https://api.ebay.com/sell/inventory/v1/inventory_item/SKU123

{
    "product": {
        "title": "Vintage Nike Swoosh Hoodie Size L",
        "description": "Great condition vintage Nike hoodie...",
        "aspects": {
            "Brand": ["Nike"],
            "Size": ["L"],
            "Color": ["Blue"],
            "Condition": ["Pre-owned"]
        },
        "imageUrls": [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg"
        ]
    },
    "availability": {
        "shipToLocationAvailability": {
            "quantity": 1
        }
    },
    "condition": "USED_EXCELLENT",
    "packageWeightAndSize": {
        "weight": {
            "value": 1.5,
            "unit": "POUND"
        }
    }
}
```

### Response:

```json
{
    "sku": "SKU123",
    "status": "PUBLISHED",
    "offerIds": ["7891011121314"],
    "listingId": "123456789012"
}
```

---

## Inventory Sync

### Real-Time Synchronization

Rebel Operator automatically syncs with eBay:

1. **Create:** New listings auto-publish to eBay
2. **Update:** Changes sync within 5 minutes
3. **Sold:** Auto-updates quantity and cancels on other platforms
4. **Delete:** Removed from eBay within 5 minutes

### Sync Status Tracking

```python
{
    "listing_id": 123,
    "platform": "ebay",
    "platform_listing_id": "123456789012",
    "platform_url": "https://ebay.com/itm/123456789012",
    "status": "active",
    "last_synced": "2026-01-21T10:30:00Z"
}
```

---

## CSV Format (Fallback)

eBay also supports CSV bulk upload as a fallback option.

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `*Action(SiteID=US\|Country=US\|Currency=USD\|Version=1193)` | String | Action type | "Add" |
| `*Category` | Integer | eBay category ID | 15724 |
| `*Title` | String (80 max) | Listing title | "Vintage Nike Hoodie" |
| `*Quantity` | Integer | Available quantity | 1 |
| `*Format` | String | Listing format | "FixedPrice" |
| `*StartPrice` | Decimal | Item price | 45.00 |
| `*Duration` | String | Listing duration | "GTC" |
| `*Location` | String | Item location | "New York, NY" |
| `*C:Brand` | String | Brand name | "Nike" |
| `*C:Size` | String | Size | "L" |
| `*C:Condition` | Integer | Condition ID | 3000 (Used) |
| `Description` | HTML | Item description | "<p>Great condition...</p>" |
| `PicURL` | URL | Image URLs (pipe-separated) | "url1\|url2\|url3" |

### Sample CSV

See `sample.csv` in `/docs/platforms/csv-formats/ebay/`

---

## Rate Limits

| API | Calls/Day | Burst Limit |
|-----|-----------|-------------|
| Trading API | 5,000 | 10/sec |
| Inventory API | 5,000 | 5/sec |
| Browse API | 5,000 | 5/sec |

**Note:** Limits are per application, not per user.

---

## Error Handling

### Common Errors

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `1001` | Invalid token | Refresh OAuth token |
| `21916884` | Category mismatch | Update category ID |
| `21916635` | Missing required field | Add missing data |
| `30001` | Rate limit exceeded | Wait and retry |

### Retry Logic

```python
# Automatic retry with exponential backoff
max_retries = 3
for attempt in range(max_retries):
    try:
        response = post_to_ebay(listing)
        break
    except RateLimitError:
        sleep(2 ** attempt)  # 1s, 2s, 4s
```

---

## Troubleshooting

### "Invalid Client" Error
- Verify Client ID and Secret are correct
- Check you're using Production (not Sandbox) credentials
- Regenerate tokens if expired

### "Insufficient Permissions" Error
- Verify OAuth scopes include required permissions
- Re-authorize application with correct scopes

### "Category Not Supported" Error
- Use eBay's Category API to find correct category ID
- Some categories require additional item specifics

### Token Expired
- Refresh tokens expire after 18 months
- Access tokens expire after 2 hours
- Automatic refresh happens before expiration

---

## Security

✅ **OAuth 2.0** - Industry-standard authentication
✅ **Encrypted Storage** - Tokens encrypted at rest
✅ **Auto-Refresh** - Access tokens refreshed automatically
✅ **Scope Limits** - Only request needed permissions
✅ **HTTPS Only** - All API calls over secure connection

---

## Compliance

✅ **eBay API Terms:** Fully compliant
✅ **Rate Limits:** Respected with backoff
✅ **User Consent:** OAuth flow requires user authorization
✅ **Data Privacy:** Credentials never logged or exposed

---

## See Also

- `/src/adapters/ebay_adapter.py` - eBay API client
- `/src/publisher/cross_platform_publisher.py` - Publishing orchestrator
- `/docs/platforms/csv-formats/ebay/` - CSV format documentation
- https://developer.ebay.com/docs - Official eBay API Documentation
