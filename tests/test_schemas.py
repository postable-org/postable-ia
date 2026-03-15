import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from pydantic import ValidationError
from schema.request import GenerateRequest


def _base_payload(**overrides) -> dict:
    return {
        "business_profile": {
            "niche": "padaria",
            "city": "Curitiba",
            "state": "PR",
            "tone": "friendly",
            "brand_identity": "Padaria artesanal do bairro",
        },
        "competitor_handles": [],
        "post_history": [],
        "campaign_brief": {
            "goal": "",
            "target_audience": "",
            "cta_channel": "whatsapp",
            "theme_hint": None,
        },
        **overrides,
    }


def test_default_platform_is_instagram():
    req = GenerateRequest(**_base_payload())
    assert req.platform == "instagram"


def test_platform_can_be_linkedin():
    req = GenerateRequest(**_base_payload(platform="linkedin"))
    assert req.platform == "linkedin"


def test_invalid_platform_raises_validation_error():
    with pytest.raises(ValidationError):
        GenerateRequest(**_base_payload(platform="tiktok"))


def test_placement_defaults_to_none():
    req = GenerateRequest(**_base_payload())
    assert req.placement is None


def test_placement_can_be_story():
    req = GenerateRequest(**_base_payload(placement="story"))
    assert req.placement == "story"


def test_objective_defaults_to_none():
    req = GenerateRequest(**_base_payload())
    assert req.objective is None


from schema.response import GenerateResponse, CreativeSpec


def test_creative_spec_fields():
    spec = CreativeSpec(aspect_ratio="4:5", style_notes="warm tones", alt_text="padaria")
    assert spec.aspect_ratio == "4:5"


def test_response_new_fields_have_defaults():
    resp = GenerateResponse(
        post_text="Olá",
        hashtags=[],
        image_base64="abc",
        image_mime_type="image/jpeg",
        gap_analysis={"theme_chosen": "x", "competitors_analyzed": [], "gaps_found": []},
        trend_data={"keywords": [], "region": "BR-PR"},
        tokens_used=100,
    )
    assert resp.placement == ""
    assert resp.cta == ""
    assert resp.brand_facts_used == []
    assert resp.sources == []
    assert resp.humanization_pass_notes == ""
    assert resp.creative_spec is None


def test_response_accepts_creative_spec():
    resp = GenerateResponse(
        post_text="Olá",
        hashtags=[],
        image_base64="abc",
        image_mime_type="image/jpeg",
        gap_analysis={"theme_chosen": "x", "competitors_analyzed": [], "gaps_found": []},
        trend_data={"keywords": [], "region": "BR-PR"},
        tokens_used=100,
        creative_spec={"aspect_ratio": "4:5", "style_notes": "warm", "alt_text": "bread"},
    )
    assert resp.creative_spec.aspect_ratio == "4:5"
