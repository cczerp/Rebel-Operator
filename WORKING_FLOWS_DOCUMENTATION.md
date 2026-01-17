# WORKING FLOWS DOCUMENTATION
## NON-NEGOTIABLE REQUIREMENTS & SOLUTIONS

**Last Updated**: After fixing Gemini API key issues (env var name correction + .strip() fixes)
**Status**: ✅ **BOTH FLOWS ARE WORKING - DO NOT BREAK**

---

## 📖 **QUICK REFERENCE**

### **Image Upload Flow** (6 steps)
1. Frontend uploads to `/api/upload-photos` → **MUST use `folder='temp'`**
2. Backend compresses image → **MUST call `seek(0)` after `img.save()`**
3. Backend uploads to Supabase → **MUST go to `temp-photos` bucket**
4. Frontend stores URLs → **MUST track in `uploadedPhotos` array**
5. On page unload → **MUST call cleanup endpoint**
6. When listing saved → **Photos moved to `listing-images` bucket**

### **AI Analysis Flow** (6 steps)
1. Frontend sends URLs to `/api/analyze`
2. Backend downloads from Supabase → **MUST flush & fsync temp file**
3. Backend prepares images → **MUST convert RGBA→RGB, resize, compress**
4. Backend encodes to base64 → **MUST strip `data:image/` prefix**
5. Backend calls Gemini API → **MUST use query string key, NO Auth header**
6. Backend returns analysis → **MUST cleanup temp files**

### **Top 10 Critical Requirements**
1. ✅ API key MUST be stripped (`.strip()`) - fixes hidden newline/space issues
2. ✅ Gemini API key in query string ONLY - NO Authorization header
3. ✅ Initial uploads MUST go to `temp-photos` bucket (`folder='temp'`)
4. ✅ Frontend cleanup MUST use `fetch` with `keepalive: true` (NOT sendBeacon)
5. ✅ Images MUST have RGBA converted to RGB (JPEG doesn't support transparency)
6. ✅ Base64 MUST NOT have `data:image/` prefix (Gemini rejects it)
7. ✅ Buffer position MUST be reset (`seek(0)`) after `img.save()`
8. ✅ Gemini payload MUST include `mime_type` in `inline_data` (required)
9. ✅ Temp files MUST always be cleaned up (even on error)
10. ✅ Database cursors MUST always be closed (prevents connection pool exhaustion)

---

**See sections below for detailed explanations and code examples.**

---

## 🖼️ **IMAGE UPLOAD FLOW** (COMPLETE)

### **Flow Overview**
1. User selects photos in frontend (`templates/create.html`)
2. Frontend uploads to `/api/upload-photos` via FormData
3. Backend processes, compresses, and uploads to Supabase Storage `temp-photos` bucket
4. Backend returns Supabase Storage URLs
5. Frontend stores URLs in `uploadedPhotos` array and displays previews
6. On page unload/close, frontend calls cleanup endpoint to delete from `temp-photos`
7. When listing is saved, photos are moved to `listing-images` bucket

---

### **1. Frontend Upload** (`templates/create.html`)

#### **File Selection**
- User clicks file input or drags files
- Multiple files supported
- Files validated client-side (image types only)

#### **Upload Function**
```javascript
// Uses FormData to send files
const formData = new FormData();
files.forEach(file => formData.append('photos', file));

fetch('/api/upload-photos', {
    method: 'POST',
    body: formData  // No Content-Type header - browser sets multipart/form-data
})
```

#### **Response Handling**
- Receives `{success: true, paths: [urls], count: N}`
- URLs are Supabase Storage URLs: `https://[project].supabase.co/storage/v1/object/public/temp-photos/[filename]`
- URLs stored in `uploadedPhotos` array
- Photo previews displayed in UI

#### **Cleanup on Page Unload** ⚠️ **CRITICAL**
```javascript
// Store temp photo URLs for cleanup
let tempPhotoUrls = uploadedPhotos.filter(url => 
    url.includes('supabase.co') && url.includes('temp-photos')
);

// Cleanup handlers (MUST BE PRESENT)
window.addEventListener('beforeunload', cleanupTempPhotos);
document.addEventListener('visibilitychange', function() {
    if (document.hidden) cleanupTempPhotos();
});

function cleanupTempPhotos() {
    // Only cleanup if listing hasn't been saved
    if (hasBeenSaved) return;
    
    // Use fetch with keepalive (NOT sendBeacon - doesn't support JSON properly)
    fetch('/api/cleanup-temp-photos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({photos: tempPhotoUrls}),
        keepalive: true  // Ensures request completes even if page closes
    });
}
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST use `fetch` with `keepalive: true` (NOT `sendBeacon`)
- ✅ MUST check `hasBeenSaved` flag before cleanup
- ✅ MUST only cleanup URLs from `temp-photos` bucket
- ✅ MUST have both `beforeunload` and `visibilitychange` handlers

---

### **2. Backend Upload Endpoint** (`routes_main.py` - `/api/upload-photos`)

#### **Route Handler**
```python
@main_bp.route("/api/upload-photos", methods=["POST"])
@login_required
def api_upload_photos():
```

#### **Processing Steps** (IN ORDER)

**Step 1: Receive Files**
- Get files from `request.files.getlist('photos')`
- Validate file type (JPEG, PNG, GIF, WebP)

**Step 2: Image Compression** ⚠️ **CRITICAL**
```python
from PIL import Image
import io

img = Image.open(file)
# Convert RGBA to RGB if needed
if img.mode == 'RGBA':
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[-1])
    img = background

