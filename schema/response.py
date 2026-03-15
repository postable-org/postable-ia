from pydantic import BaseModel


class GapAnalysis(BaseModel):
    theme_chosen: str
    competitors_analyzed: list[str]
    gaps_found: list[str]


class TrendData(BaseModel):
    keywords: list[str]
    region: str


class CreativeSpec(BaseModel):
    aspect_ratio: str
    style_notes: str
    alt_text: str


class GenerateResponse(BaseModel):
    post_text: str
    hashtags: list[str]
    image_base64: str
    image_mime_type: str
    placement: str = ""
    cta: str = ""
    creative_spec: CreativeSpec | None = None
    gap_analysis: GapAnalysis
    trend_data: TrendData
    brand_facts_used: list[str] = []
    sources: list[str] = []
    humanization_pass_notes: str = ""
    tokens_used: int
