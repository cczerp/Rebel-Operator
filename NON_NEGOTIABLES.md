# 📋 NON-NEGOTIABLE RULES

**CRITICAL: Read these files before modifying any code.**

These rules are proven patterns that must be followed exactly. They're distilled from hundreds of hours of debugging and represent what actually works.

---

## 🎯 Quick Reference

| Area | Rule File | When to Read |
|------|-----------|-------------|
| **Frontend** | `FRONTEND_RULES.md` | Before touching templates, JavaScript, or photo upload UI |
| **Backend** | `BACKEND_RULES.md` | Before modifying APIs, database code, or image processing |
| **External APIs** | `EXTERNAL_API_RULES.md` | Before integrating with Gemini, Claude, Supabase, or Mercari |

---

## 🚨 Most Critical Rules

### 1. Template Variables in JavaScript (Frontend)
```jinja
❌ NEVER: const value = {{ some_variable }};
✅ ALWAYS: {% if some_variable is not none %}const value = {{ some_variable }};{% endif %}
```

### 2. Database Cursors (Backend)
```python
✅ ALWAYS close cursors in finally blocks
❌ NEVER leave cursors open (causes connection pool exhaustion)
```

### 3. Image Format Conversion (External APIs)
```python
✅ Claude accepts: JPEG, PNG, GIF only
✅ Gemini accepts: JPEG, PNG, GIF, WebP
❌ NEVER send HEIC/WebP to Claude without converting
```

### 4. Event Handlers (Frontend)
```html
✅ USE inline handlers: onclick="..."
❌ DON'T USE addEventListener (timing issues)
```

### 5. API Authentication
```python
✅ Gemini: API key in query param (?key=...)
✅ Claude: x-api-key header
✅ Supabase: Authorization Bearer header
✅ eBay: Bearer token from Browse API (client_credentials)
❌ NEVER mix them up
```

### 6. eBay Integration
```python
✅ USE Browse API (https://api.ebay.com/buy/browse/v1/...)
❌ NEVER use Finding API (svcs.ebay.com) - returns 500 errors, deprecated
✅ Env var: EBAY_PROD_B64 (uppercase) or EBAY_PROD_APP_ID + EBAY_PROD_CERT_ID
✅ Must enable Browse API in eBay Developer Portal
```

---

## 📚 Detailed Implementations

For detailed code examples and implementations, see:
- `/image flow/` - Detailed technical contracts with working code
- `/docs/archive/` - Old debug sessions and lessons learned

---

## 🔑 Golden Rules

1. **Read the rule files first** - Before writing ANY code
2. **Follow patterns exactly** - Consistency > "best practices"
3. **Test both user types** - Guest AND logged-in users
4. **Check ALL console errors** - Not just the first one
5. **When in doubt, check working code** - Don't try to be clever
6. **Reference the contracts** - `/image flow/` has proven patterns

---

## ⚠️ When Things Break

1. Check browser console for ALL errors
2. Search for template variables: `grep -n "{{" templates/*.html`
3. Review the relevant rule file
4. Check `/image flow/` for working implementation
5. If user says "check this branch" - DO IT

---

*"The best code is the code that works and nobody has to think about."*
*"The best developer is the one who listens to the user."*
