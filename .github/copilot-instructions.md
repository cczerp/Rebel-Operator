# GitHub Copilot Instructions for Resell Rebel

## 🔒 CRITICAL: Contract Enforcement

This project has **strict architectural rules** defined in contract documents.

**Before suggesting ANY code:**
1. Check if it affects auth, UI, database, or navigation
2. Verify compliance with `docs/GLOBAL_CONTRACT.md`
3. Reject suggestions that violate immutable rules

## Immutable Rules

### UI System
- **Red (#DC2626)**: Primary actions — ONE per page max
- **Steel (#475569)**: Secondary actions
- **Charcoal (#1F2937)**: Utility actions
- **Required**: Material depth on all buttons (elevation, shadows, edges)
- **Forbidden**: Flat styles, white buttons, custom colors

Navigation:
- Bottom nav: Home, Create, Account (3 items only)
- Logged-in landing: Personalized greeting + workflow entry points
- NO marketing CTAs for authenticated users

### Authentication
```python
# CORRECT
with self._get_connection() as conn:
    cursor = conn.cursor()
    # work here
    conn.commit()

# WRONG - Connection leak
conn = self.pool.getconn()
# Missing putconn()!
```

Rules:
- Supabase → Flask-Login → Redis → PostgreSQL
- Every `getconn()` needs `putconn()`
- Never store `conn` on `self`

### Database
- PostgreSQL ONLY (no SQLite suggestions)
- Connection pool maxconn=2
- Storage location REQUIRED for active listings
- UUIDs for user IDs, SERIAL for auto-increment

## Forbidden Completions

DO NOT suggest:
- Multiple red buttons on same page
- `self.conn = pool.getconn()` (connection leak)
- `btn-success` for non-primary actions
- Custom button classes outside contract
- Flat/white button styles
- Bottom nav with > 3 items
- Frontend auth state rendering

## Approved Patterns

DO suggest:
```python
# Database operations
with self._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(...)
    conn.commit()

# Primary button (red)
<button class="btn btn-success btn-lg">Post Now</button>

# Secondary button (steel)
<button class="btn btn-hero-outline">View Inventory</button>

# Utility button (charcoal)
<button class="btn btn-outline-primary">Save Draft</button>
```

## Conflict Handling

If completion would violate contract:
1. Comment why it's rejected
2. Suggest compliant alternative
3. Reference specific contract section

Example comment:
```python
# ❌ Multiple red buttons violates GLOBAL_CONTRACT.md Section 2.2
# ✅ Use steel (#475569) for secondary action
```

**The contracts are NON-NEGOTIABLE. Prioritize compliance over convenience.**
