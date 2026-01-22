# AI Photo Analyzer - Configuration Guide

The AI Photo Analyzer automatically identifies products, generates descriptions, estimates prices, and extracts metadata from product photos.

## 🎯 Supported AI Providers

The analyzer supports **3 provider options** with automatic fallback:

1. **Ollama** (Local, FREE) - Run AI on your own machine
2. **Nebius AI Studio** (Cloud, CHEAP) - OpenAI-compatible with open-source models
3. **OpenAI** (Cloud, PREMIUM) - ChatGPT/GPT-4 Vision
4. **Anthropic Claude** (Cloud, PREMIUM) - Claude with vision

**Recommended setup:** Use **Nebius** for the best balance of cost, reliability, and performance.

---

## 📊 Provider Comparison

| Provider | Cost/Image | Speed | Quality | Setup | Best For |
|----------|-----------|-------|---------|-------|----------|
| **Ollama** | $0.00 | Medium-Fast | Good | Complex | Privacy & offline use |
| **Nebius** | ~$0.001 | Fast | Excellent | Easy | **Production use** ⭐ |
| **OpenAI** | ~$0.01-0.05 | Fast | Excellent | Easy | Premium quality |
| **Claude** | ~$0.01-0.03 | Fast | Excellent | Easy | Alternative to OpenAI |

---

## 🚀 Quick Start: Nebius (Recommended)

**Why Nebius?**
- ✅ OpenAI-compatible API (drop-in replacement)
- ✅ Open-source models (Qwen, Llama, etc.)
- ✅ **~100x cheaper** than OpenAI ($0.001 vs $0.01 per image)
- ✅ Sub-second latency, 99.9% uptime
- ✅ No tunneling or local setup required

### 1. Sign Up

Go to: https://studio.nebius.ai/
- Sign up for free account
- Add credits ($5-10 recommended)

### 2. Get API Key

In Nebius Dashboard:
- Go to **API Keys**
- Create new key
- Copy the API key

### 3. Configure Environment Variables

Add to your `.env` file or Render environment:

```bash
# Enable OpenAI provider (Nebius is OpenAI-compatible)
USE_OPENAI=true
USE_OLLAMA=false
USE_ANTHROPIC=false

# Nebius configuration
OPENAI_API_KEY=your-nebius-api-key-here
OPENAI_BASE_URL=https://api.studio.nebius.ai/v1
OPENAI_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
```

### 4. Recommended Models

Nebius offers multiple vision-capable models:

**Best Quality:**
- `Qwen/Qwen2.5-VL-72B-Instruct` - High-end multimodal ($0.25/1M in, $0.75/1M out) ⭐
- Premium vision-language model for accurate product analysis

**Budget Option:**
- `nvidia/Nemotron-Nano-V2-12b` - Compact model ($0.07/1M in, $0.20/1M out)
- Fast (70 tok/s) and efficient

**Other Options:**
- `google/Gemma-3-27b-it` - Google's instruction-tuned model
- Check Nebius dashboard for latest available models

### 5. Deploy & Test

Restart your app and analyze a photo. You should see:
```
🤖 ChatGPT analyzing photos (paid fallback)...
✅ ChatGPT successfully identified the item
```

*Note: Even though it says "ChatGPT", it's actually using Nebius since you set `OPENAI_BASE_URL`.*

---

## 💰 Cost Breakdown

### Nebius Pricing (Qwen2.5-VL-72B)

**Per image analysis:**
- Input: ~1,000 tokens (image + prompt) = $0.00025
- Output: ~500 tokens (description) = $0.00038
- **Total: ~$0.0006 per image**

**100 analyses:** $0.06
**1,000 analyses:** $0.60
**10,000 analyses:** $6.00

Compare to OpenAI GPT-4 Vision: **~$15-50 for 1,000 images**

---

## 🏠 Option 2: Local Ollama (Free)

**Best for:** Privacy, offline use, unlimited analyses

See full guide: [`OLLAMA_SETUP.md`](./OLLAMA_SETUP.md)

