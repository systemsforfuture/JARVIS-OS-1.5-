#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Health Check
# SYSTEMS™ · architectofscale.com
# ═══════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

JARVIS_DIR="${JARVIS_DIR:-/opt/jarvis}"

echo ""
echo -e "${CYAN}JARVIS 1.5 — Health Check${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ALL_OK=true

# JARVIS Services
echo ""
echo -e "${CYAN}Docker Services:${NC}"
for svc in jarvis-db jarvis-redis jarvis-litellm jarvis-core jarvis-dashboard jarvis-ollama; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${svc}$"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null)
        if [[ "$STATUS" == "running" ]]; then
            echo -e "  ${GREEN}OK${NC}    ${svc}"
        else
            echo -e "  ${YELLOW}${STATUS}${NC}  ${svc}"
            ALL_OK=false
        fi
    else
        echo -e "  ${RED}DOWN${NC}  ${svc}"
        ALL_OK=false
    fi
done

# Externe Services
echo ""
echo -e "${CYAN}Externe Services:${NC}"

if [[ -f "${JARVIS_DIR}/.env" ]]; then
    source "${JARVIS_DIR}/.env"
fi

# OpenClaw
OPENCLAW_URL="${OPENCLAW_URL:-http://localhost:8080}"
if curl -sf "${OPENCLAW_URL}" >/dev/null 2>&1; then
    echo -e "  ${GREEN}OK${NC}    OpenClaw (${OPENCLAW_URL})"
else
    echo -e "  ${RED}DOWN${NC}  OpenClaw (${OPENCLAW_URL})"
    ALL_OK=false
fi

# N8N
N8N_URL="${N8N_URL:-http://localhost:5678}"
if curl -sf "${N8N_URL}" >/dev/null 2>&1; then
    echo -e "  ${GREEN}OK${NC}    N8N (${N8N_URL})"
else
    echo -e "  ${RED}DOWN${NC}  N8N (${N8N_URL})"
    ALL_OK=false
fi

# Dashboard API
echo ""
echo -e "${CYAN}APIs:${NC}"
if curl -sf http://localhost:3000/api/health >/dev/null 2>&1; then
    HEALTH=$(curl -sf http://localhost:3000/api/health 2>/dev/null)
    echo -e "  ${GREEN}OK${NC}    Dashboard API"
else
    echo -e "  ${RED}DOWN${NC}  Dashboard API"
    ALL_OK=false
fi

# LiteLLM
if curl -sf http://localhost:4000/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}OK${NC}    LiteLLM Router"
else
    echo -e "  ${YELLOW}!!${NC}    LiteLLM Router (evtl. noch am starten)"
fi

# Ollama
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo "?")
    echo -e "  ${GREEN}OK${NC}    Ollama (${MODELS} Modelle)"
else
    echo -e "  ${YELLOW}!!${NC}    Ollama (evtl. CPU-only, langsam)"
fi

echo ""
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if $ALL_OK; then
    echo -e "\n${GREEN}Alle Systeme operational.${NC}\n"
else
    echo -e "\n${YELLOW}Einige Services brauchen Aufmerksamkeit.${NC}\n"
    exit 1
fi
