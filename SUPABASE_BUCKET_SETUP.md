# Supabase Storage Bucket Setup Guide

## The Real Issue: Bucket Permissions

Even with the correct `service_role` key, uploads can fail if the bucket isn't configured properly.

## Step 1: Verify Bucket Exists and is Public

1. Go to **Supabase Dashboard → Storage**
2. Check if `listing-images` bucket exists
3. If it doesn't exist:
   - Click **"New bucket"**
   - Name: `listing-images`
   - **Make it PUBLIC** (toggle "Public bucket" ON)
   - Click **"Create bucket"**

## Step 2: Check Bucket Policies (Even with service_role key)

Even though `service_role` key bypasses RLS, you still need to ensure:

1. **Bucket is Public:**
   - Go to Storage → `listing-images` bucket
   - Check "Public bucket" is enabled
   - If not, click the bucket → Settings → Enable "Public bucket"

2. **Storage Policies (if bucket is private):**
   - If bucket is NOT public, you need storage policies
   - Go to Storage → `listing-images` → Policies
   - Create policy to allow uploads

## Step 3: Test with Diagnostics

Visit: `/api/supabase-diagnostics`

It will show:
- ✅ If bucket exists
- ✅ If bucket is accessible
- ✅ If keys are working

## Common Issues

### Issue 1: Bucket Not Public
**Error:** `Permission denied` or `403`
**Fix:** Enable "Public bucket" in Storage → `listing-images` → Settings

### Issue 2: Bucket Doesn't Exist
**Error:** `Bucket 'listing-images' not found`
**Fix:** Create the bucket in Storage dashboard

### Issue 3: Wrong Bucket Name
**Error:** `Bucket not found`
**Fix:** Verify bucket name is exactly `listing-images` (case-sensitive)

## Quick Test

1. Visit `/api/supabase-diagnostics`
2. Check `bucket_status`:
   ```json
   {
     "listing_images_exists": true,  // Should be true
     "can_list": true                // Should be true
   }
   ```
3. If `listing_images_exists: false`, create the bucket
4. If `can_list: false`, check bucket permissions

## Why service_role Key Still Needs Public Bucket?

The `service_role` key bypasses **database RLS policies**, but **Storage** has its own permission system:
- Public buckets: Anyone can read, but uploads still need proper auth
- Private buckets: Need storage policies even with service_role key

**Recommendation:** Make `listing-images` bucket **PUBLIC** for simplicity.

