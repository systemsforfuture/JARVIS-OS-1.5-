#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Repo Structure Test
# ═══════════════════════════════════════════════════════════

set -euo pipefail

PASS=0
FAIL=0
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

check() {
    if [ -f "$REPO_ROOT/$1" ]; then
        echo "  PASS: $1"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $1"
        FAIL=$((FAIL + 1))
    fi
}

check_dir() {
    if [ -d "$REPO_ROOT/$1" ]; then
        echo "  PASS: $1/"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $1/"
        FAIL=$((FAIL + 1))
    fi
}

echo "JARVIS 1.5 — Structure Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Core Files:"
check "docker-compose.yml"
check ".gitignore"
check ".env.example"
check "README.md"

echo ""
echo "Installer:"
check "installer/install.sh"
check "installer/scripts/update.sh"
check "installer/scripts/health-check.sh"
check "installer/scripts/backup.sh"

echo ""
echo "Agents:"
for agent in jarvis elon steve donald archi donna iris satoshi felix andreas; do
    check "agents/$agent/IDENTITY.md"
done

echo ""
echo "Config:"
check "config/litellm/config.yaml"
check "config/openclaw/gateway.json"
check "config/openclaw/teams.json"
check "config/nginx/jarvis.conf"
check "config/db/init.sql"

echo ""
echo "Dashboard:"
check "dashboard/Dockerfile"
check "dashboard/server.js"
check "dashboard/package.json"
check "dashboard/public/index.html"

echo ""
echo "Skills:"
for cat in global marketing sales development operations analytics crypto; do
    check "skills/$cat/skills.json"
done

echo ""
echo "GitHub:"
check ".github/workflows/lint.yml"
check ".github/workflows/release.yml"
check ".github/ISSUE_TEMPLATE/bug_report.md"
check ".github/ISSUE_TEMPLATE/feature_request.md"

echo ""
echo "Docs:"
check "docs/architecture/overview.md"
check "docs/onboarding/quickstart.md"
check "docs/agents/agent-overview.md"
check "docs/api/api-reference.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $PASS passed, $FAIL failed"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
