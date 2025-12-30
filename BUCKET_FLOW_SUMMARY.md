# Supabase Storage Bucket Flow Summary

## Your 3-Bucket System

1. **`temp-photos`** - Temporary uploads (20MB limit, public, no RLS)
   - Photos uploaded but not saved
   - Cleaned up when user leaves page without saving

2. **`draft-images`** - Saved draft photos
   - Photos moved here when "Save as Draft" is clicked
   - Stays here until listing is published

3. **`listing-images`** - Posted listing photos
   - Photos moved here when draft is published/activated
   - Permanent storage for active listings

## Complete Flow

```
User Uploads Photo
    ↓
Upload to: temp-photos bucket
    ↓
┌─────────────────────────────┐
│ User Action:                │
├─────────────────────────────┤
│ Save Draft?                 │
│   → Move to draft-images    │
│                             │
│ Publish Listing?            │
│   → Move to listing-images  │
│                             │
│ Analyze with AI?            │
│   → Download → Base64      │
│   → Send to Gemini          │
│   → Cleanup temp file       │
│                             │
│ Leave Page (no save)?       │
│   → Delete from temp-photos │
└─────────────────────────────┘
```

## Why Download is Needed for Gemini

**Question**: Why download images if they're already in Supabase Storage?

**Answer**: The Gemini API requires images as **base64-encoded strings** in the JSON request body. It cannot access URLs directly. So we must:

1. Download image from Supabase Storage URL
2. Encode to base64
3. Send base64 string to Gemini API
4. Clean up temporary file

This is a Gemini API requirement, not a limitation of our code.

## Environment Variables Needed

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Optional (defaults shown)
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

## Cloudinary Removal

✅ All Cloudinary logic has been removed. The system now exclusively uses Supabase Storage.

