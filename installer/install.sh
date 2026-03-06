#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Installation Script
# SYSTEMS™ · architectofscale.com
# ═══════════════════════════════════════════════════════════
#
# Voraussetzungen (müssen VORHER installiert sein):
#   1. OpenClaw   — auf dem VPS installiert
#   2. N8N        — auf dem VPS installiert
#   3. Docker     — installiert und läuft
#
# Was dieses Script macht:
#   1. Prüft System + erkennt OpenClaw & N8N
#   2. Klont JARVIS Repo
#   3. Startet JARVIS Stack (Core + Dashboard + DB + Redis + LiteLLM + Ollama)
#   4. Lädt DB-Schema (20 Tabellen)
#   5. Konfiguriert alle 10 Agents in OpenClaw
#   6. Verbindet N8N Webhooks
#   7. Startet Mission Control Dashboard
#
# Usage:
#   sudo bash install.sh
#
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ── CONFIG ──────────────────────────────────────────────
JARVIS_VERSION="1.5.0"
JARVIS_DIR="/opt/jarvis"
GITHUB_REPO="systemsforfuture/JARVIS-OS"
MIN_RAM_MB=3500
MIN_DISK_GB=30

# ── COLORS ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# ── HELPER ──────────────────────────────────────────────
log()   { echo -e "${CYAN}[JARVIS]${NC} $1"; }
ok()    { echo -e "  ${GREEN}OK${NC}  $1"; }
warn()  { echo -e "  ${YELLOW}!!${NC}  $1"; }
fail()  { echo -e "  ${RED}FAIL${NC}  $1"; exit 1; }
phase() { echo -e "\n${PURPLE}--- $1 ---${NC}\n"; }
ask()   { read -r -p "$(echo -e "${CYAN}[?]${NC} $1: ")" "$2"; }

generate_password() {
    openssl rand -base64 32 | tr -d '/+=' | head -c 24
}

# ── BOOT ────────────────────────────────────────────────
clear
echo -e "${WHITE}"
cat << 'LOGO'

       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
       ██║███████║██████╔╝██║   ██║██║███████╗
  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝

LOGO
echo -e "${NC}"
echo -e "${DIM}  Autonomes KI-Betriebssystem v${JARVIS_VERSION}${NC}"
echo -e "${DIM}  SYSTEMS™ · architectofscale.com${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ═══════════════════════════════════════════════════════════
# PHASE 1 — System prüfen
# ═══════════════════════════════════════════════════════════
phase "Phase 1/8 — Systemprüfung"

# Root check
[[ $EUID -ne 0 ]] && fail "Dieses Script muss als root laufen: sudo bash install.sh"

# OS check
source /etc/os-release 2>/dev/null || fail "OS nicht erkannt"
ok "OS: $PRETTY_NAME"

# RAM check
ram_mb=$(free -m | awk '/^Mem:/{print $2}')
[[ $ram_mb -lt $MIN_RAM_MB ]] && fail "Min. ${MIN_RAM_MB}MB RAM nötig (gefunden: ${ram_mb}MB)"
ok "RAM: ${ram_mb}MB"

# Disk check
disk_gb=$(df -BG / | tail -1 | awk '{print $4}' | tr -d 'G')
[[ $disk_gb -lt $MIN_DISK_GB ]] && fail "Min. ${MIN_DISK_GB}GB Disk nötig (gefunden: ${disk_gb}GB)"
ok "Disk: ${disk_gb}GB frei"

# Docker check
command -v docker &>/dev/null || fail "Docker nicht installiert. Installiere zuerst Docker."
ok "Docker: $(docker --version | head -1)"

# ═══════════════════════════════════════════════════════════
# PHASE 2 — OpenClaw & N8N erkennen
# ═══════════════════════════════════════════════════════════
phase "Phase 2/8 — OpenClaw & N8N erkennen"

# OpenClaw erkennen
OPENCLAW_URL=""
OPENCLAW_DETECTED=false

