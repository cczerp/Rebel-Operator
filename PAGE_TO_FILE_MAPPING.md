# Page-to-File Mapping
## Complete Web Application Route Structure

This document provides a comprehensive mapping of all web pages in the Rebel Operator / AI Cross-Poster application, organized by the files that define them.

---

## 📄 FILE: `web_app.py`
*Main application entry point - contains core page routes*

### Landing & Dashboard
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/` | `index.html` | Landing page/dashboard | ❌ No (guest accessible) |

### Listing Management Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/create` | `create.html` | Create new listing with AI analysis | ❌ No (8 free AI uses for guests) |
| `/drafts` | `drafts.html` | Manage draft listings before publishing | ✅ Yes |
| `/inventory` | `inventory.html` | Centralized inventory management | ✅ Yes |
| `/listings` | `listings.html` | View active (non-draft) listings | ✅ Yes |
| `/post-listing` | `post-listing.html` | Post listing to platforms | ✅ Yes |

### Storage Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/storage` | `storage.html` | Storage system overview | ✅ Yes |
| `/storage/clothing` | `storage_clothing.html` | Clothing storage management | ✅ Yes |
| `/storage/cards` | `storage_cards.html` | Card storage management | ✅ Yes |
| `/storage/map` | `storage_map.html` | Visual storage location map | ✅ Yes |
| `/storage/instructions` | `storage_instructions.html` | Storage organization guide | ✅ Yes |

### Collection & Vault Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/vault` | `vault.html` | Collection vault overview | ✅ Yes |
| `/hall-of-records` | `hall_of_records.html` | Browse public artifacts gallery | ❌ No |

### Utility Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/notifications` | `notifications.html` | User notifications center | ✅ Yes |
| `/settings` | `settings.html` | User settings & preferences | ✅ Yes |
| `/export` | `export.html` | CSV export functionality | ✅ Yes |

---

## 🔐 FILE: `routes_auth.py`
*Authentication & user account management*

| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/login` | `login.html` | User login page | ❌ No |
| `/register` | `register.html` | New user registration | ❌ No |
| `/logout` | N/A (redirect) | Log out user | ✅ Yes |
| `/forgot-password` | `forgot_password.html` | Password recovery initiation | ❌ No |
| `/reset-password/<token>` | `reset_password.html` | Password reset with token | ❌ No |

**API Endpoints (not pages):**
- `POST /api/auth/login` - Programmatic login
- `POST /api/auth/logout` - API logout
- `GET /api/auth/session` - Check session status
- `POST /api/auth/google` - Google OAuth login
- `GET /api/auth/google-client-id` - Get Google client ID

---

## 👑 FILE: `routes_admin.py`
*Administrator-only pages and controls*

### Admin Dashboard & Users
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/admin` | `admin/dashboard.html` | Main admin dashboard with system stats | 🔒 Admin only |
| `/admin/users` | `admin/users.html` | User management list | 🔒 Admin only |
| `/admin/user/<int:user_id>` | `admin/user_detail.html` | Individual user details & activity | 🔒 Admin only |
| `/admin/activity` | `admin/activity.html` | System-wide activity logs | 🔒 Admin only |

### Admin Content Management
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/admin/photo-curation` | `admin/photo_curation.html` | Photo curation dashboard | 🔒 Admin only |
| `/admin/hall-photos` | `admin/hall_photos.html` | Hall of Records photo review | 🔒 Admin only |

**API Endpoints (admin-only):**
- `POST /api/admin/toggle-photo-selection` - Toggle photo in gallery
- `POST /api/admin/user/<user_id>/toggle-active` - Activate/deactivate user
- `POST /api/admin/user/<user_id>/toggle-admin` - Grant/revoke admin
- `DELETE /api/admin/user/<user_id>/delete` - Delete user account
- `GET /api/admin/debug/users` - Debug user data

---

## 🃏 FILE: `routes_cards.py`
*Card collection & collectibles management*

| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/cards` | `cards.html` | Card collection management page | ✅ Yes |
| `/vault/cards` | `vault_cards.html` | Card vault view | ✅ Yes |
| `/vault/coins` | `vault_coins.html` | Coin collection vault | ✅ Yes |

