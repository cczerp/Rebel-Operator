# Features & Capabilities
## Comprehensive Feature List - Rebel Operator / AI Cross-Poster

This document provides a complete inventory of all features and capabilities in the Rebel Operator / AI Cross-Poster application, organized by functional category.

---

## 🎯 1. CORE LISTING FEATURES

### Listing Creation & Management
| Feature | Description |
|---------|-------------|
| **Manual Listing Creation** | Create listings manually with full control over all fields (title, description, price, condition, SKU, category) |
| **AI-Powered Photo Analysis** | Upload photos and let AI (Claude/GPT-4) auto-generate title, description, condition, and attributes |
| **Draft Management** | Save listings as drafts before publishing; edit, update, or delete drafts anytime |
| **Bulk Draft Operations** | Select multiple drafts to delete, edit, or publish simultaneously |
| **Listing Preview** | Preview how your listing will appear on different platforms before posting |
| **Multi-Photo Support** | Upload 5-20 photos per listing (platform-dependent limits) |
| **Post Queue Management** | Queue listings for scheduled posting across platforms |
| **Batch Listing Creation** | Create multiple listings efficiently in one operation |
| **Editable Drafts** | Full edit capabilities for draft listings before publication |
| **SKU Management** | Auto-generate or manually assign SKUs for inventory tracking |
| **Category Selection** | Choose from platform-specific categories or auto-suggest via AI |
| **Condition Assessment** | Rate items from "New" to "For Parts" with platform-specific mappings |
| **Price Management** | Set prices with optional compare-at pricing for discounts |
| **Shipping Configuration** | Configure shipping costs, methods, and handling times |

---

## 🌐 2. PLATFORM INTEGRATIONS (17 Platforms)

### API-Based Direct Publishing (7 Platforms)
| Platform | Integration Type | Status | Key Features |
|----------|------------------|--------|--------------|
| **eBay** | Full Sell API | ✅ Production | Direct posting, inventory sync, offer management |
| **Etsy** | Official API v3 | ✅ Production | Shop integration, listing management |
| **Shopify** | Store API | ✅ Production | Inventory sync, product management |
| **WooCommerce** | WordPress Plugin API | ✅ Production | Store integration, order sync |
| **Depop** | Official API | ⚠️ Pending approval | Fashion marketplace integration |
| **Square** | POS API | ✅ Production | Point-of-sale inventory sync |
| **Pinterest** | Pins API | ✅ Production | Product pins for discovery |

### CSV Export Integrations (5 Platforms)
| Platform | Integration Type | Status | Key Features |
|----------|------------------|--------|--------------|
| **Poshmark** | CSV Export | ✅ Production | Formatted CSV for bulk import |
| **Bonanza** | CSV Export | ✅ Production | Auction listing format |
| **Ecrater** | CSV Export | ✅ Production | Small business marketplace format |
| **Ruby Lane** | CSV Export | ✅ Production | Vintage/antique booth rental format |
| **OfferUp** | CSV Export | ✅ Production | Mobile marketplace export |

### Feed/Catalog Integrations (2 Platforms)
| Platform | Integration Type | Status | Key Features |
|----------|------------------|--------|--------------|
| **Facebook Shops** | Product Feed | ✅ Production | Catalog feed upload, auto-sync |
| **Google Shopping** | Merchant Feed | ✅ Production | Shopping feed generation and submission |

### Template/Manual Integrations (3 Platforms)
| Platform | Integration Type | Status | Key Features |
|----------|------------------|--------|--------------|
| **Craigslist** | Template Generation | ✅ Production | Pre-filled templates for manual posting |
| **Nextdoor** | Template Generation | ✅ Production | Hyperlocal marketplace templates |
| **Chairish** | Template Generation | ✅ Production | Furniture/home goods format |

### Platform Management Features
- **Multi-Platform Publishing** - Send one listing to all platforms simultaneously
- **Selective Publishing** - Choose specific platforms per listing
- **Platform Status Tracking** - Monitor where each listing is posted
- **Credential Management** - Securely store API keys and login credentials per platform
- **Connection Testing** - Validate platform connections before publishing
- **Auto-Cancel on Sale** - Remove listing from all platforms when sold on one
- **Platform Format Adaptation** - Auto-convert listings to meet each platform's requirements
- **Rate Limiting** - Respect platform API rate limits to avoid bans
- **Failed Post Retry** - Automatic retry logic (up to 3 attempts) for failed postings

