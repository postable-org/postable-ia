FROM python:3.11-slim

# System dependencies (gcc needed for some Python packages, e.g. pytrends deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source only (no tests in the image)
COPY postable_ia/ ./postable_ia/

EXPOSE 8000

CMD ["uvicorn", "postable_ia.main:app", "--host", "0.0.0.0", "--port", "8000"]
