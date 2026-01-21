# Supabase Connection Diagnostic Tools

If you're getting "couldn't download image from supabase" errors, use these tools to diagnose the issue.

## Quick Start

### Method 1: Command Line Script (Recommended)

Run this diagnostic script to test your Supabase connection:

```bash
python test_supabase_connection.py
```

This will check:
- ✅ Environment variables (SUPABASE_URL, keys)
- ✅ Supabase client connection
- ✅ Bucket listing and permissions
- ✅ File downloads (both SDK and HTTP)
- ✅ Common configuration issues

### Method 2: Web API Endpoint

If your app is running, visit this endpoint in your browser:

```
http://localhost:5003/api/test-supabase
```

Or use curl:

```bash
curl http://localhost:5003/api/test-supabase | python -m json.tool
```

Returns a JSON diagnostic report with:
- Environment variable status
- Connection status
- Bucket information
- Download test results

## Common Issues & Solutions

### ❌ "SUPABASE_URL: NOT SET"

**Problem:** Missing environment variable

**Solution:**
1. Create a `.env` file in your project root
2. Add: `SUPABASE_URL=https://your-project.supabase.co`
3. Get URL from: https://app.supabase.com → Your Project → Settings → API → Project URL

### ❌ "No Supabase API key found"

**Problem:** Missing API key

**Solution:**
1. Add to `.env`: `SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here`
2. Get key from: https://app.supabase.com → Your Project → Settings → API → service_role key
3. **Important:** Use `service_role` key (NOT `anon` key) to avoid RLS errors

### ⚠️ "Using anon key may cause RLS permission errors"

**Problem:** Using the wrong API key

**Solution:**
1. Replace `SUPABASE_ANON_KEY` with `SUPABASE_SERVICE_ROLE_KEY` in your `.env`
2. The service_role key bypasses Row Level Security (RLS) policies
3. Get it from: https://app.supabase.com → Your Project → Settings → API

### ❌ "HTTP 403: Permission Denied" or "Bucket is private"

**Problem:** Bucket permissions are too restrictive

**Solution - Option 1 (Easiest):**
Make your buckets PUBLIC:
1. Go to: https://app.supabase.com → Storage → [bucket name]
2. Click "Settings"
3. Enable "Public bucket"
4. Repeat for all buckets: `temp-photos`, `draft-images`, `listing-images`

**Solution - Option 2 (More Secure):**
Use service_role key instead of anon key:
- Set `SUPABASE_SERVICE_ROLE_KEY` in your `.env` file
- This bypasses RLS and works with private buckets

### ❌ "HTTP 404: File Not Found"

**Problem:** File doesn't exist at the URL

**Solution:**
1. Check that files are being uploaded to the correct bucket
2. Verify the URL format: `https://[project].supabase.co/storage/v1/object/public/[bucket]/[file]`
3. Check server logs for upload errors
4. Use the diagnostic tools to see which buckets have files

### ❌ "Download timeout" or "Network error"

**Problem:** Connection to Supabase is slow or blocked

**Solution:**
1. Check your internet connection
2. Verify you can access your Supabase project URL in a browser
3. Check if a firewall is blocking access to Supabase
4. Try again - temporary network issues may resolve

## Environment Variables Reference

Add these to your `.env` file:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Optional - bucket names (defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

### Get Your Credentials

1. Go to: https://app.supabase.com
2. Select your project
3. Navigate to: **Settings → API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** → `SUPABASE_SERVICE_ROLE_KEY` (⚠️ Keep secret!)

## For Render Deployment

If deploying to Render, add environment variables in the Render dashboard:

1. Go to your Render service
2. Navigate to: **Environment** tab
3. Add the same variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - (Optional) Bucket name overrides

## Checking Server Logs

When analyzing images, the server logs now include detailed diagnostics:

```bash
# Run your app and check logs
python web_app.py

# Look for these patterns in logs:
# ✅ Success indicators:
[ANALYZE DEBUG] Downloaded image 1 from Supabase...
✅ Downloaded X bytes from bucket/path

# ❌ Error indicators:
❌ Supabase SDK download error: ...
⚠️ RLS POLICY ERROR: ...
💡 SOLUTION: Set SUPABASE_SERVICE_ROLE_KEY...
```

## Still Having Issues?

1. Run the diagnostic script: `python test_supabase_connection.py`
2. Check the full output for specific error messages
3. Follow the "💡 SOLUTION:" suggestions in the output
4. Verify all environment variables are spelled correctly
5. Make sure there are no extra spaces in the variable values
6. Restart your app after changing `.env` variables

## Testing in Production (Render)

If the diagnostic works locally but fails on Render:

1. Check Render environment variables are set correctly
2. View Render logs for detailed error messages
3. Ensure service_role key is set (not just anon key)
4. Verify Render can access Supabase (network/firewall)
5. Check that bucket names match between local and production

## Quick Verification Checklist

- [ ] `.env` file exists in project root
- [ ] `SUPABASE_URL` is set and starts with `https://`
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is set (long random string)
- [ ] All buckets (`temp-photos`, `draft-images`, `listing-images`) exist in Supabase
- [ ] Buckets are either PUBLIC or you're using service_role key
- [ ] Can access Supabase dashboard at your SUPABASE_URL
- [ ] Diagnostic script shows "✅ Connected"
- [ ] Download test shows "✅ SUCCESS"

---

**Need More Help?**
- Supabase Docs: https://supabase.com/docs/guides/storage
- Supabase Storage RLS: https://supabase.com/docs/guides/storage/security/access-control
