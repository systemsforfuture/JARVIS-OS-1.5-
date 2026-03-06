#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Dashboard API Tests
# Requires running dashboard: docker compose up
# ═══════════════════════════════════════════════════════════

set -euo pipefail

BASE_URL="${1:-http://localhost:3000}"
PASS=0
FAIL=0

test_endpoint() {
    local method=$1
    local path=$2
    local expected_status=$3
    local description=$4

    local status
    status=$(curl -sf -o /dev/null -w "%{http_code}" "${BASE_URL}${path}" 2>/dev/null || echo "000")

    if [ "$status" = "$expected_status" ]; then
        echo "  PASS: $description ($status)"
        ((PASS++))
    else
        echo "  FAIL: $description (expected $expected_status, got $status)"
        ((FAIL++))
    fi
}

echo "JARVIS 1.5 — API Tests (${BASE_URL})"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health
test_endpoint "GET" "/api/health" "200" "Health endpoint"

# Agents
test_endpoint "GET" "/api/agents" "200" "List agents"

# Tasks
test_endpoint "GET" "/api/tasks" "200" "List tasks"

# Skills
test_endpoint "GET" "/api/skills" "200" "List skills"

# Memory
test_endpoint "GET" "/api/memory" "200" "List memory"

# Stats
test_endpoint "GET" "/api/stats" "200" "System stats"

# Auth required
test_endpoint "GET" "/api/audit" "401" "Audit (no auth)"

# Frontend
test_endpoint "GET" "/" "200" "Dashboard frontend"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $PASS passed, $FAIL failed"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