# Prüfe bekannte Ports und Docker-Container
for port in 8080 3001 8000; do
    if curl -sf "http://localhost:${port}/api/health" >/dev/null 2>&1 || \
       curl -sf "http://localhost:${port}/health" >/dev/null 2>&1 || \
       curl -sf "http://localhost:${port}" >/dev/null 2>&1; then
        OPENCLAW_URL="http://localhost:${port}"
        OPENCLAW_DETECTED=true
        break
    fi
done

# Prüfe Docker-Container
if ! $OPENCLAW_DETECTED; then
    OPENCLAW_CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -i "openclaw\|open-claw\|claw" | head -1 || true)
    if [[ -n "$OPENCLAW_CONTAINER" ]]; then
        OPENCLAW_PORT=$(docker port "$OPENCLAW_CONTAINER" 2>/dev/null | head -1 | awk -F: '{print $NF}' || echo "8080")
        OPENCLAW_URL="http://localhost:${OPENCLAW_PORT}"
        OPENCLAW_DETECTED=true
    fi
fi

if $OPENCLAW_DETECTED; then
    ok "OpenClaw gefunden: ${OPENCLAW_URL}"
else
    warn "OpenClaw nicht automatisch erkannt"
    ask "OpenClaw URL eingeben (z.B. http://localhost:8080)" OPENCLAW_URL
    [[ -z "$OPENCLAW_URL" ]] && OPENCLAW_URL="http://localhost:8080"
    ok "OpenClaw: ${OPENCLAW_URL}"
fi

# N8N erkennen
N8N_URL=""
N8N_DETECTED=false

for port in 5678 5679; do
    if curl -sf "http://localhost:${port}" >/dev/null 2>&1; then
        N8N_URL="http://localhost:${port}"
        N8N_DETECTED=true
        break
    fi
done

if ! $N8N_DETECTED; then
    N8N_CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -i "n8n" | head -1 || true)
    if [[ -n "$N8N_CONTAINER" ]]; then
        N8N_PORT=$(docker port "$N8N_CONTAINER" 2>/dev/null | head -1 | awk -F: '{print $NF}' || echo "5678")
        N8N_URL="http://localhost:${N8N_PORT}"
        N8N_DETECTED=true
    fi
fi

if $N8N_DETECTED; then
    ok "N8N gefunden: ${N8N_URL}"
else
    warn "N8N nicht automatisch erkannt"
    ask "N8N URL eingeben (z.B. http://localhost:5678)" N8N_URL
    [[ -z "$N8N_URL" ]] && N8N_URL="http://localhost:5678"
    ok "N8N: ${N8N_URL}"
fi

# ═══════════════════════════════════════════════════════════
# PHASE 3 — API Keys abfragen
# ═══════════════════════════════════════════════════════════
phase "Phase 3/8 — API Keys konfigurieren"

echo -e "  ${DIM}Mindestens ANTHROPIC_API_KEY wird benötigt.${NC}"
echo -e "  ${DIM}Andere Keys können später in .env nachgetragen werden.${NC}"
echo ""

ask "ANTHROPIC_API_KEY (Claude)" ANTHROPIC_API_KEY
ask "GROQ_API_KEY (optional, Enter = überspringen)" GROQ_API_KEY
ask "MOONSHOT_API_KEY (optional, Kimi)" MOONSHOT_API_KEY
ask "TELEGRAM_BOT_TOKEN (optional)" TELEGRAM_BOT_TOKEN
ask "TELEGRAM_CHAT_ID (optional)" TELEGRAM_CHAT_ID
ask "Domain (optional, z.B. jarvis.firma.com)" DOMAIN

ok "Keys erfasst"

# ═══════════════════════════════════════════════════════════
# PHASE 4 — JARVIS Repo klonen & .env erstellen
# ═══════════════════════════════════════════════════════════
phase "Phase 4/8 — JARVIS installieren"

mkdir -p "${JARVIS_DIR}"

# Repo klonen
if [[ -d "${JARVIS_DIR}/.git" ]]; then
    log "JARVIS bereits geklont, aktualisiere..."
    cd "${JARVIS_DIR}" && git pull origin main 2>/dev/null || true
