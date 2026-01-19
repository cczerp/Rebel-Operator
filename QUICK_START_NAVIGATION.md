# Quick Start Navigation Guide
## How to Find Anything in the Codebase

This is a **fast reference** for navigating the Rebel Operator codebase. Use this when you need to quickly find where something is implemented.

---

## 🎯 "I need to find..."

### "...where a page is defined"
→ **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**

**Example:** Where is the `/create` page?
- Open PAGE_TO_FILE_MAPPING.md
- Search for `/create`
- Result: Defined in `web_app.py`, renders `create.html`

---

### "...what features the app has"
→ **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)**

**Example:** Does the app support eBay?
- Open FEATURES_CAPABILITIES.md
- Go to "Platform Integrations"
- Result: Yes, full eBay Sell API integration

---

### "...how to structure my code change"
→ **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** + existing code patterns

**Example:** I need to add a new API endpoint for cards
- Check PAGE_TO_FILE_MAPPING.md → card endpoints are in `routes_cards.py`
- Open `routes_cards.py`
- Follow existing patterns (blueprint, decorators, database calls)

---

### "...all documentation files"
→ **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)**

Lists all documentation files with descriptions and links.

---

## 📂 File Quick Reference

### When to edit each file:

| File | Edit when... | Examples |
|------|--------------|----------|
| `web_app.py` | Adding core pages, configuring Flask, adding blueprints | New dashboard page, session config |
| `routes_main.py` | Adding listing features, storage, artifacts, platforms | New export format, storage feature |
| `routes_auth.py` | Authentication changes | New OAuth provider, password rules |
| `routes_admin.py` | Admin features | New admin dashboard widget |
| `routes_cards.py` | Card/collectible features | New card type support |
| `routes_csv.py` | CSV operations | New CSV format support |

---

## 🚀 Common Tasks

### Task: Add a new page

1. **Decide which file:**
   - Auth-related? → `routes_auth.py`
   - Admin-only? → `routes_admin.py`
   - Cards/collectibles? → `routes_cards.py`
   - General feature? → `web_app.py` or `routes_main.py`

2. **Add the route:**
   ```python
   @blueprint.route('/my-new-page')
   @login_required  # if auth needed
   def my_new_page():
       return render_template('my_new_page.html')
   ```

3. **Create the template:**
   - Add `templates/my_new_page.html`

4. **Update documentation:**
   - Add route to `PAGE_TO_FILE_MAPPING.md`
   - If it's a major feature, add to `FEATURES_CAPABILITIES.md`

---

### Task: Add a new API endpoint

1. **Find the right file:**
   - Check `PAGE_TO_FILE_MAPPING.md` for similar endpoints
   - Match category (auth → `routes_auth.py`, etc.)

2. **Add the endpoint:**
   ```python
   @blueprint.route('/api/my-endpoint', methods=['POST'])
   @login_required
   def api_my_endpoint():
       data = request.get_json()
       # Your logic here
       return jsonify({'success': True})
   ```

3. **Update documentation:**
   - Add to API list in `PAGE_TO_FILE_MAPPING.md`

---

### Task: Add a new platform integration

1. **Check existing patterns:**
   - See `FEATURES_CAPABILITIES.md` → Platform Integrations
   - Review code in `routes_main.py` (search "platform")

2. **Add platform logic:**
   - Add to `/api/platform/<platform>/connect`
   - Add to `/api/listing/<listing_id>/publish-to-platform`

3. **Update documentation:**
   - Add to `FEATURES_CAPABILITIES.md` platform list
   - Update platform count

---

### Task: Fix a bug on a page

1. **Find the page route:**
   - Search `PAGE_TO_FILE_MAPPING.md` for the page

2. **Open the file:**
   - Check which file defines it
   - Look for related API endpoints in same file

3. **Debug:**
   - Add logging to trace the issue
   - Check template rendering
   - Verify database queries

4. **Test:**
   - Run the app locally
   - Visit the page
   - Verify the fix

---

## 🔍 Search Strategies

### By Page URL
```bash
# Find where /drafts is defined
grep -n "'/drafts'" web_app.py routes_*.py
```

### By Feature
```bash
# Find all card-related code
grep -r "card" routes_*.py | grep "def "
```

### By Template
```bash
# Find which route renders a template
grep -r "create.html" *.py
```

### By API Endpoint
```bash
# Find API endpoint definition
grep -r "/api/upload-photos" routes_*.py
```

---

## 📊 Quick Stats

- **33** HTML pages across 5 route files
- **120+** API endpoints
- **17** platform integrations
- **100+** features across 17 categories
- **3** AI providers (Claude, GPT-4, Gemini)

---

## �� Best Practices

### Before changing code:
1. ✅ Check if feature already exists (FEATURES_CAPABILITIES.md)
2. ✅ Find similar code patterns (PAGE_TO_FILE_MAPPING.md)
3. ✅ Review existing implementation
4. ✅ Follow established patterns

### After changing code:
1. ✅ Test locally
2. ✅ Update documentation
3. ✅ Check for broken references
4. ✅ Commit with clear message

---

## 🆘 "I'm stuck!"

### Can't find a page definition?
- Search ALL files: `grep -r "route_path" *.py`
- Check `PAGE_TO_FILE_MAPPING.md`

### Can't find a feature?
- Search `FEATURES_CAPABILITIES.md`
- Use browser search (Ctrl+F / Cmd+F)

### Need to understand the flow?
- Check "Quick Reference by Functionality" in `PAGE_TO_FILE_MAPPING.md`
- Follow the workflow diagrams

### Documentation seems wrong?
- Verify against actual code
- Update documentation if outdated
- Report issue if unclear

---

## 🔗 Essential Links

- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Find code locations
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Discover features
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All documentation
- **[README.md](README.md)** - Project overview

---

*Last Updated: 2026-01-19*
*Quick reference guide for Rebel Operator codebase*
