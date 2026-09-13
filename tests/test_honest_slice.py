from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from packages.context_engine import ContextEngine
from packages.context_engine.resample import resample_closed
from packages.evaluator.metrics import signed_direction_accuracy
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from packages.journal import ForecastJournal
from packages.models import emit_baseline_forecast, walk_forward_baselines
from services.api.runtime import freshness, reset_runtime


def test_as_of_is_candle_close_not_open():
    xs = sept_2026_failed_breakout()[:400]
    snap = ContextEngine().build_snapshot(xs)
    assert snap.as_of == xs[-1].close_time()
    assert snap.as_of == xs[-1].open_time + timedelta(minutes=5)


def test_unfinished_parent_bucket_does_not_change_15m_state():
    engine = ContextEngine()
    full = sept_2026_failed_breakout()[:90]
    complete = resample_closed(full, 15, "15m")
    assert complete
    # Keep only complete 15m groups, then add two extra 5m of a new parent.
    cutoff = complete[-1].close_time()
    closed_complete = [c for c in full if c.close_time() <= cutoff]
    before = engine.build_snapshot(closed_complete)
    extra_start = closed_complete[-1].open_time + timedelta(minutes=5)
    extras = []
    price = closed_complete[-1].close
    for i in range(2):
        t = extra_start + timedelta(minutes=5 * i)
        extras.append(
            type(closed_complete[0])(
                "AVAXUSDT",
                "5m",
                t,
                price,
                price + 0.5,
                price - 0.01,
                price + 0.4,
                1,
            )
        )
    after = engine.build_snapshot(closed_complete + extras)
    assert before.timeframes["15m"].as_of == after.timeframes["15m"].as_of
    assert before.timeframes["15m"].close == after.timeframes["15m"].close


def test_5m_relief_bounce_does_not_flip_4h():
    candles = sept_2026_failed_breakout()
    idx = bounce_start_index(candles)
    engine = ContextEngine()
    before = engine.build_snapshot(candles[:idx])
    after = engine.build_snapshot(candles)
    assert before.timeframes["4h"].regime in {"bearish", "transition_down"}
    assert after.timeframes["4h"].regime == before.timeframes["4h"].regime
    assert after.interpretation != ""
    assert "reversal" in after.interpretation or "higher-timeframe" in after.interpretation


def test_emit_forecast_ignores_future_if_caller_truncates():
    candles = sept_2026_failed_breakout()
    t = 500
    a = emit_baseline_forecast(candles[: t + 1])
    mutated = list(candles)
    mutated[t + 1] = mutated[t + 1].__class__(
        mutated[t + 1].symbol,
        "5m",
        mutated[t + 1].open_time,
        99,
        120,
        80,
        110,
        1,
    )
    b = emit_baseline_forecast(mutated[: t + 1])
    assert a["horizons"] == b["horizons"]
    assert a["p_close_above_origin"] if False else a["horizons"][0]["p_close_above_origin"] is None


def test_walk_forward_reports_sample_count_and_zero_abstains():
    candles = sept_2026_failed_breakout()[:400]
    report = walk_forward_baselines(candles, horizons=3, min_history=80, step=20)
    assert report["validation"] == "walk_forward"
    h1 = report["horizons"]["1"]
    assert h1["sample_count"] > 0
    assert h1["zero"]["signed_direction"]["accuracy"] is None
    assert h1["zero"]["signed_direction"]["abstentions"] == h1["sample_count"]
    assert h1["drift20"]["signed_direction"]["metric"] == "signed_direction_accuracy"


def test_signed_direction_skips_zero_predictions():
    result = signed_direction_accuracy([0.1, -0.2, 0.3], [0.0, -0.1, 0.2])
    assert result["decided"] == 2
    assert result["abstentions"] == 1
    assert result["accuracy"] == 1.0


def test_journal_stores_snapshot_id(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    digest = journal.append_forecast(
        "f-1",
        "AVAXUSDT",
        "2026-09-01T00:05:00Z",
        "baseline.drift20",
        {"h": 1},
        context_snapshot_id="snap-9",
        data_manifest_id="man-1",
    )
    got = journal.get_forecast("f-1")
    assert got["context_snapshot_id"] == "snap-9"
    assert len(digest) == 64
    journal.close()


def test_freshness_live_only_when_close_is_recent():
    now = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
    assert freshness(now - timedelta(minutes=5), now)["status"] == "live"
    assert freshness(now - timedelta(hours=2), now)["status"] == "stale"
    assert freshness(now - timedelta(days=11), now)["status"] == "stale"


def test_api_replay_hides_post_as_of_candles(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    candles = sept_2026_failed_breakout()
    idx = bounce_start_index(candles)
    as_of = candles[idx - 1].close_time().isoformat()
    client = TestClient(app)
    body = client.get("/api/v1/replay/AVAXUSDT", params={"as_of": as_of}).json()
    assert body["replay"] is True
    assert body["health"]["status"] == "fixture"
    assert abs(body["last_price"] - candles[idx - 1].close) < 1e-9
    assert body["snapshot"]["timeframes"]["4h"]["regime"] in {"bearish", "transition_down"}
    reset_runtime()


def test_api_fixture_market_is_not_live(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/market/AVAXUSDT").json()
    assert body["health"]["status"] == "fixture"
    assert body["execution_enabled"] is False
    p = body["forecast"]["forecast"]["horizons"][0]["p_close_above_origin"]
    if p is not None:
        assert 0.0 <= p <= 1.0
        assert body["forecast"]["forecast"].get("calibration_ref")
    assert body["metrics"]["available"] is True
    assert "4h" in body["snapshot"]["timeframes"]
    analogs = body["snapshot"].get("analogs") or []
    assert analogs
    for row in analogs:
        assert row["known_at"] <= body["as_of"]
        assert "Not a forecast" in row["note"]
        assert "confidence" not in row
    reset_runtime()
