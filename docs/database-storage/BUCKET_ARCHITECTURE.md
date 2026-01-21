# Supabase Storage Bucket Architecture

This document describes the complete bucket architecture for Rebel Operator's image storage system.

## Bucket Overview

```
┌─────────────────────┬──────────────┬────────────────┬─────────────────────────────────────┐
│ Bucket              │ Privacy      │ RLS            │ Purpose                             │
├─────────────────────┼──────────────┼────────────────┼─────────────────────────────────────┤
│ temp-photos         │ PUBLIC       │ None           │ Temporary uploads during scanning   │
│ draft-images        │ PUBLIC*      │ None           │ Saved drafts + Hall pending images  │
│ listing-images      │ PUBLIC       │ None           │ Active public listings (for sale)   │
│ vault               │ PRIVATE      │ Per-user RLS   │ Personal collection (not for sale)  │
│ hall-of-records     │ PUBLIC       │ None           │ Collectibles database (approved)    │
└─────────────────────┴──────────────┴────────────────┴─────────────────────────────────────┘

* Set to PUBLIC for building/testing. Can be PRIVATE in production with appropriate RLS policies.
```

## Bucket Details

### 1. temp-photos (Temporary Uploads)
**Environment Variable:** `SUPABASE_BUCKET_TEMP` (default: `temp-photos`)

- **Purpose:** Temporary storage during photo upload and analysis
- **Lifecycle:** Images are deleted after page refresh or navigation
- **Privacy:** PUBLIC (for easy access during analysis)
- **File Size Limit:** 20 MB
- **Used By:**
  - Photo uploader component
  - Quick analysis endpoint
  - Guest users (no login required)

**Cleanup Strategy:**
- Implement auto-delete after 24 hours (optional)
- Delete on page navigation
- Periodic cleanup job (optional)

---

### 2. draft-images (Saved Drafts + Hall Pending)
**Environment Variable:** `SUPABASE_BUCKET_DRAFTS` (default: `draft-images`)

- **Purpose:**
  1. Saved draft listings (can be edited/deleted by user)
  2. **Pending Hall of Records images** awaiting admin approval
- **Lifecycle:** Persistent until user deletes or listing is posted
- **Privacy:** PUBLIC (for building), can be PRIVATE with RLS in production
- **File Size Limit:** Unlimited (4.88 GB default)
- **Used By:**
  - Draft management system
  - **Hall of Records pending images (stored in separate table)**
  - Enhanced scan endpoint

**Hall of Records Integration:**
When a new collectible item/franchise is scanned:
1. **Info** → Goes to `hall_of_records` table (automatic)
2. **Images** → Go to `draft-images` bucket (in `pending_hall_images` table)
3. **Admin reviews** → Approves or denies images
4. **If approved** → Moves to `hall-of-records` bucket
5. **If denied** → Deleted from `draft-images`

---

### 3. listing-images (Active Listings)
**Environment Variable:** `SUPABASE_BUCKET_LISTINGS` (default: `listing-images`)

- **Purpose:** Public images for active marketplace listings
- **Lifecycle:** Persistent while listing is active
- **Privacy:** PUBLIC (must be accessible to buyers)
- **File Size Limit:** Unlimited (4.88 GB default)
- **Used By:**
  - Posted listings
  - Public marketplace views
  - Sharing/embedding

**Deletion Strategy:**
- Optional: Keep after sale (for history)
- Optional: Move to archive bucket
- Optional: Delete after 90 days post-sale

---

### 4. vault (Personal Collection)
**Environment Variable:** `SUPABASE_BUCKET_VAULT` (default: `vault`)

- **Purpose:** User's private digital inventory/collection
- **Lifecycle:** Persistent (user controls deletion)
- **Privacy:** PRIVATE with RLS (each user can only see their own)
- **File Size Limit:** Unlimited (4.88 GB default)
- **Used By:**
  - Personal collection tracking
  - Digital inventory management
  - Items not for sale

**File Organization:**
```
vault/
├── {user_id_1}/
│   ├── abc123.jpg
│   ├── def456.png
│   └── ...
├── {user_id_2}/
│   ├── ghi789.jpg
│   └── ...
└── ...
```

**RLS Policies:**
- Users can only read/write files in `vault/{their_user_id}/`
- Admins can read all vault files (optional)
- See: `supabase_vault_rls_policies.sql`

**Usage Example:**
```python
from src.storage.supabase_storage import get_supabase_storage

storage = get_supabase_storage()
success, url = storage.upload_to_vault(
    file_data=image_bytes,
    user_id=current_user.id,
    filename="pokemon-charizard-1999.jpg"
)
```

