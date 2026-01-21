#!/usr/bin/env python3
"""
Supabase Connection Diagnostic Tool
====================================
Tests Supabase Storage connection and downloads to identify issues.

Usage: python test_supabase_connection.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")
    print("   Will use system environment variables")

print("\n" + "="*70)
print("SUPABASE CONNECTION DIAGNOSTIC")
print("="*70 + "\n")

# Step 1: Check environment variables
print("STEP 1: Checking Environment Variables")
print("-" * 70)

supabase_url = os.getenv('SUPABASE_URL', '').strip()
service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
secret_api_key = os.getenv('SUPABASE_SECRET_API_KEY', '').strip()
supabase_key = os.getenv('SUPABASE_KEY', '').strip()
anon_key = os.getenv('SUPABASE_ANON_KEY', '').strip()

# Determine which key will be used
active_key = None
active_key_name = None
if service_role_key:
    active_key = service_role_key
    active_key_name = 'SUPABASE_SERVICE_ROLE_KEY'
elif secret_api_key:
    active_key = secret_api_key
    active_key_name = 'SUPABASE_SECRET_API_KEY'
elif supabase_key:
    active_key = supabase_key
    active_key_name = 'SUPABASE_KEY'
elif anon_key:
    active_key = anon_key
    active_key_name = 'SUPABASE_ANON_KEY'

# Print results
if supabase_url:
    print(f"✅ SUPABASE_URL: {supabase_url}")
else:
    print(f"❌ SUPABASE_URL: NOT SET")
    print("   💡 Add to .env: SUPABASE_URL=https://your-project.supabase.co")

if active_key:
    # Mask key for security
    masked_key = active_key[:10] + "..." + active_key[-10:] if len(active_key) > 20 else "***"
    print(f"✅ Active Key: {active_key_name}")
    print(f"   Value: {masked_key}")

    if active_key_name == 'SUPABASE_ANON_KEY':
        print(f"   ⚠️  WARNING: Using anon key may cause RLS permission errors!")
        print(f"   💡 Recommended: Use SUPABASE_SERVICE_ROLE_KEY instead")
    else:
        print(f"   ✅ Good: Service role key should bypass RLS")
else:
    print(f"❌ No Supabase API key found!")
    print("   💡 Add to .env: SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")

# Bucket names
temp_bucket = os.getenv('SUPABASE_BUCKET_TEMP', 'temp-photos')
drafts_bucket = os.getenv('SUPABASE_BUCKET_DRAFTS', 'draft-images')
listings_bucket = os.getenv('SUPABASE_BUCKET_LISTINGS', 'listing-images')

print(f"\n📁 Bucket Configuration:")
print(f"   Temp: {temp_bucket}")
print(f"   Drafts: {drafts_bucket}")
print(f"   Listings: {listings_bucket}")

if not supabase_url or not active_key:
    print("\n" + "="*70)
    print("❌ CRITICAL: Missing environment variables!")
    print("="*70)
    print("\nCannot proceed with connection test.")
    print("\nTO FIX:")
    print("1. Create a .env file in your project root")
    print("2. Add these lines:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here")
    print("\n3. Get credentials from: https://app.supabase.com → Your Project → Settings → API")
    sys.exit(1)

# Step 2: Test Supabase client initialization
print("\n" + "="*70)
print("STEP 2: Testing Supabase Client Initialization")
print("-" * 70)

try:
    from supabase import create_client, Client
    print("✅ Supabase package imported successfully")

    client = create_client(supabase_url, active_key)
    print(f"✅ Supabase client created successfully")
    print(f"   Using: {active_key_name}")

except ImportError as e:
    print(f"❌ Failed to import supabase package: {e}")
    print("   💡 Install with: pip install supabase")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to create Supabase client: {e}")
    print("   💡 Check that your SUPABASE_URL and key are correct")
    sys.exit(1)

# Step 3: List buckets
print("\n" + "="*70)
print("STEP 3: Listing Storage Buckets")
print("-" * 70)

try:
    buckets = client.storage.list_buckets()
    print(f"✅ Successfully connected to Supabase Storage!")
    print(f"   Found {len(buckets)} bucket(s):")

    for bucket in buckets:
        bucket_name = bucket.get('name') if isinstance(bucket, dict) else bucket.name
        bucket_public = bucket.get('public') if isinstance(bucket, dict) else getattr(bucket, 'public', 'unknown')
        status = "PUBLIC ✅" if bucket_public else "PRIVATE ⚠️"
        print(f"   - {bucket_name} ({status})")

except Exception as e:
    print(f"❌ Failed to list buckets: {e}")
    print(f"   Error type: {type(e).__name__}")
    error_str = str(e).lower()
    if 'unauthorized' in error_str or '401' in error_str or '403' in error_str:
        print("   💡 Your API key doesn't have permission to access Storage")
        print("   💡 Make sure you're using the service_role key, not the anon key")
    else:
        import traceback
        print(f"\n   Full traceback:")
        traceback.print_exc()

# Step 4: Test file listing in buckets
print("\n" + "="*70)
print("STEP 4: Testing File Listing in Buckets")
print("-" * 70)

for bucket_name in [temp_bucket, drafts_bucket, listings_bucket]:
    try:
        print(f"\n📁 Bucket: {bucket_name}")
        files = client.storage.from_(bucket_name).list()
        print(f"   ✅ Listed files successfully: {len(files)} file(s)")

        # Show first 5 files
        for i, file in enumerate(files[:5]):
            file_name = file.get('name') if isinstance(file, dict) else file.name
            print(f"      {i+1}. {file_name}")

        if len(files) > 5:
            print(f"      ... and {len(files) - 5} more")

    except Exception as e:
        print(f"   ❌ Failed to list files: {e}")
        error_str = str(e).lower()
        if 'not found' in error_str or '404' in error_str:
            print(f"      💡 Bucket '{bucket_name}' doesn't exist")
        elif 'unauthorized' in error_str or '401' in error_str or '403' in error_str:
            print(f"      💡 No permission to access bucket '{bucket_name}'")

# Step 5: Test download from first available file
print("\n" + "="*70)
print("STEP 5: Testing File Download")
print("-" * 70)

test_file_found = False
for bucket_name in [listings_bucket, drafts_bucket, temp_bucket]:
    try:
        files = client.storage.from_(bucket_name).list()
        if files:
            test_file = files[0]
            test_file_name = test_file.get('name') if isinstance(test_file, dict) else test_file.name

            print(f"\n📥 Testing download from: {bucket_name}/{test_file_name}")

            # Try download
            response = client.storage.from_(bucket_name).download(test_file_name)

            if isinstance(response, bytes):
                print(f"   ✅ Download successful!")
                print(f"      Downloaded: {len(response)} bytes")
                print(f"      Type: {type(response)}")
                test_file_found = True
                break
            elif hasattr(response, 'read'):
                data = response.read()
                print(f"   ✅ Download successful!")
                print(f"      Downloaded: {len(data)} bytes")
                print(f"      Type: file-like object → bytes")
                test_file_found = True
                break
            else:
                print(f"   ⚠️  Unexpected response type: {type(response)}")

    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        continue

if not test_file_found:
    print("\n⚠️  No files found in any bucket to test download")
    print("   Upload a test image to one of your buckets to test downloads")

# Step 6: Test public URL download (HTTP)
print("\n" + "="*70)
print("STEP 6: Testing Public URL Download (HTTP)")
print("-" * 70)

if test_file_found:
    try:
        import requests

        # Construct public URL
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{test_file_name}"
        print(f"\n🌐 Testing HTTP download from public URL:")
        print(f"   {public_url[:80]}...")

        response = requests.get(public_url, timeout=10)

        if response.status_code == 200:
            print(f"   ✅ HTTP download successful!")
            print(f"      Status: {response.status_code}")
            print(f"      Size: {len(response.content)} bytes")
        elif response.status_code in [401, 403]:
            print(f"   ❌ HTTP {response.status_code}: Permission Denied")
            print(f"      💡 Bucket is not public or RLS is blocking access")
            print(f"      💡 Check bucket settings in Supabase Dashboard")
        elif response.status_code == 404:
            print(f"   ❌ HTTP 404: File not found at public URL")
            print(f"      💡 File may not be in public bucket")
        else:
            print(f"   ❌ HTTP {response.status_code}: Unexpected status")
            print(f"      Response: {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ HTTP download failed: {e}")

# Final summary
print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)

if supabase_url and active_key:
    print("\n✅ Environment variables are configured")
    print(f"✅ Using {active_key_name}")

    if active_key_name == 'SUPABASE_ANON_KEY':
        print("\n⚠️  RECOMMENDATION:")
        print("   Switch to SUPABASE_SERVICE_ROLE_KEY to avoid RLS issues")

    if test_file_found:
        print("\n✅ File download is working!")
        print("   Your Supabase Storage connection is functional.")
    else:
        print("\n⚠️  No files found to test download")
        print("   Upload test images to verify download functionality")
else:
    print("\n❌ Missing critical environment variables")
    print("   Fix the issues above and run this script again")

print("\n" + "="*70)
print("For more help, see: https://supabase.com/docs/guides/storage")
print("="*70 + "\n")
