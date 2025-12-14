# Deployment Setup Guide - Render + Supabase + Upstash Redis

This guide walks you through setting up all required environment variables for deploying the Resell Rebel application to Render.

## Prerequisites

Before deploying, you need accounts and resources from:
1. **Render** - Web hosting platform
2. **Supabase** - PostgreSQL database + Google OAuth
3. **Upstash** - Redis (for session storage)
4. **Google Cloud** - OAuth credentials (configured via Supabase)
5. **Gmail** (optional) - For sending verification emails

---

## Part 1: Create Required Services

### 1.1 Create Upstash Redis Database

**Why:** Required for session storage (sessions persist across server restarts)

1. Go to https://upstash.com
2. Sign up / Log in
3. Click "Create Database"
4. Choose:
   - **Name:** `resell-rebel-sessions`
   - **Type:** Regional
   - **Region:** Choose closest to your Render region (e.g., `us-west-1` for Oregon)
   - **TLS:** Enabled (required)
5. Click "Create"
6. **Copy the following:**
   - Click "Connect" tab
   - Find "Redis URL" (starts with `redis://` or `rediss://`)
   - **Save this URL** - you'll need it for `REDIS_URL` environment variable

**Example Redis URL:**
```
rediss://default:XXXXXX@us1-proper-mantis-12345.upstash.io:6379
```

---

### 1.2 Create Supabase Project

**Why:** Provides PostgreSQL database + Google OAuth authentication

1. Go to https://app.supabase.com
2. Click "New Project"
3. Choose:
   - **Name:** `resell-rebel`
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your Render region
4. Click "Create new project" (takes ~2 minutes)
5. **Copy the following:**
   - Go to "Settings" → "API"
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`) - for `SUPABASE_URL`
   - **Project API keys** → `anon` `public` key - for `SUPABASE_ANON_KEY`
   - Go to "Settings" → "Database"
   - **Connection string** → "URI" (starts with `postgresql://`) - for `DATABASE_URL`

**Example values:**
```
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.abcdefgh.supabase.co:5432/postgres
```

---

### 1.3 Configure Google OAuth in Supabase

**Why:** Enables "Sign in with Google" functionality

1. In Supabase dashboard, go to "Authentication" → "Providers"
2. Find "Google" and click "Enable"
3. Follow Supabase's guide to:
   - Create Google OAuth credentials in Google Cloud Console
   - Copy Client ID and Client Secret to Supabase
4. **Add Redirect URLs:**
   - In Supabase: "Authentication" → "URL Configuration"
   - Add redirect URLs:
     ```
     http://localhost:5000/auth/callback  (for local testing)
     https://YOUR-APP.onrender.com/auth/callback  (for production)
     ```
   - Replace `YOUR-APP` with your actual Render app name
5. Click "Save"

---

### 1.4 Set Up Gmail App Password (Optional)

**Why:** Enables email verification for new users

1. Go to your Google Account settings
2. Navigate to "Security"
3. Enable "2-Step Verification" (if not already enabled)
4. Go to "App passwords"
5. Create a new app password:
   - App: Mail
   - Device: Other (custom name) → "Resell Rebel"
6. **Copy the generated password** - you'll need it for `MAIL_PASSWORD`

---

## Part 2: Configure Render Environment Variables

### 2.1 Deploy to Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** `resell-rebel` (or your preferred name)
   - **Environment:** Python 3
   - **Build Command:** (uses render.yaml)
   - **Start Command:** (uses render.yaml)
5. Click "Create Web Service"

---

### 2.2 Set Environment Variables

**CRITICAL:** The following environment variables are REQUIRED for the app to work:

Go to your Render service → "Environment" tab → Add the following variables:

#### Required - Flask & Security
```
SECRET_KEY=<generate-random-secret>
FLASK_SECRET_KEY=<same-as-SECRET_KEY>
FLASK_ENV=production
```

**How to generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Required - Redis (Session Storage)
```
REDIS_URL=<your-upstash-redis-url>
```
Example: `rediss://default:XXXXXX@us1-proper-mantis-12345.upstash.io:6379`

#### Required - Database
```
DATABASE_URL=<your-supabase-postgresql-url>
```
Example: `postgresql://postgres:[YOUR-PASSWORD]@db.abcdefgh.supabase.co:5432/postgres`

#### Required - Supabase OAuth
```
SUPABASE_URL=<your-supabase-project-url>
SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

#### Optional - OAuth Redirect (recommended)
```
SUPABASE_REDIRECT_URL=https://YOUR-APP.onrender.com/auth/callback
```
(If not set, app uses `RENDER_EXTERNAL_URL` automatically)

#### Optional - Email Verification
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<your-gmail-app-password>
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

#### Optional - AI Features
```
GEMINI_API_KEY=<your-gemini-api-key>
```

---

### 2.3 Environment Variables Summary Table

| Variable | Required? | Example Value | Where to Get It |
|----------|-----------|---------------|-----------------|
| `SECRET_KEY` | ✅ Yes | `xK9mP2...` | Generate with Python command above |
| `FLASK_SECRET_KEY` | ✅ Yes | Same as SECRET_KEY | Same value as SECRET_KEY |
| `FLASK_ENV` | ✅ Yes | `production` | Fixed value |
| `REDIS_URL` | ✅ Yes | `rediss://default:...@upstash.io:6379` | Upstash dashboard |
| `DATABASE_URL` | ✅ Yes | `postgresql://postgres:...@supabase.co:5432/postgres` | Supabase → Settings → Database |
| `SUPABASE_URL` | ✅ Yes | `https://abcdefgh.supabase.co` | Supabase → Settings → API |
| `SUPABASE_ANON_KEY` | ✅ Yes | `eyJhbGci...` | Supabase → Settings → API |
| `SUPABASE_REDIRECT_URL` | ⚠️ Recommended | `https://your-app.onrender.com/auth/callback` | Your Render app URL + `/auth/callback` |
| `MAIL_USERNAME` | ❌ Optional | `your-email@gmail.com` | Your Gmail address |
| `MAIL_PASSWORD` | ❌ Optional | `abcd efgh ijkl mnop` | Gmail App Password |
| `GEMINI_API_KEY` | ❌ Optional | `AIza...` | Google AI Studio |

