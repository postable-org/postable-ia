from typing import Literal
from pydantic import BaseModel


class BusinessProfile(BaseModel):
    niche: str
    city: str
    state: str
    tone: str
    brand_identity: str


class CampaignBrief(BaseModel):
    goal: str
    target_audience: str
    cta_channel: str
    theme_hint: str | None = None


class GenerateRequest(BaseModel):
    business_profile: BusinessProfile
    competitor_handles: list[str]
    post_history: list[str]
    campaign_brief: CampaignBrief
    platform: Literal["instagram", "facebook", "linkedin", "x"] = "instagram"
    placement: str | None = None   # feed, story, reel, carousel, thread, post
    objective: str | None = None   # leads, awareness, community, hiring, event
