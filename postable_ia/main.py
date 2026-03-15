"""FastAPI entrypoint for the Postable AI Agent service.

FastAPI owns the HTTP interface. The ADK agent loop (agent.py + tools.py)
handles internal generation when called from the generate service.
"""
from dotenv import load_dotenv
load_dotenv()  # populates os.environ from .env — must run before google-adk imports

# Patch google-genai BaseApiClient.aclose to guard against partially-initialized
# clients being GC'd. Some internal ADK clients (e.g. GoogleSearchAgentTool)
# can reach __del__ without _async_httpx_client ever being set, causing
# "Task exception was never retrieved" noise on every request.
from google.genai import _api_client as _genai_api_client

_orig_aclose = _genai_api_client.BaseApiClient.aclose


async def _safe_aclose(self):
    if hasattr(self, "_async_httpx_client"):
        await _orig_aclose(self)


_genai_api_client.BaseApiClient.aclose = _safe_aclose

from fastapi import FastAPI

from api.routes.generate import router as generate_router

app = FastAPI(
    title="Postable AI Agent",
    description="AI-powered social media post generation for Brazilian SMBs.",
    version="1.0.0",
)

app.include_router(generate_router)
