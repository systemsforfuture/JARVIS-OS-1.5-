#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Backup Script
# SYSTEMS™ · architectofscale.com
# ═══════════════════════════════════════════════════════════

set -euo pipefail

JARVIS_DIR="/opt/jarvis"
BACKUP_DIR="${JARVIS_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[BACKUP]${NC} $1"; }
ok()  { echo -e "${GREEN}[  OK  ]${NC} $1"; }

[[ $EUID -ne 0 ]] && { echo "Root erforderlich"; exit 1; }

source "${JARVIS_DIR}/.env"

mkdir -p "${BACKUP_DIR}"

log "Starte Backup..."

# Database backup
docker exec jarvis-db pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
ok "Datenbank gesichert"

# Config backup
tar -czf "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" -C "${JARVIS_DIR}" config .env
ok "Konfiguration gesichert"

# Cleanup old backups (keep last 7)
ls -t "${BACKUP_DIR}"/db_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm
ls -t "${BACKUP_DIR}"/config_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
ok "Alte Backups bereinigt (max. 7 behalten)"

echo ""
echo -e "${GREEN}Backup abgeschlossen: ${BACKUP_DIR}${NC}"
ls -lh "${BACKUP_DIR}"/*_${TIMESTAMP}* 2>/dev/null