---

## 🤖 3. AI CAPABILITIES

### AI Provider Strategy (Cost-Optimized)
| Provider | Model | Use Case | Cost per Analysis |
|----------|-------|----------|-------------------|
| **Claude (Anthropic)** | Claude 3.5 Sonnet | Primary analyzer (~90% success) | ~$0.01-0.02 |
| **GPT-4 (OpenAI)** | GPT-4 Vision | Fallback analyzer (only when Claude fails) | ~$0.01-0.03 |
| **Gemini (Google)** | Gemini 1.5 Pro | Collectible classification | ~$0.005-0.01 |

### AI Analysis Features
| Feature | Description |
|---------|-------------|
| **Item Identification** | Automatically classify items by type (clothing, electronics, cards, collectibles, etc.) |
| **Brand Detection** | Extract brand names from logos, labels, and visual cues |
| **Attribute Extraction** | Detect size, color, material, model number, year |
| **Condition Assessment** | AI rates condition (new/excellent/good/fair/poor) based on visible wear |
| **Market Value Estimation** | AI suggests optimal pricing based on market knowledge |
| **Description Generation** | Create compelling, SEO-optimized product descriptions |
| **Keyword Generation** | Auto-suggest search terms and tags for maximum visibility |
| **Title Optimization** | Generate titles optimized for each platform's search algorithm |
| **Category Suggestion** | Recommend appropriate categories based on item analysis |
| **Fallback Strategy** | Automatically use GPT-4 Vision if Claude's analysis is incomplete |
| **Cost Optimization** | Only use expensive models when cheaper ones fail (~90% cost savings) |

### Collectible-Specific AI
| Feature | Description |
|---------|-------------|
| **Trading Card Recognition** | Identify Pokemon, Magic: The Gathering, Yu-Gi-Oh, Sports cards |
| **Set & Edition Detection** | Determine card set, edition, and print year |
| **Rarity Classification** | Detect rarity (common, uncommon, rare, holographic, etc.) |
| **Grading Suggestion** | Estimate PSA/BGS grade based on visible condition |
| **Coin Identification** | Identify coins by country, denomination, year, mint mark |
| **Collectible Valuation** | Market price estimates for collectibles |
| **Authentication Assessment** | Flag potential counterfeits or reproductions |

---

## 📸 4. STORAGE & PHOTO MANAGEMENT

### Photo Upload & Processing
| Feature | Description |
|---------|-------------|
| **Multi-Photo Upload** | Upload 5-20 photos per listing (platform-dependent) |
| **Format Support** | PNG, JPG, JPEG, GIF, WEBP, HEIC formats supported |
| **Automatic Compression** | Optimize images to reduce file size (JPEG, quality 85, max 2MB) |
| **Image Resizing** | Auto-resize to max 2048px on longest side |
| **Format Conversion** | Convert RGBA/HEIC to RGB/JPEG automatically |
| **Photo Editing API** | Basic editing (crop, rotate, filter) |
| **Drag-and-Drop Upload** | Easy drag-drop interface for photo uploads |
| **Progress Tracking** | Real-time upload progress indicators |
| **Temporary Photo Cleanup** | Auto-delete temporary files after processing |
| **Photo Reordering** | Drag to reorder photos; set primary photo |
| **Bulk Photo Upload** | Upload entire folders of product photos |

### Cloud Storage Integration
| Feature | Description |
|---------|-------------|
| **Supabase Storage** | Cloud storage with row-level security policies |
| **Cloudinary Support** | Optional CDN integration for image delivery |
| **Local Storage Fallback** | On-premise photo storage option for privacy |
| **URL Management** | Generate and track photo URLs across platforms |
| **Secure Access** | Pre-signed URLs with expiration for security |
| **Storage Buckets** | Organize photos in buckets (drafts, published, archive) |

### Photo Organization
| Feature | Description |
|---------|-------------|
| **Hall of Records** | Curated photo gallery showcasing best-performing items |
| **Photo Curation Dashboard** | Admin tool to approve/reject photos for public gallery |
| **Photo Selection Tool** | Choose best photos for artifact display |
| **Temporary Staging** | Hold photos before final listing publication |
| **Archive Management** | Move sold item photos to archive automatically |

