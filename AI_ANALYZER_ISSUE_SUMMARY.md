# AI Analyzer Issue - Current State & Next Steps

## 🎯 **CRITICAL CONTEXT FOR NEXT AGENT**

The image upload flow is **WORKING PERFECTLY** - images upload to Supabase Storage, display correctly, and the entire flow is stable. **DO NOT BREAK THIS.**

The **ONLY** issue is the AI analyzer (`/api/analyze` endpoint) failing when sending images to Gemini API.

---

## ✅ **What's Working (DO NOT TOUCH)**

1. **Image Upload Flow** (`/api/upload-photos`)
   - Files upload to Supabase Storage `temp-photos` bucket
   - Images display correctly in frontend
   - File validation on frontend works
   - Supabase Storage integration is solid

2. **Image Storage**
   - Supabase Storage buckets: `temp-photos`, `draft-images`, `listing-images`
   - Photos are stored as full Supabase Storage URLs (e.g., `https://xxx.supabase.co/storage/v1/object/public/temp-photos/uuid.jpg`)
   - Download from Supabase works (verified in logs)

3. **Frontend**
   - File selection and preview works
   - Image display handles Supabase URLs correctly
   - All UI elements functional

---

## ❌ **What's NOT Working**

**The `/api/analyze` endpoint fails when calling Gemini API**

**Error Message:** `"Invalid request to Gemini. Make sure photos are valid images."`

**Current Flow:**
1. User selects images → Uploads to Supabase Storage ✅
2. User clicks "Analyze with AI" → Frontend sends Supabase URLs to `/api/analyze` ✅
3. Backend downloads images from Supabase to temp files ✅ (verified in logs)
4. Backend prepares images for Gemini (converts to JPEG, base64 encodes) ✅ (verified in logs)
5. **Gemini API rejects the request** ❌

---

## 🔍 **What We've Tried**

### 1. Image Validation & Conversion (`src/ai/gemini_classifier.py`)
- ✅ Validates image exists and is readable
- ✅ Detects actual format using PIL (not file extension)
- ✅ Converts unsupported formats to JPEG
- ✅ Resizes if >20MP
- ✅ Compresses if >15MB (pre-base64)
- ✅ Converts RGBA to RGB
- ✅ Ensures `mime_type` is always `image/jpeg`
- ✅ Strips `data:` prefix from base64

### 2. Payload Structure (`src/ai/gemini_classifier.py`)
- ✅ Uses `inline_data` structure
- ✅ Includes `mime_type` field (non-negotiable)
- ✅ Includes `data` field (base64, no prefix)
- ✅ Includes `role: "user"` in contents

### 3. Debugging Added
- ✅ Frontend file validation with console logging
- ✅ Backend download verification (`[ANALYZE DEBUG]`)
- ✅ Gemini payload structure logging (`[GEMINI DEBUG]`)
- ✅ File existence and size checks at every step

---

## 📋 **Gemini API Requirements (Research Findings)**

### Supported Formats
- ✅ `image/jpeg` / `image/jpg`
- ✅ `image/png`
- ⚠️ `image/webp` (sometimes rejected)
- ❌ `image/heic` / `image/heif` (NOT supported)

### Size Limits
- **File size:** 20MB max (before base64 encoding)
- **Dimensions:** 20MP max (20,000,000 pixels)

### Payload Structure (NON-NEGOTIABLE)
```json
{
  "contents": [{
    "role": "user",
    "parts": [
      {"text": "Analyze this image"},
      {
        "inline_data": {
          "mime_type": "image/jpeg",  // MUST be present
          "data": "base64_string_here"  // Clean base64, NO data: prefix
        }
      }
    ]
  }]
}
```

### Critical Requirements
1. **`mime_type` MUST be present** - Missing = hard fail
2. **Base64 must be clean** - No `data:image/jpeg;base64,` prefix
3. **File must be actual bytes** - Not a URL or path
4. **Format must be supported** - JPEG/PNG are safest

---

## 🐛 **Current Implementation Details**

