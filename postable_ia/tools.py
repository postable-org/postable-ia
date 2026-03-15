"""Custom tool functions for the Postable agent.

Each plain Python function passed to Agent.tools becomes a callable tool the
agent can invoke during a conversation. ADK automatically generates the tool
schema from the function signature and docstring, so keep them descriptive.
"""

import base64
import logging
import time
import uuid
from typing import Any
from google import genai
from google.genai import types

from pytrends.request import TrendReq

from .config import settings

logger = logging.getLogger(__name__)


class ImageGenerationError(RuntimeError):
    """Raised when generate_image exhausts all retry attempts."""


# ---------------------------------------------------------------------------
# In-memory image store: the LLM cannot reliably repeat a ~1 MB base64 string
# in its text output. We store the real bytes here, keyed by a short ref token,
# and let the route layer resolve the token after the agent finishes.
# ---------------------------------------------------------------------------
_image_store: dict[str, dict] = {}

_IMG_REF_PREFIX = "img_ref:"


def resolve_image_ref(ref: str) -> dict | None:
    """Look up and remove an image ref from the store. Returns None if not found."""
    return _image_store.pop(ref, None)


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
    try:
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
    except Exception as e:
        logger.warning("fetch_trends failed for %s/%s: %s", niche, state, e)
        return {"keywords": [], "region": geo, "interest": {}, "error": str(e)}


_VALID_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _build_image_prompt(prompt: str, style: str) -> str:
    return (
        f"{prompt}. "
        f"Visual style: {style}. "
        "Composition: centered subject, clean background, strong contrast. "
        "Mood: warm, inviting, professional. "
        "Lighting: natural soft light. "
        "Aspect ratio: 1:1 square. "
        "Platform: Instagram/Facebook feed post. "
        "Quality: photorealistic or illustrative as appropriate, "
        "no watermarks, no text overlays, no logos unless described."
    )


def _parse_image_response(response: Any) -> "tuple[bytes, str] | None":
    for part in response.parts:
        if part.inline_data and part.inline_data.data:
            raw: bytes = part.inline_data.data
            mime_type: str = part.inline_data.mime_type or "image/png"
            return raw, mime_type
    return None


def _validate_image_output(image_base64: str, mime_type: str) -> None:
    if not image_base64:
        raise ImageGenerationError("image_base64 is empty")
    if mime_type not in _VALID_MIME_TYPES:
        raise ImageGenerationError(f"Unexpected mime_type: {mime_type!r}")
    try:
        decoded = base64.b64decode(image_base64, validate=True)
    except Exception as exc:
        raise ImageGenerationError("image_base64 is not valid base64") from exc
    if len(decoded) < 100:
        raise ImageGenerationError(
            f"Decoded image is suspiciously small: {len(decoded)} bytes"
        )


def _call_with_retry(fn, max_attempts: int, backoff_seconds: float, *args, **kwargs):
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts:
                logger.warning(
                    "generate_image attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt,
                    max_attempts,
                    exc,
                    backoff_seconds * attempt,
                )
                time.sleep(backoff_seconds * attempt)
            else:
                logger.error(
                    "generate_image attempt %d/%d failed: %s — no more retries",
                    attempt,
                    max_attempts,
                    exc,
                )
    raise ImageGenerationError(
        f"generate_image failed after {max_attempts} attempts"
    ) from last_exc


def generate_image(prompt: str, style: str = "vibrant") -> dict[str, Any]:
    """Generate a social media post image using Gemini.

    Returns:
        {
            "image_base64": str,
            "image_mime_type": str,
        }

    Raises:
        ImageGenerationError: if all retry attempts are exhausted without a valid image.
    """
    full_prompt = _build_image_prompt(prompt, style)
    logger.info(
        "generate_image: model=%s style=%r prompt_length=%d",
        settings.image_model,
        style,
        len(full_prompt),
    )

    def _attempt() -> dict[str, Any]:
        client = genai.Client()
        response = client.models.generate_content(
            model=settings.image_model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    image_size="2K",
                    aspect_ratio="1:1",
                ),
            ),
        )

        parsed = _parse_image_response(response)
        if parsed is None:
            finish_reasons = [
                getattr(c, "finish_reason", None)
                for c in getattr(response, "candidates", [])
            ]
            raise ImageGenerationError(
                f"No image part in response. finish_reasons={finish_reasons}"
            )

        image_bytes, mime_type = parsed
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        _validate_image_output(image_base64, mime_type)

        # Store the real base64 out-of-band so the LLM never has to repeat it.
        ref = f"{_IMG_REF_PREFIX}{uuid.uuid4().hex}"
        _image_store[ref] = {"image_base64": image_base64, "image_mime_type": mime_type}
        logger.info(
            "generate_image: stored ref=%s mime_type=%s encoded_size=%d",
            ref,
            mime_type,
            len(image_base64),
        )
        # Return the short ref — the route layer will resolve this to real bytes.
        return {"image_base64": ref, "image_mime_type": mime_type}

    return _call_with_retry(
        _attempt,
        settings.image_max_retries,
        settings.image_retry_backoff_seconds,
    )