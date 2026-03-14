"""Tests for POST /generate endpoint."""
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


def _base_payload() -> dict:
    return {
        "niche": "bakery",
        "city": "São Paulo",
        "state": "SP",
        "tone_of_voice": "casual",
        "cta_channel": "whatsapp",
    }


async def test_generate_includes_gap_analysis(client, mock_gemini, mock_trends):
    payload = _base_payload()
    payload["competitor_snapshots"] = [
        {
            "handle": "@RivalOne",
            "status": "active",
            "themes": {"delivery speed": 0.20},
            "theme_signals": {
                "delivery speed": {
                    "trend_momentum": 0.70,
                    "brand_fit": 0.82,
                    "confidence": 0.90,
                }
            },
        }
    ]

    response = await client.post("/generate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["competitor_gap_analysis"]["primary_gap_theme"] == "delivery speed"
    assert body["competitor_gap_analysis"]["selection_mode"] == "gap_first"
    assert body["competitor_gap_analysis"]["fallback_reason"] is None


async def test_fallback_mode_marks_no_strong_gap(client, mock_gemini, mock_trends):
    payload = _base_payload()
    payload["competitor_snapshots"] = [
        {
            "handle": "@RivalLow",
            "status": "active",
            "themes": {"generic tip": 0.60},
            "theme_signals": {
                "generic tip": {
                    "trend_momentum": 0.30,
                    "brand_fit": 0.50,
                    "confidence": 0.80,
                }
            },
        }
    ]

    response = await client.post("/generate", json=payload)
    assert response.status_code == 200
    analysis = response.json()["competitor_gap_analysis"]
    assert analysis["selection_mode"] == "trend_fallback"
    assert analysis["fallback_reason"] == "no_strong_gap_found"


async def test_token_budget_still_enforced(client, mock_trends):
    with patch("postable_ia.services.gemini.genai") as mock_genai:
        count_result = MagicMock()
        count_result.total_tokens = 1600
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = count_result
        mock_genai.GenerativeModel.return_value = mock_model

        payload = _base_payload()
        payload["competitor_snapshots"] = [
            {
                "handle": "@RivalOne",
                "status": "active",
                "themes": {"delivery speed": 0.20},
                "theme_signals": {
                    "delivery speed": {
                        "trend_momentum": 0.70,
                        "brand_fit": 0.82,
                        "confidence": 0.90,
                    }
                },
            }
        ]
        response = await client.post("/generate", json=payload)
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "Token budget exceeded"
        mock_model.generate_content.assert_not_called()
