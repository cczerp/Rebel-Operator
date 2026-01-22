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
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_required, current_user
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

from src.database import get_db

# Load environment
load_dotenv()

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================

app = Flask(__name__)
import json

@app.template_filter('fromjson')
def fromjson_filter(json_string):
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = './data/uploads'

# ============================================================================
# SESSION & SECURITY CONFIGURATION
# ============================================================================

# Detect if we're in production with HTTPS
is_production = os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT')
use_https = is_production or os.getenv('FORCE_HTTPS', 'False').lower() == 'true'

# Session security settings - using standard Flask sessions (client-side, signed cookies)
app.config['SESSION_COOKIE_SECURE'] = use_https  # HTTPS-only cookies (only in production)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF while allowing OAuth flows
app.config['PERMANENT_SESSION_LIFETIME'] = 604800  # 7 days in seconds

print(f"[SESSION] Production: {is_production}, HTTPS: {use_https}, Secure cookies: {use_https}")

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize database (PostgreSQL)
db = get_db()
# Admin user is created automatically by db.py on connection

# Initialize notification manager (optional)
notification_manager = None
try:
    from src.notifications import NotificationManager
    notification_manager = NotificationManager.from_env()
except Exception:
    pass

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
        """Get user by ID from PostgreSQL"""
        user_data = db.get_user_by_id(user_id)
        if user_data:
            return User(
                user_data['id'],
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
    """Load user for Flask-Login"""
    return User.get(int(user_id))

# ============================================================================
# SECURITY HEADERS & CACHE CONTROL
# ============================================================================

@app.after_request
def add_security_headers(response):
    """Add security headers to prevent caching and session hijacking"""

    # Prevent caching of dynamic content (pages, API responses)
    # Allow static assets (JS, CSS, images) to be cached
    if request.path.startswith('/static/') or request.path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
        # Allow caching for static assets
        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:
        # Prevent caching for dynamic content
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Only add HSTS in production with HTTPS
    if use_https:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Remove server header to reduce information disclosure
    response.headers.pop('Server', None)

    return response

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
from src.routes.auth import auth_bp, init_routes as init_auth
from src.routes.admin import admin_bp, init_routes as init_admin
from src.routes.cards import cards_bp, init_routes as init_cards
from src.routes.main import main_bp, init_routes as init_main
from src.routes.csv import csv_bp
from src.routes.import_routes import import_bp
from src.routes.ledger_routes import ledger_bp
from src.routes.search_routes import search_bp, init_routes as init_search
from monitoring.health import health_bp

# Initialize blueprints with database and User class
init_auth(db, User)
init_admin(db)
init_cards(db)
init_main(db)
init_search(db)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cards_bp)
app.register_blueprint(main_bp)
app.register_blueprint(csv_bp)
app.register_blueprint(import_bp)  # Listing import routes
app.register_blueprint(ledger_bp)  # Master ledger system
app.register_blueprint(search_bp)  # Multi-platform search
app.register_blueprint(health_bp)

# ============================================================================
# MAIN ROUTES (not in blueprints)
# ============================================================================

@app.route('/')
def index():
    """Landing page / dashboard - allows guest access"""
    return render_template('index.html', is_guest=not current_user.is_authenticated)

@app.route('/create')
def create_listing():
    """Create new listing page - allows guest access with 8 free AI uses"""
    from flask import session
    draft_id = request.args.get('draft_id', type=int)
    scan_draft = request.args.get('scan_draft', type=int)
    
    # Initialize guest usage tracking if not authenticated
    if not current_user.is_authenticated:
        if 'guest_ai_uses' not in session:
            session['guest_ai_uses'] = 0
        guest_uses_remaining = 8 - session.get('guest_ai_uses', 0)
    else:
        guest_uses_remaining = None
    
    return render_template('create.html', 
                         draft_id=draft_id,
                         scan_draft=scan_draft,
                         is_guest=not current_user.is_authenticated,
                         guest_uses_remaining=guest_uses_remaining)

@app.route('/drafts')
@login_required
def drafts():
    """Drafts page - CSV-style ledger view"""
    return render_template('drafts_ledger.html')

@app.route('/inventory')
@login_required
def inventory():
    """Inventory page - CSV-based"""
    return render_template('inventory.html')

@app.route('/listings')
@login_required
def listings():
    """Listings page - CSV-style ledger view with switcher"""
    return render_template('listings_ledger.html')

@app.route('/notifications')
@login_required
def notifications():
    """Notifications page"""
    return render_template('notifications.html')

@app.route('/storage')
@login_required
def storage():
    """Storage overview"""
    storage_map = db.get_storage_map(current_user.id)
    return render_template('storage.html', storage_map=storage_map)

@app.route('/storage/clothing')
@login_required
def storage_clothing():
    """Clothing storage"""
    bins = db.get_storage_bins(current_user.id, bin_type='clothing')
    return render_template('storage_clothing.html', bins=bins)

@app.route('/storage/cards')
@login_required
def storage_cards():
    """Card storage"""
    bins = db.get_storage_bins(current_user.id, bin_type='cards')
    return render_template('storage_cards.html', bins=bins)

@app.route('/storage/map')
@login_required
def storage_map():
    """Storage map"""
    return render_template('storage_map.html')

@app.route('/storage/instructions')
@login_required
def storage_instructions():
    """Storage organization instructions and guide"""
    return render_template('storage_instructions.html')

@app.route('/settings')
@login_required
def settings():
    """User settings"""
    return render_template('settings.html')

@app.route('/export')
@login_required
def export_page():
    """CSV export page"""
    return render_template('export.html')

@app.route('/vault')
@login_required
def vault():
    """Collection Vault page"""
    return render_template('vault.html')

@app.route('/hall-of-records')
def hall_of_records():
    """Hall of Records - Browse all public artifacts"""
    try:
        artifacts = db.get_all_artifacts(limit=100)
    except Exception as e:
        import logging
        logging.error(f"Hall of Records error: {e}")
        artifacts = []
    return render_template('hall_of_records.html', artifacts=artifacts)

@app.route('/post-listing')
@login_required
def post_listing_page():
    """Post Listing page"""
    return render_template('post-listing.html')

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
