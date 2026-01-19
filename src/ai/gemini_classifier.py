"""
Gemini-based Fast Item Classification
======================================
Uses Google Gemini for quick, cost-effective item classification.
This is the PRIMARY analyzer for the "Analyze with AI" button.

Gemini handles:
- Basic item identification
- Brand/franchise detection
- Category classification
- Simple description generation
- Collectible YES/NO detection (triggers deep analysis)
- Basic value estimation
- **CARD DETECTION** - Identifies trading cards & sports cards
- **CARD CLASSIFICATION** - Extracts card-specific details

Claude handles deep collectible analysis (authentication, grading, variants).
"""

import os
import base64
import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests

from ..schema.unified_listing import Photo

logger = logging.getLogger(__name__)


class GeminiClassifier:
    """
    Fast item classifier using Google Gemini.

    This is designed for speed and cost-efficiency.
    Use for initial classification before deep collectible analysis.
    Now includes specialized card detection and classification.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini classifier with round-robin API key failover"""

        # Load all available API keys for round-robin failover
        # Priority: GEMINI_API_KEY_1 → GEMINI_API_KEY_2 → GEMINI_API_KEY_3 → legacy single key
        self.api_keys = []

        # Try loading keys 1, 2, 3 first
        for i in range(1, 4):
            key_var = f"GEMINI_API_KEY_{i}"
            raw_key = os.getenv(key_var)
            if raw_key:
                cleaned_key = raw_key.strip()
                if cleaned_key:
                    self.api_keys.append({
                        'key': cleaned_key,
                        'name': key_var,
                        'index': i
                    })
                    logger.info(f"[GEMINI KEYS] ✅ Loaded {key_var}: {cleaned_key[:5]}...{cleaned_key[-5:]}")

        # Fallback to legacy single key if numbered keys not found
        if not self.api_keys:
            legacy_raw_key = (
                api_key or
                os.getenv("GOOGLE_AI_API_KEY") or
                os.getenv("GEMINI_API_KEY") or
                os.getenv("GEMENI_API_KEY")  # Common typo
            )

            if not legacy_raw_key:
                raise ValueError(
                    "No Gemini API keys found! Set GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3 "
                    "or legacy GEMINI_API_KEY in your .env file"
                )

            cleaned_key = legacy_raw_key.strip()
            self.api_keys.append({
                'key': cleaned_key,
                'name': 'GEMINI_API_KEY (legacy)',
                'index': 0
            })
            logger.info(f"[GEMINI KEYS] ✅ Loaded legacy GEMINI_API_KEY: {cleaned_key[:5]}...{cleaned_key[-5:]}")

        # Set current key to first available (will be rotated on rate limits)
        self.current_key_index = 0
        self.api_key = self.api_keys[0]['key']

        logger.info(f"[GEMINI KEYS] 🔄 Round-robin failover enabled with {len(self.api_keys)} key(s)")
        logger.info(f"[GEMINI KEYS] 🎯 Starting with: {self.api_keys[0]['name']}")

        # Validate first key format
        if not self.api_key.startswith('AIza'):
            logger.warning(f"[GEMINI DEBUG] ⚠️ API key doesn't start with 'AIza'. May be invalid format.")

        if len(self.api_key) < 30 or len(self.api_key) > 60:
            logger.warning(f"[GEMINI DEBUG] ⚠️ API key length unusual: {len(self.api_key)} chars (expected ~39-45)")

        # Use Gemini 2.0 Flash for speed and cost-efficiency
        # Current image-capable models (v1beta API endpoint):
        # - gemini-2.0-flash-exp (DEFAULT - experimental, fast, supports images)
        # - gemini-1.5-flash-002 (stable 1.5 version)
        # - gemini-1.5-pro-002 (paid tier, better quality but costs money)
        # NOTE: gemini-2.0-flash-exp is the latest and fastest
        # IMPORTANT: Using 2.0 FLASH for latest features and better performance
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        # Use v1beta endpoint for Gemini models
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _prepare_image_for_gemini(self, image_path: str) -> tuple[bytes, str]:
        """
        Validate and convert image to Gemini-compatible format.
        
        This function:
        1. Validates the image exists and is readable
        2. Detects actual format using PIL (not file extension)
        3. Converts unsupported formats (HEIC, etc.) to JPEG
        4. Resizes if dimensions exceed 20MP limit
        5. Compresses if file size exceeds 20MB
        6. Converts RGBA/transparency to RGB
        
        Returns:
            (image_bytes, mime_type) tuple
        """
        from PIL import Image
        import io
        
        try:
            # Open and validate image
            # NOTE: Image.verify() is DEPRECATED and can corrupt images
            # We'll use try/except instead to validate the image
            try:
                img = Image.open(image_path)
                # Validate by attempting to load the image data
                img.load()  # Force loading of image data to catch corruption
            except Exception as img_error:
                logger.error(f"Failed to open/load image {image_path}: {img_error}")
                raise ValueError(f"Invalid or corrupted image: {str(img_error)}")
            
            # Reopen for actual use (load() may have modified state)
            img = Image.open(image_path)
            
            # Check dimensions (20MP limit = 20,000,000 pixels)
            total_pixels = img.size[0] * img.size[1]
            if total_pixels > 20_000_000:
                # Resize to fit within 20MP
                ratio = (20_000_000 / total_pixels) ** 0.5
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {img.size} to {new_size} (20MP limit)")
            
            # Convert RGBA/LA/P to RGB (remove alpha channel for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to JPEG (most compatible format for Gemini)
            # Start with quality 85
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)  # Reset position before reading
            image_bytes = output.getvalue()
            
            # Validate JPEG was created successfully (try to open it)
            try:
                test_img = Image.open(io.BytesIO(image_bytes))
                test_img.verify()  # Quick verify
                logger.debug(f"[GEMINI DEBUG] JPEG conversion validated - {len(image_bytes)} bytes")
            except Exception as verify_error:
                logger.error(f"[GEMINI DEBUG] JPEG validation failed: {verify_error}")
                # Continue anyway - might still work
            
            # Check file size (20MB limit, but account for base64 overhead ~33%)
            # So we want to keep under ~15MB to be safe after base64 encoding
            max_size_bytes = 15 * 1024 * 1024  # 15MB
            
            if len(image_bytes) > max_size_bytes:
                # Reduce quality if still too large
                output = io.BytesIO()
                quality = 75
                img.save(output, format='JPEG', quality=quality, optimize=True)
                output.seek(0)
                image_bytes = output.getvalue()
                
                # If still too large, reduce quality further
                if len(image_bytes) > max_size_bytes:
                    output = io.BytesIO()
                    quality = 60
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    output.seek(0)
                    image_bytes = output.getvalue()
                    logger.info(f"Reduced image quality to {quality}% to meet size limit")
            
            return image_bytes, 'image/jpeg'
            
        except Exception as e:
            logger.error(f"Failed to prepare image {image_path}: {e}")
            raise ValueError(f"Invalid or corrupted image: {str(e)}")

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Prepare and encode image for Gemini API.
        
        This validates, converts, and encodes the image to base64.
        Returns ONLY the base64 string (no data:image prefix).
        """
        image_bytes, _ = self._prepare_image_for_gemini(image_path)
        # Return base64 string WITHOUT data:image prefix (Gemini expects raw base64)
        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        
        # Ensure no data URI prefix (strip if somehow present)
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',')[1] if ',' in base64_str else base64_str
        
        return base64_str

    def _get_image_mime_type(self, image_path: str) -> str:
        """
        Get MIME type for Gemini API.
        
        Note: After _prepare_image_for_gemini, all images are converted to JPEG,
        so this always returns 'image/jpeg'. The actual format detection happens
        in _prepare_image_for_gemini.
        """
        # All images are converted to JPEG in _prepare_image_for_gemini
        return "image/jpeg"

    def analyze_item(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Fast item classification using Gemini.

        Returns:
            {
                "item_name": str,
                "brand": str,
                "franchise": str,  # e.g., "Star Wars", "MLB", "Pokemon"
                "category": str,  # electronics, toys, apparel, home_goods, etc.
                "description": str,  # simple description
                "collectible": bool,  # YES/NO - triggers deep analysis
                "collectible_confidence": float,  # 0.0 to 1.0
                "collectible_indicators": List[str],  # what triggered collectible flag
                "estimated_value_low": float,
                "estimated_value_high": float,
                "detected_keywords": List[str],
                "sku_upc": str,  # if visible
                "logos_marks": List[str],
                "condition": str,  # new, like_new, good, fair, poor
                "color": str,
                "size": str,
                "material": str,
                "suggested_title": str,
                "suggested_price": float,
            }
        """
        if not photos:
            return {"error": "No photos provided"}

        # Prepare images for Gemini (limit to 4 photos for speed)
        image_parts = []
        for i, photo in enumerate(photos[:4]):
            if photo.local_path:
                try:
                    # Debug logging (as per user's suggestion)
                    file_path = photo.local_path
                    file_exists = Path(file_path).exists()
                    file_size = Path(file_path).stat().st_size if file_exists else 0
                    
                    debug_info = {
                        'hasFile': bool(photo.local_path),
                        'filePath': file_path,
                        'exists': file_exists,
                        'fileSize': file_size,
                        'isFile': Path(file_path).is_file() if file_exists else False
                    }
                    logger.info(f"[GEMINI DEBUG] Image {i+1} before encoding: {debug_info}")
                    
                    # Validate file exists
                    if not file_exists:
                        logger.error(f"❌ Image file not found: {file_path}")
                        continue
                    
                    if file_size == 0:
                        logger.error(f"❌ Image file is empty: {file_path}")
                        continue
                    
                    # Prepare and encode image (validates, converts, encodes)
                    image_b64 = self._encode_image_to_base64(file_path)
                    mime_type = self._get_image_mime_type(file_path)  # Always 'image/jpeg' after conversion
                    
                    # Debug after encoding
                    logger.info(f"[GEMINI DEBUG] Image {i+1} after encoding: mime_type={mime_type}, base64_length={len(image_b64)}, starts_with_data={image_b64.startswith('data:')}")
                    
                    # Gemini requirement: mimeType MUST be present (non-negotiable)
                    if not mime_type:
                        mime_type = 'image/jpeg'  # Default fallback
                    
                    # Only use safe formats (Gemini sometimes rejects WebP)
                    supported_mimes = ['image/jpeg', 'image/jpg', 'image/png']
                    if mime_type not in supported_mimes:
                        logger.warning(f"Unsupported mime_type {mime_type}, using image/jpeg")
                        mime_type = 'image/jpeg'
                    
                    # Ensure base64 is clean (no data:image prefix)
                    if image_b64.startswith('data:image'):
                        logger.warning(f"⚠️ Base64 had data: prefix, stripping it")
                        image_b64 = image_b64.split(',')[1] if ',' in image_b64 else image_b64
                    
                    # Final validation before adding to payload (as per user's suggestion)
                    if not mime_type:
                        logger.error(f"❌ mime_type is missing for image {i+1}")
                        continue
                    
                    if not image_b64 or len(image_b64) == 0:
                        logger.error(f"❌ base64 data is empty for image {i+1}")
                        continue
                    
                    # Create inline_data part (Gemini requirement)
                    inline_data = {
                        "mime_type": mime_type,  # MUST be present (non-negotiable)
                        "data": image_b64  # Clean base64 string (no prefix)
                    }
                    
                    # Debug the inline_data structure
                    logger.debug(f"[GEMINI DEBUG] Image {i+1} inline_data: mime_type={inline_data['mime_type']}, data_length={len(inline_data['data'])}")
                    
                    image_parts.append({
                        "inline_data": inline_data
                    })
                    logger.info(f"✅ Prepared image {i+1}/{min(len(photos), 4)} for Gemini (mime_type: {mime_type}, data_len: {len(image_b64)})")
                    
                except Exception as e:
                    logger.error(f"Failed to prepare image {i+1}: {e}")
                    # Continue with other images instead of failing completely
                    continue
        
        if not image_parts:
            return {"error": "No valid images could be prepared for analysis"}

        # Build comprehensive classification prompt
        prompt = """Analyze these product images and provide a FAST, ACCURATE classification.

🔵 PRIMARY TASK: Item Classification

Identify:
1. Item name/type (what is this?)
2. Brand (Nike, Apple, Hasbro, etc.)
3. Franchise (Star Wars, MLB, Pokemon, Marvel, etc.)
4. Category (electronics, toys, apparel, home_goods, sports, collectibles, etc.)
5. Simple description (1-2 sentences)
6. Condition (new, like_new, good, fair, poor)
7. Color, size, material (if visible)
8. Any SKU, UPC, barcodes visible
9. Any logos, trademarks, marks
10. Detected keywords

🟢 COLLECTIBLE DETECTION (CRITICAL)

Mark collectible = TRUE if you see ANY of these:

**Brands & Franchises:**
- Pokemon (cards, toys, games, anything)
- MLB / NFL / NBA / NHL (any sports league items)
- Star Wars / Marvel / DC (any franchise items)
- Hot Wheels, Matchbox cars
- Barbie dolls
- Funko Pop figures
- Hallmark ornaments
- Disney items
- Vintage Coke, Pepsi, M&M tins
- Lego sets
- Anime merchandise
- Video game consoles or vintage games
- Magic: The Gathering, Yu-Gi-Oh cards
- Any autographed items

**Item Types:**
- Trading cards (sports, Pokemon, Magic, etc.)
- Action figures
- Vintage toys (1990s or earlier)
- Comics or graphic novels
- Coins, stamps, currency
- Sports memorabilia
- Vintage electronics
- Vintage tools
- Vintage clothing (band tees, jerseys, etc.)
- Limited edition items
- Numbered prints
- Vintage kitchenware (Pyrex, Fire King, etc.)

**Visual Traits:**
- Holographic stickers or seals
- Authentication tags or stamps
- Signatures (autographs)
- Serial numbers or edition numbers
- "Limited Edition" markings
- Vintage dates (especially 1990s or earlier)
- Protective cases or sleeves (cards, figures)
- Original packaging from collectible brands
- Team logos (Cubs, Yankees, Lakers, etc.)
- Character artwork (Pokemon, Star Wars, etc.)

**Examples that ARE collectibles:**
- Baseball card in protective case → collectible = TRUE
- Chicago Cubs jacket with MLB logo → collectible = TRUE
- Pokemon card (even common) → collectible = TRUE
- Vintage M&M tin → collectible = TRUE
- Star Wars action figure → collectible = TRUE
- Autographed photo → collectible = TRUE
- Hot Wheels in package → collectible = TRUE

**Examples that are NOT collectibles:**
- Plain white t-shirt → collectible = FALSE
- Generic coffee mug → collectible = FALSE
- Standard kitchen knife → collectible = FALSE
- Modern mass-produced clothing → collectible = FALSE

🎯 OUTPUT FORMAT

You MUST respond with ONLY valid JSON (no markdown, no explanations):

{
  "item_name": "1999 Pokemon Charizard Trading Card",
  "brand": "Pokemon",
  "franchise": "Pokemon",
  "category": "trading_cards",
  "description": "Holographic Charizard card from the 1999 Base Set, appears to be in protective sleeve.",
  "collectible": true,
  "collectible_confidence": 0.95,
  "collectible_indicators": [
    "Pokemon franchise",
    "Trading card in protective case",
    "Holographic card",
    "Vintage (1999)",
    "Charizard is highly collectible"
  ],
  "estimated_value_low": 50,
  "estimated_value_high": 500,
  "detected_keywords": ["pokemon", "charizard", "holographic", "1999", "base set"],
  "sku_upc": "",
  "logos_marks": ["Pokemon logo", "Nintendo copyright"],
  "condition": "good",
  "color": "multi-color",
  "size": "standard card",
  "material": "cardstock",
  "suggested_title": "1999 Pokemon Charizard Holographic Card - Base Set",
  "suggested_price": 150
}

OR if NOT a collectible:

{
  "item_name": "Blue Cotton T-Shirt",
  "brand": "Hanes",
  "franchise": "",
  "category": "apparel",
  "description": "Plain blue cotton t-shirt, appears to be size large.",
  "collectible": false,
  "collectible_confidence": 0.1,
  "collectible_indicators": [],
  "estimated_value_low": 5,
  "estimated_value_high": 15,
  "detected_keywords": ["t-shirt", "blue", "cotton"],
  "sku_upc": "",
  "logos_marks": ["Hanes tag"],
  "condition": "good",
  "color": "blue",
  "size": "L",
  "material": "cotton",
  "suggested_title": "Blue Hanes Cotton T-Shirt - Size L",
  "suggested_price": 10
}

IMPORTANT:
- Be AGGRESSIVE about marking collectibles
- If you see a sports logo, it's probably collectible
- If you see a franchise character, it's probably collectible
- If you see a trading card, it's DEFINITELY collectible
- When in doubt, mark collectible = true (deep analysis will verify)
- Respond with ONLY JSON, no other text
"""

        # Build request payload
        # Gemini API structure: contents[0] contains parts array with text + images
        # Each image part must have inline_data with mime_type (non-negotiable) and data (base64)
        payload = {
            "contents": [{
                "role": "user",  # Explicitly set role (best practice)
                "parts": [
                    {"text": prompt},
                    *image_parts  # Each image_parts item has inline_data with mime_type and data
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,  # Lower temp for more consistent classification
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        # Log payload structure for debugging (as per user's suggestion)
        logger.info(f"[GEMINI DEBUG] Payload structure: {len(image_parts)} images, prompt length: {len(prompt)}")
        for i, img_part in enumerate(image_parts):
            if 'inline_data' in img_part:
                inline_data = img_part['inline_data']
                mime = inline_data.get('mime_type', 'unknown')
                data = inline_data.get('data', '')
                data_len = len(data)
                has_mime = bool(mime)
                has_data = bool(data)
                is_base64 = not data.startswith('data:') if data else False
                
                logger.info(f"[GEMINI DEBUG] Image {i+1} in payload:")
                logger.info(f"  - has_inline_data: True")
                logger.info(f"  - has_mime_type: {has_mime} ({mime})")
                logger.info(f"  - has_data: {has_data} (length: {data_len})")
                logger.info(f"  - is_clean_base64: {is_base64}")
                
                if not has_mime:
                    logger.error(f"❌ Image {i+1} missing mime_type in payload!")
                if not has_data:
                    logger.error(f"❌ Image {i+1} missing data in payload!")
                if data.startswith('data:'):
                    logger.error(f"❌ Image {i+1} data still has data: prefix!")
            else:
                logger.error(f"❌ Image {i+1} missing inline_data in payload!")

        # Retry logic with round-robin API key failover
        max_retries_per_key = 2  # Try each key twice before moving to next
        base_delay = 2  # seconds (exponential backoff: 2s, 4s, 8s, 16s, 32s)
        total_attempts = 0
        max_total_attempts = len(self.api_keys) * max_retries_per_key

        for key_index in range(len(self.api_keys)):
            # Switch to next key
            current_key_info = self.api_keys[key_index]
            self.api_key = current_key_info['key']
            self.current_key_index = key_index

            logger.info(f"[GEMINI KEYS] 🔑 Using {current_key_info['name']} ({current_key_info['key'][:5]}...{current_key_info['key'][-5:]})")

            for key_attempt in range(max_retries_per_key):
                total_attempts += 1

                try:
                    # CRITICAL: Gemini API ONLY wants key in query string, NO Authorization header
                    api_url_with_key = f"{self.api_url}?key={self.api_key}"

                    # Ensure headers ONLY contain Content-Type (no Authorization)
                    headers = {"Content-Type": "application/json"}

                    # Debug: Log request details (key hidden for security)
                    logger.debug(f"[GEMINI DEBUG] Request URL: {self.api_url}?key=***")
                    logger.debug(f"[GEMINI DEBUG] Using key: {current_key_info['name']}")
                    logger.debug(f"[GEMINI DEBUG] Attempt {total_attempts}/{max_total_attempts}")

                    response = requests.post(
                        api_url_with_key,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        # Check if response is actually JSON (not HTML error page)
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/json' not in content_type:
                            logger.error(f"[GEMINI ERROR] Response is not JSON! Content-Type: {content_type}")
                            logger.error(f"[GEMINI ERROR] Response text (first 500 chars): {response.text[:500]}")
                            return {
                                "error": f"Gemini API returned non-JSON response (Content-Type: {content_type}). This usually means the API endpoint is wrong or the API key is invalid.",
                                "error_type": "invalid_response",
                                "details": response.text[:500]
                            }

                        try:
                            result = response.json()
                        except json.JSONDecodeError as e:
                            logger.error(f"[GEMINI ERROR] Failed to parse JSON response: {e}")
                            logger.error(f"[GEMINI ERROR] Response text (first 500 chars): {response.text[:500]}")
                            # Check if it's HTML
                            if response.text.strip().startswith('<'):
                                return {
                                    "error": "Gemini API returned HTML instead of JSON. This usually means the API endpoint is wrong, the API key is invalid, or there's a network issue.",
                                    "error_type": "html_response",
                                    "details": response.text[:500]
                                }
                            return {
                                "error": f"Failed to parse Gemini API response as JSON: {str(e)}",
                                "error_type": "json_parse_error",
                                "details": response.text[:500]
                            }

                        # Extract text from Gemini response
                        try:
                            content_text = result["candidates"][0]["content"]["parts"][0]["text"]
                        except (KeyError, IndexError) as e:
                            logger.error(f"[GEMINI ERROR] Unexpected response structure: {e}")
                            logger.error(f"[GEMINI ERROR] Full response: {json.dumps(result, indent=2)}")
                            return {
                                "error": f"Unexpected Gemini response structure: {str(e)}",
                                "raw_response": result
                            }

                        # Parse JSON response
                        try:
                            # Clean up any markdown formatting
                            if "```json" in content_text:
                                content_text = content_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in content_text:
                                content_text = content_text.split("```")[1].split("```")[0].strip()

                            analysis = json.loads(content_text)
                            analysis["ai_provider"] = "gemini"
                            analysis["api_key_used"] = current_key_info['name']  # Track which key worked
                            logger.info(f"[GEMINI KEYS] ✅ Success with {current_key_info['name']}")
                            return analysis

                        except json.JSONDecodeError as e:
                            return {
                                "error": f"JSON parse error: {str(e)}",
                                "raw_response": content_text
                            }

                    # Handle rate limit errors (429) and service overload (503) - try next key
                    elif response.status_code in [429, 503]:
                        error_type = "rate_limit" if response.status_code == 429 else "service_overload"

                        logger.warning(f"⚠️ {current_key_info['name']} hit {response.status_code} ({error_type})")

                        # If this is the last retry for this key, move to next key
                        if key_attempt == max_retries_per_key - 1:
                            if key_index < len(self.api_keys) - 1:
                                logger.info(f"[GEMINI KEYS] 🔄 Switching to next API key...")
                                break  # Break inner loop to try next key
                            else:
                                # Last key exhausted, give up
                                logger.error(f"❌ All {len(self.api_keys)} API keys exhausted!")
                                return {
                                    "error": f"All {len(self.api_keys)} Gemini API keys are rate-limited or overloaded. Please wait 1-2 minutes before trying again.",
                                    "error_type": error_type,
                                    "status_code": response.status_code,
                                    "keys_tried": len(self.api_keys),
                                    "retry_after": 120,
                                    "tips": [
                                        f"All {len(self.api_keys)} API keys hit rate limits",
                                        "Wait 1-2 minutes before trying again",
                                        "Try during off-peak hours (late night/early morning)",
                                        "Consider adding more API keys or upgrading to paid tier"
                                    ]
                                }
                        else:
                            # Retry with same key after delay
                            delay = base_delay * (2 ** key_attempt)
                            logger.warning(f"⚠️ Retrying with same key in {delay}s... (attempt {key_attempt + 1}/{max_retries_per_key})")
                            print(f"⚠️ Gemini API overloaded. Retrying in {delay} seconds...")
                            time.sleep(delay)
                            continue

                    # Handle other API errors
                    else:
                        # Log error details
                        error_msg_full = response.text
                        error_msg_short = error_msg_full[:500] if len(error_msg_full) > 500 else error_msg_full

                        logger.error(f"[GEMINI ERROR] {response.status_code} error with {current_key_info['name']}")
                        logger.error(f"[GEMINI ERROR] Response: {error_msg_short}")

                        # For 403 (auth errors), try next key immediately
                        if response.status_code == 403:
                            logger.warning(f"⚠️ {current_key_info['name']} authentication failed (403)")
                            if key_index < len(self.api_keys) - 1:
                                logger.info(f"[GEMINI KEYS] 🔄 Key invalid, switching to next API key...")
                                break  # Try next key
                            else:
                                return {
                                    "error": f"All {len(self.api_keys)} Gemini API keys failed authentication. Please check your API keys are valid.",
                                    "error_type": "auth_error",
                                    "keys_tried": len(self.api_keys)
                                }

                        # For 400 errors, return immediately (bad request, not a key issue)
                        if response.status_code == 400:
                            return {
                                "error": "Invalid request to Gemini API. Please check your photos are valid images.",
                                "error_type": "bad_request",
                                "details": error_msg_short
                            }

                        # For 500+ errors, retry
                        if response.status_code >= 500:
                            if key_attempt < max_retries_per_key - 1:
                                delay = base_delay * (2 ** key_attempt)
                                logger.warning(f"⚠️ Server error, retrying in {delay}s...")
                                time.sleep(delay)
                                continue
                            else:
                                # Try next key on server errors
                                if key_index < len(self.api_keys) - 1:
                                    break
                                else:
                                    return {
                                        "error": "Gemini API is experiencing server issues. Please try again later.",
                                        "error_type": "server_error"
                                    }

                        # Other errors
                        return {
                            "error": f"Gemini API error ({response.status_code}): {error_msg_short}",
                            "error_type": "unknown"
                        }

                except requests.Timeout:
                    logger.warning(f"⚠️ Request timeout with {current_key_info['name']}")
                    if key_attempt < max_retries_per_key - 1:
                        delay = base_delay * (2 ** key_attempt)
                        logger.warning(f"⚠️ Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        # Try next key on timeout
                        if key_index < len(self.api_keys) - 1:
                            break
                        else:
                            return {
                                "error": "Request to Gemini API timed out. Please check your internet connection.",
                                "error_type": "timeout"
                            }

                except Exception as e:
                    logger.error(f"[GEMINI ERROR] Exception with {current_key_info['name']}: {str(e)}")
                    if key_attempt < max_retries_per_key - 1:
                        delay = base_delay * (2 ** key_attempt)
                        logger.warning(f"⚠️ Exception, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        # Try next key on exception
                        if key_index < len(self.api_keys) - 1:
                            logger.info(f"[GEMINI KEYS] 🔄 Exception occurred, trying next key...")
                            break
                        else:
                            return {
                                "error": f"Error communicating with Gemini API: {str(e)}",
                                "error_type": "exception"
                            }

        # If we get here, all keys failed
        return {
            "error": f"All {len(self.api_keys)} Gemini API keys failed after {max_total_attempts} total attempts",
            "error_type": "all_keys_failed",
            "keys_tried": len(self.api_keys)
        }

    def analyze_card(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Specialized card analysis using Gemini Vision.

        Extracts card-specific details for:
        - Trading Card Games (Pokémon, MTG, Yu-Gi-Oh, etc.)
        - Sports Cards (NFL, NBA, MLB, NHL, etc.)

        Returns:
            {
                "is_card": bool,
                "card_type": str,  # 'pokemon', 'mtg', 'yugioh', 'sports_nfl', etc.
                "card_name": str,
                "player_name": str,  # For sports cards
                "card_number": str,
                "set_name": str,
                "set_code": str,
                "year": int,
                "brand": str,  # Topps, Panini, etc. (sports cards)
                "series": str,  # Prizm, Chrome, etc. (sports cards)
                "rarity": str,
                "is_rookie_card": bool,
                "is_autographed": bool,
                "is_graded": bool,
                "grading_company": str,  # PSA, BGS, CGC
                "grading_score": float,
                "parallel": str,  # Silver, Gold, etc.
                "condition": str,
                "estimated_value_low": float,
                "estimated_value_high": float,
                "confidence": float,
            }
        """
        if not photos:
            return {"error": "No photos provided", "is_card": False}

        # Prepare images for Gemini (with validation and conversion)
        image_parts = []
        for i, photo in enumerate(photos[:4]):
            if photo.local_path:
                try:
                    # Validate file exists
                    if not Path(photo.local_path).exists():
                        logger.error(f"Image file not found: {photo.local_path}")
                        continue
                    
                    # Prepare and encode image (validates, converts, encodes)
                    image_b64 = self._encode_image_to_base64(photo.local_path)
                    mime_type = self._get_image_mime_type(photo.local_path)  # Always 'image/jpeg' after conversion
                    
                    # Gemini requirement: mimeType MUST be present (non-negotiable)
                    if not mime_type:
                        mime_type = 'image/jpeg'  # Default fallback
                    
                    # Only use safe formats (Gemini sometimes rejects WebP)
                    supported_mimes = ['image/jpeg', 'image/jpg', 'image/png']
                    if mime_type not in supported_mimes:
                        logger.warning(f"Unsupported mime_type {mime_type}, using image/jpeg")
                        mime_type = 'image/jpeg'
                    
                    # Ensure base64 is clean (no data:image prefix)
                    if image_b64.startswith('data:image'):
                        image_b64 = image_b64.split(',')[1] if ',' in image_b64 else image_b64
                    
                    image_parts.append({
                        "inline_data": {
                            "mime_type": mime_type,  # MUST be present (non-negotiable)
                            "data": image_b64  # Clean base64 string (no prefix)
                        }
                    })
                    logger.info(f"✅ Prepared card image {i+1}/{min(len(photos), 4)} for Gemini (mime_type: {mime_type}, data_len: {len(image_b64)})")
                    
                except Exception as e:
                    logger.error(f"Failed to prepare card image {i+1}: {e}")
                    # Continue with other images instead of failing completely
                    continue
        
        if not image_parts:
            return {"error": "No valid images could be prepared for card analysis", "is_card": False}

        # Card-specific analysis prompt
        prompt = """Analyze this image and determine if it's a trading card or sports card.

🎴 CARD DETECTION & CLASSIFICATION

**Step 1: Is this a card?**
Look for:
- Standard card dimensions (roughly 2.5" x 3.5")
- Card in protective sleeve, top loader, or grading case
- Visible card features (borders, text, stats)
- Trading card game elements (energy symbols, mana costs, etc.)
- Sports card elements (player photo, team logo, stats on back)

**Step 2: What type of card?**

TRADING CARD GAMES:
- Pokemon: Look for Pokemon logo, energy symbols, HP, attacks
- Magic: The Gathering (MTG): Look for mana symbols, card types, expansion symbols
- Yu-Gi-Oh!: Look for ATK/DEF numbers, card types (Monster/Spell/Trap)
- One Piece, Dragon Ball, etc.

SPORTS CARDS:
- NFL: Football players, team logos, NFL shield
- NBA: Basketball players, team logos, NBA logo
- MLB: Baseball players, team logos, MLB logo
- NHL: Hockey players, team logos, NHL logo
- Soccer: Players, team crests, league logos

**Step 3: Extract Details**

For TCG Cards:
- Card name (at top of card)
- Set symbol (bottom right, or expansion mark)
- Card number (usually bottom: "12/102" format)
- Rarity (star, circle, diamond, or text like "Rare", "Ultra Rare")
- Set name if visible

For Sports Cards:
- Player name
- Year (usually on front or back)
- Brand (Topps, Panini, Upper Deck, Donruss, Fleer, Bowman)
- Series (Prizm, Chrome, Optic, Select, etc.)
- Card number
- Rookie Card designation ("RC" logo or text)
- Parallel/variant (Silver, Gold, Refractor, etc.)
- Team and position

**Step 4: Grading & Condition**

Check for:
- PSA, BGS, CGC grading case (plastic slab)
- Grading score (1-10 scale)
- Serial number on case
- If ungraded: estimate condition (Mint, Near Mint, Excellent, Good, Poor)

**Step 5: Special Features**

- Autograph (signature on card)
- Rookie card (RC designation)
- Limited edition / numbered (e.g., "5/99")
- Holographic / foil finish
- Insert set designation

**Step 6: Value Estimation**

Provide rough market value based on:
- Player/character popularity
- Card rarity
- Condition/grade
- Year (vintage vs modern)
- Market demand

OUTPUT FORMAT (JSON only, no markdown):

For a CARD:
{
  "is_card": true,
  "card_type": "pokemon",
  "card_name": "Charizard",
  "player_name": "",
  "card_number": "4/102",
  "set_name": "Base Set",
  "set_code": "BS",
  "year": 1999,
  "brand": "",
  "series": "",
  "rarity": "Rare Holo",
  "is_rookie_card": false,
  "is_autographed": false,
  "is_graded": true,
  "grading_company": "PSA",
  "grading_score": 9.0,
  "parallel": "",
  "condition": "Mint",
  "estimated_value_low": 2000,
  "estimated_value_high": 5000,
  "confidence": 0.95
}

For a SPORTS CARD:
{
  "is_card": true,
  "card_type": "sports_nfl",
  "card_name": "Tom Brady Rookie Card",
  "player_name": "Tom Brady",
  "card_number": "236",
  "set_name": "2000 Playoff Contenders",
  "set_code": "",
  "year": 2000,
  "brand": "Playoff",
  "series": "Contenders",
  "rarity": "Rookie Ticket Autograph",
  "is_rookie_card": true,
  "is_autographed": true,
  "is_graded": true,
  "grading_company": "PSA",
  "grading_score": 10.0,
  "parallel": "",
  "condition": "Gem Mint",
  "estimated_value_low": 100000,
  "estimated_value_high": 500000,
  "confidence": 0.98
}

For NOT A CARD:
{
  "is_card": false,
  "confidence": 0.95
}

Analyze the image(s) now and respond with ONLY the JSON."""

        # Combine text + images
        content = [{"text": prompt}]
        content.extend(image_parts)

        # Build request payload
        # Gemini API structure: contents[0] contains parts array with text + images
        # Each image part must have inline_data with mime_type (non-negotiable) and data (base64)
        payload = {
            "contents": [{
                "role": "user",  # Explicitly set role (best practice)
                "parts": content  # Array with text + image parts
            }],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for factual extraction
                "maxOutputTokens": 1024,
            }
        }
        
        # Log payload structure for debugging (without full base64 data)
        logger.debug(f"Card analysis payload: {len(image_parts)} images, prompt length: {len(prompt)}")
        for i, img_part in enumerate(image_parts):
            if 'inline_data' in img_part:
                mime = img_part['inline_data'].get('mime_type', 'unknown')
                data_len = len(img_part['inline_data'].get('data', ''))
                logger.debug(f"  Card image {i+1}: mime_type={mime}, data_length={data_len}")

        try:
            # CRITICAL: Gemini API ONLY wants key in query string, NO Authorization header
            api_url_with_key = f"{self.api_url}?key={self.api_key}"
            headers = {"Content-Type": "application/json"}  # ONLY Content-Type, NO Authorization
            
            response = requests.post(
                api_url_with_key,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']

                # Parse JSON response
                content_text = content_text.strip()
                if content_text.startswith('```json'):
                    content_text = content_text[7:-3].strip()
                elif content_text.startswith('```'):
                    content_text = content_text[3:-3].strip()

                card_data = json.loads(content_text)
                return card_data

            else:
                return {
                    "error": f"Gemini API error: {response.status_code}",
                    "is_card": False
                }

        except Exception as e:
            return {
                "error": f"Card analysis failed: {str(e)}",
                "is_card": False
            }

    def analyze_collectible_detailed(self, photos: List[Photo], basic_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detailed collectible analysis using Gemini with the comprehensive prompt.
        
        Extracts detailed collector attributes:
        - Mint marks (coin mint locations, production facility marks)
        - Serial numbers (production numbers, limited edition numbers)
        - Signatures (autographs with authenticity assessment)
        - Errors/variations (error coins, misprints, factory defects)
        - Historical context (backstory, significance, rarity context)
        - Authentication markers
        - Condition grading
        - Market analysis
        
        Args:
            photos: List of Photo objects to analyze
            basic_analysis: Optional basic analysis from quick scan (item_name, brand, franchise, category)
        
        Returns:
            Detailed collectible analysis with all collector attributes
        """
        if not photos:
            return {"error": "No photos provided"}
        
        # Get basic info from provided analysis or set defaults
        if basic_analysis:
            item_name = basic_analysis.get('suggested_title') or basic_analysis.get('item_name', 'collectible item')
            brand = basic_analysis.get('brand', '')
            franchise = basic_analysis.get('franchise', '')
            category = basic_analysis.get('category', '')
        else:
            item_name = 'collectible item'
            brand = ''
            franchise = ''
            category = ''
        
        # Prepare images for Gemini (same as analyze_item)
        image_parts = []
        for i, photo in enumerate(photos[:4]):
            if photo.local_path:
                try:
                    file_path = photo.local_path
                    file_exists = Path(file_path).exists()
                    file_size = Path(file_path).stat().st_size if file_exists else 0
                    
                    if not file_exists or file_size == 0:
                        continue
                    
                    image_b64 = self._encode_image_to_base64(file_path)
                    mime_type = 'image/jpeg'  # Always JPEG after conversion
                    
                    if image_b64.startswith('data:image'):
                        image_b64 = image_b64.split(',')[1] if ',' in image_b64 else image_b64
                    
                    image_parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to prepare image {i+1}: {e}")
                    continue
        
        if not image_parts:
            return {"error": "No valid images could be prepared for analysis"}
        
        # Build detailed prompt (adapted from EnhancedScanner)
        prompt = f"""You are an expert collectibles appraiser specializing in authentication, valuation, and historical research.

I need you to perform a COMPREHENSIVE DEEP ANALYSIS of this collectible item, with particular attention to collector value indicators.

**BASIC INFORMATION:**
- Item: {item_name}
- Brand/Manufacturer: {brand}
- Franchise/Series: {franchise}
- Category: {category}

**YOUR CRITICAL TASK - Focus on Collector Value Indicators:**

1. **MINT MARKS & PRODUCTION MARKINGS**
   - For coins: Identify mint mark location and letter (P, D, S, W, etc.)
   - For collectibles: Identify production facility marks, factory codes, or manufacturing location indicators
   - Note any special mint marks or rare production locations
   - Explain the significance of the mint mark for value

2. **SERIAL NUMBERS & LIMITED EDITION MARKINGS**
   - Extract any serial numbers, production numbers, or limited edition numbers
   - Note if it's a numbered edition (e.g., "123/500", "Limited Edition #45")
   - Identify certificate numbers, authentication numbers, or tracking numbers
   - Explain how the serial number affects value (lower numbers often more valuable)

3. **SIGNATURES & AUTOGRAPHS**
   - Check for any signatures, autographs, or artist signatures
   - Identify the signer if possible
   - Assess signature authenticity markers
   - Note signature placement and condition
   - Explain the value impact of signatures

4. **ERRORS, VARIATIONS & MANUFACTURING DEFECTS**
   - Look for error coins (misprints, double strikes, off-center strikes, etc.)
   - Check for printing errors (misprints, color errors, cut errors)
   - Identify factory defects or variations
   - Note any unique manufacturing anomalies
   - Explain how errors/variations affect value (errors can be valuable!)

5. **HISTORICAL CONTEXT & BACKSTORY**
   - Research and provide a compelling short history/backstory of this SPECIFIC item
   - When was it produced/released? What was happening at that time?
   - Why is this item significant to collectors?
   - What makes it rare or desirable?
   - Include interesting facts or context that give the item character
   - Explain its place in collecting history

6. **AUTHENTICATION & CONDITION**
   - Verify authenticity markers
   - Assess condition and grading
   - Note any concerns or red flags
   - Identify authentication markers visible in photos

7. **MARKET VALUE ANALYSIS**
   - Current market value range
   - Recent sales data (if known)
   - Market trend
   - How do the above factors (mint marks, serial numbers, signatures, errors) affect value?

**OUTPUT FORMAT:**

You MUST respond with ONLY valid JSON (no markdown, no explanations). Use this exact structure:

{{
  "item_name": "{item_name}",
  "category": "{category}",
  "brand": "{brand}",
  "franchise": "{franchise}",
  
  "card_type": "pokemon / mtg / yugioh / sports_nfl / sports_nba / sports_mlb / sports_nhl / tcg / unknown (ONLY if this is a card)",
  "game_name": "Pokemon / Magic: The Gathering / Yu-Gi-Oh! / etc. (ONLY for TCG cards)",
  "sport": "NFL / NBA / MLB / NHL / etc. (ONLY for sports cards)",
  "set_name": "set or series name (if this is a card)",
  "card_number": "card number (if visible on card)",
  "rarity": "rarity level (if this is a card)",
  "player_name": "player name (ONLY for sports cards)",
  "is_rookie_card": true/false,
  "is_graded": true/false,
  "grading_company": "PSA / BGS / CGC / etc. (if graded)",
  "grading_score": 9.5,
  
  "mint_mark": {{
    "present": true/false,
    "location": "description of where mint mark appears",
    "mark": "letter or symbol (e.g., 'D', 'P', 'S', 'W')",
    "significance": "why this mint mark matters for value",
    "rarity_notes": "is this a common or rare mint mark?"
  }},
  
  "serial_number": {{
    "present": true/false,
    "number": "the actual serial number if visible",
    "type": "serial number / limited edition / certificate number / etc.",
    "format": "description (e.g., 'Limited Edition 45/500', 'Serial #12345')",
    "significance": "how this affects value (lower numbers, numbered editions, etc.)"
  }},
  
  "signature": {{
    "present": true/false,
    "signer": "name of signer if identifiable",
    "location": "where signature appears",
    "authenticity_confidence": 0.0-1.0,
    "condition": "description of signature condition",
    "value_impact": "how signature affects value"
  }},
  
  "errors_variations": {{
    "present": true/false,
    "error_type": "description (e.g., 'misprint', 'double strike', 'off-center', 'color error')",
    "error_description": "detailed description of the error",
    "error_severity": "minor / moderate / significant",
    "value_impact": "how this error affects value (errors can increase value significantly!)",
    "known_error_types": ["list any known error variations for this item type"]
  }},
  
  "historical_context": {{
    "release_year": 0,
    "manufacturer": "manufacturer name",
    "series": "series or set name",
    "backstory": "compelling short history giving this item character - make it interesting! What makes this item special? What was happening when it was made? Why do collectors care?",
    "significance": "why this item is significant to collectors",
    "rarity_context": "context about why this item is rare or desirable"
  }},
  
  "authentication": {{
    "is_authentic": true/false,
    "confidence": 0.0-1.0,
    "authentication_markers": ["list of visible authentication markers"],
    "red_flags": ["any concerns about authenticity"],
    "verification_notes": "authentication assessment"
  }},
  
  "condition": {{
    "overall_grade": "condition grade (e.g., 'Mint', 'Near Mint', 'Excellent', 'Very Good')",
    "grading_scale": "PSA / CGC / raw / other",
    "condition_details": "detailed condition assessment",
    "wear_and_tear": "description of any wear",
    "damage": ["list any damage items"],
    "preservation_notes": "how well preserved it is"
  }},
  
  "market_analysis": {{
    "current_market_value_low": 0.0,
    "current_market_value_high": 0.0,
    "estimated_value": 0.0,
    "market_trend": "Rising / Stable / Declining",
    "demand_level": "High / Medium / Low",
    "value_factors": ["list of factors affecting value including mint marks, serial numbers, signatures, errors"],
    "market_notes": "market analysis notes"
  }},
  
  "collector_notes": "summary of what makes this item special for collectors, highlighting mint marks, serial numbers, signatures, errors, and historical significance"
}}

**IMPORTANT GUIDELINES:**
- Be thorough in examining images for mint marks, serial numbers, signatures, and errors
- Provide a compelling, interesting backstory that gives the item character
- Be specific about what you see - exact numbers, letters, locations
- If you cannot determine something, set present: false and explain why in significance/notes
- Errors and variations can SIGNIFICANTLY increase value - don't miss them!
- Make the backstory engaging - collectors love knowing the history behind their items
- Be honest about confidence levels - if uncertain, indicate that
- Respond with ONLY JSON, no other text"""
        
        # Build request payload (same structure as analyze_item)
        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    *image_parts
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 4096,  # Higher for detailed analysis
            }
        }
        
        # Make API request (same as analyze_item)
        api_url_with_key = f"{self.api_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                api_url_with_key,
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for detailed analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Parse JSON response
                content_text = content_text.strip()
                if content_text.startswith('```json'):
                    content_text = content_text[7:-3].strip()
                elif content_text.startswith('```'):
                    content_text = content_text[3:-3].strip()
                
                analysis = json.loads(content_text)
                return analysis
            else:
                return {
                    "error": f"Gemini API error: {response.status_code}",
                    "error_type": "api_error"
                }
        
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse JSON response: {str(e)}",
                "error_type": "json_parse_error"
            }
        except Exception as e:
            return {
                "error": f"Detailed analysis failed: {str(e)}",
                "error_type": "exception"
            }

    @classmethod
    def from_env(cls) -> "GeminiClassifier":
        """Create classifier from environment variables"""
        return cls()


# Convenience functions
def classify_item(photos: List[Photo]) -> Dict[str, Any]:
    """
    Quick function to classify an item using Gemini.

    Args:
        photos: List of Photo objects

    Returns:
        Classification dict with item details and collectible flag
    """
    classifier = GeminiClassifier.from_env()
    return classifier.analyze_item(photos)


def analyze_card(photos: List[Photo]) -> Dict[str, Any]:
    """
    Quick function to analyze a card using Gemini.
    
    Args:
        photos: List of Photo objects
        
    Returns:
        Card analysis dict with card-specific details
    """
    classifier = GeminiClassifier.from_env()
    return classifier.analyze_card(photos)


def smart_analyze(photos: List[Photo]) -> Dict[str, Any]:
    """
    Smart analyzer that detects item type and routes appropriately.
    
    First does quick card detection, then:
    - If card: run detailed card analysis
    - If not card: run standard item classification
    
    Args:
        photos: List of Photo objects
        
    Returns:
        Analysis dict with appropriate details
    """
    classifier = GeminiClassifier.from_env()
    
    # Try card analysis first (faster than full classification)
    card_result = classifier.analyze_card(photos)
    
    if card_result.get('is_card'):
        # It's a card! Return card-specific data
        return {
            **card_result,
            'analysis_type': 'card'
        }
    else:
        # Not a card, do standard classification
        item_result = classifier.analyze_item(photos)
        return {
            **item_result,
            'analysis_type': 'item'
        }
