# SYSTEM CONTRACT — AUTH + UI

## AUTHENTICATION (IMMUTABLE)

- Supabase authenticates users (credentials + OAuth only)
- Flask-Login owns session state
- Redis stores sessions server-side
- PostgreSQL stores user data only
- Browser cookies store session ID only

### Invariants
- Supabase UID == Flask-Login user_id
- login_user(user) MUST be called after auth
- user_loader MUST fetch user from DB
- Every DB getconn() MUST have putconn()
- If user_loader fails, user is treated as logged out
- No DB connections stored on self

If any invariant is violated, login instability is expected.

## UI SYSTEM (IMMUTABLE)

### Brand Color Hierarchy (DO NOT DEVIATE)

**Red = primary brand + primary actions only**
- Hex: #DC2626 (--red-primary)
- Dark: #991B1B (--red-primary-dark)
- Light: #EF4444 (--red-primary-light)

**Charcoal = foundational background / app canvas**
- Hex: #1F2937 (--charcoal)
- Light: #374151 (--charcoal-light)
- Dark: #111827 (--charcoal-dark)

**Steel blue-grey = functional UI surfaces and secondary actions**
- Hex: #475569 (--steel-blue-grey)
- Light: #64748B (--steel-blue-grey-light)
- Dark: #334155 (--steel-blue-grey-dark)

**Off-white = accent only (text, icons, outlines), never a surface**
- Hex: #F9FAFB (--off-white)
- Text: #E5E7EB (--off-white-text)

These are roles, not suggestions.

### Button Rules (Global)

**No button may be flat grey or solid white.**

**No page may invent a new button style.**

**All buttons must feel like materials (depth, elevation, interaction), not flat fills.**

#### Button Tiers:

1. **Primary action → red** (only one per page)
   - Material depth with elevation
   - Edge highlights
   - Hover: brighter, higher shadow
   - Active: darker, compressed

2. **Secondary action → steel blue-grey**
   - Lower elevation than primary
   - Subtle material depth
   - Hover: brighter material, subtle lift
   - Active: darker, compressed

3. **Utility action (Save Draft, etc.) → dark steel / charcoal surface with subtle edge highlight**
   - Minimal elevation
   - Charcoal gradient background
   - Subtle edge highlight
   - Hover: slightly elevated
   - Active: darker, compressed

**Hover and active states must change material feel (light, depth), not just color.**

### Layout Rules (Global)

- **The landing page is the only page allowed to show multiple workflow entry buttons.**
- **Logged-out landing page: marketing CTAs only.**
- **Logged-in landing page: Create Listing (primary), Inventory, Storage (secondary).**
- **Create page is a focused work page: AI actions + Save Draft only.**
- **Inventory / Storage navigation lives under Account or global nav, not scattered.**

### Consistency Requirement

- Color usage, button hierarchy, spacing, and elevation must be identical across all pages.
- Do not restyle a single button in isolation.
- Apply the system everywhere in one coherent pass.

### Explicit Constraints

- Masculine, industrial tone.
- No orange.
- No pastel.
- No "flat modern" look.
- Depth through tone, elevation, and edges — not flashy gradients.

**If any part of the UI violates this hierarchy, it is considered incorrect.**


## ENFORCEMENT

This file is the source of truth.

Before implementing ANY of the following:
- login changes
- session changes
- button styles
- page layouts
- navigation changes

The implementation MUST be verified against this contract.

If a requested change conflicts with this contract:
- The contract wins
- The change must be rejected or adjusted

No exceptions.