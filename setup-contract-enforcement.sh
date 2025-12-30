#!/bin/bash
# Setup Contract Enforcement for Resell Rebel
# This script ensures all AI agents automatically see and follow the contract rules

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🔒 Setting up Contract Enforcement for Resell Rebel"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: Run this script from the Resell-Rebel root directory"
    exit 1
fi

# 1. Create .claude directory structure
echo "📁 Creating .claude directory structure..."
mkdir -p .claude/hooks

# 2. Copy/verify Claude instructions
if [ ! -f ".claude/instructions.md" ]; then
    echo "✅ .claude/instructions.md already exists"
else
    echo "⚠️  .claude/instructions.md missing - please run git pull to get it"
fi

# 3. Verify session start hook
if [ -f ".claude/hooks/session-start.sh" ]; then
    chmod +x .claude/hooks/session-start.sh
    echo "✅ Session start hook configured and executable"
else
    echo "⚠️  .claude/hooks/session-start.sh missing"
fi

# 4. Create .github directory
echo "📁 Creating .github directory..."
mkdir -p .github

# 5. Verify Cursor rules
if [ -f ".cursorrules" ]; then
    echo "✅ Cursor rules configured"
else
    echo "⚠️  .cursorrules missing"
fi

# 6. Verify GitHub Copilot instructions
if [ -f ".github/copilot-instructions.md" ]; then
    echo "✅ GitHub Copilot instructions configured"
else
    echo "⚠️  .github/copilot-instructions.md missing"
fi

# 7. Verify contract documents exist
echo ""
echo "📄 Verifying contract documents..."
contracts_ok=true

if [ ! -f "docs/GLOBAL_CONTRACT.md" ]; then
    echo "❌ docs/GLOBAL_CONTRACT.md missing"
    contracts_ok=false
else
    echo "✅ docs/GLOBAL_CONTRACT.md"
fi

if [ ! -f "docs/SYSTEM-CONTRACT.md" ]; then
    echo "❌ docs/SYSTEM-CONTRACT.md missing"
    contracts_ok=false
else
    echo "✅ docs/SYSTEM-CONTRACT.md"
fi

if [ ! -f "docs/DATA_MODEL.md" ]; then
    echo "❌ docs/DATA_MODEL.md missing"
    contracts_ok=false
else
    echo "✅ docs/DATA_MODEL.md"
fi

if [ ! -f "docs/INVENTORY_MANAGEMENT.md" ]; then
    echo "❌ docs/INVENTORY_MANAGEMENT.md missing"
    contracts_ok=false
else
    echo "✅ docs/INVENTORY_MANAGEMENT.md"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"

if [ "$contracts_ok" = true ]; then
    echo "✅ Contract enforcement setup complete!"
    echo ""
    echo "All AI agents (Claude, Cursor, GitHub Copilot) will now:"
    echo "  • See contract requirements on every session"
    echo "  • Verify compliance before suggesting changes"
    echo "  • Reject changes that violate immutable rules"
    echo ""
    echo "Next steps:"
    echo "  1. Start a new Claude Code session to see the enforcement message"
    echo "  2. Verify session hook displays contract reminder"
    echo "  3. Test by requesting a change that violates a contract rule"
    echo ""
    echo "Contract files location:"
    echo "  📄 docs/GLOBAL_CONTRACT.md (master ruleset)"
    echo "  📄 docs/SYSTEM-CONTRACT.md (auth + UI)"
    echo "  📄 docs/DATA_MODEL.md (database)"
    echo "  📄 docs/INVENTORY_MANAGEMENT.md (inventory)"
else
    echo "⚠️  Some contract files are missing!"
    echo "Run 'git pull' to fetch them from the repository"
fi

echo "════════════════════════════════════════════════════════════════"
