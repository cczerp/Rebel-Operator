# Multi-User Search - Credential Setup Guide

## Overview

For the multi-platform search to work for ALL users (not just you), you need to decide on a credential strategy for each platform type.

## Credential Strategies

### Strategy 1: **App-Level Credentials** (RECOMMENDED for most platforms)
- **What**: Single API key/app credentials shared across all users
- **Best for**: Public search APIs that don't require user-specific auth
- **How**: Store credentials in environment variables or admin settings
- **Platforms**: eBay Finding API, Etsy, TCGplayer, Amazon Product API, Discogs

### Strategy 2: **User-Level Credentials**
- **What**: Each user connects their own account
- **Best for**: Platforms that require OAuth or user-specific access
- **How**: Users authenticate via OAuth flow, tokens stored in `marketplace_credentials` table
- **Platforms**: Shopify (individual stores), StockX, GOAT

### Strategy 3: **Hybrid** (App creds + optional user creds)
- **What**: Use app credentials for basic search, user credentials for enhanced features
- **Best for**: Platforms with tiered API access
- **How**: Fall back to app creds if user hasn't connected
- **Platforms**: eBay (basic search vs saved searches), Reverb

---

## Platform-by-Platform Credential Requirements

### 🟢 **GREEN TIER: Full API Access**

#### **eBay**
- **Search Method**: eBay Finding API (public, read-only)
- **Credential Type**: App-Level
- **Required**:
  - App ID (Client ID)
  - _(Optional: OAuth for saved searches, but not needed for basic search)_
