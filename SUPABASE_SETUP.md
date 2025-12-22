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

### 2. Set Bucket Policies

After creating the bucket, set up Row Level Security (RLS) policies:

1. Click on the `listing-images` bucket
2. Go to **Policies** tab
3. Add these policies:

#### Policy 1: Public Read Access
```sql
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'listing-images' );
```

#### Policy 2: Authenticated Upload
```sql
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'listing-images'
  AND auth.role() = 'authenticated'
);
```

#### Policy 3: Users can update their own files
```sql
CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'listing-images'
  AND auth.uid()::text = (storage.foldername(name))[1]
);
```

#### Policy 4: Users can delete their own files
```sql
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'listing-images'
  AND auth.uid()::text = (storage.foldername(name))[1]
);
```

### 3. Verify Environment Variables

Make sure these environment variables are set in your Render.com dashboard:

- **SUPABASE_URL**: Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
- **SUPABASE_ANON_KEY**: Your Supabase anonymous/public key

To find these values:
1. Go to your Supabase project dashboard
2. Click **Settings** → **API**
3. Copy:
   - **Project URL** → use as `SUPABASE_URL`
   - **anon/public key** → use as `SUPABASE_ANON_KEY`

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

**Error: "Upload failed: new row violates row-level security policy"**
- Set up the bucket policies as described in Step 2
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
