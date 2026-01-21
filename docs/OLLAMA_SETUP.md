# Ollama Setup - FREE Local AI for Photo Analysis

Ollama lets you run AI vision models **locally** and **for free** - no API costs!

## 🚀 Quick Start

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from https://ollama.com/download

### 2. Start Ollama Service

```bash
ollama serve
```

Keep this running in the background (or it will auto-start on macOS/Windows).

### 3. Pull the Vision Model

Pull Meta's LLaMA 3.2 Vision model (11B parameters):

```bash
ollama pull llama3.2-vision:11b
```

**Download size:** ~7GB
**First time:** Takes 5-15 minutes depending on your internet speed

**Alternative models (if 11B is too large):**
- `llama3.2-vision` - Full 90B (best quality, ~50GB)
- `llava:13b` - Older but reliable (~8GB)
- `llava:7b` - Lighter and faster (~4.7GB)

### 4. Test Ollama

```bash
cd /home/user/Rebel-Operator
python3 scripts/test_ollama.py
```

If it works, you'll see analysis results!

### 5. Configure Your App (Optional)

Add to your `.env` file:

```bash
# Enable Ollama (default: true)
USE_OLLAMA=true

# Ollama model to use (default: llama3.2-vision:11b)
OLLAMA_MODEL=llama3.2-vision:11b

# Ollama server URL (default: http://localhost:11434)
OLLAMA_HOST=http://localhost:11434
```

## 📊 How It Works

Your app now tries AI providers in this order:

1. **Ollama** (local, FREE) - Tries first
2. **ChatGPT** (paid API) - Fallback if Ollama unavailable
3. **Claude** (paid API) - Final fallback

This means:
- ✅ **FREE** photo analysis if Ollama is running
- ✅ **No API costs** for unlimited usage
- ✅ **Fast** - runs on your machine
- ✅ **Private** - photos never leave your computer
- ✅ **Automatic fallback** to paid APIs if Ollama is down

## 💡 Tips

### Performance
- First analysis is slow (model loading) - subsequent ones are fast
- GPU recommended but not required (CPU works fine)
- 11B model needs ~8GB RAM

### Quality
- Ollama (llama3.2-vision:11b) is comparable to GPT-4 Vision for product listings
- For best results, use clear, well-lit photos
- Multiple angles help the AI understand the item better

### Troubleshooting

**"Ollama not running" error:**
```bash
ollama serve
```

**Model not found:**
```bash
ollama pull llama3.2-vision:11b
```

**Connection refused:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Check firewall settings

**Slow performance:**
- First run is always slow (model loading)
- Try a smaller model: `llava:7b`
- Close other memory-intensive apps

## 🎯 What You Get

With Ollama running, every photo analysis:
- ✅ **$0.00 cost** (vs $0.01-0.03 per image with APIs)
- ✅ **Complete privacy** (data never leaves your machine)
- ✅ **Unlimited usage** (no rate limits, no quotas)
- ✅ **Works offline** (no internet needed after model download)

**Estimated savings:** If you analyze 100 photos/month:
- With OpenAI API: ~$2-3/month
- With Ollama: **$0/month**

Over a year: **$24-36 saved!**

## 📚 Learn More

- Ollama: https://ollama.com
- LLaMA 3.2 Vision: https://ollama.com/library/llama3.2-vision
- Model library: https://ollama.com/library
