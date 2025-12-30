# Gemini API Image Format Requirements - Research Summary

## Official Supported Formats (from Google Gemini API Documentation)

Based on Google's Gemini API v1 documentation, the following image formats are **officially supported**:

### ✅ Supported MIME Types:
1. **`image/jpeg`** - JPEG images (most common)
2. **`image/png`** - PNG images (supports transparency)
3. **`image/gif`** - GIF images (animated GIFs supported)
4. **`image/webp`** - WebP images (modern format)

### ❌ NOT Supported:
- **`image/heic`** / **`image/heif`** - Apple HEIC format (must convert)
- **`image/bmp`** - Bitmap (must convert)
- **`image/tiff`** - TIFF (must convert)
- **`image/svg+xml`** - SVG vector graphics (not supported)

## Image Size & Dimension Limits

### File Size:
- **Maximum**: 20MB per image
- **Recommended**: Under 4MB for faster processing
- **Base64 overhead**: Base64 encoding increases size by ~33%, so a 15MB image becomes ~20MB when encoded

### Dimensions:
- **Maximum**: 20 megapixels total (e.g., 4096x4096 = 16.7MP ✅)
- **Example limits**:
  - 4096 x 4096 = 16.7MP ✅
  - 5000 x 4000 = 20MP ✅ (at limit)
  - 6000 x 4000 = 24MP ❌ (exceeds limit)

## Base64 Encoding Requirements

1. **Format**: Must be valid base64 string
2. **No data URI prefix**: Just the base64 string (no `data:image/jpeg;base64,` prefix)
3. **MIME type must match**: The declared `mime_type` must match the actual image format
4. **UTF-8 encoding**: Base64 string must be UTF-8 encoded

## Current Implementation Issues

### Problem 1: MIME Type Detection
**Current code** uses file extension to determine MIME type:
```python
ext = Path(image_path).suffix.lower()
mime_types = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
```

**Issue**: File extension might not match actual format. For example:
- A file saved as `.jpg` might actually be a PNG
- A file saved as `.png` might actually be a WebP
- HEIC files might have `.jpg` extension

**Solution**: Use PIL/Pillow to detect actual format:
```python
from PIL import Image
img = Image.open(image_path)
actual_format = img.format  # Returns 'JPEG', 'PNG', 'GIF', 'WEBP', etc.
```

### Problem 2: Format Conversion
**Current code** doesn't convert unsupported formats:
- HEIC files uploaded by users won't work
- Files with wrong extensions won't be detected

**Solution**: Convert all images to a supported format (JPEG recommended) before sending to Gemini.

### Problem 3: Image Validation
**Current code** doesn't validate images before encoding:
- Corrupted files will fail
- Invalid formats will fail
- Oversized images will fail

**Solution**: Validate image before encoding:
1. Check file exists
2. Try to open with PIL (validates it's a real image)
3. Check file size (< 20MB)
4. Check dimensions (< 20MP)
5. Verify format is supported

## Recommended Implementation

### Step 1: Validate & Convert Image
```python
from PIL import Image
import io

def prepare_image_for_gemini(image_path: str) -> tuple[bytes, str]:
    """
    Validate and convert image to Gemini-compatible format.
    
    Returns:
        (image_bytes, mime_type)
    """
    # Open and validate image
    img = Image.open(image_path)
    
    # Check dimensions (20MP limit)
    total_pixels = img.size[0] * img.size[1]
    if total_pixels > 20_000_000:
        # Resize to fit within 20MP
        ratio = (20_000_000 / total_pixels) ** 0.5
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert RGBA/LA/P to RGB (remove alpha channel)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to JPEG (most compatible format)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    image_bytes = output.getvalue()
    
    # Check file size (20MB limit)
    if len(image_bytes) > 20 * 1024 * 1024:
        # Reduce quality if still too large
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=60, optimize=True)
        image_bytes = output.getvalue()
    
    return image_bytes, 'image/jpeg'
```

### Step 2: Update Gemini Classifier
```python
def _encode_image_to_base64(self, image_path: str) -> tuple[str, str]:
    """
    Prepare and encode image for Gemini API.
    
    Returns:
        (base64_string, mime_type)
    """
    # Validate and convert image
    image_bytes, mime_type = prepare_image_for_gemini(image_path)
    
    # Encode to base64
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    
    return base64_string, mime_type
```

## Use Cases & Compliance

### Use Case 1: User Uploads from Phone
- **Common formats**: HEIC (iPhone), JPEG, PNG
- **Action**: Convert HEIC → JPEG, validate all others

### Use Case 2: User Uploads from Computer
- **Common formats**: JPEG, PNG, WebP, GIF
- **Action**: Validate format, convert if needed

### Use Case 3: Downloaded Images
- **Common formats**: Various (might have wrong extensions)
- **Action**: Detect actual format, convert to JPEG

### Use Case 4: Compressed Images from Supabase
- **Current**: Images are compressed to JPEG before upload
- **Action**: Should already be JPEG, but validate anyway

## Error Messages to Handle

1. **"Invalid image format"** → Format not supported, convert to JPEG
2. **"Image too large"** → Resize or reduce quality
3. **"Invalid base64"** → Encoding issue, re-encode
4. **"MIME type mismatch"** → MIME type doesn't match actual format, detect actual format

## Testing Checklist

- [ ] JPEG images (various sizes)
- [ ] PNG images (with/without transparency)
- [ ] GIF images (static and animated)
- [ ] WebP images
- [ ] HEIC images (iPhone photos)
- [ ] Corrupted images (should fail gracefully)
- [ ] Oversized images (>20MB, should resize)
- [ ] High-resolution images (>20MP, should resize)
- [ ] Images with wrong extensions (should detect actual format)

