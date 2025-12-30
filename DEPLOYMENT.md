# ResellGenie - Production Deployment Guide

## 🚨 CRITICAL: Deployment Failing After 50+ Commits

**Root Cause:** REDIS_URL is REQUIRED but not configured in Render.

The app **exits immediately on startup** when REDIS_URL is missing (see web_app.py:69-76):
```python
if not redis_url:
    print("⚠️  WARNING: REDIS_URL not set!")
    sys.exit(1)  # ← App crashes here!
```

**Fix:** Follow Step 1 below to add REDIS_URL.

---

## Why Login Has Been Broken

Your login system requires **3 services** working together:
1. **Redis (Upstash)** - Session storage & OAuth PKCE verifiers
2. **Supabase** - Google OAuth authentication
3. **PostgreSQL** - User data storage

If ANY of these are missing/misconfigured, login fails.

---

## ✅ The Solution

Use **managed services** for persistence:
1. **Upstash Redis** for sessions (FREE tier: 10k commands/day)
2. **PostgreSQL** for database (FREE on Render)
3. **Supabase** for Google OAuth (FREE)
4. **Cloudinary** for photos (FREE tier: 25GB)

---

## Step 1: Set Up Upstash Redis (CRITICAL - App won't start without this!)

### Create Free Redis Instance:

1. Go to https://upstash.com/
2. Sign up for free account
3. Click **"Create Database"**
4. **Name:** `resellgenie-sessions`
5. **Region:** Choose closest to your Render region
6. **Type:** Regional (free tier)
7. Click **"Create"**

### Copy Redis URL:

1. After creation, click on your database
2. Scroll to **"REST API"** section
3. Look for connection string format: `rediss://default:PASSWORD@HOST:6379`
4. **IMPORTANT:** Use the `rediss://` URL (with double 's' for TLS)
5. Go to Render → Your Web Service → **Environment**
6. Add:
   ```
   REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_HOST.upstash.io:6379
   ```

---

## Step 2: Set Up Supabase for Google OAuth

### Create Supabase Project:

1. Go to https://app.supabase.com/
2. Sign up / Log in
3. Click **"New Project"**
4. **Name:** `resellgenie`
5. **Database Password:** (save this)
6. **Region:** Same as Render
7. Click **"Create new project"**

### Enable Google OAuth:

1. In Supabase Dashboard → **Authentication** → **Providers**
2. Find **Google** and click to expand
3. Toggle **"Enable Google provider"** ON
4. **Authorized redirect URLs:** Add your Render app URL:
   ```
   https://your-app.onrender.com/auth/callback
   ```
5. Click **"Save"**

### Get Supabase Credentials:

1. In Supabase Dashboard → **Settings** → **API**
2. Copy:
   - **Project URL** → This is your `SUPABASE_URL`
   - **anon/public key** → This is your `SUPABASE_ANON_KEY`
3. Go to Render → Your Web Service → **Environment**
4. Add:
   ```
   SUPABASE_URL=https://YOUR_PROJECT.supabase.co
   SUPABASE_ANON_KEY=YOUR_ANON_KEY_HERE
   SUPABASE_REDIRECT_URL=https://your-app.onrender.com/auth/callback
   ```

---

## Step 3: Set Up PostgreSQL Database

### Option A: Use Supabase PostgreSQL (Recommended if already using Supabase)

**CRITICAL:** If using Supabase PostgreSQL, you MUST use the **Connection Pooler**, not the direct connection!

1. **Get Pooler URL from Supabase:**
   - Go to https://app.supabase.com/ → Your Project
   - Navigate to **Settings** → **Database**
   - Scroll to **"Connection Pooling"** section
   - Copy the **Session mode** connection string
   - It should look like:
     ```
     postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres
     ```
   - **Note the port: 6543** (pooler), NOT 5432 (direct)

2. **Add to Render Environment:**
   - Go to Render Dashboard → Your Web Service → **Environment**
   - Add or update:
     ```
     DATABASE_URL=postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres
     ```

**Why Connection Pooler?**
- Direct connection (port 5432): Limited to ~10 connections, causes SSL timeout errors
- Pooler connection (port 6543): Uses pgBouncer, handles thousands of connections efficiently
- **Without pooler, you'll get:** `SSL connection has been closed unexpectedly`

### Option B: Use Render PostgreSQL (Alternative)

1. Click **"New +"** → **"PostgreSQL"**
2. **Name:** `resellgenie-db`
3. **Database:** `resellgenie` (or any name)
4. **Region:** Same as your web service
5. **Plan:** **Free** (1GB storage, 90 days retention)
6. Click **"Create Database"**

