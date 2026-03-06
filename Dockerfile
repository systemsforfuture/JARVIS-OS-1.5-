FROM python:3.12-slim

WORKDIR /app

# System-Pakete
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code
COPY core/ core/
COPY prompts/ prompts/
COPY skills/ skills/
COPY config/ config/
COPY main.py .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "main.py"]
