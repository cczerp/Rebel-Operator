# Supabase Storage Troubleshooting Guide

Diagnostic tools and solutions for common Supabase Storage issues.

---

## Quick Diagnostics

### Method 1: Command Line (Recommended)

Run the diagnostic script:

```bash
python test_supabase_connection.py
```

This checks:
- ✅ Environment variables (SUPABASE_URL, keys)
- ✅ Supabase client connection
- ✅ Bucket listing and permissions
- ✅ File downloads (both SDK and HTTP)
- ✅ Common configuration issues

### Method 2: Web API Endpoint

If your app is running:

```bash
curl http://localhost:5000/api/test-supabase | python -m json.tool
```

Or visit in browser: `http://localhost:5000/api/test-supabase`

Returns diagnostic report with:
- Environment variable status
- Connection status
- Bucket information
- Download test results

---

## Common Issues & Solutions

### ❌ "SUPABASE_URL: NOT SET"

**Problem:** Missing environment variable

**Solution:**
1. Create `.env` file in project root
2. Add: `SUPABASE_URL=https://your-project.supabase.co`
3. Get URL from: Supabase Dashboard → Settings → API → Project URL

---

### ❌ "No Supabase API key found"

**Problem:** Missing API key

**Solution:**
1. Add to `.env`: `SUPABASE_KEY=your-service-role-key-here`
2. Get key from: Supabase Dashboard → Settings → API → **service_role** key
3. **Important:** Use `service_role` key (NOT `anon` key)

---

### ⚠️ "Using anon key may cause RLS permission errors"

**Problem:** Using wrong API key type

**Solution:**
1. Replace `SUPABASE_ANON_KEY` with `SUPABASE_KEY` in `.env`
2. Use the **service_role** key to bypass Row Level Security
3. Backend operations require service_role, not anon key

---

### ❌ "HTTP 403: Permission Denied"

**Problem:** Bucket permissions too restrictive OR wrong key type

**Solution Option 1 (Easiest):**
Make buckets PUBLIC:
1. Go to: Supabase Dashboard → Storage → [bucket name]
2. Click "Settings"
3. Enable "Public bucket"
4. Repeat for: `temp-photos`, `draft-images`, `listing-images`

**Solution Option 2 (Use service_role key):**
1. Set `SUPABASE_KEY` with service_role key in `.env`
2. Service_role bypasses RLS and works with private buckets

---

### ❌ "HTTP 404: File Not Found"

**Problem:** File doesn't exist at the URL

**Diagnosis:**
1. Check file was uploaded successfully (check server logs)
2. Verify URL format: `https://[project].supabase.co/storage/v1/object/public/[bucket]/[file]`
3. Use diagnostic tools to list bucket contents
4. Check you're using the correct bucket name

**Solution:**
- Ensure upload endpoint returns success
- Verify bucket name matches environment variable
- Check database for correct photo URLs

---

### ❌ "Download timeout" or "Network error"

**Problem:** Connection to Supabase is slow or blocked

**Solution:**
1. Check internet connection
2. Verify Supabase project URL accessible in browser
3. Check firewall settings
4. Try again (may be temporary network issue)
5. Increase timeout in code if consistently slow

---

### ❌ "Bucket not found"

**Problem:** Bucket doesn't exist in Supabase

**Solution:**
1. Go to Supabase Dashboard → Storage
2. Create missing buckets:
   - `temp-photos` (public, 20MB limit)
   - `draft-images` (public or private)
   - `listing-images` (public, required)
   - `vault` (private)
   - `hall-of-records` (public)
3. Ensure bucket names match `.env` variables

---

### ❌ "Images not loading in frontend"

**Problem:** Photos uploaded but not displaying

**Diagnosis:**
1. Check browser console for errors
2. Verify photo URLs in network tab
3. Check if bucket is PUBLIC
4. Test URL directly in browser

**Solution:**
- Ensure bucket is PUBLIC (for frontend display)
- Verify URL format is correct
- Check CORS settings in Supabase
- Clear browser cache

---

### ❌ "Couldn't download image from Supabase"

**Problem:** Backend can't download for AI analysis