# Resize if too large (max 2048px on longest side)
max_size = 2048
if max(img.size) > max_size:
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

# Compress to JPEG (quality 85)
compressed_file = io.BytesIO()
img.save(compressed_file, format='JPEG', quality=85, optimize=True)
compressed_file.seek(0)  # ⚠️ CRITICAL: Reset position before reading
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST convert RGBA to RGB (JPEG doesn't support transparency)
- ✅ MUST resize if dimensions exceed 2048px
- ✅ MUST call `compressed_file.seek(0)` after `img.save()`
- ✅ MUST save as JPEG (universally supported)

**Step 3: Upload to Supabase Storage** ⚠️ **CRITICAL BUCKET**
```python
from src.storage.supabase_storage import get_supabase_storage

storage = get_supabase_storage()

# ⚠️ MUST use folder='temp' to upload to temp-photos bucket
success, result = storage.upload_photo(
    file_data=compressed_file,  # BytesIO object
    folder='temp',  # ⚠️ This maps to 'temp-photos' bucket
    content_type='image/jpeg'
)
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST use `folder='temp'` (NOT 'draft' or 'listing')
- ✅ This maps to `SUPABASE_BUCKET_TEMP` env var (default: 'temp-photos')
- ✅ Photos MUST go to `temp-photos` bucket on initial upload
- ✅ Return Supabase Storage public URL

**Step 4: Logging** (for debugging)
```python
import logging
if 'temp-photos' in result:
    logging.info(f"[UPLOAD DEBUG] ✅ Photo uploaded to temp-photos bucket")
elif 'listing-images' in result:
    logging.warning(f"[UPLOAD DEBUG] ⚠️ Photo uploaded to listing-images bucket (WRONG!)")
```

**Step 5: Return URLs**
```python
return jsonify({
    "success": True,
    "paths": uploaded_urls,  # Array of Supabase Storage URLs
    "count": len(uploaded_urls)
})
```

---

### **3. Supabase Storage Manager** (`src/storage/supabase_storage.py`)

#### **Bucket Mapping** ⚠️ **CRITICAL**
```python
# Environment variables (with .strip() to remove whitespace)
self.temp_bucket = os.getenv('SUPABASE_BUCKET_TEMP', 'temp-photos').strip()
self.drafts_bucket = os.getenv('SUPABASE_BUCKET_DRAFTS', 'draft-images').strip()
self.listings_bucket = os.getenv('SUPABASE_BUCKET_LISTINGS', 'listing-images').strip()

# Folder to bucket mapping
bucket_map = {
    'temp': self.temp_bucket,      # → 'temp-photos'
    'draft': self.drafts_bucket,    # → 'draft-images'
    'listing': self.listings_bucket # → 'listing-images'
}
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST strip whitespace from bucket names (prevents newline issues)
- ✅ `folder='temp'` → `temp-photos` bucket
- ✅ `folder='draft'` → `draft-images` bucket
- ✅ `folder='listing'` → `listing-images` bucket

#### **Upload Function**
```python
def upload_photo(self, file_data, folder='temp', content_type='image/jpeg'):
    bucket = self._get_bucket_for_folder(folder)
    
    # Generate unique filename
    filename = f"{uuid.uuid4().hex}.jpg"
    
    # Upload to Supabase Storage
    response = self.client.storage.from_(bucket).upload(
        path=filename,
        file=file_data,
        file_options={"content-type": content_type}
    )
    
    # Return public URL
    url = f"{self.supabase_url}/storage/v1/object/public/{bucket}/{filename}"
    return True, url
```

#### **Download Function**
```python
def download_photo(self, url: str) -> bytes:
    # Extract bucket and filename from URL
    # Download file data
    # Return bytes
```

#### **Delete Function**
```python
def delete_photo(self, url: str) -> bool:
    # Extract bucket and filename from URL
    # Delete from Supabase Storage
    # Return success status
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST use Supabase Python SDK for all operations
- ✅ MUST use service role key (bypasses RLS)
- ✅ MUST return public URLs (not signed URLs) for image display

---

### **4. Cleanup Endpoint** (`routes_main.py` - `/api/cleanup-temp-photos`)

#### **Route Handler**
```python
@main_bp.route("/api/cleanup-temp-photos", methods=["POST"])
@login_required
def api_cleanup_temp_photos():
    data = request.get_json()
    photo_urls = data.get('photos', [])
    
    storage = get_supabase_storage()
    deleted = 0
    failed = 0
    
    for url in photo_urls:
        # ⚠️ ONLY delete from temp-photos bucket
        if 'supabase.co' in url and 'temp-photos' in url:
            if storage.delete_photo(url):
                deleted += 1
            else:
                failed += 1
        else:
            logging.warning(f"[CLEANUP] ⚠️ Skipping URL (not temp-photos bucket)")
    
    return jsonify({
        "success": True,
        "deleted": deleted,
        "failed": failed
    })
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST only delete URLs from `temp-photos` bucket
- ✅ MUST skip URLs from other buckets (draft-images, listing-images)
- ✅ MUST log cleanup operations for debugging

---

## 🤖 **AI ANALYSIS FLOW** (COMPLETE)

### **Flow Overview**
1. Frontend sends photo URLs to `/api/analyze` endpoint
2. Backend downloads images from Supabase Storage to temp files
3. Backend creates `Photo` objects with local paths
4. Backend calls `GeminiClassifier.analyze_item()` with photos
5. Gemini prepares images (validate, convert, resize, compress, encode to base64)
6. Gemini builds API payload with images and prompt
7. Gemini sends POST request to Google API with key in query string (NO Authorization header)
8. Gemini parses JSON response and returns analysis
9. Backend returns analysis to frontend
10. Backend cleans up temp files

---

### **1. Frontend Analysis Request** (`templates/create.html`)

#### **Trigger**
- User clicks "Analyze with AI" button
- After photos are uploaded

#### **Request**
```javascript
const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        photos: uploadedPhotos  // Array of Supabase Storage URLs
    })
});

const data = await response.json();
if (data.success) {
    const analysis = data.analysis;
    // Fill form fields with analysis results
}
```

---

### **2. Backend Analysis Endpoint** (`routes_main.py` - `/api/analyze`)

#### **Route Handler**
```python
@main_bp.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze():
    data = request.get_json()
    paths = data.get("photos", [])  # Array of Supabase Storage URLs
    
    # Log which bucket URLs are from (for debugging)
    for path in paths:
        if 'temp-photos' in path:
            logging.info(f"[ANALYZE DEBUG] ✅ URL from temp-photos bucket")
        elif 'listing-images' in path:
            logging.warning(f"[ANALYZE DEBUG] ⚠️ URL from listing-images bucket (unexpected)")
```

#### **Download Images from Supabase** ⚠️ **CRITICAL**
```python
from src.storage.supabase_storage import get_supabase_storage
import tempfile
import os

storage = get_supabase_storage()
photo_objects = []
temp_files = []  # Track for cleanup

for path in paths:
    if 'supabase.co' in path:
        # Download from Supabase Storage
        file_data = storage.download_photo(path)
        
        if file_data and len(file_data) > 0:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(file_data)
            temp_file.flush()  # ⚠️ Ensure data written
            os.fsync(temp_file.fileno())  # ⚠️ Force write to disk
            temp_file.close()
            local_path = temp_file.name
            temp_files.append(local_path)
            
            # Verify file exists
            if not Path(local_path).exists() or Path(local_path).stat().st_size == 0:
                return jsonify({"error": "Failed to create temp file"}), 500
        else:
            return jsonify({"error": "Failed to download from Supabase"}), 404
    
    # Create Photo object
    photo_objects.append(Photo(url=path, local_path=local_path))
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST download from Supabase Storage for URLs containing 'supabase.co'
- ✅ MUST call `temp_file.flush()` after writing
- ✅ MUST call `os.fsync(temp_file.fileno())` to force disk write
- ✅ MUST verify file exists and size > 0 before using
- ✅ MUST track temp files in `temp_files` array for cleanup

#### **Initialize Gemini Classifier**
```python
from src.ai.gemini_classifier import GeminiClassifier

classifier = GeminiClassifier.from_env()
```

#### **Analyze Photos**
```python
result = classifier.analyze_item(photo_objects)
```

#### **Cleanup Temp Files** ⚠️ **CRITICAL**
```python
# ALWAYS cleanup temp files, even on error
for temp_file in temp_files:
    try:
        os.unlink(temp_file)
    except:
        pass
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST cleanup temp files after analysis (even on error)
- ✅ MUST use try/except to handle cleanup errors gracefully

#### **Return Results**
```python
if result.get("error"):
    return jsonify({"success": False, "error": result.get("error")}), 500

return jsonify({"success": True, "analysis": result})
```

---

### **3. Gemini Classifier** (`src/ai/gemini_classifier.py`)

#### **Initialization** ⚠️ **CRITICAL - API KEY HANDLING**

```python
def __init__(self, api_key: Optional[str] = None):
    # Check multiple env var names (including typo GEMENI_API_KEY)
    raw_key = (
        api_key or
        os.getenv("GOOGLE_AI_API_KEY") or
        os.getenv("GEMINI_API_KEY") or
        os.getenv("GEMENI_API_KEY")  # Common typo
    )
    
    if not raw_key:
        raise ValueError("API key must be set")
    
    # ⚠️ CRITICAL: Strip whitespace (fixes hidden newline/space issues)
    self.api_key = raw_key.strip()
    
    # Debug logging (first/last 5 chars only for security)
    logger.info(f"[GEMINI DEBUG] API Key loaded: length={len(self.api_key)}")
    
    # Validate key format
    if len(self.api_key) < 30 or len(self.api_key) > 60:
        logger.warning(f"[GEMINI DEBUG] ⚠️ Key length unexpected: {len(self.api_key)}")
    if not self.api_key.startswith('AIza'):
        logger.warning(f"[GEMINI DEBUG] ⚠️ Key doesn't start with 'AIza'")
    
    # Model and API URL
    self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST strip whitespace from API key (`.strip()`)
- ✅ MUST check multiple env var names (GOOGLE_AI_API_KEY, GEMINI_API_KEY, GEMENI_API_KEY)
- ✅ MUST log key length and format for debugging
- ✅ API key should be 39-45 characters and start with 'AIza'

#### **Image Preparation** ⚠️ **CRITICAL**

```python
def _prepare_image_for_gemini(self, image_path: str) -> tuple[bytes, str]:
    """
    Validate and convert image to Gemini-compatible format.
    
    Steps:
    1. Open and validate image exists
    2. Detect actual format using PIL (not file extension)
    3. Convert unsupported formats (HEIC, etc.) to JPEG
    4. Resize if dimensions exceed 20MP limit
    5. Compress if file size exceeds 20MB
    6. Convert RGBA/transparency to RGB
    """
    from PIL import Image
    import io
    
    # Open image
    img = Image.open(image_path)
    
    # Validate image (use img.load() - Image.verify() is deprecated)
    img.load()
    
    # Convert RGBA to RGB (JPEG doesn't support transparency)
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    
    # Resize if too large (20MP limit = ~4472x4472 pixels)
    max_pixels = 20_000_000
    if img.width * img.height > max_pixels:
        scale = (max_pixels / (img.width * img.height)) ** 0.5
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Compress to JPEG (quality 85)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)  # ⚠️ CRITICAL: Reset position before reading
    
    # Get bytes
    image_bytes = output.read()
    
    # Validate size (20MB limit)
    max_size = 20 * 1024 * 1024  # 20MB
    if len(image_bytes) > max_size:
        # Further compress
        quality = 70
        while len(image_bytes) > max_size and quality > 20:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            image_bytes = output.read()
            quality -= 10
    
    return image_bytes, 'image/jpeg'
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST use `img.load()` for validation (NOT `Image.verify()` - deprecated)
- ✅ MUST convert RGBA to RGB (JPEG doesn't support transparency)
- ✅ MUST resize if dimensions exceed 20MP (4472x4472 pixels)
- ✅ MUST compress to under 20MB file size
- ✅ MUST call `output.seek(0)` after `img.save()` before reading
- ✅ MUST return `(bytes, 'image/jpeg')` tuple

#### **Base64 Encoding**

```python
def _encode_image_to_base64(self, image_path: str) -> str:
    """
    Prepare and encode image for Gemini API.
    Returns ONLY the base64 string (no data:image prefix).
    """
    image_bytes, _ = self._prepare_image_for_gemini(image_path)
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    
    # Ensure no data URI prefix (strip if somehow present)
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',')[1] if ',' in base64_str else base64_str
    
    return base64_str
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST return raw base64 string (NO `data:image/jpeg;base64,` prefix)
- ✅ MUST strip prefix if present

#### **Analysis Method**

```python
def analyze_item(self, photos: List[Photo]) -> Dict[str, Any]:
    # Prepare images (limit to 4 for speed)
    image_parts = []
    for i, photo in enumerate(photos[:4]):
        if photo.local_path:
            # Validate file exists
            if not Path(photo.local_path).exists():
                continue
            
            # Encode to base64
            image_b64 = self._encode_image_to_base64(photo.local_path)
            mime_type = 'image/jpeg'  # Always JPEG after conversion
            
            # Build image part
            image_parts.append({
                "inline_data": {
                    "mime_type": mime_type,  # ⚠️ REQUIRED by Gemini
                    "data": image_b64        # ⚠️ Raw base64 (no prefix)
                }
            })
    
    # Build prompt (omitted for brevity - see code for full prompt)
    prompt = "..."
    
    # Build payload
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                *image_parts  # Each has inline_data with mime_type and data
            ]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
        }
    }
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST include `mime_type` in `inline_data` (Gemini rejects without it)
- ✅ MUST use raw base64 string in `data` field (no prefix)
- ✅ MUST structure as `contents[0].parts[]` with text + images
- ✅ MUST limit to 4 images for performance