- **Setup**:
  1. Register at [developer.ebay.com](https://developer.ebay.com)
  2. Create app → Get App ID
  3. Add to environment variable: `EBAY_APP_ID=your_app_id`
- **Cost**: Free (up to 5,000 calls/day)
- **Rate Limits**: 5,000 calls/day per App ID

#### **Etsy**
- **Search Method**: Etsy Open API v3
- **Credential Type**: App-Level
- **Required**:
  - API Key (keystring)
- **Setup**:
  1. Register at [developers.etsy.com](https://developers.etsy.com)
  2. Create app → Get API Key
  3. Add to environment variable: `ETSY_API_KEY=your_api_key`
- **Cost**: Free (up to 10,000 calls/day)
- **Rate Limits**: 10 requests/second

#### **TCGplayer**
- **Search Method**: TCGplayer API
- **Credential Type**: App-Level
- **Required**:
  - Public Key
  - Private Key
  - Bearer Token (generated from keys)
- **Setup**:
  1. Apply for API access at [tcgplayer.com/api](https://www.tcgplayer.com)
  2. Get Public/Private keys
  3. Generate bearer token
  4. Add to environment: `TCGPLAYER_PUBLIC_KEY`, `TCGPLAYER_PRIVATE_KEY`
- **Cost**: Free (must be approved seller or have business justification)
- **Rate Limits**: 300 requests/minute

#### **Amazon Product Advertising API**
- **Search Method**: Amazon PA-API 5.0
- **Credential Type**: App-Level (but requires Associate ID)
- **Required**:
  - Access Key
  - Secret Key
  - Associate Tag (affiliate ID)
- **Setup**:
  1. Register for Amazon Associates
  2. Apply for PA-API access
  3. Get credentials from AWS
  4. Add to environment: `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_ASSOCIATE_TAG`
- **Cost**: Free (must generate sales quota to maintain access)
- **Rate Limits**: 1 request/second (can increase with volume)

#### **Reverb**
- **Search Method**: Reverb API
- **Credential Type**: App-Level
- **Required**:
  - Personal Access Token (for read-only search)
- **Setup**:
  1. Register at [reverb.com/api](https://reverb.com/page/api)
  2. Generate Personal Access Token
  3. Add to environment: `REVERB_API_TOKEN=your_token`
- **Cost**: Free
- **Rate Limits**: 3,600 requests/hour

#### **Discogs**
- **Search Method**: Discogs API
- **Credential Type**: App-Level
- **Required**:
  - Consumer Key
  - Consumer Secret
- **Setup**:
  1. Register at [discogs.com/settings/developers](https://www.discogs.com/settings/developers)
  2. Create app → Get Consumer Key/Secret
  3. Add to environment: `DISCOGS_CONSUMER_KEY`, `DISCOGS_CONSUMER_SECRET`
- **Cost**: Free
- **Rate Limits**: 60 requests/minute (authenticated), 25/minute (unauthenticated)

---

### 🟡 **YELLOW TIER: No Public API (Limited Options)**

These platforms don't have official public search APIs. Options:

#### **Poshmark, Mercari, Grailed, Depop**
- **Search Method**: None officially supported
- **Options**:
  1. **Wait for official API** (Mercari announced API coming 2024)
  2. **RSS/Sitemap parsing** (if available and ToS-compliant)
  3. **Show as "Not Available"** in platform list
- **Recommendation**: Mark as unavailable until official API exists

#### **The RealReal, Vestiaire Collective, Vinted**
- **Search Method**: No public API
- **Recommendation**: Mark as unavailable

---

### 🟠 **ORANGE TIER: Market-Controlled (May Have APIs)**

#### **StockX**
- **Search Method**: StockX API (Partner access only)
- **Credential Type**: Partner Agreement Required
- **Required**:
  - Must apply for partner API access (difficult to get)
  - JWT token
- **Setup**: Contact StockX for partner program
- **Recommendation**: Mark as unavailable unless you have partner access

#### **GOAT**
- **Search Method**: No public API
- **Recommendation**: Mark as unavailable

#### **Chrono24**
- **Search Method**: Chrono24 API (requires dealer account)
- **Credential Type**: Dealer-only
- **Recommendation**: Mark as unavailable for general users

#### **Whatnot**
- **Search Method**: No public search API
- **Recommendation**: Mark as unavailable

---

### 🔴 **RED TIER: Local/Manual (No Search Possible)**

Facebook Marketplace, Craigslist, OfferUp, Nextdoor, VarageSale - **Cannot be automated**, mark as unavailable

---

## Implementation Priority

### Phase 1: **Implement Now** (Easy, Free, High Value)
1. ✅ eBay (Finding API - no auth required for basic search)
2. ✅ Etsy (API key only)
3. ✅ TCGplayer (API key, must apply)
4. Reverb (simple token auth)
5. Discogs (simple key/secret)
6. Amazon (requires affiliate account)

### Phase 2: **Implement Next** (More Complex)
7. AbeBooks (if API available)
8. Bonanza (CSV-based, might have search endpoint)
9. Ruby Lane (check for API)
10. Cardmarket (European TCG, has API)

### Phase 3: **Mark as "Coming Soon"**
- Mercari (API in development)
- Poshmark (if API becomes available)
- StockX (if partner access obtained)

### Phase 4: **Mark as "Unavailable"**
- Facebook Marketplace, Craigslist, OfferUp (no automation possible)
- GOAT, Grailed, Depop (no public API)

---

## Environment Variables Setup

Create a `.env` file or add to your hosting platform's environment variables:

```bash
# eBay
EBAY_APP_ID=your_ebay_app_id

# Etsy
ETSY_API_KEY=your_etsy_api_key

# TCGplayer
TCGPLAYER_PUBLIC_KEY=your_tcg_public_key
TCGPLAYER_PRIVATE_KEY=your_tcg_private_key

# Amazon
AMAZON_ACCESS_KEY=your_amazon_access_key
AMAZON_SECRET_KEY=your_amazon_secret_key
AMAZON_ASSOCIATE_TAG=your_associate_tag

# Reverb
REVERB_API_TOKEN=your_reverb_token

# Discogs
DISCOGS_CONSUMER_KEY=your_discogs_key
DISCOGS_CONSUMER_SECRET=your_discogs_secret
```

---

## Database Schema (marketplace_credentials table)

The existing `marketplace_credentials` table can store both:
1. **App-level credentials** (user_id = admin or system user)
2. **User-level credentials** (user_id = specific user)

```sql
-- Example: Store app-level eBay credentials
INSERT INTO marketplace_credentials (user_id, platform, credentials_json, credential_type)
VALUES (1, 'ebay', '{"app_id": "YourAppID"}', 'app_level');

-- Example: Store user-level OAuth token
INSERT INTO marketplace_credentials (user_id, platform, credentials_json, credential_type)
VALUES (123, 'etsy', '{"oauth_token": "abc123", "oauth_secret": "xyz789"}', 'oauth');
```

---

## Recommendation for Your Platform

**START WITH THESE 6:**
1. **eBay** - Largest marketplace, free API, no auth needed for search
2. **Etsy** - Handmade/vintage, simple API key
3. **TCGplayer** - Trading cards (your niche), must apply
4. **Reverb** - Music gear, simple token
5. **Discogs** - Vinyl/music, simple auth
6. **Amazon** - Huge selection (requires affiliate account)

This gives users 6 major platforms right away, covering collectibles, general merchandise, and niche markets.

**LATER ADD:**
- Cardmarket (European TCG)
- AbeBooks (books)
- Ruby Lane (antiques/collectibles)

**MARK AS UNAVAILABLE:**
- All platforms without public APIs
- Clearly communicate "Coming soon" vs "Not supported"

---

## Code Structure

```python
# src/search/credential_manager.py
class CredentialManager:
    """Manages app-level and user-level credentials"""

    @staticmethod
    def get_search_credentials(platform: str, user_id: Optional[int] = None):
        """
        Get credentials for platform search.

        Priority:
        1. User-specific credentials (if user_id provided)
        2. App-level credentials
        3. Environment variables
        """
        # Try user-specific first
        if user_id:
            user_creds = db.get_marketplace_credentials(user_id, platform)
            if user_creds:
                return json.loads(user_creds['credentials_json'])

        # Fall back to app-level (user_id=1 for admin/system)
        app_creds = db.get_marketplace_credentials(1, platform)
        if app_creds:
            return json.loads(app_creds['credentials_json'])

        # Fall back to environment variables
        return CredentialManager._get_env_credentials(platform)

    @staticmethod
    def _get_env_credentials(platform: str):
        """Load credentials from environment variables"""
        if platform == 'ebay':
            return {'app_id': os.getenv('EBAY_APP_ID')}
        elif platform == 'etsy':
            return {'api_key': os.getenv('ETSY_API_KEY')}
        # ... etc
```

---

## Next Steps

1. **Apply for API keys** for eBay, Etsy, TCGplayer, Reverb, Discogs
2. **Add environment variables** to your hosting platform
3. **Update platform_searchers.py** to use CredentialManager
4. **Test with your own credentials** first
5. **Deploy** and let users search across 6+ platforms immediately

All other platforms can show as "Coming Soon" or "Unavailable" with clear messaging about why.
