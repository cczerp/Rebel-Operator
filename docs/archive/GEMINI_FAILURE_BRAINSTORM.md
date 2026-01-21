# Gemini API Analyzer Failure - Brainstorming Document

## 🎯 Goal
Understand why Gemini API is rejecting image requests despite all validation and conversion steps passing.

## 📋 Current Flow (What's Working)
1. ✅ Images upload to Supabase Storage successfully
2. ✅ Images display correctly in frontend
3. ✅ Backend downloads images from Supabase to temp files
4. ✅ PIL opens and validates images
5. ✅ Images are converted to JPEG format
6. ✅ Images are resized/compressed if needed
7. ✅ Base64 encoding happens without errors
8. ✅ Payload structure looks correct in logs

## ❌ What's Failing
Gemini API returns: `"Invalid request to Gemini. Make sure photos are valid images."` (400 Bad Request)

---

## 🔍 Potential Issues to Investigate

### 1. **PIL Image.verify() Problem** ⚠️ HIGH PRIORITY

**Location**: `src/ai/gemini_classifier.py:87`

```python
img.verify()  # ⚠️ POTENTIAL ISSUE
img = Image.open(image_path)  # Reopen after verify
```

**Problem**: 
- `Image.verify()` is **deprecated** and can sometimes corrupt image files
- It's meant for validation only, not for images you plan to use
- Some image formats don't survive the verify/reopen cycle properly
- PIL documentation recommends using `Image.open()` with exception handling instead

**Why This Could Cause Gemini Failure**:
- If verify() corrupts the image data, the reopened image might be invalid
- The base64 encoding would encode corrupted data
- Gemini would reject it as "invalid image"

**Recommended Approach**:
- Remove `img.verify()`
- Use try/except around `Image.open()` instead
- Validate by attempting operations (like checking size/format)

---

### 2. **BytesIO Stream Position Issue** ⚠️ MEDIUM PRIORITY

**Location**: `src/ai/gemini_classifier.py:113-115`

```python
output = io.BytesIO()
img.save(output, format='JPEG', quality=85, optimize=True)
image_bytes = output.getvalue()
```

**Problem**:
- After `save()`, the stream position might be at the end
- `getvalue()` should work regardless, but could theoretically have issues
- If stream position matters, data might be incomplete

**Why This Could Cause Gemini Failure**:
- Incomplete image bytes → invalid base64 → Gemini rejection

**Recommended Approach**:
- Add `output.seek(0)` before `getvalue()` (defensive programming)
- Or use `output.getvalue()` which should work regardless

---

### 3. **Temp File Not Fully Flushed** ⚠️ MEDIUM PRIORITY

**Location**: `routes_main.py:759-762`

```python
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
temp_file.write(file_data)
temp_file.close()
local_path = temp_file.name
```

**Problem**:
- File might not be fully written to disk when `close()` is called
- OS buffering might delay the actual write
- PIL might try to read the file before it's fully written

**Why This Could Cause Gemini Failure**:
- PIL reads incomplete file → corrupted image data → invalid base64 → Gemini rejection

**Recommended Approach**:
- Add `temp_file.flush()` before `temp_file.close()`
- Add `os.fsync(temp_file.fileno())` to force write to disk
- Add small delay or verify file size matches expected

---

### 4. **Base64 Encoding Issues** ⚠️ HIGH PRIORITY

**Location**: `src/ai/gemini_classifier.py:151`

```python
base64_str = base64.b64encode(image_bytes).decode("utf-8")
```

**Potential Issues**:

#### 4a. **Whitespace/Newlines in Base64**
- Base64 strings should be continuous (no whitespace)
- If somehow newlines or spaces are introduced, Gemini might reject it
- Python's `base64.b64encode()` shouldn't add whitespace, but worth checking

#### 4b. **Base64 String Validation**
- No validation that the base64 string is actually valid base64
- If encoding fails silently, invalid base64 would be sent

#### 4c. **UTF-8 Decoding Issues**
- `.decode("utf-8")` should always work for base64, but if there are encoding issues...
- Base64 only uses ASCII characters, so UTF-8 decode should be safe

**Why This Could Cause Gemini Failure**:
- Invalid base64 string → Gemini can't decode → rejection

**Recommended Approach**:
- Add base64 validation: try to decode and re-encode to verify
- Strip any whitespace/newlines from base64 string
- Log first/last 50 characters of base64 to verify format
- Check base64 string length is reasonable (should be ~33% larger than image bytes)

---

### 5. **JSON Serialization - Snake Case vs Camel Case** ⚠️ LOW PRIORITY

