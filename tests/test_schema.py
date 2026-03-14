"""Tests for GenerateRequest and GenerateResponse Pydantic schemas."""
import pytest
from pydantic import ValidationError
from postable_ia.schema.response import GenerateRequest, GenerateResponse


class TestGenerateRequest:
    def test_valid_request(self):
        req = GenerateRequest(
            niche="bakery",
            city="São Paulo",
            state="SP",
            tone_of_voice="casual",
            cta_channel="whatsapp",
        )
        assert req.niche == "bakery"
        assert req.state == "SP"
        assert req.tone_custom is None

    def test_valid_request_with_tone_custom(self):
        req = GenerateRequest(
            niche="gym",
            city="Rio de Janeiro",
            state="RJ",
            tone_of_voice="custom",
            tone_custom="energetic and bold",
            cta_channel="dm",
        )
        assert req.tone_custom == "energetic and bold"

    def test_missing_required_niche_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                city="São Paulo",
                state="SP",
                tone_of_voice="casual",
                cta_channel="whatsapp",
            )

    def test_missing_required_city_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                niche="bakery",
                state="SP",
                tone_of_voice="casual",
                cta_channel="whatsapp",
            )

    def test_missing_required_state_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                niche="bakery",
                city="São Paulo",
                tone_of_voice="casual",
                cta_channel="whatsapp",
            )

    def test_missing_required_tone_of_voice_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                niche="bakery",
                city="São Paulo",
                state="SP",
                cta_channel="whatsapp",
            )

    def test_missing_required_cta_channel_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                niche="bakery",
                city="São Paulo",
                state="SP",
                tone_of_voice="casual",
            )


class TestGenerateResponse:
    def test_valid_response(self):
        resp = GenerateResponse(
            post_text="Check out our fresh bread!",
            cta="Click the link below",
            hashtags=["#bakery", "#bread", "#fresh"],
            suggested_format="feed_post",
            strategic_justification="High local search volume for bakery",
            tokens_used=312,
        )
        assert resp.post_text == "Check out our fresh bread!"
        assert len(resp.hashtags) == 3
        assert resp.tokens_used == 312

    def test_missing_required_post_text_raises(self):
        with pytest.raises(ValidationError):
            GenerateResponse(
                cta="Click",
                hashtags=["#test"],
                suggested_format="feed_post",
                strategic_justification="trending",
                tokens_used=100,
            )

    def test_missing_required_hashtags_raises(self):
        with pytest.raises(ValidationError):
            GenerateResponse(
                post_text="Post",
                cta="Click",
                suggested_format="feed_post",
                strategic_justification="trending",
                tokens_used=100,
            )

    def test_hashtags_is_list(self):
        resp = GenerateResponse(
            post_text="Post",
            cta="Click",
            hashtags=["#a", "#b"],
            suggested_format="carousel",
            strategic_justification="trending",
            tokens_used=100,
        )
        assert isinstance(resp.hashtags, list)
