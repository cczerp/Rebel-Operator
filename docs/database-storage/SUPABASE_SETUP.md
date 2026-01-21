# Supabase Storage Setup Guide

Complete guide for setting up Supabase Storage integration with Rebel Operator's photo management system.

---

## Overview

The application uses **Supabase Storage** with a multi-bucket system for photo lifecycle management:

- **temp-photos**: Temporary uploads during scanning
- **draft-images**: Saved drafts + pending Hall of Records images
- **listing-images**: Active marketplace listings
- **vault**: Private user collections
- **hall-of-records**: Public collectibles database

---

## Quick Setup

### 1. Environment Variables

Add these to your `.env` file or Render environment:

```bash
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Optional: Custom bucket names (defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
SUPABASE_BUCKET_VAULT=vault
SUPABASE_BUCKET_HALL=hall-of-records
```

### 2. Get Your Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → Use as `SUPABASE_URL`
   - **service_role** key → Use as `SUPABASE_KEY` (for server-side)

---

## Supabase Dashboard Setup

### Step 1: Create Storage Buckets

Go to your Supabase Dashboard → **Storage** → Click **"New bucket"**

Create these buckets:

#### 1. **temp-photos**
- **Public**: ✅ Yes
- **File size limit**: 20MB
- **Purpose**: Temporary uploads during analysis

#### 2. **draft-images**
- **Public**: ✅ Yes (or PRIVATE with RLS)
- **File size limit**: Unlimited
- **Purpose**: Saved drafts + pending Hall images

#### 3. **listing-images**
- **Public**: ✅ Yes (required for marketplace)
- **File size limit**: Unlimited
- **Purpose**: Active public listings

#### 4. **vault**
- **Public**: ❌ No (PRIVATE)
- **File size limit**: Unlimited
- **Purpose**: Private user collections

#### 5. **hall-of-records**
- **Public**: ✅ Yes
- **File size limit**: Unlimited
- **Purpose**: Approved collectibles database

### Step 2: Set Up Row Level Security (RLS) Policies

For each bucket, you need to allow authenticated users to upload/read/delete.

**Option A: Use Dashboard (Easiest)**

1. Go to **Storage** → Select bucket → **Policies**
2. Click **"New Policy"**
3. Use template: **"Allow authenticated users to perform all operations"**
4. Apply to all buckets

**Option B: Use SQL (Advanced)**

Run the SQL from `/supabase_vault_rls_policies.sql` file in your project root, or use these examples:

```sql
-- Example for temp-photos bucket
CREATE POLICY "Authenticated users can upload temp photos"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'temp-photos');

CREATE POLICY "Authenticated users can read temp photos"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'temp-photos');

CREATE POLICY "Authenticated users can delete temp photos"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'temp-photos');
```

Repeat for each bucket, replacing `'temp-photos'` with the bucket name.

---

## How One URL & Key Works

### Single Client Initialization

The code creates **one Supabase client** with your URL and key:

```python
# One client for all buckets
self.client = create_client(self.supabase_url, self.supabase_key)
```

### Bucket Selection by Name

All operations specify the bucket by name:

```python
# Upload to temp-photos
self.client.storage.from_('temp-photos').upload(...)

# Upload to draft-images
self.client.storage.from_('draft-images').upload(...)

# Upload to listing-images
self.client.storage.from_('listing-images').upload(...)
```

✅ **One URL** → `SUPABASE_URL`
✅ **One Key** → `SUPABASE_KEY` (service_role for server)
✅ **Bucket names** → Specified in code, configurable via env vars

---

## Key Type Recommendations

### For Server-Side (Flask Backend)
- Use `SUPABASE_KEY` with your **service_role key**
- Bypasses RLS (required for backend operations)
- This is what the current code uses

### For Client-Side (Optional)
- Use `SUPABASE_ANON_KEY` with your **anon key**
- Respects RLS policies
- Only if you add direct client-to-Supabase uploads

---

## Photo Upload Flow

### 1. User Uploads Photos
1. User selects photos via camera or file picker
2. Photos compressed (max 20MB, quality 85)
3. Uploaded to `temp-photos` bucket
4. Frontend displays images from Supabase Storage URLs

### 2. User Analyzes with AI
1. Backend downloads photos from `temp-photos`
2. Converts to base64 for AI API
3. AI analyzes and returns results
4. Temporary files cleaned up

### 3. User Saves as Draft
1. Photos moved from `temp-photos` to `draft-images`
2. Database stores Supabase Storage URLs
3. Temp photos deleted

### 4. User Publishes Listing
1. Photos moved from `draft-images` to `listing-images`
2. Listing becomes public
3. Draft photos deleted

### 5. User Leaves Without Saving
1. Frontend calls cleanup endpoint
2. Temp photos deleted from `temp-photos`

---

## Verification

After setup, verify your configuration:

### Method 1: Command Line
```bash
python test_supabase_connection.py
```

This checks:
- ✅ Environment variables
- ✅ Supabase client connection
- ✅ Bucket listing and permissions
- ✅ File downloads

### Method 2: Web API
If your app is running:
```bash
curl http://localhost:5000/api/test-supabase | python -m json.tool
```

---

## Common Issues

### "SUPABASE_URL: NOT SET"
**Solution**: Create `.env` file with `SUPABASE_URL=https://your-project.supabase.co`

### "Permission denied" errors
**Solution**: Use **service_role key** for `SUPABASE_KEY`, not anon key

### "Bucket not found"
**Solution**: Create buckets in Supabase Dashboard with exact names:
- `temp-photos`
- `draft-images`
- `listing-images`

### Images not loading
**Solution**: Ensure buckets are set to **PUBLIC** in Supabase Dashboard

---

## Next Steps

Once setup is complete:
1. Test photo upload on the Create Listing page
2. Try AI analysis
3. Save a draft
4. Verify images appear correctly

For troubleshooting, see `SUPABASE_TROUBLESHOOTING.md`

For architecture details, see `BUCKET_ARCHITECTURE.md`
