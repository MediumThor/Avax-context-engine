"""EMA / RSI / ATR / realized-vol wrappers.

Prefers ``packages.context_engine.indicators`` when that package is importable.
"""

from __future__ import annotations

from typing import Iterable

from . import _lib

_USING_CONTEXT_ENGINE = False
_ema = _lib.ema
_rsi = _lib.rsi
_atr = _lib.atr
_realized_volatility = _lib.realized_volatility

try:
    from packages.context_engine.indicators import (  # type: ignore
        atr as _ce_atr,
        ema as _ce_ema,
        realized_volatility as _ce_realized_volatility,
        rsi as _ce_rsi,
    )
except ImportError:
    pass
else:
    _USING_CONTEXT_ENGINE = True
    _ema = _ce_ema
    _rsi = _ce_rsi
    _atr = _ce_atr
    _realized_volatility = _ce_realized_volatility


def using_context_engine() -> bool:
    return _USING_CONTEXT_ENGINE


def ema(values: Iterable[float], span: int) -> list[float]:
    return _ema(values, span)


def rsi(values: Iterable[float], period: int = 14) -> list[float | None]:
    return _rsi(values, period)


def atr(
    highs: Iterable[float],
    lows: Iterable[float],
    closes: Iterable[float],
    period: int = 14,
) -> list[float | None]:
    return _atr(highs, lows, closes, period)


def realized_volatility(values: Iterable[float], window: int = 24) -> float | None:
    return _realized_volatility(values, window)
