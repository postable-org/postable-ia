from pydantic import BaseModel, Field
from typing import Optional

from postable_ia.schema.competitor_gap import CompetitorGapAnalysis

class GenerateRequest(BaseModel):
    niche: str
    city: str
    state: str  # 2-char BR state code
    tone_of_voice: str
    tone_custom: Optional[str] = None
    cta_channel: str  # "whatsapp" | "landing_page" | "dm"
    competitor_snapshots: list[dict] = Field(default_factory=list)
    locality_basis: Optional[str] = None
    locality_state_key: Optional[str] = None
    previous_primary_theme: Optional[str] = None


class GenerateResponse(BaseModel):
    post_text: str
    cta: str
    hashtags: list[str]
    suggested_format: str  # "carousel" | "feed_post" | "story"
    strategic_justification: str
    tokens_used: int
    competitor_gap_analysis: Optional[CompetitorGapAnalysis] = None
