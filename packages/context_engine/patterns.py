"""Competing pattern hypotheses. Never structure truth or trade signals.

Constitution §3: invalidation rules are frozen at create time.
Constitution §5: only pivots/candles with known_at / period_end <= T are usable.
Constitution §10: pattern frameworks compete; none are privileged. Elliott, if
emitted, is a labeled candidate only.

Scores are deterministic evidence counts (score_provenance=evidence_count_v1).
They are not calibrated confidence percentages and must not be presented as such.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Iterable, Literal, Sequence

from .models import Candle, Pivot
from .resample import resample_closed
from .structure import confirmed_pivots, swing_state

TIMEFRAME_MINUTES: dict[str, int] = {
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}

PATTERN_KINDS = (
    "continuation",
    "flag",
    "wedge",
    "triangle",
    "compression",
    "failed_breakout",
    "successful_reclaim",
    "accumulation",
    "distribution",
    "elliott_impulse",
    "elliott_correction",
)

ELLIOTT_KINDS = frozenset({"elliott_impulse", "elliott_correction"})
SCORE_PROVENANCE = "evidence_count_v1"
HYPOTHESIS_AUTHORITY = "hypothesis"

Direction = Literal["bull", "bear", "neutral"]
HypothesisStatus = Literal["candidate", "active", "confirmed", "invalidated", "superseded"]
RegimeRelation = Literal["aligned", "countertrend", "mixed", "unknown"]
RuleKind = Literal[
    "close_above",
    "close_below",
    "high_above",
    "low_below",
    "range_expansion",
    "pivot_high_above",
    "pivot_low_below",
]
LevelOutcome = Literal["failed_breakout", "successful_reclaim"]
PatternKind = Literal[
    "continuation",
    "flag",
    "wedge",
    "triangle",
    "compression",
    "failed_breakout",
    "successful_reclaim",
    "accumulation",
    "distribution",
    "elliott_impulse",
    "elliott_correction",
]


class ImmutableInvalidationError(Exception):
    """Constitution §3 — invalidation rules cannot be moved on an existing version."""


class NaiveTimestampError(ValueError):
    """Raised when a timestamp is naive or not UTC."""


def _require_utc(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise NaiveTimestampError(f"{name} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise NaiveTimestampError(f"{name} must be UTC")


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def candle_period_end(candle: Candle) -> datetime:
    minutes = TIMEFRAME_MINUTES.get(candle.timeframe)
    if minutes is None:
        raise ValueError(f"unknown timeframe: {candle.timeframe}")
    _require_utc("Candle.open_time", candle.open_time)
    return candle.open_time + timedelta(minutes=minutes)


def usable_candles(candles: Sequence[Candle], as_of: datetime) -> list[Candle]:
    _require_utc("as_of", as_of)
    out: list[Candle] = []
    for candle in candles:
        if not candle.is_closed:
            continue
        if candle_period_end(candle) > as_of:
            continue
        out.append(candle)
    return out


def usable_pivots(pivots: Sequence[Pivot], as_of: datetime) -> list[Pivot]:
    _require_utc("as_of", as_of)
    out: list[Pivot] = []
    for pivot in pivots:
        _require_utc("Pivot.known_at", pivot.known_at)
        _require_utc("Pivot.time", pivot.time)
        if pivot.known_at <= as_of:
            out.append(pivot)
    return out


def score_from_counts(n_evidence: int, n_counter: int, n_confirmation: int = 0) -> float:
    """Uncalibrated rank from counts. Not a confidence percentage."""
    denom = n_evidence + n_counter + n_confirmation + 1
    return (n_evidence + 2 * n_confirmation - n_counter) / denom


def competing_ranked(hypotheses: Sequence[PatternHypothesis]) -> tuple[PatternHypothesis, ...]:
    """Rank by evidence score only. Kind name, including Elliott, is never a boost."""
    return tuple(
        sorted(hypotheses, key=lambda h: (-h.evidence_score, h.kind, h.id))
    )


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    code: str
    detail: str
    known_at: datetime
    timeframe: str

    def __post_init__(self) -> None:
        _require_utc("EvidenceItem.known_at", self.known_at)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "detail": self.detail,
            "known_at": self.known_at.isoformat(),
            "timeframe": self.timeframe,
        }


@dataclass(frozen=True, slots=True)
class PatternRule:
    id: str
    kind: RuleKind
    price: float
    timeframe: str
    description: str = ""

    def __post_init__(self) -> None:
        if self.kind not in {
            "close_above",
            "close_below",
            "high_above",
            "low_below",
            "range_expansion",
            "pivot_high_above",
            "pivot_low_below",
        }:
            raise ValueError(f"unsupported rule kind: {self.kind}")
        if not self.timeframe:
            raise ValueError("rule timeframe is required")
        if self.price != self.price:
            raise ValueError("rule price must be finite")

    def fires_on_candle(self, candle: Candle) -> bool:
        if candle.timeframe != self.timeframe:
            return False
        if not candle.is_closed:
            return False
        if self.kind == "close_above":
            return candle.close > self.price
        if self.kind == "close_below":
            return candle.close < self.price
        if self.kind == "high_above":
            return candle.high > self.price
        if self.kind == "low_below":
            return candle.low < self.price
        if self.kind == "range_expansion":
            return (candle.high - candle.low) >= self.price
        return False

    def fires_on_pivot(self, pivot: Pivot) -> bool:
        if self.kind == "pivot_high_above":
            return pivot.kind == "high" and pivot.price > self.price
        if self.kind == "pivot_low_below":
            return pivot.kind == "low" and pivot.price < self.price
        return False

    def fingerprint(self) -> str:
        payload = {
            "id": self.id,
            "kind": self.kind,
            "price": self.price,
            "timeframe": self.timeframe,
            "description": self.description,
        }
        return hashlib.sha256(_canonical(payload).encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PatternHypothesis:
    """One competing pattern hypothesis. Not confirmed structure. Not a trade signal."""

    id: str
    lineage_id: str
    symbol: str
    kind: PatternKind
    direction: Direction
    timeframe: str
    status: HypothesisStatus
    created_at: datetime
    known_at: datetime
    evidence: tuple[EvidenceItem, ...]
    counter_evidence: tuple[EvidenceItem, ...]
    confirmation: tuple[EvidenceItem, ...]
    confirmation_rules: tuple[PatternRule, ...]
    invalidation: tuple[PatternRule, ...]
    evidence_score: float
    score_provenance: str = SCORE_PROVENANCE
    authority: str = HYPOTHESIS_AUTHORITY
    privileged: bool = False
    regime_relation: RegimeRelation = "unknown"
    version: int = 1
    framework: str | None = None
    outcome: LevelOutcome | None = None
    closed_at: datetime | None = None
    closure_reason: str | None = None
    fired_invalidation_ids: tuple[str, ...] = ()
    supersedes: str | None = None
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        _require_utc("created_at", self.created_at)
        _require_utc("known_at", self.known_at)
        if self.closed_at is not None:
            _require_utc("closed_at", self.closed_at)
        if self.kind not in PATTERN_KINDS:
            raise ValueError(f"unsupported pattern kind: {self.kind}")
        if self.direction not in {"bull", "bear", "neutral"}:
            raise ValueError("direction must be bull, bear, or neutral")
        if self.status not in {"candidate", "active", "confirmed", "invalidated", "superseded"}:
            raise ValueError("invalid hypothesis status")
        if not self.confirmation_rules:
            raise ValueError("hypothesis requires confirmation_rules")
        if not self.invalidation:
            raise ValueError("hypothesis requires invalidation rules")
        if self.privileged:
            raise ValueError("pattern hypotheses are never privileged (Constitution §10)")
        if self.authority != HYPOTHESIS_AUTHORITY:
            raise ValueError("pattern objects are hypotheses, not confirmed structure or trade signals")
        if self.score_provenance != SCORE_PROVENANCE:
            raise ValueError(f"score_provenance must be {SCORE_PROVENANCE}")
        if self.kind in ELLIOTT_KINDS:
            if self.status not in {"candidate", "invalidated", "superseded"}:
                raise ValueError("Elliott hypotheses stay candidate until invalidated or superseded")
            if self.framework != "elliott":
                raise ValueError("Elliott hypotheses must set framework='elliott'")
        if self.status in {"candidate", "active", "confirmed"}:
            if self.closed_at is not None or self.closure_reason is not None:
                raise ValueError("open hypothesis cannot carry closure fields")
            if self.fired_invalidation_ids:
                raise ValueError("open hypothesis cannot record fired invalidation")

    @property
    def invalidation_rules(self) -> tuple[PatternRule, ...]:
        return self.invalidation

    @property
    def invalidation_fingerprint(self) -> str:
        parts = [rule.fingerprint() for rule in self.invalidation]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def move_invalidation(self, *args: object, **kwargs: object) -> None:
        raise ImmutableInvalidationError(
            "Constitution §3: cannot move invalidation on an existing pattern hypothesis; "
            "close this version and open a successor"
        )

    def with_invalidation_rules(self, _rules: Sequence[PatternRule]) -> PatternHypothesis:
        raise ImmutableInvalidationError(
            "Constitution §3: cannot replace invalidation on an existing pattern hypothesis"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lineage_id": self.lineage_id,
            "symbol": self.symbol,
            "kind": self.kind,
            "direction": self.direction,
            "timeframe": self.timeframe,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "known_at": self.known_at.isoformat(),
            "evidence": [item.to_dict() for item in self.evidence],
            "counter_evidence": [item.to_dict() for item in self.counter_evidence],
            "confirmation": [item.to_dict() for item in self.confirmation],
            "confirmation_rules": [rule.to_dict() for rule in self.confirmation_rules],
            "invalidation": [rule.to_dict() for rule in self.invalidation],
            "evidence_score": self.evidence_score,
            "score_provenance": self.score_provenance,
            "authority": self.authority,
            "privileged": False,
            "regime_relation": self.regime_relation,
            "version": self.version,
            "framework": self.framework,
            "outcome": self.outcome,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "closure_reason": self.closure_reason,
            "fired_invalidation_ids": list(self.fired_invalidation_ids),
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
        }


def _status_from_evidence(kind: str, evidence: Sequence[EvidenceItem], counter: Sequence[EvidenceItem]) -> HypothesisStatus:
    if kind in ELLIOTT_KINDS:
        return "candidate"
    if len(evidence) >= 2 and len(evidence) > len(counter):
        return "active"
    return "candidate"


def _regime_relation(direction: Direction, parent_regime: str | None) -> RegimeRelation:
    if parent_regime is None or parent_regime in {"unknown", ""}:
        return "unknown"
    if parent_regime in {"bullish", "transition_up"}:
        parent_dir: Direction | None = "bull"
    elif parent_regime in {"bearish", "transition_down"}:
        parent_dir = "bear"
    elif parent_regime == "neutral":
        return "mixed"
    else:
        return "unknown"
    if direction == "neutral":
        return "mixed"
    return "aligned" if direction == parent_dir else "countertrend"


def _new_id(*parts: object) -> str:
    payload = _canonical(list(parts))
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def _build_hypothesis(
    *,
    kind: PatternKind,
    direction: Direction,
    timeframe: str,
    symbol: str,
    known_at: datetime,
    evidence: Sequence[EvidenceItem],
    counter_evidence: Sequence[EvidenceItem],
    confirmation_rules: Sequence[PatternRule],
    invalidation: Sequence[PatternRule],
    parent_regime: str | None = None,
    framework: str | None = None,
    outcome: LevelOutcome | None = None,
    confirmation: Sequence[EvidenceItem] = (),
    version: int = 1,
    lineage_id: str | None = None,
    supersedes: str | None = None,
) -> PatternHypothesis:
    if kind in ELLIOTT_KINDS:
        framework = "elliott"
    status = _status_from_evidence(kind, evidence, counter_evidence)
    score = score_from_counts(len(evidence), len(counter_evidence), len(confirmation))
    ident = _new_id(
        kind,
        direction,
        timeframe,
        symbol,
        known_at.isoformat(),
        [rule.fingerprint() for rule in confirmation_rules],
        [rule.fingerprint() for rule in invalidation],
        [item.code for item in evidence],
        version,
    )
    lineage = lineage_id or ident
    return PatternHypothesis(
        id=ident,
        lineage_id=lineage,
        symbol=symbol,
        kind=kind,
        direction=direction,
        timeframe=timeframe,
        status=status,
        created_at=known_at,
        known_at=known_at,
        evidence=tuple(evidence),
        counter_evidence=tuple(counter_evidence),
        confirmation=tuple(confirmation),
        confirmation_rules=tuple(confirmation_rules),
        invalidation=tuple(invalidation),
        evidence_score=score,
        regime_relation=_regime_relation(direction, parent_regime),
        version=version,
        framework=framework,
        outcome=outcome,
        supersedes=supersedes,
    )


def _inputs_at(
    candles: Sequence[Candle],
    as_of: datetime,
    timeframe: str | None,
    left: int,
    right: int,
) -> tuple[list[Candle], list[Pivot], str, str]:
    closed_source = [c for c in candles if c.is_closed]
    if not closed_source:
        return [], [], timeframe or "5m", "UNKNOWN"
    source_tf = closed_source[0].timeframe
    symbol = closed_source[0].symbol
    target_tf = timeframe or source_tf
    if source_tf == "5m" and target_tf != "5m":
        minutes = TIMEFRAME_MINUTES.get(target_tf)
        if minutes is None:
            raise ValueError(f"unknown timeframe: {target_tf}")
        series = resample_closed(closed_source, minutes, target_tf)
    else:
        series = [c for c in closed_source if c.timeframe == target_tf]
    usable = usable_candles(series, as_of)
    if len(usable) < left + right + 1:
        pivots: list[Pivot] = []
    else:
        pivots = usable_pivots(confirmed_pivots(usable, left, right), as_of)
    return usable, pivots, target_tf, symbol


def _latest_known(*timestamps: datetime) -> datetime:
    return max(timestamps)


def classify_level_resolution(
    level: float,
    candles: Sequence[Candle],
    as_of: datetime,
    timeframe: str,
    *,
    acceptance_closes: int = 2,
) -> LevelOutcome | None:
    """Distinguish failed-breakout rejection from successful reclaim-with-acceptance.

    These outcomes are mutually exclusive. A rejection before acceptance is never
    a reclaim; a reclaim requires an accepted breakdown and later accepted recovery.
    """
    xs = [c for c in usable_candles(candles, as_of) if c.timeframe == timeframe]
    start: int | None = None
    side: Literal["above", "below"] | None = None
    for i, candle in enumerate(xs):
        if candle.close > level:
            start, side = i, "above"
            break
        if candle.close < level:
            start, side = i, "below"
            break
    if start is None or side is None:
        return None

    run = 0
    j = start
    while j < len(xs) and (
        (side == "above" and xs[j].close > level) or (side == "below" and xs[j].close < level)
    ):
        run += 1
        j += 1
    accepted = run >= acceptance_closes

    if side == "above":
        if not accepted and j < len(xs) and xs[j].close <= level:
            return "failed_breakout"
        return None

    if not accepted and j < len(xs) and xs[j].close >= level:
        return "failed_breakout"

    if accepted:
        above_run = 0
        for candle in xs[j:]:
            if candle.close > level:
                above_run += 1
                if above_run >= acceptance_closes:
                    return "successful_reclaim"
            else:
                above_run = 0
    return None


def _detect_continuation(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> PatternHypothesis | None:
    highs = [p for p in pivots if p.kind == "high"]
    lows = [p for p in pivots if p.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return None
    last_h, prev_h = highs[-1], highs[-2]
    last_l, prev_l = lows[-1], lows[-2]
    swing = swing_state(pivots)
    known = _latest_known(last_h.known_at, last_l.known_at, prev_h.known_at, prev_l.known_at)
    if swing == "HH_HL":
        direction: Direction = "bull"
        evidence = [
            EvidenceItem("higher_high", f"high {last_h.price} > {prev_h.price}", last_h.known_at, timeframe),
            EvidenceItem("higher_low", f"low {last_l.price} > {prev_l.price}", last_l.known_at, timeframe),
        ]
        confirm = (
            PatternRule("cont-confirm-hh", "close_above", last_h.price, timeframe, "same-TF close above last high"),
            PatternRule("cont-confirm-pivot", "pivot_high_above", last_h.price, timeframe, "new confirmed higher high"),
        )
        invalid = (
            PatternRule("cont-invalid-ll", "close_below", last_l.price, timeframe, "same-TF close below last higher low"),
        )
    elif swing == "LH_LL":
        direction = "bear"
        evidence = [
            EvidenceItem("lower_high", f"high {last_h.price} < {prev_h.price}", last_h.known_at, timeframe),
            EvidenceItem("lower_low", f"low {last_l.price} < {prev_l.price}", last_l.known_at, timeframe),
        ]
        confirm = (
            PatternRule("cont-confirm-ll", "close_below", last_l.price, timeframe, "same-TF close below last low"),
            PatternRule("cont-confirm-pivot", "pivot_low_below", last_l.price, timeframe, "new confirmed lower low"),
        )
        invalid = (
            PatternRule("cont-invalid-hh", "close_above", last_h.price, timeframe, "same-TF close above last lower high"),
        )
    else:
        return None
    last = candles[-1]
    counter: list[EvidenceItem] = []
    if direction == "bull" and last.close < last_l.price:
        counter.append(EvidenceItem("close_under_last_low", "close lost the last higher low", candle_period_end(last), timeframe))
    if direction == "bear" and last.close > last_h.price:
        counter.append(EvidenceItem("close_over_last_high", "close recovered the last lower high", candle_period_end(last), timeframe))
    return _build_hypothesis(
        kind="continuation",
        direction=direction,
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=evidence,
        counter_evidence=counter,
        confirmation_rules=confirm,
        invalidation=invalid,
        parent_regime=parent_regime,
        framework="price_action",
    )


def _detect_flag(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> PatternHypothesis | None:
    if len(pivots) < 4 or len(candles) < 8:
        return None
    impulse = max(
        zip(pivots, pivots[1:]),
        key=lambda pair: abs(pair[1].price - pair[0].price),
    )
    start, end = impulse
    impulse_size = abs(end.price - start.price)
    if impulse_size <= 0:
        return None
    after = [p for p in pivots if p.known_at_index > end.known_at_index]
    if len(after) < 2:
        return None
    flag_high = max(p.price for p in after)
    flag_low = min(p.price for p in after)
    flag_width = flag_high - flag_low
    if flag_width >= impulse_size * 0.62:
        return None
    bullish_impulse = end.price > start.price
    known = _latest_known(end.known_at, after[-1].known_at)
    evidence = [
        EvidenceItem("impulse", f"impulse size {impulse_size:.6f}", end.known_at, timeframe),
        EvidenceItem("flag_compression", f"flag width {flag_width:.6f} < 0.62 impulse", after[-1].known_at, timeframe),
    ]
    counter: list[EvidenceItem] = []
    if bullish_impulse:
        if flag_low < start.price:
            counter.append(EvidenceItem("flag_lost_origin", "bull flag undercut impulse origin", after[-1].known_at, timeframe))
        return _build_hypothesis(
            kind="flag",
            direction="bull",
            timeframe=timeframe,
            symbol=symbol,
            known_at=known,
            evidence=evidence,
            counter_evidence=counter,
            confirmation_rules=(
                PatternRule("flag-confirm", "close_above", flag_high, timeframe, "same-TF close above flag high"),
            ),
            invalidation=(
                PatternRule("flag-invalid", "close_below", start.price, timeframe, "same-TF close below impulse origin"),
            ),
            parent_regime=parent_regime,
            framework="price_action",
        )
    if flag_high > start.price:
        counter.append(EvidenceItem("flag_lost_origin", "bear flag overshot impulse origin", after[-1].known_at, timeframe))
    return _build_hypothesis(
        kind="flag",
        direction="bear",
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=evidence,
        counter_evidence=counter,
        confirmation_rules=(
            PatternRule("flag-confirm", "close_below", flag_low, timeframe, "same-TF close below flag low"),
        ),
        invalidation=(
            PatternRule("flag-invalid", "close_above", start.price, timeframe, "same-TF close above impulse origin"),
        ),
        parent_regime=parent_regime,
        framework="price_action",
    )


def _detect_wedge_triangle(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> PatternHypothesis | None:
    highs = [p for p in pivots if p.kind == "high"][-4:]
    lows = [p for p in pivots if p.kind == "low"][-4:]
    if len(highs) < 3 or len(lows) < 3:
        return None
    early_width = highs[0].price - lows[0].price
    late_width = highs[-1].price - lows[-1].price
    if early_width <= 0 or late_width >= early_width * 0.92:
        return None
    high_slope = highs[-1].price - highs[0].price
    low_slope = lows[-1].price - lows[0].price
    known = _latest_known(highs[-1].known_at, lows[-1].known_at)
    evidence = [
        EvidenceItem("converging_range", f"width {early_width:.6f} -> {late_width:.6f}", known, timeframe),
        EvidenceItem("geometry", f"high_slope={high_slope:.6f} low_slope={low_slope:.6f}", known, timeframe),
    ]
    flat_high = abs(high_slope) <= 0.15 * max(abs(highs[0].price), 1e-9)
    flat_low = abs(low_slope) <= 0.15 * max(abs(lows[0].price), 1e-9)
    if high_slope > 0 and low_slope > 0:
        kind: PatternKind = "wedge"
        direction: Direction = "bear"
        detail = "rising_wedge"
    elif high_slope < 0 and low_slope < 0:
        kind = "wedge"
        direction = "bull"
        detail = "falling_wedge"
    elif flat_high and low_slope > 0:
        kind = "triangle"
        direction = "bull"
        detail = "ascending_triangle"
    elif flat_low and high_slope < 0:
        kind = "triangle"
        direction = "bear"
        detail = "descending_triangle"
    elif high_slope < 0 and low_slope > 0:
        kind = "triangle"
        direction = "neutral"
        detail = "symmetrical_triangle"
    else:
        return None
    evidence = [
        *evidence,
        EvidenceItem("subtype", detail, known, timeframe),
    ]
    upper = max(p.price for p in highs)
    lower = min(p.price for p in lows)
    if direction == "bull":
        confirm = (PatternRule("geo-confirm", "close_above", upper, timeframe, "same-TF close above geometry high"),)
        invalid = (PatternRule("geo-invalid", "close_below", lower, timeframe, "same-TF close below geometry low"),)
    elif direction == "bear":
        confirm = (PatternRule("geo-confirm", "close_below", lower, timeframe, "same-TF close below geometry low"),)
        invalid = (PatternRule("geo-invalid", "close_above", upper, timeframe, "same-TF close above geometry high"),)
    else:
        confirm = (PatternRule("geo-confirm-up", "close_above", upper, timeframe, "same-TF resolution above"),)
        invalid = (PatternRule("geo-invalid-down", "close_below", lower, timeframe, "same-TF resolution below"),)
    return _build_hypothesis(
        kind=kind,
        direction=direction,
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=evidence,
        counter_evidence=(),
        confirmation_rules=confirm,
        invalidation=invalid,
        parent_regime=parent_regime,
        framework="price_action",
    )


def _detect_compression(
    candles: list[Candle],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> PatternHypothesis | None:
    if len(candles) < 16:
        return None
    prior = candles[-16:-8]
    recent = candles[-8:]
    prior_range = max(c.high for c in prior) - min(c.low for c in prior)
    recent_range = max(c.high for c in recent) - min(c.low for c in recent)
    if prior_range <= 0 or recent_range >= prior_range * 0.6:
        return None
    known = candle_period_end(recent[-1])
    box_high = max(c.high for c in recent)
    box_low = min(c.low for c in recent)
    evidence = [
        EvidenceItem("range_contraction", f"recent {recent_range:.6f} vs prior {prior_range:.6f}", known, timeframe),
        EvidenceItem("compressed_box", f"{box_low:.6f}-{box_high:.6f}", known, timeframe),
    ]
    threshold = max(recent_range * 1.5, (box_high - box_low) * 1.5)
    return _build_hypothesis(
        kind="compression",
        direction="neutral",
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=evidence,
        counter_evidence=(),
        confirmation_rules=(
            PatternRule("comp-confirm", "range_expansion", threshold, timeframe, "same-TF range expansion"),
        ),
        invalidation=(
            PatternRule("comp-invalid-high", "close_above", box_high + 5 * max(recent_range, 1e-9), timeframe, "geometry blown out above"),
            PatternRule("comp-invalid-low", "close_below", box_low - 5 * max(recent_range, 1e-9), timeframe, "geometry blown out below"),
        ),
        parent_regime=parent_regime,
        framework="price_action",
    )


def _detect_break_outcomes(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> list[PatternHypothesis]:
    found: list[PatternHypothesis] = []
    levels: list[tuple[str, float, datetime]] = []
    for pivot in pivots[-6:]:
        levels.append((pivot.kind, pivot.price, pivot.known_at))
    seen: set[tuple[str, float]] = set()
    for kind, price, known in levels:
        key = (kind, round(price, 8))
        if key in seen:
            continue
        seen.add(key)
        after = [c for c in candles if candle_period_end(c) >= known]
        outcome = classify_level_resolution(price, after, as_of, timeframe)
        if outcome is None:
            continue
        last = after[-1] if after else candles[-1]
        known_at = candle_period_end(last)
        if outcome == "failed_breakout":
            direction: Direction = "bear" if kind == "high" else "bull"
            evidence = [
                EvidenceItem("break_then_reject", f"level {price} rejected before acceptance", known_at, timeframe),
                EvidenceItem("source_pivot", f"{kind} {price}", known, timeframe),
            ]
            if kind == "high":
                confirm = (PatternRule("fb-confirm", "close_below", price, timeframe, "hold below failed breakout"),)
                invalid = (PatternRule("fb-invalid", "close_above", price, timeframe, "reclaim of the broken high"),)
            else:
                confirm = (PatternRule("fb-confirm", "close_above", price, timeframe, "hold above failed breakdown"),)
                invalid = (PatternRule("fb-invalid", "close_below", price, timeframe, "re-loss of the defended low"),)
            found.append(
                _build_hypothesis(
                    kind="failed_breakout",
                    direction=direction,
                    timeframe=timeframe,
                    symbol=symbol,
                    known_at=known_at,
                    evidence=evidence,
                    counter_evidence=(),
                    confirmation_rules=confirm,
                    invalidation=invalid,
                    parent_regime=parent_regime,
                    framework="price_action",
                    outcome="failed_breakout",
                )
            )
        elif outcome == "successful_reclaim":
            evidence = [
                EvidenceItem("breakdown_then_reclaim", f"level {price} lost then accepted back above", known_at, timeframe),
                EvidenceItem("source_pivot", f"{kind} {price}", known, timeframe),
            ]
            found.append(
                _build_hypothesis(
                    kind="successful_reclaim",
                    direction="bull",
                    timeframe=timeframe,
                    symbol=symbol,
                    known_at=known_at,
                    evidence=evidence,
                    counter_evidence=(),
                    confirmation_rules=(
                        PatternRule("sr-confirm", "close_above", price, timeframe, "continued acceptance above reclaimed level"),
                    ),
                    invalidation=(
                        PatternRule("sr-invalid", "close_below", price, timeframe, "loss of the reclaimed level"),
                    ),
                    parent_regime=parent_regime,
                    framework="price_action",
                    outcome="successful_reclaim",
                )
            )
    return found


def _detect_acc_dist(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> PatternHypothesis | None:
    if len(candles) < 12:
        return None
    window = candles[-12:]
    box_high = max(c.high for c in window)
    box_low = min(c.low for c in window)
    width = box_high - box_low
    if width <= 0:
        return None
    mid = (box_high + box_low) / 2.0
    lows = [p for p in usable_pivots(pivots, as_of) if p.kind == "low"][-3:]
    highs = [p for p in usable_pivots(pivots, as_of) if p.kind == "high"][-3:]
    up_vol = sum(c.volume for c in window if c.close >= c.open)
    down_vol = sum(c.volume for c in window if c.close < c.open)
    closes = [c.close for c in window]
    upper_half = sum(1 for close in closes if close >= mid)
    known = candle_period_end(window[-1])
    rising_lows = len(lows) >= 2 and lows[-1].price > lows[0].price
    falling_highs = len(highs) >= 2 and highs[-1].price < highs[0].price
    if rising_lows and upper_half >= 6 and up_vol >= down_vol:
        return _build_hypothesis(
            kind="accumulation",
            direction="bull",
            timeframe=timeframe,
            symbol=symbol,
            known_at=known,
            evidence=(
                EvidenceItem("rising_lows_in_box", "higher lows inside range", known, timeframe),
                EvidenceItem("wyckoff_inspired_range", "up-bar volume not dominated by down bars", known, timeframe),
            ),
            counter_evidence=(),
            confirmation_rules=(
                PatternRule("acc-confirm", "close_above", box_high, timeframe, "same-TF close above accumulation box"),
            ),
            invalidation=(
                PatternRule("acc-invalid", "close_below", box_low, timeframe, "same-TF close below accumulation box"),
            ),
            parent_regime=parent_regime,
            framework="wyckoff_inspired",
        )
    if falling_highs and upper_half <= 6 and down_vol >= up_vol:
        return _build_hypothesis(
            kind="distribution",
            direction="bear",
            timeframe=timeframe,
            symbol=symbol,
            known_at=known,
            evidence=(
                EvidenceItem("falling_highs_in_box", "lower highs inside range", known, timeframe),
                EvidenceItem("wyckoff_inspired_range", "down-bar volume not dominated by up bars", known, timeframe),
            ),
            counter_evidence=(),
            confirmation_rules=(
                PatternRule("dist-confirm", "close_below", box_low, timeframe, "same-TF close below distribution box"),
            ),
            invalidation=(
                PatternRule("dist-invalid", "close_above", box_high, timeframe, "same-TF close above distribution box"),
            ),
            parent_regime=parent_regime,
            framework="wyckoff_inspired",
        )
    return None


def _alternating(pivots: Sequence[Pivot]) -> bool:
    if len(pivots) < 2:
        return False
    return all(a.kind != b.kind for a, b in zip(pivots, pivots[1:]))


def _detect_elliott(
    candles: list[Candle],
    pivots: list[Pivot],
    as_of: datetime,
    timeframe: str,
    symbol: str,
    parent_regime: str | None,
) -> list[PatternHypothesis]:
    """Optional Elliott candidates. Never forced from five peaks. Never privileged."""
    if len(pivots) < 6:
        return []
    seq = pivots[-6:]
    if not _alternating(seq):
        return []
    start, w1, w2, w3, w4, w5 = seq
    known = w5.known_at
    evidence: list[EvidenceItem] = [
        EvidenceItem("alternating_pivots", "six alternating pivots available for a 5-wave sketch", known, timeframe),
    ]
    counter: list[EvidenceItem] = []
    impulse_ok = True
    if start.kind == "low":
        direction: Direction = "bull"
        if w2.price <= start.price:
            impulse_ok = False
            counter.append(EvidenceItem("wave2_beyond_origin", "wave 2 undercuts wave 1 origin", w2.known_at, timeframe))
        else:
            evidence.append(EvidenceItem("wave2_holds_origin", "wave 2 stays above origin", w2.known_at, timeframe))
        if w4.price <= w1.price:
            impulse_ok = False
            counter.append(EvidenceItem("wave4_overlaps_w1", "wave 4 overlaps wave 1", w4.known_at, timeframe))
        else:
            evidence.append(EvidenceItem("wave4_no_overlap", "wave 4 stays above wave 1 high", w4.known_at, timeframe))
        lengths = [abs(w1.price - start.price), abs(w3.price - w2.price), abs(w5.price - w4.price)]
    else:
        direction = "bear"
        if w2.price >= start.price:
            impulse_ok = False
            counter.append(EvidenceItem("wave2_beyond_origin", "wave 2 exceeds wave 1 origin", w2.known_at, timeframe))
        else:
            evidence.append(EvidenceItem("wave2_holds_origin", "wave 2 stays below origin", w2.known_at, timeframe))
        if w4.price >= w1.price:
            impulse_ok = False
            counter.append(EvidenceItem("wave4_overlaps_w1", "wave 4 overlaps wave 1", w4.known_at, timeframe))
        else:
            evidence.append(EvidenceItem("wave4_no_overlap", "wave 4 stays below wave 1 low", w4.known_at, timeframe))
        lengths = [abs(start.price - w1.price), abs(w2.price - w3.price), abs(w4.price - w5.price)]
    if lengths[1] == min(lengths):
        impulse_ok = False
        counter.append(EvidenceItem("wave3_shortest", "wave 3 is the shortest of 1/3/5", w3.known_at, timeframe))
    else:
        evidence.append(EvidenceItem("wave3_not_shortest", "wave 3 is not the shortest", w3.known_at, timeframe))
    if not impulse_ok and len(evidence) < 2:
        return []
    invalid_price = start.price
    if direction == "bull":
        confirm = (PatternRule("elliott-confirm", "pivot_high_above", w5.price, timeframe, "additional confirmed pivot, still a candidate"),)
        invalid = (PatternRule("elliott-invalid", "close_below", invalid_price, timeframe, "close back through labeled wave-1 origin"),)
    else:
        confirm = (PatternRule("elliott-confirm", "pivot_low_below", w5.price, timeframe, "additional confirmed pivot, still a candidate"),)
        invalid = (PatternRule("elliott-invalid", "close_above", invalid_price, timeframe, "close back through labeled wave-1 origin"),)
    impulse = _build_hypothesis(
        kind="elliott_impulse",
        direction=direction,
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=evidence,
        counter_evidence=counter,
        confirmation_rules=confirm,
        invalidation=invalid,
        parent_regime=parent_regime,
        framework="elliott",
    )
    correction = _build_hypothesis(
        kind="elliott_correction",
        direction="bull" if direction == "bear" else "bear",
        timeframe=timeframe,
        symbol=symbol,
        known_at=known,
        evidence=(
            EvidenceItem("alternate_count", "competing correction count against the impulse sketch", known, timeframe),
        ),
        counter_evidence=(
            EvidenceItem("unconfirmed_label", "five visible pivots are not an Elliott proof", known, timeframe),
        ),
        confirmation_rules=(
            PatternRule("elliott-alt-confirm", "close_above" if direction == "bear" else "close_below", w5.price, timeframe, "overlap that favors a correction"),
        ),
        invalidation=(
            PatternRule("elliott-alt-invalid", "close_below" if direction == "bear" else "close_above", w5.price, timeframe, "extension that favors the impulse sketch"),
        ),
        parent_regime=parent_regime,
        framework="elliott",
    )
    return [impulse, correction]


def hypotheses_at(
    candles: Sequence[Candle],
    as_of: datetime,
    *,
    timeframe: str | None = None,
    parent_regime: str | None = None,
    left: int = 3,
    right: int = 3,
    pivots: Sequence[Pivot] | None = None,
) -> tuple[PatternHypothesis, ...]:
    """Pattern hypotheses knowable at T. Future / unfinished inputs are ignored."""
    _require_utc("as_of", as_of)
    usable, computed, target_tf, symbol = _inputs_at(candles, as_of, timeframe, left, right)
    if pivots is None:
        known_pivots = computed
    else:
        known_pivots = usable_pivots(pivots, as_of)
        known_pivots = [p for p in known_pivots if p.known_at <= as_of]
    if not usable:
        return ()
    found: list[PatternHypothesis] = []
    continuation = _detect_continuation(usable, known_pivots, as_of, target_tf, symbol, parent_regime)
    if continuation is not None:
        found.append(continuation)
    flag = _detect_flag(usable, known_pivots, as_of, target_tf, symbol, parent_regime)
    if flag is not None:
        found.append(flag)
    geometry = _detect_wedge_triangle(usable, known_pivots, as_of, target_tf, symbol, parent_regime)
    if geometry is not None:
        found.append(geometry)
    compression = _detect_compression(usable, as_of, target_tf, symbol, parent_regime)
    if compression is not None:
        found.append(compression)
    found.extend(_detect_break_outcomes(usable, known_pivots, as_of, target_tf, symbol, parent_regime))
    acc_dist = _detect_acc_dist(usable, known_pivots, as_of, target_tf, symbol, parent_regime)
    if acc_dist is not None:
        found.append(acc_dist)
    found.extend(_detect_elliott(usable, known_pivots, as_of, target_tf, symbol, parent_regime))
    return competing_ranked(found)


def evaluate_hypothesis(
    hypothesis: PatternHypothesis,
    candles: Sequence[Candle],
    as_of: datetime,
    *,
    pivots: Sequence[Pivot] | None = None,
) -> PatternHypothesis:
    """Advance status from same-timeframe usable inputs only. Invalidation stays frozen."""
    _require_utc("as_of", as_of)
    if hypothesis.status in {"invalidated", "superseded"}:
        return hypothesis
    usable = [c for c in usable_candles(candles, as_of) if c.timeframe == hypothesis.timeframe]
    known_pivots = usable_pivots(pivots or (), as_of)
    fired_invalid: list[tuple[PatternRule, datetime]] = []
    fired_confirm: list[tuple[PatternRule, datetime]] = []
    for candle in usable:
        for rule in hypothesis.invalidation:
            if rule.fires_on_candle(candle):
                fired_invalid.append((rule, candle_period_end(candle)))
        for rule in hypothesis.confirmation_rules:
            if rule.fires_on_candle(candle):
                fired_confirm.append((rule, candle_period_end(candle)))
    for pivot in known_pivots:
        for rule in hypothesis.invalidation:
            if rule.fires_on_pivot(pivot):
                fired_invalid.append((rule, pivot.known_at))
        for rule in hypothesis.confirmation_rules:
            if rule.fires_on_pivot(pivot):
                fired_confirm.append((rule, pivot.known_at))

    if fired_invalid:
        first = min(fired_invalid, key=lambda item: item[1])
        confirm_items = tuple(
            EvidenceItem(rule.id, rule.description, when, hypothesis.timeframe)
            for rule, when in fired_confirm
        )
        score = score_from_counts(len(hypothesis.evidence), len(hypothesis.counter_evidence), len(confirm_items))
        return replace(
            hypothesis,
            status="invalidated",
            confirmation=confirm_items or hypothesis.confirmation,
            evidence_score=score,
            closed_at=first[1],
            closure_reason="invalidation_fired",
            fired_invalidation_ids=tuple(dict.fromkeys(rule.id for rule, _ in fired_invalid)),
        )

    confirm_by_id = {rule.id: when for rule, when in fired_confirm}
    all_confirm_ids = {rule.id for rule in hypothesis.confirmation_rules}
    confirm_items = tuple(
        EvidenceItem(rule.id, rule.description, confirm_by_id[rule.id], hypothesis.timeframe)
        for rule in hypothesis.confirmation_rules
        if rule.id in confirm_by_id
    )
    score = score_from_counts(len(hypothesis.evidence), len(hypothesis.counter_evidence), len(confirm_items))
    if hypothesis.kind in ELLIOTT_KINDS:
        return replace(hypothesis, confirmation=confirm_items, evidence_score=score, status="candidate")
    if confirm_items and all_confirm_ids <= set(confirm_by_id):
        return replace(
            hypothesis,
            status="confirmed",
            confirmation=confirm_items,
            evidence_score=score,
        )
    if confirm_items:
        return replace(hypothesis, confirmation=confirm_items, evidence_score=score)
    return hypothesis


class PatternBook:
    """In-memory set of competing hypotheses. Same-id invalidation mutation is rejected."""

    def __init__(self, hypotheses: Iterable[PatternHypothesis] = ()) -> None:
        self._by_id: dict[str, PatternHypothesis] = {}
        for hyp in hypotheses:
            self.add(hyp)

    def add(self, hypothesis: PatternHypothesis) -> PatternHypothesis:
        existing = self._by_id.get(hypothesis.id)
        if existing is not None and existing.invalidation_fingerprint != hypothesis.invalidation_fingerprint:
            raise ImmutableInvalidationError(
                "Constitution §3: cannot store a same-id hypothesis with moved invalidation"
            )
        self._by_id[hypothesis.id] = hypothesis
        return hypothesis

    def get(self, hyp_id: str) -> PatternHypothesis:
        return self._by_id[hyp_id]

    def all(self) -> tuple[PatternHypothesis, ...]:
        return tuple(self._by_id.values())

    def competing(self) -> tuple[PatternHypothesis, ...]:
        open_hyps = [h for h in self._by_id.values() if h.status in {"candidate", "active", "confirmed"}]
        return competing_ranked(open_hyps)

    def move_invalidation(self, hyp_id: str, new_price: float) -> None:
        hyp = self.get(hyp_id)
        hyp.move_invalidation(new_price)
        raise ImmutableInvalidationError("Constitution §3: cannot move invalidation")

    def replace_invalidation(self, hyp_id: str, rules: Sequence[PatternRule]) -> None:
        hyp = self.get(hyp_id)
        hyp.with_invalidation_rules(rules)
        raise ImmutableInvalidationError("Constitution §3: cannot replace invalidation")

    def evaluate(
        self,
        hyp_id: str,
        candles: Sequence[Candle],
        as_of: datetime,
        *,
        pivots: Sequence[Pivot] | None = None,
    ) -> PatternHypothesis:
        current = self.get(hyp_id)
        fingerprint = current.invalidation_fingerprint
        updated = evaluate_hypothesis(current, candles, as_of, pivots=pivots)
        if updated.invalidation_fingerprint != fingerprint:
            raise ImmutableInvalidationError("Constitution §3: evaluation must not move invalidation")
        self._by_id[hyp_id] = updated
        return updated

    def supersede(
        self,
        hyp_id: str,
        successor: PatternHypothesis,
        as_of: datetime,
    ) -> PatternHypothesis:
        _require_utc("as_of", as_of)
        current = self.get(hyp_id)
        closed = replace(
            current,
            status="superseded",
            closed_at=as_of,
            closure_reason="superseded",
            superseded_by=successor.id,
        )
        if closed.invalidation_fingerprint != current.invalidation_fingerprint:
            raise ImmutableInvalidationError("Constitution §3: supersede must leave prior invalidation frozen")
        self._by_id[current.id] = closed
        self.add(successor)
        return successor


def freeze_hypotheses(hypotheses: Sequence[PatternHypothesis]) -> tuple[dict, ...]:
    """Stable payload for point-in-time equality checks."""
    return tuple(h.to_dict() for h in competing_ranked(hypotheses))
