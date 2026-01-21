# Backend Non-Negotiable Rules

## Database Cursors - CRITICAL

### ✅ REQUIRED PATTERN
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

### ❌ NEVER
- Never skip cursor cleanup (causes connection pool exhaustion)
- Never assume cursor will close automatically
- Don't rely on garbage collection to close cursors

**Why**: Supabase Session Pooling has limited connections. Unclosed cursors lock connections until closed.

**Priority methods that MUST have cursor cleanup**:
- `get_user_by_id()` - Called on every request
- `get_user_by_email()` - Called during login
- All `get_*`, `create_*`, `update_*` methods

---

## File Operations

### ✅ TEMP FILES - EXACT PATTERN
```python
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
temp_file.write(file_data)
temp_file.flush()  # Force write to OS buffer
os.fsync(temp_file.fileno())  # Force write to disk
temp_file.close()
local_path = temp_file.name
```

### ❌ CRITICAL
- Don't skip flush/fsync (file may not be fully written)
- Don't assume write completes immediately
- Don't skip file size validation

**Why**: Without flush/fsync, file may not be written before next operation reads it.

---

## Image Processing

### ✅ REQUIRED VALIDATION FLOW
```python
# 1. Open and validate
img = Image.open(image_path)

# 2. Detect actual format (not extension)
actual_format = img.format  # Don't trust file extension

# 3. Check dimensions (20MP limit)
if img.size[0] * img.size[1] > 20_000_000:
    # Resize to fit

# 4. Convert RGBA to RGB (remove alpha channel)
if img.mode in ('RGBA', 'LA', 'P'):
    background = Image.new('RGB', img.size, (255, 255, 255))
    if img.mode == 'P':
        img = img.convert('RGBA')
    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
    img = background
elif img.mode != 'RGB':
    img = img.convert('RGB')

# 5. Convert to JPEG
output = io.BytesIO()
img.save(output, format='JPEG', quality=85, optimize=True)
image_bytes = output.getvalue()

# 6. Check file size (20MB limit before base64)
if len(image_bytes) > 20 * 1024 * 1024:
    # Reduce quality and try again
```

### ❌ NEVER
- Never use `Image.verify()` (deprecated, corrupts images)
- Never trust file extensions for format detection
- Never skip dimension/size validation
- Never send HEIC/HEIF formats (not supported by APIs)
- Never include data URI prefix in base64 (`data:image/jpeg;base64,`)

### ✅ FORMAT CONVERSION FOR CLAUDE API
```python
# Claude only accepts: image/jpeg, image/png, image/gif
# Convert WebP, HEIC, etc. to JPEG

def _convert_to_claude_format(image_path):
    img = Image.open(image_path)
    original_format = img.format

    # If already supported, return as-is
    if original_format in ('JPEG', 'PNG', 'GIF'):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        mime_type = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'GIF': 'image/gif'}[original_format]
        return image_bytes, mime_type

    # Convert unsupported formats to JPEG
    # Handle RGBA conversion first
    if img.mode in ('RGBA', 'LA', 'P'):
        # ... conversion code above

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    return output.getvalue(), 'image/jpeg'
```

---

## Photo Upload API

### ✅ REQUIREMENTS (routes_main.py /api/upload-photos)
- Validate file types before processing
- Compress images > 1MB
- Resize images > 20MP
- Upload to correct bucket (temp-photos for new uploads)
- Return file URLs (Supabase Storage URLs)
- Log upload destination for debugging

### ❌ DON'T
- Don't skip image validation
- Don't skip compression
- Don't upload to wrong bucket
- Don't return local paths (return Supabase URLs)

---

## Photo Edit API

### ✅ REQUIREMENTS (routes_main.py /api/edit-photo)
- Support `crop` operation with x, y, width, height
- Support `remove-bg` operation (background removal)
- Accept base64 image data OR Supabase URL
- Return edited image as base64 AND upload to Supabase
- Set timeouts: 15s for crop, 30s for background removal

### ❌ DON'T
- Don't skip timeout handling
- Don't forget to upload edited image back to Supabase
- Don't return only base64 (return Supabase URL too)

---

## API Endpoints

### ✅ REQUIREMENTS
- Validate user authorization for ALL operations
- Type conversion and validation (strings to floats, etc.)
- Return clear error messages with status codes
- Log operations for debugging
- Handle errors gracefully with try/except

### ❌ NEVER
- Don't skip user authorization checks
- Don't assume data types are correct
- Don't return vague error messages
- Don't skip error logging

---

## Authentication & Environment Variables

### ✅ REQUIRED PATTERN
```python
# Strip whitespace from ALL environment variables
api_key = os.getenv("GEMINI_API_KEY", "").strip()

# Validate key
if not api_key.startswith('AIza'):
    logger.warning("API key doesn't start with 'AIza'")

if len(api_key) < 30 or len(api_key) > 60:
    logger.warning(f"API key length unusual: {len(api_key)}")

# Log repr() to detect hidden characters
logger.info(f"API key (repr): {repr(api_key)}")
```

### ❌ NEVER
- Never use raw environment values without stripping
- Never skip key validation
- Never assume keys are correct format

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

### ✅ BUCKET MAPPING
```python
# src/storage/supabase_storage.py
if folder == 'temp':
    bucket = self.temp_bucket  # temp-photos
elif folder == 'listings':
    bucket = self.listings_bucket  # listing-images
else:  # 'drafts' or default
    bucket = self.drafts_bucket  # draft-images
```

### ✅ REQUIREMENTS
- Verify photos upload to correct bucket
- Log which bucket photos are uploaded to
- Verify bucket name appears in public URL
- Clean up temp-photos on page unload (frontend handles this)

### ❌ NEVER
- Don't skip bucket verification logging
- Don't assume folder mapping is correct without checking
- Don't let photos end up in wrong bucket

**Required Environment Variables**:
```bash
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

---

## Image Flow Contracts (Detailed Implementations)

**Before modifying backend photo/API code, check**:
- `/image flow/04_backend_photo_upload_api.txt` - Upload endpoint
- `/image flow/05_backend_photo_edit_api.txt` - Edit endpoint
- `/image flow/06_backend_ai_analyze_api.txt` - AI analysis
- `/image flow/07_backend_enhanced_scan_api.txt` - Enhanced scanning
- `/image flow/08_ai_image_format_conversion.txt` - Format conversion
- `/image flow/09_ai_gemini_classifier.txt` - Gemini integration
- `/image flow/10_ai_claude_analysis.txt` - Claude integration

**These are the source of truth. Follow them exactly.**

---

## Key Rules

1. **Cursor cleanup is non-negotiable** - Connection pool exhaustion breaks everything
2. **Flush temp files** - Files may not be written without explicit flush/fsync
3. **Image format detection** - Never trust file extensions, use PIL
4. **Strip all environment variables** - Hidden whitespace causes silent failures
5. **Service role key for server** - Bypasses RLS, never expose to client
6. **Validate bucket mapping** - Photos must go to correct bucket
7. **Convert unsupported image formats** - HEIC/WebP → JPEG for APIs
8. **Never use Image.verify()** - Corrupts images, use Image.open() only
