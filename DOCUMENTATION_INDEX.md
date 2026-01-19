# Documentation Index
## Rebel Operator / AI Cross-Poster - Complete Documentation

This index provides quick access to all documentation for the Rebel Operator / AI Cross-Poster project.

---

## 📚 DOCUMENTATION STRUCTURE

### 🗺️ **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**
**Complete page-to-file mapping of the web application**

- Maps all 33 HTML pages to their source files
- Organized by functionality (Auth, Admin, Main, Cards, etc.)
- Lists all 120+ API endpoints by file
- Shows which pages require authentication
- Quick reference for navigation flows
- Summary statistics (pages, endpoints, access control)

**Best for:** 
- Finding which file defines a specific page
- Understanding the application structure
- Locating API endpoints
- Understanding authentication requirements

---

### ✨ **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)**
**Comprehensive list of all features and capabilities**

- 17 functional categories of features
- Platform integrations (17 platforms)
- AI capabilities (3 providers)
- Storage & photo management
- Card/collectible management
- User management & authentication
- Admin features
- Export/import capabilities
- Billing & subscription framework
- Notifications & alerts
- And more...

**Best for:**
- Understanding what the application can do
- Feature discovery
- Platform capabilities reference
- Planning new features
- Technical sales/demos

---

## 🎯 QUICK REFERENCE

### By Role

#### **For Developers**
- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Find code locations
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Understand feature requirements

#### **For Product Managers**
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Complete feature list
- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - User journey mapping

#### **For Designers**
- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Page inventory
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Feature requirements

#### **For QA/Testing**
- **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Test coverage planning
- **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Feature test scenarios

---

## 📂 FILE ORGANIZATION

### Main Application Files

**Entry Point:**
- `web_app.py` - Flask app initialization, main routes, blueprints

**Route Files:**
- `routes_auth.py` - Authentication (login, register, password reset)
- `routes_admin.py` - Admin dashboard and management
- `routes_cards.py` - Card collection management
- `routes_main.py` - Core application routes (listings, storage, artifacts, platforms)
- `routes_csv.py` - CSV-based data operations

**Supporting Files:**
- `monitoring/health.py` - Health check endpoints

**Template Directory:**
- `templates/` - All HTML templates (33 files)
- `templates/admin/` - Admin-specific templates (6 files)

---

## 🔍 HOW TO USE THIS DOCUMENTATION

### Finding a Page Definition
1. Open **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**
2. Search for the route (e.g., `/create`, `/drafts`)
3. Find the file name and line numbers

### Understanding a Feature
1. Open **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)**
2. Navigate to the relevant category
3. Read feature descriptions and capabilities

### Planning a New Feature
1. Check **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** to see if it exists
2. Check **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** to find related code
3. Determine which file should contain the new feature

### Debugging a Page
1. Find the route in **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**
2. Open the corresponding file
3. Check related API endpoints in the same file

---

## 📊 PROJECT STATISTICS

### Codebase Size
| Metric | Count |
|--------|-------|
| **Python Files** | 14 main files |
| **Lines of Code** | ~10,000+ lines |
| **HTML Templates** | 33 pages |
| **Route Files** | 5 blueprints |
| **API Endpoints** | 120+ endpoints |

### Application Scope
| Metric | Count |
|--------|-------|
| **Pages** | 33 HTML pages |
| **Features** | 100+ features |
| **Platforms** | 17 platform integrations |
| **AI Providers** | 3 providers |
| **User Tiers** | 3 tiers (FREE/PRO/ELITE) |

### File Sizes
| File | Lines | Primary Purpose |
|------|-------|-----------------|
| `routes_main.py` | 4,391 | Core application routes |
| `gui.py` | 2,255 | Desktop GUI application |
| `routes_cards.py` | 619 | Card collection features |
| `main.py` | 567 | CLI interface |
| `routes_csv.py` | 554 | CSV operations |
| `routes_auth.py` | 536 | Authentication |
| `routes_admin.py` | 359 | Admin features |
| `web_app.py` | 356 | App initialization |

---

## 🚀 GETTING STARTED

### For New Developers
1. Read **[README.md](README.md)** - Project overview
2. Review **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** - Code structure
3. Skim **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Feature overview
4. Set up local environment (see README.md)

### For Feature Development
1. Check **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** - Feature scope
2. Find related code in **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**
3. Review existing patterns in the codebase
4. Implement following established conventions

### For Bug Fixes
1. Identify affected page/feature
2. Locate code in **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)**
3. Check related features in **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)**
4. Fix and test thoroughly

