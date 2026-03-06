#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Agent Identity Tests
# ═══════════════════════════════════════════════════════════

set -euo pipefail

PASS=0
FAIL=0
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

AGENTS=("jarvis" "elon" "steve" "donald" "archi" "donna" "iris" "satoshi" "felix" "andreas")

echo "JARVIS 1.5 — Agent Identity Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for agent in "${AGENTS[@]}"; do
    file="$REPO_ROOT/agents/$agent/IDENTITY.md"

    if [ ! -f "$file" ]; then
        echo "  FAIL: $agent — IDENTITY.md not found"
        ((FAIL++))
        continue
    fi

    # Check for required frontmatter fields
    for field in "name:" "slug:" "role:" "model:" "tier:"; do
        if grep -q "$field" "$file"; then
            ((PASS++))
        else
            echo "  FAIL: $agent — missing field: $field"
            ((FAIL++))
        fi
    done

    echo "  PASS: $agent — all fields present"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $PASS passed, $FAIL failed"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
