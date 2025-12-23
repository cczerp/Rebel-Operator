#!/usr/bin/env python3
"""
AI Cross-Poster Web App - Main Entry Point
============================================
PostgreSQL-compatible web application for inventory management.

This file serves as the entry point that:
- Initializes Flask app and database
- Sets up Flask-Login authentication
- Registers all route blueprints
"""

import os
import sys
import json
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, current_user
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Force fresh deployment - using Flask built-in cookie sessions
print("🚀 Starting AI Cross-Poster web app...", flush=True)

from src.database import get_db

# Load environment
load_dotenv()
print("✅ Environment loaded", flush=True)

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================

app = Flask(__name__)

# CRITICAL: Validate SECRET_KEY is set
# Try SECRET_KEY first (recommended), fall back to FLASK_SECRET_KEY for backwards compatibility
flask_secret = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
if not flask_secret or flask_secret == 'dev-secret-key-change-in-production':
    print("=" * 80, flush=True)
    print("⚠️  WARNING: SECRET_KEY not set or using default value!", flush=True)
    print("⚠️  This will cause session loss in production with multiple workers!", flush=True)
    print("⚠️  Set SECRET_KEY environment variable immediately!", flush=True)
    print("=" * 80, flush=True)

app.secret_key = flask_secret
print(f"✅ Flask secret key configured (length: {len(flask_secret)})", flush=True)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = './data/uploads'

# ============================================================================
# SESSION CONFIGURATION (Redis-based sessions via Upstash)
# ============================================================================
# Using Redis for server-side session storage:
# - Sessions stored in Upstash Redis (persistent, reliable)
# - Perfect for OAuth PKCE flow (code_verifier storage)
# - Supports multi-worker deployments
# - Works with ephemeral filesystems (Render, Heroku, etc.)

import redis
from flask_session import Session

# Detect production environment
is_production = os.getenv('FLASK_ENV') == 'production' or bool(os.getenv('RENDER_EXTERNAL_URL'))

# Get Redis URL from environment
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    print("=" * 80, flush=True)
    print("⚠️  WARNING: REDIS_URL not set!", flush=True)
    print("⚠️  Sessions will not work without Redis!", flush=True)
    print("⚠️  Set REDIS_URL environment variable immediately!", flush=True)
    print("=" * 80, flush=True)
    sys.exit(1)

# Parse Redis URL - handle CLI command format from Upstash
# Upstash gives: "redis-cli --tls -u redis://..."
# We need just: "rediss://..." (note the double 's' for TLS)
if redis_url.startswith('redis-cli'):
    # Extract URL from CLI command format
    import re
    url_match = re.search(r'redis://[^\s]+', redis_url)
    if url_match:
        redis_url = url_match.group(0)
        # Replace redis:// with rediss:// for TLS (Upstash requires TLS)
        redis_url = redis_url.replace('redis://', 'rediss://', 1)
        print(f"🔧 Extracted Redis URL from CLI format and enabled TLS", flush=True)
    else:
        print(f"❌ Failed to parse Redis URL from CLI format: {redis_url}", flush=True)
        sys.exit(1)

# Ensure we're using rediss:// for Upstash (TLS required)
if redis_url.startswith('redis://') and 'upstash.io' in redis_url:
    redis_url = redis_url.replace('redis://', 'rediss://', 1)
    print(f"🔧 Converted to rediss:// for Upstash TLS", flush=True)

# Configure Redis client for sessions
try:
    # For Upstash, we need SSL/TLS
    session_redis = redis.from_url(
        redis_url,
        decode_responses=False,  # Keep binary for session data
        socket_connect_timeout=5,
        socket_timeout=5,
        ssl_cert_reqs=None  # Upstash: don't verify SSL cert
    )
    # Test connection
    session_redis.ping()
    print(f"✅ Redis connection successful: {redis_url.split('@')[1].split('/')[0] if '@' in redis_url else 'connected'}", flush=True)
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}", flush=True)
    print(f"   Processed Redis URL: {redis_url}", flush=True)
    sys.exit(1)

