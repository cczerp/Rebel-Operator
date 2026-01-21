# Backend Non-Negotiable Rules

## Database Cursors

### ✅ ALWAYS
- Close database cursors in `finally` blocks
- Use try/finally pattern for ALL cursor operations
- Never leave cursors open after operation completes

**Required Pattern**:
```python
def some_method(self):
    cursor = None
    try:
        cursor = self._get_cursor()
        cursor.execute(...)
        return result
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
```

### ❌ CRITICAL
- Never skip cursor cleanup (causes connection pool exhaustion)
- Never assume cursor will close automatically
- Don't rely on garbage collection to close cursors

**Why**: Supabase Session Pooling has limited connections. Unclosed cursors lock connections until closed.

---

## File Operations

### ✅ TEMP FILES
- Always flush temp files before closing: `temp_file.flush()`
- Force write to disk: `os.fsync(temp_file.fileno())`
- Verify file size matches expected bytes
- Close temp files properly

**Correct Pattern**:
```python
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
temp_file.write(file_data)
temp_file.flush()  # Force write
os.fsync(temp_file.fileno())  # Ensure disk write
temp_file.close()
local_path = temp_file.name
```

### ❌ NEVER
- Don't skip flush/fsync (file may not be fully written)
- Don't assume write completes immediately
- Don't skip file size validation

---

## Image Processing

### ✅ ALWAYS
- Use PIL to detect actual image format (not file extension)
- Convert unsupported formats to JPEG before sending
- Validate images exist and are readable
- Check dimensions (max 20MP) and resize if needed
- Check file size (max 20MB before base64) and compress if needed
- Convert RGBA to RGB (remove alpha channel)
- Strip whitespace from base64 strings

**Required Validation Flow**:
```python
# 1. Open and validate
img = Image.open(image_path)

# 2. Check dimensions (20MP limit)
if img.size[0] * img.size[1] > 20_000_000:
    # Resize to fit

# 3. Convert to RGB
if img.mode in ('RGBA', 'LA', 'P'):
    # Handle alpha channel

# 4. Convert to JPEG
output = io.BytesIO()
img.save(output, format='JPEG', quality=85, optimize=True)
image_bytes = output.getvalue()

# 5. Check file size
if len(image_bytes) > 20 * 1024 * 1024:
    # Reduce quality
```

### ❌ NEVER
- Never use `Image.verify()` (deprecated, corrupts images)
- Never trust file extensions for format detection
- Never skip dimension/size validation
- Never send HEIC/HEIF formats (not supported)
- Never include data URI prefix in base64 (`data:image/jpeg;base64,`)

---

## API Endpoints

### ✅ REQUIREMENTS
- Validate user authorization for ALL operations
- Type conversion and validation (strings to floats, etc.)
- Return clear error messages
- Log operations for debugging
- Handle errors gracefully

### ❌ NEVER
- Don't skip user authorization checks
- Don't assume data types are correct
- Don't return vague error messages
- Don't skip error logging

---

## Authentication & Environment Variables

### ✅ ALWAYS
- Strip whitespace from API keys and passwords
- Log `repr()` of values to detect hidden characters
- Validate key length and format
- Check multiple possible environment variable names

**Required Pattern**:
```python
# Strip whitespace
api_key = os.getenv("GEMINI_API_KEY", "").strip()

# Validate
if not api_key.startswith('AIza'):
    logger.warning("API key doesn't start with 'AIza'")

if len(api_key) < 30 or len(api_key) > 60:
    logger.warning(f"API key length unusual: {len(api_key)}")
```

### ❌ NEVER
- Never use raw environment values without stripping
- Never skip key validation
- Never assume keys are correct format
- Don't add Authorization header to Gemini API (use query param only)

---

## Supabase Row-Level Security (RLS)

### ✅ SOLUTION
- Use `SUPABASE_SERVICE_ROLE_KEY` for server-side uploads (bypasses RLS)
- Never expose service_role key to client/frontend
- Set up proper RLS policies for production

### ❌ NEVER
- Don't use anon key for server-side storage operations
- Don't disable RLS in production
- Don't expose service_role key in frontend code

---

## Bucket Management

### ✅ REQUIREMENTS
- Verify photos upload to correct bucket:
  - `temp-photos` for temporary uploads
  - `draft-images` for saved drafts
  - `listing-images` for published listings
- Log which bucket photos are uploaded to
- Verify bucket name appears in public URL

### ❌ NEVER
- Don't skip bucket verification logging
- Don't assume folder mapping is correct without checking
- Don't let photos end up in wrong bucket

---

## Priority Methods to Monitor

**High-traffic methods that MUST have cursor cleanup**:
- `get_user_by_id()` - Called on every request
- `get_user_by_email()` - Called during login
- All `get_*` methods
- All `create_*` methods
- All `update_*` methods

---

## Key Lessons

1. **Cursor cleanup is non-negotiable** - Connection pool exhaustion breaks everything
2. **Flush temp files** - Files may not be written without explicit flush/fsync
3. **Image format detection** - Never trust file extensions
4. **Strip all environment variables** - Hidden whitespace causes silent failures
5. **Service role key for server** - Bypasses RLS, never expose to client
