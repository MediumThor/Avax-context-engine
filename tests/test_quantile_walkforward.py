from __future__ import annotations

import math

from packages.context_engine.models import Candle
from packages.fixtures import sept_2026_failed_breakout
from packages.models.freqai_quantiles import emit_quantile_forecast
from packages.models.quantile_walkforward import walk_forward_quantiles
from tests.test_freqai_quantiles import as_of_index, make_5m, mutate_after


def test_walk_forward_quantiles_scores_without_promotion():
    candles = make_5m(180)
    report = walk_forward_quantiles(
        candles,
        horizons=3,
        min_history=90,
        step=20,
        lookback=180,
        backend="python",
        min_train=30,
    )
    assert report["validation"] == "walk_forward"
    assert report["promotion_allowed"] is False
    assert report["freqai_beats_baselines"] is None
    assert report["origin_count"] > 0
    h1 = report["horizons"]["1"]
    assert h1["sample_count"] > 0
    assert h1["q50"]["mae"] >= 0
    assert h1["drift20"]["mae"] >= 0
    assert 0.0 <= h1["q10_q90"]["coverage"] <= 1.0
    assert "ece" not in report
    assert "ece" not in h1


def test_walk_forward_ignores_future_perturbation():
    candles = make_5m(160)
    origin = 110
    as_of = as_of_index(candles, origin)
    before = emit_quantile_forecast(candles[: origin + 1], as_of=as_of, backend="python")
    mutated = mutate_after(candles, origin + 1)
    after = emit_quantile_forecast(mutated, as_of=as_of, backend="python")
    assert before["horizons"] == after["horizons"]

    cap = origin + 2
    full = walk_forward_quantiles(
        candles[:cap],
        horizons=2,
        min_history=100,
        step=25,
        lookback=160,
        backend="python",
    )
    perturbed = walk_forward_quantiles(
        mutated[:cap],
        horizons=2,
        min_history=100,
        step=25,
        lookback=160,
        backend="python",
    )
    assert full["horizons"]["1"]["sample_count"] == perturbed["horizons"]["1"]["sample_count"]
    assert math.isclose(
        full["horizons"]["1"]["q50"]["mae"],
        perturbed["horizons"]["1"]["q50"]["mae"],
        rel_tol=0,
        abs_tol=1e-12,
    )


def test_september_fixture_walk_forward_has_samples():
    candles = sept_2026_failed_breakout()[:500]
    report = walk_forward_quantiles(
        candles,
        horizons=2,
        min_history=120,
        step=80,
        lookback=200,
        backend="python",
    )
    assert report["origin_count"] >= 2
    assert report["horizons"]["1"]["sample_count"] == report["origin_count"]
    assert report["promotion_allowed"] is False
