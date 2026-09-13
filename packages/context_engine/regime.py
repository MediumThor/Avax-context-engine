"""Hysteretic regime classifier. A 5m bounce cannot silently reset a parent bear."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Regime = Literal["bullish", "bearish", "neutral", "transition_up", "transition_down", "unknown"]


@dataclass(frozen=True, slots=True)
class RegimeScores:
    trend_score: float
    structure_score: float
    momentum_score: float
    volume_score: float
    parent_alignment: float
    final_state: Regime

    def to_dict(self) -> dict:
        return asdict(self)


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))


def classify_regime(
    *,
    ema_order: float,
    swing: float,
    momentum: float,
    volume: float,
    parent_regime: Regime | None = None,
    prior: Regime | None = None,
    hysteresis: float = 0.35,
) -> RegimeScores:
    parent = 0.0
    if parent_regime == "bullish":
        parent = 0.7
    elif parent_regime == "bearish":
        parent = -0.7
    raw = 0.30 * ema_order + 0.25 * swing + 0.15 * momentum + 0.10 * volume + 0.20 * parent
    raw = _clip(raw)
    state: Regime
    if raw >= hysteresis:
        state = "bullish"
    elif raw <= -hysteresis:
        state = "bearish"
    elif prior in {"bullish", "bearish"} and abs(raw) < hysteresis:
        state = "transition_down" if prior == "bullish" else "transition_up"
    else:
        state = "neutral"
    if parent_regime in {"bullish", "bearish"} and state in {"bullish", "bearish"} and state != parent_regime:
        # Child may be countertrend; do not report it as a parent flip.
        state = "transition_up" if state == "bullish" else "transition_down"
    return RegimeScores(
        trend_score=_clip(ema_order),
        structure_score=_clip(swing),
        momentum_score=_clip(momentum),
        volume_score=_clip(volume),
        parent_alignment=_clip(parent),
        final_state=state,
    )


def parent_child_reading(parent: Regime, child: Regime) -> str:
    if parent in {"bearish", "bullish"} and child != parent:
        return f"child_{child}_inside_parent_{parent}"
    return f"aligned_{parent}"
