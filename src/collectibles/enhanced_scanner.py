"""
Enhanced Scanner - Deep Collectible Analysis
============================================
Unified scanner for deep collectible analysis focusing on:
- Mint marks
- Serial numbers
- Signatures
- Errors (error coins, misprints, etc.)
- Historical context and backstory

This is the Tier 2 analyzer that runs after Gemini's quick classification.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..schema.unified_listing import Photo
from ..ai.claude_collectible_analyzer import ClaudeCollectibleAnalyzer
from ..ai.gemini_classifier import GeminiClassifier


class EnhancedScanner:
    """
    Enhanced scanner for deep collectible analysis using Claude AI.
    
    This scanner focuses on collector-specific value indicators:
    - Mint marks (coin mint locations)
    - Serial numbers (production numbers, limited edition numbers)
    - Signatures (autographs, artist signatures)
    - Errors (error coins, misprints, factory defects)
    - Historical backstory (item significance, rarity context)
    """

    def __init__(self, claude_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Initialize enhanced scanner"""
        try:
            self.claude_analyzer = ClaudeCollectibleAnalyzer(api_key=claude_api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Claude analyzer: {e}")
        try:
            self.gemini_classifier = GeminiClassifier(api_key=gemini_api_key)
        except Exception as e:
            # Gemini is optional for enhanced scan, just log warning
            print(f"Warning: Gemini classifier not available: {e}")
            self.gemini_classifier = None

        # Initialize OpenAI for image-to-text extraction
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("Warning: OpenAI API key not available - ChatGPT image-to-text disabled")
        
    @classmethod
    def from_env(cls):
        """Create scanner from environment variables"""
        # Ensure .env is loaded
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dotenv not available, rely on system env vars
        return cls()

    def scan(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Scan collectible item for deep analysis.

        NOW USES CHATGPT AS PRIMARY SCANNER with Claude as fallback.

        Args:
            photos: List of Photo objects to analyze

        Returns:
            {
                'type': 'collectible' | 'card' | 'standard_item',
                'data': {...collectible data...},
                'market_prices': {...pricing info...},
                'ai_provider': 'chatgpt' | 'claude',
                'error': str (if error occurred)
            }
        """
        if not photos:
            return {'error': 'No photos provided', 'type': 'standard_item'}

        # Use ChatGPT as PRIMARY scanner with OCR capabilities
        return self.scan_with_chatgpt_ocr(photos)

    def _deep_analyze_collectible_chatgpt(
        self,
        photos: List[Photo]
    ) -> Dict[str, Any]:
        """
        PRIMARY SCANNER: Use ChatGPT (GPT-4 Vision) for comprehensive deep analysis.

        Performs complete collectible analysis including:
        - Text extraction (OCR)
        - Mint marks, serial numbers, signatures
        - Authentication and grading
        - Market valuation
        - Historical context
        """
        if not self.openai_api_key:
            return {"error": "No OpenAI API key available"}

        # Prepare images
        image_contents = []
        for photo in photos[:4]:  # GPT-4 Vision supports multiple images
            if photo.local_path:
                local_path = Path(photo.local_path)
                if not local_path.exists():
                    continue

                # Encode image to base64
                image_bytes = local_path.read_bytes()
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                # Detect MIME type
                from PIL import Image
                try:
                    img = Image.open(local_path)
                    mime_type = {
                        'JPEG': 'image/jpeg',
                        'PNG': 'image/png',
                        'GIF': 'image/gif',
                        'WEBP': 'image/webp'
                    }.get(img.format, 'image/jpeg')
                except:
                    mime_type = 'image/jpeg'

                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_b64}",
                        "detail": "high"  # High detail for better text extraction
                    }
                })

        if not image_contents:
            return {"error": "No valid images found"}

        # Build comprehensive deep analysis prompt for ChatGPT
        prompt = """You are an expert collectibles appraiser specializing in authentication, valuation, and historical research.

I need you to perform a COMPREHENSIVE DEEP ANALYSIS of this collectible item, with particular attention to collector value indicators.

**YOUR CRITICAL TASK - Focus on Collector Value Indicators:**

1. **COIN IDENTIFICATION** (CRITICAL FOR COINS - Skip if not a coin)
   - **Denomination**: Identify the exact coin type (Penny/Cent, Nickel, Dime, Quarter, Half Dollar, Dollar Coin, Other)
   - **Year**: Extract the year minted (visible on the coin)
   - **Mint Mark**: Location and letter (P=Philadelphia, D=Denver, S=San Francisco, W=West Point, CC=Carson City, O=New Orleans, etc.)
   - **Coin Type/Series**: (Lincoln Penny, Jefferson Nickel, Roosevelt Dime, Washington Quarter, Kennedy Half Dollar, Eisenhower Dollar, Sacagawea Dollar, etc.)
   - **Composition**: Material (Copper, Nickel, Silver, etc.) - identify by year and appearance
   - **Mintage**: If known, provide the mintage number (how many were produced)
   - **Diameter/Weight**: Standard measurements if known
   - **Special Designations**: (Proof, Commemorative, Error, Variety, etc.)

2. **MINT MARKS & PRODUCTION MARKINGS**
   - For coins: Identify mint mark location and letter (P, D, S, W, CC, O, etc.)
   - Location matters: Penny mint mark is below date, Quarter is behind neck/head, etc.
   - For collectibles: Identify production facility marks, factory codes, or manufacturing location indicators
   - Note any special mint marks or rare production locations
   - Explain the significance of the mint mark for value

3. **SERIAL NUMBERS & LIMITED EDITION MARKINGS**
   - Extract any serial numbers, production numbers, or limited edition numbers
   - Note if it's a numbered edition (e.g., "123/500", "Limited Edition #45")
   - Identify certificate numbers, authentication numbers, or tracking numbers
   - Explain how the serial number affects value (lower numbers often more valuable)

4. **SIGNATURES & AUTOGRAPHS**
   - Check for any signatures, autographs, or artist signatures
   - Identify the signer if possible
   - Assess signature authenticity markers:
     * Real signatures: Ink bleeds into surface, pressure variation, natural flow
     * Fake signatures: Uniform thickness, no bleeding, perfectly straight
   - Note signature placement and condition
   - Explain the value impact of signatures

5. **ERRORS, VARIATIONS & MANUFACTURING DEFECTS**
   - Look for error coins (misprints, double strikes, off-center strikes, etc.)
   - Check for printing errors (misprints, color errors, cut errors)
   - Identify factory defects or variations
   - Note any unique manufacturing anomalies
   - Explain how errors/variations affect value (errors can be valuable!)

6. **CARD IDENTIFICATION** (if this is a trading card)
   - Card name/title
   - Set name and number
   - Card number (e.g., "45/102")
   - Rarity (Common, Uncommon, Rare, Ultra Rare, etc.)
   - Edition stamps (1st Edition, Limited, Shadowless, etc.)
   - Game type (Pokemon, Magic, Yu-Gi-Oh, Sports, etc.)
   - Player name (for sports cards)
   - Is it a rookie card?
   - Grading (PSA, BGS, CGC score if visible)

7. **HISTORICAL CONTEXT & BACKSTORY**
   - Research and provide a compelling short history/backstory of this SPECIFIC item
   - When was it produced/released? What was happening at that time?
   - Why is this item significant to collectors?
   - What makes it rare or desirable?
   - Include interesting facts or context that give the item character
   - Explain its place in collecting history

8. **AUTHENTICATION & CONDITION**
   - Verify authenticity markers
   - Assess condition and grading (Gem Mint, Near Mint, Excellent, Good, etc.)
   - Note any concerns or red flags
   - Identify authentication markers visible in photos

9. **MARKET VALUE ANALYSIS**
   - Current market value range
   - Recent sales data (if known)
   - Market trend (Rising, Stable, Declining)
   - How do the above factors (mint marks, serial numbers, signatures, errors) affect value?

**OUTPUT FORMAT:**

You MUST respond with ONLY valid JSON (no markdown, no explanations). Use this exact structure:

{
  "item_name": "Item name",
  "category": "coins / trading_cards / toys / stamps / etc.",
  "brand": "Brand or manufacturer",
  "franchise": "Franchise or series name",

  "coin_info": {
    "is_coin": true/false,
    "denomination": "Penny / Nickel / Dime / Quarter / Half Dollar / Dollar Coin / Other",
    "year": 0,
    "coin_type": "Lincoln Penny / Jefferson Nickel / etc.",
    "composition": "Copper / Nickel / Silver / etc.",
    "mintage": 0,
    "diameter_mm": 0.0,
    "weight_grams": 0.0,
    "special_designation": "Proof / Commemorative / Error / Variety / Standard",
    "series_info": "description"
  },

  "card_type": "pokemon / mtg / yugioh / sports_nfl / sports_nba / sports_mlb / sports_nhl / tcg / unknown (ONLY if card)",
  "game_name": "Pokemon / Magic: The Gathering / Yu-Gi-Oh! / etc. (ONLY for TCG cards)",
  "sport": "NFL / NBA / MLB / NHL / etc. (ONLY for sports cards)",
  "set_name": "set or series name (if card)",
  "card_number": "card number (if visible)",
  "rarity": "rarity level (if card)",
  "player_name": "player name (ONLY for sports cards)",
  "is_rookie_card": true/false,
  "is_graded": true/false,
  "grading_company": "PSA / BGS / CGC / etc. (if graded)",
  "grading_score": 9.5,

  "mint_mark": {
    "present": true/false,
    "location": "where mint mark appears",
    "mark": "letter (e.g., 'D', 'P', 'S')",
    "significance": "why this matters for value",
    "rarity_notes": "common or rare?"
  },

  "serial_number": {
    "present": true/false,
    "number": "actual serial number",
    "type": "serial number / limited edition / etc.",
    "format": "description",
    "significance": "how this affects value"
  },

  "signature": {
    "present": true/false,
    "signer": "name of signer",
    "location": "where signature appears",
    "authenticity_confidence": 0.0-1.0,
    "condition": "condition description",
    "value_impact": "how signature affects value"
  },

  "errors_variations": {
    "present": true/false,
    "error_type": "description",
    "error_description": "detailed description",
    "error_severity": "minor / moderate / significant",
    "value_impact": "how error affects value",
    "known_error_types": ["list"]
  },

  "historical_context": {
    "release_year": 0,
    "manufacturer": "manufacturer",
    "series": "series name",
    "backstory": "compelling history - make it interesting!",
    "significance": "why collectors care",
    "rarity_context": "why rare or desirable"
  },

  "authentication": {
    "is_authentic": true/false,
    "confidence": 0.0-1.0,
    "authentication_markers": ["markers"],
    "red_flags": ["concerns"],
    "verification_notes": "notes"
  },

  "condition": {
    "overall_grade": "Mint / Near Mint / Excellent / etc.",
    "grading_scale": "PSA / CGC / raw",
    "condition_details": "detailed assessment",
    "wear_and_tear": "wear description",
    "damage": ["damage items"],
    "preservation_notes": "preservation notes"
  },

  "market_analysis": {
    "current_market_value_low": 0.0,
    "current_market_value_high": 0.0,
    "estimated_value": 0.0,
    "market_trend": "Rising / Stable / Declining",
    "demand_level": "High / Medium / Low",
    "value_factors": ["factors affecting value"],
    "market_notes": "market notes"
  },

  "collector_notes": "summary of what makes this special"
}

**IMPORTANT GUIDELINES:**
- Extract ALL text you see - mint marks, serial numbers, signatures, dates, card text
- Be thorough in examining images for all collector value indicators
- Provide compelling, interesting backstory
- Be specific about what you see - exact numbers, letters, locations
- Assess signature authenticity (ink bleeding, pressure variation)
- Errors and variations can SIGNIFICANTLY increase value
- Be honest about confidence levels
"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",  # GPT-4 with vision
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.2  # Low temperature for precise analysis
        }

        try:
            import requests
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                content_text = result["choices"][0]["message"]["content"]

                # Parse JSON response
                try:
                    # Clean JSON (remove markdown code blocks if present)
                    content_text = content_text.strip()
                    if content_text.startswith("```json"):
                        content_text = content_text[7:]
                    if content_text.startswith("```"):
                        content_text = content_text[3:]
                    if content_text.endswith("```"):
                        content_text = content_text[:-3]
                    content_text = content_text.strip()

                    # Find JSON object boundaries
                    if not content_text.startswith("{"):
                        start_idx = content_text.find("{")
                        if start_idx != -1:
                            content_text = content_text[start_idx:]

                    if not content_text.endswith("}"):
                        end_idx = content_text.rfind("}")
                        if end_idx != -1:
                            content_text = content_text[:end_idx + 1]

                    analysis = json.loads(content_text)
                    return analysis

                except json.JSONDecodeError as e:
                    return {
                        "error": f"JSON parse error: {str(e)}",
                        "raw_response": content_text[:1000]
                    }
            else:
                error_text = response.text[:500] if response.text else "Unknown error"
                return {
                    "error": f"ChatGPT API error ({response.status_code}): {error_text}"
                }

        except Exception as e:
            return {
                "error": f"Exception during ChatGPT analysis: {str(e)}"
            }

    def _deep_analyze_collectible(
        self,
        photos: List[Photo],
        basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        FALLBACK: Claude deep analysis (used when ChatGPT fails).

        Perform deep collectible analysis with enhanced focus on:
        - Mint marks
        - Serial numbers
        - Signatures
        - Errors
        - History/backstory
        """
        import base64

        # Prepare images for Claude
        image_parts = []
        for photo in photos[:4]:  # Claude supports up to 4 images
            if photo.local_path:
                local_path = Path(photo.local_path)
                if not local_path.exists():
                    continue
                    
                # Convert to Claude-compatible format
                image_bytes, mime_type = self.claude_analyzer._convert_to_claude_format(str(local_path))
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                image_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_b64
                    }
                })

        if not image_parts:
            return {"error": "No valid images found"}

        # Build enhanced prompt focused on collector value indicators
        item_name = basic_analysis.get('suggested_title') or basic_analysis.get('item_name', 'collectible item')
        brand = basic_analysis.get('brand', '')
        franchise = basic_analysis.get('franchise', '')
        category = basic_analysis.get('category', '')

        prompt = f"""You are an expert collectibles appraiser specializing in authentication, valuation, and historical research.

I need you to perform a COMPREHENSIVE DEEP ANALYSIS of this collectible item, with particular attention to collector value indicators.

**BASIC INFORMATION:**
- Item: {item_name}
- Brand/Manufacturer: {brand}
- Franchise/Series: {franchise}
- Category: {category}

**YOUR CRITICAL TASK - Focus on Collector Value Indicators:**

1. **COIN IDENTIFICATION** (CRITICAL FOR COINS - Skip if not a coin)
   - **Denomination**: Identify the exact coin type (Penny/Cent, Nickel, Dime, Quarter, Half Dollar, Dollar Coin, Other)
   - **Year**: Extract the year minted (visible on the coin)
   - **Mint Mark**: Location and letter (P=Philadelphia, D=Denver, S=San Francisco, W=West Point, CC=Carson City, O=New Orleans, etc.)
   - **Coin Type/Series**: (Lincoln Penny, Jefferson Nickel, Roosevelt Dime, Washington Quarter, Kennedy Half Dollar, Eisenhower Dollar, Sacagawea Dollar, etc.)
   - **Composition**: Material (Copper, Nickel, Silver, etc.) - identify by year and appearance
   - **Mintage**: If known, provide the mintage number (how many were produced)
   - **Diameter/Weight**: Standard measurements if known
   - **Special Designations**: (Proof, Commemorative, Error, Variety, etc.)

2. **MINT MARKS & PRODUCTION MARKINGS**
   - For coins: Identify mint mark location and letter (P, D, S, W, CC, O, etc.)
   - Location matters: Penny mint mark is below date, Quarter is behind neck/head, etc.
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

  "coin_info": {{
    "is_coin": true/false,
    "denomination": "Penny / Nickel / Dime / Quarter / Half Dollar / Dollar Coin / Other",
    "year": 0,
    "coin_type": "Lincoln Penny / Jefferson Nickel / Roosevelt Dime / Washington Quarter / Kennedy Half Dollar / Eisenhower Dollar / Sacagawea Dollar / etc.",
    "composition": "Copper / Nickel / Silver / etc.",
    "mintage": 0,
    "diameter_mm": 0.0,
    "weight_grams": 0.0,
    "special_designation": "Proof / Commemorative / Error / Variety / Standard",
    "series_info": "description of the series or variety"
  }},

  "card_type": "pokemon / mtg / yugioh / sports_nfl / sports_nba / sports_mlb / sports_nhl / tcg / unknown (ONLY if this is a card)",
  "game_name": "Pokemon / Magic: The Gathering / Yu-Gi-Oh! / etc. (ONLY for TCG cards)",
  "sport": "NFL / NBA / MLB / NHL / etc. (ONLY for sports cards)",
  "set_name": "set or series name (if this is a card)",
  "card_number": "card number (if visible on card)",
  "rarity": "rarity level (if this is a card)",
  "player_name": "player name (ONLY for sports cards)",
  "is_rookie_card": true/false,
  "is_graded": true/false,
  "grading_company": "PSA / BGS / CGC / PCGS / NGC / ANACS / etc. (if graded)",
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
"""

        # Use Claude analyzer's API call method
        try:
            content = image_parts + [{"type": "text", "text": prompt}]
            
            headers = {
                "x-api-key": self.claude_analyzer.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            payload = {
                "model": self.claude_analyzer.model,
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }

            import requests
            response = requests.post(
                self.claude_analyzer.api_url,
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()

            result = response.json()

            # Extract and parse JSON response
            if "content" in result and len(result["content"]) > 0:
                text_content = result["content"][0]["text"]
                
                # Clean JSON (remove markdown code blocks if present)
                text_content = text_content.strip()
                if text_content.startswith("```json"):
                    text_content = text_content[7:]
                if text_content.startswith("```"):
                    text_content = text_content[3:]
                if text_content.endswith("```"):
                    text_content = text_content[:-3]
                text_content = text_content.strip()

                analysis = json.loads(text_content)
                return analysis
            else:
                return {"error": "No content in Claude response"}

        except Exception as e:
            return {"error": f"Deep analysis failed: {str(e)}"}

    def _extract_text_with_chatgpt(
        self,
        photos: List[Photo]
    ) -> Dict[str, Any]:
        """
        Use ChatGPT (GPT-4 Vision) to extract text from images.

        Focused on OCR and text extraction for:
        - Serial numbers
        - Mint marks
        - Signatures
        - Dates and years
        - Manufacturing codes
        - Text on collectibles
        - Card numbers
        - Edition numbers

        Returns:
            {
                'text_found': true/false,
                'extracted_text': {...},
                'confidence': 0.0-1.0,
                'error': str (if error)
            }
        """
        if not self.openai_api_key:
            return {"error": "No OpenAI API key available", "text_found": False}

        # Prepare images
        image_contents = []
        for photo in photos[:4]:  # Limit to 4 photos
            if photo.local_path:
                local_path = Path(photo.local_path)
                if not local_path.exists():
                    continue

                # Encode image to base64
                image_bytes = local_path.read_bytes()
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                # Detect MIME type
                from PIL import Image
                try:
                    img = Image.open(local_path)
                    mime_type = {
                        'JPEG': 'image/jpeg',
                        'PNG': 'image/png',
                        'GIF': 'image/gif',
                        'WEBP': 'image/webp'
                    }.get(img.format, 'image/jpeg')
                except:
                    mime_type = 'image/jpeg'

                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_b64}"
                    }
                })

        if not image_contents:
            return {"error": "No valid images found", "text_found": False}

        # Build OCR-focused prompt
        prompt = """You are an expert OCR and text extraction specialist. Your task is to extract ALL visible text from these images with extreme precision.

CRITICAL EXTRACTION TASKS:

1. **SERIAL NUMBERS & PRODUCTION CODES:**
   - Extract any serial numbers, production numbers, or limited edition numbers
   - Include format (e.g., "SN-12345", "Limited Edition 45/500", "#0123")
   - Note location on item

2. **MINT MARKS (for coins):**
   - Identify and extract mint mark letters (P, D, S, W, CC, O, etc.)
   - Note exact location (below date, behind neck, etc.)
   - Extract the letter clearly

3. **DATES & YEARS:**
   - Extract all visible dates and years
   - Include copyright dates, manufacturing dates, release dates
   - Note format (e.g., "© 1999", "2024", "EST. 1950")

4. **SIGNATURES & AUTOGRAPHS:**
   - Transcribe any visible signatures
   - Note if signature appears hand-written vs printed
   - Describe ink characteristics (bleeding, pressure variation, etc.)
   - Indicate signature location

5. **CARD TEXT (for trading cards):**
   - Card name/title
   - Set name and number
   - Card number (e.g., "45/102")
   - Rarity indicators
   - Edition stamps (1st Edition, Limited, etc.)
   - Copyright text
   - Any small print or legal text

6. **MANUFACTURING TEXT:**
   - Brand names and logos
   - Model numbers
   - Manufacturing location (Made in USA, etc.)
   - Material composition text
   - Care instructions or labels

7. **GRADING & AUTHENTICATION TEXT:**
   - Grading company names (PSA, BGS, CGC, PCGS, NGC, etc.)
   - Grade numbers
   - Certification numbers
   - Hologram text

8. **DENOMINATION & VALUE (for currency/coins):**
   - Face value (PENNY, NICKEL, DIME, QUARTER, etc.)
   - Dollar amounts
   - Currency symbols

9. **ANY OTHER VISIBLE TEXT:**
   - Slogans
   - Taglines
   - Descriptions
   - Small print
   - Watermarks

RESPONSE FORMAT:

You MUST respond with ONLY valid JSON (no markdown, no explanations). Use this exact structure:

{
  "text_found": true,
  "confidence": 0.95,

  "serial_numbers": [
    {
      "number": "SN-12345",
      "location": "bottom right corner",
      "type": "serial number"
    }
  ],

  "mint_marks": [
    {
      "mark": "D",
      "location": "below date on obverse",
      "description": "Denver mint mark"
    }
  ],

  "dates": [
    {
      "date": "1999",
      "location": "front center",
      "type": "manufacturing year"
    },
    {
      "date": "© 1999",
      "location": "bottom edge",
      "type": "copyright"
    }
  ],

  "signatures": [
    {
      "text": "Michael Jordan",
      "location": "lower right corner",
      "appears_handwritten": true,
      "ink_notes": "Shows ink bleeding and pressure variation - likely authentic"
    }
  ],

  "card_text": {
    "card_name": "Charizard",
    "set_name": "Base Set",
    "card_number": "4/102",
    "rarity": "Rare Holo",
    "edition": "1st Edition",
    "copyright": "© 1999 Nintendo"
  },

  "grading": [
    {
      "company": "PSA",
      "grade": "9",
      "cert_number": "12345678"
    }
  ],

  "denomination": {
    "value": "QUARTER DOLLAR",
    "face_value": "25 cents"
  },

  "brand_text": [
    {
      "text": "Pokemon",
      "location": "top center",
      "type": "brand name"
    }
  ],

  "manufacturing_text": [
    {
      "text": "Made in USA",
      "location": "bottom edge"
    }
  ],

  "other_text": [
    {
      "text": "Gotta Catch 'Em All!",
      "location": "bottom",
      "type": "slogan"
    }
  ],

  "all_text_raw": "Complete transcription of ALL visible text in reading order, including every word, number, and symbol you can see.",

  "extraction_notes": "Any important observations about the text, quality of image, readability issues, or confidence notes"
}

**IMPORTANT:**
- Be extremely thorough - extract EVERY piece of text you can see
- If no text is found in a category, use an empty array []
- Include exact spelling and formatting of text
- Note if text is partially obscured or unclear
- Provide confidence level based on image quality and text clarity
- For coin mint marks, be extremely precise about the letter and location

REMEMBER: Respond with ONLY the JSON object. No markdown code blocks, no other text."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",  # GPT-4 with vision
            "messages": messages,
            "max_tokens": 3000,
            "temperature": 0.1  # Low temperature for precise extraction
        }

        try:
            import requests
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content_text = result["choices"][0]["message"]["content"]

                # Parse JSON response
                try:
                    # Clean JSON (remove markdown code blocks if present)
                    content_text = content_text.strip()
                    if content_text.startswith("```json"):
                        content_text = content_text[7:]
                    if content_text.startswith("```"):
                        content_text = content_text[3:]
                    if content_text.endswith("```"):
                        content_text = content_text[:-3]
                    content_text = content_text.strip()

                    # Find JSON object boundaries
                    if not content_text.startswith("{"):
                        start_idx = content_text.find("{")
                        if start_idx != -1:
                            content_text = content_text[start_idx:]

                    if not content_text.endswith("}"):
                        end_idx = content_text.rfind("}")
                        if end_idx != -1:
                            content_text = content_text[:end_idx + 1]

                    extracted_data = json.loads(content_text)
                    extracted_data["ai_provider"] = "chatgpt"
                    return extracted_data

                except json.JSONDecodeError as e:
                    return {
                        "text_found": False,
                        "error": f"JSON parse error: {str(e)}",
                        "raw_response": content_text[:1000]
                    }
            else:
                return {
                    "text_found": False,
                    "error": f"OpenAI API error ({response.status_code}): {response.text[:500]}"
                }

        except Exception as e:
            return {
                "text_found": False,
                "error": f"Exception during ChatGPT image-to-text: {str(e)}"
            }

    def scan_with_chatgpt_ocr(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Scan collectible using ChatGPT as PRIMARY scanner.

        ChatGPT performs BOTH:
        1. Text extraction (OCR)
        2. Deep collectible analysis

        Claude is used as fallback if ChatGPT fails.
        """
        if not photos:
            return {'error': 'No photos provided', 'type': 'standard_item'}

        # Step 1: Use ChatGPT for full deep analysis (includes text extraction)
        print("🔍 Analyzing with ChatGPT (PRIMARY scanner)...")
        deep_analysis = self._deep_analyze_collectible_chatgpt(photos)

        if deep_analysis.get('error'):
            print(f"⚠️  ChatGPT analysis failed: {deep_analysis['error']}")
            print("   Falling back to Claude...")

            # Fallback to Claude
            quick_analysis = {}
            if self.gemini_classifier:
                try:
                    quick_analysis = self.gemini_classifier.analyze_item(photos)
                    if quick_analysis.get('error'):
                        quick_analysis = {}
                except Exception:
                    quick_analysis = {}

            claude_analysis = self._deep_analyze_collectible(photos, quick_analysis)

            if claude_analysis.get('error'):
                return {
                    'error': f"Both ChatGPT and Claude failed. ChatGPT: {deep_analysis['error']}. Claude: {claude_analysis['error']}",
                    'type': 'collectible'
                }

            # Determine type and format response
            category = quick_analysis.get('category', '').lower()
            is_card = 'card' in category or 'trading card' in category or 'tcg' in category

            if is_card:
                return self._format_card_response(claude_analysis, quick_analysis)
            else:
                return self._format_collectible_response(claude_analysis, quick_analysis)

        # ChatGPT succeeded
        print("✅ ChatGPT analysis complete")

        # Determine type from ChatGPT's analysis
        is_card = deep_analysis.get('coin_info', {}).get('is_coin') == False and (
            deep_analysis.get('card_type') or
            deep_analysis.get('game_name') or
            deep_analysis.get('sport')
        )

        # Format response based on type
        quick_analysis = {}  # No Gemini needed when ChatGPT succeeds
        if is_card:
            result = self._format_card_response(deep_analysis, quick_analysis)
        else:
            result = self._format_collectible_response(deep_analysis, quick_analysis)

        # Override AI provider
        result['ai_provider'] = 'chatgpt'
        return result

    def _deep_analyze_with_extracted_text(
        self,
        photos: List[Photo],
        basic_analysis: Dict[str, Any],
        text_extraction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform deep analysis with ChatGPT-extracted text as context.
        This improves Claude's accuracy by providing pre-extracted text.
        """
        import base64

        # Prepare images for Claude
        image_parts = []
        for photo in photos[:4]:
            if photo.local_path:
                local_path = Path(photo.local_path)
                if not local_path.exists():
                    continue

                image_bytes, mime_type = self.claude_analyzer._convert_to_claude_format(str(local_path))
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                image_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_b64
                    }
                })

        if not image_parts:
            return {"error": "No valid images found"}

        # Build prompt with extracted text context
        item_name = basic_analysis.get('suggested_title') or basic_analysis.get('item_name', 'collectible item')
        brand = basic_analysis.get('brand', '')
        franchise = basic_analysis.get('franchise', '')
        category = basic_analysis.get('category', '')

        # Format extracted text for Claude
        extracted_text_summary = "**TEXT EXTRACTED FROM IMAGE (via ChatGPT OCR):**\n\n"

        if text_extraction.get('serial_numbers'):
            extracted_text_summary += "Serial Numbers Found:\n"
            for sn in text_extraction['serial_numbers']:
                extracted_text_summary += f"- {sn.get('number')} ({sn.get('location')})\n"
            extracted_text_summary += "\n"

        if text_extraction.get('mint_marks'):
            extracted_text_summary += "Mint Marks Found:\n"
            for mm in text_extraction['mint_marks']:
                extracted_text_summary += f"- {mm.get('mark')} at {mm.get('location')}\n"
            extracted_text_summary += "\n"

        if text_extraction.get('dates'):
            extracted_text_summary += "Dates Found:\n"
            for date in text_extraction['dates']:
                extracted_text_summary += f"- {date.get('date')} ({date.get('type')})\n"
            extracted_text_summary += "\n"

        if text_extraction.get('signatures'):
            extracted_text_summary += "Signatures Found:\n"
            for sig in text_extraction['signatures']:
                extracted_text_summary += f"- \"{sig.get('text')}\" at {sig.get('location')}\n"
                if sig.get('ink_notes'):
                    extracted_text_summary += f"  Notes: {sig['ink_notes']}\n"
            extracted_text_summary += "\n"

        if text_extraction.get('card_text'):
            ct = text_extraction['card_text']
            extracted_text_summary += "Card Text:\n"
            if ct.get('card_name'):
                extracted_text_summary += f"- Name: {ct['card_name']}\n"
            if ct.get('set_name'):
                extracted_text_summary += f"- Set: {ct['set_name']}\n"
            if ct.get('card_number'):
                extracted_text_summary += f"- Number: {ct['card_number']}\n"
            if ct.get('edition'):
                extracted_text_summary += f"- Edition: {ct['edition']}\n"
            extracted_text_summary += "\n"

        if text_extraction.get('all_text_raw'):
            extracted_text_summary += f"All Visible Text:\n{text_extraction['all_text_raw']}\n\n"

        prompt = f"""You are an expert collectibles appraiser specializing in authentication, valuation, and historical research.

I need you to perform a COMPREHENSIVE DEEP ANALYSIS of this collectible item, with particular attention to collector value indicators.

{extracted_text_summary}

**BASIC INFORMATION:**
- Item: {item_name}
- Brand/Manufacturer: {brand}
- Franchise/Series: {franchise}
- Category: {category}

**YOUR CRITICAL TASK - Focus on Collector Value Indicators:**

1. **COIN IDENTIFICATION** (CRITICAL FOR COINS - Skip if not a coin)
   - Use the extracted text above to identify denomination, year, and mint mark
   - **Denomination**: Identify the exact coin type (Penny/Cent, Nickel, Dime, Quarter, Half Dollar, Dollar Coin, Other)
   - **Year**: Use the date extracted above (visible on the coin)
   - **Mint Mark**: Use the mint mark extracted above (P=Philadelphia, D=Denver, S=San Francisco, W=West Point, CC=Carson City, O=New Orleans, etc.)
   - **Coin Type/Series**: (Lincoln Penny, Jefferson Nickel, Roosevelt Dime, Washington Quarter, Kennedy Half Dollar, Eisenhower Dollar, Sacagawea Dollar, etc.)
   - **Composition**: Material (Copper, Nickel, Silver, etc.) - identify by year and appearance
   - **Mintage**: If known, provide the mintage number (how many were produced)
   - **Diameter/Weight**: Standard measurements if known
   - **Special Designations**: (Proof, Commemorative, Error, Variety, etc.)

2. **MINT MARKS & PRODUCTION MARKINGS**
   - Use the extracted mint marks above
   - For coins: Verify mint mark location and letter from extracted text
   - For collectibles: Use extracted production facility marks, factory codes from text extraction
   - Note any special mint marks or rare production locations
   - Explain the significance of the mint mark for value

3. **SERIAL NUMBERS & LIMITED EDITION MARKINGS**
   - Use the serial numbers extracted above
   - Note if it's a numbered edition (e.g., "123/500", "Limited Edition #45")
   - Identify certificate numbers, authentication numbers, or tracking numbers
   - Explain how the serial number affects value (lower numbers often more valuable)

4. **SIGNATURES & AUTOGRAPHS**
   - Use the signatures extracted above
   - Identify the signer if possible
   - Assess signature authenticity using the ink notes from ChatGPT extraction
   - Note signature placement and condition
   - Explain the value impact of signatures

5. **ERRORS, VARIATIONS & MANUFACTURING DEFECTS**
   - Look for error coins (misprints, double strikes, off-center strikes, etc.)
   - Check for printing errors (misprints, color errors, cut errors)
   - Identify factory defects or variations
   - Note any unique manufacturing anomalies
   - Explain how errors/variations affect value (errors can be valuable!)

6. **HISTORICAL CONTEXT & BACKSTORY**
   - Use the dates extracted above for historical context
   - Research and provide a compelling short history/backstory of this SPECIFIC item
   - When was it produced/released? What was happening at that time?
   - Why is this item significant to collectors?
   - What makes it rare or desirable?
   - Include interesting facts or context that give the item character
   - Explain its place in collecting history

7. **AUTHENTICATION & CONDITION**
   - Verify authenticity markers
   - Assess condition and grading
   - Note any concerns or red flags
   - Identify authentication markers visible in photos

8. **MARKET VALUE ANALYSIS**
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

  "coin_info": {{
    "is_coin": true/false,
    "denomination": "Penny / Nickel / Dime / Quarter / Half Dollar / Dollar Coin / Other",
    "year": 0,
    "coin_type": "Lincoln Penny / Jefferson Nickel / Roosevelt Dime / Washington Quarter / Kennedy Half Dollar / Eisenhower Dollar / Sacagawea Dollar / etc.",
    "composition": "Copper / Nickel / Silver / etc.",
    "mintage": 0,
    "diameter_mm": 0.0,
    "weight_grams": 0.0,
    "special_designation": "Proof / Commemorative / Error / Variety / Standard",
    "series_info": "description of the series or variety"
  }},

  "card_type": "pokemon / mtg / yugioh / sports_nfl / sports_nba / sports_mlb / sports_nhl / tcg / unknown (ONLY if this is a card)",
  "game_name": "Pokemon / Magic: The Gathering / Yu-Gi-Oh! / etc. (ONLY for TCG cards)",
  "sport": "NFL / NBA / MLB / NHL / etc. (ONLY for sports cards)",
  "set_name": "set or series name (if this is a card)",
  "card_number": "card number (if visible on card)",
  "rarity": "rarity level (if this is a card)",
  "player_name": "player name (ONLY for sports cards)",
  "is_rookie_card": true/false,
  "is_graded": true/false,
  "grading_company": "PSA / BGS / CGC / PCGS / NGC / ANACS / etc. (if graded)",
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
- Use the text extracted by ChatGPT OCR above to fill in details
- Be thorough in examining images for mint marks, serial numbers, signatures, and errors
- Provide a compelling, interesting backstory that gives the item character
- Be specific about what you see - exact numbers, letters, locations
- If you cannot determine something, set present: false and explain why in significance/notes
- Errors and variations can SIGNIFICANTLY increase value - don't miss them!
- Make the backstory engaging - collectors love knowing the history behind their items
- Be honest about confidence levels - if uncertain, indicate that
"""

        # Use Claude analyzer's API call method
        try:
            content = image_parts + [{"type": "text", "text": prompt}]

            headers = {
                "x-api-key": self.claude_analyzer.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            payload = {
                "model": self.claude_analyzer.model,
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }

            import requests
            response = requests.post(
                self.claude_analyzer.api_url,
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()

            result = response.json()

            # Extract and parse JSON response
            if "content" in result and len(result["content"]) > 0:
                text_content = result["content"][0]["text"]

                # Clean JSON (remove markdown code blocks if present)
                text_content = text_content.strip()
                if text_content.startswith("```json"):
                    text_content = text_content[7:]
                if text_content.startswith("```"):
                    text_content = text_content[3:]
                if text_content.endswith("```"):
                    text_content = text_content[:-3]
                text_content = text_content.strip()

                analysis = json.loads(text_content)
                return analysis
            else:
                return {"error": "No content in Claude response"}

        except Exception as e:
            return {"error": f"Deep analysis failed: {str(e)}"}

    def _format_collectible_response(
        self,
        deep_analysis: Dict[str, Any],
        basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format deep analysis as collectible response"""
        
        # Extract market prices
        market_analysis = deep_analysis.get('market_analysis', {})
        market_prices = {
            'retail': market_analysis.get('estimated_value') or market_analysis.get('current_market_value_high'),
            'actual_selling': market_analysis.get('estimated_value'),
            'quick_sale': market_analysis.get('current_market_value_low'),
            'value_range': {
                'low': market_analysis.get('current_market_value_low', 0),
                'high': market_analysis.get('current_market_value_high', 0)
            }
        }

        # Build collectible data object
        collectible_data = {
            'item_name': deep_analysis.get('item_name') or basic_analysis.get('suggested_title', 'Unknown Collectible'),
            'franchise': deep_analysis.get('franchise') or basic_analysis.get('franchise', ''),
            'brand': deep_analysis.get('brand') or basic_analysis.get('brand', ''),
            'category': deep_analysis.get('category') or basic_analysis.get('category', ''),

            # Coin-specific information
            'coin_info': deep_analysis.get('coin_info', {}),
            'is_coin': deep_analysis.get('coin_info', {}).get('is_coin', False),

            # Key collector attributes
            'mint_mark': deep_analysis.get('mint_mark', {}),
            'serial_number': deep_analysis.get('serial_number', {}),
            'signature': deep_analysis.get('signature', {}),
            'errors_variations': deep_analysis.get('errors_variations', {}),
            'historical_context': deep_analysis.get('historical_context', {}),

            # Condition and authentication
            'condition': deep_analysis.get('condition', {}),
            'authentication': deep_analysis.get('authentication', {}),

            # Display-friendly fields
            'item_significance': deep_analysis.get('historical_context', {}).get('backstory', ''),
            'rarity_info': deep_analysis.get('collector_notes', ''),
            'authentication_markers': deep_analysis.get('authentication', {}).get('authentication_markers', []),

            # Market info
            'market_analysis': market_analysis,
            'collector_notes': deep_analysis.get('collector_notes', '')
        }

        return {
            'type': 'collectible',
            'data': collectible_data,
            'market_prices': market_prices,
            'ai_provider': 'claude'
        }

    def _format_card_response(
        self,
        deep_analysis: Dict[str, Any],
        basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format deep analysis as card response"""
        
        # Extract market prices
        market_analysis = deep_analysis.get('market_analysis', {})
        market_prices = {
            'tcgplayer': {'market': market_analysis.get('estimated_value')},
            'ebay': {'avg': market_analysis.get('estimated_value')},
            'actual_selling': market_analysis.get('estimated_value'),
            'quick_sale': market_analysis.get('current_market_value_low')
        }

        # Determine card type and franchise from analysis
        franchise = deep_analysis.get('franchise') or basic_analysis.get('franchise', '')
        category = basic_analysis.get('category', '').lower()
        
        # Determine card type from franchise/category
        card_type = 'unknown'
        game_name = None
        sport = None
        
        if 'pokemon' in franchise.lower() or 'pokemon' in category:
            card_type = 'pokemon'
            game_name = 'Pokemon'
        elif 'magic' in franchise.lower() or 'mtg' in franchise.lower() or 'magic' in category:
            card_type = 'mtg'
            game_name = 'Magic: The Gathering'
        elif 'yugioh' in franchise.lower() or 'yu-gi-oh' in franchise.lower() or 'yugioh' in category:
            card_type = 'yugioh'
            game_name = 'Yu-Gi-Oh!'
        elif 'football' in franchise.lower() or 'nfl' in franchise.lower() or 'football' in category:
            card_type = 'sports_nfl'
            sport = 'NFL'
        elif 'basketball' in franchise.lower() or 'nba' in franchise.lower() or 'basketball' in category:
            card_type = 'sports_nba'
            sport = 'NBA'
        elif 'baseball' in franchise.lower() or 'mlb' in franchise.lower() or 'baseball' in category:
            card_type = 'sports_mlb'
            sport = 'MLB'
        elif 'hockey' in franchise.lower() or 'nhl' in franchise.lower() or 'hockey' in category:
            card_type = 'sports_nhl'
            sport = 'NHL'
        elif basic_analysis.get('is_sports_card'):
            card_type = 'sports'
        elif 'trading card' in category or 'tcg' in category:
            card_type = 'tcg'
        
        # Get card-specific fields from Claude's deep analysis (he may have extracted these)
        claude_card_type = deep_analysis.get('card_type', '').lower() if deep_analysis.get('card_type') else ''
        claude_game_name = deep_analysis.get('game_name', '')
        claude_sport = deep_analysis.get('sport', '')
        claude_set_name = deep_analysis.get('set_name', '') or deep_analysis.get('historical_context', {}).get('series', '')
        claude_card_number = deep_analysis.get('card_number', '')
        claude_rarity = deep_analysis.get('rarity', '')
        claude_player_name = deep_analysis.get('player_name', '')
        claude_franchise = deep_analysis.get('franchise', '')
        
        # Use Claude's analysis if available, otherwise fall back to our detection
        if claude_card_type and claude_card_type != 'unknown':
            card_type = claude_card_type
        if claude_game_name:
            game_name = claude_game_name
        if claude_sport:
            sport = claude_sport
        if claude_franchise:
            franchise = claude_franchise
        
        # Build card data object with all required fields for storage maps
        card_data = {
            'card_name': deep_analysis.get('item_name') or basic_analysis.get('suggested_title', 'Unknown Card'),
            'player_name': claude_player_name or basic_analysis.get('player_name', ''),
            'set_name': claude_set_name or basic_analysis.get('set_name', '') or deep_analysis.get('historical_context', {}).get('series', ''),
            'set_code': basic_analysis.get('set_code', ''),
            'card_number': claude_card_number or basic_analysis.get('card_number', ''),
            'card_type': card_type,
            'game_name': claude_game_name or game_name,
            'franchise': franchise,
            'rarity': claude_rarity or basic_analysis.get('rarity', ''),
            'year': deep_analysis.get('historical_context', {}).get('release_year') or basic_analysis.get('year'),
            'brand': deep_analysis.get('brand') or basic_analysis.get('brand', ''),
            'sport': claude_sport or basic_analysis.get('sport', ''),
            
            # Key collector attributes
            'serial_number': deep_analysis.get('serial_number', {}),
            'signature': deep_analysis.get('signature', {}),
            'errors_variations': deep_analysis.get('errors_variations', {}),
            'historical_context': deep_analysis.get('historical_context', {}),
            
            # Condition and authentication
            'condition': deep_analysis.get('condition', {}),
            'authentication': deep_analysis.get('authentication', {}),
            'is_graded': basic_analysis.get('is_graded', False),
            'grading_company': basic_analysis.get('grading_company', ''),
            'grading_score': basic_analysis.get('grading_score'),
            'is_rookie_card': basic_analysis.get('is_rookie_card', False),
            
            'estimated_value_low': market_analysis.get('current_market_value_low', 0),
            'estimated_value_high': market_analysis.get('current_market_value_high', 0),
            'collector_notes': deep_analysis.get('collector_notes', ''),
            'is_card': True  # Mark as card for vault saving
        }

        return {
            'type': 'card',
            'data': card_data,
            'market_prices': market_prices,
            'ai_provider': 'claude'
        }