**Location**: `src/ai/gemini_classifier.py:260-270`

```python
inline_data = {
    "mime_type": mime_type,  # snake_case
    "data": image_b64
}
```

**Problem**:
- Gemini REST API documentation shows `inline_data` with `mime_type` (snake_case)
- But some Google APIs use camelCase (`inlineData`, `mimeType`)
- If the API expects camelCase but we send snake_case, it might reject

**Research Finding**:
- Web search suggests REST API uses snake_case
- But worth verifying the exact format required

**Why This Could Cause Gemini Failure**:
- Wrong field names → Gemini doesn't recognize image parts → rejection

**Recommended Approach**:
- Check Gemini API documentation for exact field names
- Try camelCase version if snake_case fails
- Log the exact payload structure being sent

---

### 6. **Request Headers Missing** ⚠️ MEDIUM PRIORITY

**Location**: `src/ai/gemini_classifier.py:476-479`

```python
response = requests.post(
    f"{self.api_url}?key={self.api_key}",
    headers={"Content-Type": "application/json"},
    json=payload,
    timeout=30
)
```

**Problem**:
- Only `Content-Type` header is set
- Might need `Accept: application/json` header
- Some APIs require specific headers

**Why This Could Cause Gemini Failure**:
- Missing headers might cause API to reject request before processing payload

**Recommended Approach**:
- Add `Accept: application/json` header
- Check Gemini API documentation for required headers

---

### 7. **API Endpoint or Model Name Issue** ⚠️ LOW PRIORITY

**Location**: `src/ai/gemini_classifier.py:60-62`

```python
self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
```

**Problem**:
- Model name might be incorrect
- Endpoint format might have changed
- Model might not support vision/images

**Why This Could Cause Gemini Failure**:
- Wrong endpoint → 404 or wrong API version
- Wrong model → model doesn't support images

**Recommended Approach**:
- Verify model name is correct for image support
- Check if endpoint format is correct
- Try a known-working model name

---

### 8. **Image Data Corruption During Download/Write** ⚠️ HIGH PRIORITY

**Location**: `routes_main.py:746-762`

**Flow**:
1. Download bytes from Supabase
2. Write to temp file
3. PIL reads temp file
4. PIL converts to JPEG
5. Encode to base64

**Problem**:
- If bytes are corrupted during download, file is invalid
- If write is incomplete, file is truncated
- If PIL can't properly read the file, conversion fails silently

**Why This Could Cause Gemini Failure**:
- Corrupted image data → invalid JPEG → Gemini rejection

**Recommended Approach**:
- Validate image bytes after download (try PIL.open on bytes directly)
- Verify temp file size matches downloaded bytes
- Add checksum/hash verification
- Try opening image from bytes without temp file

---

### 9. **PIL Image.save() Quality/Format Issues** ⚠️ MEDIUM PRIORITY

**Location**: `src/ai/gemini_classifier.py:113-114`

```python
img.save(output, format='JPEG', quality=85, optimize=True)
```

**Problem**:
- Quality 85 might produce invalid JPEG in edge cases
- `optimize=True` might cause issues with some images
- Some image modes might not convert properly to JPEG

**Why This Could Cause Gemini Failure**:
- Invalid JPEG encoding → Gemini can't decode → rejection

**Recommended Approach**:
- Try saving without `optimize=True`
- Try different quality levels
- Validate JPEG after saving (try to open and verify)

---

### 10. **Base64 String Too Large or Malformed** ⚠️ MEDIUM PRIORITY

**Problem**:
- Base64 string might exceed API limits (even if image bytes are under limit)
- Base64 encoding increases size by ~33%
- If image is 15MB, base64 is ~20MB
- But what if there's extra overhead?

**Why This Could Cause Gemini Failure**:
- Base64 string too large → API rejects
- Malformed base64 → API can't decode

**Recommended Approach**:
- Check base64 string length
- Verify it's within API limits
- Try decoding base64 and re-encoding to validate

---

### 11. **Multiple Images in Payload** ⚠️ LOW PRIORITY

**Location**: `src/ai/gemini_classifier.py:432`

```python
"parts": [
    {"text": prompt},
    *image_parts  # Multiple images
]
```

**Research Finding**:
- Web search suggests sending >9 images can cause 500 errors
- But code limits to 4 images, so this shouldn't be the issue
- However, maybe there's a limit on total payload size?

**Why This Could Cause Gemini Failure**:
- Too many images or total payload too large → API rejects

**Recommended Approach**:
- Try with single image first (isolate issue)
- Check total payload size
- Verify image count is within limits

---

