from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle, Pivot
from packages.context_engine.pivots_atr import atr_zigzag_pivots, pivots_known_as_of
from packages.context_engine.structure import confirmed_pivots


def _t0() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _bar(
    i: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    *,
    is_closed: bool = True,
    minutes: int = 5,
) -> Candle:
    return Candle(
        "AVAXUSDT",
        "5m",
        _t0() + timedelta(minutes=minutes * i),
        open_,
        high,
        low,
        close,
        100.0 + i,
        is_closed=is_closed,
    )


def _path(closes: list[float], wick: float = 0.05) -> list[Candle]:
    out: list[Candle] = []
    prev = closes[0]
    for i, close in enumerate(closes):
        open_ = prev
        high = max(open_, close) + wick
        low = min(open_, close) - wick
        out.append(_bar(i, open_, high, low, close))
        prev = close
    return out


def _identity(pivot: Pivot) -> tuple:
    return (pivot.index, pivot.known_at_index, pivot.time, pivot.known_at, pivot.price, pivot.kind)


def _known_set(pivots: list[Pivot], as_of: datetime) -> set[tuple]:
    return {_identity(p) for p in pivots_known_as_of(pivots, as_of)}


def _swing_series() -> list[Candle]:
    """Decline, rally to a peak, shallow pause, then a confirming crash."""
    closes: list[float] = []
    price = 14.0
    for _ in range(24):
        price -= 0.12
        closes.append(round(price, 6))
    for _ in range(22):
        price += 0.18
        closes.append(round(price, 6))
    peak = price
    for _ in range(8):
        price -= 0.02
        closes.append(round(price, 6))
    pause_end = len(closes)
    for _ in range(24):
        price -= 0.22
        closes.append(round(price, 6))
    xs = _path(closes, wick=0.04)
    xs.pause_end = pause_end  # type: ignore[attr-defined]
    xs.peak = peak  # type: ignore[attr-defined]
    return xs


def test_window_confirmed_pivots_not_replaced():
    xs = _path([10.0, 10.1, 10.2, 11.5, 10.2, 10.1, 10.0, 9.9])
    window = confirmed_pivots(xs, left=2, right=2)
    atrs = atr_zigzag_pivots(xs, atr_period=3, atr_multiple=1.0)
    assert confirmed_pivots.__module__ == "packages.context_engine.structure"
    assert atr_zigzag_pivots.__module__ == "packages.context_engine.pivots_atr"
    assert confirmed_pivots is not atr_zigzag_pivots
    high = next(p for p in window if p.kind == "high")
    assert high.index == 3
    assert high.known_at_index == 5
    assert isinstance(atrs, list)


def test_pivot_exposes_candle_time_and_known_at():
    xs = _swing_series()
    pivots = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    assert pivots
    for pivot in pivots:
        assert pivot.time == xs[pivot.index].open_time
        assert pivot.known_at == xs[pivot.known_at_index].open_time
        assert pivot.known_at >= pivot.time
        assert pivot.known_at_index >= pivot.index
        expected = xs[pivot.index].high if pivot.kind == "high" else xs[pivot.index].low
        assert pivot.price == expected


def test_pivot_unavailable_before_known_at():
    xs = _swing_series()
    pivots = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    later = [p for p in pivots if p.known_at > p.time]
    assert later
    sample = later[0]
    before = sample.known_at - timedelta(seconds=1)
    assert sample not in pivots_known_as_of(pivots, before)
    assert sample in pivots_known_as_of(pivots, sample.known_at)
    as_of_time = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0, as_of=sample.time)
    assert all(p.known_at <= sample.time for p in as_of_time)
    assert sample not in as_of_time


