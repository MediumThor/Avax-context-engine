"""Structural zone lifecycle: ranges with probe/acceptance/reclaim provenance.

Zones are ranges (lower/upper), never thin lines. Bounds are frozen at
creation (Constitution §3 — no moving invalidation after the fact).
A wick through a zone is a probe, not acceptance. Acceptance requires a
configurable close count and/or ATR distance beyond the far edge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Iterable, Literal, Sequence
import hashlib
import json

from .indicators import atr as wilder_atr
from .models import Candle, Pivot, StructuralZone
from .structure import cluster_zones

ZoneRole = Literal["support", "resistance", "mixed"]
Interaction = Literal[
    "approaching",
    "testing",
    "rejected",
    "penetrated",
    "accepted",
    "retesting",
    "reclaimed",
    "retired",
]
ZoneStatus = Literal["active", "broken", "reclaimed", "retired"]
AcceptanceMode = Literal["close_count", "atr_distance", "either", "both"]
BreakDirection = Literal["up", "down"]
Outcome = Literal[
    "held",
    "failed_breakout",
    "failed_breakdown",
    "accepted_through",
    "successful_reclaim",
]
BandPosition = Literal["below", "inside", "above"]

INTERACTIONS: tuple[Interaction, ...] = (
    "approaching",
    "testing",
    "rejected",
    "penetrated",
    "accepted",
    "retesting",
    "reclaimed",
    "retired",
)

MIN_RANGE_PCT = 0.001


class ImmutableZoneBoundsError(Exception):
    """Raised when an agent tries to move a zone after it was created."""


class ZoneNotFoundError(KeyError):
    """Raised when a zone id is not in the tracker."""


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _zone_id(lower: float, upper: float, role: str) -> str:
    return hashlib.sha1(f"{lower:.8f}:{upper:.8f}:{role}".encode()).hexdigest()[:12]


def as_range(
    lower: float,
    upper: float,
    *,
    ref_price: float | None = None,
    atr_value: float | None = None,
    min_pct: float = MIN_RANGE_PCT,
) -> tuple[float, float]:
    """Return an ordered (lower, upper) band. Degenerate lines are padded into ranges."""
    if lower != lower or upper != upper:
        raise ValueError("zone bounds must be finite")
    lo, hi = (lower, upper) if lower <= upper else (upper, lower)
    width = hi - lo
    ref = ref_price if ref_price is not None else ((lo + hi) / 2.0 or 1.0)
    min_width = max(abs(ref) * min_pct, (atr_value or 0.0) * 0.25, 1e-8)
    if width < min_width:
        mid = (lo + hi) / 2.0
        half = min_width / 2.0
        return mid - half, mid + half
    return lo, hi


def _usable_atr(atr_value: float | None, ref: float, fallback_pct: float) -> float:
    if atr_value is not None and atr_value == atr_value and atr_value > 0.0:
        return float(atr_value)
    return max(abs(ref) * fallback_pct, 1e-8)


def _band_position(lower: float, upper: float, price: float) -> BandPosition:
    if price < lower:
        return "below"
    if price > upper:
        return "above"
    return "inside"


def _intersects(lower: float, upper: float, candle: Candle) -> bool:
    return candle.high >= lower and candle.low <= upper


def _is_beyond(break_direction: BreakDirection, position: BandPosition) -> bool:
    return position == ("above" if break_direction == "up" else "below")


def _is_origin(break_direction: BreakDirection, position: BandPosition) -> bool:
    return position == ("below" if break_direction == "up" else "above")


def _acceptance(
    count: int,
    need: int,
    atr_hit: bool,
    mode: AcceptanceMode,
    on_side: bool,
) -> bool:
    if not on_side:
        return False
    if mode == "close_count":
        return count >= need
    if mode == "atr_distance":
        return atr_hit
    if mode == "both":
        return count >= need and atr_hit
    return count >= need or atr_hit


def atrs_through(candles: Sequence[Candle], period: int = 14) -> list[float | None]:
    """Wilder ATR at each index using only candles through that index."""
    if not candles:
        return []
    return wilder_atr(
        [c.high for c in candles],
        [c.low for c in candles],
        [c.close for c in candles],
        period,
    )


def _candle_hash(candle: Candle) -> str:
    payload = {
        "symbol": candle.symbol,
        "timeframe": candle.timeframe,
        "open_time": candle.open_time.isoformat(),
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "volume": candle.volume,
    }
    return "sha256:" + hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _status_for(interaction: Interaction) -> ZoneStatus:
    if interaction == "retired":
        return "retired"
    if interaction == "reclaimed":
        return "reclaimed"
    if interaction in {"accepted", "retesting"}:
        return "broken"
    return "active"


def _strength(base: float, tests: int, interaction: Interaction) -> float:
    if interaction in {"accepted", "retesting"}:
        return max(0.0, min(1.0, base * 0.45))
    if interaction == "reclaimed":
        return max(0.0, min(1.0, base + 0.10 * tests))
    if interaction == "rejected":
        return max(0.0, min(1.0, base + 0.08 * tests))
    return max(0.0, min(1.0, base + 0.04 * tests))


def _infer_break_direction(role: ZoneRole, lower: float, upper: float, close: float) -> BreakDirection:
    if role == "resistance":
        return "up"
    if role == "support":
        return "down"
    mid = (lower + upper) / 2.0
    return "up" if close <= mid else "down"


def _outcome_for(
    *,
    interaction: Interaction,
    accepted_through: bool,
    break_direction: BreakDirection,
    prior: Outcome | None,
) -> Outcome | None:
    if interaction == "reclaimed":
        if break_direction == "up":
            return "failed_breakout"
        if accepted_through:
            return "successful_reclaim"
        return "failed_breakdown"
    if interaction in {"accepted", "retesting"}:
        return "accepted_through"
    if interaction == "retired":
        return prior
    if interaction == "rejected":
        return "held"
    return None


@dataclass(frozen=True, slots=True)
class AcceptanceConfig:
    """Acceptance is never wick-based. Close count and/or ATR distance must fire."""

    close_count: int = 2
    atr_multiple: float = 0.5
    mode: AcceptanceMode = "either"
    approach_atr: float = 1.5
    retire_atr: float = 4.0
    atr_fallback_pct: float = 0.01
    volume_multiple: float | None = None

    def __post_init__(self) -> None:
        if self.close_count < 1:
            raise ValueError("close_count must be >= 1")
        if self.atr_multiple < 0.0:
            raise ValueError("atr_multiple must be >= 0")
        if self.mode not in {"close_count", "atr_distance", "either", "both"}:
            raise ValueError(f"unsupported acceptance mode: {self.mode}")


@dataclass(frozen=True, slots=True)
class ZoneSpec:
    """Immutable declared range. Bounds cannot be rewritten later."""

    lower: float
    upper: float
    role: ZoneRole
    id: str = ""
    symbol: str = "AVAXUSDT"
    timeframes: tuple[str, ...] = ("5m",)
    sources: tuple[str, ...] = ("declared",)
    strength: float = 0.4
    created_at: datetime | None = None
    known_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.role not in {"support", "resistance", "mixed"}:
            raise ValueError(f"unsupported role: {self.role}")
        if self.created_at is not None:
            _require_aware("created_at", self.created_at)
        if self.known_at is not None:
            _require_aware("known_at", self.known_at)
        lo, hi = as_range(self.lower, self.upper)
        object.__setattr__(self, "lower", lo)
        object.__setattr__(self, "upper", hi)
        if not self.id:
            object.__setattr__(self, "id", _zone_id(lo, hi, self.role))
        if self.strength != self.strength or not (0.0 <= self.strength <= 1.0):
            raise ValueError("strength must be in [0, 1]")

    def with_bounds(self, _lower: float, _upper: float) -> ZoneSpec:
        raise ImmutableZoneBoundsError(
            f"zone {self.id} bounds are frozen at [{self.lower}, {self.upper}]; "
            "close this zone and open a new one instead of moving invalidation"
        )


@dataclass(frozen=True, slots=True)
class ZoneProvenance:
    at: datetime
    entity: str
    from_state: Interaction | Literal["none"]
    to_state: Interaction
    cause: tuple[str, ...]
    close: float
    known_at: datetime
    input_snapshot: str
    timeframe: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["at"] = self.at.isoformat()
        payload["known_at"] = self.known_at.isoformat()
        payload["cause"] = list(self.cause)
        return payload


@dataclass(frozen=True, slots=True)
class TrackedZone:
    id: str
    symbol: str
    lower: float
    upper: float
    role: ZoneRole
    interaction: Interaction
    status: ZoneStatus
    timeframes: tuple[str, ...]
    sources: tuple[str, ...]
    strength: float
    tests: int
    last_test_at: datetime | None
    created_at: datetime
    known_at: datetime
    provenance: tuple[ZoneProvenance, ...] = ()
    outcome: Outcome | None = None
    break_direction: BreakDirection = "up"
    closes_beyond: int = 0
    closes_origin: int = 0
    saw_close_beyond: bool = False
    accepted_through: bool = False
    last_transition_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_aware("created_at", self.created_at)
        _require_aware("known_at", self.known_at)
        if self.lower >= self.upper:
            raise ValueError("zone must be a range: lower < upper")
        if self.interaction not in INTERACTIONS:
            raise ValueError(f"unsupported interaction: {self.interaction}")

    @property
    def kind(self) -> ZoneRole:
        return self.role

    @property
    def test_count(self) -> int:
        return self.tests

    def with_bounds(self, _lower: float, _upper: float) -> TrackedZone:
        raise ImmutableZoneBoundsError(
            f"zone {self.id} bounds are frozen at [{self.lower}, {self.upper}]; "
            "cannot move invalidation after the fact"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "lower": self.lower,
            "upper": self.upper,
            "kind": self.role,
            "role": self.role,
            "status": self.status,
            "interaction": self.interaction,
            "timeframes": list(self.timeframes),
            "sources": list(self.sources),
            "strength": self.strength,
            "tests": self.tests,
            "test_count": self.tests,
            "last_test_at": self.last_test_at.isoformat() if self.last_test_at else None,
            "created_at": self.created_at.isoformat(),
            "known_at": self.known_at.isoformat(),
            "provenance": [event.to_dict() for event in self.provenance],
            "outcome": self.outcome,
            "break_direction": self.break_direction,
        }


def spec_from_structural(
    zone: StructuralZone,
    *,
    symbol: str = "AVAXUSDT",
    timeframes: Sequence[str] = ("5m",),
    known_at: datetime | None = None,
    atr_value: float | None = None,
) -> ZoneSpec:
    lower, upper = as_range(zone.lower, zone.upper, atr_value=atr_value)
    sources = (zone.source,) if getattr(zone, "source", None) else ("pivot_cluster",)
    return ZoneSpec(
        id=zone.id,
        lower=lower,
        upper=upper,
        role=zone.role,
        symbol=symbol,
        timeframes=tuple(timeframes),
        sources=sources,
        strength=max(0.0, min(1.0, zone.strength)),
        known_at=known_at,
    )


def specs_from_pivots(
    pivots: Sequence[Pivot],
    current_price: float,
    *,
    symbol: str = "AVAXUSDT",
    timeframes: Sequence[str] = ("5m",),
    known_at: datetime | None = None,
    atr_value: float | None = None,
    tolerance_pct: float = 0.006,
) -> list[ZoneSpec]:
    clustered = cluster_zones(list(pivots), current_price, tolerance_pct=tolerance_pct)
    return [
        spec_from_structural(
            zone,
            symbol=symbol,
            timeframes=timeframes,
            known_at=known_at,
            atr_value=atr_value,
        )
        for zone in clustered
    ]


@dataclass
class ZoneTracker:
    """Walk closed candles forward. Never uses a later candle to rewrite earlier state."""

    specs: Sequence[ZoneSpec]
    config: AcceptanceConfig = field(default_factory=AcceptanceConfig)
    _zones: dict[str, TrackedZone] = field(default_factory=dict, init=False, repr=False)
    _events: list[ZoneProvenance] = field(default_factory=list, init=False, repr=False)
    _order: tuple[str, ...] = field(default_factory=tuple, init=False, repr=False)

    def __post_init__(self) -> None:
        specs = tuple(self.specs)
        ids = [spec.id for spec in specs]
        if len(ids) != len(set(ids)):
            raise ValueError("zone ids must be unique")
        object.__setattr__(self, "specs", specs)
        object.__setattr__(self, "_order", tuple(ids))
        object.__setattr__(self, "_pending", {spec.id: spec for spec in specs})

    def current(self) -> tuple[TrackedZone, ...]:
        return tuple(self._zones[zone_id] for zone_id in self._order if zone_id in self._zones)

    def get(self, zone_id: str) -> TrackedZone:
        if zone_id not in self._zones:
            raise ZoneNotFoundError(zone_id)
        return self._zones[zone_id]

    def events(self) -> tuple[ZoneProvenance, ...]:
        return tuple(self._events)

    def relocate(self, zone_id: str, lower: float, upper: float) -> TrackedZone:
        """Forbidden: moving a live or closed zone's bounds after creation."""
        if zone_id in self._zones:
            zone = self._zones[zone_id]
            self._events.append(
                ZoneProvenance(
                    at=zone.last_transition_at or zone.known_at,
                    entity=zone.id,
                    from_state=zone.interaction,
                    to_state=zone.interaction,
                    cause=("rejected_bounds_move",),
                    close=(zone.lower + zone.upper) / 2.0,
                    known_at=zone.known_at,
                    input_snapshot="sha256:refused",
                    timeframe=zone.timeframes[0] if zone.timeframes else "unknown",
                )
            )
            zone.with_bounds(lower, upper)
        pending = getattr(self, "_pending", {})
        if zone_id in pending:
            pending[zone_id].with_bounds(lower, upper)
        raise ZoneNotFoundError(zone_id)

    def ingest(self, candle: Candle, atr_value: float | None = None) -> tuple[TrackedZone, ...]:
        if not candle.is_closed:
            return self.current()
        _require_aware("candle.open_time", candle.open_time)
        pending: dict[str, ZoneSpec] = getattr(self, "_pending")
        for spec in self.specs:
            if spec.id not in self._zones:
                self._zones[spec.id] = self._open(spec, candle)
                pending.pop(spec.id, None)
            current = self._zones[spec.id]
            nxt = self._step(current, candle, atr_value)
            if nxt.interaction != current.interaction or nxt.tests != current.tests:
                self._zones[spec.id] = nxt
            else:
                self._zones[spec.id] = nxt
        return self.current()

    def replay(
        self,
        candles: Sequence[Candle],
        atrs: Sequence[float | None] | None = None,
    ) -> tuple[TrackedZone, ...]:
        series = list(candles)
        values: Sequence[float | None]
        if atrs is None:
            values = atrs_through(series)
        else:
            if len(atrs) != len(series):
                raise ValueError("atrs length must match candles")
            values = atrs
        for candle, atr_i in zip(series, values, strict=True):
            self.ingest(candle, atr_i)
        return self.current()

    def _open(self, spec: ZoneSpec, candle: Candle) -> TrackedZone:
        known = spec.known_at if spec.known_at is not None else candle.open_time
        if known > candle.open_time:
            known = candle.open_time
        created = spec.created_at if spec.created_at is not None else candle.open_time
        if created > candle.open_time:
            created = candle.open_time
        direction = _infer_break_direction(spec.role, spec.lower, spec.upper, candle.close)
        event = ZoneProvenance(
            at=candle.open_time,
            entity=spec.id,
            from_state="none",
            to_state="approaching",
            cause=("opened", "range_declared"),
            close=candle.close,
            known_at=known,
            input_snapshot=_candle_hash(candle),
            timeframe=candle.timeframe,
        )
        self._events.append(event)
        return TrackedZone(
            id=spec.id,
            symbol=spec.symbol,
            lower=spec.lower,
            upper=spec.upper,
            role=spec.role,
            interaction="approaching",
            status="active",
            timeframes=spec.timeframes,
            sources=spec.sources,
            strength=spec.strength,
            tests=0,
            last_test_at=None,
            created_at=created,
            known_at=known,
            provenance=(event,),
            outcome=None,
            break_direction=direction,
        )

    def _step(self, zone: TrackedZone, candle: Candle, atr_value: float | None) -> TrackedZone:
        if zone.interaction == "retired":
            return zone

        mid = (zone.lower + zone.upper) / 2.0
        usable = _usable_atr(atr_value, mid, self.config.atr_fallback_pct)
        position = _band_position(zone.lower, zone.upper, candle.close)
        intersects = _intersects(zone.lower, zone.upper, candle)
        beyond = _is_beyond(zone.break_direction, position)
        origin = _is_origin(zone.break_direction, position)
        atr_beyond = (
            candle.close >= zone.upper + self.config.atr_multiple * usable
            if zone.break_direction == "up"
            else candle.close <= zone.lower - self.config.atr_multiple * usable
        )
        atr_origin = (
            candle.close <= zone.lower - self.config.atr_multiple * usable
            if zone.break_direction == "up"
            else candle.close >= zone.upper + self.config.atr_multiple * usable
        )
        if beyond:
            closes_beyond = zone.closes_beyond + 1
            closes_origin = 0
            saw_close_beyond = True
        elif origin:
            closes_beyond = 0
            closes_origin = zone.closes_origin + 1
            saw_close_beyond = zone.saw_close_beyond
        else:
            closes_beyond = 0
            closes_origin = 0
            saw_close_beyond = zone.saw_close_beyond

        if self.config.volume_multiple is not None and beyond and candle.volume > 0:
            # Optional volume expansion counts as one extra close toward acceptance.
            if candle.volume >= self.config.volume_multiple:
                closes_beyond += 1

        accept = _acceptance(
            closes_beyond, self.config.close_count, atr_beyond, self.config.mode, beyond
        )
        reclaim_accept = _acceptance(
            closes_origin, self.config.close_count, atr_origin, self.config.mode, origin
        )
        distance_beyond = (
            candle.close - zone.upper if zone.break_direction == "up" else zone.lower - candle.close
        )
        distance_origin = (
            zone.lower - candle.close if zone.break_direction == "up" else candle.close - zone.upper
        )
        far_beyond = beyond and distance_beyond >= self.config.retire_atr * usable
        far_origin = origin and distance_origin >= self.config.retire_atr * usable
        accepted_through = zone.accepted_through or accept

        nxt, causes = self._transition(
            zone=zone,
            accept=accept,
            reclaim_accept=reclaim_accept,
            beyond=beyond,
            origin=origin,
            intersects=intersects,
            far_beyond=far_beyond,
            far_origin=far_origin,
            accepted_through=accepted_through,
            saw_close_beyond=saw_close_beyond or zone.saw_close_beyond,
            close_in_zone=position == "inside",
        )
        tests = zone.tests
        last_test_at = zone.last_test_at
        if nxt == "testing" and zone.interaction != "testing":
            tests += 1
            last_test_at = candle.open_time
        outcome = _outcome_for(
            interaction=nxt,
            accepted_through=accepted_through and nxt != "rejected",
            break_direction=zone.break_direction,
            prior=zone.outcome,
        )
        if nxt == zone.interaction and tests == zone.tests:
            return replace(
                zone,
                closes_beyond=closes_beyond,
                closes_origin=closes_origin,
                saw_close_beyond=saw_close_beyond,
                accepted_through=accepted_through,
                outcome=outcome if nxt == "rejected" else zone.outcome,
                strength=_strength(self._base_strength(zone), tests, nxt),
            )

        event = ZoneProvenance(
            at=candle.open_time,
            entity=zone.id,
            from_state=zone.interaction,
            to_state=nxt,
            cause=causes,
            close=candle.close,
            known_at=candle.open_time,
            input_snapshot=_candle_hash(candle),
            timeframe=candle.timeframe,
        )
        self._events.append(event)
        return replace(
            zone,
            interaction=nxt,
            status=_status_for(nxt),
            strength=_strength(self._base_strength(zone), tests, nxt),
            tests=tests,
            last_test_at=last_test_at,
            provenance=zone.provenance + (event,),
            outcome=outcome,
            closes_beyond=closes_beyond,
            closes_origin=closes_origin,
            saw_close_beyond=saw_close_beyond,
            accepted_through=accepted_through,
            last_transition_at=candle.open_time,
        )

    def _base_strength(self, zone: TrackedZone) -> float:
        for spec in self.specs:
            if spec.id == zone.id:
                return spec.strength
        return zone.strength

    def _transition(
        self,
        *,
        zone: TrackedZone,
        accept: bool,
        reclaim_accept: bool,
        beyond: bool,
        origin: bool,
        intersects: bool,
        far_beyond: bool,
        far_origin: bool,
        accepted_through: bool,
        saw_close_beyond: bool,
        close_in_zone: bool,
    ) -> tuple[Interaction, tuple[str, ...]]:
        state = zone.interaction
        probe = ("probe",) if intersects and not close_in_zone and not beyond else ()
        in_zone = ("close_in_zone",) if close_in_zone else ()
        beyond_cause = ("close_beyond",) if beyond else ()
        accept_cause = ("acceptance_beyond",) if accept else ()
        fail_label = "failed_breakout" if zone.break_direction == "up" else "failed_breakdown"

        if state == "reclaimed":
            if far_origin:
                return "retired", ("retired_extended_origin", "bounds_frozen")
            return "reclaimed", ("bounds_frozen",)

        if state == "accepted":
            if accepted_through and reclaim_accept:
                reclaim_kind = (
                    "failed_breakout" if zone.break_direction == "up" else "successful_reclaim"
                )
                return "reclaimed", ("reclaim_acceptance", reclaim_kind)
            if origin or (intersects and not beyond):
                return "retesting", ("retest_opposite_side",)
            if far_beyond:
                return "retired", ("retired_extended_beyond", "accepted_through")
            return "accepted", beyond_cause or ("hold_beyond",)

        if state == "retesting":
            if reclaim_accept:
                return "reclaimed", ("reclaim_acceptance", "successful_reclaim")
            if accept or (beyond and not intersects):
                return "accepted", ("retest_held",) + accept_cause
            return "retesting", ("retest_opposite_side",) + in_zone

        if state == "penetrated":
            if accept:
                return "accepted", ("acceptance_beyond",) + beyond_cause
            if origin:
                seen = ("had_close_beyond",) if saw_close_beyond else ()
                return "reclaimed", ("failed_hold", fail_label, "close_origin") + seen
            if not beyond and intersects:
                return "testing", ("pullback_into_zone",) + in_zone
            return "penetrated", beyond_cause or ("still_beyond",)

        if state == "testing":
            if accept:
                return "accepted", ("acceptance_beyond",) + beyond_cause
            if beyond:
                return "penetrated", ("close_beyond",)
            if origin:
                return "rejected", ("rejected_close_origin",)
            return "testing", probe or in_zone or ("still_testing",)

        if state == "rejected":
            if accept:
                return "accepted", ("acceptance_beyond",) + beyond_cause
            if beyond:
                return "penetrated", ("close_beyond",)
            if intersects:
                return "testing", probe or in_zone or ("repeat_test",)
            return "rejected", ("held",)

        # approaching (and any unexpected active state)
        if accept:
            return "accepted", ("acceptance_beyond",) + beyond_cause
        if beyond:
            return "penetrated", ("close_beyond",)
        if intersects:
            return "testing", probe or in_zone or ("test",)
        return "approaching", ("approaching",)


def track_zones(
    candles: Sequence[Candle],
    specs: Sequence[ZoneSpec] | Iterable[ZoneSpec],
    *,
    config: AcceptanceConfig | None = None,
    atrs: Sequence[float | None] | None = None,
) -> ZoneTracker:
    tracker = ZoneTracker(tuple(specs), config=config or AcceptanceConfig())
    tracker.replay(candles, atrs)
    return tracker