---

### 5. hall-of-records (Collectibles Database)
**Environment Variable:** `SUPABASE_BUCKET_HALL` (default: `hall-of-records`)

- **Purpose:** Public collectibles database/wiki with approved images
- **Lifecycle:** Permanent (curated content)
- **Privacy:** PUBLIC (everyone can view)
- **File Size Limit:** Unlimited (4.88 GB default)
- **Used By:**
  - Hall of Records page
  - Collectibles information database
  - Franchise/item reference images

**Content:**
- NOT a leaderboard or sales tracker
- Information about collectible franchises and items
- Reference images, logos, examples
- **Automatic:** Entries created automatically when scanner detects new collectible
- **No manual control:** Users/admins cannot manually add entries
- **Admin control:** Only photo approval/denial

**Automatic Workflow:**
```
Scanner detects NEW collectible item/franchise
         ↓
✅ AUTOMATICALLY create hall_of_records entry
   (franchise, item_name, category, description)
         ↓
✅ AUTOMATICALLY save images to draft-images bucket
   (stored in pending_hall_images table)
         ↓
Admin reviews pending images
         ↓
    ┌────┴────┐
    ↓         ↓
Approved   Denied
    ↓         ↓
Move to    Delete from
hall-of-   draft-images
records    (image removed,
bucket     but hall entry
(image     remains)
approved)
```

**Key Points:**
- ✅ Hall of Records entry creation is **100% automatic** (triggered by scanner)
- ✅ NO "Add to Hall of Records" button or manual submission
- ✅ Scanner determines what's new and creates entries automatically
- ⚠️ Admin ONLY approves/denies **photos** (not entries)
- ⚠️ Hall entries persist even if photos are denied (info is still valuable)

**Admin Photo Approval Function:**
```python
from src.storage.supabase_storage import get_supabase_storage

# Admin approves a pending photo (ONLY admin action needed)
storage = get_supabase_storage()
success, new_url = storage.move_to_hall_of_records(
    source_url="https://...supabase.co/.../draft-images/pending123.jpg",
    new_filename="pokemon-franchise-logo.jpg"  # optional
)

if success:
    # Update hall_of_records table to add new_url to approved_image_urls[]
    # Update pending_hall_images: status='approved', reviewed_by, reviewed_at
    # Photo is now public in hall-of-records bucket
```

**Important Notes:**
- This function is ONLY for admin photo approval
- Hall of Records entries are created automatically by the scanner
- No user/admin action needed to create entries - scanner handles it all

---

## Image Flow Diagram

### Upload Flow
```
┌─────────────────┐
│ User Uploads    │
│ Photo           │
└────────┬────────┘
         ↓
┌─────────────────┐
│  temp-photos    │ (Temporary)
└────────┬────────┘
         │
         ├─→ Quick Analysis → Deleted after use
         │
         └─→ Save Draft
                ↓
         ┌─────────────────┐
         │  draft-images   │ (Saved)
         └────────┬────────┘
                  │
                  ├─→ Post Listing
                  │         ↓
                  │  ┌─────────────────┐
                  │  │ listing-images  │ (Public)
                  │  └─────────────────┘
                  │
                  └─→ Add to Vault
                            ↓
                     ┌─────────────────┐
                     │     vault       │ (Private)
                     └─────────────────┘
```

### Hall of Records Flow (Automatic)
```
┌──────────────────────────────────┐
│ User Scans Collectible Item     │
│ (via /api/analyze endpoint)      │
└────────┬─────────────────────────┘
         ↓
    Scanner analyzes
         ↓
  ┌──────────────────┐
  │ Is this NEW?     │
  │ (franchise/item  │
  │ not in hall yet?)│
  └───┬──────────┬───┘
      │          │
     NO         YES ← ✅ AUTOMATIC TRIGGER
      │          │
      ↓          ↓
   Skip    ┌─────────────────────────┐
           │ 1. Auto-create entry in │
           │    hall_of_records DB   │
           │    (franchise, item,    │
           │     category, etc.)     │
           └──────────┬──────────────┘
                      ↓
           ┌─────────────────────────┐
           │ 2. Auto-save images to  │
           │    draft-images bucket  │
           │    (pending_hall_images │
           │     table)              │
           └──────────┬──────────────┘
                      ↓
           ┌─────────────────────────┐
           │ 3. Notify admins:       │
           │    "New Hall entry      │
           │     needs photo review" │
           └──────────┬──────────────┘
                      ↓
              ┌─────────────┐
              │Admin Reviews│
              │   Photos    │
              └──────┬──────┘
                     │
           ┌─────────┴─────────┐
           ↓                   ↓
      Approved              Denied
           ↓                   ↓
┌──────────────────┐   ┌──────────────────┐
│ Move image to    │   │ Delete image     │
│ hall-of-records  │   │ from draft-      │
│ bucket (public)  │   │ images           │
└──────────────────┘   └──────────────────┘
           │                   │
           ↓                   ↓
    Add URL to          Update status to
    approved_image_     'denied' in
    urls[] in DB        pending table
           │                   │
           └───────┬───────────┘
                   ↓
         Hall entry persists
         (with or without photos)
```