**API Endpoints:**
- `POST /api/analyze-card` - AI card analysis
- `POST /api/cards/add` - Add card to collection
- `GET /api/cards/list` - List all cards
- `GET /api/cards/search` - Search cards
- `GET /api/cards/stats` - Collection statistics
- `GET /api/cards/organized` - Get organized card view
- `GET /api/cards/<card_id>` - Get single card
- `PUT /api/cards/<card_id>` - Update card
- `DELETE /api/cards/<card_id>` - Delete card
- `POST /api/cards/switch-organization` - Change organization mode
- `GET /api/cards/export` - Export collection
- `POST /api/cards/import` - Import collection
- `GET /api/coins/list` - List coins
- `GET /api/coins/stats` - Coin statistics
- `GET /api/vault/stats` - Vault statistics

---

## 📋 FILE: `routes_main.py`
*Main application routes - listings, storage, artifacts, platforms*

### Artifact Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/my-artifacts` | `my_artifacts.html` | User's personal artifact collection | ✅ Yes |
| `/artifact/<int:artifact_id>` | `artifact_detail.html` | Individual artifact detail view | ✅ Yes |

### Commerce Pages
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/platforms` | `platforms.html` | Platform connections management | ✅ Yes |
| `/invoicing` | `invoicing.html` | Invoice management system | ✅ Yes |
| `/billing` | `billing.html` | Billing & subscription management | ✅ Yes |

### Billing Success
| Route | Template | Description | Auth Required |
|-------|----------|-------------|---------------|
| `/billing/success` | N/A (redirect or message) | Successful billing callback | ✅ Yes |

**Major API Endpoints (100+ total):**

**Photo & Image Processing:**
- `POST /api/upload-photos` - Upload product photos
- `POST /api/edit-photo` - Edit uploaded photo
- `POST /api/cleanup-temp-photos` - Clean temporary files
- `POST /api/image/process` - Process image

**AI Analysis:**
- `POST /api/analyze` - AI photo analysis
- `POST /api/analyze-card` - Card-specific AI analysis
- `POST /api/enhanced-scan` - Enhanced scanning

**Draft Management:**
- `GET /api/drafts` - Get user drafts
- `POST /api/save-draft` - Save listing as draft
- `GET /api/get-draft/<listing_id>` - Get specific draft
- `DELETE /api/delete-draft/<listing_id>` - Delete draft
- `DELETE /api/drafts/bulk-delete` - Bulk delete drafts
- `PATCH /api/update-drafts` - Update draft listings
- `POST /api/bulk-edit-drafts` - Bulk edit drafts

**Storage Management:**
- `GET /api/storage/locations` - Get storage locations
- `GET /api/storage/location/<location_id>` - Get specific location
- `POST /api/storage/location` - Create storage location
- `POST /api/storage/assign` - Assign item to storage
- `POST /api/storage/bulk-assign` - Bulk assign storage
- `GET /api/storage/find` - Find storage item
- `POST /api/storage/suggest` - Get storage suggestions
- `GET /api/storage/bins` - Get storage bins
- `POST /api/storage/create-bin` - Create storage bin
- `POST /api/storage/create-section` - Create storage section
- `GET /api/storage/items` - Get stored items
- `POST /api/storage/add-item` - Add item to storage

**Platform Publishing:**
- `POST /api/listing/<listing_id>/publish-to-platform` - Publish to specific platform
- `POST /api/listing/<listing_id>/delist-from-platform` - Remove from platform
- `GET /api/listing/<listing_id>/platforms` - Get listing's platform status
- `POST /api/platform/<platform>/connect` - Connect platform credentials
- `DELETE /api/platform/<platform>/disconnect` - Disconnect platform
- `GET /api/platform/<platform>/test` - Test platform connection

**Sales & Sync:**
- `GET /api/sales/<listing_id>` - Get sales for listing
- `POST /api/sales/manual-sale` - Record manual sale
- `POST /api/sales/sync-all` - Sync all platform sales
- `POST /api/sales/sync/<platform>` - Sync specific platform

**Export/Import:**
- `POST /api/export/csv/<platform>` - Export CSV for platform
- `GET /api/export/platforms` - Get available platforms
- `POST /api/export/preview/<platform>` - Preview export
- `POST /api/import/csv` - Import CSV data
- `POST /api/export-csv` - General CSV export

**Settings:**
- `POST /api/settings/api-credentials` - Save API credentials
- `GET /api/settings/api-credentials/<platform>` - Get platform credentials
- `POST /api/settings/platform-credentials` - Save platform credentials
- `GET /api/settings/platform-credentials` - Get all credentials
- `POST /api/settings/marketplace-credentials` - Save marketplace login
- `DELETE /api/settings/marketplace-credentials/<platform>` - Remove credentials
- `POST /api/settings/notification-email` - Update notification email

**Artifacts & Collectibles:**
- `GET /api/artifacts/<artifact_id>` - Get artifact details
- `POST /api/artifacts/<artifact_id>/select-photos` - Select artifact photos
- `POST /api/user/artifacts/save` - Save artifact to collection
- `POST /api/collectibles/add` - Add collectible
- `POST /api/cards/add` - Add card
- `GET /api/cards/<card_id>` - Get card
- `PUT /api/cards/<card_id>` - Update card
- `DELETE /api/cards/<card_id>` - Delete card

**Inventory:**
- `GET /api/inventory/listings` - Get inventory listings
- `GET /api/inventory/export` - Export inventory
- `POST /api/inventory/bulk-update` - Bulk update inventory
- `POST /api/inventory/bulk-delete` - Bulk delete inventory

**Invoicing:**
- `POST /api/create-invoice` - Create new invoice
- `GET /api/invoices` - Get all invoices
- `GET /api/invoice/<invoice_id>` - Get specific invoice
- `POST /api/email-invoice/<invoice_id>` - Email invoice to customer

**Billing:**
- `POST /api/billing/create-checkout-session` - Create Stripe session
- `POST /api/billing/cancel-subscription` - Cancel subscription
- `GET /api/billing/check-feature-access` - Check tier access
- `GET /api/billing/usage` - Get usage stats
- `POST /api/billing/webhook` - Stripe webhook handler

**Reports:**
- `GET /api/reports/profit` - Profit report
- `GET /api/reports/tax/<period>` - Tax report for period

**Feed Management:**
- `POST /api/generate-feed` - Generate product feed
- `POST /api/schedule-feed-sync` - Schedule feed sync

**Other:**
- `GET /api/test-supabase` - Test Supabase connection
- `GET /uploads/<filename>` - Serve uploaded files

---

## 📊 FILE: `routes_csv.py`
*CSV-based data management (legacy/compatibility)*

**No page routes - API only:**
- `GET /api/drafts-csv` - Get drafts as CSV
- `POST /api/save-draft-csv` - Save draft to CSV
- `PATCH /api/drafts-csv/update` - Update CSV draft
- `DELETE /api/drafts-csv/delete` - Delete CSV draft
- `POST /api/save-vault-csv` - Save to vault CSV
- `GET /api/inventory-csv` - Get inventory CSV
- `POST /api/inventory-csv/add` - Add to inventory CSV
- `PATCH /api/inventory-csv/update` - Update inventory CSV
- `DELETE /api/inventory-csv/delete` - Delete from inventory CSV
- `POST /api/post-listing` - Post listing from CSV

---

## 🏥 FILE: `monitoring/health.py`
*Health check endpoints for deployment*

**No page routes - Health checks only:**
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (checks database)
- `GET /health/live` - Liveness probe

---

## 📈 Summary Statistics

### Total Pages: **33 HTML pages**
- **Main pages:** 15 (web_app.py)
- **Authentication pages:** 4 (routes_auth.py)
- **Admin pages:** 6 (routes_admin.py)
- **Card collection pages:** 3 (routes_cards.py)
- **Artifact pages:** 2 (routes_main.py)
- **Commerce pages:** 3 (routes_main.py)

### Total API Endpoints: **120+ endpoints**
- **routes_main.py:** ~80 endpoints
- **routes_cards.py:** ~16 endpoints
- **routes_csv.py:** ~11 endpoints
- **routes_admin.py:** ~5 endpoints
- **routes_auth.py:** ~4 endpoints
- **monitoring/health.py:** 3 endpoints

### Access Control Summary:
- **Public pages (no auth):** 6 pages
  - `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/hall-of-records`
- **Guest accessible with limits:** 1 page
  - `/create` (8 free AI uses)
- **Authenticated pages:** 20 pages
- **Admin-only pages:** 6 pages

---

## 🎯 Quick Reference by Functionality

### **Authentication Flow:**
`/register` → `/login` → `/` (dashboard)

### **Listing Creation Flow:**
`/create` → `/drafts` → `/post-listing` → `/listings`

### **Card Collection Flow:**
`/cards` → `/vault/cards` or `/vault/coins`

### **Storage Management Flow:**
`/storage` → `/storage/map` or `/storage/cards` or `/storage/clothing`

### **Admin Workflow:**
`/admin` → `/admin/users` → `/admin/user/<id>` or `/admin/photo-curation`

---

*Last Updated: 2026-01-19*
*Generated from codebase analysis of Rebel-Operator repository*
