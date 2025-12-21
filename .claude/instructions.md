# Claude Code Project Instructions

## 🔒 MANDATORY: Read Contract Files First

**Before making ANY changes to this codebase**, you MUST:

1. Read `docs/GLOBAL_CONTRACT.md` in full (comprehensive rules)
2. Reference specific contracts as needed:
   - `docs/SYSTEM-CONTRACT.md` — Auth + UI deep dive
   - `docs/DATA_MODEL.md` — Database schema
   - `docs/INVENTORY_MANAGEMENT.md` — Inventory workflows
3. Verify your proposed changes comply with ALL rules
4. If there's a conflict between user request and contract: **THE CONTRACT WINS**

## Key Invariants (See Contracts for Full Details)

### Authentication (IMMUTABLE)
- **Stack**: Supabase → Flask-Login → Redis → PostgreSQL
- **Rule**: Supabase UID == Flask-Login user_id
- **Rule**: Every `getconn()` MUST have `putconn()`
- **Rule**: Use context managers: `with self._get_connection() as conn:`
- **Rule**: NEVER store connections on `self`

### UI System (IMMUTABLE)
- **Red (#DC2626)** = Primary actions only (**ONE** per page max)
- **Steel (#475569)** = Secondary actions
- **Charcoal (#1F2937)** = Utility actions (Save Draft, etc.)
- **NO** flat grey or white buttons
- All buttons MUST have material depth (elevation, shadows, edge highlights)
- Bottom nav: Home, Create, Account (3 items only)

### Data Model (IMMUTABLE)
- PostgreSQL via Supabase (NO SQLite)
- Connection pool: maxconn=2 (Render free tier)
- Storage location REQUIRED for all active listings
- Users table: UUID primary key, OAuth support
- 15-minute cooldown on cross-platform cancellations

### Navigation (IMMUTABLE)
- **Logged-in**: Home, Create, Account only
- **Account menu**: Listings, Inventory, Storage, Invoicing, Alerts, Settings, Website Credentials, Drafts, Billing, Logout
- **Landing page auth**: Render based on `current_user.is_authenticated` (server-side), NOT frontend state

## Enforcement Rules

### If You Receive a Violating Request:

1. **Identify the conflict** with specific contract section
2. **Explain the rule** being violated
3. **Propose compliant alternative** that achieves user's goal
4. **Wait for confirmation** before implementing

### Example Response:

```
❌ This conflicts with docs/GLOBAL_CONTRACT.md Section 2.2:
"Only ONE red (primary) button per page"

Alternative: Move the existing red button to a sticky position
that stays visible while scrolling. This maintains the one-button
rule while keeping it accessible.

Proceed with alternative?
```

### NEVER:
- ❌ Silently implement changes that violate contracts
- ❌ Modify contracts without explicit user approval
- ❌ Add custom button styles outside defined hierarchy
- ❌ Create multiple primary actions on same page
- ❌ Skip reading contracts before major changes
- ❌ Store database connections on instance (`self.conn`)

### ALWAYS:
- ✅ Read relevant contract section before implementation
- ✅ Use exact CSS color values from contract
- ✅ Maintain material depth on all buttons
- ✅ Use connection pool context managers
- ✅ Enforce storage location on active listings
- ✅ Follow button hierarchy: red → steel → utility

## Quick Sanity Checks

Before committing code, verify:

- [ ] No multiple red buttons on same page
- [ ] All database operations use `with self._get_connection()`
- [ ] Button styles match contract (red/steel/charcoal only)
- [ ] Bottom nav has exactly 3 items (Home, Create, Account)
- [ ] Landing page renders auth state server-side
- [ ] Storage location captured for all active listings
- [ ] No custom colors outside contract palette

## Contract Priority

**Order of Authority:**
1. `docs/GLOBAL_CONTRACT.md` (master ruleset)
2. Specific contracts (`SYSTEM-CONTRACT.md`, `DATA_MODEL.md`, etc.)
3. User requests (if they don't conflict)
4. Code comments/documentation

**The contracts are NON-NEGOTIABLE. If unclear, ask before implementing.**