### File: `routes_main.py` - `/api/analyze` endpoint
- Downloads images from Supabase Storage URLs to temp files
- Creates `Photo` objects with `local_path` pointing to temp files
- Passes `Photo` objects to `GeminiClassifier.analyze_item()`

### File: `src/ai/gemini_classifier.py` - `GeminiClassifier` class
- `_prepare_image_for_gemini()`: Validates, converts, resizes, compresses
- `_encode_image_to_base64()`: Converts image bytes to base64
- `_get_image_mime_type()`: Returns `'image/jpeg'` (all converted to JPEG)
- `analyze_item()`: Builds payload with `inline_data` structure

### Debug Logs to Check
Look for these in Render logs:
- `[ANALYZE DEBUG]` - File download and temp file creation
- `[GEMINI DEBUG]` - Image encoding and payload structure
- Check for: `hasFile`, `exists`, `fileSize`, `has_mime_type`, `has_data`, `is_clean_base64`

---

## 💡 **Potential Issues to Investigate**

### 1. **Base64 Encoding**
- Verify base64 string is actually valid
- Check if there are any newlines or whitespace
- Ensure it's pure base64 (no data URI prefix)

### 2. **MIME Type**
- Double-check `mime_type` is exactly `"image/jpeg"` (not `"image/jpg"`)
- Verify it's a string, not None or empty

### 3. **Payload Structure**
- Verify `inline_data` is nested correctly
- Check if Gemini expects `inlineData` (camelCase) vs `inline_data` (snake_case)
- Verify `role: "user"` is correct

### 4. **Image Data**
- Verify temp files are actually valid images
- Check if PIL can open and verify the temp files
- Ensure file isn't corrupted during download/write

### 5. **API Key & Endpoint**
- Verify Gemini API key is valid
- Check if using correct API endpoint (v1beta vs v1)
- Verify API key has vision permissions

### 6. **Request Format**
- Check if Gemini API version changed
- Verify request headers are correct
- Check if there's a different endpoint for vision

---

## 🔧 **Recommended Next Steps**

1. **Add raw payload logging** (without base64 data) to see exact structure sent to Gemini
2. **Test with a single, known-good image** (simple JPEG, <1MB)
3. **Verify Gemini API response** - What exact error is Gemini returning?
4. **Check Gemini API documentation** for any recent changes
5. **Test base64 encoding** - Decode and verify it's valid image data
6. **Compare with working Gemini examples** - Find a minimal working example and compare

---

## 📁 **Key Files to Review**

- `routes_main.py` - `/api/analyze` endpoint (lines ~707-800)
- `src/ai/gemini_classifier.py` - `GeminiClassifier` class (lines ~195-270, ~405-460)
- `src/storage/supabase_storage.py` - `download_photo()` method
- `templates/create.html` - Frontend analyzer call (search for `analyzeBtn`)

---

## ⚠️ **IMPORTANT WARNINGS**

1. **DO NOT modify the upload flow** - It's working perfectly
2. **DO NOT change Supabase Storage integration** - It's stable
3. **DO NOT remove the debugging** - It's helping identify the issue
4. **DO test changes incrementally** - One change at a time
5. **DO check Render logs** - They contain the debugging output

---

## 🎯 **Success Criteria**

The analyzer will work when:
- Gemini API accepts the request (no "invalid format" error)
- Gemini returns analysis results
- Results are displayed in the frontend

---

## 📝 **Additional Context**

- **Environment:** Render.com (production)
- **Database:** PostgreSQL (Supabase)
- **Storage:** Supabase Storage (not local filesystem)
- **AI Service:** Google Gemini API
- **Python Version:** Check `requirements.txt` or `runtime.txt`
- **Flask Version:** Check `requirements.txt`

---

**Last Updated:** Based on conversation where user reported analyzer still failing after adding comprehensive debugging and validation.

**User's Request:** Fresh start with AI analyzer - needs brainstorming session to solve this specific issue without breaking the working image upload flow.