**Key Difference:** Hall of Records creation is AUTOMATIC during scan.
No user or admin action is needed to create entries - only to approve photos.

---

## Database Tables

### Existing Tables
- `listings` → References `listing-images` bucket
- `drafts` → References `draft-images` bucket

### New Tables Needed

#### pending_hall_images
Stores Hall of Records images awaiting admin approval.

```sql
CREATE TABLE pending_hall_images (
    id SERIAL PRIMARY KEY,
    hall_record_id INTEGER REFERENCES hall_of_records(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,  -- URL in draft-images bucket
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, denied
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    admin_notes TEXT
);
```

#### hall_of_records
Stores collectibles database information.

```sql
CREATE TABLE hall_of_records (
    id SERIAL PRIMARY KEY,
    franchise VARCHAR(255) NOT NULL,  -- Pokemon, Magic the Gathering, etc.
    item_name VARCHAR(255),  -- Charizard, Black Lotus, etc.
    category VARCHAR(100),  -- Trading Cards, Sports Cards, Video Games, etc.
    description TEXT,
    approved_image_urls TEXT[],  -- Array of URLs in hall-of-records bucket
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    is_verified BOOLEAN DEFAULT FALSE  -- Admin verified
);
```

---

## API Endpoints

### Existing
- `POST /api/upload-temp` → Uploads to temp-photos
- `POST /api/save-draft` → Moves to draft-images
- `POST /api/post-listing` → Moves to listing-images

### New Endpoints Needed

#### Hall of Records

**IMPORTANT:** Hall of Records entries are created AUTOMATICALLY during scan.
There is NO manual submission endpoint. The scanner handles everything.

**Automatic Process (in scanner/analysis endpoint):**
```python
# Inside /api/analyze or /api/enhanced-scan endpoint:
# After successful scan, check if collectible is new:

if is_new_collectible(franchise, item_name):
    # 1. AUTOMATICALLY create hall_of_records entry
    hall_entry = db.create_hall_of_records_entry(
        franchise=franchise,
        item_name=item_name,
        category=category,
        description=description,
        created_by=current_user.id if current_user else None
    )

    # 2. AUTOMATICALLY save images to draft-images bucket
    for image_url in scanned_images:
        db.create_pending_hall_image(
            hall_record_id=hall_entry.id,
            image_url=image_url,  # Already in draft-images from scan
            uploaded_by=current_user.id if current_user else None
        )

    # No user action required - it's all automatic!
```

**Admin Endpoints (ONLY for photo approval):**

```python
@main_bp.route("/api/hall/approve-image/<int:image_id>", methods=["POST"])
@admin_required
def approve_hall_image(image_id):
    """
    Admin approves a pending Hall of Records image.
    Moves from draft-images to hall-of-records bucket.
    This is the ONLY admin action needed - entries are auto-created by scanner.
    """
    storage = get_supabase_storage()

    # Get pending image
    pending = db.get_pending_hall_image(image_id)

    # Move to hall-of-records bucket
    success, new_url = storage.move_to_hall_of_records(pending.image_url)

    if success:
        # Add new_url to hall_of_records.approved_image_urls[]
        db.add_approved_image_to_hall(pending.hall_record_id, new_url)
        # Update pending_hall_images: status='approved'
        db.update_pending_hall_image(image_id, status='approved', reviewed_by=current_user.id)
        # Return success
        return jsonify({"success": True, "url": new_url})

@main_bp.route("/api/hall/deny-image/<int:image_id>", methods=["POST"])
@admin_required
def deny_hall_image(image_id):
    """
    Admin denies a pending Hall of Records image.
    Deletes from draft-images bucket.
    """
    # Delete from draft-images
    # Update pending_hall_images status
    # Return success
```

#### Vault
```python
@main_bp.route("/api/vault/upload", methods=["POST"])
@login_required
def upload_to_vault():
    """
    Upload image to user's personal vault.
    Organized by user_id in vault bucket.
    """
    storage = get_supabase_storage()

    success, url = storage.upload_to_vault(
        file_data=request.files['image'].read(),
        user_id=current_user.id
    )

    # Save to vault_items table (if needed)
    # Return URL
```

