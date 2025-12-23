"""
Platform Image Transfer Utilities
==================================
Handles downloading images from Supabase Storage and preparing them
for upload to marketplace platforms.

This module ensures images are properly transferred when publishing
listings from drafts to active status on external platforms.
"""

import io
import requests
from typing import List, Tuple, Optional
from PIL import Image


class ImageTransferHelper:
    """Helper class for transferring images between storage and platforms"""

    @staticmethod
    def download_image_from_url(image_url: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Download an image from a URL (e.g., Supabase Storage).

        Args:
            image_url: Public URL to the image

        Returns:
            Tuple of (success, image_bytes, error_message)
            - (True, bytes, None) on success
            - (False, None, error_msg) on failure
        """
        try:
            print(f"[IMAGE_TRANSFER] Downloading image from: {image_url}", flush=True)

            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            print(f"[IMAGE_TRANSFER] ✅ Downloaded {len(image_bytes)} bytes", flush=True)

            return True, image_bytes, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to download image: {str(e)}"
            print(f"[IMAGE_TRANSFER ERROR] {error_msg}", flush=True)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error downloading image: {str(e)}"
            print(f"[IMAGE_TRANSFER ERROR] {error_msg}", flush=True)
            return False, None, error_msg

    @staticmethod
    def download_multiple_images(image_urls: List[str]) -> Tuple[List[bytes], List[str]]:
        """
        Download multiple images from URLs.

        Args:
            image_urls: List of public URLs to images

        Returns:
            Tuple of (successful_images, error_messages)
            - successful_images: List of image bytes for successfully downloaded images
            - error_messages: List of error messages for failed downloads
        """
        successful_images = []
        error_messages = []

        for idx, url in enumerate(image_urls):
            print(f"[IMAGE_TRANSFER] Downloading image {idx + 1}/{len(image_urls)}", flush=True)
            success, image_bytes, error = ImageTransferHelper.download_image_from_url(url)

            if success:
                successful_images.append(image_bytes)
            else:
                error_messages.append(f"Image {idx + 1}: {error}")

        return successful_images, error_messages

    @staticmethod
    def resize_image_if_needed(
        image_bytes: bytes,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        max_size_mb: Optional[float] = None
    ) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Resize image if it exceeds platform limits.

        Args:
            image_bytes: Original image bytes
            max_width: Maximum width in pixels (None = no limit)
            max_height: Maximum height in pixels (None = no limit)
            max_size_mb: Maximum file size in MB (None = no limit)

        Returns:
            Tuple of (success, resized_bytes, error_message)
        """
        try:
            # Check file size
            size_mb = len(image_bytes) / (1024 * 1024)

            # Check if resizing is needed
            needs_resize = False
            if max_size_mb and size_mb > max_size_mb:
                needs_resize = True

            # Open image to check dimensions
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size

            if max_width and width > max_width:
                needs_resize = True
            if max_height and height > max_height:
                needs_resize = True

            # If no resize needed, return original
            if not needs_resize:
                return True, image_bytes, None

            # Calculate new dimensions
            new_width = width
            new_height = height

            if max_width and width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)

            if max_height and new_height > max_height:
                ratio = max_height / new_height
                new_height = max_height
                new_width = int(new_width * ratio)

            # Resize image
            print(f"[IMAGE_TRANSFER] Resizing image from {width}x{height} to {new_width}x{new_height}", flush=True)
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            img_format = img.format or 'JPEG'
            img.save(output, format=img_format, quality=85, optimize=True)
            resized_bytes = output.getvalue()

            new_size_mb = len(resized_bytes) / (1024 * 1024)
            print(f"[IMAGE_TRANSFER] ✅ Resized from {size_mb:.2f}MB to {new_size_mb:.2f}MB", flush=True)

            return True, resized_bytes, None

        except Exception as e:
            error_msg = f"Failed to resize image: {str(e)}"
            print(f"[IMAGE_TRANSFER ERROR] {error_msg}", flush=True)
            return False, None, error_msg

    @staticmethod
    def prepare_images_for_platform(
        image_urls: List[str],
        platform_name: str,
        platform_limits: Optional[dict] = None
    ) -> Tuple[List[bytes], List[str]]:
        """
        Download and prepare images for a specific platform.

        Args:
            image_urls: List of image URLs from Supabase Storage
            platform_name: Name of target platform (e.g., "ebay", "mercari")
            platform_limits: Optional dict with 'max_width', 'max_height', 'max_size_mb'

        Returns:
            Tuple of (prepared_images, error_messages)
        """
        print(f"[IMAGE_TRANSFER] Preparing {len(image_urls)} images for {platform_name}", flush=True)

        # Download all images
        downloaded_images, download_errors = ImageTransferHelper.download_multiple_images(image_urls)

        if not downloaded_images:
            return [], download_errors

        # Apply platform-specific limits if specified
        if not platform_limits:
            return downloaded_images, download_errors

        prepared_images = []
        all_errors = download_errors.copy()

        for idx, img_bytes in enumerate(downloaded_images):
            success, processed_bytes, error = ImageTransferHelper.resize_image_if_needed(
                img_bytes,
                max_width=platform_limits.get('max_width'),
                max_height=platform_limits.get('max_height'),
                max_size_mb=platform_limits.get('max_size_mb')
            )

            if success:
                prepared_images.append(processed_bytes)
            else:
                all_errors.append(f"Image {idx + 1} processing: {error}")

        return prepared_images, all_errors


# Platform-specific image limits
PLATFORM_IMAGE_LIMITS = {
    'ebay': {
        'max_width': 1600,
        'max_height': 1600,
        'max_size_mb': 12,
        'max_images': 24
    },
    'mercari': {
        'max_width': 2048,
        'max_height': 2048,
        'max_size_mb': 10,
        'max_images': 12
    },
    'poshmark': {
        'max_width': 2048,
        'max_height': 2048,
        'max_size_mb': 10,
        'max_images': 16
    },
    'etsy': {
        'max_width': 3000,
        'max_height': 3000,
        'max_size_mb': 10,
        'max_images': 10
    },
    'facebook': {
        'max_width': 2048,
        'max_height': 2048,
        'max_size_mb': 8,
        'max_images': 30
    }
}


def get_platform_image_limits(platform_name: str) -> dict:
    """
    Get image limits for a specific platform.

    Args:
        platform_name: Platform name (case-insensitive)

    Returns:
        Dict with image limits or default limits if platform not found
    """
    platform_key = platform_name.lower()

    if platform_key in PLATFORM_IMAGE_LIMITS:
        return PLATFORM_IMAGE_LIMITS[platform_key]

    # Default limits if platform not found
    return {
        'max_width': 2048,
        'max_height': 2048,
        'max_size_mb': 10,
        'max_images': 12
    }
