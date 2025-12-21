#!/bin/bash
# Claude Code Session Start Hook
# This displays automatically every time a new session starts

cat << 'CONTRACT'

╔══════════════════════════════════════════════════════════════╗
║  🔒 CRITICAL: CONTRACT ENFORCEMENT ENABLED                   ║
╚══════════════════════════════════════════════════════════════╝

Before making ANY code changes, you MUST read and comply with:

📄 docs/GLOBAL_CONTRACT.md     (Master ruleset - READ THIS FIRST)
📄 docs/SYSTEM-CONTRACT.md     (Auth + UI deep dive)
📄 docs/DATA_MODEL.md          (Database schema)
📄 docs/INVENTORY_MANAGEMENT.md (Inventory workflows)

═══════════════════════════════════════════════════════════════

KEY RULES (Non-Negotiable):

🔴 UI SYSTEM:
  • Red (#DC2626) = Primary actions ONLY (ONE per page max)
  • Steel (#475569) = Secondary actions
  • Charcoal (#1F2937) = Utility actions
  • ALL buttons MUST have material depth (NO flat styles)
  • Bottom nav: Home, Create, Account (3 items only)

🔐 AUTH SYSTEM:
  • Supabase → Flask-Login → Redis → PostgreSQL
  • Every getconn() MUST have putconn()
  • NEVER store connections on self
  • Use: with self._get_connection() as conn:

💾 DATA MODEL:
  • PostgreSQL ONLY (NO SQLite)
  • Storage location REQUIRED for active listings
  • Connection pool maxconn=2 (Render free tier)

═══════════════════════════════════════════════════════════════

⚠️  IF USER REQUEST CONFLICTS WITH CONTRACT:
    → THE CONTRACT WINS
    → Explain conflict with specific section reference
    → Propose compliant alternative
    → Wait for user confirmation

═══════════════════════════════════════════════════════════════

Read the contracts now before proceeding:
$ cat docs/GLOBAL_CONTRACT.md

CONTRACT
