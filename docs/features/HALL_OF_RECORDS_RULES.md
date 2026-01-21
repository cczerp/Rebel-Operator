# Hall of Records - Non-Negotiable Requirements

**Last Updated:** 2026-01-19
**Status:** MANDATORY - All implementations must follow these rules exactly.

---

## 🔒 Core Principle

**The scanner is the ONLY determining factor for what enters Hall of Records.**

No exceptions. No manual submissions. No user control. No admin discretion on entries.

---

## ✅ NON-NEGOTIABLE RULES

### Rule #1: Automatic Entry Creation ONLY
- ✅ Hall of Records entries are created **AUTOMATICALLY** when scanner detects NEW collectible
- ✅ Detection happens during `/api/analyze` or `/api/enhanced-scan` endpoints
- ✅ Check: `if is_new_collectible(franchise, item_name):` then auto-create
- ❌ **NO manual "Add to Hall" button or form**
- ❌ **NO user submission endpoint** (e.g., `/api/hall/submit-entry`)
- ❌ **NO admin ability to manually create entries**
- ❌ **NO bypass or override mechanism**

**Enforcement:** Any code allowing manual entry creation will be rejected.

---

### Rule #2: Scanner Determines "New" Status
- ✅ Scanner checks database: Does `hall_of_records` already contain this `(franchise, item_name)` pair?
- ✅ If NO → Create entry automatically
- ✅ If YES → Skip (entry already exists)
- ❌ **NO user/admin input on "is this new?"**
- ❌ **NO prompts like "Add to Hall of Records?"**

**Enforcement:** The scanner decides. Period.

---

### Rule #3: Admin Control is Photo Approval ONLY
- ✅ Admin can **approve** pending photos (move to hall-of-records bucket)
- ✅ Admin can **deny** pending photos (delete from draft-images bucket)
- ❌ **Admin CANNOT create Hall of Records entries**
- ❌ **Admin CANNOT delete Hall of Records entries** (they persist even without photos)
- ❌ **Admin CANNOT edit entry data** (franchise, item_name, category, description)

**Enforcement:** Admin endpoints are restricted to photo operations only.

---

### Rule #4: Entries Persist, Photos Don't
- ✅ Hall of Records entries remain in database permanently
- ✅ Entries persist even if ALL photos are denied
- ✅ Entry data (franchise, item, category, description) is historical record
- ❌ **Deleting photos DOES NOT delete the entry**
- ❌ **Entries are NEVER auto-deleted**

**Why:** Info is valuable even without images. Someone scanned it, so it exists in the wild.

---

### Rule #5: Draft-Images Bucket is Staging for Photos
- ✅ When scanner detects NEW collectible, images are saved to **draft-images** bucket
- ✅ Images are tracked in `pending_hall_images` table with status='pending'
- ✅ Admin reviews and approves/denies
- ✅ Approved photos move to **hall-of-records** bucket
- ✅ Denied photos are deleted from **draft-images** bucket
- ❌ **Photos DO NOT go directly to hall-of-records bucket**
- ❌ **NO bypassing the approval flow**

**Enforcement:** All Hall photos must pass through pending review.

---

## 🔄 MANDATORY WORKFLOW

### Step 1: Scanner Detects Collectible
```python
# Inside /api/analyze or /api/enhanced-scan
scan_result = scanner.analyze(images)

franchise = scan_result.get('franchise')  # e.g., "Pokemon"
item_name = scan_result.get('item_name')  # e.g., "Charizard 1999"
category = scan_result.get('category')    # e.g., "Trading Cards"
```

### Step 2: Check if NEW (Automatic)
```python
# Check database
exists = db.hall_of_records_exists(franchise, item_name)

if not exists:  # NEW collectible detected
    # Proceed to Step 3
else:
    # Skip - already in Hall of Records
```

### Step 3: Auto-Create Entry (Automatic)
```python
# AUTOMATICALLY create hall_of_records entry
hall_entry = db.create_hall_of_records_entry(
    franchise=franchise,
    item_name=item_name,
    category=category,
    description=scan_result.get('description', ''),
    created_by=current_user.id if current_user else None,
    is_verified=False  # Admin can verify later if needed
)
```

### Step 4: Auto-Save Images to Draft-Images (Automatic)
```python
# Images are already in draft-images from scan
# Create pending_hall_images entries for admin review

for image_url in scan_result.get('image_urls', []):
    db.create_pending_hall_image(
        hall_record_id=hall_entry.id,
        image_url=image_url,  # URL in draft-images bucket
        uploaded_by=current_user.id if current_user else None,
        status='pending'
    )
```

### Step 5: Notify Admins (Automatic)
```python
# Notify admins that new Hall entry needs photo review
notification.send_to_admins(
    f"New Hall of Records entry: {franchise} - {item_name}",
    f"Pending photo review: {len(image_urls)} photo(s)"
)
```

