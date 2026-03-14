"""Tests for pytrends wrapper with TTL cache."""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
import pandas as pd


def _make_df():
    return pd.DataFrame({"keyword": [50, 60, 70]})


class TestTrendsCache:
    def setup_method(self):
        """Clear the cache before each test."""
        from postable_ia.services import trends as trends_module
        trends_module._cache.clear()

    def test_cache_hit(self):
        """Second call with same (keyword, geo, timeframe) returns cached result without calling pytrends."""
        with patch("postable_ia.services.trends.TrendReq") as mock_trend_req:
            mock_instance = MagicMock()
            mock_instance.interest_over_time.return_value = _make_df()
            mock_trend_req.return_value = mock_instance

            from postable_ia.services.trends import get_trends

            result1 = get_trends("padaria", "BR-SP", "now 7-d")
            result2 = get_trends("padaria", "BR-SP", "now 7-d")

            # TrendReq should only be instantiated once
            assert mock_trend_req.call_count == 1
            assert result1 == result2

    def test_cache_miss_different_args(self):
        """Different args each result in a separate pytrends call."""
        with patch("postable_ia.services.trends.TrendReq") as mock_trend_req:
            mock_instance = MagicMock()
            mock_instance.interest_over_time.return_value = _make_df()
            mock_trend_req.return_value = mock_instance

            from postable_ia.services.trends import get_trends

            get_trends("padaria", "BR-SP", "now 7-d")
            get_trends("academia", "BR-RJ", "now 7-d")

            assert mock_trend_req.call_count == 2

    def test_cache_expires_after_ttl(self):
        """Cache entry is ignored after TTL expires."""
        with patch("postable_ia.services.trends.TrendReq") as mock_trend_req:
            mock_instance = MagicMock()
            mock_instance.interest_over_time.return_value = _make_df()
            mock_trend_req.return_value = mock_instance

            from postable_ia.services import trends as trends_module
            from postable_ia.services.trends import get_trends

            # First call — populates cache
            get_trends("padaria", "BR-SP", "now 7-d")
            assert mock_trend_req.call_count == 1

            # Simulate cache expiry by backdating the cached_at timestamp
            key = ("padaria", "BR-SP", "now 7-d")
            result, cached_at = trends_module._cache[key]
            expired_at = cached_at - timedelta(hours=trends_module.TTL_HOURS + 1)
            trends_module._cache[key] = (result, expired_at)

            # Second call after TTL — should call pytrends again
            get_trends("padaria", "BR-SP", "now 7-d")
            assert mock_trend_req.call_count == 2

    def test_pytrends_error_returns_empty_dict(self):
        """If pytrends raises an exception, get_trends returns empty dict (graceful degradation)."""
        with patch("postable_ia.services.trends.TrendReq") as mock_trend_req:
            mock_trend_req.side_effect = Exception("429 Too Many Requests")

            from postable_ia.services.trends import get_trends

            result = get_trends("padaria", "BR-SP", "now 7-d")
            assert result == {}
