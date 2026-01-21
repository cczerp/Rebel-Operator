# Supabase Storage Integration Guide

## Overview

The application now uses **Supabase Storage** for photo management with a temporary/permanent bucket system:

- **Temp Bucket** (`temp-photos`): Photos uploaded but not yet saved as draft
- **Drafts Bucket** (`draft-photos`): Photos saved with a draft listing

## Environment Variables Required

Add these to your `.env` file or Render environment:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-or-service-key

# Optional: Custom bucket names (defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-photos
```

## Supabase Dashboard Setup

### 1. Create Storage Buckets

1. Go to your Supabase Dashboard → **Storage**
2. Click **"New bucket"**
3. Create two buckets:
   - **Name**: `temp-photos`
     - **Public**: ✅ Yes (for easy access)
     - **File size limit**: 20MB (Gemini API limit)
   - **Name**: `draft-photos`
     - **Public**: ✅ Yes
     - **File size limit**: 20MB

### 2. Set Up Row Level Security (RLS) Policies

For both buckets, you need to allow authenticated users to upload/read/delete:

**For `temp-photos` bucket:**
```sql
-- Allow authenticated users to upload
CREATE POLICY "Authenticated users can upload temp photos"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'temp-photos');

-- Allow authenticated users to read temp photos
CREATE POLICY "Authenticated users can read temp photos"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'temp-photos');

-- Allow authenticated users to delete temp photos
CREATE POLICY "Authenticated users can delete temp photos"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'temp-photos');
```

**For `draft-photos` bucket:**
```sql
-- Allow authenticated users to upload draft photos
CREATE POLICY "Authenticated users can upload draft photos"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'draft-photos');

-- Allow authenticated users to read draft photos
CREATE POLICY "Authenticated users can read draft photos"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'draft-photos');

-- Allow authenticated users to delete draft photos
CREATE POLICY "Authenticated users can delete draft photos"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'draft-photos');
```

**OR** use the Supabase Dashboard:
1. Go to **Storage** → Select bucket → **Policies**
2. Click **"New Policy"**
3. Use the template: **"Allow authenticated users to perform all operations"**
4. Apply to both buckets

## How It Works

### Photo Upload Flow

1. **User uploads photos** → Photos compressed and uploaded to `temp-photos` bucket
2. **Photos displayed** → Frontend shows images from Supabase Storage URLs
3. **User clicks "Save as Draft"** → Photos moved from `temp-photos` to `draft-photos` bucket
4. **User leaves without saving** → Frontend calls cleanup endpoint to delete temp photos

### Gemini Analysis Flow

1. **User clicks "Analyze with AI"** → Frontend sends Supabase Storage URLs
2. **Backend downloads** → Photos downloaded from Supabase to temp files
3. **Gemini analyzes** → Temp files sent to Gemini API
4. **Cleanup** → Temp files deleted after analysis

### Cleanup Mechanism

- **Automatic**: When user saves draft, photos move from temp to drafts
- **Manual**: Frontend calls `/api/cleanup-temp-photos` when user leaves page
- **Scheduled** (optional): Set up cron job to clean old temp photos (older than 24 hours)

## File Size Limits

- **Supabase bucket limit**: 20MB (set in bucket settings)
- **Gemini API limit**: 20MB per image
- **Client-side validation**: Added in upload endpoint

## Troubleshooting

### "Storage service unavailable" error

- Check `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
- Verify buckets exist in Supabase Dashboard
- Check RLS policies allow authenticated users

### Photos not displaying

- Verify buckets are set to **Public**
- Check browser console for CORS errors
- Verify Supabase Storage URLs are correct format

### "Failed to download photo" error

- Check RLS policies allow SELECT operations
- Verify photo URL is valid Supabase Storage URL
- Check network connectivity

### Photos not moving to drafts

- Verify `draft-photos` bucket exists
- Check RLS policies allow INSERT to `draft-photos`
- Check server logs for specific error messages

## Migration from Local/Cloudinary Storage

If you were using local storage or Cloudinary:

1. **Existing photos**: Will continue to work (legacy support)
2. **New uploads**: Will use Supabase Storage
3. **Gradual migration**: Can migrate old photos to Supabase Storage later

## Testing

1. Upload a photo → Should appear in `temp-photos` bucket
2. Save as draft → Photo should move to `draft-photos` bucket
3. Analyze with AI → Should download and analyze successfully
4. Leave page without saving → Temp photos should be cleaned up