### Step 6: Admin Reviews Photos (Manual - ONLY Admin Action)
**Admin navigates to:** `/admin/hall-of-records/pending-photos`

**Admin sees:**
- List of pending photos
- Associated Hall of Records entry (franchise, item, category)
- Approve or Deny buttons

**Admin clicks "Approve":**
```python
# Backend: /api/hall/approve-image/<int:image_id>

storage = get_supabase_storage()
pending = db.get_pending_hall_image(image_id)

# Move from draft-images to hall-of-records bucket
success, new_url = storage.move_to_hall_of_records(pending.image_url)

if success:
    # Add to hall_of_records.approved_image_urls[]
    db.add_approved_image_to_hall(pending.hall_record_id, new_url)

    # Update pending_hall_images
    db.update_pending_hall_image(
        image_id,
        status='approved',
        reviewed_by=current_user.id,
        reviewed_at=datetime.now()
    )
```

**Admin clicks "Deny":**
```python
# Backend: /api/hall/deny-image/<int:image_id>

storage = get_supabase_storage()
pending = db.get_pending_hall_image(image_id)

# Delete from draft-images bucket
storage.delete_photo(pending.image_url)

# Update pending_hall_images
db.update_pending_hall_image(
    image_id,
    status='denied',
    reviewed_by=current_user.id,
    reviewed_at=datetime.now()
)

# Hall of Records entry REMAINS (info is still valuable)
```

---

## 🚫 FORBIDDEN OPERATIONS

### These Operations Must Be Blocked

1. **Manual Entry Creation**
   - ❌ No forms for users to submit Hall entries
   - ❌ No admin panel for creating entries
   - ❌ No API endpoint accepting manual entry data

2. **Manual Photo Submission Without Scan**
   - ❌ No uploading photos directly to Hall
   - ❌ Photos must come from scanner results

3. **Entry Deletion**
   - ❌ No delete button for Hall entries
   - ❌ No admin ability to remove entries
   - ❌ Entries are permanent historical records

4. **Entry Editing**
   - ❌ No editing franchise, item_name, category, description
   - ❌ If data is wrong, it reflects what the scanner detected (historical accuracy)
   - ⚠️ Exception: Admin can mark entry as `is_verified=true` after manual verification (optional)

5. **Bypassing Photo Approval**
   - ❌ No direct upload to hall-of-records bucket
   - ❌ All photos must go through pending review
   - ❌ No "auto-approve" or "skip review" option

---

## 📊 DATABASE SCHEMA (MANDATORY)

### hall_of_records Table
```sql
CREATE TABLE hall_of_records (
    id SERIAL PRIMARY KEY,
    franchise VARCHAR(255) NOT NULL,          -- Auto from scanner
    item_name VARCHAR(255),                   -- Auto from scanner
    category VARCHAR(100),                    -- Auto from scanner
    description TEXT,                         -- Auto from scanner
    approved_image_urls TEXT[],               -- Approved photos only
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),  -- Who scanned it
    is_verified BOOLEAN DEFAULT FALSE,        -- Admin can verify (optional)

    -- Ensure uniqueness: one entry per (franchise, item_name) pair
    UNIQUE(franchise, item_name)
);
```

### pending_hall_images Table
```sql
CREATE TABLE pending_hall_images (
    id SERIAL PRIMARY KEY,
    hall_record_id INTEGER NOT NULL REFERENCES hall_of_records(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,                  -- URL in draft-images bucket
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',     -- 'pending', 'approved', 'denied'
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    admin_notes TEXT                          -- Optional notes from admin
);
```

**Critical Indexes:**
```sql
CREATE INDEX idx_hall_franchise_item ON hall_of_records(franchise, item_name);
CREATE INDEX idx_pending_hall_status ON pending_hall_images(status);
CREATE INDEX idx_pending_hall_record ON pending_hall_images(hall_record_id);
```

---

## 🗂️ BUCKET USAGE (MANDATORY)

### draft-images Bucket
**Purpose:** Staging area for pending Hall of Records photos

**Contains:**
1. Saved draft listings (user drafts)
2. **Pending Hall of Records photos** (awaiting admin approval)

**Photo Lifecycle:**
```
Scanner saves image → draft-images bucket
                   → pending_hall_images table (status='pending')
                   → Admin reviews
                   → If approved: move to hall-of-records bucket
                   → If denied: delete from draft-images bucket
```

### hall-of-records Bucket
**Purpose:** Public, approved collectibles database images

**Contains:** ONLY admin-approved photos

**Properties:**
- Public: YES (everyone can view)
- RLS: NO (public access)
- Auto-delete: NEVER (permanent archive)

