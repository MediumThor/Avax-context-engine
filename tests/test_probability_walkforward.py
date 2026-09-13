from __future__ import annotations

from packages.fixtures import sept_2026_failed_breakout
from packages.models import walk_forward_probabilities
from tests.test_freqai_quantiles import make_5m, mutate_after


def test_fixture_walk_forward_scores_brier_without_promotion():
    candles = sept_2026_failed_breakout()
    report = walk_forward_probabilities(candles, horizons=10, min_history=80, step=20)
    assert report["promotion_allowed"] is False
    assert report["freqai_beats_baselines"] is None
    h1 = report["horizons"]["1"]["probability"]
    assert h1["sample_count"] >= 8
    assert h1["brier"] is not None
    assert 0.0 <= h1["brier"] <= 1.0
    # Fixture / unspecified source is not a live calibration claim.
    assert h1["ece"] is None
    coverage = report["horizons"]["1"]["interval"]["coverage"]
    if coverage is not None:
        assert 0.0 <= coverage <= 1.0


def test_future_perturbation_does_not_change_scores_at_t():
    candles = make_5m(220)
    as_of = candles[180].close_time()
    before = walk_forward_probabilities(candles, horizons=3, min_history=80, step=10, as_of=as_of)
    after = walk_forward_probabilities(
        mutate_after(candles, 181),
        horizons=3,
        min_history=80,
        step=10,
        as_of=as_of,
    )
    assert before == after


def test_short_series_leaves_scores_unscored():
    candles = make_5m(100)
    report = walk_forward_probabilities(candles, horizons=2, min_history=80, step=10)
    assert report["horizons"]["1"]["probability"]["brier"] is None
    assert report["horizons"]["1"]["probability"]["ece"] is None
