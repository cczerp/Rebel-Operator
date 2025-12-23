# DATA MODEL — IMMUTABLE DATABASE SCHEMA

## Database Technology Stack

**PostgreSQL (Supabase) — NO SQLite**
- Primary: PostgreSQL with connection pooling
- Session storage: Redis (server-side sessions)
- User authentication: Supabase Auth + Flask-Login
- File storage: Local filesystem (data/ directory)

## Core Tables

### `users` — User Authentication & Accounts
**Purpose**: Stores all user accounts with Supabase OAuth integration

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PRIMARY KEY | Auto-generated UUID |
| `username` | TEXT | UNIQUE NOT NULL | Display name |
| `email` | TEXT | UNIQUE NOT NULL | Login email |
| `password_hash` | TEXT | NULLABLE | NULL for OAuth users |
| `supabase_uid` | TEXT | | Supabase Auth UID |
| `oauth_provider` | TEXT | | google, github, etc. |
| `is_admin` | BOOLEAN | DEFAULT FALSE | Admin access flag |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account enabled |
| `tier` | TEXT | DEFAULT 'FREE' | Subscription level |
| `notification_email` | TEXT | | Notification destination |
| `email_verified` | BOOLEAN | DEFAULT FALSE | Email confirmation |
| `verification_token` | TEXT | | Email verification |
| `reset_token` | TEXT | | Password reset |
| `reset_token_expiry` | TIMESTAMP | | Token expiration |
| `created_at` | TIMESTAMP | DEFAULT NOW | Account creation |
| `last_login` | TIMESTAMP | | Last login time |

**Invariants:**
- `supabase_uid` == Flask-Login `user_id`
- OAuth users have `password_hash` = NULL
- Every user MUST have unique email and username

---

### `listings` — Product Listings
**Purpose**: All user listings (draft, active, sold)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `listing_uuid` | TEXT | UNIQUE NOT NULL | Public UUID |
| `user_id` | UUID | FK → users.id | Owner |
| `collectible_id` | INTEGER | FK → collectibles.id | Optional link |
| `title` | TEXT | NOT NULL | Item title (max 80 chars) |
| `description` | TEXT | | Full description |
| `price` | REAL | NOT NULL | Sale price |
| `cost` | REAL | | Cost basis |
| `condition` | TEXT | | new, like_new, excellent, good, fair, poor |
| `category` | TEXT | | Item category |
| `item_type` | TEXT | | general, clothing, electronics, trading_card, collectible, etc. |
| `attributes` | TEXT | JSON | Additional attributes |
| `photos` | TEXT | JSON array | Photo paths |
| `quantity` | INTEGER | DEFAULT 1 | Available quantity |
| `storage_location` | TEXT | | Physical location (B1, C2, Shelf-3) |
| `sku` | TEXT | | Custom SKU |
| `upc` | TEXT | | UPC/barcode |
| `status` | TEXT | DEFAULT 'draft' | draft, active, sold, canceled |
| `sold_platform` | TEXT | | Platform where sold |
| `sold_date` | TIMESTAMP | | Sale timestamp |
| `sold_price` | REAL | | Actual sale price |
| `platform_statuses` | TEXT | JSON | Per-platform status |
| `created_at` | TIMESTAMP | DEFAULT NOW | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW | Last modified |

**Invariants:**
- `quantity` >= 0
- If `status` = 'sold', `sold_platform`, `sold_date`, `sold_price` must be set
- `storage_location` REQUIRED for all active listings

---

### `platform_listings` — Multi-Platform Tracking
**Purpose**: Tracks each listing on each platform

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `listing_id` | INTEGER | FK → listings.id | Parent listing |
| `platform` | TEXT | NOT NULL | poshmark, ebay, etsy, etc. |
| `platform_listing_id` | TEXT | | External platform ID |
| `platform_url` | TEXT | | Direct link |
| `status` | TEXT | DEFAULT 'pending' | pending, active, sold, failed, canceled, pending_cancel |
| `posted_at` | TIMESTAMP | | When posted |
| `last_synced` | TIMESTAMP | | Last sync time |
| `cancel_scheduled_at` | TIMESTAMP | | Auto-cancel time (15-min cooldown) |
| `error_message` | TEXT | | Last error |
| `retry_count` | INTEGER | DEFAULT 0 | Retry attempts |

**Constraints:**
- UNIQUE(listing_id, platform) — one record per platform per listing

**Invariants:**
- When listing sells, cancel_scheduled_at = sold_time + 15 minutes
- Status transitions: pending → active → sold/canceled

---

