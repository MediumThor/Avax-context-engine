"""Gap handling and leakage tests for BTC/ETH/AVAX cross-market context."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from math import log

import pytest

from packages.context_engine.cross_market import (
    CrossMarketError,
    build_cross_market,
    classify_move,
    log_return,
    ols_beta,
    pearson,
)
from packages.context_engine.models import Candle


def _t0() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _bar(
    i: int,
    close: float,
    *,
    symbol: str = "AVAXUSDT",
    is_closed: bool = True,
    minutes: int = 5,
    open_: float | None = None,
) -> Candle:
    prev = close if open_ is None else open_
    high = max(prev, close) + 0.01
    low = min(prev, close) - 0.01
    return Candle(
        symbol,
        "5m",
        _t0() + timedelta(minutes=minutes * i),
        prev,
        high,
        low,
        close,
        100.0 + i,
        is_closed=is_closed,
    )


def _series(
    n: int,
    *,
    start: float,
    step: float,
    symbol: str,
    skip: set[int] | None = None,
    unclosed: set[int] | None = None,
) -> list[Candle]:
    skip = skip or set()
    unclosed = unclosed or set()
    out: list[Candle] = []
    price = start
    for i in range(n):
        nxt = price + step
        if i not in skip:
            out.append(_bar(i, nxt, symbol=symbol, is_closed=i not in unclosed, open_=price))
        price = nxt
    return out


def _state(
    avax: list[Candle],
    btc: list[Candle],
    eth: list[Candle] | None = None,
    avaxbtc: list[Candle] | None = None,
    *,
    as_of: datetime | None = None,
    window: int = 8,
):
    cutoff = as_of if as_of is not None else avax[-1].open_time
    return build_cross_market(
        avax,
        btc,
        eth,
        avaxbtc,
        as_of=cutoff,
        window=window,
        sync_abs_logret=0.001,
    )


def test_relative_strength_is_log_return_difference():
    avax = _series(20, start=10.0, step=0.10, symbol="AVAXUSDT")
    btc = _series(20, start=100.0, step=0.10, symbol="BTCUSDT")
    eth = _series(20, start=50.0, step=0.05, symbol="ETHUSDT")
    state = _state(avax, btc, eth, as_of=avax[15].open_time, window=8)

    avax_r = log(avax[15].close / avax[14].close)
    btc_r = log(btc[15].close / btc[14].close)
    eth_r = log(eth[15].close / eth[14].close)
    assert state.avax_btc.relative_strength == pytest.approx(avax_r - btc_r)
    assert state.avax_eth.relative_strength == pytest.approx(avax_r - eth_r)
    assert state.avax_btc.health == "valid"
    assert state.health == "valid"
    assert state.avax_btc.correlation is not None
    assert state.avax_btc.beta is not None


def test_missing_btc_candle_at_t_is_unknown_not_invented():
    avax = _series(16, start=8.0, step=0.02, symbol="AVAXUSDT")
    btc = _series(16, start=90_000.0, step=10.0, symbol="BTCUSDT", skip={10})
    as_of = avax[10].open_time

    state = _state(avax, btc, as_of=as_of, window=8)

    assert state.avax_btc.health == "unknown"
    assert state.avax_btc.move_flag == "unknown"
    assert state.avax_btc.relative_strength is None
    assert state.avax_btc.correlation is None
    assert state.avax_btc.beta is None
    assert state.synchronized_breakout is None
    assert "missing_aligned_candle" in state.avax_btc.evidence

    # Using the previous BTC print would invent an aligned return. Prove we do not.
    invented = log_return(avax[10].close, avax[9].close) - log_return(btc[9].close, btc[8].close)
    assert invented is not None
    assert state.avax_btc.relative_strength != invented


def test_gap_in_window_marks_corr_beta_unknown_without_compacting():
    avax = _series(20, start=10.0, step=0.05, symbol="AVAXUSDT")
    btc = _series(20, start=100.0, step=0.20, symbol="BTCUSDT", skip={12})
    as_of = avax[18].open_time
    window = 8

    state = _state(avax, btc, as_of=as_of, window=window)

    # 1-bar pair at 18 is aligned (17 and 18 exist on both).
    assert state.avax_btc.relative_strength is not None
    assert state.avax_btc.health == "degraded"
    assert state.avax_btc.correlation is None
    assert state.avax_btc.beta is None
    assert "gap_or_short_window" in state.avax_btc.evidence

    # Compacted intersection (drop the gap and compute on remaining neighbors)
    # would produce a number. That invents consecutive returns across the hole.
    btc_closes = [c.close for c in btc if c.open_time <= as_of][-window - 1 :]
    avax_closes = [c.close for c in avax if c.open_time <= as_of][-window - 1 :]
    avax_rets = [log(avax_closes[i] / avax_closes[i - 1]) for i in range(1, len(avax_closes))]
    btc_rets = [log(btc_closes[i] / btc_closes[i - 1]) for i in range(1, len(btc_closes))]
    compacted = pearson(avax_rets, btc_rets)
    assert compacted is not None
    assert state.avax_btc.correlation is None


def test_future_btc_candle_cannot_change_avax_btc_feature_at_t():
    avax = _series(30, start=8.0, step=0.01, symbol="AVAXUSDT")
    btc = _series(30, start=90_000.0, step=12.0, symbol="BTCUSDT")
    eth = _series(30, start=3_000.0, step=1.0, symbol="ETHUSDT")
    t = avax[18].open_time

    baseline = _state(avax, btc, eth, as_of=t, window=8)

    mutated_btc = []
    for candle in btc:
        if candle.open_time > t:
            mutated_btc.append(
                replace(candle, open=1.0, high=2.0, low=0.5, close=1.0, volume=1e9)
            )
        else:
            mutated_btc.append(candle)

    leaked = _state(avax, mutated_btc, eth, as_of=t, window=8)
    assert baseline.to_dict() == leaked.to_dict()
    assert baseline.avax_btc.relative_strength == leaked.avax_btc.relative_strength
    assert baseline.avax_btc.correlation == leaked.avax_btc.correlation
    assert baseline.avax_btc.beta == leaked.avax_btc.beta


def test_future_avax_candle_cannot_change_state_at_t():
    avax = _series(24, start=8.0, step=0.03, symbol="AVAXUSDT")
    btc = _series(24, start=80_000.0, step=8.0, symbol="BTCUSDT")
    t = avax[12].open_time
    baseline = _state(avax, btc, as_of=t, window=8)
    mutated = [
        replace(c, close=c.close * 3, high=c.close * 3 + 0.01) if c.open_time > t else c
        for c in avax
    ]
    assert _state(mutated, btc, as_of=t, window=8).to_dict() == baseline.to_dict()


def test_unclosed_btc_bar_at_t_is_ignored():
    avax = _series(16, start=9.0, step=0.02, symbol="AVAXUSDT")
    btc = _series(16, start=95_000.0, step=5.0, symbol="BTCUSDT", unclosed={12})
    as_of = avax[12].open_time
    state = _state(avax, btc, as_of=as_of, window=8)
    assert state.avax_btc.health == "unknown"
    assert state.avax_btc.relative_strength is None


def test_as_of_between_bars_uses_last_closed_only():
    avax = _series(16, start=10.0, step=0.04, symbol="AVAXUSDT")
    btc = _series(16, start=100.0, step=0.40, symbol="BTCUSDT")
    t = avax[10].open_time
    between = t + timedelta(minutes=2)
    at_bar = _state(avax, btc, as_of=t, window=8)
    later = _state(avax, btc, as_of=between, window=8)
    assert later.known_at == t
    assert later.avax_btc.to_dict() == at_bar.avax_btc.to_dict()


def test_synchronized_and_decoupled_flags():
    n = 16
    avax_up = _series(n, start=10.0, step=0.20, symbol="AVAXUSDT")
    btc_up = _series(n, start=100.0, step=2.00, symbol="BTCUSDT")
    btc_down = _series(n, start=100.0, step=-2.00, symbol="BTCUSDT")
    avax_down = _series(n, start=10.0, step=-0.20, symbol="AVAXUSDT")
    btc_flat = _series(n, start=100.0, step=0.0, symbol="BTCUSDT")

    sync_up = _state(avax_up, btc_up, as_of=avax_up[-1].open_time, window=8)
    assert sync_up.avax_btc.move_flag == "synchronized_breakout"
    assert sync_up.synchronized_breakout is True
    assert sync_up.decoupled is False

    sync_down = _state(avax_down, btc_down, as_of=avax_down[-1].open_time, window=8)
    assert sync_down.avax_btc.move_flag == "synchronized_breakdown"
    assert sync_down.synchronized_breakdown is True

    decoupled = _state(avax_up, btc_down, as_of=avax_up[-1].open_time, window=8)
    assert decoupled.avax_btc.move_flag == "decoupled"
    assert decoupled.decoupled is True
    assert decoupled.synchronized_breakout is False

    quiet = _state(avax_up, btc_flat, as_of=avax_up[-1].open_time, window=8)
    assert quiet.avax_btc.move_flag == "quiet"
    assert quiet.decoupled is False


def test_eth_missing_degrades_health_but_avax_btc_can_remain_valid():
    avax = _series(16, start=10.0, step=0.05, symbol="AVAXUSDT")
    btc = _series(16, start=100.0, step=0.50, symbol="BTCUSDT")
    state = _state(avax, btc, eth=None, as_of=avax[-1].open_time, window=8)
    assert state.avax_btc.health == "valid"
    assert state.avax_eth.health == "unknown"
    assert state.eth_btc.health == "unknown"
    assert state.health == "degraded"
    assert "eth_unavailable_or_unaligned" in state.evidence


def test_native_avaxbtc_uses_exact_alignment():
    avax = _series(16, start=10.0, step=0.05, symbol="AVAXUSDT")
    btc = _series(16, start=100.0, step=0.50, symbol="BTCUSDT")
    ratio = [
        _bar(i, avax[i].close / btc[i].close, symbol="AVAXBTC", open_=avax[i].open / btc[i].open)
        for i in range(len(avax))
    ]
    state = _state(avax, btc, avaxbtc=ratio, as_of=avax[-1].open_time, window=8)
    expected = log_return(ratio[-1].close, ratio[-2].close)
    assert state.avaxbtc_log_return == pytest.approx(expected)

    gapped = [c for i, c in enumerate(ratio) if i != len(ratio) - 1]
    missing = _state(avax, btc, avaxbtc=gapped, as_of=avax[-1].open_time, window=8)
    assert missing.avaxbtc_log_return is None


def test_naive_as_of_is_rejected():
    avax = _series(8, start=10.0, step=0.01, symbol="AVAXUSDT")
    btc = _series(8, start=100.0, step=0.01, symbol="BTCUSDT")
    with pytest.raises(CrossMarketError, match="timezone-aware"):
        build_cross_market(avax, btc, as_of=datetime(2026, 1, 1, 1, 0), window=3)


def test_classify_move_and_stats_helpers():
    assert classify_move(None, 0.01) == "unknown"
    assert classify_move(0.0001, 0.0001) == "quiet"
    assert classify_move(0.02, 0.01) == "synchronized_breakout"
    assert classify_move(-0.02, -0.01) == "synchronized_breakdown"
    assert classify_move(0.02, -0.01) == "decoupled"
    assert pearson([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)
    assert ols_beta([2.0, 4.0, 6.0], [1.0, 2.0, 3.0]) == pytest.approx(2.0)
    assert pearson([1.0, 1.0, 1.0], [2.0, 3.0, 4.0]) is None
    assert log_return(0.0, 1.0) is None


def test_btc_regime_unknown_when_btc_gapped_at_eval():
    avax = _series(20, start=10.0, step=0.02, symbol="AVAXUSDT")
    btc = _series(20, start=100.0, step=0.40, symbol="BTCUSDT", skip={15})
    state = _state(avax, btc, as_of=avax[15].open_time, window=8)
    assert state.btc_regime == "unknown"
    assert state.btc_volatility == "unknown"
    assert state.btc_realized_vol is None


def test_no_execution_surface():
    source = open("packages/context_engine/cross_market.py", encoding="utf-8").read().lower()
    for banned in ("create_order", "place_order", "exchange.create", "api_key", "leverage"):
        assert banned not in source