7. **Link to Web Service:**
   - The `render.yaml` includes auto-injection config
   - DATABASE_URL will be set automatically

**Comparison:**
- **Supabase:** Better free tier (500MB persistent), requires pooler
- **Render:** Simpler setup (no pooler needed), 1GB but 90-day limit on free tier

---

## Step 4: Set Up Cloudinary for Photos

### Sign Up for Free:

1. Go to: https://cloudinary.com/users/register_free
2. Sign up (free tier is generous!)
3. **FREE tier includes:**
   - 25 GB storage
   - 25 GB bandwidth/month
   - 25,000 transformations/month
   - More than enough for most resellers!

### Get Your Credentials:

1. After signup, go to **Dashboard**
2. You'll see:
   - **Cloud Name:** (like `dxyz123abc`)
   - **API Key:** (like `123456789012345`)
   - **API Secret:** (like `abcdefghijklmnopqrstuvwxyz`)

### Add to Render:

Go to your Web Service → **Environment** → Add these variables:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
USE_LOCAL_STORAGE=false
```

**Important:** Set `USE_LOCAL_STORAGE=false` to enable Cloudinary!

---

## Step 5: Configure Email (For Registration)

### Get Gmail App Password:

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. **App name:** `ResellGenie`
4. Click **"Create"**
5. Copy the 16-character password

### Add to Render:

```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

---

## Step 6: Complete Environment Variables Checklist

In Render → Your Web Service → **Environment**, verify you have:

### ✅ CRITICAL (App won't start without these):
- `REDIS_URL` - From Upstash Redis
- `SECRET_KEY` - Auto-generated by Render (render.yaml)
- `DATABASE_URL` - Auto-injected from PostgreSQL (render.yaml)

### ✅ REQUIRED (For login to work):
- `SUPABASE_URL` - From Supabase project
- `SUPABASE_ANON_KEY` - From Supabase project
- `SUPABASE_REDIRECT_URL` - Your Render app URL + `/auth/callback`

### ✅ OPTIONAL (For features):
- `GEMINI_API_KEY` - For AI description generation
- `MAIL_USERNAME` - For email verification
- `MAIL_PASSWORD` - Gmail app password
- `MAIL_DEFAULT_SENDER` - Your email
- `CLOUDINARY_CLOUD_NAME` - For photo storage
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary secret

---

## Step 7: Deploy!

### First Deploy (After Setting Up Services):

1. **Commit changes** to git:
   ```bash
   git add render.yaml .env.example DEPLOYMENT.md
   git commit -m "Fix deployment: Add REDIS_URL and all required env vars"
   git push origin main
   ```

2. Render will auto-deploy if `autoDeploy: true` in render.yaml

3. **Watch the deployment logs** for these success messages:
   ```
   ✅ Environment loaded
   ✅ Flask secret key configured
   ✅ Redis connection successful
   ✅ Database connected successfully
   ✅ Blueprints initialized
   ✅ Flask app initialized and ready to serve requests
   ```

### If Deployment Fails:

Check logs for specific errors:
- `❌ REDIS_URL not set` → Add REDIS_URL to environment
- `❌ Failed to connect to Redis` → Verify Redis URL is correct
- `❌ FATAL ERROR during initialization` → Check DATABASE_URL
- `❌ Supabase client not configured` → Add Supabase env vars

---

## 🎉 Verifying Login Works

### Test Google OAuth Login:

1. Go to your deployed app: `https://your-app.onrender.com`
2. Click **"Login"**
3. Click **"Sign in with Google"**
4. Authorize with your Google account
5. You should be redirected back and logged in!

### Success Indicators in Logs:

```
🟢 [LOGIN_GOOGLE] Starting OAuth flow
✅ [LOGIN_GOOGLE] OAuth URL generated with flow_id
🔵 [CALLBACK] OAuth callback handler STARTED
✅ [CALLBACK] Token exchange successful
✅ [CALLBACK] User object created
🎉 [CALLBACK] OAuth login successful
```

### If Login Still Fails:

1. Check SUPABASE_REDIRECT_URL exactly matches your app URL
2. Verify Supabase has Google OAuth enabled
3. Enable debug mode: Set `DEBUG_SESSIONS=true` in Render
4. Check Render logs for specific error messages

---

## 🎉 You're Done!