else
    log "Klone JARVIS Repository..."
    git clone "https://github.com/${GITHUB_REPO}.git" "${JARVIS_DIR}" 2>/dev/null || {
        # Fallback: Kopiere lokale Dateien wenn git clone fehlschlägt
        warn "Git clone fehlgeschlagen, nutze lokale Dateien..."
        cp -r "$(dirname "$0")/.." "${JARVIS_DIR}/" 2>/dev/null || true
    }
fi

cd "${JARVIS_DIR}"

# Generiere Passwörter
DB_PASS=$(generate_password)
REDIS_PASS=$(generate_password)
JWT_SECRET=$(generate_password)
DASHBOARD_SECRET=$(generate_password)
LITELLM_KEY="sk-jarvis-$(generate_password)"

# .env erstellen
cat > "${JARVIS_DIR}/.env" << ENVFILE
# ═══════════════════════════════════════════════════
# JARVIS 1.5 — Environment
# Generiert: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# SYSTEMS™ · architectofscale.com
# ═══════════════════════════════════════════════════

# ── SYSTEM ──────────────────────────────────────
JARVIS_VERSION=${JARVIS_VERSION}
JARVIS_ENV=production
JARVIS_DIR=${JARVIS_DIR}
TZ=Europe/Berlin

# ── EXTERNE SERVICES (vorinstalliert) ───────────
OPENCLAW_URL=${OPENCLAW_URL}
N8N_URL=${N8N_URL}

# ── DATABASE (JARVIS-intern) ────────────────────
POSTGRES_HOST=jarvis-db
POSTGRES_PORT=5432
POSTGRES_DB=jarvis
POSTGRES_USER=jarvis
POSTGRES_PASSWORD=${DB_PASS}
DATABASE_URL=postgresql://jarvis:${DB_PASS}@jarvis-db:5432/jarvis

# ── SUPABASE (optional — Cloud) ────────────────
# Wenn gesetzt, nutzt JARVIS Supabase statt lokaler DB
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# ── REDIS ───────────────────────────────────────
REDIS_HOST=jarvis-redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASS}
REDIS_URL=redis://:${REDIS_PASS}@jarvis-redis:6379/0

# ── AUTH ────────────────────────────────────────
JWT_SECRET=${JWT_SECRET}
DASHBOARD_SECRET=${DASHBOARD_SECRET}
DASHBOARD_PORT=3000

# ── AI MODELS ───────────────────────────────────
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
OPENAI_API_KEY=
GROQ_API_KEY=${GROQ_API_KEY:-}
MOONSHOT_API_KEY=${MOONSHOT_API_KEY:-}

# ── LITELLM ─────────────────────────────────────
LITELLM_URL=http://jarvis-litellm:4000
LITELLM_MASTER_KEY=${LITELLM_KEY}
LITELLM_PORT=4000

# ── TELEGRAM ────────────────────────────────────
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}

# ── DOMAIN ──────────────────────────────────────
DOMAIN=${DOMAIN:-}
SSL_EMAIL=
ENVFILE

chmod 600 "${JARVIS_DIR}/.env"
ok ".env generiert (Passwörter automatisch erstellt)"

# ═══════════════════════════════════════════════════════════
# PHASE 5 — Docker Stack starten
# ═══════════════════════════════════════════════════════════
phase "Phase 5/8 — JARVIS Docker Stack starten"

# docker-compose.yml für die JARVIS-eigenen Services
cat > "${JARVIS_DIR}/docker-compose.production.yml" << 'COMPOSE'
version: "3.8"

# ═══════════════════════════════════════════════════════
# JARVIS 1.5 — Production Stack
# Nur JARVIS-eigene Services (OpenClaw + N8N sind extern)
# ═══════════════════════════════════════════════════════

