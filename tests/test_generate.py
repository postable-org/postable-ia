"""Tests for POST /generate endpoint."""
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.asyncio


async def test_generate_success(client, mock_gemini, mock_trends):
    """Valid request returns 200 with all GenerateResponse fields."""
    payload = {
        "niche": "bakery",
        "city": "São Paulo",
        "state": "SP",
        "tone_of_voice": "casual",
        "cta_channel": "whatsapp",
    }
    response = await client.post("/generate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "post_text" in body
    assert "cta" in body
    assert "hashtags" in body
    assert isinstance(body["hashtags"], list)
    assert "suggested_format" in body
    assert "strategic_justification" in body
    assert "tokens_used" in body


async def test_token_budget_exceeded(client, mock_trends):
    """When token count exceeds 1500 the endpoint returns 400 without calling Gemini."""
    with patch("postable_ia.services.gemini.genai") as mock_genai:
        count_result = MagicMock()
        count_result.total_tokens = 1600
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = count_result
        mock_genai.GenerativeModel.return_value = mock_model

        payload = {
            "niche": "bakery",
            "city": "São Paulo",
            "state": "SP",
            "tone_of_voice": "casual",
            "cta_channel": "whatsapp",
        }
        response = await client.post("/generate", json=payload)
        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        # generate_content should NOT have been called
        mock_model.generate_content.assert_not_called()


async def test_generate_missing_required_field(client):
    """Request missing required field returns 422."""
    payload = {
        "city": "São Paulo",
        "state": "SP",
        "tone_of_voice": "casual",
        "cta_channel": "whatsapp",
        # missing niche
    }
    response = await client.post("/generate", json=payload)
    assert response.status_code == 422
