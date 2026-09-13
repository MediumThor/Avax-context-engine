from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .schema import FEATURE_NAMES, FEATURE_SCHEMA_VERSION


def require_aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return require_aware(value, field_name="datetime").isoformat()


@dataclass(frozen=True, slots=True)
class FeatureCandle:
    """Closed-or-partial OHLCV bar. Unfinished bars are never assembled."""

    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool = True

    def __post_init__(self) -> None:
        require_aware(self.open_time, field_name="FeatureCandle.open_time")
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC ordering")


@dataclass(frozen=True, slots=True)
class AvailabilityRecord:
    """When a timeframe's last completed bar became knowable."""

    timeframe: str
    last_closed_open_time: datetime | None
    known_at: datetime | None
    closed_bar_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "last_closed_open_time": isoformat_utc(self.last_closed_open_time),
            "known_at": isoformat_utc(self.known_at),
            "closed_bar_count": self.closed_bar_count,
        }


@dataclass(frozen=True, slots=True)
class FeatureSnapshot:
    feature_schema_version: str
    symbol: str
    as_of: datetime
    known_at: datetime
    values: dict[str, float | None]
    availability: dict[str, AvailabilityRecord]
    source_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_aware(self.as_of, field_name="FeatureSnapshot.as_of")
        require_aware(self.known_at, field_name="FeatureSnapshot.known_at")
        if self.feature_schema_version != FEATURE_SCHEMA_VERSION:
            raise ValueError("feature_schema_version does not match assembler schema")
        missing = [name for name in FEATURE_NAMES if name not in self.values]
        if missing:
            raise ValueError(f"snapshot missing schema fields: {missing[:8]}")
        extra = [name for name in self.values if name not in FEATURE_NAMES]
        if extra:
            raise ValueError(f"snapshot has unknown fields: {extra[:8]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_schema_version": self.feature_schema_version,
            "symbol": self.symbol,
            "as_of": isoformat_utc(self.as_of),
            "known_at": isoformat_utc(self.known_at),
            "values": dict(self.values),
            "availability": {key: rec.to_dict() for key, rec in self.availability.items()},
            "source_counts": dict(self.source_counts),
        }

    def feature_vector(self) -> list[float | None]:
        return [self.values[name] for name in FEATURE_NAMES]


def candle_from_mapping(record: Mapping[str, Any]) -> FeatureCandle:
    open_time = record["open_time"]
    if isinstance(open_time, str):
        open_time = datetime.fromisoformat(open_time.replace("Z", "+00:00"))
    return FeatureCandle(
        symbol=str(record["symbol"]),
        timeframe=str(record.get("timeframe", "5m")),
        open_time=open_time,
        open=float(record["open"]),
        high=float(record["high"]),
        low=float(record["low"]),
        close=float(record["close"]),
        volume=float(record["volume"]),
        is_closed=bool(record.get("is_closed", True)),
    )


def as_feature_candle(record: Any) -> FeatureCandle:
    if isinstance(record, FeatureCandle):
        return record
    if isinstance(record, Mapping):
        return candle_from_mapping(record)
    return FeatureCandle(
        symbol=record.symbol,
        timeframe=record.timeframe,
        open_time=record.open_time,
        open=float(record.open),
        high=float(record.high),
        low=float(record.low),
        close=float(record.close),
        volume=float(record.volume),
        is_closed=bool(getattr(record, "is_closed", True)),
    )


def snapshot_as_dict(snapshot: FeatureSnapshot) -> dict[str, Any]:
    return asdict(snapshot)