#### **API Request** ⚠️ **CRITICAL - NO AUTHORIZATION HEADER**

```python
# CRITICAL: Gemini API ONLY wants key in query string, NO Authorization header
api_url_with_key = f"{self.api_url}?key={self.api_key}"

# ⚠️ ONLY Content-Type header (NO Authorization header)
headers = {"Content-Type": "application/json"}

response = requests.post(
    api_url_with_key,
    headers=headers,
    json=payload,
    timeout=30
)
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST include API key in query string: `?key=API_KEY`
- ✅ MUST NOT include `Authorization: Bearer` header (will be rejected)
- ✅ MUST only include `Content-Type: application/json` header
- ✅ This is the #2 most common cause of "invalid key" errors

#### **Response Handling**

```python
if response.status_code == 200:
    # Check if response is actually JSON (not HTML error page)
    content_type = response.headers.get('Content-Type', '').lower()
    if 'application/json' not in content_type:
        logger.error(f"[GEMINI ERROR] Response is not JSON! Content-Type: {content_type}")
        logger.error(f"[GEMINI ERROR] Response text: {response.text[:500]}")
        return {"error": "Gemini API returned non-JSON response (usually means invalid API key)"}
    
    # Parse JSON
    result = response.json()
    
    # Extract text from response
    text = result['candidates'][0]['content']['parts'][0]['text']
    
    # Parse JSON from text (Gemini returns JSON as text)
    analysis = json.loads(text)
    
    return analysis