def test_future_candles_do_not_create_pivots_known_at_or_before_t():
    xs = _swing_series()
    t = xs.pause_end  # type: ignore[attr-defined]
    cutoff = xs[t - 1].open_time

    prefix = atr_zigzag_pivots(xs[:t], atr_period=5, atr_multiple=2.0)
    full = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    as_of = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0, as_of=cutoff)

    prefix_ids = {_identity(p) for p in prefix}
    assert prefix_ids == _known_set(full, cutoff)
    assert prefix_ids == {_identity(p) for p in as_of}

    later = [p for p in full if p.known_at > cutoff]
    assert later, "fixture must confirm at least one pivot after T"

    mutated = xs[:t] + [
        Candle(
            "AVAXUSDT",
            "5m",
            c.open_time,
            200.0,
            250.0,
            50.0,
            180.0,
            99999.0,
        )
        for c in xs[t:]
    ]
    mutated_full = atr_zigzag_pivots(mutated, atr_period=5, atr_multiple=2.0)
    assert prefix_ids == _known_set(mutated_full, cutoff)
    assert {_identity(p) for p in atr_zigzag_pivots(mutated[:t], 5, 2.0)} == prefix_ids
    leaked = [p for p in mutated_full if p.known_at <= cutoff and _identity(p) not in prefix_ids]
    assert leaked == []


def test_prefix_equals_as_of_for_every_cut():
    xs = _swing_series()
    full = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    for t in range(1, len(xs) + 1):
        cutoff = xs[t - 1].open_time
        prefix = atr_zigzag_pivots(xs[:t], atr_period=5, atr_multiple=2.0)
        as_of = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0, as_of=cutoff)
        expected = _known_set(full, cutoff)
        assert {_identity(p) for p in prefix} == expected
        assert {_identity(p) for p in as_of} == expected


def test_unclosed_candle_cannot_confirm():
    xs = _swing_series()
    t = xs.pause_end  # type: ignore[attr-defined]
    with_partial = xs[:t] + [
        Candle(
            xs[t].symbol,
            xs[t].timeframe,
            xs[t].open_time,
            9.0,
            9.2,
            4.0,
            4.5,
            100.0,
            is_closed=False,
        )
    ]
    assert atr_zigzag_pivots(with_partial, atr_period=5, atr_multiple=2.0) == atr_zigzag_pivots(
        xs[:t], atr_period=5, atr_multiple=2.0
    )


def test_flat_market_does_not_emit_zero_atr_pivots():
    xs = _path([10.0] * 40, wick=0.0)
    assert atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0) == []


def test_short_series_and_invalid_params():
    assert atr_zigzag_pivots([], atr_period=5) == []
    assert atr_zigzag_pivots(_path([10.0, 10.1, 10.2]), atr_period=14) == []
    try:
        atr_zigzag_pivots(_path([10.0, 10.1]), atr_period=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
    try:
        atr_zigzag_pivots(_path([10.0, 10.1]), atr_multiple=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
    try:
        atr_zigzag_pivots(_path([10.0, 10.1]), as_of=datetime(2026, 1, 1))
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_as_of_before_first_candle_is_empty():
    xs = _swing_series()
    early = xs[0].open_time - timedelta(minutes=5)
    assert atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0, as_of=early) == []


def test_deterministic_and_alternating_after_first():
    xs = _swing_series()
    a = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    b = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    assert [_identity(p) for p in a] == [_identity(p) for p in b]
    kinds = [p.kind for p in a]
    assert len(kinds) >= 2
    assert all(kinds[i] != kinds[i + 1] for i in range(len(kinds) - 1))


def test_v_reversal_confirms_low_only_after_atr_move():
    closes = [12.0 - 0.15 * i for i in range(20)] + [9.0 + 0.2 * i for i in range(20)]
    xs = _path(closes, wick=0.03)
    bottom_time = xs[19].open_time
    before_reversal = atr_zigzag_pivots(xs[:20], atr_period=5, atr_multiple=2.0)
    lows_before = [p for p in before_reversal if p.kind == "low" and p.index == 19]
    assert lows_before == []
    full = atr_zigzag_pivots(xs, atr_period=5, atr_multiple=2.0)
    lows = [p for p in full if p.kind == "low" and abs(p.time - bottom_time) <= timedelta(minutes=25)]
    assert lows
    confirmed = lows[-1]
    assert confirmed.known_at > confirmed.time
    assert confirmed not in pivots_known_as_of(full, confirmed.time)
