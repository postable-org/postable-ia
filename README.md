# postable-ia

AI agent service for [Postable](../), built with [Google ADK](https://google.github.io/adk-docs/) (Python) and Docker.

---

## Project structure

```
postable-ia/
├── postable_ia/          # ADK agent package
│   ├── __init__.py
│   ├── agent.py          # Root agent (model, instructions, tools)
│   └── tools.py          # Custom tool functions
├── .env.example          # Environment variable template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.11 |
| Docker Desktop | 4.x |
| Google API Key | — |

---

## Quick start

### 1 — Configure environment

```bash
cp .env.example .env
# Open .env and set GOOGLE_API_KEY=<your key>
```

### 2a — Run with Docker Compose (recommended)

```bash
docker compose up --build
```

Open **http://localhost:8000** in your browser to access the ADK web UI.

### 2b — Run locally (no Docker)

```bash
# Create venv and install deps (uv handles both in one step)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

adk web postable_ia
```

Open **http://localhost:8000**.

---

## Customising the agent

| What | Where |
|---|---|
| Change model | `postable_ia/agent.py` → `model=` |
| Change system prompt | `postable_ia/agent.py` → `instruction=` |
| Add tools | `postable_ia/tools.py` → add functions, then list them in `agent.py` |

---

## Using Vertex AI instead of AI Studio

In `.env`:

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1
# Remove GOOGLE_API_KEY
```

Make sure your local gcloud credentials are configured:

```bash
gcloud auth application-default login
```

---

## Deploying to Cloud Run

```bash
# Build & push image
gcloud builds submit --tag gcr.io/<PROJECT_ID>/postable-ia

# Deploy
gcloud run deploy postable-ia \
  --image gcr.io/<PROJECT_ID>/postable-ia \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=<key>
```