---

## 🃏 5. CARD & COLLECTIBLE MANAGEMENT

### Trading Card Support
| Card Type | Features |
|-----------|----------|
| **Pokemon TCG** | Set detection, rarity classification, holographic identification |
| **Magic: The Gathering** | Card name, set, rarity, mana cost, card type recognition |
| **Yu-Gi-Oh** | Card name, type (monster/spell/trap), rarity detection |
| **Sports Cards** | Player identification, team, year, card number, manufacturer |
| **NBA/NFL/MLB/NHL** | League-specific player and team recognition |

### Card Collection Features
| Feature | Description |
|---------|-------------|
| **Unified Card Schema** | Single data structure for all card types |
| **Card Import** | Import existing collections via CSV |
| **Card Export** | Export collection to CSV for backup/sharing |
| **Full-Text Search** | Search across all card fields (name, set, player, etc.) |
| **Collection Statistics** | Total cards, total value, rarity breakdown |
| **Value Tracking** | Track market value changes over time |
| **Grading Management** | Track PSA/BGS grades for graded cards |

### Collection Organization Modes
| Mode | Description |
|------|-------------|
| **By Franchise** | Group by Pokemon, MTG, Yu-Gi-Oh, Sports, etc. |
| **By Game** | Organize by card game type |
| **By Rarity** | Sort by common/uncommon/rare/ultra-rare/secret |
| **By Value Tier** | Group into low/medium/high value buckets |
| **By Storage Location** | Track physical storage location per card |
| **By Set/Year** | Organize chronologically by set release |

### Coin Collection
| Feature | Description |
|---------|-------------|
| **Coin Vault** | Dedicated vault for coin/currency collection |
| **Coin Identification** | Country, denomination, year, mint mark detection |
| **Coin Statistics** | Total coins, total value, rarity metrics |
| **Grading Support** | Track PCGS/NGC grades |

### Storage Maps (for Cards)
| Region | Description |
|--------|-------------|
| **North Region** | Top section - High-value cards |
| **South Region** | Bottom section - Bulk commons |
| **East Region** | Right section - Mid-value cards |
| **West Region** | Left section - Sets in progress |
| **Center Region** | Middle section - Currently active cards |

---

## 📦 6. PHYSICAL STORAGE MANAGEMENT

### Storage System Features
| Feature | Description |
|---------|-------------|
| **Storage Bins** | Create and manage physical storage containers |
| **Storage Sections** | Organize bins into labeled sections (shelf 1, drawer 2, etc.) |
| **Storage Mapping** | Visual map of storage locations with instructions |
| **Item Tracking** | Log items in specific storage locations with "storage IDs" |
| **Location Finder** | Search database to find where specific items are stored |
| **Storage Instructions** | User guide for organizing and maintaining storage system |
| **Bulk Assignment** | Assign multiple items to storage locations at once |
| **Storage Suggestions** | AI suggests optimal storage location based on item type |

### Storage Types
| Type | Description |
|------|-------------|
| **Card Storage** | Dedicated organization for card collections |
| **Clothing Storage** | Wardrobe inventory management by size/type |
| **General Inventory** | Multi-purpose item storage tracking |

### Storage Management Tools
| Tool | Description |
|------|-------------|
| **Location Search** | Find items by storage location |
| **Item Search** | Find storage location by item name/SKU |
| **Capacity Tracking** | Monitor how full each storage location is |
| **Low Stock Alerts** | Notify when storage location is running low |

---

## 👤 7. USER MANAGEMENT & AUTHENTICATION

### Authentication Methods
| Method | Description | Status |
|--------|-------------|--------|
| **Email/Password** | Standard account creation with email verification | ✅ Active |
| **Google Sign-In** | OAuth 2.0 integration for Google accounts | ✅ Active |
| **Password Reset** | Forgot password with time-limited token | ✅ Active |
| **Remember Me** | Long-lived session tokens (7 days) | ✅ Active |

