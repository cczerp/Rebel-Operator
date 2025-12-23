# Image Upload Workflow Documentation

## Overview

This document explains the complete image upload workflow from device selection to platform publishing.

## Architecture

The image upload system follows a **three-stage workflow**:

1. **Device Upload to Supabase** (Immediate)
2. **Save as Draft or Post** (Uses existing Supabase images)
3. **Publish to Marketplace Platform** (Transfer from Supabase to platform)

---

## Stage 1: Device Image Upload to Supabase

### User Flow
1. User opens Create Listing page
2. User clicks "Take Photo" or "Upload Files"
3. Device file picker opens
4. User selects image(s) from camera or gallery
5. Images upload to Supabase Storage **immediately**

### Technical Implementation

#### Frontend (templates/create.html)

**HTML Input Elements:**
```html
<!-- Camera capture -->
<input type="file" id="cameraInput" accept="image/*" capture="environment">

<!-- Gallery upload -->
<input type="file" id="photoInput" accept="image/*" multiple>
```

**JavaScript Handler:**
```javascript
async function handlePhotoSelect(e) {
    // 1. Get selected files
    const files = e.target.files;

    // 2. Create FormData with listing_id
    const formData = new FormData();
    formData.append('listing_id', currentListingId);
    for (let file of files) {
        formData.append('photos', file);
    }

    // 3. Upload to backend
    const response = await fetch('/api/upload-photos', {
        method: 'POST',
        body: formData
    });

    // 4. Update UI with database-backed photo list
    const data = await response.json();
    uploadedPhotos = data.all_photos;  // Database is source of truth
    refreshPhotoPreviews();
}
```

#### Backend (routes_main.py:561-697)

**Endpoint:** `POST /api/upload-photos`

**Process:**
1. Validate user authentication
2. Verify listing exists and belongs to user
3. Upload each file to Supabase Storage
   - Bucket: `listing-images`
   - Path: `{user_id}/{listing_uuid}/{timestamp}_{filename}`
4. Update listing record in database with photo URLs
5. Return both new URLs and complete photo list

**Storage Integration (src/storage/supabase_storage.py):**
```python
def upload_to_supabase_storage(
    file_data: bytes,
    filename: str,
    user_id: str,
    listing_uuid: str,
    bucket_name: str = "listing-images"
) -> Tuple[bool, str]:
    # Upload to Supabase Storage
    # Returns (success, public_url)
```

### Key Features
- ✅ Images upload **before** listing is saved
- ✅ Images attached to listing_id immediately
- ✅ Database is source of truth for photo list
- ✅ Mobile camera access via `capture="environment"`
- ✅ Multiple file selection via `multiple` attribute
- ✅ Secure storage namespaced by user_id

---

## Stage 2: Save as Draft or Post

### User Flow
1. User fills out listing details (title, price, etc.)
2. User clicks "Save as Draft" or "Post Now"
3. Listing saves with existing Supabase image URLs

### Technical Implementation

#### Frontend (templates/create.html:1672-1718)

```javascript
async function saveListing(status = 'draft') {
    const formData = collectFormData();
    formData.photos = uploadedPhotos;  // Already in Supabase
    formData.status = status;

    const response = await fetch('/api/save-draft', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    });
}
```

#### Backend (routes_main.py:832-900)

**Endpoint:** `POST /api/save-draft`

**Process:**
1. Verify listing exists and belongs to user
2. Update listing fields (title, price, description, etc.)
3. Photos already in database from upload step
4. Set status to 'draft' or 'active'

### Key Features
- ✅ Photos persist in Supabase Storage
- ✅ No re-upload needed when saving
- ✅ Draft status doesn't affect images
- ✅ Images remain accessible via public URLs

---

## Stage 3: Publish to Marketplace Platform

### User Flow
1. User has a listing with photos in Supabase
2. User clicks "Publish to eBay/Mercari/etc."
3. System transfers images to marketplace platform
4. Listing created on platform with platform-hosted images

### Technical Implementation

#### API Endpoint (routes_main.py:2565-2589)

**Endpoint:** `POST /api/listing/<listing_id>/publish-to-platform`

