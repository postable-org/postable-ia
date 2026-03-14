from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from postable_ia.schema.competitor_gap import CompetitorGapAnalysis, GapCandidate, KeySignals

BRAND_FIT_GATE = 0.45
CONFIDENCE_GATE = 0.40
MIN_GAP_SCORE = 0.50
ROTATION_DELTA = 0.10


@dataclass
class ThemeSelectionResult:
    selected_theme: str
    selection_mode: str
    fallback_reason: Optional[str]
    analysis: CompetitorGapAnalysis
    score_breakdown: dict[str, dict[str, Any]]


def _weighted_score(candidate: GapCandidate) -> float:
    signal = candidate.signal
    return (
        0.55 * signal.gap_strength
        + 0.25 * signal.trend_momentum
        + 0.20 * signal.brand_fit
        - signal.novelty_penalty
    )


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.50:
        return "medium"
    return "low"


def _fallback_analysis(selected_theme: str, candidates: list[GapCandidate]) -> CompetitorGapAnalysis:
    source = candidates[0] if candidates else None
    signal = source.signal if source else None
    competitors = source.competitors_considered if source else []
    return CompetitorGapAnalysis(
        primary_gap_theme=selected_theme,
        selection_mode="trend_fallback",
        why_now_summary=(
            "No strong competitor gap met quality gates, so trend momentum was used "
            "as the primary selection signal."
        ),
        competitors_considered=competitors,
        key_signals=KeySignals(
            gap_strength=signal.gap_strength if signal else 0.0,
            trend_momentum=signal.trend_momentum if signal else 0.0,
            brand_fit=signal.brand_fit if signal else 0.0,
        ),
        confidence_band=_confidence_band(signal.confidence if signal else 0.0),  # type: ignore[arg-type]
        fallback_reason="no_strong_gap_found",
    )


def select_primary_theme(
    candidates: list[GapCandidate],
    *,
    previous_primary_theme: str | None = None,
) -> ThemeSelectionResult:
    """Select the primary theme with deterministic scoring and policy gates."""
    score_breakdown: dict[str, dict[str, Any]] = {}
    eligible: list[tuple[GapCandidate, float]] = []

    ordered = sorted(candidates, key=lambda candidate: candidate.theme)
    for candidate in ordered:
        score = _weighted_score(candidate)
        signal = candidate.signal
        gate_reason = None
        if signal.brand_fit < BRAND_FIT_GATE:
            gate_reason = "brand_fit_gate"
        elif signal.confidence < CONFIDENCE_GATE:
            gate_reason = "confidence_gate"
        else:
            eligible.append((candidate, score))

        score_breakdown[candidate.theme] = {
            "gap_strength": signal.gap_strength,
            "trend_momentum": signal.trend_momentum,
            "brand_fit": signal.brand_fit,
            "confidence": signal.confidence,
            "novelty_penalty": signal.novelty_penalty,
            "weighted_score": score,
            "eligible": gate_reason is None,
            "gate_reason": gate_reason,
        }

    if not eligible:
        best_trend = max(
            ordered,
            key=lambda candidate: (candidate.signal.trend_momentum, candidate.theme),
            default=None,
        )
        selected_theme = best_trend.theme if best_trend else "trend_opportunity"
        analysis = _fallback_analysis(selected_theme, ordered)
        return ThemeSelectionResult(
            selected_theme=selected_theme,
            selection_mode="trend_fallback",
            fallback_reason="no_strong_gap_found",
            analysis=analysis,
            score_breakdown=score_breakdown,
        )

    eligible.sort(key=lambda item: (-item[1], item[0].theme))
    selected_candidate, selected_score = eligible[0]

    if (
        previous_primary_theme
        and selected_candidate.theme == previous_primary_theme
        and len(eligible) > 1
    ):
        next_candidate, next_score = eligible[1]
        if selected_score - next_score < ROTATION_DELTA:
            selected_candidate = next_candidate
            selected_score = next_score

    if selected_score < MIN_GAP_SCORE:
        trend_sorted = sorted(
            eligible,
            key=lambda item: (-item[0].signal.trend_momentum, item[0].theme),
        )
        selected_theme = trend_sorted[0][0].theme
        analysis = _fallback_analysis(selected_theme, [item[0] for item in trend_sorted])
        return ThemeSelectionResult(
            selected_theme=selected_theme,
            selection_mode="trend_fallback",
            fallback_reason="no_strong_gap_found",
            analysis=analysis,
            score_breakdown=score_breakdown,
        )

    signal = selected_candidate.signal
    analysis = CompetitorGapAnalysis(
        primary_gap_theme=selected_candidate.theme,
        selection_mode="gap_first",
        why_now_summary=(
            f"The '{selected_candidate.theme}' theme has the strongest weighted gap "
            "signal right now."
        ),
        competitors_considered=selected_candidate.competitors_considered,
        key_signals=KeySignals(
            gap_strength=signal.gap_strength,
            trend_momentum=signal.trend_momentum,
            brand_fit=signal.brand_fit,
        ),
        confidence_band=_confidence_band(signal.confidence),  # type: ignore[arg-type]
        fallback_reason=None,
    )

    return ThemeSelectionResult(
        selected_theme=selected_candidate.theme,
        selection_mode="gap_first",
        fallback_reason=None,
        analysis=analysis,
        score_breakdown=score_breakdown,
    )
