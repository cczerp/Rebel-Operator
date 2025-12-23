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
        return None
    
    # Try service role key first (bypasses RLS policies)
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if service_role_key:
        try:
            print(f"[SUPABASE_STORAGE] ✅ Using service role key for storage operations (bypasses RLS)", flush=True)
            return Client(
                supabase_url,
                service_role_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
        except Exception as e:
            print(f"[SUPABASE_STORAGE] Service role key failed, trying anon key: {e}", flush=True)
    
    # Fallback to anon key (requires proper storage policies)
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if anon_key:
        try:
            print(f"[SUPABASE_STORAGE] ⚠️  Using anon key (may require storage policies)", flush=True)
            return Client(
                supabase_url,
                anon_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
        except Exception as e:
            print(f"[SUPABASE_STORAGE] Anon key failed: {e}", flush=True)
    
    return None


def upload_to_supabase_storage(
    file_data: bytes,
    filename: str,
    user_id: str,
    listing_uuid: Optional[str] = None,
    bucket_name: str = "listing-images"
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
        supabase = _get_supabase_storage_client()
        if not supabase:
            print(f"[SUPABASE_STORAGE ERROR] Supabase client not configured - check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY", flush=True)
            return False, "Supabase client not configured. Please check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) environment variables."

        # Get and validate SUPABASE_URL early
        supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
        if not supabase_url:
            print(f"[SUPABASE_STORAGE ERROR] SUPABASE_URL not configured", flush=True)
            return False, "SUPABASE_URL not configured in environment variables"

        # Namespace path by user_id per system contract
        # Format: {user_id}/{listing_uuid}/{filename} or {user_id}/{filename}
        if listing_uuid:
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

        # Upload to Supabase Storage
        # Supabase Python client API: storage.from_(bucket).upload(path, file_bytes, file_options)
        try:
            print(f"[SUPABASE_STORAGE] Attempting upload - File size: {len(file_data)} bytes, Content-Type: {content_type}", flush=True)

            # Convert bytes to file-like object if needed, or use bytes directly
            # Supabase expects file_data as bytes or file-like object
            response = supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": False  # Don't overwrite existing files (boolean, not string)
                }
            )

            print(f"[SUPABASE_STORAGE] Upload response type: {type(response)}, Response: {response}", flush=True)

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
            print(f"[SUPABASE_STORAGE ERROR] Upload exception ({error_type}): {error_msg}", flush=True)

            # Check for specific error patterns
            if "bucket" in error_msg.lower() and ("not found" in error_msg.lower() or "does not exist" in error_msg.lower()):
                return False, f"Bucket '{bucket_name}' not found. Please create it in Supabase Storage dashboard."
            elif "row-level security" in error_msg.lower() or "policy" in error_msg.lower():
                return False, f"Permission denied: Storage policies blocking upload. Set SUPABASE_SERVICE_ROLE_KEY to bypass RLS, or configure storage policies in Supabase dashboard."
            elif "unauthenticated" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return False, f"Authentication failed: Please check SUPABASE_ANON_KEY is correct."

            return False, f"Upload failed ({error_type}): {error_msg}"

    except Exception as e:
        error_msg = f"Supabase Storage upload error: {str(e)}"
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

