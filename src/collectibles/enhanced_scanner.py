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

    def __init__(self, claude_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
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
        
        Args:
            photos: List of Photo objects to analyze
            
        Returns:
            {
                'type': 'collectible' | 'card' | 'standard_item',
                'data': {...collectible data...},
                'market_prices': {...pricing info...},
                'ai_provider': 'claude',
                'error': str (if error occurred)
            }
        """
        if not photos:
            return {'error': 'No photos provided', 'type': 'standard_item'}

        # Optional: Get basic context from Gemini (if available) for better Claude analysis
        quick_analysis = {}
        if self.gemini_classifier:
            try:
                quick_analysis = self.gemini_classifier.analyze_item(photos)
                if quick_analysis.get('error'):
                    quick_analysis = {}
            except Exception as e:
                quick_analysis = {}
                print(f"Warning: Quick classification failed: {e}")

        # Always run Claude deep analysis - let Claude determine if it's a collectible/card
        # Don't reject based on Gemini's initial classification since user clicked Enhanced Scan
        try:
            deep_analysis = self._deep_analyze_collectible(photos, quick_analysis)
            
            if deep_analysis.get('error'):
                return {
                    'error': deep_analysis['error'],
                    'type': 'collectible',  # Default to collectible if error
                    'raw_response': deep_analysis.get('raw_response')
                }

            # Determine type from Claude's analysis or fallback to quick_analysis hints
            category = quick_analysis.get('category', '').lower()
            is_card = 'card' in category or 'trading card' in category or 'tcg' in category
            
            # Format response based on determined type
            if is_card:
                return self._format_card_response(deep_analysis, quick_analysis)
            else:
                return self._format_collectible_response(deep_analysis, quick_analysis)
                
        except Exception as e:
            import traceback
            import os
            error_trace = traceback.format_exc()
            print(f"Enhanced scan error: {e}\n{error_trace}")
            return {
                'error': str(e),
                'type': 'collectible',  # Default type
                'raw_response': error_trace if os.getenv('FLASK_DEBUG') else None
            }

    def _deep_analyze_collectible(
        self,
        photos: List[Photo],
        basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
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