### Quick Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull vision model
ollama pull llama3.2-vision:11b
```

### Environment Variables

```bash
USE_OLLAMA=true
USE_OPENAI=false
OLLAMA_MODEL=llama3.2-vision:11b
OLLAMA_HOST=http://localhost:11434
```

### Pros & Cons

✅ **Pros:**
- 100% free (no API costs)
- Complete privacy (data never leaves your machine)
- Unlimited usage
- Works offline

❌ **Cons:**
- Requires local setup (Ollama installation)
- Needs ~8GB RAM for 11B model
- Slower on CPU (faster with GPU)
- First analysis slow (model loading ~2-3 min)

---

## 🌐 Option 3: Remote Ollama via Tunnel

Run Ollama on a powerful machine and expose it via tunnel.

**Use cases:**
- Run Ollama on GPU server
- Share one Ollama instance across multiple deployments
- Deploy to cloud (Render, Vercel) while using local AI

### With Cloudflare Tunnel (Recommended - FREE)

```bash
# On machine with Ollama (Windows/Mac/Linux)
# 1. Install cloudflared
winget install --id Cloudflare.cloudflared
# OR: brew install cloudflared
# OR: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# 2. Start Ollama
ollama serve

# 3. Create tunnel
cloudflared tunnel --url http://localhost:11434
```

Copy the URL (e.g., `https://random-words-123.trycloudflare.com`)

### Environment Variables

```bash
USE_OLLAMA=true
OLLAMA_HOST=https://random-words-123.trycloudflare.com
OLLAMA_MODEL=llama3.2-vision:11b
```

### With ngrok (Paid - $8/month)

```bash
# Install ngrok
brew install ngrok
# OR: https://ngrok.com/download

# Start tunnel
ngrok http 11434
```

*Note: ngrok free tier blocks API requests with 403. Use Cloudflare Tunnel instead.*

---

## 🔧 Option 4: OpenAI (Premium)

**Best for:** Maximum quality, simple setup

### Environment Variables

```bash
USE_OPENAI=true
USE_OLLAMA=false
OPENAI_API_KEY=sk-proj-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### Cost

- **gpt-4o:** ~$0.01-0.05 per image
- **gpt-4-turbo:** ~$0.01-0.03 per image

Get API key: https://platform.openai.com/api-keys

---

## 🔧 Option 5: Anthropic Claude

### Environment Variables

```bash
USE_ANTHROPIC=true
USE_OPENAI=false
USE_OLLAMA=false
ANTHROPIC_API_KEY=sk-ant-...
```

Get API key: https://console.anthropic.com/

---

## 🎨 What the AI Analyzer Provides

For each photo analysis, you get:

1. **Title** - SEO-optimized, keyword-rich (under 80 chars)
2. **Description** - 2-3 paragraphs covering features, condition, value
3. **SEO Keywords** - 15-20 relevant search terms
4. **Search Terms** - Alternative phrases buyers use
5. **Category** - Suggested category (e.g., "Electronics > Cameras")
6. **Item Specifics** - Brand, model, color, size, material
7. **Condition Notes** - Observations about item condition
8. **Features** - Bullet points of key selling points
9. **Estimated Price** - Fair market value in USD ⭐ NEW

---

## ⚙️ Advanced Configuration

### Multiple Providers (Fallback Chain)

Enable multiple providers for redundancy:

```bash
# Try Nebius first, fallback to OpenAI if it fails
USE_OPENAI=true
OPENAI_API_KEY=your-nebius-key
OPENAI_BASE_URL=https://api.studio.nebius.ai/v1
OPENAI_MODEL=Qwen/Qwen2.5-VL-72B-Instruct

