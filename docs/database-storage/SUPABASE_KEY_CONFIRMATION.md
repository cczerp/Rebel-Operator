# Supabase Storage Key Configuration - Confirmed ✅

## Your Current Setup

You're correct - **one Supabase URL and one API key** works for all buckets. The implementation already follows this pattern.

## How It Works in the Code

### Single Client Initialization
```python
# One client created with one URL and one key
self.client = create_client(self.supabase_url, self.supabase_key)
```

### Bucket Selection by Name
All operations specify the bucket by name:
```python
# Upload to temp-photos
self.client.storage.from_('temp-photos').upload(...)

# Upload to draft-images  
self.client.storage.from_('draft-images').upload(...)

# Upload to listing-images
self.client.storage.from_('listing-images').upload(...)
```

## Environment Variables You Need

```bash
# One URL for the entire project
SUPABASE_URL=https://your-project.supabase.co

# One key (use service_role for server-side, anon for client-side)
SUPABASE_KEY=your-service-role-key  # For server-side operations
# OR
SUPABASE_ANON_KEY=your-anon-key     # For client-side (if needed)
```

## Bucket Names (Optional - defaults shown)

These are just for convenience, defaults match your bucket names:
```bash
SUPABASE_BUCKET_TEMP=temp-photos
SUPABASE_BUCKET_DRAFTS=draft-images
SUPABASE_BUCKET_LISTINGS=listing-images
```

## Key Type Recommendation

**For server-side (Flask backend):**
- Use `SUPABASE_KEY` with your **service_role key** (bypasses RLS)
- This is what the current code uses

**For client-side (if you add frontend uploads later):**
- Use `SUPABASE_ANON_KEY` with your **anon key** (respects RLS)
- Only if you need direct client-to-Supabase uploads

## Summary

✅ **One URL** → `SUPABASE_URL`  
✅ **One Key** → `SUPABASE_KEY` (service_role for server)  
✅ **Bucket names** → Specified in code calls, configurable via env vars  
✅ **Already implemented correctly** → No changes needed!

Your existing Supabase credentials will work perfectly as long as the bucket names match:
- `temp-photos`
- `draft-images`  
- `listing-images`

