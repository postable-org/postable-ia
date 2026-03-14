from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

CompetitorStatus = Literal["active", "invalid", "private", "inactive", "replaced"]
SelectionMode = Literal["gap_first", "trend_fallback"]
ConfidenceBand = Literal["high", "medium", "low"]


class CompetitorThemeSignal(BaseModel):
    gap_strength: float = Field(ge=0.0, le=1.0)
    trend_momentum: float = Field(ge=0.0, le=1.0)
    brand_fit: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    novelty_penalty: float = Field(default=0.0, ge=0.0)


class CompetitorHandleStatus(BaseModel):
    handle: str
    status: CompetitorStatus
    replacement_handle: Optional[str] = None


class GapCandidate(BaseModel):
    theme: str
    signal: CompetitorThemeSignal
    competitors_considered: list[str] = Field(default_factory=list)
    competitor_statuses: list[CompetitorHandleStatus] = Field(default_factory=list)
    locality_basis: Optional[str] = None
    locality_state_key: Optional[str] = None


class KeySignals(BaseModel):
    gap_strength: float = Field(ge=0.0, le=1.0)
    trend_momentum: float = Field(ge=0.0, le=1.0)
    brand_fit: float = Field(ge=0.0, le=1.0)


class CompetitorGapAnalysis(BaseModel):
    primary_gap_theme: str
    selection_mode: SelectionMode
    why_now_summary: str
    competitors_considered: list[str] = Field(default_factory=list)
    key_signals: KeySignals
    confidence_band: ConfidenceBand
    fallback_reason: Optional[str] = None