### `marketplace_credentials` — Platform API Keys
**Purpose**: Stores user credentials for each marketplace

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | UUID | FK → users.id | Owner |
| `platform` | TEXT | NOT NULL | Platform name |
| `username` | TEXT | | Platform username |
| `password` | TEXT | | Encrypted password |
| `created_at` | TIMESTAMP | DEFAULT NOW | |
| `updated_at` | TIMESTAMP | DEFAULT NOW | |

**Constraints:**
- UNIQUE(user_id, platform) — one credential set per platform per user

---

### `card_collections` — Trading Card Storage
**Purpose**: Specialized storage for TCG and sports cards

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | UUID | FK → users.id | Owner |
| `card_uuid` | TEXT | UNIQUE NOT NULL | Public UUID |
| `card_type` | TEXT | NOT NULL | tcg, sports |
| `title` | TEXT | NOT NULL | Card name |
| `card_number` | TEXT | | Card # in set |
| `quantity` | INTEGER | DEFAULT 1 | How many owned |
| `organization_mode` | TEXT | | by_set, by_value, by_player, custom |
| `primary_category` | TEXT | | Primary org category |
| `custom_categories` | TEXT | JSON | User-defined tags |
| `storage_location` | TEXT | | Physical location |
| `storage_item_id` | INTEGER | FK → storage_items.id | Storage link |
| `game_name` | TEXT | | MTG, Pokemon, etc. |
| `set_name` | TEXT | | Set name |
| `set_code` | TEXT | | Set code |
| `set_symbol` | TEXT | | Set symbol URL |
| `rarity` | TEXT | | common, uncommon, rare, mythic, etc. |
| `card_subtype` | TEXT | | Foil, reverse, etc. |
| `format_legality` | TEXT | JSON | Legal formats |
| `sport` | TEXT | | baseball, basketball, etc. |
| `year` | INTEGER | | Card year |
| `brand` | TEXT | | Topps, Panini, etc. |
| `series` | TEXT | | Series name |
| `player_name` | TEXT | | Athlete name |
| `team` | TEXT | | Team name |
| `is_rookie_card` | BOOLEAN | DEFAULT FALSE | Rookie card flag |
| `parallel_color` | TEXT | | Parallel variant |
| `insert_series` | TEXT | | Insert set |
| `grading_company` | TEXT | | PSA, BGS, CGC, etc. |
| `grading_score` | REAL | | Grade (1-10) |
| `grading_serial` | TEXT | | Cert number |
| `estimated_value` | REAL | | Market value |
| `value_tier` | TEXT | | low, mid, high, grail |
| `purchase_price` | REAL | | Cost basis |
| `photos` | TEXT | JSON | Photo paths |
| `notes` | TEXT | | User notes |
| `ai_identified` | BOOLEAN | DEFAULT FALSE | AI detected |
| `ai_confidence` | REAL | | AI confidence |
| `created_at` | TIMESTAMP | DEFAULT NOW | |
| `updated_at` | TIMESTAMP | DEFAULT NOW | |

---

### `storage_bins` — Physical Storage Containers
**Purpose**: Physical bins/boxes for inventory organization

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | UUID | FK → users.id | Owner |
| `bin_name` | TEXT | NOT NULL | Bin label (A, B, C) |
| `bin_type` | TEXT | NOT NULL | clothing, cards |
| `description` | TEXT | | Optional notes |
| `created_at` | TIMESTAMP | DEFAULT NOW | |

**Constraints:**
- UNIQUE(user_id, bin_name, bin_type)

---

### `storage_sections` — Bin Compartments
**Purpose**: Sections/dividers within storage bins

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `bin_id` | INTEGER | FK → storage_bins.id | Parent bin |
| `section_name` | TEXT | NOT NULL | Section label (1, 2, 3) |
| `capacity` | INTEGER | | Max items |
| `item_count` | INTEGER | DEFAULT 0 | Current count |
| `created_at` | TIMESTAMP | DEFAULT NOW | |

**Constraints:**
- UNIQUE(bin_id, section_name)

---

### `storage_items` — Individual Stored Items
**Purpose**: Track specific items in storage bins

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | UUID | FK → users.id | Owner |
| `storage_id` | TEXT | UNIQUE NOT NULL | Unique storage ID |
| `bin_id` | INTEGER | FK → storage_bins.id | Bin location |
| `section_id` | INTEGER | FK → storage_sections.id | Section location |
| `item_type` | TEXT | | Item category |
| `category` | TEXT | | Subcategory |
| `title` | TEXT | | Item name |
| `description` | TEXT | | Notes |
| `quantity` | INTEGER | DEFAULT 1 | Quantity |
| `photos` | TEXT | JSON | Photos |
| `notes` | TEXT | | User notes |
| `listing_id` | INTEGER | FK → listings.id | Linked listing |
| `created_at` | TIMESTAMP | DEFAULT NOW | |
| `updated_at` | TIMESTAMP | DEFAULT NOW | |

