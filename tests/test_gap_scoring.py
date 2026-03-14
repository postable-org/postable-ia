from postable_ia.schema.competitor_gap import CompetitorThemeSignal, GapCandidate
from postable_ia.services.gap_scoring import select_primary_theme


def _candidate(
    theme: str,
    *,
    gap_strength: float,
    trend_momentum: float,
    brand_fit: float,
    confidence: float = 0.8,
    novelty_penalty: float = 0.0,
) -> GapCandidate:
    return GapCandidate(
        theme=theme,
        signal=CompetitorThemeSignal(
            gap_strength=gap_strength,
            trend_momentum=trend_momentum,
            brand_fit=brand_fit,
            confidence=confidence,
            novelty_penalty=novelty_penalty,
        ),
        competitors_considered=["@rivalone", "@rivaltwo"],
    )


def test_weighted_selection():
    result = select_primary_theme(
        [
            _candidate(
                "delivery speed",
                gap_strength=0.80,
                trend_momentum=0.60,
                brand_fit=0.70,
            ),
            _candidate(
                "healthy menu",
                gap_strength=0.60,
                trend_momentum=0.70,
                brand_fit=0.80,
            ),
        ]
    )

    assert result.selection_mode == "gap_first"
    assert result.selected_theme == "delivery speed"
    assert round(result.score_breakdown["delivery speed"]["weighted_score"], 3) == 0.730


def test_brand_fit_gate():
    result = select_primary_theme(
        [
            _candidate(
                "aggressive promo",
                gap_strength=0.95,
                trend_momentum=0.80,
                brand_fit=0.40,
                confidence=0.95,
            ),
            _candidate(
                "local quality",
                gap_strength=0.70,
                trend_momentum=0.60,
                brand_fit=0.60,
                confidence=0.80,
            ),
        ]
    )

    assert result.selected_theme == "local quality"
    assert result.score_breakdown["aggressive promo"]["eligible"] is False
    assert result.score_breakdown["aggressive promo"]["gate_reason"] == "brand_fit_gate"


def test_trend_fallback():
    result = select_primary_theme(
        [
            _candidate(
                "low-signal idea",
                gap_strength=0.40,
                trend_momentum=0.30,
                brand_fit=0.50,
                confidence=0.80,
            )
        ]
    )

    assert result.selection_mode == "trend_fallback"
    assert result.fallback_reason == "no_strong_gap_found"
    assert result.analysis.fallback_reason == "no_strong_gap_found"


def test_soft_rotation():
    result = select_primary_theme(
        [
            _candidate(
                "repeat theme",
                gap_strength=0.80,
                trend_momentum=0.60,
                brand_fit=0.70,
            ),
            _candidate(
                "fresh angle",
                gap_strength=0.60,
                trend_momentum=0.70,
                brand_fit=0.80,
            ),
        ],
        previous_primary_theme="repeat theme",
    )

    assert result.selection_mode == "gap_first"
    assert result.selected_theme == "fresh angle"
