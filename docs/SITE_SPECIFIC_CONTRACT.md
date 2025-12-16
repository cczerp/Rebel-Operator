NON-NEGOTIABLES (GLOBAL)

Every supported site must be explicitly listed everywhere it applies

Create page

Credentials page

CSV import/export page

Future sites must have a reserved slot even if disabled

Nothing is generic

No “Enter API Key” without saying what key, why, and where to get it

No “Upload CSV” without exact format + source instructions

Site-specific clarity beats compactness

Users should never have to Google “How do I get X API key”

If a site does not require credentials or CSVs, that fact must be stated explicitly

1️⃣ MASTER SITE REGISTRY (FOUNDATIONAL)

This is the backbone everything references.

Each site entry contains metadata that drives UI behavior.

Example structure (conceptual, not code):

Site:
- Name
- Status: active | coming_soon | planned
- Posting Method: API | CSV | Manual | Hybrid
- Requires Credentials: yes/no
- Requires API Key: yes/no
- Requires Username/Password: yes/no
- Requires OAuth: yes/no
- Supports CSV Import: yes/no
- Supports CSV Export: yes/no
- Notes / Constraints


This registry feeds:

Create page sections

Credential picker dropdown

CSV documentation renderer

Future integrations without refactors

2️⃣ CREATE PAGE (YOU ALREADY DID THIS RIGHT)

You noted this is already sectioned. Good. Keep it.

Rule:
Each section must reference the same site registry IDs used elsewhere.

Example:

Create Listing →
  ├─ Mercari
  ├─ eBay
  ├─ Facebook Marketplace
  ├─ Poshmark
  └─ [Reserved: Etsy, Shopify, Depop, etc.]


No changes needed here other than ensuring it pulls from the same registry.

3️⃣ CREDENTIALS PAGE (THIS IS THE BIG FIX)
A. Site Picker First (Non-Negotiable)

At the top of the credentials page:

“Select the site you want to connect:”

Dropdown or tile grid:

Mercari

eBay

Facebook Marketplace

Poshmark

(Disabled but visible: Etsy, Shopify, etc.)

Nothing shows until a site is selected.

B. Site-Specific Credential Panel

Once a site is selected, render only what that site needs.

Example: eBay

Required Credentials

✔ API Key (OAuth Token)

✖ Username/Password (not used)

Where to Get It

Step-by-step, inline:

Go to eBay Developer Program

Create an application

Generate OAuth credentials

Copy the Production Token

What This Key Does (Short Summary)

This API key allows the app to create, update, and manage listings on your behalf without storing your eBay password. You can revoke access at any time from eBay.

Input Fields

API Key

Environment toggle (Sandbox / Production)

Example: Facebook Marketplace

Required Credentials

✔ Email

✔ Password

✖ API Key

Explanation

Facebook Marketplace does not provide a public posting API. Credentials are used to automate listing creation through approved browser automation.

Security Note

Credentials are encrypted and never shared. You can remove access at any time.

Example: Mercari

If applicable:

Required Credentials

Email

Password

Optional session token (if supported later)

Explain why.

C. If a Site Requires NOTHING

Example:

Poshmark

Poshmark currently does not require credentials. Listings are created using CSV import only.

That sentence matters. It prevents confusion.

4️⃣ CSV DOCUMENTATION (SITE-SPECIFIC, NO EXCEPTIONS)

This is a separate page or tab, but follows the same site picker logic.

A. Site Picker Again

Same list. Same order. Same IDs.

B. Per-Site CSV Section Structure

Every site that supports CSV gets this structure:

📄 Mercari CSV Support
Where to Upload the CSV

Mercari Dashboard → Listings → Import CSV

Or: Direct upload via this app (if supported)

CSV Template

Download sample CSV (button)

Column-by-column explanation

Example:

title – Listing title
description – Full description
price – USD, no symbols
quantity – Integer
condition – Enum (New, Like New, Used)

How to Export From Mercari (If Supported)

Step-by-step or:

Mercari does not support CSV export. Use this app’s export feature instead.

📄 eBay CSV Support
Where to Upload

Seller Hub → Listings → Upload → File Exchange

Export Instructions

Seller Hub → Reports → Listings → Download active listings

Notes

Category IDs required

Variations require separate rows

📄 Facebook Marketplace

If unsupported:

Facebook Marketplace does not support CSV import or export. Listings must be created individually or via automation.

Again, stating “no” is just as important as stating “yes”.

5️⃣ SHORT SUMMARIES (MANDATORY UX RULE)

Every credentials section must include one short summary, either at the top or bottom:

What the credential does

What permissions it grants

How to revoke it

One paragraph max. No fluff.

This prevents:

Fear

Support tickets

“What did I just paste in here?” moments

6️⃣ ROOM FOR GROWTH (BUILT-IN)

For future sites:

They appear disabled but visible

Clicking them shows:

“This site is planned. Credential requirements will appear here when available.”

No redesign later. No mystery additions.