# Configure Flask-Session to use Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = session_redis
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Sign session cookies for security
app.config['SESSION_KEY_PREFIX'] = 'resell_rebel:session:'  # Namespace for session keys
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Optional: 1 hour session lifetime

# Cookie settings for OAuth compatibility
# CRITICAL FIX: Use 'Lax' for production since we're on the same domain (no cross-site needed)
# SameSite='None' requires Secure=True but can cause issues with proxies/load balancers
app.config['SESSION_COOKIE_SECURE'] = True if is_production else False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from 'None' to 'Lax' for same-site compatibility
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS attacks
app.config['SESSION_COOKIE_NAME'] = 'resell_rebel_session'

# Flask-Login remember cookie settings (critical for session persistence)
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 24 hours
app.config['REMEMBER_COOKIE_SECURE'] = True if is_production else False
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Session
Session(app)

print(f"🔧 Session configuration (Redis-based sessions):", flush=True)
print(f"   - Storage: Upstash Redis (server-side)", flush=True)
print(f"   - Session Type: {app.config['SESSION_TYPE']}", flush=True)
print(f"   - Cookie SameSite: {app.config['SESSION_COOKIE_SAMESITE']}", flush=True)
print(f"   - Cookie Secure: {app.config['SESSION_COOKIE_SECURE']}", flush=True)
print(f"   - Cookie HTTPOnly: {app.config['SESSION_COOKIE_HTTPONLY']}", flush=True)
print(f"   - Session Lifetime: {app.config['PERMANENT_SESSION_LIFETIME']}s", flush=True)
print(f"   - Remember Cookie Secure: {app.config['REMEMBER_COOKIE_SECURE']}", flush=True)
print(f"   - Remember Cookie SameSite: {app.config['REMEMBER_COOKIE_SAMESITE']}", flush=True)

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Ensure draft photos folder exists (for unauthenticated users)
Path('./data/draft_photos').mkdir(parents=True, exist_ok=True)

# Per-request database instance using Flask's g object
# This ensures connections are properly returned to pool after each request
def get_db_instance():
    """Get per-request database instance from Flask's g object

    CRITICAL FIX: Use per-request Database instances instead of singleton
    This ensures connections are properly returned to pool after each request,
    preventing SSL connection errors on Render
    """
    from flask import g
    if 'db' not in g:
        from src.database import Database
        g.db = Database()
    return g.db

@app.teardown_appcontext
def close_db_connection(exception=None):
    """Close database connection at end of request

    CRITICAL FIX: Return connections to pool after each request
    Without this, connections leak and cause SSL errors on Render
    """
    from flask import g
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            print(f"⚠️  Error closing database connection: {e}", flush=True)

# Initialize notification manager (optional)
notification_manager = None
try:
    from src.notifications import NotificationManager
    notification_manager = NotificationManager.from_env()
except Exception:
    pass

# ============================================================================
# FLASK-MAIL CONFIGURATION
# ============================================================================

from flask_mail import Mail

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

# Initialize Flask-Mail
mail = Mail(app)

# Export mail instance for use in routes
app.mail = mail

# Check if email is configured
if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
    print("✅ Flask-Mail configured for email verification")
else:
    print("⚠️  Flask-Mail not fully configured (MAIL_USERNAME/MAIL_PASSWORD missing)")
    print("   Email verification will not work until configured")

# ============================================================================
# USER MODEL FOR FLASK-LOGIN
# ============================================================================

