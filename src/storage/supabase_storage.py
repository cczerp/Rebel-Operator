"""
Supabase Storage Manager
========================
Handles photo uploads to Supabase Storage buckets per system contract.

System Contract Requirements:
- Provider: Supabase Storage
- Buckets: listing-images
- Paths are namespaced by user_id
- Database stores image references (URLs), not binaries
"""

import os
from typing import Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime


def _get_supabase_storage_client():
    """
    Get Supabase client for storage operations.
    
    Per Supabase docs: "All other bucket or file operations require you to meet storage policies"
    Since we use Flask-Login (not Supabase Auth), we need service role key to bypass RLS policies.
    Falls back to anon key if service role key not available.
    """
    import os
    from supabase.client import Client, ClientOptions
    
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    if not supabase_url:
        print(f"[SUPABASE_STORAGE ERROR] SUPABASE_URL environment variable is not set", flush=True)
        return None
    
    # Validate URL format
    if not supabase_url.startswith("http"):
        print(f"[SUPABASE_STORAGE ERROR] SUPABASE_URL appears invalid (should start with http/https): {supabase_url[:50]}...", flush=True)
        return None
    
    print(f"[SUPABASE_STORAGE] SUPABASE_URL configured: {supabase_url[:30]}...", flush=True)
    
    # Try service role key first (bypasses RLS policies)
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if service_role_key:
        # Validate key format - service role keys should NOT start with sb_temp_
        if service_role_key.startswith("sb_temp_"):
            print(f"[SUPABASE_STORAGE ERROR] ⚠️  Service role key appears to be a temporary/invalid key (starts with 'sb_temp_'). Get the permanent service_role key from Supabase Dashboard → Settings → API", flush=True)
            # Continue anyway, but warn
        elif len(service_role_key) < 50:
            print(f"[SUPABASE_STORAGE WARNING] Service role key seems too short ({len(service_role_key)} chars). Verify it's the full key from Supabase Dashboard.", flush=True)
        
        try:
            print(f"[SUPABASE_STORAGE] ✅ Using service role key for storage operations (bypasses RLS)", flush=True)
            print(f"[SUPABASE_STORAGE] Key prefix: {service_role_key[:20]}... (length: {len(service_role_key)})", flush=True)
            client = Client(
                supabase_url,
                service_role_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
            # Test client by checking if we can access storage
            print(f"[SUPABASE_STORAGE] Service role client initialized successfully", flush=True)
            return client
        except Exception as e:
            error_msg = str(e)
            print(f"[SUPABASE_STORAGE ERROR] Service role key failed to initialize client: {type(e).__name__}: {error_msg}", flush=True)
            if "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                print(f"[SUPABASE_STORAGE ERROR] ⚠️  API key appears invalid. Verify SUPABASE_SERVICE_ROLE_KEY is the correct 'service_role' key (not 'anon' key) from Supabase Dashboard → Settings → API", flush=True)
            import traceback
            traceback.print_exc()
    
    # Fallback to anon key (requires proper storage policies)
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if anon_key:
        try:
            print(f"[SUPABASE_STORAGE] ⚠️  Using anon key (may require storage policies)", flush=True)
            client = Client(
                supabase_url,
                anon_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
            print(f"[SUPABASE_STORAGE] Anon key client initialized successfully", flush=True)
            return client
        except Exception as e:
            print(f"[SUPABASE_STORAGE ERROR] Anon key failed to initialize client: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()
    else:
        print(f"[SUPABASE_STORAGE ERROR] Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY is set", flush=True)
    
    return None


def upload_to_supabase_storage(
    file_data: bytes,
    filename: str,
    user_id: str,
    listing_uuid: Optional[str] = None,
    bucket_name: str = "listing-images",
    override_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Upload a file to Supabase Storage bucket.

    IMPORTANT: Per Supabase docs, public buckets only allow public downloads.
    Upload operations require storage policies. This function uses service role key
    (if available) to bypass RLS, or anon key with proper policies.

    Args:
        file_data: File bytes to upload
        filename: Original filename
        user_id: User ID for namespacing (required per system contract)
        listing_uuid: Optional listing UUID for organization
        bucket_name: Bucket name (default: "listing-images" per system contract)

    Returns:
        (success: bool, url_or_path: str)
        - On success: Returns Supabase Storage public URL
        - On failure: Returns error message string
    """
    try:
        # Validate environment variables upfront
        supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
        
        print(f"[SUPABASE_STORAGE DEBUG] Environment check:", flush=True)
        print(f"  - SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'} ({supabase_url[:30] + '...' if supabase_url else 'N/A'})", flush=True)
        print(f"  - SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if service_role_key else '❌ Missing'}", flush=True)
        print(f"  - SUPABASE_ANON_KEY: {'✅ Set' if anon_key else '❌ Missing'}", flush=True)
        
        if not supabase_url:
            error_msg = "SUPABASE_URL environment variable is not set. Please set it in your .env file or environment variables."
            print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
            return False, error_msg
        
        if not service_role_key and not anon_key:
            error_msg = "Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY is set. Please set at least one in your .env file or environment variables."
            print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
            return False, error_msg
        
        supabase = _get_supabase_storage_client()
        if not supabase:
            error_msg = "Failed to initialize Supabase client. Please check: 1) SUPABASE_URL is correct, 2) SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is correct, 3) Check server logs for detailed error."
            print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
            return False, error_msg

        # Namespace path by user_id per system contract
        # Format: {user_id}/{listing_uuid}/{filename} or {user_id}/{filename}
        # For temp uploads we can override the exact storage path (e.g. temp/{user_id}/{session_id}/filename)
        if override_path:
            storage_path = override_path
        elif listing_uuid:
            storage_path = f"{user_id}/{listing_uuid}/{filename}"
        else:
            # Use timestamp-based folder for temporary uploads
            timestamp = datetime.now().strftime('%Y%m%d')
            storage_path = f"{user_id}/{timestamp}/{filename}"

        print(f"[SUPABASE_STORAGE] Uploading to bucket '{bucket_name}' at path: {storage_path}", flush=True)

        # Detect content type from filename
        content_type = "image/jpeg"  # Default
        filename_lower = filename.lower()
        if filename_lower.endswith('.png'):
            content_type = "image/png"
        elif filename_lower.endswith('.gif'):
            content_type = "image/gif"
        elif filename_lower.endswith('.webp'):
            content_type = "image/webp"

        # Check if bucket exists before attempting upload
        try:
            print(f"[SUPABASE_STORAGE] Checking if bucket '{bucket_name}' exists...", flush=True)
            buckets_response = supabase.storage.list_buckets()
            print(f"[SUPABASE_STORAGE] Available buckets response: {buckets_response}", flush=True)
            
            # Parse buckets list
            buckets_list = []
            if isinstance(buckets_response, dict):
                buckets_list = buckets_response.get('data', []) or []
            elif hasattr(buckets_response, 'data'):
                buckets_list = buckets_response.data or []
            elif isinstance(buckets_response, list):
                buckets_list = buckets_response
            
            bucket_names = []
            if buckets_list:
                for bucket in buckets_list:
                    if isinstance(bucket, dict):
                        bucket_names.append(bucket.get('name', ''))
                    elif hasattr(bucket, 'name'):
                        bucket_names.append(bucket.name)
                    elif isinstance(bucket, str):
                        bucket_names.append(bucket)
            
            print(f"[SUPABASE_STORAGE] Found buckets: {bucket_names}", flush=True)
            
            if bucket_name not in bucket_names:
                error_msg = f"Bucket '{bucket_name}' not found. Available buckets: {', '.join(bucket_names) if bucket_names else 'none'}. Please create the bucket '{bucket_name}' in Supabase Storage dashboard and make it public."
                print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
                return False, error_msg
            
            print(f"[SUPABASE_STORAGE] ✅ Bucket '{bucket_name}' exists", flush=True)
        except Exception as bucket_check_error:
            print(f"[SUPABASE_STORAGE WARNING] Could not verify bucket existence (may not have list permission): {type(bucket_check_error).__name__}: {bucket_check_error}", flush=True)
            # Continue anyway - upload will fail with a clearer error if bucket doesn't exist
        
        # Upload to Supabase Storage
        # Supabase Python client API: storage.from_(bucket).upload(path, file_bytes, file_options)
        try:
            print(f"[SUPABASE_STORAGE] Attempting upload - File size: {len(file_data)} bytes, Content-Type: {content_type}", flush=True)
            print(f"[SUPABASE_STORAGE] Upload path: {storage_path}", flush=True)

            # Convert bytes to file-like object if needed, or use bytes directly
            # Supabase expects file_data as bytes or file-like object
            # Note: file_options only accepts string values for headers
            # upsert is not a valid file_option - it's handled by the upload method itself
            
            # Log exactly what we're sending
            print(f"[SUPABASE_STORAGE] About to upload:", flush=True)
            print(f"  - Bucket: {bucket_name}", flush=True)
            print(f"  - Path: {storage_path}", flush=True)
            print(f"  - File size: {len(file_data)} bytes", flush=True)
            print(f"  - Content-Type: {content_type}", flush=True)
            print(f"  - Supabase URL: {supabase_url}", flush=True)
            
            # Check what key we're actually using
            current_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_ANON_KEY", "").strip()
            if current_key:
                print(f"  - Using key prefix: {current_key[:30]}... (length: {len(current_key)})", flush=True)
            
            response = supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": content_type
                }
            )

            print(f"[SUPABASE_STORAGE] Upload response type: {type(response)}, Response: {response}", flush=True)
            
            # Log full response details for debugging
            if hasattr(response, '__dict__'):
                print(f"[SUPABASE_STORAGE] Response attributes: {list(response.__dict__.keys())}", flush=True)
            if isinstance(response, dict):
                print(f"[SUPABASE_STORAGE] Response keys: {list(response.keys())}", flush=True)

            # Check response - handle both dict and object responses
            # Response might be a dict with 'error' key or an object with error attribute
            has_error = False
            error_msg = None

            if isinstance(response, dict):
                has_error = 'error' in response and response['error']
                error_msg = response.get('error', 'Unknown error') if has_error else None
            elif hasattr(response, 'error'):
                has_error = response.error is not None
                error_msg = str(response.error) if has_error else None
            elif hasattr(response, '__dict__') and 'error' in response.__dict__:
                has_error = response.__dict__['error'] is not None
                error_msg = str(response.__dict__['error']) if has_error else None

            if has_error and error_msg:
                print(f"[SUPABASE_STORAGE ERROR] Upload failed: {error_msg}", flush=True)
                return False, f"Supabase Storage upload failed: {error_msg}"

            # If response is successful, construct public URL
            # Format: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
            public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"

            print(f"[SUPABASE_STORAGE] ✅ Upload successful: {public_url}", flush=True)
            return True, public_url

        except Exception as upload_error:
            # Handle specific Supabase errors (including StorageException)
            error_msg = str(upload_error)
            error_type = type(upload_error).__name__
            
            # Get full error details
            import traceback
            traceback_str = traceback.format_exc()
            
            print(f"[SUPABASE_STORAGE ERROR] ========== UPLOAD FAILED ==========", flush=True)
            print(f"[SUPABASE_STORAGE ERROR] Exception type: {error_type}", flush=True)
            print(f"[SUPABASE_STORAGE ERROR] Error message: {error_msg}", flush=True)
            print(f"[SUPABASE_STORAGE ERROR] Full traceback:", flush=True)
            print(traceback_str, flush=True)
            
            # Check what key was actually used
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
            print(f"[SUPABASE_STORAGE ERROR] Environment check at error time:", flush=True)
            print(f"  - SUPABASE_SERVICE_ROLE_KEY set: {bool(service_role_key)} (length: {len(service_role_key) if service_role_key else 0})", flush=True)
            print(f"  - SUPABASE_ANON_KEY set: {bool(anon_key)} (length: {len(anon_key) if anon_key else 0})", flush=True)
            if service_role_key:
                print(f"  - Service role key prefix: {service_role_key[:30]}...", flush=True)
            print(f"[SUPABASE_STORAGE ERROR] =====================================", flush=True)
            
            # Upload error to logs bucket
            try:
                from src.storage.log_storage import log_error
                log_error(
                    error_message=error_msg,
                    error_type=f"SupabaseStorage{error_type}",
                    traceback=traceback_str,
                    context={
                        "bucket_name": bucket_name,
                        "storage_path": storage_path,
                        "filename": filename,
                        "file_size": len(file_data),
                    },
                    user_id=user_id,
                )
            except Exception as log_error_exception:
                print(f"[SUPABASE_STORAGE ERROR] Failed to log error to storage: {log_error_exception}", flush=True)

            # Check for specific error patterns
            error_lower = error_msg.lower()
            if "bucket" in error_lower and ("not found" in error_lower or "does not exist" in error_lower):
                return False, f"Bucket '{bucket_name}' not found. Please create it in Supabase Storage dashboard and make it public."
            elif "row-level security" in error_lower or "policy" in error_lower or "permission" in error_lower or "403" in error_msg:
                # Check if we're using service role key
                service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
                if not service_role_key:
                    return False, f"❌ Permission denied (403): Storage policies blocking upload. SOLUTION: Set SUPABASE_SERVICE_ROLE_KEY in Render environment variables to bypass RLS policies. Get it from Supabase Dashboard → Settings → API → service_role key."
                else:
                    return False, f"❌ Permission denied (403): Even with service role key, upload blocked. Check: 1) SUPABASE_SERVICE_ROLE_KEY is correct, 2) Bucket '{bucket_name}' exists and is public, 3) Storage policies allow uploads."
            elif "unauthenticated" in error_lower or "unauthorized" in error_lower or "401" in error_msg:
                return False, f"❌ Authentication failed (401): Please check SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is correct. Get keys from Supabase Dashboard → Settings → API."
            elif "404" in error_msg:
                return False, f"Bucket or path not found (404). Please verify: 1) Bucket '{bucket_name}' exists and is public, 2) Storage path is valid."
            elif "network" in error_lower or "connection" in error_lower or "timeout" in error_lower:
                return False, f"Network error: Could not connect to Supabase. Please check SUPABASE_URL is correct and network connectivity."

            return False, f"Upload failed ({error_type}): {error_msg}. Check server logs for details."

    except Exception as e:
        error_msg = f"Supabase Storage upload error: {str(e)}"
        print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        return False, error_msg


def move_supabase_object(
    from_path: str,
    to_path: str,
    bucket_name: str = "listing-images",
) -> Tuple[bool, str]:
    """
    Move an object within a Supabase Storage bucket.

    Args:
        from_path: Existing path in bucket (e.g., "temp/{user_id}/{session_id}/photo.jpg")
        to_path: Destination path in bucket (e.g., "{user_id}/{listing_uuid}/photo.jpg")
        bucket_name: Bucket name (default: "listing-images")

    Returns:
        (success: bool, url_or_error: str)
        - On success: Returns public URL for the new location
        - On failure: Returns error message string
    """
    try:
        supabase = _get_supabase_storage_client()
        if not supabase:
            return False, "Supabase client not configured"

        supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        if not supabase_url:
            return False, "SUPABASE_URL not configured in environment variables"

        print(f"[SUPABASE_STORAGE] Moving object from '{from_path}' to '{to_path}' in bucket '{bucket_name}'", flush=True)

        response = supabase.storage.from_(bucket_name).move(from_path, to_path)
        print(f"[SUPABASE_STORAGE] Move response: {response}", flush=True)

        # Best-effort error detection
        has_error = False
        error_msg = None
        if isinstance(response, dict):
            has_error = "error" in response and response["error"]
            error_msg = response.get("error") if has_error else None
        elif hasattr(response, "error"):
            has_error = response.error is not None
            error_msg = str(response.error) if has_error else None

        if has_error:
            print(f"[SUPABASE_STORAGE ERROR] Move failed: {error_msg}", flush=True)
            return False, f"Supabase Storage move failed: {error_msg}"

        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{to_path}"
        print(f"[SUPABASE_STORAGE] ✅ Move successful: {public_url}", flush=True)
        return True, public_url

    except Exception as e:
        error_msg = f"Supabase Storage move error: {str(e)}"
        print(f"[SUPABASE_STORAGE ERROR] {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        return False, error_msg


def get_supabase_storage_url(
    storage_path: str,
    bucket_name: str = "listing-images"
) -> str:
    """
    Get public URL for a file in Supabase Storage.
    
    Args:
        storage_path: Path in bucket (e.g., "{user_id}/{listing_uuid}/photo.jpg")
        bucket_name: Bucket name (default: "listing-images")
    
    Returns:
        Public URL string
    """
    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
    if not supabase_url:
        raise ValueError("SUPABASE_URL not configured")
    
    return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"

