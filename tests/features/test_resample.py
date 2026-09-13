from packages.features.resample import completed_parents, is_visible_at, period_end, visible_candles
from tests.features.conftest import make_candle, series, utc


def test_unclosed_5m_is_not_visible():
    t = utc(2026, 1, 1, 10, 30)
    bar = make_candle(t, 10.0, is_closed=False)
    assert period_end(t, "5m") == utc(2026, 1, 1, 10, 35)
    assert not is_visible_at(bar, utc(2026, 1, 1, 10, 35))


def test_closed_5m_visible_only_at_or_after_period_end():
    t = utc(2026, 1, 1, 10, 30)
    bar = make_candle(t, 10.0, is_closed=True)
    assert not is_visible_at(bar, utc(2026, 1, 1, 10, 34))
    assert is_visible_at(bar, utc(2026, 1, 1, 10, 35))


def test_visible_candles_drop_future_and_open_bars():
    xs = series(6, start=utc(2026, 1, 1, 10, 0))
    xs[-1] = make_candle(xs[-1].open_time, 99.0, is_closed=False, open_=98.0)
    as_of = utc(2026, 1, 1, 10, 20)
    vis = visible_candles(xs, as_of)
    assert [c.open_time for c in vis] == [
        utc(2026, 1, 1, 10, 0),
        utc(2026, 1, 1, 10, 5),
        utc(2026, 1, 1, 10, 10),
        utc(2026, 1, 1, 10, 15),
    ]


def test_completed_15m_requires_full_bucket_and_period_end():
    # 10:00-10:15 needs 10:00, 10:05, 10:10
    xs = series(4, start=utc(2026, 1, 1, 10, 0))
    at_1010 = completed_parents(xs, utc(2026, 1, 1, 10, 10), "15m")
    assert at_1010 == []
    at_1014 = completed_parents(xs, utc(2026, 1, 1, 10, 14), "15m")
    assert at_1014 == []
    at_1015 = completed_parents(xs, utc(2026, 1, 1, 10, 15), "15m")
    assert len(at_1015) == 1
    assert at_1015[0].open_time == utc(2026, 1, 1, 10, 0)
    assert at_1015[0].timeframe == "15m"
    assert at_1015[0].open == xs[0].open
    assert at_1015[0].close == xs[2].close
    assert at_1015[0].high == max(c.high for c in xs[:3])
    assert at_1015[0].volume == sum(c.volume for c in xs[:3])


def test_incomplete_hour_is_not_resampled():
    xs = series(7, start=utc(2026, 1, 1, 10, 0))
    parents = completed_parents(xs, utc(2026, 1, 1, 10, 35), "1h")
    assert parents == []


def test_complete_hour_appears_only_after_close():
    xs = series(12, start=utc(2026, 1, 1, 9, 0))
    before = completed_parents(xs, utc(2026, 1, 1, 9, 55), "1h")
    assert before == []
    at_close = completed_parents(xs, utc(2026, 1, 1, 10, 0), "1h")
    assert len(at_close) == 1
    assert at_close[0].open_time == utc(2026, 1, 1, 9, 0)
    assert at_close[0].close == xs[11].close
