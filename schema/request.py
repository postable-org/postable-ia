from pydantic import BaseModel


class BusinessProfile(BaseModel):
    niche: str                # e.g. "padaria artesanal"
    city: str                 # e.g. "Curitiba"
    state: str                # e.g. "PR"
    tone: str                 # e.g. "friendly", "professional"
    brand_identity: str       # brief brand description


class CampaignBrief(BaseModel):
    goal: str                 # e.g. "increase foot traffic"
    target_audience: str
    cta_channel: str          # e.g. "whatsapp", "instagram_dm"
    theme_hint: str | None = None


class GenerateRequest(BaseModel):
    business_profile: BusinessProfile
    competitor_handles: list[str]   # e.g. ["@rival_bakery"]
    post_history: list[str]         # recent posts for style reference
    campaign_brief: CampaignBrief
