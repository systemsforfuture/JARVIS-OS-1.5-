#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Update Script
# SYSTEMS™ · architectofscale.com
# ═══════════════════════════════════════════════════════════

set -euo pipefail

JARVIS_DIR="/opt/jarvis"
GITHUB_REPO="systems-tm/jarvis-15"
GITHUB_RAW="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[UPDATE]${NC} $1"; }
ok()   { echo -e "${GREEN}[  OK  ]${NC} $1"; }
fail() { echo -e "${RED}[FATAL ]${NC} $1"; exit 1; }

# Check root
[[ $EUID -ne 0 ]] && fail "Root erforderlich: sudo bash update.sh"

# Check installation
[[ ! -d "${JARVIS_DIR}" ]] && fail "JARVIS nicht gefunden unter ${JARVIS_DIR}"

log "JARVIS Update gestartet..."

# Backup current .env
cp "${JARVIS_DIR}/.env" "${JARVIS_DIR}/.env.backup.$(date +%Y%m%d%H%M%S)"
ok "Backup erstellt"

# Pull latest configs
log "Lade neueste Konfiguration..."
curl -fsSL "${GITHUB_RAW}/config/litellm/config.yaml" -o "${JARVIS_DIR}/config/litellm/config.yaml"
curl -fsSL "${GITHUB_RAW}/config/openclaw/gateway.json" -o "${JARVIS_DIR}/config/openclaw/gateway.json"
curl -fsSL "${GITHUB_RAW}/config/openclaw/teams.json" -o "${JARVIS_DIR}/config/openclaw/teams.json"
ok "Konfiguration aktualisiert"

# Pull latest images
log "Aktualisiere Docker Images..."
cd "${JARVIS_DIR}"
docker compose pull
ok "Images aktualisiert"

# Restart
log "Starte JARVIS neu..."
docker compose down
docker compose up -d
ok "JARVIS neugestartet"

# Health check
sleep 10
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    ok "JARVIS laeuft und ist gesund"
else
    log "Dashboard noch nicht erreichbar — bitte 30 Sekunden warten"
fi

echo ""
echo -e "${GREEN}Update abgeschlossen.${NC}"