---

### `notifications` — System Alerts
**Purpose**: Sales, errors, and activity notifications

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `type` | TEXT | NOT NULL | sale, error, warning, info |
| `listing_id` | INTEGER | FK → listings.id | Related listing |
| `platform` | TEXT | | Source platform |
| `title` | TEXT | NOT NULL | Notification title |
| `message` | TEXT | | Full message |
| `data` | TEXT | JSON | Additional data |
| `is_read` | BOOLEAN | DEFAULT FALSE | Read status |
| `sent_email` | BOOLEAN | DEFAULT FALSE | Email sent |
| `created_at` | TIMESTAMP | DEFAULT NOW | |

---

### `activity_logs` — Audit Trail
**Purpose**: Track all user actions for security and debugging

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | UUID | FK → users.id | User who acted |
| `action` | TEXT | NOT NULL | login, create_listing, delete, etc. |
| `resource_type` | TEXT | | listing, user, etc. |
| `resource_id` | INTEGER | | ID of resource |
| `details` | TEXT | JSON | Action details |
| `ip_address` | TEXT | | User IP |
| `user_agent` | TEXT | | Browser info |
| `created_at` | TIMESTAMP | DEFAULT NOW | |

---

## Connection Pooling Rules

**CRITICAL INVARIANTS:**

1. **Every `getconn()` MUST have `putconn()`**
   - Use context managers: `with self._get_connection() as conn:`
   - Never store connections on `self`
   - Connection leaks = Supabase pool exhaustion

2. **Pool Configuration**
   - Min connections: 1
   - Max connections: 2 (Render free tier: 512 MB RAM)
   - Connection timeout: 5 seconds
   - Statement timeout: 10 seconds

3. **Thread Safety**
   - Use ThreadedConnectionPool
   - Never share connections between threads
   - Each request gets its own connection from pool

4. **Error Handling**
   ```python
   try:
       with self._get_connection() as conn:
           cursor = conn.cursor()
           # ... do work
           conn.commit()
   except Exception as e:
       # Connection automatically returned to pool
       raise
   ```

**If connection pool rules are violated, expect:**
- Database deadlocks
- "connection pool exhausted" errors
- Request timeouts
- Data inconsistency

---

## Indexes for Performance

```sql
-- User lookups
CREATE INDEX idx_users_is_admin ON users(is_admin);

-- Listing queries
CREATE INDEX idx_listings_uuid ON listings(listing_uuid);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_user_id ON listings(user_id);

-- Platform tracking
CREATE INDEX idx_platform_listings_status ON platform_listings(status);

-- Card collection queries
CREATE INDEX idx_card_collections_user ON card_collections(user_id, created_at DESC);
CREATE INDEX idx_card_collections_type ON card_collections(card_type);
CREATE INDEX idx_card_collections_org_mode ON card_collections(organization_mode, primary_category);
CREATE INDEX idx_card_collections_set ON card_collections(set_code, card_number);
CREATE INDEX idx_card_collections_sport_year ON card_collections(sport, year, brand);

-- Storage queries
CREATE INDEX idx_storage_items_user ON storage_items(user_id, created_at DESC);
CREATE INDEX idx_storage_items_bin_section ON storage_items(bin_id, section_id);
CREATE INDEX idx_storage_items_storage_id ON storage_items(storage_id);

-- Notification queries
CREATE INDEX idx_notifications_unread ON notifications(is_read);
CREATE INDEX idx_platform_activity_user_unread ON platform_activity(user_id, is_read, created_at DESC);

-- Activity logs
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);

-- Training data
CREATE INDEX idx_training_data_created ON training_data(created_at DESC);
```

---

## Migration Rules

**Before modifying schema:**

1. Check if column exists:
   ```sql
   SELECT column_name FROM information_schema.columns
   WHERE table_name='table' AND column_name='column'
   ```

2. Use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`

3. Never drop columns without user data backup

4. Test migrations on local database first

**If schema changes violate data model contract:**
- Data corruption is expected
- Multi-tenant isolation may break
- Connection pool issues may occur

---

## Enforcement

This data model is **IMMUTABLE**. Before modifying any table schema or connection handling:

1. Verify change complies with this contract
2. If conflict exists: **THE CONTRACT WINS**
3. Propose alternative that maintains invariants
4. Get explicit approval before proceeding

**No exceptions.**