**Common Causes:**
1. Wrong API key (using anon instead of service_role)
2. Bucket is private and RLS blocks access
3. File doesn't exist at URL
4. Network/timeout issues

**Solution:**
1. Use diagnostic script: `python test_supabase_connection.py`
2. Verify service_role key in `.env`
3. Make bucket PUBLIC or use service_role key
4. Check logs for specific error message

---

## Environment Variables Reference

Required `.env` configuration:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Supabase Buckets (Optional - defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
SUPABASE_BUCKET_VAULT=vault
SUPABASE_BUCKET_HALL=hall-of-records
```

---

## Implementation Details

### What Was Changed

The codebase was migrated from local storage to Supabase Storage:

#### 1. Storage Manager (`src/storage/supabase_storage.py`)
- ✅ Upload photos to Supabase buckets
- ✅ Download photos from Supabase URLs
- ✅ Move photos between buckets
- ✅ Delete photos from buckets
- ✅ Get public URLs for images

#### 2. Upload Endpoint (`routes_main.py`)
- ✅ Uploads to `temp-photos` bucket
- ✅ Returns Supabase Storage public URLs
- ✅ 20MB file size validation
- ✅ Image compression before upload

#### 3. Save Draft Endpoint
- ✅ Moves photos from `temp-photos` to `draft-images`
- ✅ Stores Supabase URLs in database

#### 4. AI Analyzer
- ✅ Downloads photos from Supabase before analysis
- ✅ Creates temp files for AI API
- ✅ Cleans up temp files after analysis

#### 5. Cleanup Endpoint
- ✅ `/api/cleanup-temp-photos` - Deletes orphaned temp photos
- ✅ Called when user leaves without saving

### Why Download is Needed for AI

**Question:** Why download images if they're in Supabase?

**Answer:** AI APIs (Gemini, Claude) require images as **base64-encoded strings** in the JSON request. They cannot access URLs directly.

**Flow:**
1. Download image from Supabase Storage URL
2. Encode to base64
3. Send base64 string to AI API
4. Clean up temporary file

This is an AI API requirement, not a code limitation.

---

## Photo Lifecycle

```
User Uploads Photo
    ↓
Compress (< 20MB, quality 85)
    ↓
Upload to: temp-photos bucket
    ↓
┌─────────────────────────────┐
│ User Actions:               │
├─────────────────────────────┤
│ Save Draft?                 │
│   → Move to draft-images    │
│                             │
│ Publish Listing?            │
│   → Move to listing-images  │
│                             │
│ Analyze with AI?            │
│   → Download → Base64       │
│   → Send to AI API          │
│   → Cleanup temp file       │
│                             │
│ Leave Page (no save)?       │
│   → Delete from temp-photos │
└─────────────────────────────┘
```

---

## Debugging Steps

### 1. Verify Environment
```bash
# Check .env file exists
ls -la .env

# Verify variables are set
grep SUPABASE .env
```

### 2. Test Connection
```bash
# Run diagnostic
python test_supabase_connection.py

# Check web endpoint
curl http://localhost:5000/api/test-supabase
```

### 3. Check Supabase Dashboard
1. Verify buckets exist
2. Check bucket is PUBLIC
3. Verify RLS policies (if private)
4. Check files are uploading

### 4. Check Application Logs
```bash
# Watch server logs for errors
tail -f logs/app.log  # or wherever your logs are

# Look for:
# - Upload failures
# - Download errors
# - Permission denied
# - 403/404 errors
```

### 5. Test Direct Upload
Use diagnostic script to test upload/download cycle:
```bash
python test_supabase_connection.py
```

---

## Getting Help

Still stuck? Check:

1. **Setup Guide**: `SUPABASE_SETUP.md` - Complete setup instructions
2. **Architecture**: `BUCKET_ARCHITECTURE.md` - Bucket system details
3. **Server Logs**: Check for specific error messages
4. **Supabase Logs**: Dashboard → Logs → Filter by storage events

Common patterns to search for in logs:
- `Permission denied`
- `Bucket not found`
- `403` or `404`
- `timeout`
- `couldn't download`
