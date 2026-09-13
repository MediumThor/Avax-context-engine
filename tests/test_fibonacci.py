from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine.fibonacci import (
    DEFAULT_EXTENSION_RATIOS,
    DEFAULT_MEASURED_MOVE_RATIOS,
    DEFAULT_RETRACEMENT_RATIOS,
    FibFeatureSet,
    extension_price,
    fibonacci_features,
    measured_move_anchors,
    measured_move_price,
    pivots_known_as_of,
    retracement_price,
    swing_anchors,
)
from packages.context_engine.models import Pivot
from packages.context_engine.structure import Pivot as StructurePivot

T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _ts(hours: int) -> datetime:
    return T0 + timedelta(hours=hours)


def pivot(
    index: int,
    hours: int,
    price: float,
    kind: str,
    *,
    confirm_lag: int = 2,
) -> Pivot:
    return Pivot(
        index=index,
        known_at_index=index + confirm_lag,
        time=_ts(hours),
        known_at=_ts(hours + confirm_lag),
        price=price,
        kind=kind,  # type: ignore[arg-type]
    )


def _swing_pivots() -> list[Pivot]:
    # Confirmed low → high → low pullback. High is unknown until hour 8.
    return [
        pivot(2, 2, 10.0, "low", confirm_lag=2),  # known_at hour 4
        pivot(6, 6, 20.0, "high", confirm_lag=2),  # known_at hour 8
        pivot(12, 12, 16.0, "low", confirm_lag=2),  # known_at hour 14
    ]


def test_structure_pivot_type_is_the_only_anchor_type():
    assert StructurePivot is Pivot
    with pytest.raises(TypeError, match="pixel/price"):
        swing_anchors([(10.0, 20.0)], _ts(10))  # type: ignore[list-item]


def test_pivot_unknown_at_t_cannot_be_used_as_anchor():
    pivots = _swing_pivots()
    hidden = pivots[1]
    as_of = hidden.known_at - timedelta(seconds=1)

    assert hidden.known_at > as_of
    assert hidden not in pivots_known_as_of(pivots, as_of)

    features = fibonacci_features(pivots, as_of)
    used = []
    for anchor in features.anchors:
        used.extend([anchor.start, anchor.end])
    for setup in features.measured_moves:
        used.extend([setup.start, setup.end, setup.correction])
    assert hidden not in used
    assert features.anchors == ()
    assert all(level.known_at <= as_of for level in features.levels)

    after = fibonacci_features(pivots, hidden.known_at)
    assert any(anchor.end == hidden or anchor.start == hidden for anchor in after.anchors)


def test_future_confirmation_does_not_change_features_at_t():
    pivots = _swing_pivots()
    as_of = pivots[1].known_at - timedelta(seconds=1)
    baseline = fibonacci_features(pivots, as_of)

    mutated = [
        pivots[0],
        replace(pivots[1], price=99.0),
        replace(pivots[2], price=1.0),
    ]
    assert fibonacci_features(mutated, as_of) == baseline
    later = fibonacci_features(pivots, pivots[2].known_at)
    assert later != baseline
    assert later.anchors


def test_levels_use_exact_anchor_prices():
    start, end, correction = _swing_pivots()
    features = fibonacci_features([start, end, correction], end.known_at)
    assert len(features.anchors) == 1
    anchor = features.anchors[0]
    assert anchor.start.price == 10.0
    assert anchor.end.price == 20.0
    assert anchor.direction == "up"

    retr = {level.ratio: level.price for level in features.levels if level.kind == "retracement"}
    ext = {level.ratio: level.price for level in features.levels if level.kind == "extension"}
    assert retr[0.0] == 20.0
    assert retr[1.0] == 10.0
    assert retr[0.618] == retracement_price(10.0, 20.0, 0.618)
    assert retr[0.618] == 20.0 + (10.0 - 20.0) * 0.618
    assert ext[1.618] == extension_price(10.0, 20.0, 1.618)
    assert ext[1.618] == 10.0 + (20.0 - 10.0) * 1.618


def test_downswing_retracement_and_extension_are_exact():
    high = pivot(1, 1, 20.0, "high")
    low = pivot(5, 5, 8.0, "low")
    features = fibonacci_features([high, low], low.known_at)
    retr = {level.ratio: level for level in features.levels if level.kind == "retracement"}
    ext = {level.ratio: level for level in features.levels if level.kind == "extension"}
    assert features.anchors[0].direction == "down"
    assert retr[0.5].price == 14.0
    assert ext[1.618].price == extension_price(20.0, 8.0, 1.618)
    assert retr[0.5].status == "candidate"
    assert retr[0.5].is_guaranteed_support is False


