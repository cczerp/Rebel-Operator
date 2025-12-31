# Photo Upload & Cleanup Fixes - Implementation Summary

## ✅ **Fixes Implemented**

### Fix #1: Added Page Unload Cleanup Handler ✅
**File**: `templates/create.html`
**Status**: ✅ COMPLETE

**Changes**:
- Added `cleanupTempPhotos()` function that:
  - Only cleans up photos in `temp-photos` bucket
  - Only runs if user hasn't saved (no draft/listing created)
  - Only runs if not editing existing draft/listing
  - Filters URLs to only include `temp-photos` bucket
  
- Added event handlers:
  - `beforeunload` - Cleans up when user closes tab/navigates away
  - `visibilitychange` - Cleans up when tab becomes hidden
  
- Added `hasBeenSaved` tracking:
  - Marks as saved when `saveListing()` succeeds
  - Prevents cleanup of photos that should persist

**Code Location**: Lines ~1655-1720 in `templates/create.html`

---

### Fix #2: Added Logging to Upload Endpoint ✅
**File**: `routes_main.py`
**Status**: ✅ COMPLETE

**Changes**:
- Added logging before upload to show folder being used
- Added logging after upload to verify which bucket photo was uploaded to:
  - ✅ Logs success if uploaded to `temp-photos` bucket
  - ⚠️ Logs warning if uploaded to `listing-images` bucket (WRONG!)
  - ⚠️ Logs warning if uploaded to `draft-images` bucket (unexpected)

**Code Location**: Lines ~152-177 in `routes_main.py`

**Log Messages**:
- `[UPLOAD DEBUG] Uploading {filename} with folder='temp' (should use temp-photos bucket)`
- `[UPLOAD DEBUG] ✅ Photo uploaded to temp-photos bucket: {url}...`
- `[UPLOAD DEBUG] ⚠️ Photo uploaded to listing-images bucket (WRONG!): {url}...`

---

### Fix #3: Added Logging to Storage Manager ✅
**File**: `src/storage/supabase_storage.py`
**Status**: ✅ COMPLETE

**Changes**:
- Added logging when determining which bucket to use:
  - Logs bucket name being used for each folder type
  - Logs expected bucket name for comparison
  
- Added logging after upload:
  - Verifies bucket name appears in public URL
  - Logs full public URL (first 150 chars)

**Code Location**: Lines ~121-127 and ~207-212 in `src/storage/supabase_storage.py`

**Log Messages**:
- `[STORAGE DEBUG] Using temp bucket: {bucket} (expected: temp-photos)`
- `[STORAGE DEBUG] ✅ Bucket '{bucket}' confirmed in URL`
- `[STORAGE DEBUG] Public URL: {url}...`

---

### Fix #4: Added Logging to Analyzer Endpoint ✅
**File**: `routes_main.py`
**Status**: ✅ COMPLETE

**Changes**:
- Added logging when analyzer receives photo URLs:
  - Logs which bucket each URL is from
  - ✅ Logs success if URL from `temp-photos` bucket (expected)
  - ⚠️ Logs warning if URL from `listing-images` bucket (unexpected for new uploads)
  - ℹ️ Logs info if URL from `draft-images` bucket
  - ⚠️ Logs warning if bucket is unclear

**Code Location**: Lines ~732-753 in `routes_main.py`

**Log Messages**:
- `[ANALYZE DEBUG] Received {count} photo URL(s) for analysis`
- `[ANALYZE DEBUG] Photo {i}: ✅ URL from temp-photos bucket: {url}...`
- `[ANALYZE DEBUG] Photo {i}: ⚠️ URL from listing-images bucket (unexpected for new uploads): {url}...`

---

## 🔍 **What These Fixes Do**

