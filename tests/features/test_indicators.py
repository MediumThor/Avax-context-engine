from packages.features import _lib
from packages.features.indicators import atr, ema, realized_volatility, rsi, using_context_engine


def test_ema_seeds_from_first_value_and_is_causal():
    values = [10.0, 11.0, 12.0, 9.0]
    out = ema(values, 3)
    assert out[0] == 10.0
    assert len(out) == 4
    # later values must not rewrite earlier EMA points
    longer = ema(values + [20.0], 3)
    assert longer[:4] == out


def test_rsi_and_atr_leave_warmup_none():
    closes = [float(i) for i in range(1, 20)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    r = rsi(closes, 14)
    a = atr(highs, lows, closes, 14)
    assert r[13] is not None
    assert all(v is None for v in r[:13])
    assert a[13] is not None
    assert all(v is None for v in a[:13])


def test_realized_vol_requires_window_plus_one():
    assert realized_volatility([10.0] * 24, 24) is None
    assert realized_volatility([10.0 + 0.1 * i for i in range(25)], 24) is not None


def test_fallback_matches_public_wrappers_when_context_engine_absent():
    xs = [8.0, 8.1, 7.9, 8.2, 8.4, 8.3]
    highs = [x + 0.05 for x in xs]
    lows = [x - 0.05 for x in xs]
    if not using_context_engine():
        assert ema(xs, 3) == _lib.ema(xs, 3)
        assert rsi(xs, 3) == _lib.rsi(xs, 3)
        assert atr(highs, lows, xs, 3) == _lib.atr(highs, lows, xs, 3)
        assert realized_volatility(xs, 3) == _lib.realized_volatility(xs, 3)