def test_candidate_levels_are_not_guaranteed_support():
    features = fibonacci_features(_swing_pivots(), _swing_pivots()[-1].known_at)
    assert features.levels
    payload = features.to_dict()
    assert payload["status"] == "candidate_features"
    assert payload["is_guaranteed_support"] is False
    for level in features.levels:
        assert level.status == "candidate"
        assert level.is_guaranteed_support is False
        row = level.to_dict()
        assert row["role"] == "context_feature"
        assert row["is_guaranteed_support"] is False
        assert "support" not in row["status"]
        assert "resistance" not in row["status"]


def test_no_elliott_forced_labeling():
    features = fibonacci_features(_swing_pivots(), _swing_pivots()[-1].known_at)
    blob = str(features.to_dict()).lower()
    forbidden = (
        "elliott",
        "impulse",
        "wave-1",
        "wave-2",
        "wave-3",
        "wave-4",
        "wave-5",
        "wave 1",
        "wave 2",
        "wave 3",
        "corrective wave",
    )
    for token in forbidden:
        assert token not in blob
    for level in features.levels:
        assert not hasattr(level, "elliott_label")
        assert not hasattr(level, "wave")


def test_measured_move_projects_from_confirmed_pullback():
    start, end, correction = _swing_pivots()
    as_of_before_c = correction.known_at - timedelta(seconds=1)
    assert measured_move_anchors([start, end, correction], as_of_before_c) == []

    setups = measured_move_anchors([start, end, correction], correction.known_at)
    assert len(setups) == 1
    assert setups[0].correction == correction
    assert measured_move_price(10.0, 20.0, 16.0, 1.0) == 26.0
    features = fibonacci_features([start, end, correction], correction.known_at)
    moves = [level for level in features.levels if level.kind == "measured_move"]
    by_ratio = {level.ratio: level.price for level in moves}
    assert by_ratio[1.0] == 26.0
    assert by_ratio[1.618] == 16.0 + 10.0 * 1.618
    assert all(level.known_at == correction.known_at for level in moves)


def test_same_kind_collapse_keeps_more_extreme_confirmed_swing():
    low_a = pivot(1, 1, 10.0, "low")
    low_b = pivot(3, 3, 11.5, "low")
    high = pivot(7, 7, 20.0, "high")
    features = fibonacci_features([low_a, low_b, high], high.known_at)
    assert len(features.anchors) == 1
    assert features.anchors[0].start == low_a
    assert features.anchors[0].end == high
    assert features.anchors[0].range == 10.0


def test_zero_range_swing_is_not_an_anchor():
    a = pivot(1, 1, 10.0, "low")
    b = pivot(4, 4, 10.0, "high")
    features = fibonacci_features([a, b], b.known_at)
    assert features.anchors == ()
    assert features.levels == ()


def test_as_of_must_be_timezone_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        fibonacci_features(_swing_pivots(), datetime(2026, 9, 1))


def test_naive_pivot_timestamps_are_rejected():
    naive = Pivot(
        1,
        3,
        datetime(2026, 9, 1),
        datetime(2026, 9, 1, 2),
        10.0,
        "low",
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        pivots_known_as_of([naive], _ts(10))


def test_known_at_before_pivot_time_is_rejected():
    broken = Pivot(1, 0, _ts(4), _ts(3), 10.0, "low")
    with pytest.raises(ValueError, match="known_at must be >="):
        pivots_known_as_of([broken], _ts(10))


def test_default_ratio_sets_are_structural_not_elliott_counts():
    assert 0.618 in DEFAULT_RETRACEMENT_RATIOS
    assert 1.618 in DEFAULT_EXTENSION_RATIOS
    assert 1.0 in DEFAULT_MEASURED_MOVE_RATIOS
    assert 5 not in DEFAULT_RETRACEMENT_RATIOS
    features = fibonacci_features(_swing_pivots(), _swing_pivots()[1].known_at)
    kinds = {level.kind for level in features.levels}
    assert kinds == {"retracement", "extension"}
    assert isinstance(features, FibFeatureSet)


def test_level_known_at_is_max_of_anchor_known_ats():
    start = pivot(1, 1, 10.0, "low", confirm_lag=5)
    end = pivot(8, 8, 20.0, "high", confirm_lag=2)
    features = fibonacci_features([start, end], end.known_at)
    assert start.known_at > start.time
    assert features.anchors[0].known_at == max(start.known_at, end.known_at)
    assert all(level.known_at == end.known_at for level in features.levels)
    assert all(level.provenance.source == "confirmed_swing" for level in features.levels)