---

## Part 3: Verify Deployment

### 3.1 Check Logs on First Deploy

After setting environment variables, trigger a redeploy:
1. Go to Render dashboard → your service
2. Click "Manual Deploy" → "Deploy latest commit"
3. Watch the logs for:

**Success indicators:**
```
✅ Environment loaded
✅ Flask secret key configured (length: 43)
✅ Redis connection successful: upstash.io
✅ Connection pool created (maxconn=2 for Render free tier)
✅ Database connected successfully
✅ Blueprints initialized
✅ Flask app initialized and ready to serve requests
```

**Error indicators to fix:**
```
❌ WARNING: REDIS_URL not set!
❌ Failed to connect to Redis: ...
❌ DATABASE_URL environment variable is required
❌ WARNING: SECRET_KEY not set or using default value!
```

If you see errors, go back to Part 2.2 and ensure all required variables are set.

---

### 3.2 Test Login Flow

Once deployment succeeds:

#### Test Google OAuth:
1. Go to `https://your-app.onrender.com/login`
2. Click "Sign in with Google"
3. **Expected:** Redirects to Google login page
4. Complete Google login
5. **Expected:** Redirects back to app, shows "Welcome! You're now logged in with Google"
6. **Expected:** Dashboard shows your username

#### Test Session Persistence:
1. After logging in, refresh the page
2. **Expected:** You remain logged in (don't get redirected to login page)
3. Navigate to different pages (e.g., `/drafts`, `/listings`)
4. **Expected:** You remain logged in

#### Test Email/Password Registration (if email configured):
1. Go to `/register`
2. Create account with username, email, password
3. **Expected:** "Verification email sent" message
4. Check your email for verification link
5. Click verification link
6. **Expected:** "Email verified! You can now log in"
7. Log in with email and password
8. **Expected:** Logged in successfully

---

### 3.3 Debug Common Issues

#### Issue: "REDIS_URL not set"
**Fix:** Add `REDIS_URL` in Render environment variables (see Part 2.2)

#### Issue: "Failed to connect to Redis"
**Cause:** Invalid Redis URL or Upstash database not running
**Fix:**
1. Verify Redis URL is correct (check Upstash dashboard)
2. Ensure Redis URL starts with `rediss://` (double 's' for TLS)
3. Test connection manually:
   ```bash
   redis-cli -u <YOUR_REDIS_URL> ping
   ```

#### Issue: "DATABASE_URL environment variable is required"
**Fix:** Add `DATABASE_URL` in Render environment variables (see Part 2.2)

#### Issue: Google OAuth 404 error
**Cause:** Redirect URL not whitelisted in Supabase
**Fix:**
1. Go to Supabase → Authentication → URL Configuration
2. Add: `https://your-app.onrender.com/auth/callback`
3. Save and redeploy

#### Issue: Session lost on page refresh
**Possible causes:**
1. REDIS_URL not set → Sessions stored in memory (ephemeral)
2. SECRET_KEY not set → Different secret on each worker restart
3. Cookie settings incorrect → Cookies rejected by browser

**Fix:**
1. Verify REDIS_URL is set and Redis is connected (check logs)
2. Verify SECRET_KEY is set (check logs for "secret key configured")
3. Check browser DevTools → Application → Cookies
   - Should see `resell_rebel_session` cookie
   - Should have `SameSite=Lax`, `HttpOnly=true`, `Secure=true`

---

## Part 4: Production Checklist

Before going live:

- [ ] All required environment variables set in Render
- [ ] Redis connection successful (check logs)
- [ ] Database connection successful (check logs)
- [ ] Google OAuth working (test sign-in)
- [ ] Session persistence working (test refresh)
- [ ] Email verification working (if configured)
- [ ] SECRET_KEY is random and secure (not default value)
- [ ] DATABASE_URL uses Supabase Internal URL (faster than External)
- [ ] Supabase redirect URLs whitelisted
- [ ] Monitor Render logs for errors during first few user logins

---

## Support & Troubleshooting

### Enable Debug Logging

Add this environment variable to see detailed session logs:
```
DEBUG_SESSIONS=true
```

Then check Render logs for:
```
[REQUEST] GET /
[SESSION] Authenticated: True
[SESSION] User: username (ID: user-id)
[USER_LOADER] ✅ Successfully loaded user: username
```

### Debug Endpoints

Access these URLs to check configuration:
- `/debug-config` - Shows Flask configuration
- `/debug/supabase` - Tests Supabase connectivity
- `/api/auth/session` - Checks current login status (JSON)

### Get Help

If issues persist:
1. Enable `DEBUG_SESSIONS=true`
2. Capture logs from Render during login attempt
3. Check browser DevTools → Network tab for failed requests
4. Check browser DevTools → Application → Cookies
5. Share logs and browser info in GitHub issues

---

**Last Updated:** 2025-12-14
**Version:** 1.0
**Status:** ✅ Ready for deployment
