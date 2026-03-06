#!/bin/bash
# ═══════════════════════════════════════════════════════════
# JARVIS 1.5 — Ollama Model Initialization
# SYSTEMS™ · architectofscale.com
#
# Runs after Ollama container starts.
# Pulls required models for JARVIS cron jobs and routing.
# ═══════════════════════════════════════════════════════════

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "═══════════════════════════════════════"
echo "  JARVIS — Ollama Model Init"
echo "═══════════════════════════════════════"

# Wait for Ollama to be ready
echo "Waiting for Ollama at ${OLLAMA_HOST}..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "ERROR: Ollama not reachable after ${MAX_RETRIES} retries. Exiting."
        exit 1
    fi
    echo "  Attempt $i/$MAX_RETRIES — waiting ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

# Models to pull (used by JARVIS cron jobs and SmartRouter)
MODELS=(
    "llama3.1:8b"      # Lightweight — cron jobs, quick tasks
    "qwen2.5:7b"       # General purpose — fallback
)

# Optional: pull larger models if GPU available
# "llama3.1:70b"      # Full power — quality routing
# "qwen2.5-coder:32b" # Code tasks

for MODEL in "${MODELS[@]}"; do
    echo ""
    echo "Checking model: ${MODEL}..."

    # Check if model already exists
    if curl -sf "${OLLAMA_HOST}/api/tags" | grep -q "\"${MODEL}\""; then
        echo "  Already pulled. Skipping."
        continue
    fi

    echo "  Pulling ${MODEL}... (this may take a while)"
    curl -sf "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${MODEL}\"}" | while read -r line; do
        STATUS=$(echo "$line" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$STATUS" ]; then
            printf "\r  %s" "$STATUS"
        fi
    done
    echo ""
    echo "  Done: ${MODEL}"
done

echo ""
echo "═══════════════════════════════════════"
echo "  All models ready!"
echo "═══════════════════════════════════════"
