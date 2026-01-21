# Supabase Storage Migration - Implementation Summary

## ✅ What Was Implemented

### 1. Supabase Storage Manager (`src/storage/supabase_storage.py`)
- ✅ Upload photos to Supabase Storage buckets
- ✅ Download photos from Supabase Storage URLs
- ✅ Move photos from temp bucket to drafts bucket
- ✅ Delete photos from buckets
- ✅ Get public URLs for images

### 2. Updated Upload Endpoint (`routes_main.py`)
- ✅ Now uploads to Supabase Storage `temp-photos` bucket
- ✅ Returns Supabase Storage public URLs (not local paths)
- ✅ Added 20MB file size validation
- ✅ Compresses images before upload

### 3. Updated Save Draft Endpoint
- ✅ Moves photos from `temp-photos` to `draft-photos` bucket when saving
- ✅ Stores Supabase Storage URLs in database

### 4. Updated Gemini Analyzer
- ✅ Downloads photos from Supabase Storage URLs before analysis
- ✅ Creates temp files for Gemini API
- ✅ Cleans up temp files after analysis

### 5. Cleanup Endpoint
- ✅ `/api/cleanup-temp-photos` - Deletes orphaned temp photos
- ✅ Called when user leaves page without saving

## 🔧 Required Configuration

### Environment Variables
Add these to your `.env` file or Render environment:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-or-service-key
SUPABASE_BUCKET_TEMP=temp-photos  # Optional, defaults shown
SUPABASE_BUCKET_DRAFTS=draft-photos  # Optional
```

### Supabase Dashboard Setup
1. **Create Buckets**:
   - `temp-photos` (public, 20MB limit)
   - `draft-photos` (public, 20MB limit)

2. **Set RLS Policies**:
   - Allow authenticated users to INSERT, SELECT, DELETE on both buckets
   - See `SUPABASE_STORAGE_SETUP.md` for SQL policies

## 📋 Flow Diagram

```
User Uploads Photo
    ↓
Compress Image (< 20MB)
    ↓
Upload to Supabase: temp-photos bucket
    ↓
Return Supabase Storage URL
    ↓
Frontend displays image
    ↓
┌─────────────────────────┐
│ User Action:            │
├─────────────────────────┤
│ Save Draft? → Move to   │
│   draft-photos bucket    │
│                         │
│ Analyze? → Download →   │
│   Send to Gemini        │
│                         │
│ Leave Page? → Cleanup  │
│   Delete temp photos    │
└─────────────────────────┘
```

## 🚨 Important Notes

1. **Bucket Names**: Must match exactly (`temp-photos` and `draft-photos`)
2. **Public Buckets**: Both buckets must be public for images to display
3. **RLS Policies**: Must allow authenticated users to upload/read/delete
4. **File Size**: 20MB limit enforced (Gemini API requirement)
5. **Legacy Support**: Old local/Cloudinary paths still work for existing photos

## 🧪 Testing Checklist

- [ ] Upload photo → Check `temp-photos` bucket in Supabase Dashboard
- [ ] Save draft → Check photo moved to `draft-photos` bucket
- [ ] Analyze with AI → Should work (downloads from Supabase)
- [ ] Leave page without saving → Temp photos should be deleted
- [ ] View saved draft → Photos should display from `draft-photos` bucket

## 🔄 Migration Path

**If you have existing photos in local storage:**
1. New uploads will use Supabase Storage
2. Old photos will continue to work (legacy support)
3. Can migrate old photos later if needed

## 📝 Next Steps

1. **Set environment variables** in Render dashboard
2. **Create buckets** in Supabase Dashboard
3. **Set RLS policies** (see setup guide)
4. **Test upload flow** end-to-end
5. **Monitor Supabase Storage usage** in dashboard

## 🐛 Troubleshooting

See `SUPABASE_STORAGE_SETUP.md` for detailed troubleshooting guide.