### User Features
| Feature | Description |
|---------|-------------|
| **User Registration** | Create new account with email verification |
| **Email Verification** | Token-based email confirmation on signup |
| **Login/Logout** | Session-based authentication with secure cookies |
| **Session Management** | Track active user sessions |
| **Account Settings** | Update email, password, notification preferences |
| **User Activity Tracking** | Log all user actions for audit trail |
| **Last Login Tracking** | Track user activity frequency |

### User Tiers (Framework Ready)
| Tier | Description | Status |
|------|-------------|--------|
| **FREE** | 8 free AI analyses as guest, limited features | ✅ Active |
| **PRO** | Unlimited AI, advanced features | 🔧 Framework ready |
| **ELITE** | All features, priority support | 🔧 Framework ready |

### Security Features
| Feature | Description |
|---------|-------------|
| **Secure Cookies** | HTTPONLY, SAMESITE=Lax, Secure (HTTPS only in production) |
| **Password Hashing** | Werkzeug security with bcrypt-level hashing |
| **Session Expiration** | 7-day session lifetime (configurable) |
| **CSRF Protection** | Built-in Flask CSRF protection |
| **XSS Protection** | Content Security Policy headers |
| **SQL Injection Prevention** | Parameterized queries throughout |
| **Rate Limiting** | Prevent brute-force attacks (framework ready) |

---

## 👑 8. ADMIN FEATURES

### Admin Dashboard
| Feature | Description |
|---------|-------------|
| **System Statistics** | Total users, listings, drafts, sales, revenue |
| **User Overview** | Quick stats on user activity and growth |
| **Platform Health** | Monitor API connection status for all platforms |
| **Recent Activity** | Real-time feed of all user actions |

### User Management
| Feature | Description |
|---------|-------------|
| **User List** | View all users with filtering (active/inactive/admin) |
| **User Details** | Individual user profile with complete activity history |
| **Activate/Deactivate** | Toggle user account status |
| **Grant/Revoke Admin** | Promote users to admin or demote |
| **Delete User** | Remove user account and all associated data |
| **User Search** | Search users by username, email, or ID |
| **Activity Logs** | View detailed logs of all user actions |

### Content Management
| Feature | Description |
|---------|-------------|
| **Photo Curation** | Review and approve photos for Hall of Records |
| **Hall of Photos** | Manage public artifact photo gallery |
| **Photo Selection Toggle** | Include/exclude photos from main gallery |
| **Artifact Review** | Approve or reject user-submitted artifacts |

### Admin Tools
| Feature | Description |
|---------|-------------|
| **Debug Tools** | User data inspection and debugging interface |
| **Database Console** | Execute SQL queries for advanced operations |
| **Activity Monitoring** | Real-time monitoring of all system activity |
| **Bulk Operations** | Mass user updates, deletions, or notifications |

---

## 📤 9. EXPORT & IMPORT FEATURES

### Export Capabilities
| Feature | Description |
|---------|-------------|
| **CSV Export** | Export listings/drafts to standard CSV format |
| **Multi-Platform Export** | Generate platform-specific CSV formats |
| **Bulk Export** | Export entire collection in one operation |
| **Card Collection Export** | Export card collection as CSV |
| **Inventory Export** | Download complete inventory as spreadsheet |
| **Training Data Export** | Export AI analysis results for model training (JSONL) |
| **Export Preview** | Preview export format before downloading |
| **Selective Export** | Export only selected items |

### Platform-Specific Exporters
| Platform | Format | Fields |
|----------|--------|--------|
| **Poshmark** | CSV | Title, description, price, brand, size, category, photos |
| **Bonanza** | CSV | SKU, title, description, price, quantity, category |
| **Ruby Lane** | CSV | Title, price, condition, category, vintage year |
| **Ecrater** | CSV | Product name, price, quantity, weight, category |
| **Google Shopping** | XML/CSV | GTIN, title, description, price, link, image_link |
| **Generic CSV** | CSV | All fields in universal format |

### Import Capabilities
| Feature | Description |
|---------|-------------|
| **CSV Import** | Import existing listings from spreadsheet |
| **Card Collection Import** | Import card collections from other software |
| **Batch Import** | Upload hundreds of items via single CSV |
| **Format Validation** | Validate imported data before processing |
| **Error Reporting** | Report issues with import rows (missing fields, invalid data) |
| **Auto-Mapping** | Intelligently map CSV columns to database fields |
| **Duplicate Detection** | Warn about potential duplicate SKUs |

