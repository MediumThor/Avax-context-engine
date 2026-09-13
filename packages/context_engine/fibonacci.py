"""Exact Fibonacci / measured-move features from confirmed swing anchors.

Anchors are ``Pivot`` instances that already carry ``known_at`` provenance.
This module does not detect swings, invent pixel geometry, or promote a
ratio to support/resistance. Levels are context features only.

A pivot is usable at forecast time ``T`` only when ``known_at <= T``.
No Elliott-wave labels are assigned.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Sequence

from .models import Pivot

LevelKind = Literal["retracement", "extension", "measured_move"]
SwingDirection = Literal["up", "down"]

# Common structural ratios. These are candidate prices, not support calls.
DEFAULT_RETRACEMENT_RATIOS: tuple[float, ...] = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
DEFAULT_EXTENSION_RATIOS: tuple[float, ...] = (1.272, 1.618, 2.0, 2.618)
DEFAULT_MEASURED_MOVE_RATIOS: tuple[float, ...] = (1.0, 1.272, 1.618)


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def _require_pivot(value: object, name: str = "pivot") -> Pivot:
    if not isinstance(value, Pivot):
        raise TypeError(
            f"{name} must be a confirmed Pivot with known_at; "
            "pixel/price guesses are not valid Fibonacci anchors"
        )
    _require_aware(f"{name}.time", value.time)
    _require_aware(f"{name}.known_at", value.known_at)
    if value.known_at < value.time:
        raise ValueError(f"{name}.known_at must be >= {name}.time")
    if value.kind not in {"high", "low"}:
        raise ValueError(f"{name}.kind must be 'high' or 'low'")
    if value.price != value.price:
        raise ValueError(f"{name}.price must be finite")
    return value


def _require_ratio(ratio: float) -> float:
    if ratio != ratio or ratio in {float("inf"), float("-inf")}:
        raise ValueError("ratio must be finite")
    return float(ratio)


def _direction(start: Pivot, end: Pivot) -> SwingDirection | None:
    if end.price > start.price:
        return "up"
    if end.price < start.price:
        return "down"
    return None


def _later(*times: datetime) -> datetime:
    return max(times)


def pivots_known_as_of(pivots: Sequence[Pivot], as_of: datetime) -> list[Pivot]:
    """Return confirmed pivots whose ``known_at`` is at or before ``as_of``."""
    _require_aware("as_of", as_of)
    known: list[Pivot] = []
    for raw in pivots:
        pivot = _require_pivot(raw)
        if pivot.known_at <= as_of:
            known.append(pivot)
    return sorted(known, key=lambda p: (p.time, p.index, p.known_at, p.kind))


def _collapse_same_kind(pivots: Sequence[Pivot]) -> list[Pivot]:
    """Keep the more extreme pivot when consecutive confirmed swings share a kind."""
    out: list[Pivot] = []
    for pivot in pivots:
        if not out or out[-1].kind != pivot.kind:
            out.append(pivot)
            continue
        prev = out[-1]
        if pivot.kind == "high" and pivot.price > prev.price:
            out[-1] = pivot
        elif pivot.kind == "low" and pivot.price < prev.price:
            out[-1] = pivot
    return out


@dataclass(frozen=True, slots=True)
class SwingAnchor:
    """Two opposite-kind confirmed pivots that define one structural swing."""

    start: Pivot
    end: Pivot
    direction: SwingDirection
    known_at: datetime

    def __post_init__(self) -> None:
        _require_pivot(self.start, "start")
        _require_pivot(self.end, "end")
        if self.start.kind == self.end.kind:
            raise ValueError("swing anchors must be opposite-kind pivots")
        if self.direction != _direction(self.start, self.end):
            raise ValueError("direction does not match start/end prices")
        expected = _later(self.start.known_at, self.end.known_at)
        if self.known_at != expected:
            raise ValueError("anchor known_at must be max(start.known_at, end.known_at)")

    @property
    def range(self) -> float:
        return self.end.price - self.start.price


@dataclass(frozen=True, slots=True)
class MeasuredMoveAnchor:
    """A→B swing plus a confirmed C pullback used for AB=CD-style projections."""

    start: Pivot
    end: Pivot
    correction: Pivot
    direction: SwingDirection
    known_at: datetime

    def __post_init__(self) -> None:
        _require_pivot(self.start, "start")
        _require_pivot(self.end, "end")
        _require_pivot(self.correction, "correction")
        if self.start.kind == self.end.kind or self.end.kind == self.correction.kind:
            raise ValueError("measured-move pivots must alternate high/low")
        if self.direction != _direction(self.start, self.end):
            raise ValueError("direction does not match start/end prices")
        expected = _later(self.start.known_at, self.end.known_at, self.correction.known_at)
        if self.known_at != expected:
            raise ValueError("measured-move known_at must be max of A/B/C known_at")


@dataclass(frozen=True, slots=True)
class FibProvenance:
    source: Literal["confirmed_swing"]
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    start_known_at: datetime
    end_known_at: datetime
    start_price: float
    end_price: float
    start_kind: Literal["high", "low"]
    end_kind: Literal["high", "low"]
    correction_index: int | None = None
    correction_time: datetime | None = None
    correction_known_at: datetime | None = None
    correction_price: float | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["start_time"] = self.start_time.isoformat()
        payload["end_time"] = self.end_time.isoformat()
        payload["start_known_at"] = self.start_known_at.isoformat()
        payload["end_known_at"] = self.end_known_at.isoformat()
        if self.correction_time is not None:
            payload["correction_time"] = self.correction_time.isoformat()
        if self.correction_known_at is not None:
            payload["correction_known_at"] = self.correction_known_at.isoformat()
        return payload


@dataclass(frozen=True, slots=True)
class FibLevel:
    """One exact ratio price. Never a guaranteed support/resistance call."""

    kind: LevelKind
    ratio: float
    price: float
    direction: SwingDirection
    known_at: datetime
    status: Literal["candidate"]
    is_guaranteed_support: Literal[False]
    provenance: FibProvenance

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "ratio": self.ratio,
            "price": self.price,
            "direction": self.direction,
            "known_at": self.known_at.isoformat(),
            "status": self.status,
            "is_guaranteed_support": False,
            "role": "context_feature",
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FibFeatureSet:
    as_of: datetime
    anchors: tuple[SwingAnchor, ...]
    measured_moves: tuple[MeasuredMoveAnchor, ...]
    levels: tuple[FibLevel, ...]

    def to_dict(self) -> dict:
        return {
            "as_of": self.as_of.isoformat(),
            "status": "candidate_features",
            "is_guaranteed_support": False,
            "anchor_count": len(self.anchors),
            "measured_move_count": len(self.measured_moves),
            "levels": [level.to_dict() for level in self.levels],
        }


def retracement_price(start_price: float, end_price: float, ratio: float) -> float:
    """Price at ``ratio`` from the end back toward the start (0 = end, 1 = start)."""
    _require_ratio(ratio)
    return end_price + (start_price - end_price) * ratio


def extension_price(start_price: float, end_price: float, ratio: float) -> float:
    """Price at ``ratio`` of the A→B range measured from A (1 = end)."""
    _require_ratio(ratio)
    return start_price + (end_price - start_price) * ratio


def measured_move_price(
    start_price: float,
    end_price: float,
    correction_price: float,
    ratio: float,
) -> float:
    """Project ``ratio * (B - A)`` from the confirmed C pullback (1.0 = AB=CD)."""
    _require_ratio(ratio)
    return correction_price + (end_price - start_price) * ratio


def swing_anchors(pivots: Sequence[Pivot], as_of: datetime) -> list[SwingAnchor]:
    """Opposite-kind confirmed swings knowable at ``as_of``."""
    known = _collapse_same_kind(pivots_known_as_of(pivots, as_of))
    anchors: list[SwingAnchor] = []
    for start, end in zip(known, known[1:]):
        direction = _direction(start, end)
        if direction is None:
            continue
        anchors.append(
            SwingAnchor(
                start=start,
                end=end,
                direction=direction,
                known_at=_later(start.known_at, end.known_at),
            )
        )
    return anchors


def measured_move_anchors(pivots: Sequence[Pivot], as_of: datetime) -> list[MeasuredMoveAnchor]:
    """A→B→C setups where C is a confirmed pullback strictly inside the A→B range."""
    known = _collapse_same_kind(pivots_known_as_of(pivots, as_of))
    setups: list[MeasuredMoveAnchor] = []
    for start, end, correction in zip(known, known[1:], known[2:]):
        direction = _direction(start, end)
        if direction is None:
            continue
        if start.kind == end.kind or end.kind == correction.kind:
            continue
        lo, hi = (start.price, end.price) if start.price < end.price else (end.price, start.price)
        if not (lo < correction.price < hi):
            continue
        setups.append(
            MeasuredMoveAnchor(
                start=start,
                end=end,
                correction=correction,
                direction=direction,
                known_at=_later(start.known_at, end.known_at, correction.known_at),
            )
        )
    return setups


def _swing_provenance(start: Pivot, end: Pivot) -> FibProvenance:
    return FibProvenance(
        source="confirmed_swing",
        start_index=start.index,
        end_index=end.index,
        start_time=start.time,
        end_time=end.time,
        start_known_at=start.known_at,
        end_known_at=end.known_at,
        start_price=start.price,
        end_price=end.price,
        start_kind=start.kind,
        end_kind=end.kind,
    )


def _measured_provenance(start: Pivot, end: Pivot, correction: Pivot) -> FibProvenance:
    return FibProvenance(
        source="confirmed_swing",
        start_index=start.index,
        end_index=end.index,
        start_time=start.time,
        end_time=end.time,
        start_known_at=start.known_at,
        end_known_at=end.known_at,
        start_price=start.price,
        end_price=end.price,
        start_kind=start.kind,
        end_kind=end.kind,
        correction_index=correction.index,
        correction_time=correction.time,
        correction_known_at=correction.known_at,
        correction_price=correction.price,
    )


def _level(
    *,
    kind: LevelKind,
    ratio: float,
    price: float,
    direction: SwingDirection,
    known_at: datetime,
    provenance: FibProvenance,
) -> FibLevel:
    return FibLevel(
        kind=kind,
        ratio=ratio,
        price=price,
        direction=direction,
        known_at=known_at,
        status="candidate",
        is_guaranteed_support=False,
        provenance=provenance,
    )


def fibonacci_features(
    pivots: Sequence[Pivot],
    as_of: datetime,
    *,
    retracement_ratios: Sequence[float] = DEFAULT_RETRACEMENT_RATIOS,
    extension_ratios: Sequence[float] = DEFAULT_EXTENSION_RATIOS,
    measured_move_ratios: Sequence[float] = DEFAULT_MEASURED_MOVE_RATIOS,
) -> FibFeatureSet:
    """Build leakage-safe retracement, extension, and measured-move candidates.

    Parameters
    ----------
    pivots:
        Confirmed structural swings. Raw prices, screenshot geometry, and
        unconfirmed extrema are rejected.
    as_of:
        Inclusive forecast / observation timestamp. A pivot with
        ``known_at > as_of`` is invisible and cannot become an anchor.
    """
    _require_aware("as_of", as_of)
    retracement_ratios = tuple(_require_ratio(r) for r in retracement_ratios)
    extension_ratios = tuple(_require_ratio(r) for r in extension_ratios)
    measured_move_ratios = tuple(_require_ratio(r) for r in measured_move_ratios)

    anchors = tuple(swing_anchors(pivots, as_of))
    setups = tuple(measured_move_anchors(pivots, as_of))
    levels: list[FibLevel] = []

    for anchor in anchors:
        provenance = _swing_provenance(anchor.start, anchor.end)
        for ratio in retracement_ratios:
            levels.append(
                _level(
                    kind="retracement",
                    ratio=ratio,
                    price=retracement_price(anchor.start.price, anchor.end.price, ratio),
                    direction=anchor.direction,
                    known_at=anchor.known_at,
                    provenance=provenance,
                )
            )
        for ratio in extension_ratios:
            levels.append(
                _level(
                    kind="extension",
                    ratio=ratio,
                    price=extension_price(anchor.start.price, anchor.end.price, ratio),
                    direction=anchor.direction,
                    known_at=anchor.known_at,
                    provenance=provenance,
                )
            )

    for setup in setups:
        provenance = _measured_provenance(setup.start, setup.end, setup.correction)
        for ratio in measured_move_ratios:
            levels.append(
                _level(
                    kind="measured_move",
                    ratio=ratio,
                    price=measured_move_price(
                        setup.start.price,
                        setup.end.price,
                        setup.correction.price,
                        ratio,
                    ),
                    direction=setup.direction,
                    known_at=setup.known_at,
                    provenance=provenance,
                )
            )

    return FibFeatureSet(
        as_of=as_of,
        anchors=anchors,
        measured_moves=setups,
        levels=tuple(levels),
    )
