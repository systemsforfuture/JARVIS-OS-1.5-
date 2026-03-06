#!/bin/bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — ClawHub Community Skills Installer
# SYSTEMS™ · architectofscale.com
#
# Installiert die besten Community-Skills von ClawHub.
# Diese Skills erweitern die Faehigkeiten aller Agenten.
#
# Usage:
#   ./scripts/install-clawhub-skills.sh
#   ./scripts/install-clawhub-skills.sh --minimal   (nur Basis)
#   ./scripts/install-clawhub-skills.sh --full       (alle)
# ═══════════════════════════════════════════════════════════

set -e

MODE="${1:-full}"

echo "═══════════════════════════════════════"
echo "  JARVIS — ClawHub Skills Installer"
echo "  Mode: ${MODE}"
echo "═══════════════════════════════════════"

# Check if clawhub CLI is available
if ! command -v clawhub &> /dev/null && ! command -v claw &> /dev/null; then
    echo ""
    echo "ClawHub CLI not found. Installing..."
    if command -v npm &> /dev/null; then
        npm i -g clawhub
    elif command -v pnpm &> /dev/null; then
        pnpm add -g clawhub
    else
        echo "ERROR: npm or pnpm required. Install Node.js first."
        exit 1
    fi
fi

# Use claw or clawhub, whichever is available
CLAW_CMD="clawhub"
if command -v claw &> /dev/null; then
    CLAW_CMD="claw skill"
fi

install_skill() {
    local skill_name="$1"
    local description="$2"
    echo "  Installing: ${skill_name} — ${description}"
    $CLAW_CMD install "$skill_name" 2>/dev/null || echo "    (skipped — may already be installed)"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE SKILLS (immer installieren)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "── Core Skills ──────────────────────"

install_skill "capability-evolver" "Self-improving agent capabilities"
install_skill "self-improving-agent" "Agent learns from interactions"
install_skill "summarize" "Text and document summarization"
install_skill "github" "GitHub integration (repos, PRs, issues)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESEARCH & WEB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "── Research & Web ─────────────────────"

install_skill "byterover" "Advanced web research and scraping"
install_skill "agent-browser" "Browser automation and web interaction"

if [ "$MODE" = "full" ]; then
    install_skill "gog" "Google search integration"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRODUCTIVITY & DOCUMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "── Productivity ────────────────────────"

install_skill "wacli" "Workflow automation CLI"

if [ "$MODE" = "full" ]; then
    install_skill "sonoscli" "Audio and media management"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEVELOPMENT & DEVOPS (fuer Archi)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "── Development & DevOps ───────────────"

install_skill "atxp" "Advanced task execution pipeline"

if [ "$MODE" = "full" ]; then
    echo "  (Full mode: DevOps skills)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMUNICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [ "$MODE" = "full" ]; then
    echo ""
    echo "── Communication ──────────────────────"
    echo "  (Telegram integration handled by JARVIS core)"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  Skills installation complete!"
echo "  Run 'clawhub list' to see installed skills"
echo "═══════════════════════════════════════"
