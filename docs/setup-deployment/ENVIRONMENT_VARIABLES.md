# Required Environment Variables for Supabase Storage

## Required Variables

Add these to your `.env` file or Render environment variables:

```bash
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-or-service-key

# Supabase Storage Bucket Names (OPTIONAL - defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

## How to Get Your Supabase Credentials

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY` (or use service_role key for admin operations)

## Bucket Configuration

Your Supabase buckets should be set up as:

1. **`temp-photos`**
   - Public: ✅ Yes
   - File size limit: 20MB
   - RLS: Disabled (for now, as you mentioned)

2. **`draft-images`**
   - Public: ✅ Yes
   - File size limit: 20MB (or higher)
   - RLS: Disabled (for now)

3. **`listing-images`**
   - Public: ✅ Yes
   - File size limit: 20MB (or higher)
   - RLS: Disabled (for now)

## Why Download is Needed for Gemini

**Question**: Why does the analyzer download images if they're already in Supabase Storage?

**Answer**: The Gemini API requires images to be sent as **base64-encoded strings** in the JSON request body. It cannot directly access URLs. So we must:
1. Download the image from Supabase Storage URL
2. Encode it to base64
3. Send the base64 string to Gemini API
4. Clean up the temporary file

This is a limitation of the Gemini API format, not our implementation.

## Removing Cloudinary

All Cloudinary logic has been removed. The system now exclusively uses Supabase Storage.

