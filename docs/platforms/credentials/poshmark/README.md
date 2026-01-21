# Poshmark Credentials & Authentication

## Overview

Poshmark credentials are used for:
- ✅ Account verification
- ⚠️ CSV export preparation (manual upload required)
- ❌ Direct posting (not supported - against TOS)

**Storage:** Credentials are encrypted in the `marketplace_credentials` table

---

## Required Credentials

### 1. Username or Email
- **Type:** String
- **Purpose:** Account identifier
- **Example:** `your_username` or `your.email@example.com`

### 2. Password
- **Type:** String (encrypted)
- **Purpose:** Account authentication
- **Security:** Stored encrypted in database, never logged

---

## Setup Instructions

### Step 1: Configure in Rebel Operator

1. Go to **Settings** → **Platform Integrations**
2. Find **Poshmark** in the Fashion & Apparel section
3. Click **Configure**
4. Enter your credentials:
   - **Username:** Your Poshmark username or email
   - **Password:** Your Poshmark password
5. Click **Save**

### Step 2: Verification

The system will validate that:
- Username/email format is correct
- Credentials are stored securely
- Platform is ready for CSV export

**Note:** Poshmark does not offer a public API, so we cannot verify credentials by logging in automatically. Connection testing must be done manually.

---

## Security Best Practices

### Password Security
- ✅ Use a unique password for Poshmark
- ✅ Enable 2FA on your Poshmark account
- ✅ Never share your credentials
- ✅ Credentials are encrypted at rest in our database

### Database Encryption
```sql
-- Credentials are stored encrypted
CREATE TABLE marketplace_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    username TEXT,  -- Encrypted
    password TEXT,  -- Encrypted with strong algorithm
    -- ...
);
```

---

## Connection Testing

Since Poshmark has no public API, connection testing is **manual**:

### Manual Test Procedure:

1. **Export Test CSV:**
   - Create a test listing in Rebel Operator
   - Export to Poshmark CSV format
   - Download the CSV file

2. **Login to Poshmark:**
   - Go to https://poshmark.com
   - Log in with your credentials
   - Verify you can access your account

3. **Test CSV Upload:**
   - Go to **Account** → **Bulk Upload Tool**
   - Upload the test CSV
   - Verify it processes successfully

4. **Confirm Integration:**
   - If CSV uploads successfully, integration is working
   - Update status in Rebel Operator

---

## Troubleshooting

### "Invalid Credentials" Error
- Double-check username/email spelling
- Verify password is correct
- Try logging in directly on Poshmark.com
- Reset password if needed

### 2FA Issues
- Poshmark may require 2FA code
- This must be entered on Poshmark website
- Automated login is not possible with 2FA

### Account Locked
- Too many failed login attempts may lock account
- Wait 15-30 minutes before trying again
- Contact Poshmark support if locked

---

## Limitations

### No Direct API Access
Poshmark **does not** provide a public API for:
- ❌ Automated posting
- ❌ Inventory sync
- ❌ Order management
- ❌ Credential verification

### What IS Supported:
- ✅ CSV generation
- ✅ Manual CSV upload
- ✅ Template creation
- ✅ Field mapping

---

## Future Enhancements

### Potential Features (if Poshmark adds API):
- [ ] Automated listing creation
- [ ] Real-time inventory sync
- [ ] Order management
- [ ] Automated credential verification
- [ ] Status updates

**Current Status:** Waiting for Poshmark to release public API

---

## Data Stored

When you save Poshmark credentials, we store:

```json
{
  "platform": "poshmark",
  "credential_type": "username_password",
  "username": "your_username",
  "password": "***encrypted***",
  "created_at": "2026-01-21T10:00:00Z",
  "updated_at": "2026-01-21T10:00:00Z"
}
```

**Security Features:**
- Passwords encrypted with industry-standard algorithms
- Credentials never logged or exposed
- Access restricted to your user account only
- Automatic expiration after 90 days of inactivity (optional)

---

## API Request (Internal)

```python
# Save credentials
POST /api/settings/platform-credentials
{
    "platform": "poshmark",
    "username": "your_username",
    "password": "your_password"
}

# Retrieve credentials (encrypted)
GET /api/settings/platform-credentials

# Delete credentials
DELETE /api/settings/marketplace-credentials/poshmark
```

---

## Compliance

✅ **TOS Compliant:** We do NOT automate posting to Poshmark
✅ **Privacy:** Credentials encrypted and never shared
✅ **Manual Process:** Users upload CSV manually
✅ **No Bot Activity:** No automated actions on Poshmark platform

---

## See Also

- `/src/database/db.py` - Credential storage schema
- `/src/routes/main.py` - Credential API endpoints
- `/docs/platforms/csv-formats/poshmark/` - CSV format documentation
- `SECURITY.md` - Security and encryption details
