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
```python
headers = {"Content-Type": "application/json"}  # Only this header
response = requests.post(
    f"{api_url}?key={api_key}",  # Key in query param
    headers=headers,
    json=payload,
    timeout=30
)
```

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

---

## Claude API Image Requirements

### ✅ SUPPORTED FORMATS
- `image/jpeg` (recommended)
- `image/png`
- `image/gif`

**ONLY THESE THREE - MORE RESTRICTIVE THAN GEMINI**

### ❌ NOT SUPPORTED
- `image/webp` (convert to JPEG - Claude doesn't support this!)
- `image/heic` / `image/heif` (convert to JPEG)
- All other formats (convert to JPEG)

### ✅ REQUIRED CONVERSION
```python
def _convert_to_claude_format(image_path):
    img = Image.open(image_path)
    original_format = img.format

    # If already supported, return as-is
    if original_format in ('JPEG', 'PNG', 'GIF'):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        mime_type = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif'
        }[original_format]
        return image_bytes, mime_type

    # Convert unsupported formats (WebP, HEIC, etc.) to JPEG
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    return output.getvalue(), 'image/jpeg'
```

### ✅ REQUIRED PAYLOAD STRUCTURE
```python
{
    "role": "user",
    "content": [
        {"type": "text", "text": "prompt text"},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": "clean_base64_string_no_prefix"
            }
        }
    ]
}
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

### ✅ REQUIRED FLOW
```python
# 1. Download
file_data = download_from_supabase(url)

# 2. Write to temp file
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
temp_file.write(file_data)
temp_file.flush()
os.fsync(temp_file.fileno())
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

## Base64 Encoding

### ✅ REQUIREMENTS
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

- Encode image bytes (not file paths or URLs)
- Strip any whitespace or newlines from base64 string
- No data URI prefix
- Validate base64 is valid (try decoding)
- Check base64 length is reasonable (~33% larger than bytes)

### ❌ NEVER
- Never include `data:image/jpeg;base64,` prefix
- Never skip validation
- Never send file paths or URLs as base64
- Never assume encoding succeeded

---

## Error Handling

### ✅ ALWAYS
```python
if not response.ok:
    logger.error(f"API Error: {response.status_code}")
    logger.error(f"Response: {response.text[:500]}")
    logger.error(f"Headers: {response.headers}")
    return {"error": f"API returned {response.status_code}"}
```

- Log full API error response (not just status code)
- Log request details (without sensitive data)
- Provide specific error messages to user
- Check for multiple error types

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
# API key goes in query param: ?key=API_KEY
```

### ✅ CLAUDE API
```python
headers = {
    "anthropic-version": "2023-06-01",
    "x-api-key": api_key,
    "content-type": "application/json"
}
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
- Claude uses x-api-key header
- Supabase uses Authorization Bearer header
- Check API documentation for each service

---

## Timeouts

### ✅ REQUIREMENTS
```python
response = requests.post(url, json=payload, timeout=30)
```

- Always set timeouts on requests
- Gemini API: 30-60 seconds (image processing takes time)
- Claude API: 30-60 seconds
- File downloads: 30 seconds
- Simple API calls: 10 seconds

### ❌ NEVER
- Don't skip timeouts (requests can hang forever)
- Don't use same timeout for all requests
- Don't ignore timeout exceptions

---

## Image Flow Contracts (Detailed Implementations)

**Before modifying API integration code, check**:
- `/image flow/06_backend_ai_analyze_api.txt` - Gemini integration
- `/image flow/07_backend_enhanced_scan_api.txt` - Claude integration
- `/image flow/08_ai_image_format_conversion.txt` - Format conversion for Claude
- `/image flow/09_ai_gemini_classifier.txt` - Gemini classifier
- `/image flow/10_ai_claude_analysis.txt` - Claude analysis

**These are the source of truth. Follow them exactly.**

---

## Key Rules

1. **Gemini requires exact payload structure** - `mime_type` field is non-negotiable
2. **No Authorization header for Gemini** - API key goes in query param only
3. **Claude is more restrictive** - Only JPEG/PNG/GIF (no WebP!)
4. **Supabase requires service_role key** - Anon key fails with RLS
5. **Base64 must be clean** - No prefixes, no whitespace
6. **Cookie-based auth for Mercari** - Bypasses bot detection
7. **Always validate downloads** - Don't assume files are valid
8. **Strip all API keys** - Hidden whitespace causes silent failures
9. **Different headers for different APIs** - Don't mix them up
10. **Always set timeouts** - Requests can hang forever without them
11. **eBay uses Browse API only** - Finding API is deprecated and returns 500 errors

---

## eBay API Integration

### ✅ USE BROWSE API (Working)
```
Endpoint: https://api.ebay.com/buy/browse/v1/item_summary/search
Auth: Bearer token (client_credentials)
```

### ❌ DO NOT USE FINDING API (Broken)
```
Endpoint: https://svcs.ebay.com/services/search/FindingService/v1
Status: Returns 500 errors from eBay's servers - DEPRECATED
```

### ✅ REQUIRED ENVIRONMENT VARIABLES
```bash
# Option 1: Provide B64 directly (uppercase only!)
EBAY_PROD_B64=base64_encoded_appid_colon_certid

# Option 2: Let code auto-generate B64
EBAY_PROD_APP_ID=your-app-id
EBAY_PROD_CERT_ID=your-cert-id

# The B64 value is: base64(APP_ID:CERT_ID)
# Example: base64("Christop-rebelope-PRD-123:abc-def-456")
```

### ✅ BROWSE API SETUP REQUIREMENTS
1. **Enable Browse API** in eBay Developer Portal (https://developer.ebay.com/my/keys)
2. Click your Production keyset → API Access → Enable "Buy API - Browse"
3. Uses `client_credentials` grant type (no user login required)
4. Scope: `https://api.ebay.com/oauth/api_scope`

### ✅ TOKEN REQUEST
```python
# Token endpoint
POST https://api.ebay.com/identity/v1/oauth2/token

# Headers
Authorization: Basic {base64(APP_ID:CERT_ID)}
Content-Type: application/x-www-form-urlencoded

# Body
grant_type=client_credentials
scope=https://api.ebay.com/oauth/api_scope
```

### ✅ SEARCH REQUEST
```python
# Search endpoint
GET https://api.ebay.com/buy/browse/v1/item_summary/search

# Headers
Authorization: Bearer {access_token}

# Query params
q=search+keywords
limit=10
offset=0
```

### ❌ CRITICAL MISTAKES
- **WRONG**: `EBAY_PROD_b64` (lowercase) - Code expects `EBAY_PROD_B64` (uppercase)
- **WRONG**: Using Finding API - Returns 500 errors, completely broken
- **WRONG**: Skipping Browse API enablement in Developer Portal
- **WRONG**: Using sandbox credentials in production or vice versa

### ✅ CODE ARCHITECTURE
```
Multi-platform search page (/search)
    └── eBaySearcher (platform_searchers.py)
            └── search_ebay() (ebay_search.py)  ← Uses Browse API
                    └── get_ebay_token() (ebay_auth.py)  ← Gets OAuth token

Direct eBay search API (/api/search/ebay)
    └── search_ebay() (ebay_search.py)  ← Same Browse API
            └── get_ebay_token() (ebay_auth.py)
```

### ✅ DIAGNOSTIC ENDPOINT
```
GET /ebay/diagnose
Returns: JSON with credentials status, API test results, recommendations
Use this to troubleshoot eBay connectivity issues
```

---
