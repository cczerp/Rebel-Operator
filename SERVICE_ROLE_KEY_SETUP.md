# Service Role Key Setup for Supabase Storage

## Why Service Role Key is Required

For **server-side uploads** to Supabase Storage, you **must** use the `service_role` key because:
- It bypasses Row Level Security (RLS) policies
- It's required for server-side operations
- The `anon` key respects RLS and will fail if policies aren't set up

## Environment Variables

You should have **both** keys set (they're used for different purposes):

```bash
# For server-side operations (REQUIRED for uploads)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# For client-side operations (if needed for other features)
SUPABASE_ANON_KEY=your-anon-key-here

# Project URL (same for both)
SUPABASE_URL=https://your-project.supabase.co
```

## How to Get Your Keys

1. Go to Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Go to **Settings** → **API**
4. You'll see:
   - **Project URL** → Use for `SUPABASE_URL`
   - **anon public** key → Use for `SUPABASE_ANON_KEY` (client-side)
   - **service_role** key → Use for `SUPABASE_SERVICE_ROLE_KEY` (server-side)

⚠️ **Security Warning**: 
- **service_role key**: Never expose to frontend/client code. Only use server-side.
- **anon key**: Safe for client-side use, but respects RLS policies.

## Current Code Behavior

The code now:
1. **First checks** for `SUPABASE_SERVICE_ROLE_KEY` (required for uploads)
2. **Falls back** to `SUPABASE_KEY` or `SUPABASE_ANON_KEY` (with warning)
3. **Logs** which key is being used (check server logs)

## Verification

After setting `SUPABASE_SERVICE_ROLE_KEY`, check your server logs. You should see:
```
✅ Using SUPABASE_SERVICE_ROLE_KEY (bypasses RLS - correct for server-side)
```

If you see a warning, the service_role key isn't being found.