---

## 📖 ADDITIONAL DOCUMENTATION

### Existing Documentation Files
- `README.md` - Project overview and installation
- `README_WEB_APP.md` - Web application specific docs
- `DEPLOYMENT.md` - Deployment instructions
- `ENVIRONMENT_VARIABLES.md` - Environment configuration
- `GETTING_STARTED.md` - Quick start guide
- `AUTHENTICATION.md` - Authentication system details
- `PHOTOSYNC_SETUP.md` - PhotoSync integration guide
- `PLATFORMS_README.md` - Platform integration details
- `COMPLIANCE_REPORT.md` - Compliance and security
- `EDITABLE_DRAFTS_*.md` - Draft management docs
- `IMAGE_UPLOAD_FLOW_DOCUMENTATION.md` - Photo upload flow
- `STORAGE_*.md` - Storage system documentation

### Technical Documentation
- `BUCKET_ARCHITECTURE.md` - Storage bucket architecture
- `DATABASE_CONNECTION_POOL_FIX.md` - Database connection pooling
- `SUPABASE_MIGRATION_SUMMARY.md` - Database migration guide
- `RLS_FIX.md` - Row-level security setup

### Feature-Specific Documentation
- `CARD_ORGANIZATION_GUIDE.md` - Card collection organization
- `PLATFORM_INTEGRATION_PLAN.md` - Platform integration roadmap
- `AI_TASKS.md` - AI enhancement tasks
- `CONTRACTS.md` - API contracts and interfaces

---

## 🔗 QUICK LINKS

### Page Categories (from PAGE_TO_FILE_MAPPING.md)
- [Authentication Pages](#authentication-pages) - Login, register, password reset
- [Main Application Pages](#main-application-pages) - Create, drafts, inventory, listings
- [Storage Pages](#storage-pages) - Storage management
- [Vault & Collection Pages](#vault--collection-pages) - Artifacts, cards
- [Admin Pages](#admin-pages) - Admin dashboard and tools

### Feature Categories (from FEATURES_CAPABILITIES.md)
- [Core Listing Features](#1-core-listing-features)
- [Platform Integrations](#2-platform-integrations-17-platforms)
- [AI Capabilities](#3-ai-capabilities)
- [Storage & Photo Management](#4-storage--photo-management)
- [Card/Collectible Management](#5-card--collectible-management)
- [Physical Storage Management](#6-physical-storage-management)
- [User Management & Authentication](#7-user-management--authentication)
- [Admin Features](#8-admin-features)
- [Export/Import Features](#9-export--import-features)
- [Billing & Subscription](#10-billing--subscription-framework-ready)
- [Notifications & Alerts](#11-notifications--alerts)
- [Settings & Credentials](#12-settings--credentials)
- [Cross-Platform Publishing](#13-cross-platform-publishing)
- [Shopping Mode & Market Analysis](#14-shopping-mode--market-analysis)
- [Knowledge Distillation & AI Training](#15-knowledge-distillation--ai-training)
- [Integrations & External Services](#16-integrations--external-services)
- [Unique Capabilities](#17-unique-capabilities)

---

## 📝 MAINTENANCE

### Keeping Documentation Updated
When making code changes:
1. Update **[PAGE_TO_FILE_MAPPING.md](PAGE_TO_FILE_MAPPING.md)** if adding/removing pages or major API endpoints
2. Update **[FEATURES_CAPABILITIES.md](FEATURES_CAPABILITIES.md)** if adding/removing features
3. Update this index if adding new documentation files

### Documentation Standards
- Keep page mappings accurate with actual routes
- Include file names and line numbers where helpful
- Organize features by logical categories
- Use tables for structured data
- Include code examples where appropriate

---

## 🤝 CONTRIBUTING

When contributing to this project:
1. Review existing features in **FEATURES_CAPABILITIES.md**
2. Check code location in **PAGE_TO_FILE_MAPPING.md**
3. Follow established patterns in the codebase
4. Update documentation when adding features
5. Test thoroughly before submitting PR

---

## 📞 SUPPORT

### Documentation Issues
If you find errors or omissions in this documentation:
1. Open an issue on GitHub
2. Include the documentation file name
3. Describe the error or missing information
4. Suggest corrections if possible

### Code Questions
For code-related questions:
1. Check relevant documentation file first
2. Search existing issues
3. Ask in discussions
4. Create new issue if needed

---

*Documentation generated: 2026-01-19*
*Last verified: 2026-01-19*
*Repository: cczerp/Rebel-Operator*
