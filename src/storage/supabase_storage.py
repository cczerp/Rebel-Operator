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


def upload_to_supabase_storage(
    file_data: bytes,
    filename: str,
    user_id: str,
    listing_uuid: Optional[str] = None,
    bucket_name: str = "listing-images"
) -> Tuple[bool, str]:
    """
    Upload a file to Supabase Storage bucket.
    
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
        from src.auth_utils import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return False, "Supabase client not configured"
        
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
            response = supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": "false"  # Don't overwrite existing files
                }
            )
            
            # Check response - Supabase returns dict with 'error' key if failed
            if isinstance(response, dict) and response.get('error'):
                error_msg = response.get('error', 'Unknown error')
                print(f"[SUPABASE_STORAGE ERROR] Upload failed: {error_msg}", flush=True)
                return False, f"Upload failed: {error_msg}"
            
            # If response is successful, it may be None or a dict without error
            # Get public URL
            supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
            if not supabase_url:
                return False, "SUPABASE_URL not configured"
            
            # Construct public URL
            # Format: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
            public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
            
            print(f"[SUPABASE_STORAGE] ✅ Upload successful: {public_url}", flush=True)
            return True, public_url
            
        except Exception as upload_error:
            # Handle specific Supabase errors
            error_msg = str(upload_error)
            print(f"[SUPABASE_STORAGE ERROR] Upload exception: {error_msg}", flush=True)
            
            # Check if bucket doesn't exist
            if "bucket" in error_msg.lower() or "not found" in error_msg.lower():
                return False, f"Bucket '{bucket_name}' not found. Please create it in Supabase Storage."
            
            return False, f"Upload failed: {error_msg}"
        
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