**Photo Naming Convention:**
```
{franchise}-{item-name}-{uuid}.jpg

Examples:
pokemon-charizard-1999-abc123def456.jpg
magic-black-lotus-alpha-789ghi012jkl.png
```

---

## 🔐 API ENDPOINTS (MANDATORY)

### Allowed Endpoints

#### 1. Auto-Create Entry (Built into scanner)
**Location:** Inside `/api/analyze` or `/api/enhanced-scan`

**NOT a separate endpoint** - integrated into analysis flow.

```python
@main_bp.route("/api/analyze", methods=["POST"])
def api_analyze():
    # ... scan images ...

    # AUTO-CREATE HALL ENTRY IF NEW
    if scan_result.get('is_collectible'):
        _auto_create_hall_entry_if_new(scan_result, current_user)

    # ... return scan results ...
```

#### 2. Admin Approve Photo
```python
@main_bp.route("/api/hall/approve-image/<int:image_id>", methods=["POST"])
@admin_required
def approve_hall_image(image_id):
    """Admin approves pending Hall photo."""
    # Move from draft-images to hall-of-records bucket
    # Update status to 'approved'
```

#### 3. Admin Deny Photo
```python
@main_bp.route("/api/hall/deny-image/<int:image_id>", methods=["POST"])
@admin_required
def deny_hall_image(image_id):
    """Admin denies pending Hall photo."""
    # Delete from draft-images bucket
    # Update status to 'denied'
```

#### 4. List Pending Photos (Admin Only)
```python
@main_bp.route("/api/hall/pending-photos", methods=["GET"])
@admin_required
def list_pending_hall_photos():
    """Get all pending Hall photos for review."""
    # Return list of pending_hall_images with status='pending'
```

#### 5. View Hall of Records (Public)
```python
@main_bp.route("/api/hall/entries", methods=["GET"])
def list_hall_entries():
    """Public endpoint: view all Hall of Records entries."""
    # Return hall_of_records with approved_image_urls
```

### Forbidden Endpoints

❌ `/api/hall/create-entry` - FORBIDDEN (auto-created by scanner)
❌ `/api/hall/submit-entry` - FORBIDDEN (no manual submission)
❌ `/api/hall/delete-entry/<id>` - FORBIDDEN (entries are permanent)
❌ `/api/hall/edit-entry/<id>` - FORBIDDEN (historical accuracy)
❌ `/api/hall/upload-photo` - FORBIDDEN (photos come from scans)

---

## ✅ COMPLIANCE CHECKLIST

Before deploying Hall of Records functionality, verify:

- [ ] Scanner auto-creates entries when detecting NEW collectibles
- [ ] No manual "Add to Hall" buttons anywhere in UI
- [ ] No API endpoints for manual entry creation
- [ ] Admin panel ONLY shows pending photo approval (not entry management)
- [ ] Photos go to draft-images first (not hall-of-records directly)
- [ ] `hall_of_records` table has UNIQUE constraint on (franchise, item_name)
- [ ] `pending_hall_images` table exists with proper foreign keys
- [ ] Admin approve endpoint moves photos from draft-images to hall-of-records
- [ ] Admin deny endpoint deletes photos from draft-images
- [ ] Hall entries persist even if all photos are denied
- [ ] Public view shows only entries with approved photos (optional: show all)
- [ ] Notification system alerts admins of new pending photos

---

## 🚨 VIOLATION CONSEQUENCES

Any implementation violating these rules will:

1. **Compromise data integrity** - Manual entries pollute the historical database
2. **Defeat the purpose** - Hall is meant to be automatic discovery, not manual curation
3. **Create maintenance burden** - Manual entries require fact-checking and cleanup
4. **Be rejected in code review** - All PRs must follow these rules

---

## 📝 SUMMARY

| Aspect | Rule |
|--------|------|
| **Entry Creation** | Automatic ONLY (scanner detects NEW) |
| **User Control** | NONE |
| **Admin Control** | Photo approval/denial ONLY |
| **Entry Deletion** | NEVER (permanent historical records) |
| **Photo Approval** | Required (draft-images → admin review → hall-of-records) |
| **Bypass Mechanisms** | NONE |
| **Manual Submission** | FORBIDDEN |

---

## 🎯 THE GOAL

**Hall of Records is a self-building, crowdsourced collectibles database.**

- Users scan items naturally (to create listings)
- Scanner auto-detects new collectibles and catalogs them
- Database grows organically without manual data entry
- Admins ensure photo quality (not data accuracy)
- Result: Comprehensive, historically accurate collectibles reference

**This ONLY works if the scanner is the sole authority on what gets added.**

---

**Last Updated:** 2026-01-19
**Next Review:** When implementing Hall of Records feature
**Questions?** Refer to `/BUCKET_ARCHITECTURE.md` for technical details.

---

**END OF NON-NEGOTIABLE REQUIREMENTS**
