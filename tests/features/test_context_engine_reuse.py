"""When context_engine is on the path, assembler must reuse its math."""

from __future__ import annotations

import pytest

from packages.features import _lib
from packages.features.indicators import atr, ema, realized_volatility, rsi, using_context_engine
from packages.features.resample import completed_parents, using_context_engine as resample_uses_ce
from tests.features.conftest import series, utc

pytestmark = pytest.mark.skipif(
    not using_context_engine(),
    reason="packages.context_engine not importable on this tree",
)


def test_public_indicators_match_vendored_fallback():
    xs = [8.05, 8.10, 8.00, 7.90, 7.95, 8.20, 8.15]
    highs = [x + 0.08 for x in xs]
    lows = [x - 0.08 for x in xs]
    assert ema(xs, 4) == _lib.ema(xs, 4)
    assert rsi(xs, 3) == _lib.rsi(xs, 3)
    assert atr(highs, lows, xs, 3) == _lib.atr(highs, lows, xs, 3)
    assert realized_volatility(xs, 3) == _lib.realized_volatility(xs, 3)


def test_completed_parents_match_fallback_resample_plus_as_of_filter():
    assert resample_uses_ce()
    candles = series(36, start=utc(2026, 1, 1, 9, 0))
    as_of = utc(2026, 1, 1, 12, 0)
    via_public = completed_parents(candles, as_of, "1h")
    from packages.features.resample import period_end

    via_fallback = [
        c for c in _lib.resample_closed(candles, 60, "1h") if period_end(c.open_time, "1h") <= as_of
    ]
    assert [c.open_time for c in via_public] == [c.open_time for c in via_fallback]
    assert [c.close for c in via_public] == [c.close for c in via_fallback]