---

## 💰 10. BILLING & SUBSCRIPTION (Framework Ready)

### Subscription Management
| Feature | Description | Status |
|---------|-------------|--------|
| **Stripe Integration** | Payment processing via Stripe Checkout | 🔧 Framework ready |
| **Subscription Plans** | FREE, PRO, ELITE tiers | 🔧 Framework ready |
| **Feature Gating** | Restrict features by subscription tier | 🔧 Framework ready |
| **Checkout Sessions** | Create Stripe payment sessions | 🔧 Framework ready |
| **Cancel Subscription** | User-initiated cancellation | 🔧 Framework ready |
| **Webhook Handling** | Process Stripe webhooks for events | 🔧 Framework ready |
| **Usage Tracking** | Monitor API usage per user | 🔧 Framework ready |
| **Billing History** | View past invoices and payments | 🔧 Framework ready |

---

## 🔔 11. NOTIFICATIONS & ALERTS

### Email Notifications
| Notification Type | Description |
|-------------------|-------------|
| **Sale Notifications** | Alert when item sells (with price, platform, buyer) |
| **Offer Notifications** | When buyers make offers on listings |
| **Listing Failure Alerts** | When posting fails on a platform (with error details) |
| **Price Drop Alerts** | Custom alerts for collectibles hitting target prices |
| **Low Inventory Alerts** | Notify when item quantity drops below threshold |
| **Shipping Labels** | Auto-attach shipping labels to sale emails |

### In-App Notifications
| Feature | Description |
|---------|-------------|
| **Notification Center** | Centralized notification feed in app |
| **Unread Counter** | Badge showing unread notification count |
| **Mark as Read** | Mark individual or all notifications as read |
| **Notification History** | Full archive of all notifications |
| **Real-Time Alerts** | Immediate notifications via WebSocket (framework ready) |
| **Notification Preferences** | Configure which notifications to receive |

### Notification Database
| Feature | Description |
|---------|-------------|
| **Persistent Storage** | All notifications stored in PostgreSQL |
| **User Association** | Link notifications to specific users |
| **Timestamp Tracking** | Created and read timestamps |
| **Notification Types** | Sale, offer, error, info, warning types |

---

## ⚙️ 12. SETTINGS & CREDENTIALS

### User Settings
| Setting | Description |
|---------|-------------|
| **Notification Email** | Configure email address for notifications |
| **Default Platform** | Set preferred platform for publishing |
| **Auto-Enhance** | Enable/disable automatic AI enhancement |
| **Photo Compression** | Configure image quality settings |
| **Default Shipping** | Set default shipping method and cost |

### Credential Management
| Feature | Description |
|---------|-------------|
| **API Credentials** | Store API keys for platforms (eBay, Etsy, etc.) |
| **Marketplace Credentials** | Save username/password for non-API platforms |
| **Secure Storage** | Encrypted credential storage in database |
| **Credential Validation** | Test credentials before saving |
| **Credential Deletion** | Remove saved credentials securely |
| **Multiple Accounts** | Support for multiple accounts per platform |
| **Credential Testing** | Validate connection before saving |

---

## 🔄 13. CROSS-PLATFORM PUBLISHING

### Publishing Features
| Feature | Description |
|---------|-------------|
| **Publish to All** | Send one listing to all configured platforms simultaneously |
| **Selective Publishing** | Choose specific platforms per listing |
| **Platform Adaptation** | Auto-convert listing to each platform's format |
| **Status Tracking** | Monitor where each listing is posted |
| **Failed Post Recovery** | Automatic retry for failed postings (up to 3 attempts) |
| **Success Rate Tracking** | Monitor publishing success rates per platform |

### Sync Features
| Feature | Description |
|---------|-------------|
| **Auto-Cancel on Sale** | Remove listing from all platforms when sold on one |
| **Price Sync** | Update price across all platforms |
| **Inventory Sync** | Sync quantity across platforms |
| **Status Sync** | Sync active/inactive status |
| **Sales Sync** | Pull sales data from all platforms |
| **Sync Logging** | Full audit trail of all sync operations |

### Publishing Workflow
```
Create Listing → AI Enhancement → Save as Draft → 
Select Platforms → Publish → Monitor Status → Handle Sales
```