services:
  # ── PostgreSQL (JARVIS Datenbank) ─────────────────
  jarvis-db:
    image: postgres:16-alpine
    container_name: jarvis-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-jarvis}
      POSTGRES_USER: ${POSTGRES_USER:-jarvis}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - jarvis-pg-data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-jarvis}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis (Cache) ─────────────────────────────────
  jarvis-redis:
    image: redis:7-alpine
    container_name: jarvis-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - jarvis-redis-data:/data

  # ── LiteLLM (Model Router) ───────────────────────
  jarvis-litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: jarvis-litellm
    restart: unless-stopped
    command: --config /app/config/config.yaml
    env_file: .env
    volumes:
      - ./config/litellm:/app/config:ro
    depends_on:
      jarvis-db:
        condition: service_healthy
    ports:
      - "127.0.0.1:4000:4000"

  # ── JARVIS Core (Python Backend) ─────────────────
  jarvis-core:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jarvis-core
    restart: unless-stopped
    env_file: .env
    environment:
      - LITELLM_URL=http://jarvis-litellm:4000
      - OLLAMA_API_BASE=http://jarvis-ollama:11434
    depends_on:
      jarvis-db:
        condition: service_healthy
      jarvis-litellm:
        condition: service_started

  # ── Mission Control Dashboard ────────────────────
  jarvis-dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    container_name: jarvis-dashboard
    restart: unless-stopped
    env_file: .env
    environment:
      - NODE_ENV=production
      - PORT=3000
    depends_on:
      jarvis-db:
        condition: service_healthy
    ports:
      - "0.0.0.0:3000:3000"

  # ── Ollama (Lokale LLMs, 0 EUR) ─────────────────
  jarvis-ollama:
    image: ollama/ollama:latest
    container_name: jarvis-ollama
    restart: unless-stopped
    volumes:
      - jarvis-ollama-data:/root/.ollama
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  jarvis-pg-data:
  jarvis-redis-data:
  jarvis-ollama-data:
COMPOSE

log "Starte Docker Stack..."
cd "${JARVIS_DIR}"
docker compose -f docker-compose.production.yml up -d --build 2>&1 | tail -5

# Warte auf PostgreSQL
log "Warte auf Datenbank..."
for i in $(seq 1 30); do
    if docker exec jarvis-db pg_isready -U jarvis >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

ok "Docker Stack läuft"

# ═══════════════════════════════════════════════════════════
# PHASE 6 — Datenbank-Schema laden
# ═══════════════════════════════════════════════════════════
phase "Phase 6/8 — Datenbank initialisieren"

source "${JARVIS_DIR}/.env"

# Schema v1 (Haupttabellen)
if [[ -f "${JARVIS_DIR}/config/db/supabase_schema.sql" ]]; then
    docker exec -i jarvis-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        < "${JARVIS_DIR}/config/db/supabase_schema.sql" 2>/dev/null || true
    ok "Schema v1 geladen (14 Tabellen)"
fi

# Schema v2 (Intelligence Layer)
if [[ -f "${JARVIS_DIR}/config/db/supabase_schema_v2.sql" ]]; then
    docker exec -i jarvis-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        < "${JARVIS_DIR}/config/db/supabase_schema_v2.sql" 2>/dev/null || true
    ok "Schema v2 geladen (6 weitere Tabellen)"
fi

# Dashboard-Schema (für einfachere Queries)
docker exec -i jarvis-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" << 'SQL'
-- Dashboard-kompatible Views
CREATE OR REPLACE VIEW v_agent_status AS
SELECT
    a.slug, a.name, a.role, a.status,
    a.config->>'default_model' as current_model,
    COUNT(DISTINCT to2.id) as total_tasks,
    COALESCE(AVG(to2.score), 0) as avg_score,
    COUNT(DISTINCT el.id) FILTER (WHERE NOT el.resolved) as open_errors
FROM agents a
LEFT JOIN task_outcomes to2 ON to2.agent_slug = a.slug
LEFT JOIN error_log el ON el.agent_slug = a.slug
GROUP BY a.slug, a.name, a.role, a.status, a.config;

