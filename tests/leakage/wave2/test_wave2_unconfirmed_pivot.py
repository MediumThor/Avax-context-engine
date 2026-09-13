"""WAVE2-36: unconfirmed pivots must not enter structure used at T."""

from __future__ import annotations

from packages.context_engine import Candle, ContextEngine
from packages.context_engine.structure import confirmed_pivots

from tests.leakage.wave2.support import make_5m

SPIKE_PRICE = 42.4242
LEFT = 3
RIGHT = 3
SPIKE_INDEX = 12


def _series_with_unconfirmed_high() -> list[Candle]:
    xs = make_5m(40, start=10.0, step=0.0)
    base = xs[SPIKE_INDEX]
    xs[SPIKE_INDEX] = Candle(
        base.symbol,
        base.timeframe,
        base.open_time,
        base.open,
        SPIKE_PRICE,
        min(base.low, base.open, base.close),
        base.close,
        base.volume,
        is_closed=True,
    )
    return xs


def _zone_prices(snapshot) -> list[float]:
    prices: list[float] = []
    for state in snapshot.timeframes.values():
        for zone in (*state.support_zones, *state.resistance_zones):
            prices.extend([zone.lower, zone.upper])
    return prices


def test_unconfirmed_pivot_absent_from_confirmed_pivots_and_snapshot_structure():
    xs = _series_with_unconfirmed_high()
    # Engine default windows: known_at_index = SPIKE_INDEX + RIGHT.
    # The pivot is legal only once candles[0 : SPIKE_INDEX + RIGHT + 1] exist.
    unconfirmed = xs[: SPIKE_INDEX + RIGHT]
    assert len(unconfirmed) == SPIKE_INDEX + RIGHT

    pivots = confirmed_pivots(unconfirmed, LEFT, RIGHT)
    assert all(p.index != SPIKE_INDEX for p in pivots)
    assert all(abs(p.price - SPIKE_PRICE) > 1e-9 for p in pivots)

    snap = ContextEngine().build_snapshot(unconfirmed)
    for price in _zone_prices(snap):
        assert abs(price - SPIKE_PRICE) > 1e-9

    confirmed = xs[: SPIKE_INDEX + RIGHT + 1]
    later = confirmed_pivots(confirmed, LEFT, RIGHT)
    assert any(p.index == SPIKE_INDEX and p.kind == "high" for p in later)
    assert any(abs(p.price - SPIKE_PRICE) <= 1e-9 for p in later)


def test_pivot_known_at_is_not_the_pivot_candle_time():
    xs = _series_with_unconfirmed_high()
    confirmed = xs[: SPIKE_INDEX + RIGHT + 1]
    high = next(
        p
        for p in confirmed_pivots(confirmed, LEFT, RIGHT)
        if p.index == SPIKE_INDEX and p.kind == "high"
    )
    assert high.known_at_index == SPIKE_INDEX + RIGHT
    assert high.known_at > high.time
    assert high.known_at == xs[SPIKE_INDEX + RIGHT].open_time
    # Structure at the pivot candle itself still must not include it.
    at_event = confirmed_pivots(xs[: SPIKE_INDEX + 1], LEFT, RIGHT)
    assert all(p.index != SPIKE_INDEX for p in at_event)