---

## 🛒 14. SHOPPING MODE & MARKET ANALYSIS

### Shopping Features
| Feature | Description |
|---------|-------------|
| **Quick Lookup** | Search collectible database while shopping in-store |
| **Profit Calculator** | Calculate profit margin before buying |
| **Price Comparison** | Compare asking price vs. market value |
| **Buy Recommendation** | Get AI buy/pass/wait recommendations |
| **Trend Analysis** | Track price trends for collectibles |
| **High-Value Detection** | Identify valuable items at thrift stores/auctions |

### Market Data
| Feature | Description |
|---------|-------------|
| **Price History** | Track historical pricing for items |
| **Trending Items** | See what's popular in market |
| **Collection Statistics** | Total value, average price, rarity metrics |
| **Comps Database** | Recently sold comparables for pricing |

---

## 🧠 15. KNOWLEDGE DISTILLATION & AI TRAINING

### Machine Learning Features
| Feature | Description |
|---------|-------------|
| **Training Data Collection** | Save AI analysis results for model training |
| **Student Model Support** | Train lightweight "baby bird" classifiers |
| **Teacher/Student Routing** | Smart decision on which model to use |
| **Training Data Export** | Generate JSONL datasets for fine-tuning |
| **Sample Collection** | Collect successful predictions for training |
| **Model Performance Tracking** | Monitor accuracy of different models |

---

## 🔌 16. INTEGRATIONS & EXTERNAL SERVICES

### Database & Storage
| Service | Purpose | Status |
|---------|---------|--------|
| **Supabase PostgreSQL** | Primary database with RLS | ✅ Active |
| **Cloudinary** | Optional CDN for images | ✅ Active |
| **Local Storage** | File system storage fallback | ✅ Active |

### External Services
| Service | Purpose | Status |
|---------|---------|--------|
| **SMTP Email** | Outbound email for notifications | ✅ Active |
| **Google OAuth** | Third-party authentication | ✅ Active |
| **Stripe** | Payment processing | 🔧 Framework ready |

### Monitoring & Health
| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/health/ready` | Readiness probe (checks database) |
| `/health/live` | Liveness probe |

---

## 🎁 17. UNIQUE CAPABILITIES

### Specialized Tools
| Feature | Description |
|---------|-------------|
| **Collectible Artifacts** | Store recognized items in public database |
| **Save to Collection** | Users can save items from public database |
| **Unified Listing Schema** | One data structure for all platforms |
| **Cost-Optimized AI** | Strategic use of free/cheap models |
| **Hall of Records** | Public gallery of best collectibles |
| **Guest Mode** | 8 free AI analyses without signup |
| **Mobile App Support** | Backend API for mobile clients |
| **GUI Application** | Desktop app with tabs and UI |
| **CLI Interface** | Command-line menu-driven interface |

### Advanced Features
| Feature | Description |
|---------|-------------|
| **Pre-Listing Validation** | Check listings against platform requirements |
| **SEO Optimization** | Auto-generate keywords and optimize titles |
| **Field Mapping** | Transform data between platforms automatically |
| **Compliance Checking** | Ensure listings meet platform ToS |
| **Rate Limiting** | Respect platform API rate limits |
| **Connection Pooling** | Database connection management for high concurrency |
| **Error Recovery** | Automatic retry and fallback strategies |

---

## 📊 SUMMARY STATISTICS

### Platform Support: **17 Platforms**
- **7** API-based (direct publishing)
- **5** CSV export
- **2** Feed/catalog
- **3** Template/manual

### AI Providers: **3 Providers**
- **Claude 3.5 Sonnet** (Anthropic) - Primary
- **GPT-4 Vision** (OpenAI) - Fallback
- **Gemini 1.5 Pro** (Google) - Collectibles

### Pages: **33 HTML Pages**
- 15 main pages
- 6 admin pages
- 4 auth pages
- 8 specialized pages

### API Endpoints: **120+ Endpoints**
- 80+ in routes_main.py
- 16+ in routes_cards.py
- 11+ in routes_csv.py
- 9+ in routes_admin.py + routes_auth.py

### Total Features: **100+ Features**
Organized across 17 functional categories

---

*Last Updated: 2026-01-19*
*Generated from codebase analysis of Rebel-Operator repository*