---

## Setup Instructions

### 1. Create Buckets in Supabase Dashboard

Go to: https://app.supabase.com → Your Project → Storage

Create these buckets:

| Bucket Name      | Public | File Size Limit | Allowed MIME Types |
|------------------|--------|-----------------|-------------------|
| temp-photos      | ON     | 20 MB          | image/*           |
| draft-images     | ON*    | Unlimited      | image/*           |
| listing-images   | ON     | Unlimited      | image/*           |
| vault            | OFF    | Unlimited      | image/*           |
| hall-of-records  | ON     | Unlimited      | image/*           |

*Can be OFF in production with appropriate RLS policies

### 2. Set Environment Variables

Add to your `.env` file (optional, uses defaults if not set):

```bash
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
SUPABASE_BUCKET_VAULT=vault
SUPABASE_BUCKET_HALL=hall-of-records
```

### 3. Apply RLS Policies for Vault

Run the SQL in `supabase_vault_rls_policies.sql`:
- Go to: https://app.supabase.com → SQL Editor
- Create new query
- Paste and run the SQL
- Verify policies are active

### 4. Create Database Tables

Run SQL to create:
- `pending_hall_images` table
- `hall_of_records` table
- `vault_items` table (optional)

### 5. Deploy and Test

Test each bucket:
```bash
# Test diagnostic endpoint
curl http://localhost:5003/api/test-supabase

# Or run diagnostic script
python test_supabase_connection.py
```

---

## Security Considerations

### Public Buckets (temp, drafts, listings, hall)
- ✅ Anyone can view with URL
- ⚠️ URL guessing possible (use UUIDs for filenames)
- ✅ No authentication required for viewing
- ⚠️ Sensitive images should not use public buckets

### Private Vault Bucket
- ✅ RLS enforces per-user access
- ✅ Users can only access their own files
- ✅ Server (service_role key) can access all files
- ⚠️ Client-side code using anon key will be blocked by RLS
- ✅ Admins can optionally view all files (with policy)

### Service Role Key
- ⚠️ **NEVER expose in client-side code**
- ✅ Only use on server (backend, API endpoints)
- ✅ Bypasses all RLS policies
- ⚠️ Keep secret (don't commit to git)

---

## Cost Optimization

### Storage Costs
- Supabase Free Tier: 1 GB storage
- Pro Plan: 8 GB storage, then $0.021/GB/month

**Optimization Strategies:**
1. **Auto-delete temp-photos** after 24 hours
2. **Compress images** before upload (client-side)
3. **Delete old listings** after 90 days (optional)
4. **Limit vault** to reasonable size per user
5. **Curate hall-of-records** (don't accept everything)

### Bandwidth Costs
- Supabase Free Tier: 2 GB egress/month
- Pro Plan: 50 GB egress/month, then $0.09/GB

**Optimization Strategies:**
1. **Use CDN** for frequently accessed images
2. **Lazy loading** on image-heavy pages
3. **Thumbnails** for listings (smaller file size)
4. **Cache** hall-of-records images (they rarely change)

---

## Troubleshooting

### "Could not download image from supabase"
1. Check bucket exists and is PUBLIC (or using service_role key)
2. Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
3. Run diagnostic: `python test_supabase_connection.py`
4. Check server logs for specific error

### "Permission denied" for vault
1. Verify RLS policies are applied
2. Check user is authenticated (auth.uid() returns valid ID)
3. Verify file path: `vault/{user_id}/{filename}`
4. Server operations should use service_role key

### Images not appearing in hall-of-records
1. Check admin approved the images
2. Verify move_to_hall_of_records succeeded
3. Check hall_of_records table has correct URLs
4. Verify bucket is PUBLIC

---

## Future Enhancements

1. **Auto-cleanup job** for temp-photos (delete after 24h)
2. **Image compression** pipeline
3. **Thumbnail generation** for faster loading
4. **CDN integration** for frequently accessed images
5. **Vault storage limits** per user tier
6. **Bulk admin approval** for hall-of-records
7. **Image versioning** (keep edit history)
8. **Archive bucket** for old/sold listings

---

## Related Documentation

- `SUPABASE_DIAGNOSTIC.md` - Troubleshooting guide
- `supabase_vault_rls_policies.sql` - RLS policies for vault
- `.env.example` - Environment variables
- `PHOTO_UPLOAD_DOCUMENTATION.md` - Photo upload flow
