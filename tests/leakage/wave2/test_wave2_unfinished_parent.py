"""WAVE2-36: unfinished 15m/1h/4h/1d parents must not appear in HTF state at T."""

from __future__ import annotations

import pytest

from packages.context_engine import ContextEngine
from packages.context_engine.resample import resample_closed

from tests.leakage.wave2.support import (
    PARENT_MINUTES,
    as_unclosed,
    complete_parent_count,
    expected_5m_per_parent,
    make_5m,
    parent_open,
)


@pytest.mark.parametrize("timeframe", ["15m", "1h", "4h", "1d"])
def test_unfinished_parent_bucket_is_absent_from_htf_state(timeframe: str):
    minutes = PARENT_MINUTES[timeframe]
    width = expected_5m_per_parent(minutes)
    complete_bars = 3 if timeframe != "1d" else 1
    leftover = 2 if width > 2 else 1
    n = complete_bars * width + leftover
    xs = make_5m(n, start=12.0, step=-0.01)

    resampled = resample_closed(xs, minutes, timeframe)
    assert len(resampled) == complete_bars

    last_complete_start = xs[(complete_bars - 1) * width].open_time
    assert resampled[-1].open_time == parent_open(last_complete_start, minutes)
    unfinished_close = xs[-1].close
    assert resampled[-1].close != unfinished_close

    snap = ContextEngine().build_snapshot(xs)
    assert timeframe in snap.timeframes
    state = snap.timeframes[timeframe]
    assert state.as_of == resampled[-1].open_time
    assert state.close == resampled[-1].close
    assert state.close != unfinished_close


@pytest.mark.parametrize("timeframe", ["15m", "1h", "4h", "1d"])
def test_unclosed_5m_cannot_complete_a_parent_bucket(timeframe: str):
    minutes = PARENT_MINUTES[timeframe]
    width = expected_5m_per_parent(minutes)
    closed = make_5m(width - 1, start=11.0, step=-0.02)
    filler = as_unclosed(make_5m(width, start=20.0, step=0.5)[-1:])
    # One unclosed 5m that would finish the bucket if wrongly counted.
    mixed = closed + filler
    resampled = resample_closed(mixed, minutes, timeframe)
    assert resampled == []
    if width - 1 < 1:
        return
    # Engine still needs at least one closed 5m.
    snap = ContextEngine().build_snapshot(mixed)
    assert timeframe not in snap.timeframes


def test_partial_first_15m_does_not_create_15m_state():
    xs = make_5m(2, start=10.0, step=0.02)
    assert complete_parent_count(2, 15) == 0
    assert resample_closed(xs, 15, "15m") == []
    snap = ContextEngine().build_snapshot(xs)
    assert "15m" not in snap.timeframes
    assert "1h" not in snap.timeframes
    assert "4h" not in snap.timeframes
    assert "1d" not in snap.timeframes
