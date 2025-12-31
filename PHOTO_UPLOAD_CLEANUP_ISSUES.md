# Photo Upload & Cleanup Issues - Critical Discovery

## 🚨 **CRITICAL ISSUES FOUND**

Based on user observation: Photos are ending up in `listing-images` bucket when they should be in `temp-photos` bucket, and cleanup isn't happening.

---

## ❌ **Issue #1: No Page Unload Cleanup Handler**

**Problem**: 
- Cleanup endpoint exists at `/api/cleanup-temp-photos`
- **BUT** there's no JavaScript event handler to call it when user navigates away
- Result: Temporary photos are NEVER deleted

**Location**: `templates/create.html`
- Search for `beforeunload`, `unload`, `pagehide`, `visibilitychange` - **NOT FOUND**

**Impact**:
- Photos accumulate in Supabase Storage
- Storage costs increase
- Potential data leakage (unsaved photos persist)

**Fix Required**:
```javascript
// Add to create.html
window.addEventListener('beforeunload', async function(e) {
    // Only cleanup if there are unsaved photos
    if (uploadedPhotos.length > 0) {
        // Send cleanup request (fire and forget - don't wait)
        navigator.sendBeacon('/api/cleanup-temp-photos', JSON.stringify({
            photos: uploadedPhotos
        }));
    }
});

// Also handle visibility change (when tab becomes hidden)
document.addEventListener('visibilitychange', async function() {
    if (document.hidden && uploadedPhotos.length > 0) {
        // Cleanup when tab becomes hidden (user navigated away)
        try {
            await fetch('/api/cleanup-temp-photos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({photos: uploadedPhotos}),
                keepalive: true  // Important: ensures request completes even if page closes
            });
        } catch (e) {
            // Ignore errors - cleanup is best effort
        }
    }
});
```

---

## ❌ **Issue #2: Photos Ending Up in Wrong Bucket**

**User Observation**: 
- Photos are in `listing-images` bucket
- Should be in `temp-photos` bucket

**Code Analysis**:

### Upload Endpoint (`routes_main.py:102-195`)
- ✅ Uses `folder='temp'` (correct)
- ✅ Maps to `temp-photos` bucket via `SupabaseStorageManager`
- ✅ Code looks correct

### Bucket Mapping (`src/storage/supabase_storage.py:121-127`)
```python
if folder == 'temp':
    bucket = self.temp_bucket  # Should be 'temp-photos'
elif folder == 'listings':
    bucket = self.listings_bucket  # Should be 'listing-images'
else:  # 'drafts' or default
    bucket = self.drafts_bucket  # Should be 'draft-images'
```

**Possible Causes**:
1. **Environment variable misconfiguration**: `SUPABASE_BUCKET_TEMP` might be set to `listing-images`
2. **Photos were moved**: Photos might have been moved to `listing-images` during publish
3. **Old code path**: Some code might be uploading directly to `listing-images`

**Investigation Needed**:
- Check environment variables on Render
- Verify `SUPABASE_BUCKET_TEMP` is set to `temp-photos`
- Check if any code is uploading with `folder='listings'` during initial upload

---

## ❌ **Issue #3: Cleanup Only Works for temp-photos Bucket**

**Location**: `routes_main.py:197-232`

**Current Code**:
```python
for url in photo_urls:
    # Only delete from temp bucket
    if 'supabase.co' in url and 'temp-photos' in url:
        if storage.delete_photo(url):
            deleted += 1
```

**Problem**: 
- Cleanup endpoint only deletes from `temp-photos` bucket
- If photos somehow end up in `listing-images`, they won't be cleaned up
- **BUT** this is actually correct behavior - we only want to cleanup temp photos

**Fix**: 
- The cleanup logic is correct (only cleanup temp photos)
- The issue is that photos shouldn't be in `listing-images` in the first place
- Need to fix the root cause (upload going to wrong bucket)

---

