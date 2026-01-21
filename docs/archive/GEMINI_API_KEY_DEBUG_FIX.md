# Gemini API Key Debugging & Fixes

## 🔥 **The Problem**

Gemini API returning HTML instead of JSON with error: `SyntaxError: Unexpected token '<'`

This indicates the API key is being rejected by Google, NOT a network or endpoint issue.

## ✅ **Fixes Applied**

### 1. **Key Validation & Stripping** (ChatGPT's #1 Fix)
- ✅ Strip whitespace from API key (leading/trailing spaces, newlines, etc.)
- ✅ Log `repr()` of raw key to detect hidden characters
- ✅ Warn if key length is unexpected (< 30 or > 60 chars)
- ✅ Warn if key doesn't start with 'AIza'

### 2. **No Authorization Header** (ChatGPT's #2 Fix)
- ✅ Verified we're ONLY using `?key=API_KEY` in query string
- ✅ Verified we're NOT adding `Authorization: Bearer` header
- ✅ Explicitly set headers to only `Content-Type: application/json`

### 3. **Environment Variable Debugging** (ChatGPT's #3 Fix)
- ✅ Log which env vars are found (GEMINI_API_KEY, GOOGLE_AI_API_KEY, GEMENI_API_KEY)
- ✅ Log length and repr of each found env var
- ✅ Check all three possible env var names

## 📋 **What to Check in Logs**

After deployment, look for these log messages:

```
[GEMINI DEBUG] RAW KEY REPR (first 50 chars): 'AIzaSy...'
[GEMINI DEBUG] STRIPPED KEY REPR (first 50 chars): 'AIzaSy...'
[GEMINI DEBUG] API Key loaded: length=39, preview=AIzaS...xyz12
[GEMINI DEBUG] Environment variables found: ['GEMINI_API_KEY']
```

### ⚠️ **Red Flags to Look For:**

1. **Hidden Characters:**
   ```
   RAW KEY REPR: 'AIzaSy...\n'  ← NEWLINE!
   RAW KEY REPR: ' AIzaSy...'   ← LEADING SPACE!
   ```

2. **Wrong Length:**
   ```
   API Key loaded: length=25  ← TOO SHORT (expected 39-45)
   API Key loaded: length=80  ← TOO LONG (may have extra chars)
   ```

3. **Wrong Format:**
   ```
   API key doesn't start with 'AIza'  ← WRONG KEY TYPE
   ```

4. **Whitespace Detected:**
   ```
   API key had whitespace! Stripped 2 characters.
   ```

## 🔧 **If Key Has Hidden Characters**

1. **In Render Dashboard:**
   - Go to Environment Variables
   - Delete `GEMINI_API_KEY` entirely
   - Re-add it manually
   - **Type it, don't paste** (or paste into notepad first, then copy)
   - Save
   - Redeploy

2. **Verify in Logs:**
   - Check that `RAW KEY REPR` shows no `\n`, `\r`, or spaces
   - Check that length is ~39-45 characters
   - Check that it starts with `AIza`

## 🎯 **Expected Behavior**

After fixes:
- ✅ Key is stripped of whitespace automatically
- ✅ No Authorization header sent (only query param)
- ✅ Detailed logging shows key state
- ✅ API calls should work if key is valid

## 📝 **Code Changes**

### `src/ai/gemini_classifier.py`

1. **`__init__()` method:**
   - Strips whitespace from API key
   - Logs `repr()` of raw and stripped key
   - Validates key length and format
   - Logs which env vars are found

2. **`analyze()` method:**
   - Explicitly sets headers to only `Content-Type`
   - Logs request details (key hidden)
   - Verifies no Authorization header

3. **`_classify_image()` method:**
   - Same header fix applied

---

**Last Updated**: After implementing ChatGPT's debugging recommendations
**Status**: Ready for testing - check logs for key issues

