# 📋 NON-NEGOTIABLE CONTRACTS

This file serves as the master index for all non-negotiable contracts in the codebase.

**IMPORTANT:** When modifying code, ALWAYS check the relevant contract first. These patterns are proven to work and must be followed exactly.

---

## 🎯 Quick Reference

| Area | Contract File | What It Covers |
|------|--------------|----------------|
| **Photo Upload** | `image flow/01_frontend_image_flow_javascript.txt` | Upload handlers, event patterns, template variables |
| **AI Analysis** | `image flow/02_frontend_ai_analysis_javascript.txt` | AI analyzer integration |
| **UI/CSS** | `image flow/03_frontend_html_css.txt` | Photo upload UI patterns |
| **Backend Upload** | `image flow/04_backend_photo_upload_api.txt` | Photo upload API endpoint |
| **Photo Editing** | `image flow/05_backend_photo_edit_api.txt` | Edit API endpoints |
| **AI Backend** | `image flow/06_backend_ai_analyze_api.txt` | AI analysis backend |
| **Enhanced Scan** | `image flow/07_backend_enhanced_scan_api.txt` | Enhanced scanning API |

---

## 🚨 CRITICAL NON-NEGOTIABLES

### 1. Template Variables in JavaScript

**❌ NEVER:**
```javascript
const value = {{ some_variable }};  // If None, breaks everything!
```

**✅ ALWAYS:**
```jinja
{% if some_variable is not none %}
const value = {{ some_variable }};
{% endif %}
```

**Why:** Python `None` renders as literal `None` in JavaScript, creating syntax errors that break the entire script.

### 2. Guest User Pattern

**✅ REQUIRED PATTERN:**
```jinja
{% if is_guest and guest_uses_remaining is not none %}
const newRemaining = Math.max(0, {{ guest_uses_remaining }} - 1);
// guest-specific code here
{% endif %}
```

**Why:** Must check BOTH conditions to prevent `None` from rendering in JavaScript.

### 3. Event Handlers

**✅ USE INLINE HANDLERS:**
```html
<button onclick="document.getElementById('input').click()">
<input onchange="handlePhotoSelect(event)">
```

**❌ DON'T USE addEventListener:**
```javascript
// Avoid this - timing issues, overcomplicated
button.addEventListener('click', ...);
```

**Why:** Inline handlers are simple, reliable, and match existing codebase patterns.

### 4. Reference Branch

**Working reference implementation:**
`claude/update-website-logo-vfdYM`

**Before making changes:**
1. Check this branch first
2. Compare your code with the working version
3. If it doesn't match, you're probably doing it wrong
4. Copy working code EXACTLY - don't "improve" it

---

## 📚 Contract Locations

All contracts are located in:
```
/home/user/Rebel-Operator/image flow/
```

### Image Flow Contracts

1. **01_frontend_image_flow_javascript.txt**
   - Photo upload handler (`handlePhotoSelect`)
   - Photo editor functions
   - Photo preview rendering
   - ⚠️ **NON-NEGOTIABLE RULES** section (CRITICAL)

2. **02_frontend_ai_analysis_javascript.txt**
   - AI analyzer integration
   - Quick analysis flow
   - Enhanced scan flow

3. **03_frontend_html_css.txt**
   - Photo upload UI structure
   - Button layouts
   - Preview display

4. **04_backend_photo_upload_api.txt**
   - `/api/upload-photos` endpoint
   - File validation
   - Image compression
   - Supabase storage integration

5. **05_backend_photo_edit_api.txt**
   - `/api/edit-photo` endpoint
   - Crop functionality
   - Background removal

6. **06_backend_ai_analyze_api.txt**
   - `/api/analyze` endpoint
   - Gemini integration
   - Quick analysis

7. **07_backend_enhanced_scan_api.txt**
   - `/api/enhanced-scan` endpoint
   - Claude integration
   - Detailed card analysis

8. **README.txt**
   - Architecture overview
   - Component relationships

---

## 🔍 How to Use Contracts

### When Adding New Features

1. **Check existing contracts** - See if there's already a pattern
2. **Follow the pattern exactly** - Don't "improve" or "modernize"
3. **Update the contract** - If you add new patterns, document them
4. **Test with multiple user states** - Guest AND logged-in

### When Debugging

1. **Check browser console** - Read ALL errors, not just the first one
2. **Look for template variable issues** - Search for `{{ }}` in templates
3. **Compare with reference branch** - `claude/update-website-logo-vfdYM`
4. **Check the contract** - See if there's a known pattern you should follow

### When Reviewing Code

1. **Verify template variable checks** - All `{{ }}` wrapped in `{% if %}`?
2. **Check event handler pattern** - Using inline handlers?
3. **Verify guest user handling** - Both `is_guest` AND `not none` checked?
4. **Compare with contracts** - Does it match the documented patterns?

---

## ⚠️ Common Mistakes to Avoid

### 1. Duplicate If Statements
```jinja
❌ WRONG:
{% if is_guest and guest_uses_remaining is not none %}
  {% if guest_uses_remaining is not none %}  <!-- DUPLICATE! -->
    ...
  {% endif %}
{% endif %}
```

### 2. Missing is_guest Check
```jinja
❌ WRONG:
{% if guest_uses_remaining is not none %}
  // Still breaks for logged-in users if code tries to use the variable
{% endif %}
```

### 3. Trying to "Improve" Working Code
```
❌ WRONG:
"I'll modernize these inline handlers with addEventListener"
"I'll refactor this to be more DRY"
"I'll add better error handling"

✅ CORRECT:
Copy the working branch exactly. Don't touch what works.
```

---

## 📖 Additional Resources

- **Lessons Learned:** See `LESSONS_LEARNED.md` for debugging war stories
- **Working Branch:** `claude/update-website-logo-vfdYM` - reference implementation
- **Image Flow Directory:** `/image flow/` - detailed technical contracts

---

## 🎓 Golden Rules

1. **Check contracts first** - Before writing or modifying code
2. **Follow patterns exactly** - Consistency > "best practices"
3. **Test both user types** - Guest AND logged-in
4. **Read ALL console errors** - Don't stop at the first one
5. **When in doubt, copy working code** - Don't try to be clever

---

*"The best code is the code that works and nobody has to think about."*
*"The best developer is the one who listens to the user."*
