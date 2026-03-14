"""POST /generate endpoint.

Accepts a brand profile JSON, fetches Google Trends data, calls the Gemini
service with token budgeting, and returns a validated GenerateResponse.
"""
import logging
from typing import Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from postable_ia.schema.response import GenerateRequest, GenerateResponse
from postable_ia.services.gemini import TokenBudgetExceededError, generate_post
from postable_ia.services.trends import get_trends

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(brand: GenerateRequest) -> Union[GenerateResponse, JSONResponse]:
    """Generate a social media post for the given brand profile.

    Args:
        brand: Brand profile including niche, location, tone, and CTA channel.

    Returns:
        GenerateResponse with post_text, cta, hashtags, suggested_format,
        strategic_justification, and tokens_used.

    Raises:
        400: If the prompt exceeds the 1,500 input token budget.
        422: If the request body fails Pydantic validation.
    """
    geo = f"BR-{brand.state}"
    trends = get_trends(brand.niche, geo, "now 7-d")

    try:
        result = await generate_post(brand, trends)
    except TokenBudgetExceededError as exc:
        logger.warning(
            "Token budget exceeded for niche=%s state=%s: %d tokens",
            brand.niche,
            brand.state,
            exc.actual,
        )
        return JSONResponse(
            status_code=400,
            content={"error": "Token budget exceeded", "tokens": exc.actual},
        )

    return result