# Keep OpenAI as backup (optional)
# If Nebius fails, set USE_OPENAI=true and remove OPENAI_BASE_URL
```

### Priority Order

The analyzer tries providers in this order:

1. **Ollama** (if `USE_OLLAMA=true`)
2. **OpenAI/Nebius** (if `USE_OPENAI=true`)
3. **Claude** (if `USE_ANTHROPIC=true`)

First provider that returns complete data (title + description + category) wins.

### Disable Specific Providers

```bash
# Only use Nebius (no fallbacks)
USE_OLLAMA=false
USE_OPENAI=true
USE_ANTHROPIC=false
```

---

## 🐛 Troubleshooting

### "AI service not configured" Error

**Cause:** No AI providers enabled or no API keys set

**Fix:** Set at least one provider:
```bash
USE_OPENAI=true
OPENAI_API_KEY=your-key-here
```

### Nebius Returns Empty Response

**Cause:** Wrong model name or API endpoint

**Fix:** Check exact model name in Nebius dashboard:
- Model names are case-sensitive
- Use format: `Qwen/Qwen2.5-VL-72B-Instruct` (not `qwen2.5-vl-72b`)

### Price Estimation Missing

**Cause:** Old code version or AI didn't return price

**Fix:**
1. Make sure you're on latest code (includes price estimation prompt)
2. Some models may not return price - it's optional
3. Check logs for `estimated_price` field in AI response

### Ollama Timeout Errors

**Cause:** Model loading takes too long (first run)

**Fix:**
- First analysis: Wait 3-5 minutes (model loads into RAM)
- Subsequent analyses: Fast (~10-60 seconds)
- Increase timeout: `OLLAMA_TIMEOUT=600` (10 minutes)

### ngrok 403 Forbidden

**Cause:** ngrok free tier blocks API requests

**Fix:** Use Cloudflare Tunnel instead (free, no restrictions)

---

## 📊 Performance Tips

### Speed Optimization

1. **Use Nebius with Fast config** - Sub-second response time
2. **Keep Ollama model loaded** - Set `keep_alive: "1h"` (already configured)
3. **Limit photo count** - Analyzer uses max 4 photos per analysis
4. **Use smaller images** - Resize to 1024x1024 before upload

### Cost Optimization

1. **Use Nebius instead of OpenAI** - 100x cheaper
2. **Use local Ollama** - 100% free
3. **Disable unnecessary fallbacks** - Only enable providers you need
4. **Batch analyses** - Process multiple items together

### Quality Optimization

1. **Use high-quality photos** - Well-lit, clear focus
2. **Multiple angles** - Show different views of item
3. **Use premium models** - Qwen2.5-VL-72B or GPT-4o for best results
4. **Include closeups** - Detail shots for condition assessment

---

## 🔐 Security Notes

### API Keys

- Never commit API keys to git
- Use environment variables or secret managers
- Rotate keys periodically
- Use separate keys for dev/staging/production

### Privacy

**Ollama (local):**
- ✅ Data never leaves your machine
- ✅ No logging or tracking
- ✅ Full privacy

**Nebius/OpenAI/Claude:**
- ⚠️ Photos sent to third-party API
- ⚠️ Subject to provider's terms of service
- Check provider privacy policies:
  - Nebius: https://nebius.com/privacy
  - OpenAI: https://openai.com/policies/privacy-policy
  - Anthropic: https://anthropic.com/privacy

---

## 📚 Related Documentation

- [Ollama Setup Guide](./OLLAMA_SETUP.md) - Detailed local AI setup
- [Master Ledger System](./MASTER_LEDGER_SYSTEM.md) - Inventory tracking
- [Import System](./IMPORT_SYSTEM.md) - Import from platforms
- [Deployment Guide](./setup-deployment/DEPLOYMENT.md) - Deploy to Render

---

## 🆘 Support

**Issues?**
- Check troubleshooting section above
- Review logs for specific error messages
- Ensure environment variables are set correctly

**Need help?**
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Check provider status pages:
  - Nebius: https://status.nebius.com/
  - OpenAI: https://status.openai.com/
  - Anthropic: https://status.anthropic.com/

---

**Last Updated:** 2026-01-22
**Tested With:** Nebius Qwen2.5-VL-72B, Ollama llama3.2-vision:11b, OpenAI gpt-4o
