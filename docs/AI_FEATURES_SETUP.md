# AI Features Setup Guide

## Overview

Resell Rebel includes powerful AI features for analyzing products, cards, and collectibles. These features require API keys from Google's Gemini AI service (and optionally other AI providers).

## Required API Keys

### Gemini AI (Required)
The "Analyze with AI" and "Enhanced Analyzer" buttons require a Gemini API key.

**How to get your Gemini API key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy the generated key

**Add to your `.env` file:**
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Optional API Keys

#### OpenAI (Optional - for enhanced features)
```
OPENAI_API_KEY=your_openai_key_here
```

#### Claude/Anthropic (Optional - for collectible analysis)
```
CLAUDE_API_KEY=your_claude_key_here
```

## AI Features Available

### 1. Analyze with AI Button
**Location:** Create Listing page (after uploading photos)

**What it does:**
- Analyzes uploaded photos using Google Gemini AI
- Detects item type, brand, condition, color, size
- Suggests title, description, and pricing
- Identifies trading cards and collectibles
- Provides market analysis and sell-through rates

**Requirements:**
- `GEMINI_API_KEY` must be set
- At least one photo uploaded

### 2. Enhanced Analyzer Button
**Location:** Create Listing page (after running basic AI analysis)

**What it does:**
- Deep analysis for collectibles and trading cards
- Authentication check for potential counterfeits
- Grading assessment (centering, corners, edges, surface)
- Rarity detection and variant identification
- Market trends and pricing recommendations
- Fraud detection and red flags

**Requirements:**
- `GEMINI_API_KEY` must be set
- Basic AI analysis completed first
- Works best with collectibles, trading cards, sports cards

### 3. Card Scanner
**Location:** Card Collection page

**What it does:**
- Identifies trading cards (Pokémon, MTG, Yu-Gi-Oh!, Sports)
- Extracts card details (name, set, number, year)
- Detects grading and condition
- Estimates value ranges

**Requirements:**
- `GEMINI_API_KEY` must be set
- Clear photo of the card

### 4. Photo Editor AI Features
**Location:** Photo editor (click any uploaded photo)

**What it does:**
- Remove background from photos (FREE feature)
- Enlarge photos using AI
- Smart cropping

**Requirements:**
- `GEMINI_API_KEY` for background removal
- Works with any uploaded photo

## Button States

### Enabled State
- **Appearance:** Steel blue-grey gradient with white text
- **Visual:** Prominent shadows and edge highlights
- **Hover:** Glowing effect and slight elevation
- **Indicates:** Feature is ready to use

### Disabled State
- **Appearance:** Dim charcoal gradient, faded text
- **Visual:** Minimal shadows, low opacity
- **Indicates:** Prerequisites not met (no photos uploaded, API key missing, etc.)

## Troubleshooting

### "AI service not configured" Error
**Cause:** `GEMINI_API_KEY` is not set or invalid

**Solution:**
1. Check that `.env` file exists in project root
2. Verify `GEMINI_API_KEY=...` line is present and correct
3. Restart the application after adding the key
4. Make sure there are no extra spaces or quotes around the key

### Button is Disabled/Greyed Out

**For "Analyze with AI":**
- Upload at least one photo first
- Check that `GEMINI_API_KEY` is configured

**For "Enhanced Analyzer":**
- Run basic "Analyze with AI" first
- Item must be detected as a collectible or card
- Check that `GEMINI_API_KEY` is configured

### Analysis Takes Too Long
- Analysis can take 10-60 seconds depending on photo count
- The system polls for results every 2 seconds
- A loading spinner indicates processing is active
- If timeout occurs after 60-90 seconds, try with fewer photos

## API Usage & Costs

### Gemini AI
- **Free tier:** 60 requests per minute
- **Cost:** Most requests are free under Google's generous limits
- **Rate limits:** Handled automatically with retry logic

### Best Practices
1. Upload 1-3 high-quality photos for best results
2. Ensure photos are well-lit and focused
3. For cards: capture the entire card clearly
4. For collectibles: include multiple angles if needed

## Color Scheme Reference

Per the SYSTEM_CONTRACT.md, AI buttons follow the brand color hierarchy:

- **Primary Actions (Red #DC2626):** Post Now, Create Listing
- **Secondary Actions (Steel #475569):** Analyze with AI, Enhanced Analyzer
- **Utility Actions (Charcoal #1F2937):** Save Draft, View Drafts

AI buttons use steel blue-grey to indicate they are important secondary features, not primary workflow actions.

## Support

If you continue to have issues with AI features:
1. Check console logs in browser developer tools
2. Verify your API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Ensure your internet connection is stable
4. Review application logs for detailed error messages

## Future Enhancements

Planned improvements to AI features:
- Batch photo analysis for multiple items
- Image quality enhancement before analysis
- Multi-language support for international listings
- Integration with additional AI providers
- Voice-to-text for faster listing creation
