from pydantic import BaseModel


class GapAnalysis(BaseModel):
    theme_chosen: str
    competitors_analyzed: list[str]
    gaps_found: list[str]


class TrendData(BaseModel):
    keywords: list[str]
    region: str


class GenerateResponse(BaseModel):
    post_text: str
    hashtags: list[str]
    image_base64: str
    image_mime_type: str
    gap_analysis: GapAnalysis
    trend_data: TrendData
    tokens_used: int
