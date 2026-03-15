import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from postable_ia.tools import get_aspect_ratio


def test_instagram_feed_returns_4_5():
    assert get_aspect_ratio("instagram", "feed") == "4:5"


def test_instagram_carousel_returns_4_5():
    assert get_aspect_ratio("instagram", "carousel") == "4:5"


def test_instagram_story_returns_9_16():
    assert get_aspect_ratio("instagram", "story") == "9:16"


def test_instagram_reel_returns_9_16():
    assert get_aspect_ratio("instagram", "reel") == "9:16"


def test_instagram_none_placement_defaults_to_feed():
    assert get_aspect_ratio("instagram", None) == "4:5"


def test_facebook_feed_returns_1_91():
    assert get_aspect_ratio("facebook", "feed") == "1.91:1"


def test_facebook_story_returns_9_16():
    assert get_aspect_ratio("facebook", "story") == "9:16"


def test_linkedin_returns_1_91():
    assert get_aspect_ratio("linkedin", "post") == "1.91:1"


def test_x_returns_16_9():
    assert get_aspect_ratio("x", "post") == "16:9"


def test_unknown_platform_returns_1_1():
    assert get_aspect_ratio("unknown_platform", None) == "1:1"