### 1. **Prevents Photo Accumulation**
- Cleanup handler automatically deletes temp photos when user navigates away
- Only cleans up unsaved photos (doesn't delete saved drafts/listings)
- Uses `navigator.sendBeacon` for reliability (works even if page is closing)

### 2. **Identifies Bucket Misconfiguration**
- Logging shows exactly which bucket photos are uploaded to
- If photos end up in wrong bucket, logs will clearly show it
- Helps identify if environment variables are misconfigured

### 3. **Debug Analyzer Issues**
- Logs show which bucket URLs analyzer receives
- Can identify if analyzer is getting wrong URLs (listing-images vs temp-photos)
- Helps debug why Gemini might be failing (wrong/stale photos)

---

## 📋 **Testing Checklist**

After deployment, verify:

- [ ] **Upload Flow**:
  - [ ] Upload photos → Check logs for `[UPLOAD DEBUG]` messages
  - [ ] Verify logs show `✅ Photo uploaded to temp-photos bucket`
  - [ ] Check Supabase → Verify photos are in `temp-photos` bucket (not `listing-images`)

- [ ] **Cleanup Flow**:
  - [ ] Upload photos (don't save)
  - [ ] Navigate away from page
  - [ ] Check Supabase → Verify photos are deleted from `temp-photos` bucket
  - [ ] Check browser console → Look for `[CLEANUP]` messages

- [ ] **Save Flow**:
  - [ ] Upload photos
  - [ ] Save as draft or create listing
  - [ ] Navigate away → Photos should NOT be deleted (they're saved)
  - [ ] Check logs → Should NOT see cleanup messages

- [ ] **Analyzer Flow**:
  - [ ] Upload photos
  - [ ] Click "Analyze with AI"
  - [ ] Check logs for `[ANALYZE DEBUG]` messages
  - [ ] Verify logs show `✅ URL from temp-photos bucket`
  - [ ] If Gemini fails, check logs to see which bucket URLs came from

---

## 🔧 **Next Steps if Issues Persist**

### If Photos Still End Up in `listing-images`:

1. **Check Environment Variables on Render**:
   - Verify `SUPABASE_BUCKET_TEMP=temp-photos`
   - Verify `SUPABASE_BUCKET_LISTINGS=listing-images`
   - Verify `SUPABASE_BUCKET_DRAFTS=draft-images`

2. **Check Logs**:
   - Look for `[STORAGE DEBUG] Using temp bucket: {bucket}`
   - If bucket name is wrong, environment variable is misconfigured

3. **Check for Code Paths Uploading to Wrong Bucket**:
   - Search codebase for `folder='listings'` in upload calls
   - Should only be used when publishing, not during initial upload

### If Cleanup Doesn't Work:

1. **Check Browser Console**:
   - Look for `[CLEANUP]` messages
   - Check for JavaScript errors

2. **Check Backend Logs**:
   - Look for `/api/cleanup-temp-photos` requests
   - Check if cleanup endpoint is being called

3. **Test Cleanup Endpoint Directly**:
   - Manually call `/api/cleanup-temp-photos` with test URLs
   - Verify it works independently

### If Analyzer Still Fails:

1. **Check Analyzer Logs**:
   - Look for `[ANALYZE DEBUG]` messages showing which bucket URLs are from
   - If URLs are from `listing-images`, that's the problem

2. **Check Download Logs**:
   - Look for `[ANALYZE DEBUG]` messages showing download success/failure
   - If downloads fail, photos might not exist in that bucket

3. **Compare with Gemini Logs**:
   - Check if Gemini error correlates with wrong bucket URLs
   - Wrong bucket → Photos don't exist → Download fails → Gemini fails

---

## 📝 **Log Messages Reference**

### Upload Flow:
```
[UPLOAD DEBUG] Uploading photo.jpg with folder='temp' (should use temp-photos bucket)
[STORAGE DEBUG] Using temp bucket: temp-photos (expected: temp-photos)
[STORAGE DEBUG] ✅ Bucket 'temp-photos' confirmed in URL
[STORAGE DEBUG] Public URL: https://xxx.supabase.co/storage/v1/object/public/temp-photos/...
[UPLOAD DEBUG] ✅ Photo uploaded to temp-photos bucket: https://xxx.supabase.co/...
```

### Cleanup Flow:
```
[CLEANUP] Cleaning up 3 temp photos
[CLEANUP] Cleanup request sent for 3 photos
```

### Analyzer Flow:
```
[ANALYZE DEBUG] Received 3 photo URL(s) for analysis
[ANALYZE DEBUG] Photo 1: ✅ URL from temp-photos bucket: https://xxx.supabase.co/...
[ANALYZE DEBUG] Downloading image 1/3 from Supabase: https://xxx.supabase.co/...
✅ Downloaded image 1 (245678 bytes) to /tmp/xxx.jpg
```

---

**Last Updated**: Implementation complete
**Status**: ✅ All fixes implemented and ready for testing