```python
@main_bp.route("/api/listing/<int:listing_id>/publish-to-platform", methods=["POST"])
@login_required
def publish_to_platform(listing_id):
    platform = request.get_json().get('platform')

    # Use ListingManager to handle image transfer
    from src.listing_manager import ListingManager
    manager = ListingManager()
    result = manager.publish_to_platform(listing_id, platform)

    return jsonify(result)
```

#### Listing Manager (src/listing_manager/listing_manager.py:167-369)

**Method:** `publish_to_platform(listing_id, platform)`

**Process:**
1. Fetch listing from database
2. Convert to UnifiedListing format
3. Get platform adapter (eBay, Mercari, etc.)
4. Call adapter's `publish_listing()` method
5. Track platform listing in database

#### Platform Adapter (src/adapters/ebay_adapter.py:257-320)

**Method:** `publish_listing(listing)`

**Image Transfer Process:**
1. Extract Supabase image URLs from listing
2. Download images from Supabase (via ImageTransferHelper)
3. Resize images if needed (per platform limits)
4. Upload images to platform's image service
5. Create listing with platform-hosted image URLs

#### Image Transfer Helper (src/adapters/image_transfer.py)

**Method:** `prepare_images_for_platform(image_urls, platform_name)`

**Process:**
1. Download images from Supabase URLs
2. Apply platform-specific limits:
   - eBay: 1600x1600px max, 12MB, 24 images
   - Mercari: 2048x2048px max, 10MB, 12 images
   - Poshmark: 2048x2048px max, 10MB, 16 images
3. Resize if exceeds limits
4. Return prepared image bytes

### Example: eBay Image Upload

```python
def _upload_images_for_listing(self, image_urls: List[str]) -> List[str]:
    # 1. Download from Supabase
    prepared_images, errors = self.image_helper.prepare_images_for_platform(
        image_urls, 'ebay', limits
    )

    # 2. Upload each to eBay Picture Services
    ebay_image_urls = []
    for idx, image_bytes in enumerate(prepared_images):
        ebay_url = self._upload_image_to_ebay(image_bytes, idx)
        ebay_image_urls.append(ebay_url)

    return ebay_image_urls
```

### Key Features
- ✅ Images downloaded from Supabase on-demand
- ✅ Platform-specific resizing and optimization
- ✅ Images uploaded to platform's image service
- ✅ Platform hosts images (not Supabase)
- ✅ Error handling for failed transfers
- ✅ Detailed logging for debugging

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DEVICE UPLOAD                                            │
├─────────────────────────────────────────────────────────────┤
│ User Device                                                  │
│   ↓ (select images)                                         │
│ Browser File Picker                                         │
│   ↓ (FormData with files)                                   │
│ POST /api/upload-photos                                     │
│   ↓ (upload to Supabase)                                    │
│ Supabase Storage Bucket: listing-images                     │
│   Path: {user_id}/{listing_uuid}/{filename}                 │
│   ↓ (update database)                                       │
│ Database: listings.photos = [public URLs]                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. SAVE DRAFT/POST                                          │
├─────────────────────────────────────────────────────────────┤
│ POST /api/save-draft                                        │
│   ↓ (update listing)                                        │
│ Database: listings.photos = [Supabase URLs]                 │
│ Database: listings.status = 'draft' or 'active'             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. PUBLISH TO PLATFORM                                      │
├─────────────────────────────────────────────────────────────┤
│ POST /api/listing/<id>/publish-to-platform                  │
│   ↓                                                          │
│ ListingManager.publish_to_platform()                        │
│   ↓                                                          │
│ PlatformAdapter.publish_listing()                           │
│   ↓ (download from Supabase)                                │
│ ImageTransferHelper.prepare_images_for_platform()           │
│   ↓ (resize if needed)                                      │
│ PlatformAdapter._upload_images_for_listing()                │
│   ↓ (upload to platform)                                    │
│ eBay Picture Services / Mercari CDN / etc.                  │
│   ↓ (create listing)                                        │
│ Platform Listing with Platform-Hosted Images                │
│   ↓ (track in database)                                     │
│ Database: platform_listings                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure in Supabase

