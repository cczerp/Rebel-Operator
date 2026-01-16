# Google Sign-In Setup Guide

## ✅ Non-Negotiable Requirements

Google OAuth 2.0 has **strict security requirements** that MUST be followed:

1. ✅ **JWT Signature Verification** - REQUIRED (not optional)
2. ✅ **Client ID Validation** - Must validate `aud` claim matches your Client ID
3. ✅ **Issuer Validation** - Must verify `iss` is `accounts.google.com`
4. ✅ **Email Verification** - Only accept verified emails (`email_verified: true`)
5. ✅ **Token Expiration** - Must validate `exp` claim (tokens expire after 1 hour)
6. ✅ **HTTPS Required** - Production must use HTTPS (Render provides this)

**Status:** ✅ All requirements implemented in `routes_auth.py`

---

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console
Visit: https://console.cloud.google.com/apis/credentials

### 1.2 Create or Select Project
- Click "Select a project" → "New Project"
- Name it: `Rebel Operator` or similar
- Click "Create"

### 1.3 Enable Google Sign-In API
- Go to "APIs & Services" → "Library"
- Search for "Google Sign-In API"
- Click "Enable"

### 1.4 Create OAuth 2.0 Client ID
1. Go to "Credentials" tab
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - **User Type:** External (unless you have Google Workspace)
   - **App name:** Rebel Operator
   - **User support email:** Your email
   - **Developer contact email:** Your email
   - **Scopes:** Add `email` and `profile` (default)
   - Click "Save and Continue"

4. Create OAuth Client ID:
   - **Application type:** Web application
   - **Name:** Rebel Operator Web App
   - **Authorized JavaScript origins:**
     ```
     http://localhost:5000
     https://yourdomain.com
     https://rebel-operator.onrender.com
     ```
   - **Authorized redirect URIs:**
     ```
     http://localhost:5000
     https://yourdomain.com
     https://rebel-operator.onrender.com
     ```
   - Click "Create"

5. **Copy your Client ID** - it looks like:
   ```
   123456789-abc123xyz.apps.googleusercontent.com
   ```

---

## Step 2: Configure Environment Variable

### For Render (Production)

1. Go to your Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add new environment variable:
   - **Key:** `GOOGLE_CLIENT_ID`
   - **Value:** Your Client ID from Step 1.4
5. Click "Save Changes"
6. Render will automatically redeploy

### For Local Development

1. Copy `.env.example` to `.env` if you haven't:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add:
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   ```

3. Restart your local server

---

## Step 3: Test Google Sign-In

### 3.1 Check Login Page
1. Go to `/login` on your app
2. You should see a "Sign in with Google" button
3. If the button is missing:
   - Check browser console for errors
   - Verify `GOOGLE_CLIENT_ID` is set correctly
   - Check server logs for configuration errors

### 3.2 Test Sign-In Flow
1. Click "Sign in with Google"
2. Select your Google account
3. Grant permissions (email, profile)
4. You should be redirected to `/create` page
5. Check that you're logged in (navbar shows your email)

### 3.3 Verify Backend Logging
Check your server logs for:
```
[INFO] Google login successful for user <id>
[INFO] Activity logged: google_login
```

---

## Step 4: Verify Security Implementation

### ✅ Checklist

Run through this checklist to ensure secure implementation:

- [ ] **JWT Signature Verified:** Check `routes_auth.py` uses `id_token.verify_oauth2_token()`
- [ ] **Issuer Validated:** Code checks `iss` is `accounts.google.com`
- [ ] **Audience Validated:** Code checks `aud` matches `GOOGLE_CLIENT_ID`
- [ ] **Email Verified:** Code checks `email_verified` is `True`
- [ ] **Expiration Checked:** `verify_oauth2_token()` validates `exp` automatically
- [ ] **HTTPS in Production:** Render provides HTTPS by default
- [ ] **No Insecure JWT Decode:** Code does NOT use `jwt.decode(..., options={"verify_signature": False})`

### Security Code Review

The implementation in `routes_auth.py` (lines 388-429) includes:

```python
# ✅ SECURE: Uses google-auth library for proper verification
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