## 🔍 **How This Affects Gemini Analyzer**

**Potential Impact**:

1. **Wrong Bucket URLs**:
   - If analyzer receives URLs pointing to `listing-images` bucket
   - But photos don't exist there (or were moved/deleted)
   - Download fails → Analyzer fails

2. **Stale/Deleted Photos**:
   - Photos in `listing-images` might be from old sessions
   - Photos might have been deleted
   - Analyzer tries to download → 404 error

3. **Multiple Photo Versions**:
   - Temp photos in `temp-photos` bucket
   - Same photos in `listing-images` bucket
   - Analyzer gets wrong URLs → downloads wrong/old photos

**This Could Explain Gemini Failure**:
- Analyzer downloads images from wrong bucket
- Images don't exist or are corrupted
- Gemini receives invalid image data
- Gemini rejects with "Invalid request to Gemini. Make sure photos are valid images."

---

## ✅ **Current Code Flow (What Should Happen)**

1. **User uploads photos** → `/api/upload-photos`
   - Uploads to `temp-photos` bucket ✅ (code is correct)
   - Returns Supabase Storage URLs

2. **User analyzes photos** → `/api/analyze`
   - Receives URLs (should be from `temp-photos`)
   - Downloads images from Supabase
   - Sends to Gemini

3. **User saves draft** → `/api/save-draft`
   - Photos stay in `temp-photos` (or move to `draft-images`)
   - URLs are stored in database

4. **User publishes listing** → Publishing endpoint
   - Photos move from `draft-images` to `listing-images` ✅ (correct)
   - Or from `temp-photos` to `listing-images`

5. **User navigates away without saving** → Should trigger cleanup
   - ❌ **MISSING**: No cleanup handler exists
   - Photos remain in `temp-photos` forever

---

## 🔧 **Required Fixes**

### Fix #1: Add Page Unload Cleanup Handler
**Priority**: HIGH
**File**: `templates/create.html`
**Action**: Add `beforeunload` and `visibilitychange` event handlers

### Fix #2: Verify Bucket Configuration
**Priority**: HIGH
**Action**: 
- Check Render environment variables
- Verify `SUPABASE_BUCKET_TEMP=temp-photos`
- Verify `SUPABASE_BUCKET_LISTINGS=listing-images`
- Verify `SUPABASE_BUCKET_DRAFTS=draft-images`

### Fix #3: Add Logging to Upload Endpoint
**Priority**: MEDIUM
**File**: `routes_main.py`
**Action**: Add logging to show which bucket photos are uploaded to

### Fix #4: Verify Analyzer Receives Correct URLs
**Priority**: HIGH
**File**: `routes_main.py` and `templates/create.html`
**Action**: 
- Log URLs being sent to analyzer
- Verify they point to `temp-photos` bucket
- Check if URLs point to `listing-images` (wrong!)

---

## 📝 **Testing Checklist**

After fixes:
- [ ] Upload photos → Verify they go to `temp-photos` bucket
- [ ] Navigate away without saving → Verify cleanup is called
- [ ] Check Supabase → Verify photos are deleted from `temp-photos`
- [ ] Analyze photos → Verify analyzer receives URLs from `temp-photos`
- [ ] Check logs → Verify no photos end up in `listing-images` during upload
- [ ] Save draft → Verify photos move to `draft-images` (if implemented)
- [ ] Publish listing → Verify photos move to `listing-images` only then

---

## 🎯 **Next Steps**

1. **First**: Check environment variables on Render
2. **Second**: Add cleanup handler to frontend
3. **Third**: Add logging to verify bucket usage
4. **Fourth**: Test end-to-end flow
5. **Fifth**: Verify Gemini analyzer now works (might fix the issue!)

---

**Last Updated**: Based on user discovery that photos are in wrong bucket and cleanup isn't working
**Status**: Critical issues identified - fixes needed before Gemini analyzer will work correctly

