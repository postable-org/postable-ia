# ── Stage: runtime ────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System dependencies (gcc needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY postable_ia/ ./postable_ia/

# ADK API server listens on 8000 by default
EXPOSE 8000

# Run the ADK API server (REST + WebSocket interface)
CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "postable_ia"]
