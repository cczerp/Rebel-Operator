SYSTEM CONTRACT — RESSELL REBEL

AUTH · UI · THEMING · BEHAVIOR (NON-NEGOTIABLE)

0. GLOBAL ENFORCEMENT

This document is the single source of truth.

Any implementation that:

styles a single component in isolation

modifies one page but not all affected pages

introduces new colors, button styles, elevations, or effects

relies on frontend-derived auth state

applies incremental or partial fixes

is INVALID and must be reverted.

All changes must be:

system-wide

consistent

applied in one coherent pass

If two pages disagree, the system is broken.

1. AUTHENTICATION SYSTEM (IMMUTABLE)
Architecture

Supabase authenticates users only (credentials + OAuth)

Flask-Login owns session state

Redis stores sessions server-side

PostgreSQL stores user and application data only

Browser cookies store session ID only

Invariants

supabase.uid == flask_login.user_id

login_user(user) MUST be called after authentication

user_loader MUST fetch the user from PostgreSQL

If user_loader fails, user is treated as logged out

Every pool.getconn() MUST have a matching putconn()

No pooled database connection may be stored on self

OAuth State Management (NON-NEGOTIABLE)

Supabase's PKCE flow handles state parameter internally

DO NOT add custom state via query_params in OAuth requests

DO NOT manually validate state in callback handlers

DO NOT store or manage custom OAuth state - Supabase does this automatically

The Supabase client with flow_type="pkce" automatically:
- Generates state parameter
- Stores code_verifier in FlaskSessionStorage (Redis-backed)
- Validates state on callback
- Manages the entire OAuth security flow

Any attempt to add custom state parameters will cause bad_oauth_state errors and break OAuth login

Violation of any invariant causes login instability.

2. AUTH DISPLAY RULES (CRITICAL)
Source of Truth

All auth-based rendering MUST use
current_user.is_authenticated server-side

Frontend flags, cached JS state, or derived variables are forbidden

Landing Page Rule

If current_user.is_authenticated is true:

Marketing CTAs MUST NOT render

Logged-in workflow UI MUST render

If any page shows logged-in UI while the landing page does not, the landing page is incorrect.

3. LIGHT MODE / DARK MODE SYSTEM

Light and dark mode share the same material palette.
Only lighting, contrast, and depth change.

Dark Mode

Deep, heavy, industrial

Charcoal-dark and steel-dark dominate

Emphasis on shadow, depth, and weight

May be darker than current if readability is preserved

Light Mode

Significantly brighter than dark mode

Uses charcoal-light and steel-light surfaces

Must feel like the same materials under stronger light

Must NOT feel like “dark mode minus two shades”

If light mode feels muddy, dim, or heavy, it is incorrect.

4. BRAND COLOR SYSTEM (ROLE-BASED)

Colors are roles, not decorations.

Red — Primary Signal Color

Used to indicate:

Primary forward action

Commitment or activation

Selection focus

Irreversible or high-impact actions

Red must be used sparingly.

If red appears, it must mean:
“This action matters more than the others.”

Red must never be used:

as a background surface

for general layout

for decorative accents

for secondary or utility actions

Less red increases authority.

Charcoal — Foundational Material

App canvas

Depth surfaces

Weight and grounding

--charcoal
--charcoal-light
--charcoal-dark

Steel Blue-Grey — Structural Material

UI containers

Functional surfaces

Secondary actions and controls

Charcoal and steel are equal material layers and may be used together or alternately based on context, not hierarchy.

--steel
--steel-light
--steel-dark

Off-White — Accent Only

Text

Icons

Dividers

Outlines

Off-white is never a surface.

--off-white
--off-white-text

5. BUTTON SYSTEM (GLOBAL)

Buttons are materials, not flat fills.

Absolute Rules

No solid white buttons

No flat grey buttons

No page may invent a new button style

Buttons must convey depth and interaction

Button Tiers

Primary (Red)

One per page

Highest elevation

Dominant action

Secondary (Steel)

Lower elevation

Functional emphasis

Utility (Charcoal / Dark Steel)

Minimal elevation

Supportive actions only

Hover and active states must change lighting and depth, not just color.

6. BUTTON TEXT CONTRAST (IMMUTABLE)

Button readability is governed by contrast, not brightness.

Red buttons → black text

Steel / grey-blue buttons → black text

Dark / charcoal buttons → off-white or crimson text

White text on bright or mid-tone buttons is forbidden.

If a button is not immediately readable at a glance, it is incorrect.

7. MOTION & MATERIAL EFFECTS

Motion is ambient and material-based, never flashy.

Approved effects:

Inner glow on hover

Subtle animated lighting

Slow ambient motion

Depth cues suggesting forged or machined surfaces

Forbidden effects:

Fast animations

Pulsing

Flashing

Playful or bouncy motion

Motion must feel controlled, industrial, and intentional.

8. LAYOUT & NAVIGATION RULES
Landing Page

Logged-out: marketing only

Logged-in:

Personalized greeting

Create Listing (primary)

Inventory and Storage (secondary)

Create Page

Focused work surface

AI actions + Save Draft only

No marketing CTAs

Navigation

Bottom navigation: Home · Create · Account

Listings, Inventory, Storage, Invoicing, Alerts live under Account

Account must include a quick link to Website Credentials

9. ENFORCEMENT

Before implementing any change involving:

authentication

session handling

UI styling

layout

navigation

buttons

motion

## DATA OWNERSHIP PRINCIPLES

- User-owned data MUST include `user_id`
- Global data MUST NOT include `user_id`
- All user data queries MUST filter by `user_id`
- Users may never directly modify global data
- Backend is the sole authority for data creation and mutation

---

## USER-OWNED DATA (PRIVATE)

### Drafts
- Table: drafts
- Ownership: user_id
- Images: Supabase Storage
- Scope: private, persistent

### Inventory
- Table: inventory_items
- Ownership: user_id
- Images: Supabase Storage

### Storage Locations
- Table: storage_locations
- Ownership: user_id

### Sales / Invoices
- Tables: sales, invoices
- Ownership: user_id

### Profit / Loss
- Derived from inventory + sales
- Optional cached snapshots (user_id required)

---

## GLOBAL DATA (READ-ONLY TO USERS)

### Collector Items
- Table: collector_items
- Ownership: system
- Purpose: canonical item definitions

### Item Forms / Variants
- Table: collector_item_forms
- Ownership: system

---

## USER ↔ GLOBAL RELATIONSHIPS

### User Collector Items
- Table: user_collector_items
- Links users to collector_items
- Stores user-specific condition and detected attributes

---

## STORAGE (IMAGES)

- Provider: Supabase Storage
- Buckets:
  - listing-images
- Paths are namespaced by user_id
- Database stores image references, not binaries




The change MUST be verified against this contract.

If a requested change conflicts:

The contract wins

The change is rejected or adapted

No exceptions to these rules and no editing this file ever. 

