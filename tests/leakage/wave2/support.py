"""Shared fixtures for WAVE2-36 leakage probes. Not collected by pytest."""

from __future__ import annotations

import importlib
import inspect
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from packages.context_engine import Candle, ContextEngine

SYMBOL = "AVAXUSDT"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
PARENT_MINUTES = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}

# Future-horizon closes used as *features* (not evaluation labels / current close).
FORBIDDEN_FEATURE_KEY = re.compile(
    r"("
    r"future[_-]?close"
    r"|next[_-]?close"
    r"|close[_-]?(lead|fwd|forward|tplus|t\+|horizon)"
    r"|target[_-]?(close|ret|return|y)"
    r"|y[_-]?(true|close|h)"
    r"|label[_-]?(close|h|horizon)"
    r"|close[_-]?h(?:orizon)?[_-]?(?:[1-9]|10)\b"
    r")",
    re.IGNORECASE,
)

ASSEMBLER_MODULES = (
    "packages.features.assembler",
    "packages.features",
    "packages.forecast.features",
    "packages.ml.feature_assembler",
    "packages.ml.features",
    "services.forecast.features",
    "services.forecast.assembler",
    "packages.context_engine.features",
)

ASSEMBLER_ATTRS = (
    "assemble",
    "assemble_features",
    "build_features",
    "feature_snapshot",
    "build_feature_snapshot",
)


def make_5m(
    n: int,
    *,
    start: float = 10.0,
    step: float = 0.001,
    t0: datetime = T0,
    symbol: str = SYMBOL,
) -> list[Candle]:
    out: list[Candle] = []
    price = start
    for i in range(n):
        close = price + step
        high = max(price, close) + 0.01
        low = min(price, close) - 0.01
        out.append(
            Candle(
                symbol,
                "5m",
                t0 + timedelta(minutes=5 * i),
                price,
                high,
                low,
                close,
                100.0 + i,
                is_closed=True,
            )
        )
        price = close
    return out


def mutate_after(candles: list[Candle], first_future: int) -> list[Candle]:
    """Replace every candle at/after first_future with an extreme closed bar."""
    out = list(candles[:first_future])
    for candle in candles[first_future:]:
        out.append(
            Candle(
                candle.symbol,
                candle.timeframe,
                candle.open_time,
                100.0,
                110.0,
                90.0,
                105.0,
                99_999.0,
                is_closed=True,
            )
        )
    return out


def as_unclosed(candles: list[Candle]) -> list[Candle]:
    return [
        Candle(
            c.symbol,
            c.timeframe,
            c.open_time,
            80.0,
            95.0,
            70.0,
            90.0,
            88_888.0,
            is_closed=False,
        )
        for c in candles
    ]


def known_at(candles: list[Candle], as_of: datetime) -> list[Candle]:
    return [c for c in candles if c.open_time <= as_of]


def snapshot_at(candles: list[Candle], as_of: datetime):
    """Build a snapshot using only information legally available at as_of.

    If a later WAVE-2 engine accepts as_of, pass the full series through that API
    so leakage in as-of filtering fails the probe. Otherwise filter the prefix.
    """
    engine = ContextEngine()
    params = inspect.signature(engine.build_snapshot).parameters
    if "as_of" in params:
        return engine.build_snapshot(candles, as_of=as_of)
    return engine.build_snapshot(known_at(candles, as_of))


def expected_5m_per_parent(minutes: int) -> int:
    return minutes // 5


def parent_open(dt: datetime, minutes: int) -> datetime:
    epoch_minutes = int(dt.timestamp() // 60)
    floored = epoch_minutes - (epoch_minutes % minutes)
    return datetime.fromtimestamp(floored * 60, tz=timezone.utc)


def complete_parent_count(n_5m: int, minutes: int) -> int:
    return n_5m // expected_5m_per_parent(minutes)


def try_import_assembler() -> Callable[..., Any] | None:
    for name in ASSEMBLER_MODULES:
        try:
            module = importlib.import_module(name)
        except ImportError:
            continue
        for attr in ASSEMBLER_ATTRS:
            fn = getattr(module, attr, None)
            if callable(fn):
                return fn
    return None


def jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str, allow_nan=False))


def walk_keys(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            found.append((child, value))
            found.extend(walk_keys(value, child))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(walk_keys(value, f"{path}[{i}]"))
    return found


def forbidden_feature_paths(payload: Any) -> list[str]:
    """Return paths that look like later-horizon closes used as features.

    Current-bar `close` on a timeframe state is allowed. Horizon keys on
    baseline metric blocks ('1'..'10') are not feature columns.
    """
    hits: list[str] = []
    for path, _value in walk_keys(payload):
        leaf = path.rsplit(".", 1)[-1]
        if leaf == "close":
            continue
        if FORBIDDEN_FEATURE_KEY.search(leaf):
            hits.append(path)
    return sorted(set(hits))