decoded = id_token.verify_oauth2_token(
    credential,
    google_requests.Request(),
    GOOGLE_CLIENT_ID,
    clock_skew_in_seconds=10
)

# ✅ SECURE: Validates issuer
if decoded.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
    return jsonify({"error": "Invalid token issuer"}), 400

# ✅ SECURE: Requires verified email
if not decoded.get('email_verified', False):
    return jsonify({"error": "Email not verified with Google"}), 400
```

---

## Troubleshooting

### Issue: "Google Sign-In not configured on server"

**Cause:** `GOOGLE_CLIENT_ID` environment variable is not set

**Solution:**
1. Add `GOOGLE_CLIENT_ID` to Render environment variables
2. Redeploy the app
3. Verify the variable is set: Check Render dashboard → Environment tab

### Issue: "Invalid token issuer"

**Cause:** Token not from Google (possible security attack)

**Solution:**
- This is a security feature working correctly
- Contact user and investigate if legitimate issue

### Issue: "Email not verified with Google"

**Cause:** User's Google account email is not verified

**Solution:**
- Ask user to verify their email with Google
- They need to check their Gmail for verification email

### Issue: "Invalid Google token: Token expired"

**Cause:** Token expired (Google tokens expire after 1 hour)

**Solution:**
- This is normal behavior
- User needs to sign in again
- Token expiration is a security feature

### Issue: Google button not showing

**Cause:** Client ID not loaded or JavaScript error

**Solution:**
1. Check browser console for errors
2. Verify `GOOGLE_CLIENT_ID` is set on server
3. Check `/api/auth/google-client-id` returns valid Client ID
4. Verify Google Sign-In library loaded: `https://accounts.google.com/gsi/client`

### Issue: "Redirect URI mismatch"

**Cause:** The redirect URI doesn't match authorized URIs in Google Console

**Solution:**
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth Client ID
3. Add your production URL to "Authorized JavaScript origins"
4. Make sure URL includes protocol (https://) and no trailing slash

---

## Dependencies

### Required Python Packages

Ensure these are in `requirements.txt`:

```txt
google-auth>=2.23.0         # Google OAuth ID token verification
pyjwt>=2.8.0                # JWT parsing (used internally)
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Production Deployment Checklist

Before deploying to production:

- [ ] `GOOGLE_CLIENT_ID` configured in Render
- [ ] Production URL added to Google Console authorized origins
- [ ] HTTPS enabled (automatic on Render)
- [ ] Test login flow works in production
- [ ] Verify secure JWT verification (no `verify_signature: False`)
- [ ] Check server logs for errors during sign-in
- [ ] Test with multiple Google accounts
- [ ] Test existing user login (should not create duplicate accounts)
- [ ] Test new user registration via Google
- [ ] Verify user data isolation (each user sees only their data)

---

## Security Best Practices

### ✅ DO

- ✅ Use `google-auth` library for token verification
- ✅ Validate all token claims (iss, aud, exp, email_verified)
- ✅ Use HTTPS in production
- ✅ Log authentication events for security auditing
- ✅ Require verified emails
- ✅ Keep `google-auth` library updated

### ❌ DON'T

- ❌ Use `jwt.decode(..., options={"verify_signature": False})`
- ❌ Skip token validation
- ❌ Trust tokens without verification
- ❌ Allow unverified emails
- ❌ Use HTTP in production
- ❌ Expose Client Secret (only Client ID is needed for frontend)

---

## Additional Resources

- **Google OAuth 2.0 Docs:** https://developers.google.com/identity/protocols/oauth2
- **Google Sign-In for Web:** https://developers.google.com/identity/gsi/web
- **Token Verification:** https://developers.google.com/identity/sign-in/web/backend-auth
- **Google Cloud Console:** https://console.cloud.google.com/

---

## Support

For issues with Google Sign-In:

1. Check this guide's troubleshooting section
2. Review `routes_auth.py` implementation
3. Check server logs for detailed error messages
4. Verify environment variables are set correctly
5. Test with Google's OAuth 2.0 Playground: https://developers.google.com/oauthplayground

---

**Last Updated:** 2025-01-09
**Status:** ✅ Production-ready with secure implementation