```
listing-images/                    # Bucket name
  └── {user_id}/                   # User isolation
      └── {listing_uuid}/          # Listing organization
          ├── 20241222_120000_photo1.jpg
          ├── 20241222_120001_photo2.jpg
          └── 20241222_120002_photo3.jpg
```

**Benefits:**
- User isolation (security)
- Listing organization (cleanup)
- Timestamp prevents filename collisions
- Public URLs for easy access

---

## Platform-Specific Image Limits

| Platform  | Max Size | Max Dimensions | Max Images |
|-----------|----------|----------------|------------|
| eBay      | 12 MB    | 1600x1600      | 24         |
| Mercari   | 10 MB    | 2048x2048      | 12         |
| Poshmark  | 10 MB    | 2048x2048      | 16         |
| Etsy      | 10 MB    | 3000x3000      | 10         |
| Facebook  | 8 MB     | 2048x2048      | 30         |

**Implementation:** `src/adapters/image_transfer.py:PLATFORM_IMAGE_LIMITS`

---

## Security Considerations

### Authentication
- ✅ User must be logged in to upload images
- ✅ Listing ownership verified before upload
- ✅ User can only upload to their own listings

### Storage
- ✅ Files namespaced by user_id (isolation)
- ✅ Secure filenames (sanitized, timestamped)
- ✅ Public read access only (no anonymous writes)

### Validation
- ✅ File type validation (image/* only)
- ✅ File size limits enforced
- ✅ Platform-specific limits applied

---

## Error Handling

### Upload Errors
- Network failures → Retry prompt
- Invalid file type → User warning
- Upload quota exceeded → Clear error message

### Transfer Errors
- Supabase download fails → Detailed logging
- Platform upload fails → Continue with successful images
- No images uploaded → Fail gracefully with explanation

---

## Setup Requirements

### Environment Variables

```bash
# Supabase (Required for Stage 1 & 2)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Platform Credentials (Required for Stage 3)
EBAY_CLIENT_ID=your_client_id
EBAY_CLIENT_SECRET=your_client_secret
EBAY_REFRESH_TOKEN=your_refresh_token

MERCARI_API_KEY=your_api_key
# ... (other platforms)
```

### Supabase Bucket Setup

1. Create bucket `listing-images`
2. Set to **Public**
3. Add RLS policies (see SUPABASE_SETUP.md)

---

## Testing the Workflow

### Test Stage 1: Device Upload
```bash
# Navigate to /create
# Click "Upload Files"
# Select image(s)
# Check browser console for "[UPLOAD]" logs
# Verify image appears in preview
```

### Test Stage 2: Save Draft
```bash
# Fill out listing details
# Click "Save as Draft"
# Navigate to /drafts
# Verify images display correctly
```

### Test Stage 3: Platform Publish
```bash
# Open draft listing
# Click "Publish to eBay"
# Check server logs for "[EBAY]" logs
# Verify images transfer and listing creates
```

---

## Troubleshooting

### Images don't upload
1. Check SUPABASE_URL and SUPABASE_ANON_KEY
2. Verify bucket exists and is public
3. Check browser console for errors
4. Check server logs for detailed error messages

### Images don't transfer to platform
1. Verify platform credentials (EBAY_CLIENT_ID, etc.)
2. Check server logs for "[IMAGE_TRANSFER]" errors
3. Verify Supabase URLs are publicly accessible
4. Check platform API rate limits

### Images too large
1. Images auto-resize per platform limits
2. Check original image size
3. Verify platform limits in PLATFORM_IMAGE_LIMITS

---

## Future Enhancements

- [ ] Add client-side image compression before upload
- [ ] Implement image caching for faster transfers
- [ ] Add bulk image operations
- [ ] Support video uploads
- [ ] Add image editing tools (crop, rotate, filters)
- [ ] Implement progressive image loading
- [ ] Add watermarking options
- [ ] Support image reordering

---

## Related Documentation

- **SUPABASE_SETUP.md** - Supabase Storage configuration
- **AI_SETUP.md** - AI image analysis setup
- **PLATFORMS_README.md** - Platform integration details

---

## Support

For issues or questions:
1. Check browser console (F12)
2. Check server logs
3. Review this documentation
4. Open GitHub issue with logs
