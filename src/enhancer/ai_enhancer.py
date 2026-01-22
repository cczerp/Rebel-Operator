"""
Dual-AI Listing Enhancer
=========================
Uses both OpenAI and Anthropic Claude to enhance listings with:
- AI-generated descriptions
- Title optimization
- Photo analysis
- Keyword extraction
- Category suggestions
"""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests
from pathlib import Path

from ..schema.unified_listing import (
    UnifiedListing,
    Photo,
    SEOData,
    Category,
    ItemSpecifics,
)


class AiAnalyzer:
    """
    Multi-AI enhancer with local Ollama support.

    Strategy:
    - Step 1: Ollama (local, free) - llama3.2-vision:11b (if available)
    - Step 2: ChatGPT (GPT-4 Vision) as fallback if Ollama unavailable
    - Step 3: Claude as final fallback if both above fail

    Ollama is FREE and runs locally - no API costs!
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_openai: bool = True,
        use_anthropic: bool = True,
        use_ollama: bool = True,
        ollama_model: str = "llama3.2-vision:11b",
        ollama_host: str = "http://localhost:11434",
        openai_base_url: str = "https://api.openai.com/v1",
        openai_model: str = "gpt-4o",
    ):
        """
        Initialize AI enhancer.

        Args:
            openai_api_key: OpenAI API key (or Nebius/compatible API key)
            anthropic_api_key: Anthropic API key
            use_openai: Enable OpenAI enhancement
            use_anthropic: Enable Anthropic enhancement
            use_ollama: Enable Ollama (local) enhancement
            ollama_model: Ollama model to use (default: llama3.2-vision:11b)
            ollama_host: Ollama server URL (default: http://localhost:11434)
            openai_base_url: OpenAI-compatible API base URL (default: OpenAI, can use Nebius)
            openai_model: Model to use (default: gpt-4o, can use Nebius models)
        """
        # Strip whitespace from API keys (common issue with env vars)
        openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_key.strip() if openai_key else None
        self.anthropic_api_key = anthropic_key.strip() if anthropic_key else None
        self.use_openai = use_openai and self.openai_api_key is not None
        self.use_anthropic = use_anthropic and self.anthropic_api_key is not None
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.ollama_host = ollama_host
        self.openai_base_url = openai_base_url
        self.openai_model = openai_model

        if not (self.use_openai or self.use_anthropic or self.use_ollama):
            raise ValueError(
                "At least one AI provider must be enabled (OpenAI, Anthropic, or Ollama)"
            )

    def _convert_to_claude_format(self, image_path: str) -> tuple[bytes, str]:
        """
        Convert image to Claude-compatible format (JPEG, PNG, or GIF).
        Claude only accepts: image/jpeg, image/png, image/gif
        
        Returns:
            (image_bytes, mime_type) tuple
        """
        from PIL import Image
        import io
        
        try:
            img = Image.open(image_path)
            
            # Get original format
            original_format = img.format
            
            # If already in supported format, return as-is (unless it's WebP/HEIC)
            if original_format in ('JPEG', 'PNG', 'GIF'):
                # Read the file
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                
                mime_type = {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif'
                }[original_format]
                
                return image_bytes, mime_type
            
            # Convert unsupported formats (WebP, HEIC, etc.) to JPEG
            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95, optimize=True)
            image_bytes = output.getvalue()
            
            return image_bytes, 'image/jpeg'
            
        except Exception as e:
            print(f"Warning: Image conversion failed for {image_path}: {e}")
            # Fallback: try to read as-is
            with open(image_path, "rb") as f:
                return f.read(), "image/jpeg"

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode local image to base64, converting to Claude-compatible format if needed"""
        image_bytes, _ = self._convert_to_claude_format(image_path)
        return base64.b64encode(image_bytes).decode("utf-8")

    def _get_image_mime_type(self, image_path: str) -> str:
        """
        Get MIME type for Claude (only JPEG, PNG, GIF supported).
        Images are converted to JPEG if not already in a supported format.
        """
        from PIL import Image
        
        try:
            img = Image.open(image_path)
            original_format = img.format
            
            # Return MIME type for supported formats
            if original_format in ('JPEG', 'PNG', 'GIF'):
                return {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif'
                }[original_format]
            
            # Unsupported formats (WebP, HEIC, etc.) will be converted to JPEG
            return 'image/jpeg'
        except Exception:
            # Fallback
            return 'image/jpeg'

    def analyze_photos_claude(self, photos: List[Photo], target_platform: str = "general") -> Dict[str, Any]:
        """
        Initial photo analysis using Claude Vision (Step 1).
        Creates comprehensive listing with details, SEO, and keywords.

        Args:
            photos: List of photos to analyze
            target_platform: Target platform for optimization

        Returns:
            Dictionary with initial analysis, title, description, keywords, etc.
        """
        if not self.use_anthropic:
            return {}

        # Prepare images for vision analysis
        image_contents = []
        for photo in photos[:4]:  # Limit to 4 photos to save tokens
            image_dict = {"type": "image"}

            if photo.local_path:
                # Convert to Claude-compatible format and encode
                image_bytes, mime_type = self._convert_to_claude_format(photo.local_path)
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                image_dict["source"] = {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": image_b64,
                }
            elif photo.url:
                image_dict["source"] = {
                    "type": "url",
                    "url": photo.url,
                }

            image_contents.append(image_dict)

        # Platform-specific context
        platform_context = {
            "ebay": "eBay (focus on detailed specs, trust-building language, and search keywords)",
            "mercari": "Mercari (casual, mobile-friendly, highlight condition and value)",
            "general": "general e-commerce",
        }
        context = platform_context.get(target_platform.lower(), "general e-commerce")

        # Build comprehensive analysis prompt
        prompt = f"""Analyze these product images and create a comprehensive listing for {context}.

Provide:
1. **Item Title**: Compelling, keyword-rich title (under 80 characters)
2. **Detailed Description**: 2-3 paragraphs covering features, condition, and value proposition
3. **SEO Keywords**: 15-20 relevant search keywords
4. **Search Terms**: Alternative phrases buyers might use
5. **Category**: Suggested category (e.g., "Electronics > Cameras")
6. **Item Specifics**: Brand, model, size, color, material if visible
7. **Condition Notes**: Specific observations about condition
8. **Key Features**: Bullet points of notable selling points

Format as JSON:
{{
  "title": "...",
  "description": "...",
  "keywords": ["...", "..."],
  "search_terms": ["...", "..."],
  "category": "...",
  "brand": "...",
  "model": "...",
  "color": "...",
  "condition_notes": "...",
  "features": ["...", "..."]
}}"""

        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Build message with images
        content = [{"type": "text", "text": prompt}]
        content.extend(image_contents)

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content_text = result["content"][0]["text"]

            # Parse JSON response
            import json
            try:
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()

                analysis = json.loads(content_text)
                return analysis
            except json.JSONDecodeError:
                return {"raw_response": content_text}
        else:
            raise Exception(f"Claude API error: {response.text}")

    def analyze_photos_ollama(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Analyze photos using local Ollama (FREE!).
        Uses llama3.2-vision:11b by default - Meta's latest vision model.

        Args:
            photos: List of photos to analyze

        Returns:
            Dictionary with photo analysis, suggested title, description, keywords
        """
        if not self.use_ollama:
            return {}

        # Prepare images for vision analysis
        image_contents = []
        for photo in photos[:4]:  # Limit to 4 photos
            if photo.local_path:
                # Ollama expects base64 encoded images
                image_b64 = self._encode_image_to_base64(photo.local_path)
                image_contents.append(image_b64)

        if not image_contents:
            return {}

        # Build prompt for comprehensive analysis
        prompt = """Analyze these product images and provide comprehensive listing details for an e-commerce resale platform.

Provide:
1. **Item Title**: Compelling, keyword-rich title (under 80 characters)
2. **Detailed Description**: 2-3 paragraphs covering features, condition, and value proposition
3. **SEO Keywords**: 15-20 relevant search keywords
4. **Search Terms**: Alternative phrases buyers might use
5. **Category**: Suggested category (e.g., "Electronics > Cameras")
6. **Item Specifics**: Brand, model, size, color, material if visible
7. **Condition Notes**: Specific observations about condition
8. **Key Features**: Bullet points of notable selling points
9. **Estimated Price**: Fair market value in USD based on condition and market research

Format as JSON:
{
  "title": "...",
  "description": "...",
  "keywords": ["...", "..."],
  "search_terms": ["...", "..."],
  "category": "...",
  "brand": "...",
  "model": "...",
  "color": "...",
  "condition_notes": "...",
  "features": ["...", "..."],
  "estimated_price": 99.99
}"""

        # Build Ollama API request
        # Ollama's vision API format
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "images": image_contents,
            "stream": False,
            "format": "json",
            "keep_alive": "1h"  # Keep model loaded for 1 hour (avoid reload time)
        }

        try:
            # Add header to bypass ngrok warning page (for free tier tunnels)
            headers = {"ngrok-skip-browser-warning": "true"}
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                headers=headers,
                timeout=300  # Ollama can be slow (5 minutes for model load + inference)
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                # Parse JSON response
                import json
                try:
                    # Try to extract JSON from markdown code blocks if present
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()

                    analysis = json.loads(response_text)
                    print(f"🔍 Ollama returned: {analysis}")  # Debug logging
                    return analysis
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    print(f"⚠️ JSON parse failed, raw response: {response_text[:200]}")  # Debug logging
                    return {"raw_response": response_text}
            else:
                raise Exception(f"Ollama API error (HTTP {response.status_code}): {response.text}")

        except requests.exceptions.ConnectionError:
            raise Exception(
                "Ollama not running. Start it with: ollama serve\n"
                "Or install from: https://ollama.com"
            )
        except requests.exceptions.Timeout:
            raise Exception(
                "Ollama request timed out. This is normal on first run (downloading model). "
                "Try again in a minute."
            )

    def analyze_photos_openai_fallback(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Analyze photos using GPT-4 Vision as fallback (when Claude fails).
        Does a fresh analysis from scratch.

        Args:
            photos: List of photos to analyze

        Returns:
            Dictionary with photo analysis, suggested title, description, keywords
        """
        if not self.use_openai:
            return {}

        # Prepare images for vision analysis
        image_contents = []
        for photo in photos[:4]:  # Limit to 4 photos to save tokens
            if photo.local_path:
                image_b64 = self._encode_image_to_base64(photo.local_path)
                mime_type = self._get_image_mime_type(photo.local_path)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_b64}"
                    }
                })
            elif photo.url:
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": photo.url}
                })

        # Build prompt for fresh analysis
        prompt = """Analyze these product images and provide comprehensive listing details.

Provide:
1. **Item Title**: Compelling, keyword-rich title (under 80 characters)
2. **Detailed Description**: 2-3 paragraphs covering features, condition, and value proposition
3. **SEO Keywords**: 15-20 relevant search keywords
4. **Search Terms**: Alternative phrases buyers might use
5. **Category**: Suggested category (e.g., "Electronics > Cameras")
6. **Item Specifics**: Brand, model, size, color, material if visible
7. **Condition Notes**: Specific observations about condition
8. **Key Features**: Bullet points of notable selling points
9. **Estimated Price**: Fair market value in USD based on condition and market research

Format as JSON:
{
  "title": "...",
  "description": "...",
  "keywords": ["...", "..."],
  "search_terms": ["...", "..."],
  "category": "...",
  "brand": "...",
  "model": "...",
  "color": "...",
  "condition_notes": "...",
  "features": ["...", "..."],
  "estimated_price": 99.99
}"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents,
                ]
            }
        ]

        # Call OpenAI-compatible API (OpenAI, Nebius, etc.)
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.openai_model,  # Configurable model (gpt-4o, Nebius models, etc.)
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
        }

        response = requests.post(
            f"{self.openai_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            import json
            try:
                # Try to extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {"raw_response": content}
        else:
            # Parse OpenAI error response for better error messages
            import json
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", response.text)
                error_type = error_data.get("error", {}).get("type", "unknown")
                error_code = error_data.get("error", {}).get("code", "")

                # Check for common errors and provide helpful messages
                if response.status_code == 429 or "rate_limit" in error_type or "quota" in error_message.lower() or "insufficient_quota" in error_code:
                    raise Exception(
                        "OpenAI API rate limit or quota exceeded. "
                        "IMPORTANT: ChatGPT Plus/Pro subscription is different from OpenAI API credits. "
                        "To use the AI analyzer, you need to: "
                        "1) Go to https://platform.openai.com/account/billing "
                        "2) Add credits to your API account (minimum $5) "
                        "3) Make sure you're using the correct API key from https://platform.openai.com/api-keys"
                    )
                elif response.status_code == 401:
                    raise Exception(
                        "OpenAI API authentication failed. "
                        "Please check that your OPENAI_API_KEY is correct. "
                        "Get your API key from: https://platform.openai.com/api-keys"
                    )
                else:
                    raise Exception(f"OpenAI API error ({error_type}): {error_message}")
            except json.JSONDecodeError:
                raise Exception(f"OpenAI API error (HTTP {response.status_code}): {response.text}")


    def _is_analysis_complete(self, analysis: Dict[str, Any]) -> bool:
        """
        Check if AI analysis successfully identified the item.

        Args:
            analysis: Analysis data from AI

        Returns:
            True if analysis has minimum required fields, False otherwise
        """
        # Check for essential fields that indicate successful identification
        has_title = bool(analysis.get("title")) and len(analysis.get("title", "")) > 10
        has_description = bool(analysis.get("description")) and len(analysis.get("description", "")) > 20
        has_category = bool(analysis.get("category"))

        return has_title and has_description and has_category

    def enhance_listing(
        self,
        listing: UnifiedListing,
        target_platform: str = "general",
        force: bool = False,
    ) -> UnifiedListing:
        """
        Complete AI enhancement workflow with Ollama as primary (FREE!).

        Strategy:
        - Step 1: Ollama (local, FREE) - llama3.2-vision:11b (if available)
        - Step 2: ChatGPT (GPT-4 Vision) as paid fallback if Ollama unavailable
        - Step 3: Claude as final fallback if both above fail

        Args:
            listing: UnifiedListing to enhance
            target_platform: Target platform for optimization
            force: Force re-enhancement even if already enhanced

        Returns:
            Enhanced UnifiedListing
        """
        if listing.ai_enhanced and not force:
            # Already enhanced, skip
            return listing

        final_data = {}
        ai_providers_used = []
        last_error = None

        # Step 1: Try Ollama first (FREE and local!)
        if self.use_ollama and listing.photos:
            try:
                print("🦙 Ollama analyzing photos (FREE, local)...")
                ollama_analysis = self.analyze_photos_ollama(listing.photos)

                # Check if Ollama successfully identified the item
                if self._is_analysis_complete(ollama_analysis):
                    print("✅ Ollama successfully identified the item")
                    final_data = ollama_analysis
                    ai_providers_used.append("Ollama (local)")
                else:
                    print(f"⚠️  Ollama analysis incomplete - missing fields. Has title: {bool(ollama_analysis.get('title'))}, description: {bool(ollama_analysis.get('description'))}, category: {bool(ollama_analysis.get('category'))}")
                    # Keep Ollama's partial data
                    final_data = ollama_analysis

            except Exception as e:
                last_error = str(e)
                print(f"❌ Ollama analysis failed: {e}")
                # Continue to ChatGPT fallback

        # Step 2: ChatGPT as fallback (if Ollama failed or incomplete)
        if self.use_openai and listing.photos:
            # Only use ChatGPT if Ollama didn't complete the analysis
            if not self._is_analysis_complete(final_data):
                try:
                    print("🤖 ChatGPT analyzing photos (paid fallback)...")
                    chatgpt_analysis = self.analyze_photos_openai_fallback(listing.photos)

                    # Check if ChatGPT successfully identified the item
                    if self._is_analysis_complete(chatgpt_analysis):
                        print("✅ ChatGPT successfully identified the item")
                        final_data = chatgpt_analysis
                        ai_providers_used.append("ChatGPT")
                    else:
                        print("⚠️  ChatGPT analysis incomplete - will try Claude as fallback")
                        # Merge with existing data
                        final_data = {**final_data, **chatgpt_analysis}

                except Exception as e:
                    last_error = str(e)
                    print(f"❌ ChatGPT analysis failed: {e}")
            else:
                print("💰 Skipping ChatGPT (Ollama analysis was complete)")

        # Step 3: Claude as final fallback
        if self.use_anthropic and listing.photos:
            # Only use Claude if neither Ollama nor ChatGPT completed the analysis
            if not self._is_analysis_complete(final_data):
                try:
                    print("🔄 Using Claude as final fallback...")
                    # Use Claude to analyze from scratch
                    claude_analysis = self.analyze_photos_claude(listing.photos, target_platform)

                    if self._is_analysis_complete(claude_analysis):
                        print("✅ Claude successfully identified the item")
                        final_data = claude_analysis
                        ai_providers_used.append("Claude (fallback)")
                    else:
                        # Merge partial results
                        final_data = {**final_data, **claude_analysis}
                        ai_providers_used.append("Claude (fallback partial)")

                except Exception as e:
                    print(f"❌ Claude fallback failed: {e}")
                    # If everything failed, raise the most relevant error
                    if last_error and not final_data:
                        raise Exception(last_error)
            else:
                print("💰 Skipping Claude (analysis already complete)")

        # Step 3: Apply enhancements to listing
        if final_data:
            # Update description if provided
            if final_data.get("description"):
                listing.description = final_data["description"]

            # Update title if provided
            if final_data.get("title"):
                listing.title = final_data["title"]

            # Update SEO data
            if final_data.get("keywords"):
                listing.seo_data.keywords = final_data["keywords"]

            if final_data.get("search_terms"):
                listing.seo_data.search_terms = final_data["search_terms"]

            # Update category if suggested
            if final_data.get("category"):
                category_parts = final_data["category"].split(" > ")
                if not listing.category:
                    listing.category = Category(
                        primary=category_parts[0],
                        subcategory=category_parts[1] if len(category_parts) > 1 else None,
                    )

            # Update item specifics if provided
            if final_data.get("brand"):
                listing.item_specifics.brand = final_data["brand"]
            if final_data.get("model"):
                listing.item_specifics.model = final_data["model"]
            if final_data.get("color"):
                listing.item_specifics.color = final_data["color"]

            # Update price if estimated
            if final_data.get("estimated_price"):
                from ..schema.unified_listing import Price
                listing.price = Price(amount=float(final_data["estimated_price"]))

            # Mark as AI enhanced
            listing.ai_enhanced = True
            listing.ai_enhancement_timestamp = datetime.now()

            # Track which AI providers were actually used
            if ai_providers_used:
                listing.ai_provider = " → ".join(ai_providers_used)
            else:
                listing.ai_provider = "None (analysis failed)"

        return listing

    @classmethod
    def from_env(cls) -> "AiAnalyzer":
        """
        Create enhancer from environment variables.

        Expected variables:
            - OPENAI_API_KEY (optional) - can be OpenAI or Nebius API key
            - OPENAI_BASE_URL (optional) - for Nebius: https://api.studio.nebius.ai/v1
            - OPENAI_MODEL (optional) - for Nebius: meta-llama/Llama-3.2-90B-Vision-Instruct, etc.
            - ANTHROPIC_API_KEY (optional)
            - USE_OPENAI (optional, default: false if OPENAI_API_KEY not set)
            - USE_ANTHROPIC (optional, default: false if ANTHROPIC_API_KEY not set)
            - USE_OLLAMA (optional, default: true)
            - OLLAMA_MODEL (optional, default: llama3.2-vision:11b)
            - OLLAMA_HOST (optional, default: http://localhost:11434)
        """
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() in ("true", "1", "yes")
        use_openai = os.getenv("USE_OPENAI", "true").lower() in ("true", "1", "yes")
        use_anthropic = os.getenv("USE_ANTHROPIC", "true").lower() in ("true", "1", "yes")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision:11b")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            use_openai=use_openai,
            use_anthropic=use_anthropic,
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            ollama_host=ollama_host,
            openai_base_url=openai_base_url,
            openai_model=openai_model,
        )


def enhance_listing(
    listing: UnifiedListing,
    target_platform: str = "general",
    force: bool = False,
) -> UnifiedListing:
    """
    Convenience function to enhance a listing.

    Args:
        listing: UnifiedListing to enhance
        target_platform: Target platform
        force: Force re-enhancement

    Returns:
        Enhanced listing
    """
    enhancer = AiAnalyzer.from_env()
    return enhancer.enhance_listing(listing, target_platform, force)
