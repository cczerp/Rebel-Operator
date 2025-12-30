"""
Log Storage Manager
===================
Uploads application logs and errors to Supabase Storage bucket for centralized logging.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from src.storage.supabase_storage import _get_supabase_storage_client


def upload_log_to_storage(
    log_data: Dict[str, Any],
    log_type: str = "error",  # "error", "info", "warning", "debug"
    bucket_name: Optional[str] = None,  # Uses SUPABASE_LOGS_BUCKET env var or "logs" default
    user_id: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Upload a log entry to Supabase Storage bucket.
    
    Args:
        log_data: Dictionary containing log information
        log_type: Type of log (error, info, warning, debug)
        bucket_name: Name of the logs bucket (defaults to SUPABASE_LOGS_BUCKET env var or "logs")
        user_id: Optional user ID for namespacing
        
    Returns:
        (success: bool, url_or_error: str)
    """
    try:
        # Get bucket name from env var or use default
        # Check both SUPABASE_BUCKET_LOGS (user's preference) and SUPABASE_LOGS_BUCKET (backwards compat)
        if bucket_name is None:
            bucket_name = os.getenv("SUPABASE_BUCKET_LOGS") or os.getenv("SUPABASE_LOGS_BUCKET", "log-ride")
        
        supabase = _get_supabase_storage_client()
        if not supabase:
            # Fallback to print if Supabase not configured
            print(f"[LOG_STORAGE] Supabase not configured, logging to console: {log_data}", flush=True)
            return False, "Supabase client not configured"
        
        # Create log entry with timestamp
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type,
            "data": log_data,
            "user_id": user_id,
        }
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{log_type}/{timestamp}.json"
        if user_id:
            filename = f"{user_id}/{filename}"
        
        # Convert to JSON string
        log_json = json.dumps(log_entry, indent=2)
        log_bytes = log_json.encode('utf-8')
        
        # Upload to Supabase Storage
        # Note: file_options only accepts string values for headers
        # upsert is not a valid file_option
        response = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=log_bytes,
            file_options={
                "content-type": "application/json"
            }
        )
        
        # Check for errors
        has_error = False
        error_msg = None
        if isinstance(response, dict):
            has_error = 'error' in response and response['error']
            error_msg = response.get('error') if has_error else None
        elif hasattr(response, 'error'):
            has_error = response.error is not None
            error_msg = str(response.error) if has_error else None
        
        if has_error:
            print(f"[LOG_STORAGE ERROR] Failed to upload log: {error_msg}", flush=True)
            return False, f"Upload failed: {error_msg}"
        
        supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
        log_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{filename}"
        
        print(f"[LOG_STORAGE] ✅ Log uploaded: {log_url}", flush=True)
        return True, log_url
        
    except Exception as e:
        error_msg = f"Log storage error: {str(e)}"
        print(f"[LOG_STORAGE ERROR] {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        return False, error_msg


def log_error(
    error_message: str,
    error_type: Optional[str] = None,
    traceback: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    bucket_name: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Convenience function to log errors to Supabase Storage.
    
    Args:
        error_message: Error message
        error_type: Type of error (e.g., "UploadError", "AuthError")
        traceback: Full traceback string
        context: Additional context (request data, user info, etc.)
        user_id: User ID if available
        bucket_name: Name of logs bucket
        
    Returns:
        (success: bool, url_or_error: str)
    """
    log_data = {
        "error_message": error_message,
        "error_type": error_type,
        "traceback": traceback,
        "context": context or {},
    }
    
    return upload_log_to_storage(
        log_data=log_data,
        log_type="error",
        bucket_name=bucket_name,
        user_id=user_id,
    )


def log_info(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    bucket_name: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Convenience function to log info messages to Supabase Storage.
    """
    log_data = {
        "message": message,
        "context": context or {},
    }
    
    return upload_log_to_storage(
        log_data=log_data,
        log_type="info",
        bucket_name=bucket_name,
        user_id=user_id,
    )