class User(UserMixin):
    """User model for Flask-Login - PostgreSQL compatible"""

    def __init__(self, user_id, username, email, is_admin=False, is_active=True, tier="FREE"):
        self.id = user_id
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self._is_active = is_active
        self.tier = tier

    @property
    def is_active(self):
        """Override Flask-Login's is_active to use database value"""
        return self._is_active

    def can_access(self, feature: str) -> bool:
        """Check if user can access a feature based on tier"""
        from src.database import can_access_feature
        return can_access_feature(self.tier, feature)

    @staticmethod
    def get(user_id):
        """Get user by Supabase UID from PostgreSQL"""
        if not user_id:
            return None
            
        user_id_str = str(user_id)
        
        # Try to get by supabase_uid first (new users)
        user_data = get_db_instance().get_user_by_supabase_uid(user_id_str)

        # Fall back to get_user_by_id for legacy users (old users with just id)
        if not user_data:
            user_data = get_db_instance().get_user_by_id(user_id_str)

        if user_data:
            # Use supabase_uid as the User.id if available, otherwise use id
            # Ensure we convert to string and handle None/empty values
            supabase_uid = user_data.get('supabase_uid')
            regular_id = user_data.get('id')
            
            if supabase_uid:
                user_identifier = str(supabase_uid)
            elif regular_id:
                user_identifier = str(regular_id)
            else:
                print(f"[User.get] ERROR: User data has neither supabase_uid nor id for user_id: {user_id_str}")
                return None
                
            return User(
                user_identifier,
                user_data['username'],
                user_data['email'],
                user_data.get('is_admin', False),
                user_data.get('is_active', True),
                user_data.get('tier', 'FREE')
            )
        return None