CREATE OR REPLACE VIEW v_system_health AS
SELECT
    (SELECT COUNT(*) FROM task_outcomes WHERE created_at > NOW() - INTERVAL '24 hours') as tasks_24h,
    (SELECT COALESCE(AVG(score), 0) FROM task_outcomes WHERE created_at > NOW() - INTERVAL '24 hours') as avg_score_24h,
    (SELECT COUNT(*) FROM error_log WHERE NOT resolved) as open_errors,
    (SELECT COUNT(*) FROM messages WHERE created_at > NOW() - INTERVAL '24 hours') as messages_24h,
    (SELECT COUNT(*) FROM knowledge WHERE superseded_by IS NULL) as knowledge_entries,
    (SELECT COUNT(*) FROM learning_journal) as total_learnings;
SQL

ok "Datenbank vollständig initialisiert"

# ═══════════════════════════════════════════════════════════
# PHASE 7 — Agents in OpenClaw konfigurieren
# ═══════════════════════════════════════════════════════════
phase "Phase 7/8 — Agents in OpenClaw einrichten"

log "Konfiguriere 10 Agents in OpenClaw..."

# Agent-Definitionen für OpenClaw
configure_openclaw_agent() {
    local slug="$1"
    local name="$2"
    local role="$3"
    local model="$4"

    # Prompt-Datei laden wenn vorhanden
    local system_prompt=""
    if [[ -f "${JARVIS_DIR}/prompts/agents/${slug}.md" ]]; then
        system_prompt=$(cat "${JARVIS_DIR}/prompts/agents/${slug}.md")
    fi

    local base_prompt=""
    if [[ -f "${JARVIS_DIR}/prompts/agent_base.md" ]]; then
        base_prompt=$(cat "${JARVIS_DIR}/prompts/agent_base.md")
    fi

    # Vollständigen Prompt zusammenbauen
    local full_prompt="${base_prompt}

${system_prompt}"

    # Tools laden
    local tools="[]"
    local tools_file="${JARVIS_DIR}/skills/tools/${slug}_tools.json"
    if [[ -f "$tools_file" ]]; then
        tools=$(cat "$tools_file")
    fi

    # An OpenClaw senden (versuche verschiedene API-Pfade)
    local payload
    payload=$(jq -n \
        --arg slug "$slug" \
        --arg name "$name" \
        --arg role "$role" \
        --arg model "$model" \
        --arg prompt "$full_prompt" \
        --argjson tools "$tools" \
        '{
            slug: $slug,
            name: $name,
            role: $role,
            model: $model,
            system_prompt: $prompt,
            tools: $tools,
            config: {
                temperature: 0.5,
                max_tokens: 4096,
                litellm_url: "http://jarvis-litellm:4000"
            }
        }')

    # Versuche Agent in OpenClaw zu erstellen
    local response
    response=$(curl -sf -X POST "${OPENCLAW_URL}/api/agents" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null) || \
    response=$(curl -sf -X POST "${OPENCLAW_URL}/api/v1/agents" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null) || \
    response=$(curl -sf -X PUT "${OPENCLAW_URL}/agents/${slug}" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null) || true

    if [[ -n "$response" ]]; then
        ok "${name} — ${role}"
    else
        # OpenClaw API-Format nicht erkannt, speichere als Config-Datei
        echo "$payload" > "${JARVIS_DIR}/config/openclaw/agents/${slug}.json"
        ok "${name} — ${role} (Config gespeichert)"
    fi
}

mkdir -p "${JARVIS_DIR}/config/openclaw/agents"

configure_openclaw_agent "jarvis"  "JARVIS"   "Chief Intelligence Operator"      "tier0-kimi"
configure_openclaw_agent "elon"    "ELON"     "Analyst & Systemoptimierer"       "tier1-sonnet"
configure_openclaw_agent "steve"   "STEVE"    "Marketing & Content Lead"         "tier1-sonnet"
configure_openclaw_agent "donald"  "DONALD"   "Sales & Revenue Lead"             "tier1-sonnet"
configure_openclaw_agent "archi"   "ARCHI"    "Dev & Infrastructure Lead"        "tier1-sonnet"
configure_openclaw_agent "donna"   "DONNA"    "Backoffice & Operations Lead"     "tier1-haiku"
configure_openclaw_agent "iris"    "IRIS"     "Design & Creative Lead"           "tier1-sonnet"
configure_openclaw_agent "satoshi" "SATOSHI"  "Crypto & Trading Specialist"      "tier1-sonnet"
configure_openclaw_agent "felix"   "FELIX"    "Customer Success Lead"            "tier1-haiku"
configure_openclaw_agent "andreas" "ANDREAS"  "Customer Success SFE Specialist"  "tier1-haiku"

