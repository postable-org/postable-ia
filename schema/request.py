from typing import Literal
from pydantic import BaseModel


class BusinessProfile(BaseModel):
    niche: str
    city: str
    state: str
    tone: str
    brand_identity: str              # narrative summary (name + history)
    brand_name: str | None = None
    brand_tagline: str | None = None
    company_history: str | None = None
    brand_values: list[str] = []
    brand_key_people: list[str] = []
    brand_colors: list[str] = []     # e.g. ["#FF6B35", "#2D2D2D"]
    brand_fonts: list[str] = []
    design_style: str | None = None
    target_gender: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    target_audience_description: str | None = None
    brand_must_use: str | None = None
    brand_must_avoid: str | None = None


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
