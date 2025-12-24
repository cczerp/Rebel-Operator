# Image Upload Flow - Non-Negotiable Requirements

**Status**: ✅ WORKING (as of current branch)  
**Last Updated**: Current implementation  
**Critical**: These requirements MUST be maintained for image uploads to function

---

## 🔴 CRITICAL: File Input Requirements (Browser File Picker)

### Non-Negotiable File Input Rules

**These rules are MANDATORY for the file picker to work. Violating any of these will cause silent failures.**

1. **MUST have a real `<input type="file">` element**
   - No exceptions. No file input = no file picker.
   - Cannot be replaced with a button alone.

2. **Button MUST trigger `.click()` on the file input**
   - The file picker only opens if the button directly triggers the input.
   - Must be: `document.getElementById("photoInput").click();`

3. **Trigger MUST be inside a direct user action**
   - The `.click()` call must happen inside an `onclick` or click event listener.
   - ✅ Allowed: `<button onclick="openPicker()">Upload</button>`
   - ❌ Blocked: `setTimeout`, `async/await`, `useEffect`, page load, background JS

4. **File input CANNOT be `display: none`** ⚠️ CRITICAL
   - This breaks functionality silently - file picker will NOT open.
   - ❌ Breaks: `input[type="file"] { display: none; }` or `class="d-none"` (Bootstrap)
   - ✅ REQUIRED: `style="opacity: 0; position: absolute; left: -9999px; width: 1px; height: 1px;"`
   - **MUST use inline styles** - CSS classes that hide elements (like Bootstrap's `d-none`) break the file picker
   - **Location**: `templates/create.html` - file input elements MUST use this exact pattern

5. **File input MUST exist in DOM at click time**
   - If conditionally rendered, the click fails.
   - ✅ Required: Render it always, hide it visually.

6. **File input MUST NOT be disabled**
   - Even temporarily. One `disabled=true` during loading = dead button.

7. **Handler function MUST exist globally** ⚠️ CRITICAL
   - If input has `onchange="handlePhotoSelect(event)"`, then `handlePhotoSelect` MUST exist in global scope
   - ❌ Fails: Function defined in closure, IIFE, or module scope
   - ✅ REQUIRED: `window.handlePhotoSelect = async function handlePhotoSelect(e) {}` 
   - **MUST be attached to window object** for inline event handlers to access it
   - Function declaration alone may not be sufficient - explicitly assign to `window` object
   - **Location**: `templates/create.html` - handler function MUST be globally accessible

8. **accept attribute MUST NOT filter everything out**
   - ❌ Over-filtered: `accept="image/jpg"`
   - ✅ Safe: `accept="image/*"`

9. **HTTPS is REQUIRED for consistent behavior**
   - File pickers behave inconsistently on HTTP.

10. **The picker NEVER shows server images**
    - File picker only shows: Local device files, Downloads, Camera roll
    - Will never show: S3 images, Database images, Previously uploaded photos
    - Those require a custom gallery UI, not the file picker.

**Canonical Working Pattern:**
```html
<input
  type="file"
  id="photoInput"
  accept="image/*"
  style="opacity: 0; position: absolute; left: -9999px; width: 1px; height: 1px;"
  onchange="handlePhotoSelect(event)"
/>

<button onclick="document.getElementById('photoInput').click();">Upload</button>

<script>
// Handler MUST be globally accessible - attach to window object
window.handlePhotoSelect = async function handlePhotoSelect(e) {
  console.log(e.target.files);
  // ... upload logic
}
</script>
```

**Key Requirements:**
- File input uses inline `style="opacity: 0; position: absolute; left: -9999px; width: 1px; height: 1px;"` (NOT `display: none` or `class="d-none"`)
- Button uses inline `onclick="document.getElementById('photoInput').click();"`
- Handler function attached to `window.handlePhotoSelect` for global access
- Inline `onchange="handlePhotoSelect(event)"` on the file input

**Location**: `templates/create.html` - Must maintain this exact structure

---

## 🔴 CRITICAL: Image Ownership Model

### Non-Negotiable Ownership Rules

**Image ownership follows a strict hierarchy that MUST be maintained:**

1. **Images are owned by: User → Listing → Image**
   - Never: Image → Listing (orphaned)
   - Never: Image → User (unattached)
   - Never: Image floating on its own

2. **Database pairing is REQUIRED (NO EXCEPTIONS)**
   - An image must be physically paired with its listing in the database.
   - The database relationship is the truth. The URL is just a pointer.

   **Structure:**
   ```
   User
    └── Listing
         ├── title
         ├── description
         ├── price
         └── images[]  ← REQUIRED ASSOCIATION
              ├── image_id
              ├── storage_path
              ├── url
              ├── order
              ├── uploaded_at
   ```

3. **URL ≠ Storage ≠ Ownership**
   - **Storage**: disk, bucket, CDN
   - **URL**: how browsers fetch it
   - **Ownership**: database relationship (lives only in database)

4. **Image upload flow (NON-NEGOTIABLE)**
   - Step 1: User uploads image → Image uploaded to storage → Temporary storage path returned
   - Step 2: Image immediately attached to `user_id` and `listing_id` (before save, not after)
   - Step 3: UI reflects database truth → Thumbnail renders from DB-backed image list, not local state alone

5. **Draft listings still own images**
   - Even if listing isn't published, user hasn't filled all fields, or AI hasn't run:
   - The listing MUST have a real `listing_id`
   - Images MUST be attached to that ID
   - No "temporary image cache" nonsense. Draft ≠ fake.

6. **Deletion rules (NON-NEGOTIABLE)**
   - Delete image → removes only that image
   - Delete listing → removes all associated images
   - Delete user → cascades listings → cascades images
   - No loose debris in storage.

7. **Acceptance test (THIS IS THE LAW)**
   - Upload image → Save listing → Refresh page → Log out → Log back in → Open listing → Images are still there
   - **If that fails, image support is not implemented, no matter what UI says.**

**Location**: Database schema and all upload/update operations must maintain this ownership model

**Related Documentation**: 
- `IMAGE_UPLOAD_WORKFLOW.md` - Complete 3-stage workflow (device upload → save draft → publish to platform)
- `docs/IMAGE_CONTRACT.MD` - **DEPRECATED** - Content merged into this file

---

## 🔴 CRITICAL: Connection Pool Configuration

### Pool Size Requirements
- **Session Mode (port 5432)**: `maxconn=3` (increased from 2)
  - **Rationale**: Must handle concurrent requests (user loader + upload + other operations)
  - **Location**: `src/database/db.py` line ~135
  - **DO NOT REDUCE BELOW 3** - Will cause "connection pool exhausted" errors

### Retry Logic Requirements
**MANDATORY**: All database operations MUST have retry logic for `psycopg2.pool.PoolError`

#### Required Retry Pattern:
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        # Database operation
        result = db.some_operation()
        break
    except psycopg2.pool.PoolError as e:
        if attempt < max_retries - 1:
            wait_time = 0.1 * (attempt + 1)  # Exponential backoff
            time.sleep(wait_time)
            continue
        else:
            # Handle final failure
            return error_response
```

#### Operations Requiring Retry Logic:
1. ✅ `current_user.is_authenticated` check (in upload route)
2. ✅ `current_user.id` access (in upload route)
3. ✅ `db.get_listing(listing_id)` (in upload route)
4. ✅ `db.update_listing(listing_id, photos=...)` (in upload route)
5. ✅ `db.get_user_by_id(user_id)` (in user loader)
6. ✅ `db.get_user_by_supabase_uid(uid)` (in user loader)

**Location**: 
- User loader: `web_app.py` lines ~300-347
- Upload route: `routes_main.py` lines ~750-1000
- Database methods: `src/database/db.py` lines ~2052-2184

---

## 🔴 CRITICAL: Authentication Flow

### User Loader Requirements
**File**: `web_app.py` - `load_user()` function

**MUST HAVE**:
1. Retry logic for connection pool exhaustion (3 attempts)
2. Fallback to `get_user_by_id` if `get_user_by_supabase_uid` fails
3. Graceful error handling (return `None` on failure, don't crash)

**Pattern**:
```python
@login_manager.user_loader
def load_user(user_id):
    # ... validation ...
    
    # Retry for pool exhaustion
    for attempt in range(max_retries):
        try:
            user = User.get(user_id_str)
            break
        except PoolError:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            return None
    
    return user
```

### Upload Route Authentication
**File**: `routes_main.py` - `api_upload_photos()` function

**MUST HAVE**:
1. Retry logic for `current_user.is_authenticated` check
2. Retry logic for `current_user.id` access
3. Clear error messages if authentication fails

**Pattern**:
```python
# Check authentication with retry
for auth_attempt in range(max_retries):
    try:
        user_authenticated = current_user.is_authenticated
        break
    except Exception as auth_error:
        if "connection pool exhausted" in str(auth_error).lower():
            time.sleep(0.1)
            continue
        # Handle other errors
```

---

## 🔴 CRITICAL: Photo Upload Flow

### Upload Endpoint Requirements
**File**: `routes_main.py` - `api_upload_photos()` function

**MUST HAVE**:
1. Authentication check with retry logic (see above)
2. Two upload modes:
   - **Listing mode**: `listing_id` provided → attach to committed listing
   - **Temp mode**: `session_id` provided → upload to `temp/{user_id}/{session_id}/`
3. Retry logic for `db.get_listing()` call
4. Retry logic for `db.update_listing()` call
5. Error collection and reporting for failed uploads

### Supabase Storage Configuration
**File**: `src/storage/supabase_storage.py`

**MANDATORY Environment Variables**:
- `SUPABASE_URL` - Must be set and valid
- `SUPABASE_SERVICE_ROLE_KEY` - **REQUIRED** (bypasses RLS)
  - **DO NOT USE** keys starting with `sb_temp_` (invalid)
  - Must start with `eyJ` (valid JWT)
  - Must be 200+ characters
- `SUPABASE_ANON_KEY` - Fallback if service role key not set

**Bucket Requirements**:
- `listing-images` bucket MUST exist and be public
- Storage path format: `{listing_uuid}/{filename}` (listing mode) or `temp/{user_id}/{session_id}/{filename}` (temp mode)

**File Options**:
- **CRITICAL**: Do NOT include `upsert: False` in `file_options`
  - Causes `AttributeError: 'bool' object has no attribute 'encode'`
  - Only include `content-type` in `file_options`

---

## 🔴 CRITICAL: Photo Removal Functionality

### Frontend Requirements
**File**: `templates/create.html`

**MUST HAVE**:
1. X button on each photo preview (red, top-right corner)
2. `removePhoto(index)` function that:
   - Removes from `uploadedPhotos` array
   - Updates UI immediately via `refreshPhotoPreviews()`
   - Calls `/api/update-listing-photos/<listing_id>` if listing is committed
   - Shows success/error messages

**Photo Preview Container Structure**:
```html
<div class="photo-preview-container" style="position: relative; display: inline-block;">
    <img class="photo-preview" src="..." onclick="openPhotoEditor(...)" />
    <button onclick="removePhoto(index)" style="position: absolute; top: 5px; right: 5px;">
        ×
    </button>
</div>
```

### Backend Requirements
**File**: `routes_main.py` - `api_update_listing_photos()` function

**MUST HAVE**:
1. Authentication check (`@login_required`)
2. Verify listing belongs to user
3. Update `photos` column in database (JSON array)
4. Return updated photos array

**Endpoint**: `POST /api/update-listing-photos/<listing_id>`

**Request Body**:
```json
{
    "photos": ["url1", "url2", "url3"]
}
```

---

## 🔴 CRITICAL: Database Update Pattern

### update_listing() Method
**File**: `src/database/db.py` - `update_listing()` method

**MUST HAVE**:
1. Use context manager for connections: `with self._get_connection() as conn:`
2. JSON encode photos array: `json.dumps(photos)`
3. Always update `updated_at` timestamp
4. Commit transaction after update

**Pattern**:
```python
def update_listing(self, listing_id: int, photos: Optional[List[str]] = None, ...):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        if photos is not None:
            updates.append("photos = %s")
            values.append(json.dumps(photos))
        # ... other updates ...
        updates.append("updated_at = CURRENT_TIMESTAMP")
        cursor.execute(query, values)
        conn.commit()
```

---

## 🔴 CRITICAL: Error Handling Requirements

### Upload Errors
**MUST**:
1. Collect errors for each failed file
2. Return detailed error messages to frontend
3. Log errors to Supabase Storage logs bucket (`log-ride`)
4. Continue processing other files if one fails

### Authentication Errors
**MUST**:
1. Return clear error message: "Authentication required to upload photos. Please log in first."
2. Include `error_type: "flask_auth_required"` in response
3. Provide hint: "Make sure you're logged in. If you just logged in, try refreshing the page."

### Connection Pool Errors
**MUST**:
1. Retry with exponential backoff (0.1s, 0.2s, 0.3s)
2. Log retry attempts
3. Return user-friendly error if all retries fail

---

## 🔴 CRITICAL: Frontend State Management

### uploadedPhotos Array
**File**: `templates/create.html`

**MUST**:
1. Initialize from `listing_photos` (database) on page load
2. Update immediately when photos are added/removed
3. Sync with database for committed listings
4. Persist in session for temp mode

**Refresh Pattern**:
```javascript
// After upload success
uploadedPhotos = uploadedPhotos.concat(newPhotos);
refreshPhotoPreviews();
updateAnalyzeButtonState();

// After remove
uploadedPhotos.splice(index, 1);
refreshPhotoPreviews();
updateAnalyzeButtonState();
```

---

## 🔴 CRITICAL: Configuration Values

### Connection Pool
- **Session Mode**: `maxconn=3`, `minconn=0` (on-demand)
- **Transaction Mode**: `maxconn=10`, `minconn=2`
- **DO NOT CHANGE** without testing concurrent load

### Retry Settings
- **Max Retries**: 3 attempts
- **Backoff**: 0.1s * attempt_number (0.1s, 0.2s, 0.3s)
- **DO NOT REDUCE** retry count below 3

### Timeouts
- **Connection Timeout**: 5 seconds
- **Statement Timeout**: 10 seconds (10000ms)
- **Keepalive**: Enabled (1, 30, 10, 3)

---

## ⚠️ BREAKING CHANGES TO AVOID

### DO NOT:
1. ❌ Reduce connection pool size below 3 (Session mode)
2. ❌ Remove retry logic from database operations
3. ❌ Add `upsert: False` to Supabase Storage `file_options`
4. ❌ Remove authentication checks from upload route
5. ❌ Change photo array structure (must be JSON array of URLs)
6. ❌ Remove X button from photo previews
7. ❌ Skip database update after photo removal
8. ❌ Use invalid Supabase keys (check for `sb_temp_` prefix)

### MUST MAINTAIN:
1. ✅ Connection pool retry logic in ALL database operations
2. ✅ Authentication retry logic in upload route
3. ✅ Photo preview container structure (img + remove button)
4. ✅ JSON encoding of photos array in database
5. ✅ Two upload modes (listing vs temp)
6. ✅ Error collection and reporting
7. ✅ Supabase Storage bucket configuration

---

## 📋 Testing Checklist

Before considering image upload "working", verify:

- [ ] Can upload single photo to new listing
- [ ] Can upload multiple photos to existing listing
- [ ] Can remove photo using X button
- [ ] Photo removal updates database
- [ ] Upload works when connection pool is busy (concurrent requests)
- [ ] Authentication errors show clear message
- [ ] Failed uploads show specific error messages
- [ ] Photos persist after page refresh
- [ ] Temp mode uploads work (session_id without listing_id)
- [ ] Listing mode uploads work (listing_id provided)

---

## 🔗 Related Files

- `src/database/db.py` - Connection pool, database methods
- `web_app.py` - User loader, Flask-Login setup
- `routes_main.py` - Upload endpoint, photo update endpoint
- `src/storage/supabase_storage.py` - Supabase Storage client
- `templates/create.html` - Frontend photo handling
- `render.yaml` - Deployment configuration

---

## 📝 Notes

- Connection pool exhaustion is the #1 cause of authentication failures
- Retry logic is **non-negotiable** - without it, uploads will fail under load
- Supabase Storage requires `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS
- Photo removal must update both frontend state AND database
- All database operations must use context managers (`with self._get_connection()`)

---

**Last Working State**: All image upload functionality working with retry logic and connection pool size 3.

