from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    niche: str
    city: str
    state: str  # 2-char BR state code
    tone_of_voice: str
    tone_custom: Optional[str] = None
    cta_channel: str  # "whatsapp" | "landing_page" | "dm"


class GenerateResponse(BaseModel):
    post_text: str
    cta: str
    hashtags: list[str]
    suggested_format: str  # "carousel" | "feed_post" | "story"
    strategic_justification: str
    tokens_used: int
