# Photo Storage & Curation Guide

## 📸 Complete Photo Flow Architecture

### When a User Scans an Item:

```
1. User uploads photos
   ↓
2. Photos → Supabase Storage "temp-photos" bucket
   URL: https://[project].supabase.co/storage/v1/object/public/temp-photos/[filename]
   ↓
3. User runs Enhanced Scan
   ↓
4. Artifact created in public_artifacts table (NO photos yet)
   ↓
5. Photos stored in pending_artifact_photos table
   {
     artifact_id: [artifact ID],
     user_id: [who uploaded],
     photo_url: [Supabase URL],
     is_selected: FALSE,
     created_at: [timestamp]
   }
   ↓
6. User saves to their vault
   ↓
7. Photos + item data → card_collections table (user's personal database)
```

---

## 🗄️ Where Photos Are Stored

### Storage Locations:

1. **Supabase Storage Buckets**:
   - **temp-photos**: Initial upload location (temporary)
   - **listing-images**: For marketplace listings
   - **draft-images**: For saved drafts

2. **Database Tables**:
   - **`pending_artifact_photos`**: Photos waiting for admin curation
   - **`public_artifacts.photos`**: Published photos (JSON array of URLs)
   - **`card_collections`**: User's personal vault (photos + item data)

---

## 🎯 How to Access & Curate Photos

### Option 1: Admin Photo Curation Dashboard (BEST)

**URL**: `/admin/photo-curation`

**Features**:
- ✅ See ALL pending photos across ALL artifacts in one place
- ✅ Grid view with visual selection
- ✅ Shows user who uploaded + timestamp
- ✅ Select/deselect with one click
- ✅ Batch publish selected photos
- ✅ Statistics dashboard

**How to Use**:
1. Navigate to `/admin/photo-curation`
2. You'll see all artifacts with pending photos
3. Click any photo to select/deselect it
4. Selected photos show green checkmark
5. Click "Publish Selected Photos" to make them public
6. Photos move from pending → Hall of Records

### Option 2: Per-Artifact Review

**URL**: `/artifact/{id}`

**Features**:
- View one artifact at a time
- See pending photos for that specific artifact
- Select and publish photos

---

## 📊 Database Structure

### pending_artifact_photos Table:

```sql
CREATE TABLE pending_artifact_photos (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER REFERENCES public_artifacts(id),
    user_id INTEGER REFERENCES users(id),
    photo_url TEXT NOT NULL,
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**What it means**:
- `is_selected = FALSE`: Photo is pending your review
- `is_selected = TRUE`: You already published this photo
- `photo_url`: Direct link to Supabase Storage

### public_artifacts Table:

```sql
CREATE TABLE public_artifacts (
    id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    brand TEXT,
    franchise TEXT,
    category TEXT,
    item_type TEXT,
    photos JSONB,  -- Array of selected photo URLs
    ...
);
```

**What it means**:
- `photos`: JSON array like `["url1", "url2"]`
- Starts empty: `[]`
- When you publish photos, they're added to this array

---

## 🔄 Photo Publishing Flow

### Before Publishing:

```
public_artifacts.photos = []
pending_artifact_photos:
  - id: 1, photo_url: "https://...", is_selected: FALSE
  - id: 2, photo_url: "https://...", is_selected: FALSE
  - id: 3, photo_url: "https://...", is_selected: FALSE
```

### After Publishing (you selected photos 1 and 3):

```
public_artifacts.photos = ["https://url1", "https://url3"]
pending_artifact_photos:
  - id: 1, photo_url: "https://...", is_selected: TRUE ✅
  - id: 2, photo_url: "https://...", is_selected: FALSE
  - id: 3, photo_url: "https://...", is_selected: TRUE ✅
```

---

## 🛡️ User Privacy & Photo Ownership

### User's Personal Vault:
- **User scans item** → Photos + details saved to their `card_collections`
- **Photos stay with user** → They own the photos in their vault
- **Never auto-published** → User photos remain private

### Hall of Records (Public):
- **Artifact metadata only** → No photos by default
- **You curate photos** → Only you (admin) select which photos go public
- **Pending photos** → Users see their own scans, you see all pending photos
- **Full control** → You decide what the world sees

---

## 🔍 How to Query Photos Directly

### Get All Pending Photos:

```sql
SELECT
    p.id,
    p.photo_url,
    p.is_selected,
    p.created_at,
    p.user_id,
    a.item_name,
    a.franchise
FROM pending_artifact_photos p
JOIN public_artifacts a ON p.artifact_id = a.id
WHERE p.is_selected = FALSE
ORDER BY p.created_at DESC;
```

### Get Artifacts With Pending Photos:

```sql
SELECT
    a.id,
    a.item_name,
    a.franchise,
    COUNT(p.id) as pending_count
FROM public_artifacts a
JOIN pending_artifact_photos p ON a.id = p.artifact_id
WHERE p.is_selected = FALSE
GROUP BY a.id, a.item_name, a.franchise
ORDER BY pending_count DESC;
```

### Get Published Photos for an Artifact:

```sql
SELECT photos
FROM public_artifacts
WHERE id = [artifact_id];
```

---

## 📋 Quick Reference

### Access Points:

| What | URL | Who Can Access |
|------|-----|----------------|
| Photo Curation Dashboard | `/admin/photo-curation` | Admin only (you) |
| Artifact Detail | `/artifact/{id}` | Everyone (pending photos only visible to admin) |
| Hall of Records List | `/hall-of-records` | Everyone |
| User's Vault | `/vault` | User (their own items only) |

### Photo States:

| State | Location | Visible To | What It Means |
|-------|----------|------------|---------------|
| Pending | `pending_artifact_photos` | Admin only | Waiting for your review |
| Published | `public_artifacts.photos` | Everyone | You selected this photo |
| User Vault | `card_collections` | User only | User's personal copy |

---

## 🎨 Your Workflow

### Daily Curation Process:

1. **Check Dashboard**: Visit `/admin/photo-curation`
2. **Review Stats**: See how many photos are pending
3. **Review Photos**: Look through all pending photos by artifact
4. **Select Best**: Click to select highest quality photos
5. **Publish**: Click "Publish Selected Photos"
6. **Repeat**: Move to next artifact

### Tips for Selection:

- ✅ Choose highest resolution photos
- ✅ Best lighting and focus
- ✅ Multiple angles if helpful
- ✅ Clear view of important details
- ❌ Avoid blurry or dark photos
- ❌ Skip photos with personal info visible
- ❌ Remove duplicates

---

## 🚀 Summary

**Key Points**:
- Photos start in **Supabase Storage** (temp-photos bucket)
- Enhanced scans create **pending photos** in `pending_artifact_photos` table
- **You (admin) review** and select best photos
- Selected photos **published** to Hall of Records
- Users keep **their own copies** in personal vault
- **Full separation** between user vault and public database

**Your Control**:
- ✅ You decide what photos go public
- ✅ Users never auto-publish to Hall of Records
- ✅ Photos stay with user's vault copy
- ✅ You curate the public database

**Access Your Dashboard**: `/admin/photo-curation`
