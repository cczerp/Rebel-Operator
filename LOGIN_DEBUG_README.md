# Login Debug - Minimal App

This is a stripped-down version of the app containing **ONLY** login functionality to debug login issues.

## What's Included

- **web_app_minimal.py** - Minimal Flask app with only auth routes
- **routes_auth.py** - All authentication routes (login, register, logout, Google OAuth)
- **src/auth_utils.py** - Google OAuth utilities via Supabase
- **src/database/db.py** - Database connection and user management
- **templates/** - Login-related templates (login.html, register.html, index_minimal.html, base.html)

## What's Removed

- All routes except auth (routes_main.py, routes_admin.py, routes_cards.py)
- Inventory, listings, storage, notifications, billing features
- Worker system
- All complex dependencies

## Setup

### 1. Install Dependencies

```bash
pip install Flask flask-login flask-session werkzeug python-dotenv psycopg2-binary supabase httpx
```

### 2. Create `.env` File

Create a `.env` file in the root directory with at minimum:

```env
# Required for basic login
DATABASE_URL=postgresql://user:password@host:5432/database
FLASK_SECRET_KEY=your-secret-key-here-change-this

# Optional: for Google OAuth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_REDIRECT_URL=http://localhost:5000/auth/callback
```

### 3. Run the Minimal App

```bash
python3 web_app_minimal.py
```

The app will run on http://localhost:5000

## Testing Login

### Test Regular Login
1. Go to http://localhost:5000
2. Click "Register" to create an account
3. After registration, you'll be logged in automatically
4. Test logout and login again with username/password

### Test Google OAuth
1. Ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in `.env`
2. Go to http://localhost:5000/login
3. Click "Sign in with Google"
4. Complete Google OAuth flow
5. You should be redirected back and logged in

### Debug Endpoints

- `/debug-config` - Shows Flask configuration (SECRET_KEY status, SESSION settings, environment vars)
- `/protected` - Protected route requiring login to test authentication

## Common Issues

### Issue: "Module not found" errors
**Solution:** Install dependencies: `pip install Flask flask-login flask-session werkzeug python-dotenv psycopg2-binary supabase httpx`

### Issue: "DATABASE_URL environment variable is required"
**Solution:** Create `.env` file with DATABASE_URL pointing to your PostgreSQL database

### Issue: Google OAuth fails with "flow_state_not_found"
**Possible causes:**
1. FLASK_SECRET_KEY not set or using default value
2. Session data lost between workers (multi-worker deployment)
3. PKCE verifier not persisted correctly

**Debug steps:**
1. Check `/debug-config` - ensure SECRET_KEY_LENGTH > 0
2. Check that filesystem sessions are working: `ls ./data/flask_session/`
3. Check OAuth state files: `ls ./data/oauth_state/`
4. Look for logs in console:
   - `[LOGIN_GOOGLE]` prefix for OAuth initiation
   - `[CALLBACK]` prefix for OAuth callback
   - Check for "flow_id" parameter passing

### Issue: Login works but session lost on refresh
**Possible causes:**
1. SESSION_COOKIE_SECURE=True but running on HTTP (not HTTPS)
2. SESSION_COOKIE_SAMESITE='None' but running locally

**Solution:** For local development, the app sets:
- SESSION_COOKIE_SECURE=False (when FLASK_ENV != production)
- SESSION_COOKIE_SAMESITE='Lax' (when FLASK_ENV != production)

## Debugging Tips

1. **Check database connection:**
   ```bash
   python3 -c "from src.database import get_db; db = get_db(); print('DB OK')"
   ```

2. **Check user exists:**
   ```bash
   python3 -c "from src.database import get_db; db = get_db(); print(db.get_user_by_username('testuser'))"
   ```

3. **Watch Flask logs:**
   The minimal app has extensive logging with prefixes:
   - `[LOGIN]` - Regular login flow
   - `[LOGIN_GOOGLE]` - Google OAuth initiation
   - `[CALLBACK]` - OAuth callback handling
   - `[USER_LOADER]` - Flask-Login user loading

4. **Test auth API directly:**
   ```bash
   # Check session
   curl http://localhost:5000/api/auth/session

   # Login via API
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}'
   ```

## Next Steps

Once login is working in this minimal app:
1. Identify what's different from the full app
2. Incrementally add back features one at a time
3. Test after each addition to isolate the issue
4. Document the fix in git commit message
