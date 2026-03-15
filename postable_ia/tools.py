"""Custom tool functions for the Postable agent.

Each plain Python function passed to Agent.tools becomes a callable tool the
agent can invoke during a conversation. ADK automatically generates the tool
schema from the function signature and docstring, so keep them descriptive.
"""

import base64
import time
from typing import Any

from pytrends.request import TrendReq

from .config import settings

# ---------------------------------------------------------------------------
# In-memory cache for trends: key=(niche, state), value=(timestamp, data)
# ---------------------------------------------------------------------------
_trends_cache: dict[tuple[str, str], tuple[float, dict]] = {}


def fetch_trends(niche: str, state: str) -> dict[str, Any]:
    """Fetch Google Trends data for the business niche and Brazilian state.

    Queries pytrends for the past 7 days, filtered to the given state in Brazil.
    Results are cached in memory for `settings.trends_cache_ttl_hours` hours.

    Args:
        niche: The business niche keyword, e.g. "padaria artesanal".
        state: The two-letter Brazilian state code, e.g. "PR".

    Returns:
        A dict with keys:
            - keywords (list[str]): related queries found
            - region (str): geo code used, e.g. "BR-PR"
            - interest (dict): raw interest-over-time data
    """
    cache_key = (niche, state)
    ttl_seconds = settings.trends_cache_ttl_hours * 3600
    now = time.time()

    cached = _trends_cache.get(cache_key)
    if cached and (now - cached[0]) < ttl_seconds:
        return cached[1]

    geo = f"BR-{state}"
    pytrends = TrendReq(hl="pt-BR", tz=180)
    pytrends.build_payload([niche], timeframe="now 7-d", geo=geo)

    interest_df = pytrends.interest_over_time()
    interest_summary: dict = {}
    if not interest_df.empty and niche in interest_df.columns:
        series = interest_df[niche]
        interest_summary = {
            "max": int(series.max()),
            "mean": round(float(series.mean()), 1),
            "trend": "up" if series.iloc[-1] > series.iloc[0] else "down",
        }

    related = pytrends.related_queries()
    keywords: list[str] = []
    if niche in related and related[niche].get("top") is not None:
        top_df = related[niche]["top"]
        keywords = top_df["query"].tolist()[:10]

    result: dict[str, Any] = {
        "keywords": keywords,
        "region": geo,
        "interest": interest_summary,
    }
    _trends_cache[cache_key] = (now, result)
    return result


def generate_image(prompt: str, style: str = "vibrant") -> dict[str, Any]:
    """Generate a social media post image using Gemini's image generation model.

    Args:
        prompt: Descriptive prompt for the image, in Portuguese or English.
        style: Visual style hint, e.g. "vibrant", "minimalist", "rustic".

    Returns:
        A dict with keys:
            - image_base64 (str): base64-encoded image bytes
            - mime_type (str): MIME type, e.g. "image/png"
    """
    import google.generativeai as genai  # type: ignore[import]

    full_prompt = f"{prompt}. Style: {style}. High quality, social media ready."

    model = genai.GenerativeModel(settings.image_model)
    response = model.generate_content(
        full_prompt,
        generation_config={"response_modalities": ["IMAGE"]},
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            mime_type = part.inline_data.mime_type
            return {
                "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
                "mime_type": mime_type,
            }

    return {"image_base64": "", "mime_type": "image/png"}
