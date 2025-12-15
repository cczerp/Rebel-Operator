## GLOBAL ENFORCEMENT (NON-NEGOTIABLE)

This file is a binding system contract.

Any implementation that:
- styles a single button in isolation
- changes a page without updating all affected pages
- relies on frontend state for auth display
- introduces a new color, elevation, or button style
- partially applies these rules

is considered INVALID and must be reverted.

All UI or auth changes must be applied:
- globally
- consistently
- in a single coherent pass

Incremental or piecemeal changes are forbidden.

### Landing Page Auth Rule (Critical)

The landing page MUST render login state exclusively from `current_user.is_authenticated`
on the server-rendered template.

- No frontend auth checks
- No cached flags
- No JavaScript-derived session state

If the landing page disagrees with other pages about auth state, the landing page is wrong.


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

### Light Mode / Dark Mode Relationship (IMMUTABLE)

Light mode and dark mode share the SAME color palette.
They differ by surface brightness, contrast, and lighting — not hue shifts.

Dark mode:
- May be very dark
- Uses charcoal-dark and steel-dark extensively
- Emphasizes depth, shadow, and material weight
- Is allowed to feel heavy and industrial

Light mode:
- Must be significantly lighter than dark mode
- Uses charcoal-light and steel-light surfaces
- Must increase contrast and separation between sections
- Must NOT look like “dark mode minus 2 shades”

If light mode feels heavy, muddy, or dim:
- It is incorrect

Light mode should feel like the same materials under brighter lighting,
not like a weak inversion of dark mode.


### Brand Red Calibration (IMMUTABLE)

Brand red must feel deliberate and weighty, not bright or plastic.

- Red should lean toward deep crimson / scarlet
- Avoid bright utility reds and notification-style reds
- Red may be darker in both modes
- Light mode red must remain restrained, not neon

Red is used sparingly for primary actions only.
Its power comes from contrast and depth, not brightness.

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


## AUTH BEHAVIOR (REQUIRED)

**The landing page must render based on `current_user`, not frontend state.**

- If the user is authenticated (`current_user.is_authenticated`), the landing page must NOT show marketing CTAs.
- Logged-in landing page should show workflow entry points only:
  - Personalized greeting (username)
  - Primary CTA: Create Listing (red)
  - Secondary CTAs: Inventory, Storage (steel)
- Do not use `is_guest` or other derived variables. Use `current_user.is_authenticated` directly in templates.

## NAVIGATION (REQUIRED)

**Bottom navigation must be reduced to: Home, Create, Account.**

- Move Listings, Inventory, Storage, Invoicing, Alerts into Account menu.
- Add a quick link under Account for "Website Credentials" (links to Settings/Credentials page).

## CREATE PAGE BUTTON HIERARCHY (REQUIRED)

**Button hierarchy must be strictly enforced:**

1. **Post Now** = primary red (one per page)
   - Must use `.btn-primary` or `.btn-success.btn-lg` with red gradient
   - Only one primary action button per page

2. **Save Draft** = utility (dark steel / charcoal)
   - Must use `.btn-secondary`, `.btn-outline-primary`, or `.btn-utility`
   - Charcoal gradient background with subtle edge highlight

3. **View Drafts** = secondary / subtle
   - Must use `.btn-secondary` or `.btn-sm` with steel/charcoal styling
   - Lower visual weight than Save Draft

## COLOR ENFORCEMENT

**Buttons must follow the red → steel → utility hierarchy.**

- No page may have multiple buttons competing at the same visual level.
- Do not apply color changes to single buttons in isolation.
- Apply changes consistently across all pages in one pass.

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