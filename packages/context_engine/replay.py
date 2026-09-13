"""Deterministic Context Engine snapshot persistence and historical replay.

This module does not reimplement regime logic. It filters candles so a query at
time T only sees closed bars whose period end is <= T, then calls ContextEngine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from .engine import TIMEFRAMES, ContextEngine
from .models import Candle, MarketSnapshot

ENGINE_VERSION = "1"
SCHEMA_VERSION = "1"

_TIMEFRAME_MINUTES: dict[str, int] = dict(TIMEFRAMES)
_TIMEFRAME_MINUTES.setdefault("1w", 10080)


def require_utc(dt: datetime) -> datetime:
    if not isinstance(dt, datetime):
        raise TypeError("timestamp must be a datetime")
    if dt.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware UTC")
    return dt.astimezone(timezone.utc)


def iso_utc(dt: datetime) -> str:
    dt = require_utc(dt)
    if dt.microsecond:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def timeframe_minutes(timeframe: str) -> int:
    if timeframe in _TIMEFRAME_MINUTES:
        return _TIMEFRAME_MINUTES[timeframe]
    if len(timeframe) < 2:
        raise ValueError(f"unknown timeframe: {timeframe}")
    unit = timeframe[-1]
    try:
        count = int(timeframe[:-1])
    except ValueError as exc:
        raise ValueError(f"unknown timeframe: {timeframe}") from exc
    if count <= 0:
        raise ValueError(f"unknown timeframe: {timeframe}")
    if unit == "m":
        return count
    if unit == "h":
        return count * 60
    if unit == "d":
        return count * 1440
    if unit == "w":
        return count * 10080
    raise ValueError(f"unknown timeframe: {timeframe}")


def period_end(candle: Candle) -> datetime:
    return require_utc(candle.open_time) + timedelta(minutes=timeframe_minutes(candle.timeframe))


def _candle_sort_key(candle: Candle) -> tuple:
    return (
        require_utc(candle.open_time),
        candle.symbol,
        candle.timeframe,
        candle.open,
        candle.high,
        candle.low,
        candle.close,
        candle.volume,
        candle.is_closed,
    )


def _jsonable(value: object) -> object:
    if isinstance(value, datetime):
        return iso_utc(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"value is not JSON-serializable: {type(value)!r}")


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _engine_version(engine: ContextEngine) -> str:
    for attr in ("ENGINE_VERSION", "VERSION", "engine_version"):
        value = getattr(engine, attr, None)
        if value:
            return str(value)
    return ENGINE_VERSION


def _fingerprint(snapshot_dict: dict) -> dict:
    values: dict[str, object] = {}
    timeframes = snapshot_dict.get("timeframes") or {}
    for timeframe in sorted(timeframes):
        state = timeframes[timeframe]
        values[f"regime_{timeframe}"] = state.get("regime")
        values[f"swing_{timeframe}"] = state.get("swing_state")
        values[f"volatility_{timeframe}"] = state.get("volatility")
    return {
        "schema_version": SCHEMA_VERSION,
        "values": values,
    }


def _candle_record(candle: Candle) -> dict:
    return {
        "close": candle.close,
        "high": candle.high,
        "is_closed": candle.is_closed,
        "low": candle.low,
        "open": candle.open,
        "open_time": iso_utc(candle.open_time),
        "symbol": candle.symbol,
        "timeframe": candle.timeframe,
        "volume": candle.volume,
    }


def source_data_hash(candles: Sequence[Candle]) -> str:
    records = [_candle_record(c) for c in candles]
    return "sha256:" + sha256_hex(canonical_json(records))


def knowable_candles(candles: Sequence[Candle], as_of: datetime) -> list[Candle]:
    """Closed candles whose period end is <= as_of, sorted deterministically."""
    cutoff = require_utc(as_of)
    visible: list[Candle] = []
    for candle in candles:
        require_utc(candle.open_time)
        if not candle.is_closed:
            continue
        if period_end(candle) <= cutoff:
            visible.append(candle)
    return sorted(visible, key=_candle_sort_key)


@dataclass(frozen=True, slots=True)
class PersistedSnapshot:
    engine_version: str
    schema_version: str
    symbol: str
    as_of: datetime
    known_at: datetime
    source_data_hash: str
    payload_sha256: str
    canonical_json: str

    def to_bytes(self) -> bytes:
        return self.canonical_json.encode("utf-8")

    def to_dict(self) -> dict:
        return json.loads(self.canonical_json)

    @property
    def timeframes(self) -> dict:
        return self.to_dict()["timeframes"]

    @property
    def fingerprint(self) -> dict:
        return self.to_dict()["fingerprint"]


@dataclass(frozen=True, slots=True)
class StateTransition:
    at: datetime
    entity: str
    from_regime: str
    to_regime: str
    cause: tuple[str, ...]
    input_snapshot: str


@dataclass(frozen=True, slots=True)
class ReplayResult:
    engine_version: str
    schema_version: str
    snapshots: tuple[PersistedSnapshot, ...]
    transitions: tuple[StateTransition, ...]

    def as_of(self, when: datetime) -> PersistedSnapshot:
        cutoff = require_utc(when)
        chosen: PersistedSnapshot | None = None
        for snapshot in self.snapshots:
            if snapshot.known_at <= cutoff:
                chosen = snapshot
            else:
                break
        if chosen is None:
            raise ValueError("Need at least one closed candle knowable at as_of")
        return chosen


def persist_snapshot(
    snapshot: MarketSnapshot,
    *,
    known_at: datetime,
    source_data_hash: str,
    engine_version: str = ENGINE_VERSION,
) -> PersistedSnapshot:
    raw = _jsonable(snapshot.to_dict())
    if not isinstance(raw, dict):
        raise TypeError("snapshot.to_dict() must produce a mapping")
    schema_version = str(raw.get("schema_version") or SCHEMA_VERSION)
    payload = {
        "as_of": raw["as_of"],
        "engine_version": engine_version,
        "fingerprint": _fingerprint(raw),
        "known_at": iso_utc(known_at),
        "schema_version": schema_version,
        "source_data_hash": source_data_hash,
        "symbol": snapshot.symbol,
        "timeframes": raw["timeframes"],
    }
    encoded = canonical_json(payload)
    return PersistedSnapshot(
        engine_version=engine_version,
        schema_version=schema_version,
        symbol=snapshot.symbol,
        as_of=require_utc(snapshot.as_of),
        known_at=require_utc(known_at),
        source_data_hash=source_data_hash,
        payload_sha256=sha256_hex(encoded),
        canonical_json=encoded,
    )


def _regime_causes(state: dict) -> tuple[str, ...]:
    evidence = state.get("evidence") or []
    return tuple(str(item) for item in evidence)


def _diff_transitions(previous: PersistedSnapshot | None, current: PersistedSnapshot) -> list[StateTransition]:
    if previous is None:
        return []
    transitions: list[StateTransition] = []
    prev_tfs = previous.timeframes
    curr_tfs = current.timeframes
    digest = f"sha256:{current.payload_sha256}"
    for timeframe in sorted(set(prev_tfs) | set(curr_tfs)):
        old = prev_tfs.get(timeframe)
        new = curr_tfs.get(timeframe)
        if new is None:
            continue
        old_regime = old["regime"] if old is not None else "unknown"
        new_regime = new["regime"]
        if old_regime == new_regime:
            continue
        transitions.append(
            StateTransition(
                at=current.known_at,
                entity=f"{current.symbol}:{timeframe}",
                from_regime=old_regime,
                to_regime=new_regime,
                cause=_regime_causes(new),
                input_snapshot=digest,
            )
        )
    return transitions


class ContextReplay:
    """Filter-then-call replay facade over ContextEngine."""

    def __init__(self, engine: ContextEngine | None = None) -> None:
        self.engine = engine or ContextEngine()
        self.engine_version = _engine_version(self.engine)

    def knowable_candles(self, candles: Sequence[Candle], as_of: datetime) -> list[Candle]:
        return knowable_candles(candles, as_of)

    def snapshot_as_of(self, candles: Sequence[Candle], as_of: datetime) -> PersistedSnapshot:
        visible = knowable_candles(candles, as_of)
        if not visible:
            raise ValueError("Need at least one closed candle knowable at as_of")
        snapshot = self.engine.build_snapshot(visible)
        known_at = max(period_end(c) for c in visible)
        return persist_snapshot(
            snapshot,
            known_at=known_at,
            source_data_hash=source_data_hash(visible),
            engine_version=self.engine_version,
        )

    def replay(self, candles: Sequence[Candle]) -> ReplayResult:
        closed = [c for c in candles if c.is_closed]
        if not closed:
            raise ValueError("Need at least one closed candle")
        for candle in candles:
            require_utc(candle.open_time)
        steps = sorted({period_end(c) for c in closed})
        snapshots: list[PersistedSnapshot] = []
        transitions: list[StateTransition] = []
        previous: PersistedSnapshot | None = None
        for step in steps:
            current = self.snapshot_as_of(candles, step)
            snapshots.append(current)
            transitions.extend(_diff_transitions(previous, current))
            previous = current
        return ReplayResult(
            engine_version=self.engine_version,
            schema_version=SCHEMA_VERSION,
            snapshots=tuple(snapshots),
            transitions=tuple(transitions),
        )


def snapshot_as_of(
    candles: Sequence[Candle],
    as_of: datetime,
    *,
    engine: ContextEngine | None = None,
) -> PersistedSnapshot:
    return ContextReplay(engine).snapshot_as_of(candles, as_of)


def replay(
    candles: Sequence[Candle],
    *,
    engine: ContextEngine | None = None,
) -> ReplayResult:
    return ContextReplay(engine).replay(candles)


def replay_bytes(candles: Iterable[Candle], *, engine: ContextEngine | None = None) -> bytes:
    result = ContextReplay(engine).replay(list(candles))
    payload = {
        "engine_version": result.engine_version,
        "schema_version": result.schema_version,
        "snapshots": [json.loads(item.canonical_json) for item in result.snapshots],
        "transitions": [
            {
                "at": iso_utc(item.at),
                "cause": list(item.cause),
                "entity": item.entity,
                "from": item.from_regime,
                "input_snapshot": item.input_snapshot,
                "to": item.to_regime,
            }
            for item in result.transitions
        ],
    }
    return canonical_json(payload).encode("utf-8")
