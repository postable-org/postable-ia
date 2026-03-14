"""FastAPI entrypoint for the Postable AI Agent service.

FastAPI owns the HTTP interface. The ADK agent loop (agent.py + tools.py)
handles internal generation when called from the generate service.
"""
from fastapi import FastAPI

from postable_ia.api.routes.generate import router as generate_router

app = FastAPI(
    title="Postable AI Agent",
    description="AI-powered social media post generation for Brazilian SMBs.",
    version="1.0.0",
)

app.include_router(generate_router)
