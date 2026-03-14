from __future__ import annotations

from collections import defaultdict
from typing import Any

from postable_ia.schema.competitor_gap import (
    CompetitorHandleStatus,
    CompetitorThemeSignal,
    GapCandidate,
)

VALID_STATUSES = {"active", "invalid", "private", "inactive", "replaced"}


def normalize_handle(handle: str) -> str:
    cleaned = (handle or "").strip().lstrip("@").lower()
    return f"@{cleaned}" if cleaned else ""


def _to_unit_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, parsed))


def _normalize_status(value: Any) -> str:
    candidate = str(value or "active").lower().strip()
    if candidate in VALID_STATUSES:
        return candidate
    return "invalid"


def build_gap_candidates(
    competitor_snapshots: list[dict[str, Any]] | None,
    *,
    locality_basis: str | None = None,
    locality_state_key: str | None = None,
) -> list[GapCandidate]:
    """Build deterministic gap candidates from competitor snapshots.

    This function intentionally preserves incoming locality metadata from the
    backend contract. It does not compute city-first locality.
    """
    snapshots = competitor_snapshots or []
    theme_values: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {
            "coverage": [],
            "trend_momentum": [],
            "brand_fit": [],
            "confidence": [],
            "novelty_penalty": [],
        }
    )
    active_handles: list[str] = []
    handle_statuses: dict[str, CompetitorHandleStatus] = {}

    resolved_basis = locality_basis
    resolved_state_key = locality_state_key

    for snapshot in snapshots:
        handle = normalize_handle(snapshot.get("handle", ""))
        status = _normalize_status(snapshot.get("status"))
        replacement = normalize_handle(snapshot.get("replacement_handle", ""))
        if handle and handle not in handle_statuses:
            handle_statuses[handle] = CompetitorHandleStatus(
                handle=handle,
                status=status,  # type: ignore[arg-type]
                replacement_handle=replacement or None,
            )

        if resolved_basis is None and snapshot.get("locality_basis"):
            resolved_basis = str(snapshot["locality_basis"])
        if resolved_state_key is None and snapshot.get("locality_state_key"):
            resolved_state_key = str(snapshot["locality_state_key"])

        if status != "active":
            continue

        if handle:
            active_handles.append(handle)

        themes = snapshot.get("themes", {}) or {}
        theme_signals = snapshot.get("theme_signals", {}) or {}
        for theme, coverage in themes.items():
            theme_name = str(theme).strip()
            if not theme_name:
                continue

            signal_values = theme_signals.get(theme_name, {})
            theme_values[theme_name]["coverage"].append(_to_unit_float(coverage))
            theme_values[theme_name]["trend_momentum"].append(
                _to_unit_float(signal_values.get("trend_momentum"), default=0.0)
            )
            theme_values[theme_name]["brand_fit"].append(
                _to_unit_float(signal_values.get("brand_fit"), default=0.5)
            )
            theme_values[theme_name]["confidence"].append(
                _to_unit_float(signal_values.get("confidence"), default=0.5)
            )
            theme_values[theme_name]["novelty_penalty"].append(
                max(float(signal_values.get("novelty_penalty", 0.0)), 0.0)
            )

    unique_handles = sorted(set(active_handles))
    statuses = [handle_statuses[key] for key in sorted(handle_statuses)]
    candidates: list[GapCandidate] = []
    for theme_name in sorted(theme_values):
        values = theme_values[theme_name]
        avg_coverage = sum(values["coverage"]) / len(values["coverage"])
        gap_strength = 1.0 - avg_coverage
        trend_momentum = sum(values["trend_momentum"]) / len(values["trend_momentum"])
        brand_fit = sum(values["brand_fit"]) / len(values["brand_fit"])
        confidence = sum(values["confidence"]) / len(values["confidence"])
        novelty_penalty = (
            sum(values["novelty_penalty"]) / len(values["novelty_penalty"])
        )

        candidates.append(
            GapCandidate(
                theme=theme_name,
                signal=CompetitorThemeSignal(
                    gap_strength=gap_strength,
                    trend_momentum=trend_momentum,
                    brand_fit=brand_fit,
                    confidence=confidence,
                    novelty_penalty=novelty_penalty,
                ),
                competitors_considered=unique_handles,
                competitor_statuses=statuses,
                locality_basis=resolved_basis,
                locality_state_key=resolved_state_key,
            )
        )

    return candidates