# ============================================================================
# FLASK-LOGIN SETUP
# ============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login - user_id is Supabase UID (or legacy UUID for old users)"""
    try:
        from flask import session as flask_session
        
        # user_id is Supabase UID string (stored in session by Flask-Login)
        user_id_str = str(user_id) if user_id else None
        if not user_id_str:
            print(f"[USER_LOADER] No user_id provided", flush=True)
            return None

        print(f"[USER_LOADER] Loading user with ID: {user_id_str}", flush=True)
        print(f"[USER_LOADER] Session keys: {list(flask_session.keys())}", flush=True)
        print(f"[USER_LOADER] Session permanent: {flask_session.permanent}", flush=True)
        
        # Get database instance with error handling and retry for pool exhaustion
        db_instance = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db_instance = get_db_instance()
                if db_instance:
                    break
            except Exception as db_error:
                error_str = str(db_error)
                if "connection pool exhausted" in error_str.lower() and attempt < max_retries - 1:
                    print(f"[USER_LOADER] Pool exhausted (attempt {attempt + 1}/{max_retries}), waiting 0.1s and retrying...", flush=True)
                    import time
                    time.sleep(0.1)  # Brief wait before retry
                    continue
                else:
                    print(f"[USER_LOADER ERROR] Failed to get database instance: {db_error}", flush=True)
                    import traceback
                    traceback.print_exc()
                    return None
        
        if not db_instance:
            print(f"[USER_LOADER ERROR] Database instance not available after {max_retries} attempts", flush=True)
            return None
        
        # Try to get user with retry for pool exhaustion
        user = None
        for attempt in range(max_retries):
            try:
                user = User.get(user_id_str)
                break
            except Exception as user_error:
                error_str = str(user_error)
                if "connection pool exhausted" in error_str.lower() and attempt < max_retries - 1:
                    print(f"[USER_LOADER] Pool exhausted during user lookup (attempt {attempt + 1}/{max_retries}), waiting 0.1s and retrying...", flush=True)
                    import time
                    time.sleep(0.1)
                    continue
                else:
                    print(f"[USER_LOADER ERROR] Error getting user: {user_error}", flush=True)
                    import traceback
                    traceback.print_exc()
                    return None

        if user:
            print(f"[USER_LOADER] ✅ Successfully loaded user: {user.username} (ID: {user.id})", flush=True)
        else:
            print(f"[USER_LOADER] ❌ User not found for ID: {user_id_str}", flush=True)
            print(f"[USER_LOADER] This may indicate a session mismatch - user_id in session doesn't match database", flush=True)

        return user
    except (ValueError, TypeError) as e:
        print(f"[USER_LOADER ERROR] Invalid user_id: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        # Database errors (SSL connection failures, etc.) should not crash the app
        # Just log and return None, which tells Flask-Login the user is not authenticated
        error_str = str(e)
        if "connection pool exhausted" in error_str.lower():
            print(f"[USER_LOADER ERROR] Connection pool exhausted - this is a critical issue. Check database connection pool configuration.", flush=True)
        else:
            print(f"[USER_LOADER ERROR] Error loading user (returning None): {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# ADMIN DECORATOR
# ============================================================================

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Export for use in blueprints
app.admin_required = admin_required

# ============================================================================
# IMPORT AND REGISTER BLUEPRINTS
# ============================================================================

# Import blueprints
from routes_auth import auth_bp, init_routes as init_auth
from routes_admin import admin_bp, init_routes as init_admin
from routes_cards import cards_bp, init_routes as init_cards
from routes_main import main_bp, init_routes as init_main

# Initialize blueprints with database instance and User class
# Database is created lazily on first blueprint init
# Must be done within app context since get_db_instance() uses Flask's g object
try:
    print("🔌 Initializing database connection...", flush=True)
    with app.app_context():
        db_instance = get_db_instance()
        print("✅ Database connected successfully", flush=True)

        print("📝 Initializing route blueprints...", flush=True)
        init_auth(db_instance, User)
        init_admin(db_instance)
        init_cards(db_instance)
        init_main(db_instance)
        print("✅ Blueprints initialized", flush=True)
except Exception as e:
    print(f"❌ FATAL ERROR during initialization: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cards_bp)
app.register_blueprint(main_bp)

print("✅ Flask app initialized and ready to serve requests", flush=True)

# ============================================================================
# REQUEST HOOKS FOR SESSION DEBUGGING
# ============================================================================

# Enable verbose session logging with DEBUG_SESSIONS=true environment variable
DEBUG_SESSIONS = os.getenv('DEBUG_SESSIONS', 'false').lower() == 'true'

if DEBUG_SESSIONS:
    @app.before_request
    def log_session_state():
        """Log session state on each request for debugging"""
        from flask import session, request
        # Only log for HTML page requests (not static assets)
        if request.path.startswith('/static/') or request.path.startswith('/data/'):
            return
        
        print(f"[REQUEST] {request.method} {request.path}", flush=True)
        print(f"[SESSION] Authenticated: {current_user.is_authenticated}", flush=True)
        if current_user.is_authenticated:
            print(f"[SESSION] User: {current_user.username} (ID: {current_user.id})", flush=True)
        print(f"[SESSION] Session keys: {list(session.keys())}", flush=True)
        print(f"[SESSION] Session permanent: {session.permanent}", flush=True)

# ============================================================================
# MAIN ROUTES (not in blueprints)
# ============================================================================

@app.route('/debug-config')
def debug_config():
    """Debug endpoint to check Flask configuration"""
    import os
    config_info = {
        'FLASK_ENV': os.getenv('FLASK_ENV', 'NOT SET'),
        'is_production_check': os.getenv('FLASK_ENV') == 'production',
        'SESSION_COOKIE_SAMESITE': app.config.get('SESSION_COOKIE_SAMESITE'),
        'SESSION_COOKIE_SECURE': app.config.get('SESSION_COOKIE_SECURE'),
        'SESSION_COOKIE_HTTPONLY': app.config.get('SESSION_COOKIE_HTTPONLY'),
        'SESSION_TYPE': app.config.get('SESSION_TYPE'),
        'SECRET_KEY_LENGTH': len(app.secret_key) if app.secret_key else 0,
        'UPLOAD_FOLDER': app.config.get('UPLOAD_FOLDER'),
    }

    from flask import jsonify
    return jsonify(config_info)

@app.route('/')
def index():
    """
    Landing page / dashboard.

    SYSTEM_CONTRACT – AUTH DISPLAY RULES:
    - If current_user.is_authenticated is true:
      - Marketing CTAs MUST NOT render
      - Logged-in workflow UI MUST render

    Implementation:
    - Logged-out: render marketing landing (index.html)
    - Logged-in: redirect to /create (primary workflow surface)
    """
    # Force user context loading by touching current_user
    if current_user.is_authenticated:
        # Logged-in workflow: send users directly to Create page
        return redirect(url_for('create_listing'))

    return render_template('index.html')

@app.route('/data/<path:filename>')
def serve_data_files(filename):
    """Serve uploaded files from data directory"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.join(os.getcwd(), 'data'), filename)

@app.route('/create')
def create_listing():
    """
    Create new listing page - per IMAGE_CONTRACT:
    - Listing must exist immediately, even if empty/draft
    - Images require listing_id to attach
    - Draft listings still own images
    - IMAGE_CONTRACT: "No anonymous writes to the database" - requires authentication
    """
    from flask import request
    import uuid
    
    # IMAGE_CONTRACT: "Nothing exists unless a user exists" - require authentication
    if not current_user.is_authenticated:
        flash('Please log in to create listings', 'info')
        return redirect(url_for('auth.login'))
    
    draft_id = request.args.get('draft_id', type=int)
    
    # If editing existing draft, load it
    if draft_id:
        db = get_db_instance()
        listing = db.get_listing(draft_id)
        if listing and listing.get('user_id') == str(current_user.id):
            # IMAGE_CONTRACT: UI reflects database truth - pass photos to template
            photos = listing.get('photos', [])
            # Ensure photos is a list (it might be JSON string or None)
            if isinstance(photos, str):
                try:
                    photos = json.loads(photos)
                except json.JSONDecodeError:
                    photos = []
            elif photos is None:
                photos = []

            return render_template('create.html',
                                 draft_id=draft_id,
                                 listing_id=draft_id,
                                 listing_uuid=listing.get('listing_uuid'),
                                 listing_photos=photos)
        else:
            # Draft not found or unauthorized
            flash('Draft not found', 'error')
            return redirect(url_for('drafts'))
    
    # IMAGE_CONTRACT Step 2: Create empty draft listing immediately for new listings
    # This ensures listing_id exists before any images are uploaded
    # "A listing is created immediately. Even if empty. Even if draft."
    try:
        db = get_db_instance()
        listing_uuid = str(uuid.uuid4())

        print(f"[CREATE] Creating draft for user_id={current_user.id}, listing_uuid={listing_uuid}", flush=True)

        # Create empty draft listing
        listing_id = db.create_listing(
            listing_uuid=listing_uuid,
            title='Untitled',
            description='',
            price=0.0,
            condition='good',
            photos=[],  # Empty photos array - images will be added via upload endpoint
            user_id=str(current_user.id),
            status='draft'
        )

        print(f"[CREATE] Draft created successfully: listing_id={listing_id}", flush=True)

        return render_template('create.html',
                             draft_id=listing_id,
                             listing_id=listing_id,
                             listing_uuid=listing_uuid,
                             listing_photos=[])
    except Exception as e:
        print(f"[CREATE ERROR] Failed to create draft: {e}", flush=True)
        import traceback
        traceback.print_exc()
        flash(f'Failed to create listing draft: {str(e)}', 'error')
        return redirect(url_for('drafts'))

@app.route('/drafts')
def drafts():
    """Drafts page - show empty state for unauthenticated users"""
    try:
        # Show empty list for unauthenticated users
        if not current_user.is_authenticated:
            return render_template('drafts.html', drafts=[])

        # Fetch all drafts for current user - user_id is UUID
        user_id_str = str(current_user.id)
        drafts_list = get_db_instance().get_drafts(user_id=user_id_str, limit=100)
        return render_template('drafts.html', drafts=drafts_list)
    except Exception as e:
        print(f"Error loading drafts page: {e}")
        import traceback
        traceback.print_exc()
        flash("Error loading drafts. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/listings')
@login_required
def listings():
    """Listings page"""
    db_instance = get_db_instance()
    cursor = db_instance._get_cursor()
    try:
        # Cast user_id to handle UUID/INTEGER type mismatch
        cursor.execute("""
            SELECT * FROM listings
            WHERE user_id::text = %s::text AND status != 'draft'
            ORDER BY created_at DESC
        """, (str(current_user.id),))
        user_listings = [dict(row) for row in cursor.fetchall()]
        return render_template('listings.html', listings=user_listings)
    finally:
        cursor.close()

@app.route('/notifications')
def notifications():
    """Notifications page - accessible to all"""
    return render_template('notifications.html')

@app.route('/storage')
def storage():
    """Storage overview - show empty state for unauthenticated users"""
    if not current_user.is_authenticated:
        return render_template('storage.html', storage_map={})

    storage_map = get_db_instance().get_storage_map(current_user.id)
    return render_template('storage.html', storage_map=storage_map)

@app.route('/storage/clothing')
@login_required
def storage_clothing():
    """Clothing storage"""
    bins = get_db_instance().get_storage_bins(current_user.id, bin_type='clothing')
    # Add section counts to each bin
    for bin in bins:
        sections = get_db_instance().get_storage_sections(bin['id'])
        bin['section_count'] = len(sections)
        bin['sections'] = sections
    return render_template('storage_clothing.html', bins=bins)

@app.route('/storage/cards')
@login_required
def storage_cards():
    """Card storage"""
    bins = get_db_instance().get_storage_bins(current_user.id, bin_type='cards')
    # Add section counts to each bin
    for bin in bins:
        sections = get_db_instance().get_storage_sections(bin['id'])
        bin['section_count'] = len(sections)
        bin['sections'] = sections
    return render_template('storage_cards.html', bins=bins)

@app.route('/storage/map')
@login_required
def storage_map():
    """Storage map"""
    storage_map_data = get_db_instance().get_storage_map(current_user.id)
    return render_template('storage_map.html', storage_map=storage_map_data)

@app.route('/settings')
@login_required
def settings():
    """User settings"""
    # Get user info
    db = get_db_instance()
    cursor = db._get_cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user = dict(cursor.fetchone())

        # Get marketplace credentials
        cursor.execute("SELECT * FROM marketplace_credentials WHERE user_id = %s", (current_user.id,))
        creds_rows = cursor.fetchall()
        credentials = {row['platform']: dict(row) for row in creds_rows}

        # Define platforms
        platforms = [
            {'id': 'poshmark', 'name': 'Poshmark', 'icon': 'fas fa-tshirt', 'color': 'text-danger'},
            {'id': 'mercari', 'name': 'Mercari', 'icon': 'fas fa-shopping-bag', 'color': 'text-primary'},
            {'id': 'ebay', 'name': 'eBay', 'icon': 'fab fa-ebay', 'color': 'text-warning'},
            {'id': 'grailed', 'name': 'Grailed', 'icon': 'fas fa-tshirt', 'color': 'text-dark'},
            {'id': 'depop', 'name': 'Depop', 'icon': 'fas fa-store', 'color': 'text-danger'},
            {'id': 'vinted', 'name': 'Vinted', 'icon': 'fas fa-tag', 'color': 'text-success'},
            {'id': 'whatnot', 'name': 'Whatnot', 'icon': 'fas fa-video', 'color': 'text-purple'},
            {'id': 'facebook', 'name': 'Facebook Marketplace', 'icon': 'fab fa-facebook', 'color': 'text-primary'},
            {'id': 'offerup', 'name': 'OfferUp', 'icon': 'fas fa-handshake', 'color': 'text-success'},
            {'id': 'rubylane', 'name': 'Ruby Lane', 'icon': 'fas fa-gem', 'color': 'text-danger'},
            {'id': 'chairish', 'name': 'Chairish', 'icon': 'fas fa-couch', 'color': 'text-info'},
        ]

        return render_template('settings.html', user=user, credentials=credentials, platforms=platforms)
    finally:
        cursor.close()

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    # Initialize worker system
    from src.workers.worker_manager import WorkerManager, sync_listing_handler, feed_sync_handler
    from src.workers.scheduler import Scheduler
    
    worker_manager = WorkerManager(num_workers=2)
    scheduler = Scheduler()
    
    # Register job handlers
    worker_manager.register_worker('sync_listing', sync_listing_handler)
    worker_manager.register_worker('feed_sync', feed_sync_handler)
    
    # Start workers and scheduler
    worker_manager.start()
    scheduler.start()
    
    print("Worker system initialized and started")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
