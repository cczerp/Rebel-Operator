# Frontend Non-Negotiable Rules

## Template Variables in JavaScript - CRITICAL

### ❌ NEVER DO THIS
```javascript
const value = {{ some_variable }};  // If None in Python, breaks JavaScript!
```

### ✅ ALWAYS DO THIS
```jinja
{% if some_variable is not none %}
const value = {{ some_variable }};
{% endif %}
```

**Why**: Python `None` renders as literal `None` in JavaScript, creating syntax errors that break the entire script.

---

## Guest User Handling - EXACT PATTERN REQUIRED

### ❌ WRONG - Missing is_guest check
```jinja
{% if guest_uses_remaining is not none %}
const newRemaining = Math.max(0, {{ guest_uses_remaining }} - 1);
{% endif %}
```

### ❌ WRONG - Duplicate if statements
```jinja
{% if is_guest and guest_uses_remaining is not none %}
  {% if guest_uses_remaining is not none %}  <!-- DUPLICATE! -->
    const newRemaining = ...
  {% endif %}
{% endif %}
```

### ✅ CORRECT - Check BOTH conditions in ONE if
```jinja
{% if is_guest and guest_uses_remaining is not none %}
const newRemaining = Math.max(0, {{ guest_uses_remaining }} - 1);
// ... rest of guest-specific code
{% endif %}
```

**Why**: Must check BOTH conditions to prevent `None` from rendering in JavaScript.

---

## Event Handlers

### ✅ USE INLINE HANDLERS
```html
<button onclick="document.getElementById('cameraInput').click()">Take Photo</button>
<input type="file" id="cameraInput" onchange="handlePhotoSelect(event)">
```

### ❌ DON'T USE addEventListener
```javascript
// Avoid this - timing issues, overcomplicated
button.addEventListener('click', function() { ... });
```

**Why**: Inline handlers are simple, reliable, and match existing codebase patterns.

---

## Photo Upload Flow

### ✅ REQUIREMENTS
- Append to existing photos: `uploadedPhotos = uploadedPhotos.concat(data.paths)`
- Reset input after select: `e.target.value = ''`
- Show analyze button when photos exist
- Create preview with delete button for each photo
- Support click-to-edit and right-click-to-zoom
- Only clean up photos from `temp-photos` bucket
- Only run cleanup if user hasn't saved (no draft/listing created)
- Use `navigator.sendBeacon` for cleanup on page unload
- Add `beforeunload` and `visibilitychange` event handlers

### ❌ DON'T
- Don't replace photos array (append only)
- Don't skip input reset
- Don't modify working upload flow
- Don't remove debugging when troubleshooting

---

## Photo Editor

### ✅ REQUIREMENTS
- Convert blob URLs to base64 before sending to API
- Destroy existing cropper before creating new one
- Use 15-second timeout for crop operations
- Use 30-second timeout for background removal
- Update both preview thumbnail and uploadedPhotos array
- Support free aspect ratio cropping (NaN)

### ❌ DON'T
- Don't skip blob-to-base64 conversion
- Don't leave croppers attached
- Don't skip timeout handling
- Don't forget to update preview after edit

---

## Debugging

### ✅ WHEN CODE BREAKS
1. Check browser console for ALL errors (not just the obvious one)
2. Look for "Illegal return statement" or "SyntaxError"
3. Search for template variables: `grep -n "{{" templates/create.html`
4. If user says "check this working branch" - DO IT IMMEDIATELY
5. Copy working code EXACTLY - don't "improve" it

### ✅ TESTING REQUIREMENTS
- MUST test with BOTH:
  - Guest users (is_guest=True, guest_uses_remaining=0-8)
  - Logged-in users (is_guest=False, guest_uses_remaining=None)
- If it works for one but not the other, it's a template variable issue

### ❌ NEVER
- Don't assume the first fix solved the problem
- Don't ignore "unrelated" console errors
- Don't create duplicate if statements
- Don't ignore user hints about working branches
- Don't try to "improve" working code

---

## Reference Branch

**Working reference implementation**: `claude/update-website-logo-vfdYM`

**Before making changes**:
1. Check this branch first
2. Compare your code with the working version
3. If it doesn't match, you're probably doing it wrong
4. Copy working code EXACTLY - don't "improve" it

---

## Image Flow Contracts (Detailed Implementations)

**Before modifying photo/image code, check**:
- `/image flow/01_frontend_image_flow_javascript.txt` - Upload handlers, editor functions
- `/image flow/02_frontend_ai_analysis_javascript.txt` - AI analyzer integration
- `/image flow/03_frontend_html_css.txt` - Photo upload UI patterns

**These are the source of truth. Follow them exactly.**

---

## Common Mistakes to Avoid

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
  // Still breaks for logged-in users if variable is used
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

## Key Rules

1. **Check browser console for ALL errors** - Not just the first one
2. **Validate ALL template variables** - Wrap in `{% if not none %}`
3. **Test BOTH user types** - Guest AND logged-in
4. **Use inline handlers** - Don't addEventListener
5. **When in doubt, copy working code** - Don't try to be clever
6. **Follow contracts exactly** - They're proven to work
