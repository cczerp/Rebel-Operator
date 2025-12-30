"""
Supabase Storage Manager
========================
Handles photo uploads to Supabase Storage buckets.

Environment Variables:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_KEY: Your Supabase anon/service key
- SUPABASE_BUCKET_TEMP: Bucket name for temporary uploads (default: 'temp-photos')
- SUPABASE_BUCKET_DRAFTS: Bucket name for saved draft photos (default: 'draft-images')
- SUPABASE_BUCKET_LISTINGS: Bucket name for posted listing photos (default: 'listing-images')
"""

import os
from typing import Optional, Tuple, List
from pathlib import Path
import uuid
import io
import logging

logger = logging.getLogger(__name__)


class SupabaseStorageManager:
    """Manages photo storage using Supabase Storage buckets"""

    def __init__(self):
        """Initialize Supabase Storage client"""
        try:
            from supabase import create_client, Client
            
            self.supabase_url = os.getenv('SUPABASE_URL', '').strip()
            
            # For server-side operations, ALWAYS use service_role key (bypasses RLS)
            # This is required for server-side uploads to work without RLS policies
            self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
            
            if not self.supabase_key:
                # Fallback warning - but service_role should be set
                logger.warning("SUPABASE_SERVICE_ROLE_KEY not found, trying SUPABASE_KEY as fallback")
                self.supabase_key = (os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or '').strip()
                if self.supabase_key:
                    logger.warning("⚠️ Using SUPABASE_KEY/SUPABASE_ANON_KEY - uploads may fail due to RLS policies. Set SUPABASE_SERVICE_ROLE_KEY instead.")
            
            if not self.supabase_url or not self.supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment for server-side uploads"
                )
            
            # Log which key type we're using (for debugging)
            if os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
                logger.info("✅ Using SUPABASE_SERVICE_ROLE_KEY (bypasses RLS - correct for server-side)")
            else:
                logger.warning("⚠️ SUPABASE_SERVICE_ROLE_KEY not set - using fallback key (may fail with RLS)")
            
            # Initialize Supabase client
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            
            # Bucket names (strip whitespace to prevent newline issues)
            self.temp_bucket = os.getenv('SUPABASE_BUCKET_TEMP', 'temp-photos').strip()
            self.drafts_bucket = os.getenv('SUPABASE_BUCKET_DRAFTS', 'draft-images').strip()
            self.listings_bucket = os.getenv('SUPABASE_BUCKET_LISTINGS', 'listing-images').strip()
            
            logger.info(f"✅ Supabase Storage initialized")
            logger.info(f"   Temp bucket: {self.temp_bucket}")
            logger.info(f"   Drafts bucket: {self.drafts_bucket}")
            logger.info(f"   Listings bucket: {self.listings_bucket}")
            
        except ImportError:
            raise ImportError("supabase package not installed. Run: pip install supabase")
        except Exception as e:
            logger.error(f"❌ Supabase Storage initialization failed: {e}")
            raise

    def upload_photo(
        self,
        file_data: bytes,
        filename: Optional[str] = None,
        folder: str = 'temp',
        content_type: str = 'image/jpeg'
    ) -> Tuple[bool, str]:
        """
        Upload a photo to Supabase Storage.

        Args:
            file_data: Image file bytes
            filename: Optional custom filename (will generate UUID if not provided)
            folder: 'temp' for temporary uploads, 'drafts' for saved drafts, 'listings' for posted listings
            content_type: MIME type (image/jpeg, image/png, etc.)

        Returns:
            (success: bool, public_url: str)
        """
        try:
            # Determine bucket
            if folder == 'temp':
                bucket = self.temp_bucket
            elif folder == 'listings':
                bucket = self.listings_bucket
            else:  # 'drafts' or default
                bucket = self.drafts_bucket
            
            # Generate filename if not provided
            if not filename:
                # Determine extension from content_type
                ext_map = {
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'image/webp': '.webp'
                }
                ext = ext_map.get(content_type, '.jpg')
                filename = f"{uuid.uuid4().hex}{ext}"
            
            # Strip any whitespace/newlines from filename and bucket
            filename = filename.strip()
            bucket = bucket.strip()
            
            # Upload to Supabase Storage
            # Ensure file_data is bytes (Supabase SDK accepts bytes or file-like objects)
            if not isinstance(file_data, bytes):
                if hasattr(file_data, 'read'):
                    # It's a file-like object, read it
                    file_data = file_data.read()
                elif isinstance(file_data, (str, int, bool)):
                    # Invalid type - log and return error
                    logger.error(f"Invalid file_data type: {type(file_data)}, value: {file_data}")
                    return False, f"Invalid file data type: {type(file_data)}"
                else:
                    # Try to convert to bytes
                    try:
                        file_data = bytes(file_data)
                    except (TypeError, ValueError) as e:
                        logger.error(f"Could not convert file_data to bytes: {e}")
                        return False, f"Could not convert file data to bytes: {str(e)}"
            
            try:
                # Supabase Python SDK upload method
                # Try without file_options first, then with minimal options
                try:
                    # Attempt upload with content-type only
                    response = self.client.storage.from_(bucket).upload(
                        path=filename,
                        file=file_data,
                        file_options={'content-type': content_type}
                    )
                except Exception as e1:
                    # If that fails, try without file_options
                    logger.warning(f"Upload with file_options failed: {e1}, trying without options")
                    response = self.client.storage.from_(bucket).upload(
                        path=filename,
                        file=file_data
                    )
                    
            except Exception as upload_error:
                logger.error(f"Supabase upload error: {upload_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Check if error message gives us a clue
                error_str = str(upload_error)
                if 'encode' in error_str.lower() and 'bool' in error_str.lower():
                    return False, "Upload failed: Invalid data type passed to Supabase. Please check file data format."
                return False, str(upload_error)
            
            # Get public URL and strip any whitespace/newlines
            public_url = self.client.storage.from_(bucket).get_public_url(filename).strip()
            
            logger.info(f"✅ Uploaded {filename} to {bucket}")
            return True, public_url
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False, str(e)

    def download_photo(self, public_url: str) -> Optional[bytes]:
        """
        Download a photo from Supabase Storage by URL.

        Args:
            public_url: Public URL of the image

        Returns:
            Image bytes or None if download fails
        """
        try:
            # Extract bucket and path from URL
            # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
            parts = public_url.split('/')
            if 'public' not in parts:
                logger.error(f"Invalid Supabase Storage URL: {public_url}")
                return None
            
            public_idx = parts.index('public')
            bucket = parts[public_idx + 1]
            path = '/'.join(parts[public_idx + 2:])
            
            # Download file
            response = self.client.storage.from_(bucket).download(path)
            
            if isinstance(response, bytes):
                return response
            else:
                # If response is a file-like object, read it
                if hasattr(response, 'read'):
                    return response.read()
                return None
                
        except Exception as e:
            logger.error(f"❌ Download failed for {public_url}: {e}")
            return None

    def move_photo(
        self,
        source_url: str,
        destination_folder: str,
        new_filename: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Move a photo from one bucket to another (or rename within bucket).

        Args:
            source_url: Public URL of source image
            destination_folder: 'drafts' to move to drafts bucket, 'listings' to move to listings bucket
            new_filename: Optional new filename (will use original if not provided)

        Returns:
            (success: bool, new_public_url: str)
        """
        try:
            # Download from source
            file_data = self.download_photo(source_url)
            if not file_data:
                return False, "Failed to download source image"
            
            # Determine destination bucket
            if destination_folder == 'listings':
                dest_bucket = self.listings_bucket
            elif destination_folder == 'drafts':
                dest_bucket = self.drafts_bucket
            else:
                dest_bucket = self.temp_bucket
            
            # Extract original filename from URL
            if not new_filename:
                parts = source_url.split('/')
                new_filename = parts[-1]
            
            # Upload to destination
            # Determine content type from filename
            ext = Path(new_filename).suffix.lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = content_type_map.get(ext, 'image/jpeg')
            
            success, new_url = self.upload_photo(
                file_data=file_data,
                filename=new_filename,
                folder=destination_folder,
                content_type=content_type
            )
            
            if success:
                # Delete from source
                self.delete_photo(source_url)
                return True, new_url
            else:
                return False, new_url
                
        except Exception as e:
            logger.error(f"❌ Move failed: {e}")
            return False, str(e)

    def delete_photo(self, public_url: str) -> bool:
        """
        Delete a photo from Supabase Storage.

        Args:
            public_url: Public URL of the image to delete

        Returns:
            success: bool
        """
        try:
            # Extract bucket and path from URL
            parts = public_url.split('/')
            if 'public' not in parts:
                logger.error(f"Invalid Supabase Storage URL: {public_url}")
                return False
            
            public_idx = parts.index('public')
            bucket = parts[public_idx + 1]
            path = '/'.join(parts[public_idx + 2:])
            
            # Delete file
            response = self.client.storage.from_(bucket).remove([path])
            
            logger.info(f"✅ Deleted {path} from {bucket}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Delete failed for {public_url}: {e}")
            return False

    def delete_multiple_photos(self, public_urls: List[str]) -> int:
        """
        Delete multiple photos from Supabase Storage.

        Args:
            public_urls: List of public URLs to delete

        Returns:
            Number of successfully deleted photos
        """
        deleted = 0
        for url in public_urls:
            if self.delete_photo(url):
                deleted += 1
        return deleted

    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Get public URL for a file in Supabase Storage.

        Args:
            bucket: Bucket name
            path: File path within bucket

        Returns:
            Public URL (stripped of whitespace)
        """
        # Strip whitespace to prevent newline issues
        bucket = bucket.strip()
        path = path.strip()
        return self.client.storage.from_(bucket).get_public_url(path).strip()

    def list_temp_photos(self, user_id: Optional[int] = None) -> List[str]:
        """
        List all photos in temp bucket (for cleanup).

        Args:
            user_id: Optional user ID to filter (if filenames include user ID)

        Returns:
            List of public URLs
        """
        try:
            # List files in temp bucket
            files = self.client.storage.from_(self.temp_bucket).list()
            
            urls = []
            for file in files:
                if file.get('name'):
                    url = self.get_public_url(self.temp_bucket, file['name'])
                    urls.append(url)
            
            return urls
            
        except Exception as e:
            logger.error(f"❌ List temp photos failed: {e}")
            return []


# Global instance
_storage = None

def get_supabase_storage() -> SupabaseStorageManager:
    """Get the global Supabase Storage manager instance"""
    global _storage
    if _storage is None:
        _storage = SupabaseStorageManager()
    return _storage

