from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle
from packages.market_data.integrity import (
    audit_ohlcv,
    canonical_payload,
    expected_5m_grid,
    find_duplicates,
    find_gaps,
    find_ohlc_violations,
    manifest_sha256,
    verify_manifest_sha256,
)
from packages.market_data.store import CandleStore


def _t(i: int, *, offset_seconds: int = 0) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=5 * i, seconds=offset_seconds)


def _candle(i: int, close: float = 10.0, *, offset_seconds: int = 0) -> Candle:
    open_time = _t(i, offset_seconds=offset_seconds)
    return Candle("AVAXUSDT", "5m", open_time, close, close + 0.1, close - 0.1, close, 100 + i)


def _contiguous(n: int = 12) -> list[Candle]:
    return [_candle(i, 10 + i * 0.01) for i in range(n)]


def test_expected_5m_grid_is_inclusive_and_aligned():
    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 0, 25, tzinfo=timezone.utc)
    grid = expected_5m_grid(start, end)
    assert grid == [_t(i) for i in range(6)]
    assert all(int(slot.timestamp()) % 300 == 0 for slot in grid)


def test_contiguous_5m_series_is_clean():
    series = _contiguous(24)
    report = audit_ohlcv(series)
    assert report.ok
    assert report.expected_slots == 24
    assert report.observed_count == 24
    assert report.unique_open_times == 24
    assert report.issues == ()
    assert find_gaps(series) == []
    assert find_duplicates(series) == []
    assert find_ohlc_violations(series) == []


def test_detects_missing_bars_on_5m_grid():
    series = [_candle(i) for i in range(12) if i not in {3, 4}]
    gaps = find_gaps(series)
    missing = {issue.open_time for issue in gaps if issue.kind == "gap"}
    assert _t(3).isoformat() in missing
    assert _t(4).isoformat() in missing
    report = audit_ohlcv(series)
    assert not report.ok
    assert report.expected_slots == 12
    assert report.observed_count == 10
    assert len(report.of_kind("gap")) == 2


def test_detects_unaligned_open_time():
    series = [_candle(0), _candle(1, offset_seconds=17), _candle(2)]
    issues = find_gaps(series)
    unaligned = [issue for issue in issues if issue.kind == "unaligned"]
    assert len(unaligned) == 1
    assert unaligned[0].open_time == _t(1, offset_seconds=17).isoformat()
    assert any(issue.kind == "gap" and issue.open_time == _t(1).isoformat() for issue in issues)


def test_detects_duplicate_open_times_and_conflicts():
    base = _contiguous(8)
    duplicate = _candle(2, 10.02)
    conflict = Candle(
        "AVAXUSDT",
        "5m",
        _t(2),
        11.0,
        11.1,
        10.9,
        11.0,
        999.0,
    )
    same_payload = audit_ohlcv([*base, duplicate])
    assert not same_payload.ok
    dupes = same_payload.of_kind("duplicate")
    assert len(dupes) == 1
    assert dupes[0].open_time == _t(2).isoformat()
    assert "conflicting" not in dupes[0].detail

    conflicted = find_duplicates([*base, conflict])
    assert len(conflicted) == 1
    assert "conflicting payloads" in conflicted[0].detail


def test_detects_ohlc_violations_on_raw_records():
    stamp = _t(0)
    records = [
        {
            "symbol": "AVAXUSDT",
            "timeframe": "5m",
            "open_time": stamp,
            "open": 10.0,
            "high": 9.5,
            "low": 9.0,
            "close": 10.2,
            "volume": 10.0,
        },
        {
            "symbol": "AVAXUSDT",
            "timeframe": "5m",
            "open_time": _t(1),
            "open": 10.0,
            "high": 10.5,
            "low": 10.2,
            "close": 10.1,
            "volume": 10.0,
        },
        {
            "symbol": "AVAXUSDT",
            "timeframe": "5m",
            "open_time": _t(2),
            "open": 10.0,
            "high": float("nan"),
            "low": 9.9,
            "close": 10.0,
            "volume": -1.0,
        },
    ]
    issues = find_ohlc_violations(records)
    assert len(issues) == 3
    assert "high below max(open, close)" in issues[0].detail
    assert "low above min(open, close)" in issues[1].detail
    assert "non-finite high" in issues[2].detail
    assert "volume is negative" in issues[2].detail
    assert not audit_ohlcv(records).ok


def test_manifest_checksum_matches_store_payload_hashing(tmp_path):
    series = _contiguous(20)
    shuffled = [series[i] for i in (4, 0, 19, 7, 1, 2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)]
    store = CandleStore(tmp_path / "integrity.db")
    assert store.insert_many("test", shuffled) == 20
    stored = store.manifest("test", "AVAXUSDT", "5m")
    assert manifest_sha256(shuffled) == stored.sha256
    assert verify_manifest_sha256(series, stored.sha256)
    assert canonical_payload(series[0]) == CandleStore._payload(series[0])
    store.close()


def test_manifest_checksum_changes_when_a_closed_bar_changes():
    series = _contiguous(6)
    mutated = [_candle(i, 10 + i * 0.01) if i != 3 else _candle(3, 99.0) for i in range(6)]
    assert manifest_sha256(series) != manifest_sha256(mutated)
