# External API Non-Negotiable Rules

## Gemini API Image Requirements

### ✅ SUPPORTED FORMATS
- `image/jpeg` (recommended)
- `image/png`
- `image/gif`
- `image/webp`

### ❌ NOT SUPPORTED
- `image/heic` / `image/heif` (convert to JPEG first)
- `image/bmp` (convert to JPEG)
- `image/tiff` (convert to JPEG)

### ✅ SIZE LIMITS
- **Maximum file size**: 20MB per image
- **Maximum dimensions**: 20 megapixels (e.g., 4096×4096)
- **Base64 overhead**: Increases size by ~33%, so 15MB image = ~20MB base64

### ✅ REQUIRED PAYLOAD STRUCTURE
```json
{
  "contents": [{
    "role": "user",
    "parts": [
      {"text": "prompt text"},
      {
        "inline_data": {
          "mime_type": "image/jpeg",
          "data": "clean_base64_string_no_prefix"
        }
      }
    ]
  }]
}
```

### ❌ CRITICAL REQUIREMENTS
- `mime_type` MUST be present (missing = hard fail)
- Base64 MUST be clean (no `data:image/jpeg;base64,` prefix)
- MIME type MUST match actual image format
- Use `inline_data` (snake_case), not `inlineData` (camelCase)
- NO Authorization header (API key in query param only: `?key=API_KEY`)

---

## Gemini API Authentication

### ✅ CORRECT
- API key in URL query parameter: `?key=YOUR_API_KEY`
- Only `Content-Type: application/json` header
- Strip whitespace from API key
- Validate key starts with `AIza`
- Validate key length (39-45 chars typical)

### ❌ WRONG
- Never add `Authorization: Bearer` header
- Never use both header and query param
- Never use raw env var without stripping whitespace
- Never skip key validation

**Correct Request**:
```python
headers = {"Content-Type": "application/json"}  # Only this header
response = requests.post(
    f"{api_url}?key={api_key}",  # Key in query param
    headers=headers,
    json=payload,
    timeout=30
)
```

---

## Supabase Storage

### ✅ BUCKET MAPPING
- `folder='temp'` → `temp-photos` bucket
- `folder='drafts'` → `draft-images` bucket
- `folder='listings'` → `listing-images` bucket

### ✅ REQUIREMENTS
- Use service_role key for server-side uploads
- Verify bucket name appears in returned URL
- Log upload destination for debugging
- Only clean up `temp-photos` bucket on page unload

### ❌ NEVER
- Don't use anon key for server uploads
- Don't skip bucket verification
- Don't clean up wrong buckets
- Don't assume folder mapping without checking environment variables

**Required Environment Variables**:
```bash
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

---

## Mercari Automation

### ✅ BEST SOLUTION
- Use cookie-based login (bypasses bot detection)
- Save cookies once with `save_mercari_cookies.py`
- Reuse saved session instead of logging in each time
- Refresh cookies every few weeks

### ✅ DEBUGGING
- Set `MERCARI_HEADLESS=false` to see browser
- Increase timeouts (60s for slow connections)
- Save screenshots on login failure
- Use multiple selector fallbacks

### ❌ AVOID
- Don't log in on every automation run (triggers bot detection)
- Don't use accounts with 2FA enabled
- Don't skip anti-detection measures
- Don't ignore CAPTCHA/verification pages

---

## Image Download from Supabase

### ✅ REQUIREMENTS
- Download images to temp files before processing
- Verify download succeeded (check file size)
- Validate image can be opened by PIL
- Clean up temp files after use

**Correct Flow**:
```python
# 1. Download
file_data = download_from_supabase(url)

# 2. Write to temp file
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
temp_file.write(file_data)
temp_file.flush()
temp_file.close()

# 3. Validate
img = Image.open(temp_file.name)  # Will raise if invalid

# 4. Process
# ... your processing ...

# 5. Clean up
os.unlink(temp_file.name)
```

### ❌ NEVER
- Don't skip download validation
- Don't assume download succeeded
- Don't skip PIL validation
- Don't leave temp files behind

---

## Base64 Encoding for Gemini

### ✅ REQUIREMENTS
- Encode image bytes (not file paths or URLs)
- Strip any whitespace or newlines from base64 string
- No data URI prefix
- Validate base64 is valid (try decoding)
- Check base64 length is reasonable (~33% larger than bytes)

**Correct Pattern**:
```python
# Encode
base64_str = base64.b64encode(image_bytes).decode('utf-8').strip()

# Validate
try:
    decoded = base64.b64decode(base64_str)
    assert len(decoded) == len(image_bytes)
except Exception as e:
    logger.error(f"Base64 validation failed: {e}")
```

### ❌ NEVER
- Never include `data:image/jpeg;base64,` prefix
- Never skip validation
- Never send file paths or URLs as base64
- Never assume encoding succeeded

---

## Error Handling

### ✅ ALWAYS
- Log full API error response (not just status code)
- Log request details (without sensitive data)
- Provide specific error messages to user
- Check for multiple error types

**Example**:
```python
if not response.ok:
    logger.error(f"API Error: {response.status_code}")
    logger.error(f"Response: {response.text[:500]}")
    logger.error(f"Headers: {response.headers}")
    return {"error": f"API returned {response.status_code}"}
```

### ❌ NEVER
- Don't return generic "API failed" messages
- Don't skip logging response details
- Don't assume error format
- Don't ignore specific error codes

---

## Request Headers

### ✅ GEMINI API
```python
headers = {
    "Content-Type": "application/json"
}
# No Authorization header!
```

### ✅ SUPABASE STORAGE
```python
headers = {
    "Authorization": f"Bearer {service_role_key}",
    "Content-Type": "application/json"
}
```

### ❌ NEVER MIX THEM UP
- Gemini uses query param, not header
- Supabase uses header, not query param
- Check API documentation for each service

---

## Timeouts

### ✅ REQUIREMENTS
- Always set timeouts on requests
- Gemini API: 30-60 seconds (image processing takes time)
- File downloads: 30 seconds
- Simple API calls: 10 seconds

```python
response = requests.post(url, json=payload, timeout=30)
```

### ❌ NEVER
- Don't skip timeouts (requests can hang forever)
- Don't use same timeout for all requests
- Don't ignore timeout exceptions

---

## Key Lessons

1. **Gemini requires exact payload structure** - `mime_type` field is non-negotiable
2. **No Authorization header for Gemini** - API key goes in query param only
3. **Supabase requires service_role key** - Anon key fails with RLS
4. **Base64 must be clean** - No prefixes, no whitespace
5. **Cookie-based auth for Mercari** - Bypasses bot detection
6. **Always validate downloads** - Don't assume files are valid
7. **Strip all API keys** - Hidden whitespace causes silent failures