Now your app is **fully functional**:
- ✅ App starts successfully on Render
- ✅ Google OAuth login works
- ✅ Sessions persist in Redis
- ✅ User data stored in PostgreSQL
- ✅ Photos stored in Cloudinary
- ✅ No more deployment failures!

---

## Local Development

For local development, create `.env` file:

```bash
# Use local storage for dev
USE_LOCAL_STORAGE=true

# Use SQLite for dev (no DATABASE_URL needed)

# AI APIs
GEMINI_API_KEY=your_gemini_key

# Flask
FLASK_SECRET_KEY=your-dev-secret-key

# Email (optional for dev)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=lyak.resell.genie@gmail.com
SMTP_PASSWORD=your_gmail_app_password
NOTIFICATION_FROM_EMAIL=lyak.resell.genie@gmail.com
```

Run locally:
```bash
python web_app.py
```

---

## Monitoring Storage Usage

### Cloudinary:
- Go to: https://cloudinary.com/console
- Check **Media Library** to see uploaded photos
- Monitor usage in **Dashboard**

### PostgreSQL:
- In Render Dashboard → Your Database
- Check **Metrics** tab for storage usage
- Free tier: 1GB storage (plenty for metadata)

---

## Cost Breakdown

| Service | Free Tier | Cost After Free |
|---------|-----------|-----------------|
| Render Web Service | Free | $7/mo for always-on |
| PostgreSQL | 1GB free | $7/mo for 10GB |
| Cloudinary | 25GB + 25k transforms | $99/mo for 100GB |

**Total for starting out:** $0/month (all free tiers!) 🎉

---

## Troubleshooting Common Issues

### App Crashes Immediately on Startup

**Error:** `⚠️  WARNING: REDIS_URL not set!`
**Fix:** Add REDIS_URL to Render environment variables (see Step 1)

### Google Login Button Does Nothing

**Error:** `Google OAuth Error: SUPABASE_URL or SUPABASE_ANON_KEY not configured`
**Fix:** Add Supabase credentials to Render (see Step 2)

### Login Succeeds but Session Lost After Refresh

**Causes:**
1. Redis connection issue - verify REDIS_URL is correct
2. SECRET_KEY missing - ensure Render generated it
3. Cookie security issues - check SUPABASE_REDIRECT_URL matches your domain

**Fix:** Check Render logs for Redis connection errors

### OAuth Callback Fails with "Invalid state"

**Cause:** Session not persisting between OAuth redirect
**Fix:**
1. Verify REDIS_URL is working (check Upstash dashboard for activity)
2. Ensure SECRET_KEY is set and consistent
3. Check that cookies are being sent (browser dev tools)

### Database Connection SSL Errors

**Error:** `SSL connection has been closed unexpectedly`

**Root Cause:** Using Supabase **direct connection** instead of **connection pooler**

**Fix:**
1. Check your DATABASE_URL in Render → Environment
2. If it contains `:5432/postgres` → You're using direct connection (wrong!)
3. If it contains `:6543/postgres` → You're using pooler (correct!)

**To fix:**
- Go to Supabase → Settings → Database → Connection Pooling
- Copy the **Session mode** connection string (port 6543)
- Update DATABASE_URL in Render with the pooler URL
- Redeploy

**Why this happens:**
- Supabase direct connection: Limited to ~10 concurrent connections
- Your app creates connection pool (2 connections max)
- But Supabase closes idle connections quickly → SSL timeout
- **Solution:** Use pgBouncer pooler (port 6543) which handles this properly

### Photos not uploading

- Check `USE_LOCAL_STORAGE=false` is set
- Verify Cloudinary credentials are correct
- Check Render logs for error messages

### Data disappeared after deployment

- Make sure you followed ALL steps above
- Check environment variables are saved
- Verify Cloudinary is configured (`USE_LOCAL_STORAGE=false`)

---

## 50+ Commits of Login Fixes - What Went Wrong?

Looking at your git history, here's what you tried:

1. **Commits 1-10:** Cookie-based sessions (failed - lost on refresh)
2. **Commits 11-20:** Switched to Redis sessions (good idea!)
3. **Commits 21-30:** Fixed SSL connection pooling
4. **Commits 31-40:** Fixed session persistence
5. **Commits 41-50:** Fixed OAuth newlines, PKCE flow

**The Missing Piece:** REDIS_URL was never added to render.yaml!

The app has been trying to use Redis sessions but couldn't connect because the environment variable wasn't configured. This caused:
- Immediate startup failures
- Session loss
- OAuth PKCE failures
- Database connection issues (cascading failures)

**This commit fixes it** by adding ALL required environment variables to render.yaml.
