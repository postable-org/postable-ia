"""pytrends wrapper with in-memory TTL cache.

Cache key: (keyword, geo, timeframe)
Cache value: (result_dict, cached_at: datetime)
TTL: settings.trends_cache_ttl_hours (default 5 hours)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from pytrends.request import TrendReq

from postable_ia.config import settings

logger = logging.getLogger(__name__)

TTL_HOURS: int = settings.trends_cache_ttl_hours

# In-memory cache: {(keyword, geo, timeframe): (result, cached_at)}
_cache: dict[tuple, tuple[Any, datetime]] = {}


def get_trends(keyword: str, geo: str, timeframe: str) -> dict:
    """Fetch Google Trends data with in-memory TTL caching.

    Args:
        keyword: Search term (e.g. "padaria").
        geo: Geographic restriction (e.g. "BR-SP").
        timeframe: Time window (e.g. "now 7-d").

    Returns:
        Dictionary of interest-over-time data, or empty dict on error.
    """
    cache_key = (keyword, geo, timeframe)

    # Check cache hit
    if cache_key in _cache:
        result, cached_at = _cache[cache_key]
        age = datetime.utcnow() - cached_at
        if age < timedelta(hours=TTL_HOURS):
            logger.debug("Cache HIT for key %s", cache_key)
            return result

    # Cache miss or expired — call pytrends
    try:
        pytrends = TrendReq(hl="pt-BR", tz=180)
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)
        df = pytrends.interest_over_time()
        # Use df.to_json() + json.loads so Timestamp index keys become strings
        result = json.loads(df.to_json()) if df is not None and not df.empty else {}
        _cache[cache_key] = (result, datetime.utcnow())
        logger.debug("Cache MISS for key %s — fetched from pytrends", cache_key)
        return result
    except Exception as exc:
        logger.warning("pytrends error for key %s: %s", cache_key, exc)
        return {}
