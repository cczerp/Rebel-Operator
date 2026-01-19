-- ============================================================================
-- Supabase Storage RLS Policies for Vault Bucket
-- ============================================================================
-- This SQL file contains Row Level Security (RLS) policies for the 'vault' bucket.
-- The vault bucket stores users' personal collections (private, not for sale).
--
-- IMPORTANT: Run these SQL commands in your Supabase SQL Editor:
-- https://app.supabase.com → SQL Editor → New Query → Paste & Run
--
-- ============================================================================

-- ============================================================================
-- STEP 1: Ensure vault bucket exists
-- ============================================================================
-- You should create the 'vault' bucket in the Supabase Dashboard first:
-- https://app.supabase.com → Storage → New Bucket
-- - Name: vault
-- - Public: OFF (private bucket - only accessible by bucket owner)
-- - File size limit: As needed (e.g., 50 MB per file)
-- - Allowed MIME types: image/*, or specific types as needed

-- ============================================================================
-- STEP 2: Enable RLS on the vault bucket
-- ============================================================================
-- RLS should be enabled automatically for new buckets, but verify in:
-- https://app.supabase.com → Storage → vault → Settings → RLS Policies

-- ============================================================================
-- STEP 3: Create RLS Policies
-- ============================================================================

-- Policy: Users can SELECT (read) their own files
-- Files are organized by user_id folders: vault/{user_id}/{filename}
CREATE POLICY "Users can read own vault files"
ON storage.objects
FOR SELECT
USING (
    bucket_id = 'vault'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can INSERT (upload) to their own folder
CREATE POLICY "Users can upload to own vault"
ON storage.objects
FOR INSERT
WITH CHECK (
    bucket_id = 'vault'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can UPDATE their own files (e.g., overwrite)
CREATE POLICY "Users can update own vault files"
ON storage.objects
FOR UPDATE
USING (
    bucket_id = 'vault'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can DELETE their own files
CREATE POLICY "Users can delete own vault files"
ON storage.objects
FOR DELETE
USING (
    bucket_id = 'vault'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================================
-- STEP 4: Admin Override Policies (Optional)
-- ============================================================================
-- If you want admins to access all vault files, add these policies:

-- Policy: Admins can read all vault files
-- Note: Replace 'is_admin' with your actual admin check
-- This assumes you have an 'is_admin' column in your users/profiles table
CREATE POLICY "Admins can read all vault files"
ON storage.objects
FOR SELECT
USING (
    bucket_id = 'vault'
    AND EXISTS (
        SELECT 1 FROM auth.users
        WHERE auth.users.id = auth.uid()
        AND auth.users.raw_user_meta_data->>'is_admin' = 'true'
    )
);

-- Policy: Admins can delete any vault files (for moderation)
CREATE POLICY "Admins can delete any vault files"
ON storage.objects
FOR DELETE
USING (
    bucket_id = 'vault'
    AND EXISTS (
        SELECT 1 FROM auth.users
        WHERE auth.users.id = auth.uid()
        AND auth.users.raw_user_meta_data->>'is_admin' = 'true'
    )
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- After running the policies, verify they're active:

-- List all policies for the vault bucket
SELECT * FROM pg_policies
WHERE tablename = 'objects'
AND policyname LIKE '%vault%';

-- Test file path parsing (should return array with user_id)
-- Example: storage.foldername('123e4567-e89b-12d3-a456-426614174000/myfile.jpg')
-- Should return: {123e4567-e89b-12d3-a456-426614174000}
SELECT storage.foldername('your-user-id/test-image.jpg');

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. File Organization:
--    - Vault files are organized by user_id: vault/{user_id}/{filename}
--    - This is handled automatically by upload_to_vault() in supabase_storage.py
--
-- 2. Authentication:
--    - Users must be authenticated (auth.uid() must return a valid user ID)
--    - Unauthenticated users cannot access vault files
--
-- 3. Service Role Key:
--    - Server-side operations using SUPABASE_SERVICE_ROLE_KEY bypass RLS
--    - This is useful for admin operations or backend processing
--
-- 4. Testing RLS:
--    - Use Supabase Dashboard: Storage → vault → View files
--    - Or use JavaScript client with user authentication
--    - Or use curl with JWT token
--
-- 5. Admin Access:
--    - Adjust admin check based on your user schema
--    - Common patterns:
--      * raw_user_meta_data->>'is_admin' = 'true'
--      * Check against separate admins table
--      * Check user role in auth.users
--
-- ============================================================================
-- TROUBLESHOOTING
-- ============================================================================
-- If users can't access their files:
-- 1. Verify user is authenticated (auth.uid() returns their ID)
-- 2. Check file path: vault/{user_id}/{filename} (user_id must match auth.uid())
-- 3. Verify policies are enabled: SELECT * FROM pg_policies WHERE tablename = 'objects';
-- 4. Check bucket RLS is enabled in Supabase Dashboard
--
-- If using service_role key on server:
-- - Server operations bypass RLS automatically
-- - No policy changes needed for server-side operations
--
-- ============================================================================
