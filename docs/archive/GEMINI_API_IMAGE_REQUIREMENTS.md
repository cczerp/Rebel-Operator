# Gemini API Image Requirements & Troubleshooting

## Current Implementation Analysis

### How Images Are Currently Sent to Gemini

**Location**: `src/ai/gemini_classifier.py`

**Process**:
1. Photo object has `local_path` (e.g., `./data/uploads/abc123.jpg`)
2. Image is read and encoded to base64: `base64.b64encode(image_file.read()).decode("utf-8")`
3. MIME type determined from file extension
4. Structured as:
```python
{
    "inline_data": {
        "mime_type": "image/jpeg",  # or image/png, image/gif, image/webp
        "data": "base64_encoded_string"
    }
}
```
5. Added to `parts` array along with text prompt
6. Sent via POST to: `https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}`

### Current Error
**Error Message**: "Invalid request to Gemini. Make sure photos are valid images."
**HTTP Status**: 400 (Bad Request)
**Location**: Line 344 in `gemini_classifier.py`

## Gemini API Official Requirements

### Supported Image Formats
According to Google Gemini API documentation:
- **JPEG** (`image/jpeg`) ✅
- **PNG** (`image/png`) ✅
- **GIF** (`image/gif`) ✅
- **WebP** (`image/webp`) ✅
- **HEIC/HEIF** - NOT directly supported (needs conversion)

### Image Size Limits
- **Maximum file size**: 20MB per image
- **Maximum dimensions**: 20 megapixels (e.g., 4096x4096)
- **Recommended**: Keep under 4MB for faster processing

### Base64 Encoding Requirements
- Must be valid base64 string
- No data URI prefix (just the base64 string)
- Must match the MIME type declared

### Request Structure
```json
{
  "contents": [{
    "parts": [
      {"text": "prompt text"},
      {
        "inline_data": {
          "mime_type": "image/jpeg",
          "data": "base64_encoded_string_here"
        }
      }
    ]
  }],
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 2048
  }
}
```

## Potential Issues & Solutions

### Issue 1: File Doesn't Exist
**Symptom**: Error when trying to read file
**Check**: Verify `local_path` exists before encoding
**Solution**: Add file existence check before encoding

### Issue 2: Invalid Image File
**Symptom**: File exists but is corrupted or not a valid image
**Check**: Validate image can be opened with PIL/Pillow
**Solution**: Try opening image before encoding to verify it's valid

### Issue 3: Wrong MIME Type
**Symptom**: MIME type doesn't match actual file format
**Check**: File extension might not match actual format
**Solution**: Detect actual format using PIL instead of extension

### Issue 4: Base64 Encoding Issue
**Symptom**: Malformed base64 string
**Check**: Verify base64 encoding is correct
**Solution**: Ensure proper encoding/decoding

### Issue 5: Image Too Large
**Symptom**: File exceeds Gemini's limits
**Check**: File size and dimensions
**Solution**: Resize/compress before encoding

### Issue 6: Unsupported Format
**Symptom**: HEIC or other unsupported format
**Check**: File extension and actual format
**Solution**: Convert to JPEG/PNG before sending

## Recommended Fixes

1. **Add File Validation**:
   - Check file exists
   - Verify file is readable
   - Check file size (< 20MB)

2. **Image Format Detection**:
   - Use PIL to detect actual format
   - Convert unsupported formats (HEIC, WebP) to JPEG
   - Ensure MIME type matches actual format

3. **Image Optimization**:
   - Resize if too large
   - Compress if file size is large
   - Convert RGBA to RGB if needed

4. **Better Error Messages**:
   - Log the actual Gemini API error response
   - Show which image failed
   - Provide specific guidance

5. **Validation Before API Call**:
   - Verify all images are valid before sending
   - Return clear error if any image is invalid

## Next Steps

1. Add comprehensive image validation
2. Implement format detection and conversion
3. Add size/dimension checks
4. Improve error logging to see actual Gemini response
5. Test with various image formats

