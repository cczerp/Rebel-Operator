🔒 GLOBAL RULE (APPLIES TO EVERYTHING)

If a UI element exists, it must either work exactly as described or be disabled with an explicit reason.

No silent failures.
No “coming soon” buttons that still click.
No internal errors surfacing to users.

1️⃣ BUTTONS (CURRENTLY UNTRUSTWORTHY)
❌ Current Reality

Buttons exist

Some do nothing

Some partially fire

Some break navigation

That means users cannot trust intent.

✅ NON-NEGOTIABLES FOR BUTTONS

Every button has ONE clear purpose

Submit

Save draft

Upload image

Generate with AI

Navigate

Every button must have a defined state machine

idle

loading

success

failure (with message)

If backend is not wired

Button is disabled

Tooltip or inline text explains why

No button may fail silently

Ever

Acceptance Test

Click → something visible happens every time
Even if that something is “This feature is not enabled yet.”

2️⃣ IMAGE / PICTURE UPLOADS (CRITICAL PATH)

Listings without images are dead on arrival. This is core.

❌ Current Reality

Upload attempts

No images persist

Unclear where they fail (frontend? backend? storage?)

✅ NON-NEGOTIABLES FOR IMAGE UPLOAD

Single known storage destination

Local (for dev) or

Cloud bucket (prod)

No ambiguity

Upload confirmation

Thumbnail appears immediately after upload

Not after save

Not after refresh

Hard validation

File type

Size limit

Max number of images

Failure messaging

“Upload failed: file too large”

“Upload failed: network error”

Images must persist

Refresh page → image still there

Navigate away → image still associated

Acceptance Test

Upload → see image → refresh → still see image

If that fails, nothing else matters yet.

3️⃣ AI FEATURES (CURRENTLY A LIE BUTTON)

Right now, “AI” exists as a promise, not a behavior.

That’s dangerous.

❌ Current Reality

AI button exists

It doesn’t reliably generate

Unclear inputs / outputs

✅ NON-NEGOTIABLES FOR AI

AI button only exists if pipeline exists

Prompt → model → response → UI update

AI scope must be explicit

Title only

Description only

Tags only

Or all fields

Deterministic fallback

If AI fails:

Show error

Do NOT wipe fields

Do NOT hang

Visible processing state

Spinner

“Generating…”

Timeout with message

No AI = no button

If key missing

If service down

If route broken

Acceptance Test

Click AI → text appears OR error explains why

Nothing in between.

4️⃣ WEBSITE CREDENTIALS PAGE (CURRENTLY BROKEN)

An internal error here is a red alert. This page is structural.

❌ Current Reality

Page throws internal error

Likely backend route, model, or migration issue

Users can’t even reach setup

✅ NON-NEGOTIABLES FOR CREDENTIALS PAGE

Page must load even with zero data

Empty state > crash

No uncaught exceptions

Errors handled server-side

UI shows safe message

Site picker must render

Even if no sites configured yet

Read-only before write

Page loads first

Then allows edits

Never the reverse

Missing dependencies are surfaced

“Database not initialized”

“No sites registered yet”

Acceptance Test

Navigate to credentials page → always loads → never 500s

🧪 DEBUG ORDER (DO NOT MIX THESE)

This is the order we go in. No skipping.

Credentials page loads

Buttons respond predictably

Image uploads persist

AI pipeline works or is hidden

Trying to fix AI before buttons is how projects rot.

🧾 MASTER NON-NEGOTIABLE CHECKLIST (PRINT THIS)

 No clickable dead UI

 No silent failures

 No internal errors exposed

 Images persist across refresh

 AI either works or is invisible

 Credentials page never crashes

 Empty states exist everywhere