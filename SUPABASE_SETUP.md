# Supabase Storage Setup Instructions

## Image Upload Fix - Required Configuration

The image upload feature requires a properly configured Supabase Storage bucket. Follow these steps:

### 1. Create Storage Bucket

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to **Storage** in the left sidebar
3. Click **New Bucket**
4. Configure the bucket:
   - **Name**: `listing-images`
   - **Public bucket**: ✅ **YES** (must be checked for public access)
   - Click **Create bucket**

### 2. Set Bucket Policies (OPTIONAL - Service Role Key Recommended)

**IMPORTANT:** Per Supabase docs: "A public bucket only means there is a public URL available for downloads. All other operations require storage policies."

Since this app uses Flask-Login (not Supabase Auth), we have two options:

#### Option A: Use Service Role Key (RECOMMENDED - Bypasses RLS)

1. Go to Supabase Dashboard → Settings → API
2. Copy the **service_role** key (NOT the anon key)
3. Add to Render environment variables:
   ```
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```
4. The app will automatically use service role key for uploads (bypasses RLS)

#### Option B: Set Storage Policies (Alternative)

If you prefer to use anon key, set up policies in Supabase:

1. Click on the `listing-images` bucket
2. Go to **Policies** tab
3. Add these policies:

**Policy 1: Public Read Access**
```sql
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'listing-images' );
```

**Policy 2: Allow All Uploads (for anon key)**
```sql
CREATE POLICY "Allow all uploads"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'listing-images' );
```

**Note:** Option A (service role key) is recommended because it bypasses RLS entirely and is simpler.

### 3. Verify Environment Variables

Make sure these environment variables are set in your Render.com dashboard:

**Required:**
- **SUPABASE_URL**: Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)

**Required (choose one):**
- **SUPABASE_SERVICE_ROLE_KEY**: Service role key (RECOMMENDED - bypasses RLS)
- **OR SUPABASE_ANON_KEY**: Anonymous/public key (requires storage policies)

To find these values:
1. Go to your Supabase project dashboard
2. Click **Settings** → **API**
3. Copy:
   - **Project URL** → use as `SUPABASE_URL`
   - **service_role key** → use as `SUPABASE_SERVICE_ROLE_KEY` (recommended)
   - **OR anon/public key** → use as `SUPABASE_ANON_KEY` (if not using service role)

### 4. Test the Upload

After configuration:
1. Restart your Render.com deployment (or wait for auto-deploy)
2. Log into your app
3. Go to Create page
4. Try uploading an image
5. Check browser console (F12) for detailed error messages if it fails
6. Check Render.com logs for server-side errors

### Troubleshooting

**Error: "Supabase client not configured"**
- Check that `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set in Render environment variables
- Restart the Render service after adding variables

**Error: "Bucket 'listing-images' not found"**
- Create the bucket as described in Step 1
- Make sure it's named exactly `listing-images`

**Error: "Upload failed: new row violates row-level security policy" or "Permission denied: Storage policies blocking upload"**
- **RECOMMENDED:** Add `SUPABASE_SERVICE_ROLE_KEY` environment variable (bypasses RLS)
- **OR:** Set up storage policies as described in Step 2 (Option B)
- Make sure the bucket is marked as **Public**

**Images upload but don't display**
- Check that the bucket is set to **Public**
- Verify the policies allow SELECT (read access)

### File Structure in Bucket

Images are organized by user and listing:
```
listing-images/
  └── {user_id}/
      └── {listing_uuid}/
          ├── 20241222_120000_image1.jpg
          ├── 20241222_120001_image2.jpg
          └── ...
```

This structure ensures:
- User isolation (users can only access their own folders)
- Listing organization (images grouped by listing)
- No filename conflicts (timestamps prevent collisions)
