# File Organization Summary
## Rebel Operator / AI Cross-Poster Codebase Structure

This document provides a high-level overview of how the codebase is organized, based on pages and functionality.

---

## 📁 MAIN APPLICATION STRUCTURE

```
Rebel-Operator/
├── web_app.py              ⭐ Flask app entry point (356 lines)
│   ├── /                   → index.html (Landing/Dashboard)
│   ├── /create             → create.html (Create Listing)
│   ├── /drafts             → drafts.html (Draft Management)
│   ├── /inventory          → inventory.html (Inventory)
│   ├── /listings           → listings.html (Active Listings)
│   ├── /notifications      → notifications.html
│   ├── /settings           → settings.html
│   ├── /export             → export.html
│   ├── /vault              → vault.html
│   ├── /hall-of-records    → hall_of_records.html
│   ├── /post-listing       → post-listing.html
│   ├── /storage            → storage.html
│   ├── /storage/clothing   → storage_clothing.html
│   ├── /storage/cards      → storage_cards.html
│   ├── /storage/map        → storage_map.html
│   └── /storage/instructions → storage_instructions.html
│
├── routes_auth.py          🔐 Authentication (536 lines)
│   ├── /login              → login.html
│   ├── /register           → register.html
│   ├── /logout             → (redirect)
│   ├── /forgot-password    → forgot_password.html
│   ├── /reset-password/<token> → reset_password.html
│   └── API: /api/auth/* (login, logout, session, google)
│
├── routes_admin.py         👑 Admin Features (359 lines)
│   ├── /admin              → admin/dashboard.html
│   ├── /admin/users        → admin/users.html
│   ├── /admin/user/<id>    → admin/user_detail.html
│   ├── /admin/activity     → admin/activity.html
│   ├── /admin/photo-curation → admin/photo_curation.html
│   ├── /admin/hall-photos  → admin/hall_photos.html
│   └── API: /api/admin/* (user management, photo curation)
│
├── routes_cards.py         🃏 Card Collections (619 lines)
│   ├── /cards              → cards.html
│   ├── /vault/cards        → vault_cards.html
│   ├── /vault/coins        → vault_coins.html
│   └── API: /api/cards/*, /api/coins/*, /api/vault/* (16+ endpoints)
│
├── routes_main.py          🎯 Core Features (4,391 lines)
│   ├── /my-artifacts       → my_artifacts.html
│   ├── /artifact/<id>      → artifact_detail.html
│   ├── /platforms          → platforms.html
│   ├── /invoicing          → invoicing.html
│   ├── /billing            → billing.html
│   └── API: 80+ endpoints (photos, drafts, storage, platforms, etc.)
│
├── routes_csv.py           📊 CSV Operations (554 lines)
│   └── API: /api/*-csv (drafts, vault, inventory, post-listing)
│
├── monitoring/health.py    🏥 Health Checks
│   ├── /health
│   ├── /health/ready
│   └── /health/live
│
└── templates/              📄 HTML Templates (33 files)
    ├── *.html              (29 main templates)
    └── admin/*.html        (6 admin templates)
```

---

## 🗂️ FILE RESPONSIBILITIES

### `web_app.py` - Application Bootstrap (15 pages)
**Purpose:** Flask initialization, main routes, blueprint registration

**Pages:**
- Landing/Dashboard (/)
- Core workflow pages (create, drafts, inventory, listings)
- Storage pages (5 pages)
- Vault & Hall of Records
- Utility pages (notifications, settings, export)

**Key Responsibilities:**
- Flask app configuration
- Session management
- Security headers
- User authentication setup (Flask-Login)
- Blueprint registration

---

### `routes_auth.py` - Authentication & User Access (4 pages)
**Purpose:** User authentication, registration, password management

**Pages:**
- Login
- Register
- Forgot Password
- Reset Password

**API Endpoints (4):**
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/session
- POST /api/auth/google
- GET /api/auth/google-client-id

**Key Responsibilities:**
- User login/logout
- Password hashing/verification
- Email verification
- Google OAuth integration
- Session management

---

### `routes_admin.py` - Admin Dashboard & Management (6 pages)
**Purpose:** Administrative functions, user management, content curation

**Pages:**
- Admin Dashboard
- User Management
- User Detail
- Activity Logs
- Photo Curation
- Hall Photos

**API Endpoints (5+):**
- User management (activate, deactivate, delete, admin toggle)
- Photo selection
- Debug tools

**Key Responsibilities:**
- User administration
- System monitoring
- Content moderation
- Activity tracking

---

### `routes_cards.py` - Card & Collectible Management (3 pages)
**Purpose:** Trading card collections, coin collections, vault management

**Pages:**
- Cards Collection
- Card Vault
- Coin Vault

**API Endpoints (16+):**
- Card CRUD operations
- Card search & filtering
- Collection statistics
- Import/export
- Organization modes

**Key Responsibilities:**
- Card collection management
- AI card analysis
- Storage location tracking
- Collection statistics
- Vault management

---

### `routes_main.py` - Core Application Features (7 pages)
**Purpose:** Main application functionality (largest file: 4,391 lines)

**Pages:**
- My Artifacts
- Artifact Detail
- Platforms
- Invoicing
- Billing
- Billing Success