### 12. **API Key Permissions** ⚠️ LOW PRIORITY

**Problem**:
- API key might not have vision/image permissions
- API key might be invalid or expired
- API key might be for wrong project

**Why This Could Cause Gemini Failure**:
- No vision permissions → API rejects image requests

**Recommended Approach**:
- Verify API key is valid (test with simple request)
- Check API key has vision permissions
- Verify API key is for correct project

---

## 🎯 Recommended Investigation Order

### Priority 1: High Likelihood Issues
1. **Remove PIL Image.verify()** - Known to cause issues
2. **Add base64 validation** - Ensure base64 is valid
3. **Validate image after download** - Check for corruption
4. **Add temp file flush/fsync** - Ensure file is written

### Priority 2: Medium Likelihood Issues
5. **Add BytesIO seek(0)** - Defensive programming
6. **Check request headers** - Add Accept header
7. **Validate JPEG after save** - Ensure conversion worked
8. **Check base64 string length** - Ensure within limits

### Priority 3: Lower Likelihood Issues
9. **Verify API endpoint/model** - Check documentation
10. **Try camelCase field names** - If snake_case fails
11. **Test with single image** - Isolate multi-image issues
12. **Verify API key permissions** - Ensure vision access

---

## 🔬 Debugging Steps to Take

### Step 1: Add Comprehensive Logging
```python
# Log base64 string details
logger.info(f"[GEMINI DEBUG] Base64 length: {len(base64_str)}")
logger.info(f"[GEMINI DEBUG] Base64 first 50 chars: {base64_str[:50]}")
logger.info(f"[GEMINI DEBUG] Base64 last 50 chars: {base64_str[-50:]}")
logger.info(f"[GEMINI DEBUG] Base64 has whitespace: {' ' in base64_str or '\n' in base64_str}")

# Validate base64
try:
    decoded = base64.b64decode(base64_str)
    reencoded = base64.b64encode(decoded).decode('utf-8')
    is_valid = (reencoded == base64_str)
    logger.info(f"[GEMINI DEBUG] Base64 is valid: {is_valid}")
except Exception as e:
    logger.error(f"[GEMINI DEBUG] Base64 validation failed: {e}")
```

### Step 2: Validate Image After Conversion
```python
# After saving to BytesIO
output.seek(0)  # Reset position
image_bytes = output.getvalue()

# Try to validate JPEG
try:
    from PIL import Image
    import io
    test_img = Image.open(io.BytesIO(image_bytes))
    test_img.verify()  # Verify JPEG is valid
    logger.info(f"[GEMINI DEBUG] JPEG validation passed")
except Exception as e:
    logger.error(f"[GEMINI DEBUG] JPEG validation failed: {e}")
```

### Step 3: Log Actual API Response
```python
# In error handling, log the full response
else:
    error_msg = response.text[:500]
    logger.error(f"[GEMINI DEBUG] API Error Response: {response.text}")  # FULL response
    logger.error(f"[GEMINI DEBUG] Response Headers: {response.headers}")
    logger.error(f"[GEMINI DEBUG] Status Code: {response.status_code}")
```

### Step 4: Test with Minimal Payload
```python
# Create minimal test payload
test_payload = {
    "contents": [{
        "role": "user",
        "parts": [
            {"text": "What's in this image?"},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_b64  # Single image
                }
            }
        ]
    }]
}
```

---

## 📝 Key Questions to Answer

1. **What is the EXACT error message from Gemini API?**
   - Current: Generic "Invalid request" message
   - Need: Full error response body from Gemini

2. **Is the base64 string actually valid?**
   - Can we decode and re-encode it?
   - Does it match the original image bytes?

3. **Is the JPEG conversion actually working?**
   - Can PIL open the BytesIO image?
   - Is it a valid JPEG?

4. **Is the payload structure correct?**
   - Does it match Gemini API documentation exactly?
   - Are field names correct (snake_case vs camelCase)?

5. **Are images corrupted during download/write?**
   - Can we verify image integrity after download?
   - Can we open image directly from bytes without temp file?

---

## 🔗 Next Steps

1. **Check Render logs** for the full Gemini API error response
2. **Add detailed logging** for base64 validation and image validation
3. **Remove PIL verify()** and use exception handling instead
4. **Add temp file flush/fsync** to ensure file is written
5. **Test with a known-good image** (simple JPEG, <1MB)
6. **Try single image** instead of multiple images
7. **Compare payload structure** with official Gemini API examples

---

**Last Updated**: Based on code review and issue summary analysis
**Status**: Brainstorming phase - No fixes applied yet

