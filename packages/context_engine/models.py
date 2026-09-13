from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

Regime = Literal["bullish", "bearish", "neutral", "transition_up", "transition_down", "unknown"]


@dataclass(frozen=True, slots=True)
class Candle:
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
        if self.open_time.tzinfo is None:
            raise ValueError("Candle.open_time must be timezone-aware")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC ordering")
        if self.high < self.low:
            raise ValueError("high must be >= low")


@dataclass(frozen=True, slots=True)
class Pivot:
    index: int
    known_at_index: int
    time: datetime
    known_at: datetime
    price: float
    kind: Literal["high", "low"]


@dataclass(frozen=True, slots=True)
class StructuralZone:
    id: str
    lower: float
    upper: float
    role: Literal["support", "resistance", "mixed"]
    strength: float
    test_count: int
    source: str = "pivot_cluster"


@dataclass(frozen=True, slots=True)
class TimeframeState:
    timeframe: str
    as_of: datetime
    close: float
    regime: Regime
    swing_state: str
    volatility: str
    ema20: float | None
    ema50: float | None
    ema200: float | None
    rsi14: float | None
    atr14: float | None
    support_zones: tuple[StructuralZone, ...] = field(default_factory=tuple)
    resistance_zones: tuple[StructuralZone, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    symbol: str
    as_of: datetime
    timeframes: dict[str, TimeframeState]
    schema_version: str = "1"

    def to_dict(self) -> dict:
        return asdict(self)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