else:
    # Handle errors
    logger.error(f"[GEMINI ERROR] Status {response.status_code}: {response.text[:500]}")
    return {"error": f"Gemini API error: {response.status_code}"}
```

**⚠️ NON-NEGOTIABLE REQUIREMENTS:**
- ✅ MUST check Content-Type header (HTML means invalid key/endpoint)
- ✅ MUST parse JSON from response text (Gemini returns JSON as string)
- ✅ MUST handle HTML responses (indicates invalid API key)

---

## 🔧 **CRITICAL FIXES IMPLEMENTED**

### **1. API Key Issues** ✅ FIXED

**Problem**: Gemini API returning HTML instead of JSON ("SyntaxError: Unexpected token '<'")

**Root Causes Found:**
1. **Hidden characters in API key** (newlines, spaces)
2. **Wrong env var name** (typo: GEMENI_API_KEY vs GEMINI_API_KEY)
3. **Authorization header present** (Gemini rejects this)

**Fixes Applied:**
- ✅ Added `.strip()` to API key (removes whitespace/newlines)
- ✅ Check multiple env var names (including typo)
- ✅ Verify NO Authorization header (only query string key)
- ✅ Log key length and format for debugging
- ✅ Check Content-Type header for HTML responses

**Files Modified:**
- `src/ai/gemini_classifier.py` - `__init__()` and API request

---

### **2. Image Processing Issues** ✅ FIXED

**Problem**: Images failing validation or encoding

**Root Causes Found:**
1. **RGBA images** (JPEG doesn't support transparency)
2. **Image.verify() deprecated** (causing errors)
3. **Buffer position not reset** (after img.save())
4. **Base64 prefix present** (Gemini rejects data: prefix)

**Fixes Applied:**
- ✅ Convert RGBA to RGB with white background
- ✅ Use `img.load()` instead of `Image.verify()`
- ✅ Call `output.seek(0)` after `img.save()`
- ✅ Strip `data:image/` prefix from base64

**Files Modified:**
- `src/ai/gemini_classifier.py` - `_prepare_image_for_gemini()`
- `src/ai/gemini_classifier.py` - `_encode_image_to_base64()`

---

### **3. Supabase Storage Bucket Issues** ✅ FIXED

**Problem**: Photos uploading to wrong bucket (listing-images instead of temp-photos)

**Root Causes Found:**
1. **Wrong folder parameter** (using 'listing' instead of 'temp')
2. **No cleanup on page unload** (temp photos accumulating)

**Fixes Applied:**
- ✅ Use `folder='temp'` for initial uploads (maps to temp-photos bucket)
- ✅ Added cleanup endpoint (`/api/cleanup-temp-photos`)
- ✅ Added frontend cleanup handlers (beforeunload, visibilitychange)
- ✅ Use `fetch` with `keepalive: true` (NOT sendBeacon)
- ✅ Only cleanup URLs from temp-photos bucket

**Files Modified:**
- `routes_main.py` - `/api/upload-photos` (uses folder='temp')
- `routes_main.py` - `/api/cleanup-temp-photos` (new endpoint)
- `templates/create.html` - cleanup handlers and function

---

### **4. Temp File Handling** ✅ FIXED

**Problem**: Temp files not being created properly or cleaned up

**Root Causes Found:**
1. **File not flushed to disk** (before reading)
2. **No verification** (file exists and size > 0)
3. **Not cleaned up** (on error or after use)

**Fixes Applied:**
- ✅ Call `temp_file.flush()` after writing
- ✅ Call `os.fsync(temp_file.fileno())` to force disk write
- ✅ Verify file exists and size > 0 before using
- ✅ Always cleanup temp files (even on error)

**Files Modified:**
- `routes_main.py` - `/api/analyze` (download and cleanup logic)

---

### **5. Database Connection Pool Exhaustion** ✅ FIXED

**Problem**: `MaxClientsInSessionMode: max clients reached`

**Root Causes Found:**
1. **Cursors not being closed** (connections stay locked)
2. **Session pooling limits** (limited connections on budget tier)

**Fixes Applied:**
- ✅ Added `_execute_with_cursor()` helper method
- ✅ Ensured all cursors are closed in `try...finally` blocks
- ✅ Fixed critical methods: `get_user_by_id()`, `create_user()`, etc.

**Files Modified:**
- `src/database/db.py` - Cursor management
- `web_app.py` - `/listings` route cursor cleanup

---

## 📋 **CHECKLIST FOR FUTURE CHANGES**

### **Before Modifying Image Upload Flow:**
- [ ] Verify `folder='temp'` is used for initial uploads
- [ ] Verify photos go to `temp-photos` bucket (check logs)
- [ ] Verify cleanup handlers are present in frontend
- [ ] Verify `fetch` with `keepalive: true` is used (NOT sendBeacon)
- [ ] Verify `hasBeenSaved` flag prevents cleanup of saved listings

### **Before Modifying AI Analysis Flow:**
- [ ] Verify API key is stripped (`.strip()`)
- [ ] Verify NO Authorization header (only query string key)
- [ ] Verify `mime_type` is included in `inline_data`
- [ ] Verify base64 has NO `data:image/` prefix
- [ ] Verify `output.seek(0)` after `img.save()`
- [ ] Verify RGBA images are converted to RGB
- [ ] Verify temp files are always cleaned up
- [ ] Verify Content-Type header is checked (not HTML)

### **Before Modifying Database Code:**
- [ ] Verify all cursors are closed in `try...finally` blocks
- [ ] Use `_execute_with_cursor()` helper for new methods
- [ ] Test connection pool doesn't exhaust (especially on Session pooling)

---

## 🚨 **DO NOT BREAK THESE**

1. **API Key Stripping** - `.strip()` on API key is CRITICAL
2. **No Authorization Header** - Only query string key for Gemini
3. **Temp Bucket Usage** - Initial uploads MUST go to temp-photos
4. **Cleanup Handlers** - Must have beforeunload + visibilitychange
5. **Buffer Position Reset** - `seek(0)` after `img.save()`
6. **RGBA to RGB Conversion** - JPEG doesn't support transparency
7. **Base64 No Prefix** - Gemini rejects `data:image/` prefix
8. **MIME Type Required** - Gemini rejects images without mime_type
9. **Temp File Cleanup** - Always cleanup temp files
10. **Cursor Cleanup** - Always close database cursors

---

**This document is the source of truth. Update it whenever flows change.**