**API Endpoints (80+):**
- Photo upload & processing
- AI analysis (analyze, enhanced-scan, analyze-card)
- Draft management (save, get, delete, update, bulk operations)
- Storage management (locations, bins, sections, items)
- Platform publishing (connect, disconnect, publish, delist)
- Sales & sync
- Export/import
- Settings & credentials
- Inventory management
- Invoicing & billing
- Reports & analytics

**Key Responsibilities:**
- Photo upload & compression
- AI-powered listing enhancement
- Draft lifecycle management
- Physical storage tracking
- Multi-platform publishing
- Sales tracking & sync
- Export/import operations
- Credential management
- Billing & subscriptions

---

### `routes_csv.py` - CSV Data Operations (0 pages, API only)
**Purpose:** CSV-based data persistence (legacy/compatibility layer)

**API Endpoints (11):**
- CSV drafts operations
- CSV vault operations
- CSV inventory operations
- Post listing from CSV

**Key Responsibilities:**
- CSV file reading/writing
- CSV data validation
- Legacy data format support

---

### `monitoring/health.py` - Health Checks (0 pages, health only)
**Purpose:** Kubernetes/deployment health checks

**Health Endpoints (3):**
- /health - Basic health
- /health/ready - Readiness (checks DB)
- /health/live - Liveness

**Key Responsibilities:**
- Application health monitoring
- Database connectivity verification
- Deployment readiness checks

---

## 📊 STATISTICS BY FILE

| File | Lines | Pages | API Endpoints | Primary Function |
|------|-------|-------|---------------|-----------------|
| routes_main.py | 4,391 | 7 | 80+ | Core features |
| gui.py | 2,255 | N/A | N/A | Desktop GUI |
| routes_cards.py | 619 | 3 | 16+ | Card collections |
| main.py | 567 | N/A | N/A | CLI interface |
| routes_csv.py | 554 | 0 | 11 | CSV operations |
| routes_auth.py | 536 | 4 | 5 | Authentication |
| routes_admin.py | 359 | 6 | 5+ | Administration |
| web_app.py | 356 | 15 | 0 | App bootstrap |
| **Total** | **~10,000+** | **33** | **120+** | |

---

## 🎯 FUNCTIONAL GROUPING

### User-Facing Pages (27 pages)
**Authentication (4):**
- Login, Register, Forgot Password, Reset Password

**Core Workflow (9):**
- Landing, Create, Drafts, Inventory, Listings, Post-Listing, Export, Settings, Notifications

**Storage (5):**
- Storage Overview, Clothing, Cards, Map, Instructions

**Collections (5):**
- Vault, Hall of Records, My Artifacts, Artifact Detail, Cards Collection

**Commerce (3):**
- Platforms, Invoicing, Billing

**Specialized (1):**
- Vault subsections (Cards, Coins)

### Admin Pages (6 pages)
- Dashboard, Users, User Detail, Activity, Photo Curation, Hall Photos

---

## 🔄 TYPICAL USER FLOWS

### New User Flow:
```
/register → /login → / (dashboard) → /create → /drafts → /post-listing → /listings
```

### Card Collector Flow:
```
/login → /cards → (upload photos) → AI analysis → /vault/cards
```

### Seller Flow:
```
/create → (upload photos) → AI enhancement → /drafts → 
/platforms (connect) → /post-listing → /listings → (sale) → /invoicing
```

### Admin Flow:
```
/admin → /admin/users → /admin/user/<id> → 
/admin/photo-curation → /admin/hall-photos
```

---

## 📦 TEMPLATE ORGANIZATION

```
templates/
├── Main Templates (29 files)
│   ├── index.html
│   ├── login.html, register.html
│   ├── create.html, drafts.html
│   ├── inventory.html, listings.html
│   ├── cards.html, vault*.html
│   ├── storage*.html
│   └── ...more
│
└── admin/ (6 files)
    ├── dashboard.html
    ├── users.html
    ├── user_detail.html
    ├── activity.html
    ├── photo_curation.html
    └── hall_photos.html
```

---

## 🧩 BLUEPRINT ARCHITECTURE

Flask uses **blueprints** to organize routes:

```python
# In web_app.py
app = Flask(__name__)

# Register blueprints
app.register_blueprint(auth_bp)      # /login, /register, etc.
app.register_blueprint(admin_bp)     # /admin/*
app.register_blueprint(cards_bp)     # /cards, /vault/*
app.register_blueprint(main_bp)      # API endpoints
app.register_blueprint(csv_bp)       # CSV API
app.register_blueprint(health_bp)    # /health
```

Each blueprint is a self-contained module with its own routes.

---

## 🎨 DESIGN PATTERNS

### Route Definition Pattern:
```python
@blueprint.route('/path')
@login_required  # If authentication needed
def page_handler():
    return render_template('template.html')
```

### API Endpoint Pattern:
```python
@blueprint.route('/api/endpoint', methods=['POST'])
@login_required
def api_handler():
    data = request.get_json()
    # Process data
    return jsonify({'success': True})
```

### Admin-Only Pattern:
```python
@admin_bp.route('/admin/feature')
@admin_required  # Custom decorator
def admin_feature():
    return render_template('admin/feature.html')
```

---

## 🔗 QUICK ACCESS

For detailed information, see:
- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Complete page-to-file mapping
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - All features documented
- **[QUICK_START_NAVIGATION.md](QUICK_START_NAVIGATION.md)** - Developer quick reference
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Master documentation index

---

*Last Updated: 2026-01-19*
*File organization summary for Rebel Operator codebase*
