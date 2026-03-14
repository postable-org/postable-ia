"""Gemini wrapper with token budgeting.

Raises TokenBudgetExceededError if the prompt exceeds TOKEN_BUDGET before
any generate_content call is made — no wasted API calls.
"""
import json
import logging

from postable_ia.config import settings
from postable_ia.schema.response import GenerateRequest, GenerateResponse

# Lazily imported so tests can patch 'postable_ia.services.gemini.genai'
# without requiring the real library to be installed.
try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

logger = logging.getLogger(__name__)

TOKEN_BUDGET: int = 1500


class TokenBudgetExceededError(Exception):
    """Raised when the prompt token count exceeds TOKEN_BUDGET."""

    def __init__(self, actual: int, budget: int = TOKEN_BUDGET):
        self.actual = actual
        self.budget = budget
        super().__init__(
            f"Token budget exceeded: {actual} tokens > {budget} allowed"
        )


def _build_prompt(brand: GenerateRequest, trends: dict) -> str:
    """Assemble the 3-layer prompt: trends context + brand identity + output spec."""
    trend_summary = json.dumps(trends, ensure_ascii=False) if trends else "{}"

    tone_desc = brand.tone_custom if brand.tone_custom else brand.tone_of_voice

    cta_instructions = {
        "whatsapp": "include a WhatsApp link or 'manda mensagem' call to action",
        "landing_page": "direct the audience to click the link in bio / landing page",
        "dm": "invite the audience to send a direct message",
    }.get(brand.cta_channel, "include a relevant call to action")

    prompt = f"""You are an expert social media copywriter for Brazilian small businesses.

## Trend Context
Current Google Trends data for this niche in the region:
{trend_summary}

## Brand Identity
- Niche: {brand.niche}
- City: {brand.city}
- State: {brand.state}
- Tone of voice: {tone_desc}
- CTA channel: {cta_instructions}

## Task
Write a high-performing Instagram post for this brand. Use the trend data to make the post
timely and relevant. Respond ONLY with a valid JSON object — no markdown fences, no preamble.

Required JSON structure:
{{
  "post_text": "<the full Instagram caption, written in Brazilian Portuguese>",
  "cta": "<the specific call-to-action line>",
  "hashtags": ["<hashtag1>", "<hashtag2>", "<hashtag3>"],
  "suggested_format": "<one of: carousel | feed_post | story>",
  "strategic_justification": "<1-2 sentences explaining why this post will perform well>",
  "tokens_used": 0
}}
"""
    return prompt


async def generate_post(brand: GenerateRequest, trends: dict) -> GenerateResponse:
    """Generate a social media post using Gemini 2.5 Flash.

    Args:
        brand: Validated brand profile from the request.
        trends: Trend data from pytrends (may be empty dict).

    Returns:
        Validated GenerateResponse Pydantic model.

    Raises:
        TokenBudgetExceededError: If the prompt exceeds TOKEN_BUDGET tokens.
        ValueError: If the model returns unparseable JSON.
    """
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = _build_prompt(brand, trends)

    # Count tokens BEFORE calling generate_content
    token_count_result = model.count_tokens(prompt)
    actual_tokens: int = token_count_result.total_tokens

    if actual_tokens > TOKEN_BUDGET:
        raise TokenBudgetExceededError(actual=actual_tokens)

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    raw_text = response.text.strip()
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned non-JSON response: {raw_text[:200]}") from exc

    # Inject the actual token count (overrides any placeholder from the model)
    data["tokens_used"] = actual_tokens

    return GenerateResponse(**data)
