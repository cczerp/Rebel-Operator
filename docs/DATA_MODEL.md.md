## AI SCANNING PIPELINE (IMMUTABLE)

The system uses a two-stage scanning pipeline.
The stages have distinct responsibilities and strict gating rules.

---

### Stage 1 — Regular AI Scanner (Classification)

Inputs:
- Text input (required)
- Images (optional)

Requirements:
- At least 3 distinct key details must be provided
- If fewer than 3 details are present, the scan must not run

Responsibilities:
- Suggest possible item identities
- Assist with labeling and categorization
- Determine collectibility status:
  - collectible: true | false | uncertain

Limitations:
- Must not assert age or authenticity as fact
- Must not write to global databases
- Must not infer condition definitively

---

### Stage 2 — Enhanced Analyzer (Verification)

Inputs:
- Images only

Prerequisites:
- Regular AI Scanner has run
- Regular AI Scanner marked item as collectible
- Images meet minimum quality thresholds

Responsibilities:
- Visually confirm collectibility
- Estimate age from physical cues
- Assess condition from observable defects
- Detect known forms, variants, and attributes

Limitations:
- Must not run without images
- Must not run on non-collectible items
- Must not accept user-provided claims as truth

---

### Global Database Ingestion

- Users may never directly create or modify global collector records
- Global records may only be created or updated by the Enhanced Analyzer
- Ingestion decisions are backend-only and automatic
- The user is never prompted to “add” an item to the global database