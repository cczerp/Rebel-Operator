# AI Analyzer Setup Instructions

## Getting Image Analysis Working

The AI analyzer feature uses two AI services:
1. **Google Gemini** - Fast classification and basic analysis
2. **Anthropic Claude** - Deep collectible analysis (authentication, grading, valuation)

Both require API keys to be configured.

## Required Environment Variables

Set these in your Render.com environment variables:

### 1. Gemini API Key (Required for basic analysis)

**Variable Name**: `GEMINI_API_KEY`

**How to get it**:
1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key
4. Add to Render environment variables as `GEMINI_API_KEY`

**What it does**:
- Classifies items (clothing, collectibles, cards, etc.)
- Detects brands, categories, conditions
- Quick initial scan of uploaded photos

### 2. Anthropic API Key (Required for collectible deep analysis)

**Variable Name**: `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY`)

**How to get it**:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to **API Keys** section
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)
6. Add to Render environment variables as `ANTHROPIC_API_KEY`

**What it does**:
- Deep analysis of collectibles (cards, vintage items, etc.)
- Authentication verification
- Condition grading
- Market value estimation
- Fraud detection

## AI Analysis Flow

### Stage 1: Gemini Classification (Always runs first)
```
User uploads photos → Gemini analyzes →
  If collectible detected → Stage 2 activates
  If regular item → Enhanced analyzer disabled
```

### Stage 2: Claude Deep Analysis (Only for collectibles)
```
Collectible detected → User clicks "Enhanced Analyzer" →
  Claude performs deep analysis →
  Returns authentication, grading, market value
```

## Testing the AI Analyzers

### Test Basic AI Analysis (Gemini)
1. Upload photos of any item
2. Click **"Analyze with AI"** button
3. Wait for results
4. Should see: title, description, category, price suggestion

**Expected behavior**:
- Button becomes enabled after photo upload
- Progress bar shows during analysis
- Results populate the form fields
- If collectible detected: Enhanced Analyzer button becomes available

### Test Enhanced Analyzer (Claude)
1. Upload photos of a collectible (card, vintage item, etc.)
2. Click **"Analyze with AI"**
3. Wait for Gemini to detect it's a collectible
4. Click **"Enhanced Analyzer"** button (should now be enabled)
5. Wait for deep analysis
6. Should see detailed collectible info

**Expected behavior**:
- Only enabled for collectibles
- Shows authentication details
- Shows grading information
- Shows market value estimates

## Troubleshooting

### "No API key found" errors

**Check browser console** (Press F12):
- Look for error messages mentioning API keys
- Error will specify which service failed (Gemini or Claude)

**Check Render logs**:
```bash
# Look for these errors:
[AI ERROR] GEMINI_API_KEY not configured
[AI ERROR] ANTHROPIC_API_KEY not configured
```

**Fix**:
1. Go to Render dashboard
2. Select your service
3. Go to **Environment** tab
4. Add the missing keys:
   - `GEMINI_API_KEY=your-gemini-key-here`
   - `ANTHROPIC_API_KEY=your-claude-key-here`
5. Click **Save Changes**
6. Render will automatically redeploy

### "Analysis failed" errors

**Possible causes**:
1. **Invalid API key** - Check that you copied the full key correctly
2. **API quota exceeded** - Check your usage at:
   - Gemini: https://aistudio.google.com/app/apikey
   - Claude: https://console.anthropic.com/settings/billing
3. **Network timeout** - Try uploading fewer/smaller photos

### Photos upload but AI doesn't analyze

**Check**:
1. Are photos actually uploaded? (Should see thumbnails)
2. Is "Analyze with AI" button enabled?
3. Click the button - what happens?
4. Check browser console for errors
5. Check Render logs for server errors

**Common issues**:
- Photos didn't upload successfully (check Supabase setup)
- API keys not configured
- Photos too large (compress to < 5MB each)

### Enhanced Analyzer button stays disabled

**This is normal if**:
- Item is not a collectible (clothing, regular items, etc.)
- Gemini analysis hasn't run yet
- Gemini didn't detect item as collectible

**Try**:
1. Upload photos of clearly collectible items:
   - Trading cards (Pokemon, Magic, sports cards)
   - Vintage toys
   - Comics
   - Coins or stamps
2. Run basic analysis first
3. Enhanced Analyzer should activate if collectible detected

## Cost Considerations

### Gemini
- Free tier: 60 requests/minute
- Should be sufficient for normal use
- Costs: Free for most users

### Claude
- Paid service (no free tier)
- Cost: ~$0.01-0.05 per image analysis
- Only runs for collectibles (saves money)
- Monthly bill depends on usage

**Recommendation**: Start with just Gemini configured. Add Claude later if you need collectible analysis.

## Quick Start (Minimal Setup)

**Just want basic AI to work?**
1. Get Gemini API key (free): https://aistudio.google.com/app/apikey
2. Add to Render: `GEMINI_API_KEY=your-key-here`
3. Save and redeploy
4. Test upload → Should get basic analysis

**Want full collectible analysis?**
1. Complete basic setup above
2. Get Claude API key: https://console.anthropic.com/
3. Add to Render: `ANTHROPIC_API_KEY=your-key-here`
4. Save and redeploy
5. Test with collectible photos → Should get enhanced analysis

## Verification Checklist

- [ ] `GEMINI_API_KEY` set in Render environment
- [ ] `ANTHROPIC_API_KEY` set in Render environment (optional, for collectibles)
- [ ] Service redeployed after adding keys
- [ ] Photos upload successfully (see SUPABASE_SETUP.md)
- [ ] "Analyze with AI" button enabled after upload
- [ ] Clicking button shows progress/results
- [ ] No errors in browser console
- [ ] No errors in Render logs
