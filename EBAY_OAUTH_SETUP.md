# eBay OAuth Integration Setup Guide

Complete guide for setting up eBay OAuth integration in Rebel Operator.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Get eBay Developer Credentials](#get-ebay-developer-credentials)
3. [Environment Variables](#environment-variables)
4. [Database Setup](#database-setup)
5. [Testing the Integration](#testing-the-integration)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- ✅ eBay Developer Account (free)
- ✅ Flask app running on HTTPS (required for OAuth)
- ✅ PostgreSQL database
- ✅ Python 3.9+

---

## Get eBay Developer Credentials

### Step 1: Create eBay Developer Account

1. Go to https://developer.ebay.com/
2. Click "Register" and create a free developer account
3. Verify your email address

### Step 2: Create Application Keyset

#### **For Sandbox (Testing)**

1. Go to https://developer.ebay.com/my/keys
2. Click "Create a Keyset" under **Sandbox Keys**
3. Fill in application details:
   - **Application Title**: `Rebel Operator Sandbox`
   - **Description**: `Multi-platform listing management (sandbox testing)`
4. Click "Continue"
5. **Save these credentials:**
   - ✅ App ID (Client ID) → `EBAY_SANDBOX_APP_ID`
   - ✅ Cert ID (Client Secret) → `EBAY_SANDBOX_CERT_ID`

#### **For Production (Live)**

1. Go to https://developer.ebay.com/my/keys
2. Click "Create a Keyset" under **Production Keys**
3. Fill in application details:
   - **Application Title**: `Rebel Operator`
   - **Description**: `Multi-platform resale listing management`
4. Click "Continue"
5. **Save these credentials:**
   - ✅ App ID (Client ID) → `EBAY_PROD_APP_ID`
   - ✅ Cert ID (Client Secret) → `EBAY_PROD_CERT_ID`

### Step 3: Create OAuth Redirect URI (RuName)

#### **For Sandbox**

1. Go to https://developer.ebay.com/my/auth/
2. Under "Sandbox", click "Create a redirect URI"
3. Fill in:
   - **Your privacy policy URL**: `https://www.rebeloperator.com/privacy`
   - **Your auth accepted URL**: `https://www.rebeloperator.com/ebay/callback`
   - **Your auth declined URL**: `https://www.rebeloperator.com/settings`
4. Click "Continue"
5. **Save the RuName** → `EBAY_SANDBOX_RUNAME`
   - Example: `Christopher_Cze-Christop-rebelo-jqkiqj`

#### **For Production**

1. Go to https://developer.ebay.com/my/auth/
2. Under "Production", click "Create a redirect URI"
3. Fill in:
   - **Your privacy policy URL**: `https://www.rebeloperator.com/privacy`
   - **Your auth accepted URL**: `https://www.rebeloperator.com/ebay/callback`
   - **Your auth declined URL**: `https://www.rebeloperator.com/settings`
4. Click "Continue"
5. **Save the RuName** → `EBAY_PROD_RUNAME`

---

## Environment Variables

Add these to your `.env` file or Render environment variables:

```bash
# =========================
# eBay OAuth Credentials
# =========================

# Sandbox (Testing)
EBAY_SANDBOX_APP_ID=your_sandbox_app_id_here
EBAY_SANDBOX_CERT_ID=your_sandbox_cert_id_here
EBAY_SANDBOX_RUNAME=your_sandbox_runame_here

# Production (Live)
EBAY_PROD_APP_ID=your_production_app_id_here
EBAY_PROD_CERT_ID=your_production_cert_id_here
EBAY_PROD_RUNAME=your_production_runame_here

# OAuth Redirect URI (same for both)
EBAY_REDIRECT_URI=https://www.rebeloperator.com/ebay/callback

# Environment Selection
EBAY_ENV=sandbox  # Use 'sandbox' for testing, 'production' for live

# Flask Secret Key (required for token encryption)
SECRET_KEY=your_super_secret_key_here_minimum_32_characters
```

### Generate SECRET_KEY

If you don't have a `SECRET_KEY` yet:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the output and set it as your `SECRET_KEY`.

---

## Database Setup

The `ebay_tokens` table will be created automatically when you start the Flask app.

### Manual Migration (Optional)

If you need to run the migration manually:

```sql
-- Run this in your PostgreSQL database

CREATE TABLE IF NOT EXISTS ebay_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    environment VARCHAR(20) NOT NULL DEFAULT 'sandbox',
    scopes TEXT,
    ebay_user_id VARCHAR(255),
    ebay_username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, environment)
);

CREATE INDEX idx_ebay_tokens_user_id ON ebay_tokens(user_id);
CREATE INDEX idx_ebay_tokens_expires_at ON ebay_tokens(expires_at);
```

---

## Testing the Integration

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Environment to Sandbox

```bash
export EBAY_ENV=sandbox
```

### Step 3: Start Flask App

```bash
python web_app.py
```

### Step 4: Connect to eBay Sandbox

1. Go to https://www.rebeloperator.com/settings
2. Scroll to "eBay Integration" section
3. Ensure "Sandbox (Testing)" is selected
4. Click "Connect to eBay Sandbox"
5. Log in with your eBay Sandbox test account
   - **Don't have a sandbox account?** Create one at https://developer.ebay.com/sandbox
6. Grant permissions
7. You should be redirected back with a success message!

### Step 5: Test the Connection

1. In settings, click "Test Connection"
2. You should see: ✅ Connection successful!

---

## Production Deployment

### Before Going Live

⚠️ **IMPORTANT:** Test thoroughly in Sandbox first!

- [ ] All OAuth flows work in Sandbox
- [ ] Token refresh works
- [ ] Disconnect/reconnect works
- [ ] Error handling tested

### Switch to Production

1. Update environment variable:
   ```bash
   EBAY_ENV=production
   ```

2. In settings UI:
   - Switch to "Production (Live)" tab
   - Click "Connect to eBay Production"
   - Use your **real eBay account**

3. Grant permissions

4. Test connection

---

## Troubleshooting

### "Missing EBAY_SANDBOX_APP_ID environment variable"

**Problem:** Environment variables not set.

**Solution:**
- Verify `.env` file exists and has correct values
- Restart Flask app after adding env vars
- Check Render dashboard if deployed

### "Invalid state token. Please try again."

**Problem:** CSRF protection detected mismatched state.

**Solution:**
- Clear browser cookies
- Try incognito mode
- Ensure `SESSION_TYPE` is set correctly in Flask

### "Failed to exchange authorization code"

**Problem:** eBay OAuth exchange failed.

**Possible causes:**
1. **Wrong environment** - Using production credentials with sandbox URL
2. **Expired code** - Authorization code expired (valid 5 minutes)
3. **Wrong redirect URI** - Mismatch between configured and actual redirect URI

**Solution:**
- Double-check `EBAY_REDIRECT_URI` matches what's configured in eBay Developer Portal
- Ensure App ID and Cert ID are from correct environment (sandbox vs production)
- Try the OAuth flow again (code expires quickly)

### "403 Forbidden" when testing connection

**Problem:** Access token expired or invalid.

**Solution:**
- Tokens auto-refresh, but if broken, disconnect and reconnect
- Check database for expired tokens
- Verify scopes are correct

### Tokens not saving to database

**Problem:** Database error or encryption issue.

**Solution:**
- Check `SECRET_KEY` is set (required for encryption)
- Verify database connection
- Check PostgreSQL logs for errors
- Run: `python -c "from src.ebay.crypto_utils import get_token_crypto; get_token_crypto()"`

---

## OAuth Flow Diagram

```
User clicks "Connect to eBay"
           ↓
Redirect to eBay authorization page
           ↓
User logs into eBay & grants permissions
           ↓
eBay redirects to /ebay/callback with code
           ↓
Exchange code for access_token & refresh_token
           ↓
Encrypt & save tokens to database
           ↓
Success! User is connected
```

---

## Token Refresh Flow

```
User makes API call
           ↓
Check if access_token is expired
           ↓
     Is expired?
    /           \
  Yes            No
   ↓              ↓
Refresh using    Use existing
refresh_token    access_token
   ↓              ↓
Save new token   ↓
   ↓              ↓
   └──────────────┘
           ↓
   Make API call
```

---

## Security Notes

### Token Encryption

- ✅ All OAuth tokens are encrypted before storage using Fernet (AES-128)
- ✅ Encryption key derived from Flask `SECRET_KEY`
- ✅ Tokens only decrypted when needed
- ✅ Never logged or displayed in plaintext

### Best Practices

1. **Use strong SECRET_KEY** - Minimum 32 characters, random
2. **HTTPS only** - OAuth requires HTTPS
3. **Validate state tokens** - CSRF protection
4. **Auto-refresh tokens** - Access tokens expire every 2 hours
5. **Delete on disconnect** - Tokens removed from DB when user disconnects

---

## Next Steps

Once eBay OAuth is working:

1. ✅ Build inventory sync from eBay to Rebel Operator
2. ✅ Implement listing creation/updates
3. ✅ Add bulk operations
4. ✅ Set up webhooks for real-time updates

---

## Support

**eBay Developer Support:**
- https://developer.ebay.com/support

**Documentation:**
- OAuth Guide: https://developer.ebay.com/api-docs/static/oauth-tokens.html
- Inventory API: https://developer.ebay.com/api-docs/sell/inventory/overview.html

**Issues:**
- GitHub: https://github.com/anthropics/rebel-operator/issues

---

## Quick Reference

| Environment | App ID Env Var | Cert ID Env Var | RuName Env Var |
|------------|----------------|-----------------|----------------|
| Sandbox | `EBAY_SANDBOX_APP_ID` | `EBAY_SANDBOX_CERT_ID` | `EBAY_SANDBOX_RUNAME` |
| Production | `EBAY_PROD_APP_ID` | `EBAY_PROD_CERT_ID` | `EBAY_PROD_RUNAME` |

**OAuth Scopes Required:**
- `https://api.ebay.com/oauth/api_scope`
- `https://api.ebay.com/oauth/api_scope/sell.inventory`
- `https://api.ebay.com/oauth/api_scope/sell.inventory.readonly`

**Token Lifetimes:**
- Access Token: 2 hours
- Refresh Token: 18 months

---

Good luck! 🚀
