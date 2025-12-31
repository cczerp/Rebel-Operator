"""
OpenAI-based Fast Item Classification
======================================
Uses OpenAI GPT-4o-mini for quick, cost-effective item classification.
This is the PRIMARY analyzer for the "Analyze with AI" button.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI
from ..schema.unified_listing import Photo

logger = logging.getLogger(__name__)


class OpenAIClassifier:
    """Fast item classifier using OpenAI GPT-4o-mini"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI classifier"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def analyze_item(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Fast item classification using OpenAI GPT-4o-mini.

        Returns:
            {
                "item_name": str,
                "brand": str,
                "franchise": str,
                "category": str,
                "description": str,
                "collectible": bool,
                "collectible_confidence": float,
                "collectible_indicators": List[str],
                "estimated_value_low": float,
                "estimated_value_high": float,
                "detected_keywords": List[str],
                "sku_upc": str,
                "logos_marks": List[str],
                "condition": str,
                "color": str,
                "size": str,
                "material": str,
                "suggested_title": str,
                "suggested_price": float,
            }
        """
        if not photos:
            return {"error": "No photos provided"}

        # Get image URLs (use Supabase URLs if available, otherwise skip)
        image_urls = []
        for photo in photos[:4]:  # Limit to 4 photos
            if photo.url and ('http://' in photo.url or 'https://' in photo.url):
                image_urls.append(photo.url)
                logger.info(f"[OPENAI DEBUG] Using photo URL: {photo.url[:100]}...")
            elif photo.local_path:
                logger.warning(f"[OPENAI DEBUG] Photo has local_path but no URL, skipping: {photo.local_path}")
        
        if not image_urls:
            return {"error": "No valid image URLs provided"}

        # Build comprehensive classification prompt (same as Gemini)
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
- Respond with ONLY JSON, no other text"""

        try:
            # Build content with text prompt + image URLs
            content = [
                {"type": "text", "text": prompt},
                *[
                    {"type": "image_url", "image_url": {"url": url}}
                    for url in image_urls
                ]
            ]

            logger.info(f"[OPENAI DEBUG] Sending {len(image_urls)} image(s) to OpenAI {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=2048
            )

            content_text = response.choices[0].message.content

            # Parse JSON response
            try:
                # Clean up any markdown formatting
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()

                analysis = json.loads(content_text)
                analysis["ai_provider"] = "openai"
                return analysis

            except json.JSONDecodeError as e:
                logger.error(f"[OPENAI ERROR] JSON parse error: {str(e)}")
                logger.error(f"[OPENAI ERROR] Response text: {content_text[:500]}")
                return {
                    "error": f"JSON parse error: {str(e)}",
                    "raw_response": content_text[:500]
                }

        except Exception as e:
            logger.error(f"[OPENAI ERROR] API call failed: {str(e)}")
            import traceback
            logger.error(f"[OPENAI ERROR] Traceback: {traceback.format_exc()}")
            return {
                "error": f"OpenAI API error: {str(e)}",
                "error_type": "api_error"
            }

    @classmethod
    def from_env(cls) -> "OpenAIClassifier":
        """Create classifier from environment variables"""
        return cls()


# Convenience function for compatibility
def classify_item(photos: List[Photo]) -> Dict[str, Any]:
    """
    Quick function to classify an item using OpenAI.

    Args:
        photos: List of Photo objects

    Returns:
        Classification dict with item details and collectible flag
    """
    classifier = OpenAIClassifier.from_env()
    return classifier.analyze_item(photos)

