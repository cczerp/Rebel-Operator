# Frontend Non-Negotiable Rules

## JavaScript Event Handlers

### ✅ DO
- Use inline `onclick` and `onchange` handlers for simple interactions
- Keep handlers direct: `onclick="document.getElementById('cameraInput').click()"`
- Follow existing patterns in the codebase

### ❌ DON'T
- Don't "modernize" working inline handlers to addEventListener
- Don't overcomplicate simple click-to-trigger flows
- Don't change patterns without checking contracts first

**Example (Correct)**:
```html
<button onclick="document.getElementById('cameraInput').click()">Take Photo</button>
<input type="file" id="cameraInput" onchange="handlePhotoSelect(event)">
```

---

## Template Variables in JavaScript

### ✅ ALWAYS
- Validate Python template variables before rendering in JavaScript
- Check for `None` values with Jinja conditionals
- Test with BOTH guest and logged-in users (different code paths)

### ❌ NEVER
- Never put Python `None` directly in JavaScript
- Never assume template variables have values
- Never skip browser console error checking

**Example (Correct)**:
```jinja
{% if is_guest and guest_uses_remaining is not none %}
const newRemaining = Math.max(0, {{ guest_uses_remaining }} - 1);
{% endif %}
```

**Example (Wrong)**:
```jinja
const newRemaining = Math.max(0, {{ guest_uses_remaining }} - 1);  {# None breaks JavaScript! #}
```

---

## Debugging

### ✅ ALWAYS
- Check browser console for ALL errors (not just the obvious one)
- Look for syntax errors that break the entire script
- Verify functions are defined before calling them
- When user says "check this working branch" - DO IT and compare line-by-line

### ❌ NEVER
- Don't assume the first fix solved the problem
- Don't ignore "unrelated" console errors
- Don't create duplicate if statements
- Don't ignore user hints about working branches

---

## Photo Upload Flow

### ✅ REQUIREMENTS
- Validate file types on frontend before upload
- Only clean up photos from `temp-photos` bucket
- Only run cleanup if user hasn't saved (no draft/listing created)
- Use `navigator.sendBeacon` for cleanup on page unload
- Add `beforeunload` and `visibilitychange` event handlers

### ❌ DON'T BREAK
- Don't modify working upload flow
- Don't change Supabase Storage integration
- Don't remove debugging when troubleshooting

---

## Contracts Reference

**Before modifying photo/image code, check:**
- `/image flow/01_frontend_image_flow_javascript.txt`
- `/image flow/02_frontend_ai_analysis_javascript.txt`
- `/image flow/03_frontend_html_css.txt`

**These are the source of truth. Follow them.**

---

## Key Lessons

1. **Simple is better** - Inline handlers work perfectly for simple interactions
2. **Follow existing patterns** - Consistency > "best practices" from elsewhere
3. **Template variables need validation** - Python values don't exist in JavaScript
4. **Check ALL console errors** - Syntax errors break everything before functions load
5. **Listen to the user** - When they say "check this branch", they know their codebase
