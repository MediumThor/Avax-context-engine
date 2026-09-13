"""WAVE2-36: a 5m bounce must not flip a completed 4H parent regime at T."""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta

from packages.context_engine import Candle, ContextEngine

from tests.leakage.wave2.support import make_5m

FOUR_HOUR_5M = 48
COMPLETE_4H_BARS = 16
BOUNCE_BARS = 10


def _bounce_after(last: Candle, n: int, step: float = 0.15) -> list[Candle]:
    out: list[Candle] = []
    price = last.close
    start = last.open_time + timedelta(minutes=5)
    for i in range(n):
        close = price + step
        out.append(
            Candle(
                last.symbol,
                "5m",
                start + timedelta(minutes=5 * i),
                price,
                close + 0.02,
                price - 0.01,
                close,
                last.volume + i + 1,
                is_closed=True,
            )
        )
        price = close
    return out


def test_5m_bounce_does_not_flip_completed_4h_parent_regime():
    decline = make_5m(COMPLETE_4H_BARS * FOUR_HOUR_5M, start=20.0, step=-0.01)
    engine = ContextEngine()
    at_t = engine.build_snapshot(decline)
    assert "4h" in at_t.timeframes
    parent_t = at_t.timeframes["4h"]
    assert parent_t.regime in {"bearish", "transition_down"}

    bounced = decline + _bounce_after(decline[-1], BOUNCE_BARS)
    assert BOUNCE_BARS < FOUR_HOUR_5M
    after = engine.build_snapshot(bounced)

    parent_after = after.timeframes["4h"]
    assert asdict(parent_after) == asdict(parent_t)
    assert after.timeframes["5m"].close != at_t.timeframes["5m"].close
    if "1d" in at_t.timeframes:
        assert asdict(after.timeframes["1d"]) == asdict(at_t.timeframes["1d"])