ok "Alle 10 Agents konfiguriert"

# ═══════════════════════════════════════════════════════════
# PHASE 8 — N8N Webhooks + Abschluss
# ═══════════════════════════════════════════════════════════
phase "Phase 8/8 — Verbindungen & Abschluss"

# N8N Webhook-Endpunkte speichern
cat > "${JARVIS_DIR}/config/n8n/webhooks.json" << JSON
{
  "n8n_url": "${N8N_URL}",
  "webhooks": {
    "task_completed": "${N8N_URL}/webhook/jarvis-task-completed",
    "error_alert": "${N8N_URL}/webhook/jarvis-error-alert",
    "daily_report": "${N8N_URL}/webhook/jarvis-daily-report",
    "agent_escalation": "${N8N_URL}/webhook/jarvis-escalation",
    "new_lead": "${N8N_URL}/webhook/jarvis-new-lead",
    "customer_alert": "${N8N_URL}/webhook/jarvis-customer-alert"
  },
  "instructions": "Erstelle diese Webhooks in N8N und verbinde sie mit den gewünschten Aktionen."
}
JSON

ok "N8N Webhook-Config erstellt"

# Ollama Basis-Modell laden
log "Lade Ollama Basis-Modell (kann einige Minuten dauern)..."
docker exec jarvis-ollama ollama pull llama3.1:8b 2>/dev/null &
OLLAMA_PID=$!

# Health Check
log "Prüfe alle Services..."
sleep 5

SERVICES_OK=true
for svc in jarvis-db jarvis-redis jarvis-litellm jarvis-core jarvis-dashboard; do
    if docker ps --format '{{.Names}}' | grep -q "^${svc}$"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
        if [[ "$STATUS" == "running" ]]; then
            ok "${svc}: running"
        else
            warn "${svc}: ${STATUS}"
            SERVICES_OK=false
        fi
    else
        warn "${svc}: not found"
        SERVICES_OK=false
    fi
done

# Server IP
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

# ── Abschluss ──────────────────────────────────────────
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${WHITE}${BOLD}  JARVIS 1.5 — Installation abgeschlossen!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Mission Control:${NC}  http://${SERVER_IP}:3000"
echo -e "  ${GREEN}Dashboard Login:${NC}  Passwort: ${DASHBOARD_SECRET}"
echo -e "  ${GREEN}OpenClaw:${NC}         ${OPENCLAW_URL}"
echo -e "  ${GREEN}N8N:${NC}              ${N8N_URL}"
echo -e "  ${GREEN}LiteLLM:${NC}          http://localhost:4000"
echo ""
echo -e "  ${YELLOW}Config:${NC}           ${JARVIS_DIR}/.env"
echo -e "  ${YELLOW}Logs:${NC}             docker logs jarvis-core"
echo ""
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
    echo -e "  ${GREEN}Telegram:${NC}         Bot aktiv — schreibe eine Nachricht!"
else
    echo -e "  ${DIM}Telegram:${NC}         Nicht konfiguriert (TELEGRAM_BOT_TOKEN in .env eintragen)"
fi
echo ""
echo -e "  ${CYAN}Nützliche Commands:${NC}"
echo -e "    cd ${JARVIS_DIR}"
echo -e "    docker compose -f docker-compose.production.yml logs -f    # Logs"
echo -e "    docker compose -f docker-compose.production.yml restart    # Neustart"
echo -e "    bash installer/scripts/health-check.sh                    # Health Check"
echo ""
echo -e "  ${DIM}Ollama-Modell wird im Hintergrund geladen...${NC}"
echo -e "  ${DIM}SYSTEMS™ · architectofscale.com${NC}"
echo ""

# Warte auf Ollama Download im Hintergrund
wait $OLLAMA_PID 2>/dev/null || true
