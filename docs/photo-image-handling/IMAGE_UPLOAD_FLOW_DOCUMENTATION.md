# Image Upload & Display Flow Documentation

## Overview
This document describes the current working image upload and display system that allows users to select images, upload them to the server, and see them displayed on the create listing page.

## Critical Components

### 1. Frontend: Photo Selection & Upload (`templates/create.html`)

#### Photo Input Elements
- **Camera Input**: `<input type="file" id="cameraInput" capture="environment">`
- **File Upload Input**: `<input type="file" id="photoInput" multiple>`
- Both trigger `handlePhotoSelect(event)` function

#### JavaScript State
```javascript
let uploadedPhotos = [];  // Stores array of server paths like ["/uploads/abc123.jpg"]
```

#### Upload Flow (`handlePhotoSelect` function)
1. **File Selection**: User selects files via camera or file picker
2. **Validation**: Checks event and files exist
3. **FormData Creation**: Creates FormData with all selected files
4. **API Call**: POST to `/api/upload-photos` with FormData
5. **Response Handling**: 
   - Server returns `{success: true, paths: ["/uploads/file1.jpg"], count: 1}`
   - Paths appended to `uploadedPhotos` array
6. **Preview Display**: Creates DOM elements for each photo:
   - Image element with `src = '/' + data.paths[i]`
   - Delete button overlay
   - Click handlers for edit/zoom
7. **Show Analyze Button**: Displays "Analyze with AI" button

#### Key Code Location
- **File**: `templates/create.html`
- **Function**: `handlePhotoSelect()` starting at line 325
- **Event Listeners**: Attached to file inputs via `onchange="handlePhotoSelect(event)"`

### 2. Backend: Photo Upload API (`routes_main.py`)

#### Endpoint: `/api/upload-photos`
- **Method**: POST
- **Auth**: `@login_required`
- **Input**: FormData with `photos` field (multiple files)

#### Processing Steps
1. **Receive Files**: `request.files.getlist('photos')`
2. **Validate**: Check file extensions (png, jpg, jpeg, gif, webp, heic)
3. **Compress**: `compress_image()` function:
   - Converts RGBA to RGB if needed
   - Resizes if > 2048px
   - Compresses to max 2MB, quality 85
4. **Save**: 
   - Generate UUID filename: `{uuid}.{ext}`
   - Save to `./data/uploads/{filename}`
5. **Return**: JSON with web-accessible paths:
   ```json
   {
     "success": true,
     "paths": ["/uploads/abc123.jpg"],
     "count": 1
   }
   ```

#### Key Code Location
- **File**: `routes_main.py`
- **Function**: `api_upload_photos()` starting at line 102

### 3. Backend: Photo Serving (`routes_main.py`)

#### Endpoint: `/uploads/<filename>`
- **Method**: GET
- **Purpose**: Serve uploaded image files to browser
- **Implementation**: `send_from_directory(upload_dir, filename)`
- **Location**: `./data/uploads/{filename}`

#### Key Code Location
- **File**: `routes_main.py`
- **Function**: `serve_upload()` starting at line 149

### 4. Image Display in Browser

#### Path Resolution
- Server returns: `"/uploads/abc123.jpg"`
- Frontend sets: `img.src = '/' + data.paths[i]`
- Browser requests: `http://domain/uploads/abc123.jpg`
- Flask serves from: `./data/uploads/abc123.jpg`

#### Preview Container Structure
```html
<div class="photo-preview-container">
  <img src="/uploads/abc123.jpg" class="photo-preview">
  <button class="photo-delete-btn">×</button>
</div>
```

## Data Flow Summary

```
User Action
    ↓
Select Files (camera/file picker)
    ↓
handlePhotoSelect(event)
    ↓
Create FormData
    ↓
POST /api/upload-photos
    ↓
Server: Compress & Save to ./data/uploads/
    ↓
Server: Return paths ["/uploads/file.jpg"]
    ↓
Frontend: Append to uploadedPhotos array
    ↓
Frontend: Create preview DOM elements
    ↓
Browser: Request /uploads/file.jpg
    ↓
Server: send_from_directory serves file
    ↓
Image displays in browser
```

## Critical Paths & Files

### Frontend
- **File**: `templates/create.html`
- **Key Function**: `handlePhotoSelect()` (line 325)
- **State Variable**: `uploadedPhotos` (line 320)
- **Preview Container**: `#photoPreview` div

### Backend
- **File**: `routes_main.py`
- **Upload Endpoint**: `api_upload_photos()` (line 102)
- **Serve Endpoint**: `serve_upload()` (line 149)
- **Storage Directory**: `./data/uploads/`

### Helper Functions
- **Compression**: `compress_image()` in `routes_main.py` (line 62)
- **File Validation**: `allowed_file()` in `routes_main.py` (line 58)

## Current Working State

✅ **Working**:
- File selection (camera & file picker)
- Upload to server
- Image compression
- File saving to `./data/uploads/`
- Path return to frontend
- Image display in browser
- Delete button functionality
- Preview container creation

❌ **Not Working**:
- Photo editor (click to edit)
- AI analyzer (returns HTML error instead of JSON)
- Image zoom (right-click)

## Recovery Steps

If image upload breaks, verify:

1. **Frontend**:
   - `uploadedPhotos` array exists
   - `handlePhotoSelect()` function is defined
   - File inputs have `onchange="handlePhotoSelect(event)"`
   - Preview container `#photoPreview` exists in DOM

2. **Backend**:
   - `/api/upload-photos` route exists and has `@login_required`
   - `compress_image()` function works
   - `./data/uploads/` directory exists and is writable
   - `/uploads/<filename>` route exists

3. **Network**:
   - Check browser console for fetch errors
   - Verify response is JSON, not HTML
   - Check server logs for upload errors

## Notes

- Images are stored temporarily in `./data/uploads/` - no cleanup yet
- Paths are relative web paths, not absolute file paths
- Compression happens server-side before saving
- Multiple files can be uploaded in one request
- Photos array is stored in `uploadedPhotos` for later use (draft save, AI analysis)

