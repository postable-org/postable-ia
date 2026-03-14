import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch


@pytest.fixture
async def client():
    from postable_ia.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_gemini():
    """Mock Gemini to return a fixed structured response and a safe token count."""
    with patch("postable_ia.services.gemini.genai") as mock:
        count_result = MagicMock()
        count_result.total_tokens = 300
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = count_result
        mock_model.generate_content.return_value.text = (
            '{"post_text":"Test post","cta":"Click here","hashtags":["#test"],'
            '"suggested_format":"feed_post","strategic_justification":"trending","tokens_used":300}'
        )
        mock.GenerativeModel.return_value = mock_model
        yield mock


@pytest.fixture
def mock_trends():
    """Mock pytrends to return fixture data."""
    with patch("postable_ia.services.trends.TrendReq") as mock:
        import pandas as pd
        df = pd.DataFrame({"test_keyword": [50, 60, 70]})
        mock.return_value.interest_over_time.return_value = df
        yield mock
