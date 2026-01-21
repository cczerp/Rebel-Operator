# Fixing RLS (Row Level Security) Error

## Error Message
```
Upload failed: {'statusCode': 400, 'error': 'Unauthorized', 'message': 'new row violates row-level security policy'}
```

## Solution

You need to use the **service_role key** for server-side uploads, which bypasses RLS policies.

### Option 1: Use Service Role Key (Recommended for Server-Side)

1. **Get your service_role key:**
   - Go to Supabase Dashboard → Settings → API
   - Copy the **service_role** key (NOT the anon key)
   - ⚠️ **Never expose this key to the client/frontend!**

2. **Set environment variable:**
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

   The code will automatically prefer `SUPABASE_SERVICE_ROLE_KEY` over other keys.

### Option 2: Disable RLS on Buckets (Temporary)

If you want to disable RLS until the flow is finalized:

1. Go to Supabase Dashboard → Storage
2. Click on each bucket (`temp-photos`, `draft-images`, `listing-images`)
3. Go to **Policies** tab
4. **Disable RLS** (toggle off "Enable RLS")

⚠️ **Warning**: This makes buckets publicly accessible. Only do this for development/testing.

### Option 3: Set Up RLS Policies (For Production)

If you want to keep RLS enabled, create policies that allow authenticated users:

**For `temp-photos` bucket:**
```sql
-- Allow authenticated users to upload
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'temp-photos');

-- Allow authenticated users to read
CREATE POLICY "Allow authenticated reads"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'temp-photos');

-- Allow authenticated users to delete
CREATE POLICY "Allow authenticated deletes"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'temp-photos');
```

Repeat for `draft-images` and `listing-images` buckets.

## Recommended Approach

**For now (development):** Use `SUPABASE_SERVICE_ROLE_KEY` - it bypasses RLS and works immediately.

**For production:** Set up proper RLS policies and use service_role key only on the server.

